-- NEW Issue10 probes; synthetic SQL identity, no JWT/Auth transport claim.
\set ON_ERROR_STOP on
begin;
insert into auth.users(id) select ('a1000000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid from generate_series(1,5) i;
insert into public.atores(id) select id from auth.users;
-- TEAM_SEED_HERE
insert into public.concessionarias(id,nome_operacional) values
 ('a2000000-0000-4000-8000-000000000001','G3 synthetic A'),('a2000000-0000-4000-8000-000000000002','G3 synthetic B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('a1000000-0000-4000-8000-000000000001','a2000000-0000-4000-8000-000000000001','operador'),
 ('a1000000-0000-4000-8000-000000000002','a2000000-0000-4000-8000-000000000001','operador'),
 ('a1000000-0000-4000-8000-000000000002','a2000000-0000-4000-8000-000000000002','operador'),
 ('a1000000-0000-4000-8000-000000000003','a2000000-0000-4000-8000-000000000001','gestor'),
 ('a1000000-0000-4000-8000-000000000005','a2000000-0000-4000-8000-000000000001','responsavel');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('a3000000-0000-4000-8000-000000000001','a2000000-0000-4000-8000-000000000001','+5500000000000'),
 ('a3000000-0000-4000-8000-000000000002','a2000000-0000-4000-8000-000000000001','+5500000000001'),
 ('a3000000-0000-4000-8000-000000000003','a2000000-0000-4000-8000-000000000002','+5500000000000');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id)
 select ('a4000000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
  ('a2000000-0000-4000-8000-'||lpad((case when i=4 then 2 else 1 end)::text,12,'0'))::uuid,
  ('a3000000-0000-4000-8000-'||lpad((case when i in (1,2) then 1 when i=3 then 2 else 3 end)::text,12,'0'))::uuid
 from generate_series(1,4) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('a5000000-0000-4000-8000-'||right(c.id::text,12))::uuid,c.concessionaria_id,c.lead_id,c.id from public.ciclos_comerciais c;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id,encerrada_em)
 select h.concessionaria_id,h.id,
  ('a1000000-0000-4000-8000-'||lpad((case when right(h.id::text,12)::int=1 then 1 else 2 end)::text,12,'0'))::uuid,
  case when right(h.id::text,12)::int=2 then clock_timestamp() else null end
 from public.casos_humanos h;
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
 select ('a7000000-0000-4000-8000-'||right(id::text,12))::uuid,id,'g3-synthetic-'||right(id::text,12) from public.concessionarias;
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 select ('a8000000-0000-4000-8000-'||right(h.id::text,12))::uuid,h.concessionaria_id,h.lead_id,
 ('a7000000-0000-4000-8000-'||right(h.concessionaria_id::text,12))::uuid,h.id from public.casos_humanos h;
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id) values
 ('a8000000-0000-4000-8000-000000000005','a2000000-0000-4000-8000-000000000001',
  'a3000000-0000-4000-8000-000000000001','a7000000-0000-4000-8000-000000000001',null);
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,conteudo_sintetico,id_externo)
 select concessionaria_id,id,canal_id,caso_id,'entrada','synthetic G3 history','g3-'||id::text from public.conversas;
-- INSTALL_CANDIDATE_HERE
set local role authenticated;
select set_config('request.jwt.claim.sub','a1000000-0000-4000-8000-000000000001',true);
do $$ begin
 if (select count(*) from public.mensagens) <> (case when CANDIDATE_BOOLEAN then 3 else 1 end)
 then raise exception 'G3 history profile mismatch'; end if;
 if exists(select 1 from public.conversas where lead_id<>'a3000000-0000-4000-8000-000000000001')
 then raise exception 'G3 other contact/store leaked';end if;
end $$;
\echo 'PASS G3-01: positive current contact, other contact and same phone in other store denied'
\echo 'PROFILE G3-02: S0 expects 1 message; S1 I63 candidate expects 3 including old case and pre-case'
savepoint valid_write;
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,conteudo_sintetico,enviada_por)
 values('a2000000-0000-4000-8000-000000000001','a8000000-0000-4000-8000-000000000001',
 'a7000000-0000-4000-8000-000000000001','a5000000-0000-4000-8000-000000000001','saida','synthetic positive control',
 'a1000000-0000-4000-8000-000000000001');
