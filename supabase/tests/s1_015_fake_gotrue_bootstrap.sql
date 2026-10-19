\set ON_ERROR_STOP on
-- SOMENTE PG17 fake-auth local; auth.sessions real é criada pelo GoTrue.
-- NÃO rodar no Supabase hospedado.
create table auth.sessions (
 id uuid primary key,
 user_id uuid not null references auth.users(id) on delete cascade
);
revoke all on auth.sessions from public,anon,authenticated,service_role;
\echo 'S1-002/I15: auth.sessions fake somente na base descartável'
