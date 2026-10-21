-- 20261018224639_uk_geography_reference revoked execute from public, anon and
-- authenticated, but the project's default function privileges still left
-- explicit grants for anon and authenticated. It is a trigger function and
-- cannot be called directly; this only brings the grants in line with intent.
revoke execute on function public.geography_validate_reference() from anon, authenticated;
