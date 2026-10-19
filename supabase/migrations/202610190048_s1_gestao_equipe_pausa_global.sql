-- S1-002/I11: corrige I10. Gestor lidera pessoas, NAO concessionarias.
-- O responsavel da plataforma configura grants A/B/C do operador.
-- A pausa do gestor e GLOBAL para o operador e remaneja casos de todas
-- as lojas pelo mecanismo I2; NAO altera nem revoga grants de lojas.
-- APENAS PostgreSQL 17 de teste descartavel. SEM RPC/REST/GOTrue real.

create table prumo_private.s1_responsaveis_plataforma(
 ator_id uuid primary key references public.atores(id) on delete restrict,
 ativo boolean not null default true,
 registrado_em timestamptz not null default pg_catalog.statement_timestamp()
);
create table prumo_private.s1_gestor_operadores(
 id bigint generated always as identity primary key,
 gestor_id uuid not null references public.atores(id) on delete restrict,
 operador_id uuid not null references public.atores(id) on delete restrict,
 atribuido_em timestamptz not null default pg_catalog.statement_timestamp(),
 encerrado_em timestamptz,
 check(gestor_id<>operador_id),
 check(encerrado_em is null or encerrado_em>=atribuido_em)
);
-- Um gestor pode coordenar varios operadores. Proposta conservadora [P]:
-- apenas uma chefia ativa por operador; o responsavel pode transferi-la.
create unique index s1_um_gestor_ativo_por_operador
 on prumo_private.s1_gestor_operadores(operador_id)
 where encerrado_em is null;
create index s1_gestor_equipe_corrente
 on prumo_private.s1_gestor_operadores(gestor_id,operador_id)
 where encerrado_em is null;

alter table prumo_private.s1_responsaveis_plataforma enable row level security;
alter table prumo_private.s1_gestor_operadores enable row level security;
revoke all on prumo_private.s1_responsaveis_plataforma,
 prumo_private.s1_gestor_operadores
 from public,anon,authenticated,service_role;
revoke all on sequence prumo_private.s1_gestor_operadores_id_seq
 from public,anon,authenticated,service_role;

-- Substitui o predicado PROVISORIO da migration 047 (sem editar o histórico).
-- p_loja = null para acoes GLOBAIS (admissao, desligamento, pausa, retorno).
-- p_loja = concessionaria válida para grants e movimento de casos.
-- Identidade p_solicitante permanece SOMENTE para prova interna postgres:
-- nunca chamar do frontend nem tratar parametro como assinatura do usuário.
create or replace function prumo_private.s1_pode_administrar_operador(
 p_solicitante uuid,p_loja uuid,p_acao text,p_alvo uuid)
returns boolean language sql stable security invoker set search_path='' as $a$
 select p_solicitante is not null and p_alvo is not null
  and p_solicitante<>p_alvo
  and exists(select 1 from public.equipe_prumo_s1 e
   where e.ator_id=p_solicitante and e.estado='ativo')
  and (
   -- RESPONSÁVEIS DA PLATAFORMA: cadastro/desligamento GLOBAL
   -- e concessões por loja (não passam pela chefia do gestor).
   (
    exists(select 1 from prumo_private.s1_responsaveis_plataforma r
     where r.ator_id=p_solicitante and r.ativo)
    and (
     (p_loja is null and p_acao in
       ('adicionar_operador','adicionar_gestor',
        'desligar_definitivo_operador','desligar_definitivo_gestor',
        'suspender_temporariamente','reativar_temporariamente'))
     or (p_loja is not null and p_acao in
       ('conceder_concessionaria_operador','revogar_concessionaria_operador',
        'mover_atendimento','redistribuir_carteira','ajustar_distribuicao')
       and exists(select 1 from public.concessionarias l
        where l.id=p_loja and l.ativo))
    )
   )
   or
   -- GESTOR: lideranca EXCLUSIVA SOBRE OPERADORES DA SUA EQUIPE,
   -- nunca editando concessoes de concessionarias nem cadastrando pessoa.
   (
    exists(select 1 from prumo_private.s1_gestor_operadores g
     where g.gestor_id=p_solicitante and g.operador_id=p_alvo
      and g.encerrado_em is null)
    and exists(select 1 from public.equipe_prumo_s1 op
     where op.ator_id=p_alvo and op.estado in ('ativo','suspenso'))
    and not exists(select 1 from prumo_private.s1_responsaveis_plataforma rp
     where rp.ator_id=p_alvo and rp.ativo)
    and not exists(select 1 from prumo_private.s1_gestor_operadores other_g
     where other_g.gestor_id=p_alvo and other_g.encerrado_em is null)
    and (
     (p_loja is null and p_acao in
      ('suspender_temporariamente','reativar_temporariamente'))
     or
     (p_loja is not null and p_acao in
      ('mover_atendimento','redistribuir_carteira','ajustar_distribuicao')
      and exists(select 1 from public.concessionarias l
       where l.id=p_loja and l.ativo)
      and exists(select 1 from public.vinculos_papel_escopo v
       where v.ator_id=p_alvo and v.concessionaria_id=p_loja
        and v.papel='operador'
        and v.valido_desde<=pg_catalog.statement_timestamp()
        and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())))
    )
   )
  );
