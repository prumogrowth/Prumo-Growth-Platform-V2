-- S0 simulated reconciliation of C07 outcomes. No Meta, real delivery proof or retries.
-- DEC-13/14/15 remain open. These are NOT authorized external results.

create table public.pendencias_reconciliacao_c07_sinteticas (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 canal_id uuid not null,
 evento_id uuid not null,
 envio_id uuid,
 categoria text not null check(categoria in
  ('SEM_CORRELACAO','RESULTADO_INCERTO','FALHA_REPORTADA','SINAIS_CONTRADITORIOS')),
 estado text not null default 'pendente' check(estado in ('pendente','encerrada')),
 versao bigint not null default 1 check(versao>=1),
 decisao text check(decisao in ('ENCERRAR_SEM_PROVA','VINCULAR_SINTETICAMENTE')),
 justificativa text,
 revisado_por uuid references public.atores(id) on delete restrict,
 criado_em timestamptz not null default statement_timestamp(),
 encerrado_em timestamptz,
 unique(concessionaria_id,id),
 unique(concessionaria_id,evento_id),
 foreign key(concessionaria_id,canal_id)
  references public.canais_loja(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,evento_id)
  references public.eventos_callback_sinteticos(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,envio_id)
  references public.envios_template_sinteticos(concessionaria_id,id) on delete restrict,
 check(
 (estado='pendente' and decisao is null and justificativa is null
  and revisado_por is null and encerrado_em is null)
 or (estado='encerrada' and decisao is not null
  and length(btrim(justificativa)) between 10 and 500
  and revisado_por is not null and encerrado_em is not null))
);
create index c07_pendencias_pendentes_por_loja on public.pendencias_reconciliacao_c07_sinteticas
 (concessionaria_id,criado_em) where estado='pendente';

-- Explicit human-verified TEST association; original callback stays unchanged.
create table public.associacoes_callback_c07_sinteticas (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 evento_id uuid not null,
 envio_id uuid not null,
 revisado_por uuid not null references public.atores(id) on delete restrict,
 criado_em timestamptz not null default statement_timestamp(),
 unique(concessionaria_id,evento_id),
 foreign key(concessionaria_id,evento_id)
  references public.eventos_callback_sinteticos(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,envio_id)
  references public.envios_template_sinteticos(concessionaria_id,id) on delete restrict
);
create table public.auditoria_reconciliacao_c07_sintetica (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 pendencia_id uuid not null,
 ator_id uuid not null references public.atores(id) on delete restrict,
 versao_anterior bigint not null check(versao_anterior>=1),
 decisao text not null check(decisao in ('ENCERRAR_SEM_PROVA','VINCULAR_SINTETICAMENTE')),
 justificativa text not null check(length(btrim(justificativa)) between 10 and 500),
 envio_associado_id uuid,
 criado_em timestamptz not null default statement_timestamp(),
 unique(concessionaria_id,pendencia_id,versao_anterior),
 foreign key(concessionaria_id,pendencia_id)
  references public.pendencias_reconciliacao_c07_sinteticas(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,envio_associado_id)
  references public.envios_template_sinteticos(concessionaria_id,id) on delete restrict
);

alter table public.pendencias_reconciliacao_c07_sinteticas enable row level security;
alter table public.associacoes_callback_c07_sinteticas enable row level security;
alter table public.auditoria_reconciliacao_c07_sintetica enable row level security;
revoke all on public.pendencias_reconciliacao_c07_sinteticas,
 public.associacoes_callback_c07_sinteticas,public.auditoria_reconciliacao_c07_sintetica
 from public,anon,authenticated,service_role;
grant select on public.pendencias_reconciliacao_c07_sinteticas,
 public.associacoes_callback_c07_sinteticas,public.auditoria_reconciliacao_c07_sintetica
 to authenticated;
create policy c07_pendencias_select_gestor on public.pendencias_reconciliacao_c07_sinteticas
 for select to authenticated using(exists(
  select 1 from public.vinculos_papel_escopo v where v.ator_id=(select auth.uid())
   and v.concessionaria_id=pendencias_reconciliacao_c07_sinteticas.concessionaria_id
   and v.papel='gestor' and v.valido_desde<=statement_timestamp()
   and (v.valido_ate is null or v.valido_ate>statement_timestamp())));
create policy c07_associacoes_select_gestor on public.associacoes_callback_c07_sinteticas
 for select to authenticated using(exists(
  select 1 from public.vinculos_papel_escopo v where v.ator_id=(select auth.uid())
   and v.concessionaria_id=associacoes_callback_c07_sinteticas.concessionaria_id
   and v.papel='gestor' and v.valido_desde<=statement_timestamp()
   and (v.valido_ate is null or v.valido_ate>statement_timestamp())));
create policy c07_auditoria_select_gestor on public.auditoria_reconciliacao_c07_sintetica
 for select to authenticated using(exists(
  select 1 from public.vinculos_papel_escopo v where v.ator_id=(select auth.uid())
   and v.concessionaria_id=auditoria_reconciliacao_c07_sintetica.concessionaria_id
   and v.papel='gestor' and v.valido_desde<=statement_timestamp()
   and (v.valido_ate is null or v.valido_ate>statement_timestamp())));

