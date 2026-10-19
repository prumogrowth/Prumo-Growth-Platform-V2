\set ON_ERROR_STOP on
-- I15: cenários GUC sintéticos, SEM assinatura JWT nem REST/GoTrue.
-- Se a migration 052 permitir sessão alheia/revogada, o teste falha.
begin;
insert into auth.users(id) values
 ('f1150000-0000-4000-8000-000000000001'),
 ('f1150000-0000-4000-8000-000000000002'),
 ('f1150000-0000-4000-8000-000000000003');
insert into public.atores(id)
 select id from auth.users where id::text like 'f1150000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like 'f1150000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('f1150000-0000-4000-8000-000000000001',
        'f1150000-0000-4000-8000-000000000002');
insert into public.concessionarias(id,nome_operacional) values
 ('f2150000-0000-4000-8000-000000000001','S1 I15 A'),
 ('f2150000-0000-4000-8000-000000000002','S1 I15 B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('f1150000-0000-4000-8000-000000000002','f2150000-0000-4000-8000-000000000001','operador'),
 ('f1150000-0000-4000-8000-000000000002','f2150000-0000-4000-8000-000000000002','operador');
insert into auth.sessions(id,user_id) values
 ('f9150000-0000-4000-8000-000000000001','f1150000-0000-4000-8000-000000000001'),
 ('f9150000-0000-4000-8000-000000000002','f1150000-0000-4000-8000-000000000003');
\echo 'PASS S1V-01: atores, chefia e duas concessoes em fixture descartavel'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub','f1150000-0000-4000-8000-000000000001',true);
do $t$ begin
 begin
  perform prumo_s1_interface.s1_pausar_operador_sessao(
   'f1150000-0000-4000-8000-000000000002','AUSENCIA_TEMPORARIA');
  raise exception 'LEGACY_SEM_CLAIMS_FOI_ACEITO';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1V-02: somente GUC legacy role/sub sem JSON nao autentica'

select pg_catalog.set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f1150000-0000-4000-8000-000000000001"}',true);
do $t$ begin
 begin
  perform prumo_s1_interface.s1_pausar_operador_sessao(
   'f1150000-0000-4000-8000-000000000002','AUSENCIA_TEMPORARIA');
  raise exception 'SEM_SESSION_ID_FOI_ACEITO';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1V-03: falta de session_id rejeitada'

select pg_catalog.set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f1150000-0000-4000-8000-000000000003","session_id":"f9150000-0000-4000-8000-000000000001"}',true);
do $t$ begin
 begin
  perform prumo_s1_interface.s1_pausar_operador_sessao(
   'f1150000-0000-4000-8000-000000000002','AUSENCIA_TEMPORARIA');
  raise exception 'CLAIM_SUB_DIVERGENTE_FOI_ACEITO';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1V-04: sub divergente de auth.uid() rejeitado'

select pg_catalog.set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f1150000-0000-4000-8000-000000000001","session_id":"f9150000-0000-4000-8000-000000000099"}',true);
do $t$ begin
 begin
  perform prumo_s1_interface.s1_pausar_operador_sessao(
   'f1150000-0000-4000-8000-000000000002','AUSENCIA_TEMPORARIA');
  raise exception 'SESSAO_INEXISTENTE_FOI_ACEITA';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1V-05: sessao inexistente rejeitada'

select pg_catalog.set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f1150000-0000-4000-8000-000000000001","session_id":"f9150000-0000-4000-8000-000000000002"}',true);
do $t$ begin
 begin
  perform prumo_s1_interface.s1_pausar_operador_sessao(
   'f1150000-0000-4000-8000-000000000002','AUSENCIA_TEMPORARIA');
  raise exception 'SESSAO_DE_OUTRO_USUARIO_FOI_ACEITA';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1V-06: sessao de outro usuario rejeitada'

select pg_catalog.set_config('request.jwt.claims',
 '{"role":"service_role","sub":"f1150000-0000-4000-8000-000000000001","session_id":"f9150000-0000-4000-8000-000000000001"}',true);
do $t$ begin
 begin
  perform prumo_s1_interface.s1_pausar_operador_sessao(
   'f1150000-0000-4000-8000-000000000002','AUSENCIA_TEMPORARIA');
  raise exception 'CLAIM_SERVICE_ROLE_FOI_ACEITA';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1V-07: role claim indevida rejeitada'

select pg_catalog.set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f1150000-0000-4000-8000-000000000001","session_id":"f9150000-0000-4000-8000-000000000001"}',true);
select prumo_s1_interface.s1_pausar_operador_sessao(
 'f1150000-0000-4000-8000-000000000002','AUSENCIA_TEMPORARIA');
reset role;
do $t$ begin
 if (select estado from public.equipe_prumo_s1
  where ator_id='f1150000-0000-4000-8000-000000000002')<>'suspenso'
 or (select count(*) from public.vinculos_papel_escopo
  where ator_id='f1150000-0000-4000-8000-000000000002')<>2
 or (select count(*) from prumo_private.s1_pausas_operadores_historico
  where operador_id='f1150000-0000-4000-8000-000000000002'
   and solicitante_id='f1150000-0000-4000-8000-000000000001'
   and acao='PAUSA_GLOBAL')<>1
 then raise exception 'SESSAO_VALIDA_NAO_OPEROU_COM_TRILHA_E_GRANTS';end if;
end $t$;
\echo 'PASS S1V-08: sessao vinculada pausa global com autoria e grants intactos'

delete from auth.sessions where id='f9150000-0000-4000-8000-000000000001';
set local role authenticated;
do $t$ begin
 begin
  perform prumo_s1_interface.s1_reativar_operador_sessao(
   'f1150000-0000-4000-8000-000000000002');
  raise exception 'SESSAO_REVOGADA_FOI_ACEITA';
 exception when insufficient_privilege then null;end;
end $t$;
reset role;
do $t$ begin
 if (select estado from public.equipe_prumo_s1 where ator_id=
 'f1150000-0000-4000-8000-000000000002')<>'suspenso'
 then raise exception 'REVOGACAO_ALTEROU_ESTADO';end if;
end $t$;
\echo 'PASS S1V-09: DELETE da sessao impede reativacao sem mutacao'

insert into auth.sessions(id,user_id) values
 ('f9150000-0000-4000-8000-000000000003','f1150000-0000-4000-8000-000000000001');
set local role authenticated;
select pg_catalog.set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f1150000-0000-4000-8000-000000000001","session_id":"f9150000-0000-4000-8000-000000000003"}',true);
select prumo_s1_interface.s1_reativar_operador_sessao(
 'f1150000-0000-4000-8000-000000000002');
reset role;
do $t$ begin
 if (select estado from public.equipe_prumo_s1 where ator_id=
 'f1150000-0000-4000-8000-000000000002')<>'ativo'
 or (select count(*) from prumo_private.s1_pausas_operadores_historico
  where operador_id='f1150000-0000-4000-8000-000000000002')<>2
 then raise exception 'NOVO_LOGIN_NAO_REATIVOU_COM_AUDITORIA';end if;
end $t$;
\echo 'PASS S1V-10: nova sessao valida reativa sem restaurar carteira'

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 'f1150000-0000-4000-8000-000000000003',true);
select pg_catalog.set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f1150000-0000-4000-8000-000000000003","session_id":"f9150000-0000-4000-8000-000000000002","user_metadata":{"papel":"gestor"},"app_metadata":{"papel":"responsavel"}}',true);
do $t$ begin
 begin
  perform prumo_s1_interface.s1_pausar_operador_sessao(
   'f1150000-0000-4000-8000-000000000002','AUSENCIA_TEMPORARIA');
  raise exception 'SESSAO_ALHEIA_COM_METADATA_FOI_ACEITA';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1V-11: usuario sem chefia nao ganha alçada por metadata'

