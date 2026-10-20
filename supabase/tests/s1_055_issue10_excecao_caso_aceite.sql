\set ON_ERROR_STOP on
-- ISSUE10 E55: somente PostgreSQL descartavel, rollback total.
begin;
insert into auth.users(id)
 select ('f1550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,7) i;
insert into public.atores(id) select id from auth.users
 where id::text like 'f1550000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like 'f1550000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 select 'f1550000-0000-4000-8000-000000000001',
 ('f1550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from (values(3),(4),(6),(7)) v(i);
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 values('f1550000-0000-4000-8000-000000000002',
        'f1550000-0000-4000-8000-000000000005');
insert into public.concessionarias(id,nome_operacional) values
 ('f2550000-0000-4000-8000-000000000001','I55 loja ficticia A'),
 ('f2550000-0000-4000-8000-000000000002','I55 loja ficticia B');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values
 ('f1550000-0000-4000-8000-000000000003',
  'f2550000-0000-4000-8000-000000000001','operador'),
 ('f1550000-0000-4000-8000-000000000003',
  'f2550000-0000-4000-8000-000000000002','operador'),
 ('f1550000-0000-4000-8000-000000000007',
  'f2550000-0000-4000-8000-000000000001','operador'),
 ('f1550000-0000-4000-8000-000000000005',
  'f2550000-0000-4000-8000-000000000001','operador');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
 values
 ('f3550000-0000-4000-8000-000000000001',
  'f2550000-0000-4000-8000-000000000001','i55-only-channel-A'),
 ('f3550000-0000-4000-8000-000000000002',
  'f2550000-0000-4000-8000-000000000002','i55-only-channel-B');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('f4550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('f2550000-0000-4000-8000-'||lpad((case when i=3 then 2 else 1 end)::text,12,'0'))::uuid,
 '+5581975500'||lpad(i::text,4,'0') from generate_series(1,3) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('f5550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 l.concessionaria_id,l.id,'em atendimento pelo operador'
 from generate_series(1,3) i join public.leads_loja l
 on l.id=('f4550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('f6550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 c.concessionaria_id,c.lead_id,c.id
 from generate_series(1,3) i join public.ciclos_comerciais c
 on c.id=('f5550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 select ('f7550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 h.concessionaria_id,h.lead_id,
 ('f3550000-0000-4000-8000-'||lpad((case when i=3 then 2 else 1 end)::text,12,'0'))::uuid,
 h.id
 from generate_series(1,3) i join public.casos_humanos h
 on h.id=('f6550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
 direcao,origem,conteudo_sintetico,id_externo)
 select co.concessionaria_id,co.id,co.canal_id,co.caso_id,
 'entrada','simulado','texto confidencial caso '||i,'e55-in-'||i
 from generate_series(1,3) i join public.conversas co
 on co.id=('f7550000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select concessionaria_id,id,'f1550000-0000-4000-8000-000000000003'
 from public.casos_humanos where id::text like 'f6550000-%';
\echo 'PASS EX55-01: tres casos em duas lojas, gestor unico e destino sem grant'
do $t$ declare a uuid;r jsonb;begin
 select id into a from public.atribuicoes_humanas
 where caso_id='f6550000-0000-4000-8000-000000000001' and encerrada_em is null;
 r:=prumo_private.s1_mover_excecao_caso_55(
 'f1550000-0000-4000-8000-000000000001',
 'f2550000-0000-4000-8000-000000000001',
 'f6550000-0000-4000-8000-000000000001',
 a,'f1550000-0000-4000-8000-000000000004');
 if r->>'outcome'<>'MOVED_CASE_EXCEPTION'
 or (select count(*) from public.atribuicoes_humanas
  where caso_id='f6550000-0000-4000-8000-000000000001'
  and operador_id='f1550000-0000-4000-8000-000000000004' and encerrada_em is null)<>1
 then raise exception 'EX55-02 failed %',r;end if;
end $t$;
\echo 'PASS EX55-02: transferiu caso A1 para membro sem grant A sem duplicar titular'
do $t$ begin
 if exists(select 1 from public.vinculos_papel_escopo
  where ator_id='f1550000-0000-4000-8000-000000000004')
 or (select count(*) from prumo_private.s1_excecoes_55
  where operador_id='f1550000-0000-4000-8000-000000000004' and revogada_em is null)<>1
 then raise exception 'EX55-03 concedeu loja inteira';end if;
end $t$;
\echo 'PASS EX55-03: zero grants gerais criados; entitlement unico por atribuicao'
do $t$ declare r jsonb;begin
 r:=prumo_private.s1_reconciliar_elegibilidade_vencida(20);
 if not exists(select 1 from public.atribuicoes_humanas
   where caso_id='f6550000-0000-4000-8000-000000000001'
    and operador_id='f1550000-0000-4000-8000-000000000004'
    and encerrada_em is null)
 then raise exception 'EX55-19 reconciliação legado tirou titular excepcional';end if;
end $t$;
\echo 'PASS EX55-19: reconciliador I3 legado nao remove titular excepcional'
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
'f1550000-0000-4000-8000-000000000004',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like 'f6550000-%')<>1
 or (select count(*) from public.atribuicoes_humanas
   where caso_id::text like 'f6550000-%' and encerrada_em is null)<>1
 or (select count(*) from public.conversas where id::text like 'f7550000-%')<>1
 or (select count(*) from public.mensagens
     where conteudo_sintetico like 'texto confidencial caso %')<>1
 or (select count(*) from public.s1_55_resumo_caso)<>1
 then raise exception 'EX55-04 RLS exibe outros casos/mensagens';end if;
end $t$;
\echo 'PASS EX55-04: RLS excepcional le 1 caso/atribuicao/conversa/mensagem/projecao'
do $t$ begin
 if (select count(*) from public.leads_loja
   where id::text like 'f4550000-%')<>0
 or (select count(*) from public.ciclos_comerciais
   where id::text like 'f5550000-%')<>0
 or (select count(*) from public.concessionarias
   where id::text like 'f2550000-%')<>0
 or (select count(*) from public.canais_loja
   where id::text like 'f3550000-%')<>0
 then raise exception 'EX55-05 leu colecao geral de concessionaria/lead/ciclo/canal';end if;
end $t$;
\echo 'PASS EX55-05: sem SELECT geral de loja, canal, lead ou ciclos; resumo minimo'
do $t$ begin
 insert into public.mensagens(
  concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,
  conteudo_sintetico,enviada_por)
 values('f2550000-0000-4000-8000-000000000001',
 'f7550000-0000-4000-8000-000000000001',
 'f3550000-0000-4000-8000-000000000001',
 'f6550000-0000-4000-8000-000000000001',
 'saida','simulado','resposta excepcional controlada',
 'f1550000-0000-4000-8000-000000000004');
 if (select count(*) from public.mensagens
  where conteudo_sintetico='resposta excepcional controlada')<>1 then
  raise exception 'EX55-06 nao gravou mensagem permitida';end if;
end $t$;
\echo 'PASS EX55-06: operador excepcional envia somente no caso transferido'
do $t$ begin
 begin
 insert into public.mensagens(
  concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,
  conteudo_sintetico,enviada_por)
 values('f2550000-0000-4000-8000-000000000001',
 'f7550000-0000-4000-8000-000000000002',
 'f3550000-0000-4000-8000-000000000001',
 'f6550000-0000-4000-8000-000000000002',
 'saida','simulado','ataque outro caso',
 'f1550000-0000-4000-8000-000000000004');
 raise exception 'EX55-07 cross-case write succeeded';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS EX55-07: escrita em outro caso da mesma loja negada'
reset role;
do $t$ declare a uuid;begin
 select id into a from public.atribuicoes_humanas
 where caso_id='f6550000-0000-4000-8000-000000000002' and encerrada_em is null;
 begin
 perform prumo_private.s1_mover_excecao_caso_55(
 'f1550000-0000-4000-8000-000000000001',
 'f2550000-0000-4000-8000-000000000001',
 'f6550000-0000-4000-8000-000000000002',
 a,'f1550000-0000-4000-8000-000000000005');
 raise exception 'EX55-08 concedeu ao operador de outra equipe';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS EX55-08: gestor nao transfere excepcionalmente a outra equipe'
do $t$ declare a uuid;begin
 select id into a from public.atribuicoes_humanas
 where caso_id='f6550000-0000-4000-8000-000000000002' and encerrada_em is null;
 begin
 perform prumo_private.s1_mover_excecao_caso_55(
 'f1550000-0000-4000-8000-000000000002',
 'f2550000-0000-4000-8000-000000000001',
 'f6550000-0000-4000-8000-000000000002',
 a,'f1550000-0000-4000-8000-000000000006');
 raise exception 'EX55-09 gestor externo moveu';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS EX55-09: gestor sem chefia da origem e destino recusado'
do $t$ declare a uuid;begin
 select id into a from public.atribuicoes_humanas
 where caso_id='f6550000-0000-4000-8000-000000000002' and encerrada_em is null;
 begin
 perform prumo_private.s1_mover_excecao_caso_55(
 'f1550000-0000-4000-8000-000000000001',
 'f2550000-0000-4000-8000-000000000002',
 'f6550000-0000-4000-8000-000000000002',
 a,'f1550000-0000-4000-8000-000000000006');
 raise exception 'EX55-10 cross-store accepted';
 exception when invalid_parameter_value then null;end;
end $t$;
\echo 'PASS EX55-10: caso A nao pode passar como caso da loja B'
do $t$ declare a uuid;begin
 select id into a from public.atribuicoes_humanas
 where caso_id='f6550000-0000-4000-8000-000000000002' and encerrada_em is null;
 begin
 perform prumo_private.s1_mover_excecao_caso_55(
 'f1550000-0000-4000-8000-000000000001',
 'f2550000-0000-4000-8000-000000000001',
 'f6550000-0000-4000-8000-000000000002',
 a,'f1550000-0000-4000-8000-000000000007');
 raise exception 'EX55-11 usou excecao em quem ja tem grant A';
 exception when invalid_parameter_value then null;end;
end $t$;
\echo 'PASS EX55-11: quem ja possui grant deve usar fluxo I12 normal'
do $t$ declare olda uuid;r jsonb;begin
 select id into olda from public.atribuicoes_humanas
 where caso_id='f6550000-0000-4000-8000-000000000001' and encerrada_em is null;
 r:=prumo_private.s1_mover_excecao_caso_55(
 'f1550000-0000-4000-8000-000000000001',
 'f2550000-0000-4000-8000-000000000001',
 'f6550000-0000-4000-8000-000000000001',
 olda,'f1550000-0000-4000-8000-000000000006');
 if r->>'outcome'<>'MOVED_CASE_EXCEPTION'
 or exists(select 1 from prumo_private.s1_excecoes_55
   where atribuicao_id=olda and revogada_em is null)
 then raise exception 'EX55-12 auto-revogacao da atribuicao anterior falhou';end if;
end $t$;
\echo 'PASS EX55-12: mover excepcionalmente de novo revoga entitlement anterior'
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
'f1550000-0000-4000-8000-000000000004',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like 'f6550000-%')<>0
 or (select count(*) from public.mensagens
      where conteudo_sintetico like 'texto confidencial caso %')<>0
 or (select count(*) from public.s1_55_resumo_caso)<>0 then
  raise exception 'EX55-13 operador anterior manteve caso';end if;
end $t$;
\echo 'PASS EX55-13: antigo titular nao le conversas apos transferencia'
select pg_catalog.set_config('request.jwt.claim.sub',
'f1550000-0000-4000-8000-000000000006',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like 'f6550000-%')<>1
 or (select count(*) from public.s1_55_resumo_caso)<>1 then
  raise exception 'EX55-14 novo titular nao recebeu acesso ao caso';end if;
end $t$;
\echo 'PASS EX55-14: novo titular recebe somente caso vigente'
reset role;
do $t$ declare x uuid;r jsonb;begin
 select id into x from prumo_private.s1_excecoes_55
 where operador_id='f1550000-0000-4000-8000-000000000006' and revogada_em is null;
 r:=prumo_private.s1_revogar_excecao_55(
 'f1550000-0000-4000-8000-000000000001',x);
 if r->>'outcome'<>'REVOKED_CASE_ACCESS' then
  raise exception 'EX55-15 revogacao explicit non applied %',r;end if;
end $t$;
\echo 'PASS EX55-15: gestor revoga entitlement especifico auditado'
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
'f1550000-0000-4000-8000-000000000006',true);
do $t$ begin
 if (select count(*) from public.casos_humanos where id::text like 'f6550000-%')<>0
 or (select count(*) from public.mensagens
      where conteudo_sintetico like 'texto confidencial caso %')<>0
 or (select count(*) from public.s1_55_resumo_caso)<>0 then
  raise exception 'EX55-16 revogado ainda le o caso';end if;
end $t$;
\echo 'PASS EX55-16: revogacao explicita corta leitura mesmo com atribuicao atual'
do $t$ begin
 begin
 insert into public.mensagens(
  concessionaria_id,conversa_id,canal_id,caso_id,direcao,origem,
  conteudo_sintetico,enviada_por)
 values('f2550000-0000-4000-8000-000000000001',
 'f7550000-0000-4000-8000-000000000001',
 'f3550000-0000-4000-8000-000000000001',
 'f6550000-0000-4000-8000-000000000001',
 'saida','simulado','tentativa apos revogacao',
 'f1550000-0000-4000-8000-000000000006');
 raise exception 'EX55-20 revogado conseguiu enviar';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS EX55-20: revogado nao consegue inserir novas mensagens'
reset role;
do $t$ begin
 if (select count(*) from prumo_private.s1_movimentos_manuais_historico
   where caso_id='f6550000-0000-4000-8000-000000000001')<>2
 or (select count(*) from prumo_private.s1_excecoes_eventos_55)<>4
 or (select count(*) from public.atribuicoes_humanas
   where caso_id='f6550000-0000-4000-8000-000000000001' and encerrada_em is null)<>1 then
  raise exception 'EX55-17 historicos/titular divergentes';end if;
end $t$;
\echo 'PASS EX55-17: historico quatro eventos, duas transferencias, um titular'
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
'f1550000-0000-4000-8000-000000000004',true);
do $t$ begin
 begin
 perform prumo_private.s1_mover_excecao_caso_55(
 'f1550000-0000-4000-8000-000000000001',
 'f2550000-0000-4000-8000-000000000001',
 'f6550000-0000-4000-8000-000000000002',
 '00000000-0000-4000-8000-000000000001',
 'f1550000-0000-4000-8000-000000000004');
 raise exception 'EX55-18 RPC privada abriu';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS EX55-18: authenticated nao executa funcoes administrativas'
reset role;
rollback;