rollback to valid_write;
do $$ begin
 begin
  insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,conteudo_sintetico,enviada_por)
   values('a2000000-0000-4000-8000-000000000001','a8000000-0000-4000-8000-000000000002',
   'a7000000-0000-4000-8000-000000000001','a5000000-0000-4000-8000-000000000002','saida','must be denied',
   'a1000000-0000-4000-8000-000000000001');
  raise exception 'old case write accepted';
 exception when insufficient_privilege then null;end;
end $$;
\echo 'PASS G3-03: current synthetic INSERT control accepted, old-case INSERT denied even with candidate historical SELECT'
select set_config('request.jwt.claim.sub','a1000000-0000-4000-8000-000000000003',true);
do $$ begin
 if (select count(*) from public.mensagens)<>(case when CANDIDATE_BOOLEAN then 2 else 4 end)
 then raise exception 'manager profile mismatch';end if;
 if CANDIDATE_BOOLEAN and exists(select 1 from public.conversas where lead_id='a3000000-0000-4000-8000-000000000002')
 then raise exception 'other team read';end if;
 begin
 insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,direcao,conteudo_sintetico,enviada_por)
 values('a2000000-0000-4000-8000-000000000001','a8000000-0000-4000-8000-000000000001',
 'a7000000-0000-4000-8000-000000000001','a5000000-0000-4000-8000-000000000001','saida','supervision cannot send',
 'a1000000-0000-4000-8000-000000000003');
 raise exception 'manager unassigned INSERT accepted';
 exception when insufficient_privilege then null;end;
end $$;
\echo 'PASS G3-04: manager cannot write unassigned case; S0 reads 4 store messages, S1 candidate reads 2 (current team case and pre-case); old case of other team denied'
select set_config('request.jwt.claim.sub','a1000000-0000-4000-8000-000000000005',true);
do $$ begin if exists(select 1 from public.mensagens) then raise exception 'responsavel blanket access';end if;end $$;
\echo 'PASS G3-05: responsavel label does not grant blanket conversation access'
reset role;
insert into auth.sessions(id,user_id) values('aa000000-0000-4000-8000-000000000001','a1000000-0000-4000-8000-000000000001');
delete from auth.sessions where id='aa000000-0000-4000-8000-000000000001';
set local role authenticated;
select set_config('request.jwt.claim.sub','a1000000-0000-4000-8000-000000000001',true);
do $$ begin if (select count(*) from public.mensagens)<>(case when CANDIDATE_BOOLEAN then 3 else 1 end)
 then raise exception 'unexpected SQL session behavior';end if;end $$;
\echo 'GAP G3-06: SQL history SELECT still works with same auth.uid after synthetic session deletion; no session-aware read gate demonstrated'
reset role;
update public.vinculos_papel_escopo set valido_ate=clock_timestamp() where ator_id='a1000000-0000-4000-8000-000000000001';
set local role authenticated;
do $$ begin if exists(select 1 from public.mensagens) then raise exception 'revoked store grant read';end if;end $$;
\echo 'PASS G3-07: revoked store grant blocks next history SELECT with same SQL identity'
reset role;
update public.vinculos_papel_escopo set valido_ate=null where ator_id='a1000000-0000-4000-8000-000000000001';
savepoint assignment_live;
update public.atribuicoes_humanas set encerrada_em=clock_timestamp()
 where operador_id='a1000000-0000-4000-8000-000000000001' and encerrada_em is null;
set local role authenticated;
do $$ begin if exists(select 1 from public.mensagens) then raise exception 'ended assignment history read';end if;end $$;
\echo 'PASS G3-08: ending the only current assignment removes contextual history, with store grant retained'
reset role;
rollback to assignment_live;
do $$ begin if CANDIDATE_BOOLEAN then
 update prumo_private.s1_gestor_operadores set encerrado_em=clock_timestamp()
 where operador_id='a1000000-0000-4000-8000-000000000001' and encerrado_em is null;
 end if;end $$;
set local role authenticated;
select set_config('request.jwt.claim.sub','a1000000-0000-4000-8000-000000000003',true);
do $$ begin if CANDIDATE_BOOLEAN and exists(select 1 from public.mensagens)
 then raise exception 'former manager history read';end if;end $$;
\echo 'PROFILE G3-09: S1 candidate denies former manager after team relation ends; S0 has no team relation model'
reset role;
rollback;
