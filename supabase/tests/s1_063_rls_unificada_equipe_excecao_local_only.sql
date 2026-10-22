\set ON_ERROR_STOP on
-- S1-002 I43: ensaio da intersecao real de policies I41 (RESTRICTIVE)
-- e I42 (excecao por caso e historico do mesmo contato).
-- BEGIN/ROLLBACK, PG17 descartavel apenas. Nenhuma migration S0.
begin;
\ir s1_062_setup_historico_excecao_local_only.sql
\ir s1_062_proto_rls_excecao_local_only.sql

-- Primeiro: entitlement I42 isolado permite ler caso atual e historico.
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '62110000-0000-4000-8000-000000000003',true);
do $t$ begin
 if (select count(*) from public.casos_humanos
  where id::text like '62550000-%')<>2
 or (select count(*) from public.s1_62_historico_contato_resumo)<>2
 then raise exception 'I43-BASE I42 nao deu historico';end if;
end $t$;
reset role;

-- Aplicar exatamente as policies I41 de supervisor restritivo, que antes
-- nunca haviam sido compostas com a excecao I42. Funcao so cobre grant
-- de loja, propria atribuicao ou Gestor da equipe.
\ir s1_061_proto_rls_equipe_local_only.sql

set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '62110000-0000-4000-8000-000000000003',true);
do $t$ begin
 if exists(select 1 from public.casos_humanos
   where id::text like '62550000-%')
 or exists(select 1 from public.conversas
   where id::text like '62770000-%')
 or exists(select 1 from public.mensagens
   where conteudo_sintetico like 'I42 mensagem historica %')
 then raise exception 'I43-RED nao reproduziu bloqueio interpolicy';end if;
 if (select count(*) from public.s1_62_historico_contato_resumo)<>2
 then raise exception 'I43-RED view nao reproduziu divergencia de objetos';end if;
end $t$;
reset role;
\echo 'OBSERVED I43-RED: I41 restrictive bloqueia o caso excepcional I42 mesmo com resumo acessivel'

-- A politica final NUNCA pode ser apenas "I41 AND I42" nem substituir
-- toda a RLS da S0 por OR amplo: o gate deve ser por linha e caso.
-- Ensaio em transacao: trocar APENAS restrictive da I41 por um predicado
-- que suporta caso normal/de equipe OU acesso excepcional valido do contato.
\ir s1_063_proto_rls_unificada_local_only.sql

-- C3: excepcional SEM GRANT de loja. Seu escopo e o contato da excecao.
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '62110000-0000-4000-8000-000000000003',true);
do $t$ begin
 if (select count(*) from public.casos_humanos
     where id::text like '62550000-%')<>2
 or (select count(*) from public.conversas
     where id::text like '62770000-%')<>2
 or (select count(*) from public.mensagens
     where conteudo_sintetico like 'I42 mensagem historica %')<>2
 or (select count(*) from public.atribuicoes_humanas
     where caso_id::text like '62550000-%')<>1
 or (select count(*) from public.s1_62_historico_contato_resumo)<>2
 or (select count(*) from public.s1_55_resumo_caso)<>1
 then raise exception 'I43-01 historico excepcional sem acesso integrado';end if;
 if exists(select 1 from public.casos_humanos
   where id in ('62550000-0000-4000-8000-000000000003',
                '62550000-0000-4000-8000-000000000004'))
 or exists(select 1 from public.leads_loja where id::text like '62330000-%')
 or exists(select 1 from public.ciclos_comerciais where id::text like '62440000-%')
 or exists(select 1 from public.concessionarias where id::text like '62220000-%')
 or exists(select 1 from public.canais_loja where id::text like '62660000-%')
 then raise exception 'I43-01 acesso generalizado a S0';end if;
end $t$;
\echo 'PASS I43-01: I41+I42 liberam historico excepcional do mesmo contato, sem grants brutos'

-- M1: gestor da equipe A/B sem grant. M4: gestor da outra equipe.
select pg_catalog.set_config('request.jwt.claim.sub',
 '62110000-0000-4000-8000-000000000001',true);
do $t$ begin
 if (select count(*) from public.casos_humanos
     where id::text like '62550000-%')<>3
 or (select count(*) from public.conversas
     where id::text like '62770000-%')<>3
 or (select count(*) from public.mensagens
     where conteudo_sintetico like 'I42 mensagem historica %')<>3
 or (select count(*) from public.atribuicoes_humanas
     where caso_id::text like '62550000-%')<>4
 then raise exception 'I43-02 Gestor M1 sem grant perdeu visibilidade da equipe';end if;
end $t$;
select pg_catalog.set_config('request.jwt.claim.sub',
 '62110000-0000-4000-8000-000000000004',true);
do $t$ begin
 if (select count(*) from public.casos_humanos
     where id::text like '62550000-%')<>1
 or (select count(*) from public.mensagens
     where conteudo_sintetico like 'I42 mensagem historica %')<>1
 then raise exception 'I43-02 Gestor de outra equipe viu caso alheio';end if;
end $t$;
\echo 'PASS I43-02: Gestores supervisionam so equipe; chefia sem grant ainda ve dados pertinentes'

