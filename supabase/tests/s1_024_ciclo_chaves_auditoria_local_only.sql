-- S1-002/I24. FIXTURE SOMENTE CI/Docker local. NAO E MIGRATION.
-- Aplicar depois I20/I21/I22, sem banco hospedado, chaves reais ou deploy.
-- Custodia de chave continua NOLOGIN e separada do executor/nonce do I22.
begin;
do $guard$
begin
 if session_user <> 'postgres' or current_user <> 'postgres' then
  raise exception 'I24_LOCAL_POSTGRES_ONLY' using errcode='42501';
 end if;
end $guard$;

-- Chaves passam a ter versao CAS e carimbo de revogacao terminal.
set local role prumo_s1_i22_custodio;
alter table prumo_s1_signed_i20.chaves
 add column versao bigint not null default 1 check(versao>=1),
 add column revogado_em timestamptz null;
alter table prumo_s1_signed_i20.chaves
 add constraint i24_revogacao_consistente check (
  (ativo and revogado_em is null) or (not ativo and revogado_em is not null)
 );
reset role;

-- Historico sem bytes, HMAC, JWT, payload, dado pessoal ou texto livre.
create table prumo_s1_signed_i20.auditoria_chaves_i24 (
 id bigint generated always as identity primary key,
 chave_id uuid not null references prumo_s1_signed_i20.chaves(id),
 evento text not null check(evento in ('PROVISIONADA','REVOGADA')),
 versao bigint not null check(versao>=1),
 motivo_codigo text not null check(motivo_codigo in (
   'BOOTSTRAP_CI','ROTACAO_PLANEJADA','RISCO_COMPROMETIMENTO','FALHA_OPERACIONAL'
 )),
 ocorrido_em timestamptz not null default clock_timestamp(),
 constraint i24_evento_versao check(
  (evento='PROVISIONADA' and versao=1) or
  (evento='REVOGADA' and versao>=2))
);
create index i24_auditoria_por_chave on
 prumo_s1_signed_i20.auditoria_chaves_i24(chave_id,ocorrido_em);
revoke all on prumo_s1_signed_i20.auditoria_chaves_i24
 from public,anon,authenticated,service_role,
      prumo_s1_signed_login_ci,prumo_s1_i21_executor;
-- Acesso auditavel do runner administrativo ao historico, sem segredo.
grant select on prumo_s1_signed_i20.auditoria_chaves_i24 to postgres;
insert into prumo_s1_signed_i20.auditoria_chaves_i24
(chave_id,evento,versao,motivo_codigo)
select id,'PROVISIONADA',versao,'BOOTSTRAP_CI'
from prumo_s1_signed_i20.chaves where ativo;

grant create on schema prumo_s1_signed_i20 to prumo_s1_i22_custodio;
alter table prumo_s1_signed_i20.auditoria_chaves_i24
 owner to prumo_s1_i22_custodio;
revoke create on schema prumo_s1_signed_i20 from prumo_s1_i22_custodio;

-- Administracao: somente LOGIN postgres local. SECURITY DEFINER executa
-- com custodia (nao com superuser). Chave nunca aparece no retorno.
create function prumo_s1_signed_i20.provisionar_chave_i24(
 p_chave uuid, p_segredo bytea, p_inicio timestamptz,
 p_fim timestamptz, p_motivo text
) returns jsonb language plpgsql security definer set search_path='' as $fn$
declare v_agora timestamptz;
begin
 if session_user <> 'postgres' then
  raise exception 'I24_ADMIN_ONLY' using errcode='42501';end if;
 v_agora:=pg_catalog.clock_timestamp();
 if p_chave is null or p_segredo is null
  or pg_catalog.octet_length(p_segredo)<>32
  or p_inicio is null or p_fim is null
  or p_inicio < v_agora - interval '1 day'
  or p_inicio > v_agora + interval '1 day'
  or p_fim<=v_agora
  or p_fim>v_agora + interval '1 day'
  or p_fim<=p_inicio
  or p_motivo not in ('ROTACAO_PLANEJADA','RISCO_COMPROMETIMENTO','FALHA_OPERACIONAL')
 then raise exception 'I24_PROVISION_INVALID' using errcode='22023';end if;
 perform pg_catalog.pg_advisory_xact_lock(
   pg_catalog.hashtextextended('prumo-s1-key-v1:'||p_chave::text,0));
 insert into prumo_s1_signed_i20.chaves
  (id,segredo,valido_desde,valido_ate,ativo,versao,revogado_em)
 values(p_chave,p_segredo,p_inicio,p_fim,true,1,null);
 insert into prumo_s1_signed_i20.auditoria_chaves_i24
  (chave_id,evento,versao,motivo_codigo)
 values(p_chave,'PROVISIONADA',1,p_motivo);
 return pg_catalog.jsonb_build_object('outcome','PROVISIONADA',
   'chave_id',p_chave,'versao',1,'ativo',true);