-- Always preserve event history, even if callback is not correlated.
-- A contradictory observation is a review item, not permission for retry.
create function prumo_private.triar_callback_c07_sintetico()
returns trigger language plpgsql security invoker set search_path='' as $fn$
declare v_categoria text;
begin
 if new.resultado='PENDENTE_RECONCILIACAO' then
  v_categoria:='SEM_CORRELACAO';
 elsif new.estado_reportado='INCERTO_SIMULADO' then
  v_categoria:='RESULTADO_INCERTO';
 elsif new.estado_reportado='FALHOU_SIMULADO' then
  if exists(select 1 from public.eventos_callback_sinteticos e
    where e.concessionaria_id=new.concessionaria_id and e.envio_id=new.envio_id
      and e.id<>new.id and e.estado_reportado in
       ('ENVIADO_SIMULADO','ENTREGUE_SIMULADO','LIDO_SIMULADO')) then
    v_categoria:='SINAIS_CONTRADITORIOS';
  else v_categoria:='FALHA_REPORTADA'; end if;
 elsif new.estado_reportado in
  ('ENVIADO_SIMULADO','ENTREGUE_SIMULADO','LIDO_SIMULADO')
  and exists(select 1 from public.eventos_callback_sinteticos e
    where e.concessionaria_id=new.concessionaria_id and e.envio_id=new.envio_id
    and e.id<>new.id and e.estado_reportado='FALHOU_SIMULADO')
 then v_categoria:='SINAIS_CONTRADITORIOS';
 end if;
 if v_categoria is not null then
  insert into public.pendencias_reconciliacao_c07_sinteticas(
   concessionaria_id,canal_id,evento_id,envio_id,categoria)
  values(new.concessionaria_id,new.canal_id,new.id,new.envio_id,v_categoria);
 end if;
 return new;
end $fn$;
create trigger c07_triar_callback_after_insert
 after insert on public.eventos_callback_sinteticos
 for each row execute function prumo_private.triar_callback_c07_sintetico();

-- Human-only simulated classification. Never sends, retries, or sets commercial status.
-- Both final decisions require an actual active gestor of the assigned shop,
-- expected_version, substantial justification, and a privileged internal caller.
create function prumo_private.conciliar_pendencia_c07_sintetica(
 p_ator uuid,p_loja uuid,p_pendencia uuid,p_versao bigint,
 p_decisao text,p_justificativa text,p_envio uuid default null
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_p record;v_evt record;v_audit record;v_canal uuid;v_ref text;
 v_lead uuid;v_plano uuid;v_ligacao uuid;
begin
 if current_user<>'postgres' then
  raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_decisao is null or p_decisao not in
    ('ENCERRAR_SEM_PROVA','VINCULAR_SINTETICAMENTE')
  or p_justificativa is null or length(btrim(p_justificativa)) not between 10 and 500
  or p_versao is null or p_versao<1
 then raise exception 'INVALID_RECONCILIATION' using errcode='22023';end if;
 if not exists(select 1 from public.vinculos_papel_escopo v
   where v.ator_id=p_ator and v.concessionaria_id=p_loja and v.papel='gestor'
    and v.valido_desde<=statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>statement_timestamp()))
 then raise exception 'FORBIDDEN_SCOPE' using errcode='42501';end if;
 if (p_decisao='VINCULAR_SINTETICAMENTE' and p_envio is null)
  or (p_decisao='ENCERRAR_SEM_PROVA' and p_envio is not null)
 then raise exception 'INVALID_RECONCILIATION_TARGET' using errcode='22023';end if;

 select * into v_p from public.pendencias_reconciliacao_c07_sinteticas
 where concessionaria_id=p_loja and id=p_pendencia for update;
 if not found then raise exception 'FORBIDDEN_SCOPE' using errcode='42501';end if;
 if v_p.versao is distinct from p_versao or v_p.estado<>'pendente' then
  select * into v_audit from public.auditoria_reconciliacao_c07_sintetica a
   where a.concessionaria_id=p_loja and a.pendencia_id=p_pendencia
     and a.versao_anterior=p_versao;
  if found and v_audit.ator_id=p_ator and v_audit.decisao=p_decisao
   and v_audit.justificativa=p_justificativa
   and v_audit.envio_associado_id is not distinct from p_envio
  then return jsonb_build_object('outcome','ALREADY_APPLIED',
    'pendencia_id',p_pendencia,'estado_atual',v_p.estado,
    'reenvio_automatico','PROIBIDO','comprovacao_real','NENHUMA');end if;
  raise exception 'CONFLICT_VERSION' using errcode='40001';
 end if;
 if p_decisao='VINCULAR_SINTETICAMENTE' then
  if v_p.categoria<>'SEM_CORRELACAO' then
   raise exception 'CORRELATION_NOT_APPLICABLE' using errcode='22023';end if;
  select * into v_evt from public.eventos_callback_sinteticos e
  where e.id=v_p.evento_id and e.concessionaria_id=p_loja;
  select p.lead_id,p.id,p.canal_id,e.correlacao_externa_ficticia
   into v_lead,v_plano,v_canal,v_ref
  from public.envios_template_sinteticos e
   join public.planos_recontato_sinteticos p
    on p.id=e.plano_id and p.concessionaria_id=e.concessionaria_id
  where e.id=p_envio and e.concessionaria_id=p_loja;
  if v_lead is null or v_canal is distinct from v_p.canal_id
     or v_ref is distinct from v_evt.correlacao_externa_ficticia
  then raise exception 'CORRELATION_SCOPE_OR_REF_MISMATCH' using errcode='42501';end if;
  perform 1 from public.leads_loja
   where concessionaria_id=p_loja and id=v_lead for update;
  perform 1 from public.planos_recontato_sinteticos
   where concessionaria_id=p_loja and id=v_plano for update;
  perform 1 from public.envios_template_sinteticos
   where concessionaria_id=p_loja and id=p_envio for update;
  insert into public.associacoes_callback_c07_sinteticas(
   concessionaria_id,evento_id,envio_id,revisado_por)
  values(p_loja,v_p.evento_id,p_envio,p_ator)
  returning id into v_ligacao;
 end if;
 update public.pendencias_reconciliacao_c07_sinteticas
  set estado='encerrada',versao=versao+1,decisao=p_decisao,
   justificativa=p_justificativa,revisado_por=p_ator,
   encerrado_em=statement_timestamp()
 where id=p_pendencia and concessionaria_id=p_loja;
 insert into public.auditoria_reconciliacao_c07_sintetica(
  concessionaria_id,pendencia_id,ator_id,versao_anterior,
  decisao,justificativa,envio_associado_id)
 values(p_loja,p_pendencia,p_ator,p_versao,p_decisao,p_justificativa,p_envio);
 return jsonb_build_object('outcome','APPLIED','pendencia_id',p_pendencia,
  'nova_versao',p_versao+1,'decisao',p_decisao,'correlacao_ficticia_id',v_ligacao,
  'reenvio_automatico','PROIBIDO','comprovacao_real','NENHUMA');
