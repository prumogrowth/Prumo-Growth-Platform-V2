-- S0 isolation: the HMAC verifier no longer runs as postgres.
-- IMPORTANT: the signed domain entrypoints remain postgres-owned until a
-- separate review; this is an incremental privilege reduction, NOT prod-ready.
--
-- No real keys or remote configuration are created.
do $role$
begin
 if not exists(select 1 from pg_catalog.pg_roles
   where rolname='prumo_s0_signer') then
  create role prumo_s0_signer nologin noinherit
   nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
 end if;
 if not exists(select 1 from pg_catalog.pg_roles
   where rolname='prumo_s0_signer' and not rolcanlogin
   and not rolinherit and not rolsuper and not rolcreatedb
   and not rolcreaterole and not rolreplication and not rolbypassrls)
 then
  raise exception 'UNSAFE_EXISTING_SIGNER_ROLE' using errcode='42501';
 end if;
 -- Dedicated verifier must not be reachable via inherited role membership.
 if exists(
  select 1 from pg_catalog.pg_auth_members am
  join pg_catalog.pg_roles member_role on member_role.oid=am.member
  where am.roleid='prumo_s0_signer'::regrole
    and member_role.rolname not in ('postgres','supabase_admin')
 )
 then raise exception 'SIGNER_ROLE_GRANTED_TO_UNTRUSTED_MEMBER' using errcode='42501';end if;
 -- Hosted and local Supabase can run migrations as non-superuser
 -- postgres. Even postgres must have SET TRUE on signer to ALTER OWNER.
 -- Role administration remains limited to established DB admins.
 if current_user not in ('postgres','supabase_admin') then
  raise exception 'UNEXPECTED_MIGRATION_ROLE' using errcode='42501';
 end if;
 -- Only postgres needs SET to transfer function ownership. In Supabase
 -- supabase_admin is reserved: never attempt GRANT or REVOKE against it.
 execute 'grant prumo_s0_signer to postgres with inherit false, set true';
end $role$;

revoke all on schema prumo_private from prumo_s0_signer;
grant usage on schema prumo_private to prumo_s0_signer;

-- Restrict access to the few columns needed by HMAC verification.
grant select(chave_id,segredo,ativo,valido_desde,valido_ate)
 on prumo_private.gateway_chaves_assinatura_s0 to prumo_s0_signer;
grant insert(nonce,chave_id),select(nonce)
 on prumo_private.gateway_provas_usadas_s0 to prumo_s0_signer;
grant execute on function prumo_private.gateway_material_assinatura_s0(
 text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,bigint,uuid)
 to prumo_s0_signer;

-- pgcrypto may have already been installed in public on local PostgreSQL,
-- or in prumo_crypto in a fresh hosted Supabase instance.
do $ext$
declare v_schema name;
begin
 select n.nspname into v_schema from pg_catalog.pg_extension e
 join pg_catalog.pg_namespace n on n.oid=e.extnamespace
 where e.extname='pgcrypto';
 if v_schema is null then
  raise exception 'PGCRYPTO_NOT_INSTALLED' using errcode='42501';end if;
 execute pg_catalog.format('grant usage on schema %I to prumo_s0_signer',v_schema);
 execute pg_catalog.format(
  'grant execute on function %I.hmac(bytea,bytea,text) to prumo_s0_signer',v_schema);
end $ext$;

-- PostgreSQL row-lock SELECT FOR SHARE requires UPDATE privilege,
-- so official revocation and verification serialize using the same advisory
-- transaction lock, without granting UPDATE on key material to the signer.
create or replace function prumo_private.gateway_validar_prova_s0(
 p_operacao text,p_ator uuid,p_sessao uuid,p_loja uuid,p_alvo uuid,
 p_versao bigint,p_decisao text,p_justificativa text,p_envio uuid,
 p_chave uuid,p_emitido bigint,p_nonce uuid,p_assinatura text
) returns void language plpgsql security definer set search_path='' as $fn$
declare v_segredo bytea;v_agora timestamptz;v_emitido timestamptz;
 v_schema text;v_esperada bytea;v_material text;v_consumida uuid;