$a$;
revoke all on function
 prumo_private.s1_pode_administrar_operador(uuid,uuid,text,uuid)
 from public,anon,authenticated,service_role;

-- Auditoria de PAUSA/RETORNO; nao armazena atestado, diagnóstico ou motivo
-- médico em texto livre. Não e a trilha de concessões, que os responsáveis
-- terão sob outro comando autorizador.
create table prumo_private.s1_pausas_operadores_historico(
 id bigint generated always as identity primary key,
 solicitante_id uuid not null references public.atores(id),
 operador_id uuid not null references public.atores(id),
 acao text not null check(acao in ('PAUSA_GLOBAL','RETORNO_GLOBAL')),
 motivo_codigo text not null check(motivo_codigo in
  ('AUSENCIA_TEMPORARIA','INDISPONIBILIDADE_OPERACIONAL','RETORNO_DISPONIBILIDADE')),
 ocorrido_em timestamptz not null default pg_catalog.statement_timestamp()
);
alter table prumo_private.s1_pausas_operadores_historico enable row level security;
revoke all on prumo_private.s1_pausas_operadores_historico
 from public,anon,authenticated,service_role;
revoke all on sequence prumo_private.s1_pausas_operadores_historico_id_seq
 from public,anon,authenticated,service_role;
create trigger s1_hist_pausas_no_mutation
 before update or delete on prumo_private.s1_pausas_operadores_historico
 for each row execute function prumo_private.s1_proibir_alteracao_historico();
create trigger s1_hist_pausas_no_truncate
 before truncate on prumo_private.s1_pausas_operadores_historico
 for each statement execute function prumo_private.s1_proibir_alteracao_historico();

-- Fluxo de prova interno. O executor postgres deste sandbox assume o papel
-- de gateway confiavel; nao concede um comando de usuario real. Em producao
-- sera obrigatoria identidade verificada, não parâmetro escolhido pelo cliente.
create function prumo_private.s1_pausar_operador_da_equipe(
 p_solicitante uuid,p_operador uuid,p_motivo_codigo text)
returns jsonb language plpgsql security invoker set search_path='' as $p$
declare v_total integer;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if not prumo_private.s1_pode_administrar_operador(
  p_solicitante,null,'suspender_temporariamente',p_operador) then
  raise exception 'GESTAO_EQUIPE_NAO_AUTORIZADA' using errcode='42501';end if;
 if p_motivo_codigo not in ('AUSENCIA_TEMPORARIA','INDISPONIBILIDADE_OPERACIONAL')
  or p_motivo_codigo is null then
  raise exception 'MOTIVO_INVALIDO' using errcode='22023';end if;
 update public.equipe_prumo_s1 set estado='suspenso'
  where ator_id=p_operador and estado='ativo';
 get diagnostics v_total=row_count;
 if v_total<>1 then raise exception 'OPERADOR_NAO_ATIVO' using errcode='22023';end if;
 -- Gatilho I2 sincronamente encerra e redistribui TODOS os casos da pessoa.
 insert into prumo_private.s1_pausas_operadores_historico(
  solicitante_id,operador_id,acao,motivo_codigo)
 values(p_solicitante,p_operador,'PAUSA_GLOBAL',p_motivo_codigo);
 return pg_catalog.jsonb_build_object('outcome','PAUSED_GLOBAL','operator_id',p_operador);
end $p$;

create function prumo_private.s1_reativar_operador_da_equipe(
 p_solicitante uuid,p_operador uuid)
returns jsonb language plpgsql security invoker set search_path='' as $p$
declare v_total integer;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if not prumo_private.s1_pode_administrar_operador(
  p_solicitante,null,'reativar_temporariamente',p_operador) then
  raise exception 'GESTAO_EQUIPE_NAO_AUTORIZADA' using errcode='42501';end if;
 update public.equipe_prumo_s1 set estado='ativo'
  where ator_id=p_operador and estado='suspenso';
 get diagnostics v_total=row_count;
 if v_total<>1 then raise exception 'OPERADOR_NAO_SUSPENSO' using errcode='22023';end if;
 -- I6 pode recuperar backlog de outros antigos operadores, mas nunca
 -- restaura por inferencia os casos que ja foram redistribuidos.
 insert into prumo_private.s1_pausas_operadores_historico(
  solicitante_id,operador_id,acao,motivo_codigo)
 values(p_solicitante,p_operador,'RETORNO_GLOBAL','RETORNO_DISPONIBILIDADE');
 return pg_catalog.jsonb_build_object('outcome','ACTIVE_GLOBAL','operator_id',p_operador);
end $p$;
revoke all on function
 prumo_private.s1_pausar_operador_da_equipe(uuid,uuid,text),
 prumo_private.s1_reativar_operador_da_equipe(uuid,uuid)
 from public,anon,authenticated,service_role;