end $fn$;

-- Diagnostic only: number of DISTINCT failed technical attempts, not "qualified"
-- provider failures. DEC-15 remains unresolved; NEVER execute retry or handoff.
create function prumo_private.diagnosticar_falhas_c07_sintetico(
 p_loja uuid,p_ciclo uuid
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_falhas bigint;v_incerto bigint;v_ambiguas bigint;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if not exists(select 1 from public.ciclos_comerciais c
   where c.concessionaria_id=p_loja and c.id=p_ciclo)
 then raise exception 'FORBIDDEN_SCOPE' using errcode='42501';end if;
 select count(distinct e.id) filter(where cb.estado_reportado='FALHOU_SIMULADO'),
   count(distinct e.id) filter(where cb.estado_reportado='INCERTO_SIMULADO')
 into v_falhas,v_incerto
 from public.planos_recontato_sinteticos p
 join public.envios_template_sinteticos e
  on e.concessionaria_id=p.concessionaria_id and e.plano_id=p.id
 join public.eventos_callback_sinteticos cb
  on cb.concessionaria_id=e.concessionaria_id and cb.envio_id=e.id
 where p.concessionaria_id=p_loja and p.ciclo_id=p_ciclo;
 select count(*) into v_ambiguas from public.pendencias_reconciliacao_c07_sinteticas pr
 join public.eventos_callback_sinteticos cb
  on cb.concessionaria_id=pr.concessionaria_id and cb.id=pr.evento_id
 join public.envios_template_sinteticos e
  on e.concessionaria_id=cb.concessionaria_id and e.id=cb.envio_id
 join public.planos_recontato_sinteticos p
  on p.concessionaria_id=e.concessionaria_id and p.id=e.plano_id
 where p.concessionaria_id=p_loja and p.ciclo_id=p_ciclo
  and pr.estado='pendente';
 return jsonb_build_object('falhas_reportadas_tentativas_distintas',v_falhas,
  'tentativas_com_incerteza',v_incerto,'pendencias_em_aberto',v_ambiguas,
  'falhas_qualificadas','NAO_AVALIADAS_DEC_15',
  'acao','SOMENTE_DIAGNOSTICO','reenvio_automatico','PROIBIDO');
end $fn$;

revoke all on function prumo_private.triar_callback_c07_sintetico()
 from public,anon,authenticated,service_role;
revoke all on function prumo_private.conciliar_pendencia_c07_sintetica(
 uuid,uuid,uuid,bigint,text,text,uuid)
 from public,anon,authenticated,service_role;
revoke all on function prumo_private.diagnosticar_falhas_c07_sintetico(uuid,uuid)
 from public,anon,authenticated,service_role;
