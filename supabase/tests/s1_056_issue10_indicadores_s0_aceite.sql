\set ON_ERROR_STOP on
-- S0/S1 issue10 I36, fixture toda revertida no final.
begin;
insert into auth.users(id) select ('f1560000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,4) i;
insert into public.atores(id) select id from auth.users where id::text like 'f1560000-%';
insert into public.equipe_prumo_s1(ator_id,estado)
 select id,'ativo' from public.atores where id::text like 'f1560000-%';
insert into prumo_private.s1_gestor_operadores(gestor_id,operador_id) values
 ('f1560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002'),
 ('f1560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000003');
insert into public.concessionarias(id,nome_operacional)
 values('f2560000-0000-4000-8000-000000000001','I56 loja de mensagens simuladas');
insert into public.canais_loja(id,concessionaria_id,identificador_emissor)
 values('f3560000-0000-4000-8000-000000000001',
 'f2560000-0000-4000-8000-000000000001','i56-only-whatsapp-simulated');
insert into public.vinculos_papel_escopo(ator_id,concessionaria_id,papel)
 values
 ('f1560000-0000-4000-8000-000000000002',
 'f2560000-0000-4000-8000-000000000001','operador'),
 ('f1560000-0000-4000-8000-000000000003',
 'f2560000-0000-4000-8000-000000000001','operador');
insert into public.leads_loja(id,concessionaria_id,telefone_cliente_normalizado)
 select ('f4560000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'f2560000-0000-4000-8000-000000000001',
 '+5581975600'||lpad(i::text,4,'0') from generate_series(1,2) i;
insert into public.ciclos_comerciais(id,concessionaria_id,lead_id,status_comercial)
 select ('f5560000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'f2560000-0000-4000-8000-000000000001',
 ('f4560000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,'em atendimento pelo operador'
 from generate_series(1,2) i;
insert into public.casos_humanos(id,concessionaria_id,lead_id,ciclo_id)
 select ('f6560000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'f2560000-0000-4000-8000-000000000001',
 ('f4560000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 ('f5560000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid from generate_series(1,2) i;
insert into public.conversas(id,concessionaria_id,lead_id,canal_id,caso_id)
 select ('f7560000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'f2560000-0000-4000-8000-000000000001',
 ('f4560000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid,
 'f3560000-0000-4000-8000-000000000001',
 ('f6560000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid
 from generate_series(1,2) i;
insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
 select concessionaria_id,id,'f1560000-0000-4000-8000-000000000002'
 from public.casos_humanos where id::text like 'f6560000-%';
\echo 'PASS MSG56-01: dois casos e duas atribuicoes sintéticas, leitura ainda ausente'
do $t$ declare j jsonb;begin
 j:=prumo_private.s0_indicador_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001',
 'f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001',
 'f1560000-0000-4000-8000-000000000002');
 if j->>'state'<>'NONE' or (j->>'unread_count')::int<>0 then
 raise exception 'MSG56-02 contagem sem mensagem %',j;end if;
end $t$;
\echo 'PASS MSG56-02: sem mensagem = indicador nenhum'
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
direcao,origem,conteudo_sintetico,id_externo)
 values
 ('f2560000-0000-4000-8000-000000000001','f7560000-0000-4000-8000-000000000001',
  'f3560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
  'entrada','simulado','primeira mensagem','msg56-in-1'),
 ('f2560000-0000-4000-8000-000000000001','f7560000-0000-4000-8000-000000000001',
  'f3560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
  'entrada','simulado','segunda mensagem','msg56-in-2'),
 ('f2560000-0000-4000-8000-000000000001','f7560000-0000-4000-8000-000000000002',
  'f3560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000002',
  'entrada','simulado','outra conversa','msg56-in-other');
do $t$ declare j jsonb;begin
 j:=prumo_private.s0_indicador_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002');
 if j->>'state'<>'COUNT' or (j->>'unread_count')::int<>2 then
 raise exception 'MSG56-03 deve ter count2 %',j;end if;
end $t$;
\echo 'PASS MSG56-03: duas entradas nao lidas => COUNT 2, outra conversa nao soma'
do $t$ declare j jsonb;begin
 j:=prumo_private.s0_visita_supervisor_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000001');
 if j->>'outcome'<>'SUPERVISOR_VIEWED'
 or (select count(*) from prumo_private.s0_leituras_operador_56)<>0 then
 raise exception 'MSG56-04 gestor marcou leitura pelo op %',j;end if;
end $t$;
\echo 'PASS MSG56-04: supervisor consulta sem marcar leitura do operador'
do $t$ declare j jsonb; m uuid;begin
 select id into m from public.mensagens where id_externo='msg56-in-1';
 j:=prumo_private.s0_marcar_leitura_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002',m);
 if (j->>'read_added')::int<>1 then raise exception 'MSG56-05 %',j;end if;
 j:=prumo_private.s0_indicador_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002');
 if j->>'state'<>'COUNT' or (j->>'unread_count')::int<>1 then
 raise exception 'MSG56-05 COUNT1 %',j;end if;
end $t$;
\echo 'PASS MSG56-05: leitura parcial => COUNT 1 prevalece sobre DOT'
do $t$ declare j jsonb;m uuid;begin
 select id into m from public.mensagens where id_externo='msg56-in-2';
 j:=prumo_private.s0_marcar_leitura_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002',m);
 if (j->>'read_added')::int<>1 then raise exception 'MSG56-06 %',j;end if;
 j:=prumo_private.s0_indicador_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002');
 if j->>'state'<>'DOT' or (j->>'unread_count')::int<>0 then
 raise exception 'MSG56-06 bolinha sem numero %',j;end if;
end $t$;
\echo 'PASS MSG56-06: todas lidas sem resposta => DOT sem numero'
do $t$ declare j jsonb;m uuid;begin
 select id into m from public.mensagens where id_externo='msg56-in-2';
 j:=prumo_private.s0_marcar_leitura_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002',m);
 if (j->>'read_added')::int<>0 then raise exception 'MSG56-07 replay %',j;end if;
end $t$;
\echo 'PASS MSG56-07: leitura idempotente'
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
direcao,origem,conteudo_sintetico,enviada_por)
values('f2560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001',
 'f3560000-0000-4000-8000-000000000001',
 'f6560000-0000-4000-8000-000000000001',
 'saida','simulado','resposta humana sintetica',
 'f1560000-0000-4000-8000-000000000002');
do $t$ declare j jsonb;begin
 j:=prumo_private.s0_indicador_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002');
 if j->>'state'<>'NONE' then raise exception 'MSG56-08 ainda DOT %',j;end if;
end $t$;
\echo 'PASS MSG56-08: resposta humana posterior limpa DOT => NONE'
insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
direcao,origem,conteudo_sintetico,id_externo)
values('f2560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001',
 'f3560000-0000-4000-8000-000000000001',
 'f6560000-0000-4000-8000-000000000001',
 'entrada','simulado','nova mensagem','msg56-in-3');
do $t$ declare j jsonb;begin
 j:=prumo_private.s0_indicador_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002');
 if j->>'state'<>'COUNT' or (j->>'unread_count')::int<>1
 then raise exception 'MSG56-09 %',j;end if;
end $t$;
\echo 'PASS MSG56-09: novo inbound apos resposta reabre COUNT1'
do $t$ declare j jsonb;begin
 perform prumo_private.s0_visita_supervisor_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000001');
 j:=prumo_private.s0_indicador_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002');
 if j->>'state'<>'COUNT' or (j->>'unread_count')::int<>1 then
 raise exception 'MSG56-10 supervisao marcou mensagem %',j;end if;
end $t$;
\echo 'PASS MSG56-10: supervisao posterior nao altera o contador'
do $t$ declare j jsonb;m uuid;begin
 select id into m from public.mensagens where id_externo='msg56-in-3';
 perform prumo_private.s0_marcar_leitura_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002',m);
 j:=prumo_private.s0_indicador_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002');
 if j->>'state'<>'DOT' then raise exception 'MSG56-11 %',j;end if;
end $t$;
\echo 'PASS MSG56-11: nova mensagem lida ainda sem resposta => DOT'
do $t$ declare m uuid;begin
 select id into m from public.mensagens where id_externo='msg56-in-other';
 begin
 perform prumo_private.s0_marcar_leitura_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002',m);
 raise exception 'MSG56-12 leitura de outra conversa accepted';
 exception when invalid_parameter_value then null;end;
end $t$;
\echo 'PASS MSG56-12: marcador de outra conversa nao entra no mesmo caso'
do $t$ declare m uuid;begin
 select id into m from public.mensagens where id_externo='msg56-in-3';
 begin
 perform prumo_private.s0_marcar_leitura_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000004',m);
 raise exception 'MSG56-13 leitura por outro operador accepted';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS MSG56-13: operador nao titular nao marca leitura alheia'
do $t$ begin
 begin
 perform prumo_private.s0_visita_supervisor_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000004');
 raise exception 'MSG56-14 outro gestor viu caso';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS MSG56-14: supervisao externa recusada'
do $t$ declare a uuid;j jsonb;begin
 select id into a from public.atribuicoes_humanas
 where caso_id='f6560000-0000-4000-8000-000000000001' and encerrada_em is null;
 j:=prumo_private.s1_mover_atendimento_da_equipe(
 'f1560000-0000-4000-8000-000000000001',
 'f2560000-0000-4000-8000-000000000001',
 'f6560000-0000-4000-8000-000000000001',
 a,'f1560000-0000-4000-8000-000000000003');
 if j->>'outcome'<>'MOVED' then raise exception 'MSG56-15 %',j;end if;
end $t$;
\echo 'PASS MSG56-15: atribuicao transferida normalmente dentro da equipe'
do $t$ declare j jsonb;begin
 j:=prumo_private.s0_indicador_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000003');
 if j->>'state'<>'COUNT' or (j->>'unread_count')::int<>3 then
 raise exception 'MSG56-16 novo titular deveria herdar mensagens nao lidas %',j;end if;
end $t$;
\echo 'PASS MSG56-16: novo titular inicia marcador independente (premissa testada)'
do $t$ begin
 begin
 perform prumo_private.s0_indicador_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000002');
 raise exception 'MSG56-17 antigo titular acessou indicador';
 exception when insufficient_privilege then null;end;
end $t$;
\echo 'PASS MSG56-17: antigo titular nao le projecao apos movimento'
set local role authenticated;
do $t$ begin
 begin
 perform prumo_private.s0_marcar_leitura_operador_fixture_56(
 'f2560000-0000-4000-8000-000000000001','f6560000-0000-4000-8000-000000000001',
 'f7560000-0000-4000-8000-000000000001','f1560000-0000-4000-8000-000000000003',
 '00000000-0000-4000-8000-000000000001');
 raise exception 'MSG56-18 RPC internal openly available';
 exception when insufficient_privilege then null;end;
end $t$;
reset role;
\echo 'PASS MSG56-18: leitura e projecao nao sao RPC publicas'
rollback;
