-- I43 shared fixture, PG17 disposable ONLY. Caller owns BEGIN/ROLLBACK.
\ir s1_053_issue10_disponibilidade_local_only.sql
\ir s1_054_issue10_s0_prova_redistribuicao_local_only.sql
\ir s1_055_issue10_excecao_caso_local_only.sql

insert into auth.users(id)
 select ('62110000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,5) i;
insert into public.atores(id)
 select id from auth.users where id::text like '62110000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like '62110000-%';
-- M1 => origem C2 (grant A/B) + destino C3 (sem grant geral).
-- M4 => C5 de outra equipe com grant A.
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
 ('62110000-0000-4000-8000-000000000001','62110000-0000-4000-8000-000000000002'),
 ('62110000-0000-4000-8000-000000000001','62110000-0000-4000-8000-000000000003'),
 ('62110000-0000-4000-8000-000000000004','62110000-0000-4000-8000-000000000005');
insert into public.concessionarias(id,nome_operacional) values
 ('62220000-0000-4000-8000-000000000001','I42 ficticia A'),
 ('62220000-0000-4000-8000-000000000002','I42 ficticia B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel) values
 ('62110000-0000-4000-8000-000000000002','62220000-0000-4000-8000-000000000001','operador'),
 ('62110000-0000-4000-8000-000000000002','62220000-0000-4000-8000-000000000002','operador'),
 ('62110000-0000-4000-8000-000000000005','62220000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado) values
 ('62330000-0000-4000-8000-000000000001','62220000-0000-4000-8000-000000000001','+5581888804242'),
 ('62330000-0000-4000-8000-000000000002','62220000-0000-4000-8000-000000000001','+5581888804243'),
 ('62330000-0000-4000-8000-000000000003','62220000-0000-4000-8000-000000000002','+5581888804242');
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('62440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 case when i=4 then '62220000-0000-4000-8000-000000000002'::uuid
 else '62220000-0000-4000-8000-000000000001'::uuid end,
 case when i in (1,2) then '62330000-0000-4000-8000-000000000001'::uuid
 when i=3 then '62330000-0000-4000-8000-000000000002'::uuid
 else '62330000-0000-4000-8000-000000000003'::uuid end,
 'em atendimento pelo operador' from generate_series(1,4) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('62550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 c.concessionaria_id,c.lead_id,c.id
 from generate_series(1,4) i
 join public.ciclos_comerciais c
 on c.id=('62440000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.canais_loja(id,concessionaria_id,identificador_emissor) values
 ('62660000-0000-4000-8000-000000000001','62220000-0000-4000-8000-000000000001','S1-I42-A'),
 ('62660000-0000-4000-8000-000000000002','62220000-0000-4000-8000-000000000002','S1-I42-B');
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 select ('62770000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 h.concessionaria_id,h.lead_id,
 ('62660000-0000-4000-8000-'||lpad((case when i=4 then 2 else 1 end)::text,12,'0'))::uuid,
 h.id
 from generate_series(1,4) i
 join public.casos_humanos h
 on h.id=('62550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
 direcao,origem,conteudo_sintetico,id_externo)
 select co.concessionaria_id,co.id,co.canal_id,co.caso_id,
 'entrada','simulado','I42 mensagem historica '||i,'i42-ext-'||i
 from generate_series(1,4) i
 join public.conversas co
 on co.id=('62770000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
-- Caso 1: historico ENCERRADO do mesmo contato A.
-- Caso 2: titular atual C2, a transferir a C3 sem grant.
-- Caso 3: outro contato e outra equipe. Caso 4: outra loja mesmo telefone.
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select h.concessionaria_id,h.id,
 case when right(h.id::text,1)='3' then '62110000-0000-4000-8000-000000000005'::uuid
 else '62110000-0000-4000-8000-000000000002'::uuid end
 from public.casos_humanos h where h.id::text like '62550000-%';
update public.atribuicoes_humanas
 set encerrada_em=greatest(atribuida_em,pg_catalog.statement_timestamp())
 where caso_id='62550000-0000-4000-8000-000000000001';

do $t$ declare aid uuid; j jsonb;begin
 select id into aid from public.atribuicoes_humanas
 where caso_id='62550000-0000-4000-8000-000000000002' and encerrada_em is null;
 j:=prumo_private.s1_mover_excecao_caso_55(
 '62110000-0000-4000-8000-000000000001',
 '62220000-0000-4000-8000-000000000001',
 '62550000-0000-4000-8000-000000000002',
 aid,'62110000-0000-4000-8000-000000000003');
 if j->>'outcome'<>'MOVED_CASE_EXCEPTION' then
  raise exception 'I42-SETUP transfer exception failed %',j;end if;
end $t$;