end $fn$;

-- Revogacao terminal, CAS, lock identico ao de verificar_hmac no I22.
create function prumo_s1_signed_i20.revogar_chave_i24(
 p_chave uuid,p_versao bigint,p_motivo text
) returns jsonb language plpgsql security definer set search_path='' as $fn$
declare v_versao bigint;v_ativa boolean;v_revogada timestamptz;
begin
 if session_user <> 'postgres' then
  raise exception 'I24_ADMIN_ONLY' using errcode='42501';end if;
 if p_chave is null or p_versao is null or p_versao<1
  or p_motivo not in ('ROTACAO_PLANEJADA','RISCO_COMPROMETIMENTO','FALHA_OPERACIONAL')
 then raise exception 'I24_REVOKE_INVALID' using errcode='22023';end if;
 perform pg_catalog.pg_advisory_xact_lock(
  pg_catalog.hashtextextended('prumo-s1-key-v1:'||p_chave::text,0));
 select versao,ativo,revogado_em into v_versao,v_ativa,v_revogada
 from prumo_s1_signed_i20.chaves where id=p_chave for update;
 if not found then raise exception 'I24_KEY_NOT_FOUND' using errcode='22023';end if;
 if v_versao <> p_versao then
  raise exception 'I24_STALE_VERSION' using errcode='40001';end if;
 if not v_ativa or v_revogada is not null then
  raise exception 'I24_IRREVERSIBLE' using errcode='22023';end if;
 update prumo_s1_signed_i20.chaves
 set ativo=false,versao=v_versao+1,revogado_em=pg_catalog.clock_timestamp()
 where id=p_chave and versao=p_versao;
 insert into prumo_s1_signed_i20.auditoria_chaves_i24
  (chave_id,evento,versao,motivo_codigo)
 values(p_chave,'REVOGADA',v_versao+1,p_motivo);
 return pg_catalog.jsonb_build_object('outcome','REVOGADA',
  'chave_id',p_chave,'versao',v_versao+1,'ativo',false);
end $fn$;

-- Por padrao qualquer funcao recebe EXECUTE de PUBLIC. Revogar tudo antes
-- de publicar (mesma transacao), conceder especificamente apenas a postgres.
revoke all on function prumo_s1_signed_i20.provisionar_chave_i24(
 uuid,bytea,timestamptz,timestamptz,text)
 from public,anon,authenticated,service_role,prumo_s1_signed_login_ci,
 prumo_s1_i21_executor,prumo_s1_i22_custodio;
revoke all on function prumo_s1_signed_i20.revogar_chave_i24(uuid,bigint,text)
 from public,anon,authenticated,service_role,prumo_s1_signed_login_ci,
 prumo_s1_i21_executor,prumo_s1_i22_custodio;
grant execute on function prumo_s1_signed_i20.provisionar_chave_i24(
 uuid,bytea,timestamptz,timestamptz,text) to postgres;
grant execute on function prumo_s1_signed_i20.revogar_chave_i24(
 uuid,bigint,text) to postgres;

grant create on schema prumo_s1_signed_i20 to prumo_s1_i22_custodio;
alter function prumo_s1_signed_i20.provisionar_chave_i24(
 uuid,bytea,timestamptz,timestamptz,text) owner to prumo_s1_i22_custodio;
alter function prumo_s1_signed_i20.revogar_chave_i24(
 uuid,bigint,text) owner to prumo_s1_i22_custodio;
revoke create on schema prumo_s1_signed_i20 from prumo_s1_i22_custodio;

-- Revogar grants herdados e comprovar ausencia de APIs indevidas.
do $check$
begin
 if has_function_privilege('prumo_s1_signed_login_ci',
 'prumo_s1_signed_i20.revogar_chave_i24(uuid,bigint,text)','EXECUTE')
 or has_function_privilege('prumo_s1_i21_executor',
 'prumo_s1_signed_i20.revogar_chave_i24(uuid,bigint,text)','EXECUTE')
 or has_function_privilege('authenticated',
 'prumo_s1_signed_i20.provisionar_chave_i24(uuid,bytea,timestamptz,timestamptz,text)','EXECUTE')
 or has_table_privilege('prumo_s1_signed_login_ci',
 'prumo_s1_signed_i20.auditoria_chaves_i24','SELECT')
 or has_table_privilege('prumo_s1_i21_executor',
 'prumo_s1_signed_i20.auditoria_chaves_i24','INSERT')
 then raise exception 'I24_UNSAFE_ADMIN_ACL' using errcode='42501';end if;
end $check$;
commit;
