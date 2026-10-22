\set ON_ERROR_STOP on
-- S1-002 I44: instala APENAS no Supabase CLI efemero validado no runner.
-- Fonte de dominio: S0 001..005 + S1 gate 038 (nao fake auth).
-- Restante: fixtures reduzidas de chefia/excecao I55 + MESMAS
-- policies candidatas dos testes I41/I42/I43, nunca migracao.
create schema if not exists prumo_private authorization postgres;
\ir ../migrations/202610170001_s0_foundation.sql
\ir ../migrations/202610170002_s0_read_policies.sql
\ir ../migrations/202610170003_s0_domain.sql
\ir ../migrations/202610170004_s0_access.sql
\ir ../migrations/202610170005_s0_scope_integrity.sql
\ir ../migrations/202610180038_s1_equipe_prumo_gate.sql

-- I55 reduzida: sem eventos externos, transferencia operacional ou grants
-- de loja. O teste valida RLS, nao fluxo S0 de transferencia.
create table prumo_private.s1_gestor_operadores (
 id bigint generated always as identity primary key,
 gestor_id uuid not null references public.atores(id),
 operador_id uuid not null references public.atores(id),
 encerrado_em timestamptz,
 check(gestor_id<>operador_id)
);
create unique index s1_i44_gestor_unico
 on prumo_private.s1_gestor_operadores(operador_id)
 where encerrado_em is null;
revoke all on prumo_private.s1_gestor_operadores
 from public,anon,authenticated,service_role;

create table prumo_private.s1_excecoes_55 (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 caso_id uuid not null,
 atribuicao_id uuid not null unique references public.atribuicoes_humanas(id),
 operador_id uuid not null references public.atores(id),
 gestor_id uuid not null references public.atores(id),
 revogada_em timestamptz,
 foreign key(concessionaria_id,caso_id)
   references public.casos_humanos(concessionaria_id,id)
);
revoke all on prumo_private.s1_excecoes_55
 from public,anon,authenticated,service_role;
alter table prumo_private.s1_excecoes_55 enable row level security;
alter table prumo_private.s1_gestor_operadores enable row level security;

-- Predicado de autorizacao I55 com assinatura e semantica canonicas
-- de fixture (copiado do laboratorio anterior).
create function prumo_private.s1_caso_excepcional_autorizado_55(
 p_loja uuid,p_caso uuid)
returns boolean language sql stable security definer set search_path='' as $fn$
 select p_loja is not null and p_caso is not null
 and (select auth.uid()) is not null
 and exists(
   select 1 from prumo_private.s1_excecoes_55 e
   join public.atribuicoes_humanas a on a.id=e.atribuicao_id
      and a.concessionaria_id=e.concessionaria_id
      and a.caso_id=e.caso_id and a.operador_id=e.operador_id
      and a.encerrada_em is null
   join public.equipe_prumo_s1 op on op.ator_id=e.operador_id and op.estado='ativo'
   join public.equipe_prumo_s1 g on g.ator_id=e.gestor_id and g.estado='ativo'
   join prumo_private.s1_gestor_operadores chefe
      on chefe.gestor_id=e.gestor_id and chefe.operador_id=e.operador_id
      and chefe.encerrado_em is null
   join public.concessionarias loja
      on loja.id=e.concessionaria_id and loja.ativo
   where e.concessionaria_id=p_loja and e.caso_id=p_caso
      and e.revogada_em is null
      and e.operador_id=(select auth.uid())
 );
$fn$;
revoke all on function
 prumo_private.s1_caso_excepcional_autorizado_55(uuid,uuid)
 from public,anon,service_role;
grant execute on function
 prumo_private.s1_caso_excepcional_autorizado_55(uuid,uuid)
 to authenticated;

create policy s1_55_caso_select on public.casos_humanos
 for select to authenticated using (
  prumo_private.s1_caso_excepcional_autorizado_55(concessionaria_id,id));
create policy s1_55_atribuicao_select on public.atribuicoes_humanas
 for select to authenticated using (
  encerrada_em is null and
  prumo_private.s1_caso_excepcional_autorizado_55(concessionaria_id,caso_id));
create policy s1_55_conversa_select on public.conversas
 for select to authenticated using (
  caso_id is not null and
  prumo_private.s1_caso_excepcional_autorizado_55(concessionaria_id,caso_id));
create policy s1_55_mensagens_restrict on public.mensagens as restrictive
 for select to authenticated using (
  exists(select 1 from public.vinculos_papel_escopo v
    where v.ator_id=(select auth.uid())
      and v.concessionaria_id=mensagens.concessionaria_id
      and v.papel in ('gestor','operador','responsavel')
      and v.valido_desde<=pg_catalog.statement_timestamp()
      and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
  ) or (
   caso_id is not null
   and prumo_private.s1_caso_excepcional_autorizado_55(concessionaria_id,caso_id)
   and exists(select 1 from public.conversas co
    where co.concessionaria_id=mensagens.concessionaria_id
      and co.id=mensagens.conversa_id and co.caso_id=mensagens.caso_id)
  )
);
create policy s1_55_msg_insert_exception on public.mensagens
 for insert to authenticated with check(
  direcao='saida' and origem='simulado' and id_externo is null
  and enviada_por=(select auth.uid()) and caso_id is not null
  and prumo_private.s1_caso_excepcional_autorizado_55(concessionaria_id,caso_id)
  and exists(select 1 from public.conversas co
   where co.concessionaria_id=mensagens.concessionaria_id
     and co.id=mensagens.conversa_id
     and co.canal_id=mensagens.canal_id
     and co.caso_id=mensagens.caso_id)
 );

-- Compartilha as MESMAS SQL I41/I42/I43 executadas no PG17.
\ir s1_061_proto_rls_equipe_local_only.sql
\ir s1_062_proto_rls_excecao_local_only.sql
\ir s1_063_proto_rls_unificada_local_only.sql
-- PostgREST precisa enxergar tabelas e view do fixture, sem schemas internos.
notify pgrst, 'reload schema';
\echo 'PASS I44-SCHEMA: S0/S1 + candidate RLS in ephemeral real-auth stack'
