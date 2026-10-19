"""Small, non-secret GitHub identity envelope for durable worker evidence."""
import os,re
def github_run_context(environ=None):
 env=os.environ if environ is None else environ
 def value(key,pattern):
  raw=env.get(key,'')
  return raw if isinstance(raw,str) and re.fullmatch(pattern,raw) else None
 return {'github_run_id':value('GITHUB_RUN_ID',r'[0-9]{1,20}'),
         'github_run_attempt':value('GITHUB_RUN_ATTEMPT',r'[0-9]{1,6}'),
         'github_sha':value('GITHUB_SHA',r'[a-f0-9]{40}'),
         'github_event':value('GITHUB_EVENT_NAME',r'[a-z_]{1,40}'),
         'github_repository':value('GITHUB_REPOSITORY',r'[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}')}