begin
 if p_operacao not in ('cancelar_plano','conciliar_c07') or
 p_ator is null or p_sessao is null or p_loja is null or p_alvo is null
 or p_versao is null or p_versao<1 or p_chave is null
 or p_emitido is null or p_nonce is null or p_assinatura is null
 or p_assinatura !~ '^[0-9a-f]{64}$'
 then raise exception 'PROVA_INVALIDA' using errcode='42501';end if;
 v_agora:=pg_catalog.clock_timestamp();
 -- Permit 5 seconds of clock skew but no token older than 30 seconds.
 if p_emitido>extract(epoch from v_agora)::bigint+5
 or p_emitido<extract(epoch from v_agora)::bigint-30
 then raise exception 'PROVA_EXPIRADA' using errcode='42501';end if;
 v_emitido:=pg_catalog.to_timestamp(p_emitido::double precision);
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('prumo-gw-key-v1:'||p_chave::text,0));
 select segredo into v_segredo
 from prumo_private.gateway_chaves_assinatura_s0
 where chave_id=p_chave and ativo
  and valido_desde<=v_emitido and valido_ate>v_agora;
 if not found then raise exception 'PROVA_INVALIDA' using errcode='42501';end if;
 select n.nspname into v_schema
 from pg_catalog.pg_extension e join pg_catalog.pg_namespace n
 on n.oid=e.extnamespace where e.extname='pgcrypto';
 if v_schema is null then raise exception 'HMAC_INDISPONIVEL' using errcode='42501';end if;
 v_material:=prumo_private.gateway_material_assinatura_s0(
 p_operacao,p_ator,p_sessao,p_loja,p_alvo,p_versao,p_decisao,p_justificativa,
 p_envio,p_emitido,p_nonce);
 execute pg_catalog.format('select %I.hmac($1,$2,''sha256'')',v_schema)
 into v_esperada using pg_catalog.convert_to(v_material,'UTF8'),v_segredo;
 if v_esperada is distinct from pg_catalog.decode(p_assinatura,'hex')
 then raise exception 'PROVA_INVALIDA' using errcode='42501';end if;
 insert into prumo_private.gateway_provas_usadas_s0(nonce,chave_id)
 values(p_nonce,p_chave) on conflict do nothing returning nonce into v_consumida;
 if v_consumida is null
 then raise exception 'PROVA_REUTILIZADA' using errcode='42501';end if;
end $fn$;

create or replace function prumo_private.alterar_estado_chave_gateway_s0(
 p_chave uuid,p_versao bigint,p_ativar boolean,p_motivo text
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_chave record;v_agora timestamptz;
begin
 if current_user<>'postgres'
 then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_chave is null or p_versao is null or p_versao<1
    or p_ativar is null or p_motivo is null
    or length(btrim(p_motivo)) not between 10 and 300
 then raise exception 'INVALID_KEY_CHANGE' using errcode='22023';end if;
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('prumo-gw-key-v1:'||p_chave::text,0));
 select * into v_chave from prumo_private.gateway_chaves_assinatura_s0
 where chave_id=p_chave for update;
 if not found then raise exception 'KEY_NOT_FOUND' using errcode='22023';end if;
 if v_chave.versao<>p_versao
 then raise exception 'CONFLICT_VERSION' using errcode='40001';end if;
 if v_chave.revogado_em is not null or v_chave.ativo=p_ativar
 then raise exception 'KEY_TRANSITION_INVALID' using errcode='22023';end if;
 v_agora:=clock_timestamp();
 if p_ativar and (v_chave.valido_desde>v_agora or v_chave.valido_ate<=v_agora)
 then raise exception 'KEY_VALIDITY_WINDOW_INVALID' using errcode='22023';end if;
 update prumo_private.gateway_chaves_assinatura_s0
 set ativo=p_ativar,versao=versao+1,
     revogado_em=case when p_ativar then null else v_agora end,
     motivo_revogacao=case when p_ativar then null else btrim(p_motivo) end
 where chave_id=p_chave;
 return pg_catalog.jsonb_build_object(
  'outcome','APPLIED','chave_id',p_chave,'nova_versao',p_versao+1,
  'ativo',p_ativar,'revogacao_definitiva',not p_ativar);
end $fn$;

-- Change ONLY the signature validator owner. This isolated role can read HMAC
-- material and consume nonces, but cannot access leads, sessions, domain
-- transitions, key rotation, or key-history audit directly.
-- ALTER OWNER also requires the new owner to have CREATE on the schema.
-- Hold that grant ONLY inside this one atomic DO statement, then revoke.
do $ownership$
begin
 execute 'grant create on schema prumo_private to prumo_s0_signer';
 execute 'alter function prumo_private.gateway_validar_prova_s0(
  text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)
  owner to prumo_s0_signer';
 execute 'revoke create on schema prumo_private from prumo_s0_signer';
end $ownership$;

revoke all on function prumo_private.gateway_validar_prova_s0(
 text,uuid,uuid,uuid,uuid,bigint,text,text,uuid,uuid,bigint,uuid,text)
 from public,anon,authenticated,service_role,prumo_s0_gateway;

-- None of the pgcrypto/material grants are exposed as domain API operations.
-- prumo_s0_gateway still executes ONLY the two signed gateway entrypoints.