select pg_catalog.set_config('request.jwt.claims',
 '{"role":"authenticated","sub":"f1150000-0000-4000-8000-000000000003","session_id":"invalido"}',true);
do $t$ begin
 begin
  perform prumo_s1_interface.s1_pausar_operador_sessao(
   'f1150000-0000-4000-8000-000000000002','AUSENCIA_TEMPORARIA');
  raise exception 'SESSION_ID_MALFORMADO_FOI_ACEITO';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS S1V-12: session_id malformado falha fechado'

reset role;
do $t$ begin
 if pg_catalog.has_schema_privilege('authenticated','prumo_private','USAGE')
 or not pg_catalog.has_schema_privilege('authenticated','prumo_s1_interface','USAGE')
 or pg_catalog.has_schema_privilege('anon','prumo_s1_interface','USAGE')
 or pg_catalog.has_schema_privilege('service_role','prumo_s1_interface','USAGE')
 or pg_catalog.has_table_privilege('authenticated','auth.sessions','SELECT')
 or pg_catalog.has_function_privilege('authenticated',
   'prumo_private.s1_exigir_identidade_sessao()','EXECUTE')
 or exists(select 1 from pg_catalog.pg_proc p where
   p.pronamespace='public'::regnamespace and p.proname like 's1_%_sessao')
 then raise exception 'ACL_SESSOES_OU_SCHEMA_EXPANDIDO';end if;
end $t$;
\echo 'PASS S1V-13: nenhum privilegio adicional de sessao ou RPC em public'
rollback;
