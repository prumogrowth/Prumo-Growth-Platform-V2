\set ON_ERROR_STOP on
-- I60: all changes including S1 candidate RLS roll back.
begin;
\ir s1_062_setup_historico_excecao_local_only.sql
\ir s1_062_proto_rls_excecao_local_only.sql
\ir s1_061_proto_rls_equipe_local_only.sql
\ir s1_063_proto_rls_unificada_local_only.sql
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
values('63430000-0000-4000-8000-000000000001',
'62220000-0000-4000-8000-000000000001','+5581888960001');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
values
('63440000-0000-4000-8000-000000000001','62220000-0000-4000-8000-000000000001','62330000-0000-4000-8000-000000000001','62660000-0000-4000-8000-000000000001',null),
('63440000-0000-4000-8000-000000000002','62220000-0000-4000-8000-000000000001','62330000-0000-4000-8000-000000000002','62660000-0000-4000-8000-000000000001',null),
('63440000-0000-4000-8000-000000000003','62220000-0000-4000-8000-000000000002','62330000-0000-4000-8000-000000000003','62660000-0000-4000-8000-000000000002',null),
('63440000-0000-4000-8000-000000000004','62220000-0000-4000-8000-000000000001','63430000-0000-4000-8000-000000000001','62660000-0000-4000-8000-000000000001',null);
insert into public.mensagens(id,concessionaria_id,conversa_id,canal_id,caso_id,
 direcao,origem,conteudo_sintetico,id_externo)
select ('63450000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 co.concessionaria_id,co.id,co.canal_id,null,'entrada','simulado',
 'I60 pre-case synthetic '||i,'i60-pg-'||i
from generate_series(1,4) i join public.conversas co on co.id=
 ('63440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
set local role authenticated;
select set_config('request.jwt.claim.sub','62110000-0000-4000-8000-000000000003',true);
do $t$ begin
 if exists(select 1 from public.conversas where id::text like '63440000-%')
 or exists(select 1 from public.mensagens where id::text like '63450000-%')
 then raise exception 'I60 baseline exposed case-less history';end if;
end $t$;
reset role;
\echo 'PASS I60-01: pre-candidate restrictive policies deny case-less history'
\ir s1_084_proto_rls_contexto_sem_caso_local_only.sql
set local role authenticated;
select set_config('request.jwt.claim.sub','62110000-0000-4000-8000-000000000003',true);
do $t$ begin
 if (select count(*) from public.conversas where id::text like '63440000-%')<>1
 or (select count(*) from public.mensagens where id::text like '63450000-%')<>1
 then raise exception 'I60 exception leaked other contact/store or lost history';end if;
end $t$;
\echo 'PASS I60-02: exceptional consultant reads pre-case history of exact contact/store only'
select set_config('request.jwt.claim.sub','62110000-0000-4000-8000-000000000001',true);
do $t$ begin
 if (select count(*) from public.conversas where id::text like '63440000-%')<>2
 then raise exception 'I60 manager team scope incorrect';end if;
end $t$;
select set_config('request.jwt.claim.sub','62110000-0000-4000-8000-000000000004',true);
do $t$ begin
 if (select count(*) from public.conversas where id::text like '63440000-%')<>1
 then raise exception 'I60 other team manager leaked data';end if;
end $t$;
\echo 'PASS I60-03: two managers see only team-history, including cross-store difference'
select set_config('request.jwt.claim.sub','62110000-0000-4000-8000-000000000002',true);
do $t$ begin
 if (select count(*) from public.conversas where id::text like '63440000-%')<>1
 or not exists(select 1 from public.conversas
 where id='63440000-0000-4000-8000-000000000003')
 then raise exception 'I60 former consultant incorrectly read old store';end if;
end $t$;
\echo 'PASS I60-04: former consultant sees only currently held case contact'
select set_config('request.jwt.claim.sub','62110000-0000-4000-8000-000000000003',true);
do $t$ begin
 begin
  insert into public.mensagens(concessionaria_id,conversa_id,canal_id,
   direcao,origem,conteudo_sintetico,enviada_por)
  values('62220000-0000-4000-8000-000000000001',
   '63440000-0000-4000-8000-000000000001',
   '62660000-0000-4000-8000-000000000001',
   'saida','simulado','I60 forbidden outbound',
   '62110000-0000-4000-8000-000000000003');
  raise exception 'I60 sent without human case';
 exception when check_violation or insufficient_privilege then null;end;
end $t$;
\echo 'PASS I60-05: read-only pre-case access never grants outbound message'
reset role;
select prumo_private.s1_revogar_excecao_55(
 '62110000-0000-4000-8000-000000000001',
 (select id from prumo_private.s1_excecoes_55
  where operador_id='62110000-0000-4000-8000-000000000003' and revogada_em is null));
set local role authenticated;
select set_config('request.jwt.claim.sub','62110000-0000-4000-8000-000000000003',true);
do $t$ begin
 if exists(select 1 from public.conversas where id::text like '63440000-%')
 or exists(select 1 from public.mensagens where id::text like '63450000-%')
 then raise exception 'I60 revoked exception still reads history';end if;
end $t$;
reset role;
do $t$ begin
 if (select count(*) from pg_catalog.pg_policies
 where schemaname='public' and policyname like 's1_60_%')<>3
 then raise exception 'I60 candidate policy count invalid';end if;
end $t$;
\echo 'PASS I60-06: revocation rescopes same JWT and three candidate policies isolated'
rollback;
\echo 'I60 6/6 PG17 candidate tests; all rolled back'
