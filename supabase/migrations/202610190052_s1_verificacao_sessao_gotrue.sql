-- S1-002/I15 — defesa adicional para operações humanas privilegiadas.
-- Acesso SOMENTE em PG17 descartável até homologação real GoTrue/PostgREST.
-- A assinatura, expiração JWT e a atribuição de request.jwt.claims ao
-- cliente autenticado DEVEM ser verificadas pelo gateway antes deste código.
-- auth.sessions deve ser a tabela GERIDA PELO GoTrue (id, user_id).
-- Se não existir, a instalação falha fechada; NÃO criar auth.sessions aqui.
--
-- No PostgREST moderno, claims chegam num objeto JSON request.jwt.claims,
-- NÃO se deve depender do legacy request.jwt.claim.role.
-- session_id vincula a sessão ao usuário; DELETE revoga o token para
-- ESTES comandos mesmo se o JWT anterior ainda estiver no prazo.
-- FOR KEY SHARE evita corridas com DELETE da sessão durante o comando.
create or replace function prumo_private.s1_exigir_identidade_sessao()
returns uuid language plpgsql security invoker set search_path='' as $auth$
declare
 v_claims jsonb;
 v_ator uuid;
 v_sub uuid;
 v_sessao uuid;
begin
 begin
  v_claims:=nullif(pg_catalog.current_setting('request.jwt.claims',true),'')::jsonb;
  if v_claims is null
   or pg_catalog.jsonb_typeof(v_claims)<>'object'
   or v_claims->>'role' is distinct from 'authenticated' then
   raise exception 'SESSAO_AUTENTICADA_OBRIGATORIA' using errcode='42501';
  end if;
  v_sub:=(v_claims->>'sub')::uuid;
  v_sessao:=(v_claims->>'session_id')::uuid;
 exception when invalid_text_representation then
  raise exception 'CLAIMS_SESSAO_INVALIDOS' using errcode='42501';
 end;
 v_ator:=auth.uid();
 if v_sub is null or v_sessao is null or v_ator is distinct from v_sub
  or not exists(select 1 from public.atores a where a.id=v_ator) then
  raise exception 'IDENTIDADE_SESSAO_INVALIDA' using errcode='42501';
 end if;
 perform 1 from auth.sessions s
  where s.id=v_sessao and s.user_id=v_ator
  for key share of s;
 if not found then
  raise exception 'SESSAO_REVOGADA_OU_INEXISTENTE' using errcode='42501';
 end if;
 return v_ator;
end $auth$;

-- Preserva fronteira I14: helper privativo, nenhuma RPC nova, nenhuma
-- exposição por public; authenticated só recebe as três fachadas 051.
revoke all on function prumo_private.s1_exigir_identidade_sessao()
 from public,anon,authenticated,service_role;