-- C2: titular com grant de A/B e caso corrente APENAS da loja B.
select pg_catalog.set_config('request.jwt.claim.sub',
 '62110000-0000-4000-8000-000000000002',true);
do $t$ begin
 if (select count(*) from public.casos_humanos
     where id::text like '62550000-%')<>1
 or (select count(*) from public.mensagens
     where conteudo_sintetico like 'I42 mensagem historica %')<>1
 then raise exception 'I43-03 ex titular C2 acessou equipe alheia';end if;
end $t$;
\echo 'PASS I43-03: Consultor normal nao le carteira transferida por grant da loja'

-- C3 pode enviar somente no caso atual, jamais no historico anterior.
select pg_catalog.set_config('request.jwt.claim.sub',
 '62110000-0000-4000-8000-000000000003',true);
do $t$ begin
 begin
  insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
   direcao,origem,conteudo_sintetico,enviada_por)
  values('62220000-0000-4000-8000-000000000001',
   '62770000-0000-4000-8000-000000000001',
   '62660000-0000-4000-8000-000000000001',
   '62550000-0000-4000-8000-000000000001',
   'saida','simulado','I43 tentativa indevida no historico',
   '62110000-0000-4000-8000-000000000003');
  raise exception 'I43-04 gravou mensagem no historico';
 exception when insufficient_privilege or check_violation then null;end;
 insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
   direcao,origem,conteudo_sintetico,enviada_por)
 values('62220000-0000-4000-8000-000000000001',
   '62770000-0000-4000-8000-000000000002',
   '62660000-0000-4000-8000-000000000001',
   '62550000-0000-4000-8000-000000000002',
   'saida','simulado','I43 resposta corrente permitida',
   '62110000-0000-4000-8000-000000000003');
end $t$;
\echo 'PASS I43-04: I41+I42 mantem historico somente leitura e envio no caso atual'

-- Revogar entitlement nao altera atribuicao S0 nem libera uso de grants
-- gerais. A leitura historica por excecao deve cessar IMEDIATAMENTE.
reset role;
do $t$ declare x uuid;v jsonb;begin
 select id into x from prumo_private.s1_excecoes_55
 where operador_id='62110000-0000-4000-8000-000000000003'
   and revogada_em is null;
 v:=prumo_private.s1_revogar_excecao_55(
    '62110000-0000-4000-8000-000000000001',x);
 if v->>'outcome'<>'REVOKED_CASE_ACCESS'
 or (select count(*) from public.atribuicoes_humanas a
    where a.operador_id='62110000-0000-4000-8000-000000000003'
      and a.encerrada_em is null)<>1
 then raise exception 'I43-05 revogacao/atribuicao inconsistente';end if;
end $t$;
set local role authenticated;
select pg_catalog.set_config('request.jwt.claim.sub',
 '62110000-0000-4000-8000-000000000003',true);
do $t$ begin
 if exists(select 1 from public.casos_humanos
      where id::text like '62550000-%')
 or exists(select 1 from public.conversas
      where id::text like '62770000-%')
 or exists(select 1 from public.mensagens
      where conteudo_sintetico like 'I42 mensagem historica %')
 or exists(select 1 from public.atribuicoes_humanas
      where caso_id::text like '62550000-%')
 or exists(select 1 from public.s1_62_historico_contato_resumo)
 or exists(select 1 from public.s1_55_resumo_caso)
 then raise exception 'I43-05 revogado continua vendo dados integrados';end if;
 begin
  insert into public.mensagens(concessionaria_id,conversa_id,canal_id,caso_id,
   direcao,origem,conteudo_sintetico,enviada_por)
  values('62220000-0000-4000-8000-000000000001',
   '62770000-0000-4000-8000-000000000002',
   '62660000-0000-4000-8000-000000000001',
   '62550000-0000-4000-8000-000000000002',
   'saida','simulado','I43 tentativa apos revogacao',
   '62110000-0000-4000-8000-000000000003');
  raise exception 'I43-05 revogado escreveu';
 exception when insufficient_privilege or check_violation then null;end;
end $t$;
\echo 'PASS I43-05: revogacao corta historia, caso e envio sob policies simultaneas'
-- Gerencia sua propria equipe independentemente da excecao do Consultor.
select pg_catalog.set_config('request.jwt.claim.sub',
 '62110000-0000-4000-8000-000000000001',true);
do $t$ begin
 if (select count(*) from public.casos_humanos
     where id::text like '62550000-%')<>3
 then raise exception 'I43-06 Gestor perdeu supervisao apos revogacao';end if;
end $t$;
reset role;
do $t$ begin
 if (select count(*) from public.vinculos_papel_escopo
    where ator_id='62110000-0000-4000-8000-000000000003')<>0
 or (select count(*) from prumo_private.s1_excecoes_eventos_55
    where tipo='CRIADA')<>1
 or (select count(*) from prumo_private.s1_excecoes_eventos_55
    where tipo='REVOGADA')<>1 then
  raise exception 'I43-06 grants/auditoria divergentes';end if;
end $t$;
rollback;
\echo 'PASS I43-06/ROLLBACK: supervisao e auditoria preservadas, nenhuma policy persistiu'
