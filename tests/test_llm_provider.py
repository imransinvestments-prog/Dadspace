import json
import os
import unittest
from urllib.error import HTTPError, URLError
from unittest.mock import patch

import llm_provider as llm

SCHEMA = {'type': 'array', 'items': {'type': 'object', 'properties': {
    'title': {'type': 'string'}, 'evidence': {'anyOf': [{'type': 'string'}, {'type': 'null'}], 'default': None}},
    'required': ['title']}}
DATA = {'items': [{'title': 'Family workshop', 'evidence': None}]}


def response(provider='openai', data=DATA):
    text = json.dumps(data)
    if provider == 'openai':
        return {'status': 'completed', 'output': [{'content': [{'type': 'output_text', 'text': text}]}],
                'usage': {'input_tokens': 10, 'output_tokens': 5, 'total_tokens': 15,
                          'output_tokens_details': {'reasoning_tokens': 3}}}
    if provider == 'deepseek':
        return {'choices': [{'finish_reason': 'stop', 'message': {'content': text}}],
                'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15}}
    return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': text}]}}],
            'usageMetadata': {'promptTokenCount': 10, 'candidatesTokenCount': 2,
                              'thoughtsTokenCount': 3, 'totalTokenCount': 15}}


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'LLM_PROVIDER': 'openai', 'LLM_MODEL': 'test-model',
            'OPENAI_API_KEY': 'secret', 'DEEPSEEK_API_KEY': 'secret', 'GEMINI_API_KEY': 'secret'}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.post = patch('llm_provider._post').start()
        self.post.return_value = response()
        self.sleep = patch('llm_provider.time.sleep').start()
        self.addCleanup(patch.stopall)

    def generator(self):
        return llm.StructuredGenerator('EXTRACTION', 'gemini-legacy')

    def test_openai_strict_array_wrapper_and_no_storage(self):
        gen = self.generator()
        self.assertEqual(gen.generate('source', SCHEMA), DATA['items'])
        url, key, body, timeout, gemini = self.post.call_args.args
        self.assertEqual(url, 'https://api.openai.com/v1/responses')
        self.assertFalse(body['store'])
        schema = body['text']['format']['schema']
        item = schema['properties']['items']['items']
        self.assertFalse(item['additionalProperties'])
        self.assertEqual(item['required'], ['title', 'evidence'])
        self.assertNotIn('default', item['properties']['evidence'])
        self.assertEqual(gen.metrics['output_tokens'], 5)  # reasoning already included
        self.assertEqual(gen.metrics['thinking_tokens'], 3)
        self.assertEqual(gen.metrics['total_tokens'], 15)

    def test_each_adapter_normalizes_and_validates(self):
        for provider in llm.KEYS:
            with self.subTest(provider=provider):
                os.environ['LLM_PROVIDER'] = provider
                self.post.return_value = response(provider)
                gen = self.generator()
                self.assertEqual(gen.generate('source', SCHEMA), DATA['items'])
                self.assertEqual(gen.metrics['output_tokens'], 5)
                self.assertEqual(gen.metrics['total_tokens'], 15)
                if provider == 'deepseek':
                    body = self.post.call_args.args[2]
                    self.assertEqual(body['response_format'], {'type': 'json_object'})
                    self.assertIn('JSON', body['messages'][0]['content'])
                    self.assertEqual(gen.metrics['unknown_thinking_attempts'], 1)

    def test_no_retry_or_fallback_on_schema_failure(self):
        self.post.return_value = response(data={'items': [{'title': 123}]})
        with self.assertRaises(ValueError):
            self.generator().generate('source', SCHEMA)
        self.assertEqual(self.post.call_count, 1)

    def test_refusal_and_incomplete_rejected_without_retry(self):
        for reply in ({**response(), 'status': 'incomplete'},
                      {**response(), 'output': [{'content': [{'type': 'refusal', 'refusal': 'no'}]}]}):
            self.post.reset_mock()
            self.post.return_value = reply
            with self.assertRaises(ValueError):
                self.generator().generate('source', SCHEMA)
            self.assertEqual(self.post.call_count, 1)

    def test_transport_retry_bounded_and_credential_error_not_retried(self):
        self.post.side_effect = [URLError('private details'), response()]
        gen = self.generator()
        gen.generate('source', SCHEMA)
        self.assertEqual(gen.metrics['api_attempts'], 2)
        self.assertEqual(gen.metrics['unknown_usage_attempts'], 1)
        for code in (400, 401, 402, 403, 404):
            self.post.reset_mock()
            self.post.side_effect = HTTPError('private-url', code, 'secret-body', {}, None)
            with self.assertRaisesRegex(llm.FatalLLMError, 'HTTP ' + str(code)) as caught:
                self.generator().generate('source', SCHEMA)
            self.assertNotIn('private', str(caught.exception))
            self.assertEqual(self.post.call_count, 1)

    def test_attempt_and_unknown_usage_budget_prevent_another_request(self):
        os.environ['LLM_RUN_MAX_ATTEMPTS'] = '1'
        gen = self.generator()
        gen.generate('source', SCHEMA)
        with self.assertRaises(llm.BudgetExhausted):
            gen.generate('again', SCHEMA)
        self.assertEqual(self.post.call_count, 1)
        os.environ['LLM_RUN_MAX_ATTEMPTS'] = '0'
        os.environ['LLM_RUN_TOKEN_BUDGET'] = '100'
        self.post.return_value = {**response(), 'usage': {}}
        gen = self.generator()
        gen.generate('source', SCHEMA)
        with self.assertRaises(llm.BudgetExhausted):
            gen.generate('again', SCHEMA)

    def test_scope_overrides_global_and_alternatives_require_model(self):
        os.environ.update(NEWS_LLM_PROVIDER='deepseek', NEWS_LLM_MODEL='news-model')
        self.assertEqual(llm.selection('NEWS'), ('deepseek', 'news-model'))
        del os.environ['LLM_MODEL']
        with self.assertRaises(llm.FatalLLMError):
            self.generator()
        os.environ['LLM_PROVIDER'] = 'typo'
        with self.assertRaises(llm.FatalLLMError):
            llm.credential_name()

    def test_pydantic_definitions_stay_at_root_for_openai(self):
        from pydantic import BaseModel
        class Item(BaseModel):
            title: str
        caller = llm.make_extractor('legacy', list[Item], 60, RuntimeError)
        self.post.return_value = response(data={'items': [{'title': 'Family workshop'}]})
        self.assertEqual(caller('source'), [{'title': 'Family workshop'}])
        schema = self.post.call_args.args[2]['text']['format']['schema']
        self.assertIn('Item', schema['$defs'])
        self.assertEqual(schema['properties']['items']['items']['$ref'], '#/$defs/Item')

    def test_originals_share_budget_between_generation_and_review(self):
        from original_content_worker import POST_SCHEMA, REVIEW_SCHEMA
        os.environ['LLM_RUN_MAX_ATTEMPTS'] = '1'
        gen = llm.StructuredGenerator('ORIGINAL_CONTENT', 'legacy')
        post = {'title': 'A family game', 'summary': 'Try this', 'sections': []}
        self.post.return_value = response(data=post)
        self.assertEqual(gen.generate('draft', POST_SCHEMA), post)
        with self.assertRaises(llm.BudgetExhausted):
            gen.generate('review', REVIEW_SCHEMA)

    def test_real_collector_schemas_use_openai_without_gemini_client(self):
        import worker
        import events_worker
        for factory in (worker.make_gemini_caller, events_worker.make_gemini_caller):
            with self.subTest(factory=factory.__module__), patch('google.genai.Client') as gemini:
                caller = factory()
                self.post.return_value = response(data={'items': []})
                self.assertEqual(caller('source page'), [])
                self.assertEqual(caller.settings['provider'], 'openai')
                gemini.assert_not_called()
                schema = self.post.call_args.args[2]['text']['format']['schema']
                item = next(iter(schema['$defs'].values()))
                self.assertIn('family_evidence', item['required'])
                self.assertIn('event_url', item['required'])

    def test_news_scoring_and_grouping_share_generator_and_use_distinct_schemas(self):
        import news_worker as news
        news._generator = None
        self.addCleanup(setattr, news, '_generator', None)
        self.post.return_value = response(data={'items': []})
        self.assertEqual(news.gemini_score([{'i': 0, 'title': 'Family news', 'source': 'Test'}]), [])
        first = news._generator
        self.assertIn('relevance', self.post.call_args.args[2]['text']['format']['schema']['properties']['items']['items']['properties'])
        news.gemini_json('group these stories', news.GROUP_SCHEMA)
        self.assertIs(news._generator, first)
        self.assertEqual(news.TOKENS['calls'], 2)
        self.assertIn('story', self.post.call_args.args[2]['text']['format']['schema']['properties']['items']['items']['properties'])

    def test_invalid_http_json_marks_usage_unknown_without_retry(self):
        gen = self.generator()
        self.post.side_effect = ValueError('private response body')
        with self.assertRaisesRegex(RuntimeError, 'invalid HTTP JSON'):
            gen.generate('source', SCHEMA)
        self.assertEqual(gen.metrics['unknown_usage_attempts'], 1)
        self.assertEqual(self.post.call_count, 1)


if __name__ == '__main__':
    unittest.main()
