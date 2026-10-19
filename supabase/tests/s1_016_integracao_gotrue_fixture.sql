-- S1-002/I16 — SOMENTE STACK LOCAL SUPABASE DESCARTAVEL NO CI.
-- Prova o contrato I14/I15 de sessao, nao regras de redistribuicao.
-- NÃO é migration; NUNCA executar em Supabase hospedado ou produção.
create schema if not exists prumo_private authorization postgres;
create table public.atores(id uuid primary key);

-- Stubs apenas para satisfazer dependencias das fachadas I14 reais.
-- Nao simulam regras de autoridade da equipe (essas ficam nos testes PG17).
create function prumo_private.s1_mover_atendimento_da_equipe(
 uuid,uuid,uuid,uuid,uuid) returns jsonb
 language sql security invoker set search_path=''
 as $$ select '{"stub":true}'::jsonb $$;
create function prumo_private.s1_pausar_operador_da_equipe(
 uuid,uuid,text) returns jsonb
 language sql security invoker set search_path=''
 as $$ select '{"stub":true}'::jsonb $$;
create function prumo_private.s1_reativar_operador_da_equipe(
 uuid,uuid) returns jsonb
 language sql security invoker set search_path=''
 as $$ select '{"stub":true}'::jsonb $$;
revoke all on function
 prumo_private.s1_mover_atendimento_da_equipe(uuid,uuid,uuid,uuid,uuid),
 prumo_private.s1_pausar_operador_da_equipe(uuid,uuid,text),
 prumo_private.s1_reativar_operador_da_equipe(uuid,uuid)
 from public,anon,authenticated,service_role;
