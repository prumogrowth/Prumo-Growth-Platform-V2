-- E04 F02/S0 audit-only POST-HUMAN INTENT, disposable PG17 fixture.
-- No C04 scheduler changes, real consent, plan creation, or Meta dispatch.
create table prumo_private.cfi01_f02_posthuman_intents_local (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 evento_fechamento_id uuid not null,
 caso_id uuid not null,
 lead_id uuid not null,
 canal_id uuid not null,
 template_id uuid not null,
 gestor_id uuid not null,
 sessao_id uuid not null,
 tentativa_s2 text not null check(tentativa_s2 ~ '^[A-Za-z0-9_.:-]{1,100}$'),
 versao_template text not null check(versao_template ~ '^v[0-9]+$'),
 categoria text not null check(categoria in ('MARKETING','UTILITY','AUTHENTICATION')),
 versao_politica text not null check(versao_politica ~ '^[A-Za-z0-9_.:-]{4,80}$'),
 decisao text not null check(decisao='EXPLICIT_REVIEW_SYNTHETIC_ONLY'),
 evidencia_gestor_sha256 text not null check(evidencia_gestor_sha256 ~ '^[0-9a-f]{64}$'),
 proposta_sha256 text not null check(proposta_sha256 ~ '^[0-9a-f]{64}$'),
 chave_idempotencia text not null check(chave_idempotencia ~ '^[A-Za-z0-9._:-]{8,128}$'),
 estado text not null default 'AUDIT_ONLY_C04_BLOCKED'
  check(estado='AUDIT_ONLY_C04_BLOCKED'),
 registrado_em timestamptz not null default statement_timestamp(),
 unique(concessionaria_id,evento_fechamento_id),
 unique(concessionaria_id,chave_idempotencia),
 foreign key(concessionaria_id,template_id)
  references public.catalogo_templates_sinteticos(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,lead_id)
  references public.leads_loja(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,canal_id)
  references public.canais_loja(concessionaria_id,id) on delete restrict
);
create function prumo_private.cfi01_f02_posthuman_intent_guard_local()
returns trigger language plpgsql security invoker set search_path=''
as $$
begin
 if tg_op<>'INSERT' then
  raise exception 'F02_POSTHUMAN_INTENT_IMMUTABLE_LOCAL' using errcode='42501';
 end if;
 if current_user<>'postgres' or not exists (
   select 1 from prumo_private.cfi01_human_closure_events_local e
   join public.casos_humanos h on h.id=e.caso_id
    and h.concessionaria_id=e.concessionaria_id
   join public.ciclos_comerciais c on c.id=h.ciclo_id
    and c.concessionaria_id=h.concessionaria_id
   join public.canais_loja ch on ch.id=new.canal_id
    and ch.concessionaria_id=e.concessionaria_id and ch.modo='simulado'
   join public.catalogo_templates_sinteticos t on t.id=new.template_id
    and t.concessionaria_id=e.concessionaria_id and t.aprovado_simulacao
   join prumo_private.cfi01_f02_posthuman_template_policy_local p
    on p.template_id=t.id and p.concessionaria_id=t.concessionaria_id
   join auth.sessions s on s.id=new.sessao_id and s.user_id=new.gestor_id
   join public.equipe_prumo_s1 team on team.ator_id=s.user_id and team.estado='ativo'
   join public.vinculos_papel_escopo role on role.ator_id=s.user_id
    and role.concessionaria_id=e.concessionaria_id and role.papel='gestor'
    and role.valido_desde<=statement_timestamp()
    and (role.valido_ate is null or role.valido_ate>statement_timestamp())
   where e.id=new.evento_fechamento_id and e.concessionaria_id=new.concessionaria_id
     and e.caso_id=new.caso_id and h.lead_id=new.lead_id
     and c.lead_id=new.lead_id and c.concessionaria_id=new.concessionaria_id
     and p.finalidade='post_human' and p.categoria=new.categoria
     and p.versao_politica=new.versao_politica
     and ('v'||t.versao)=new.versao_template
     and not exists(
       select 1 from public.supressoes_contato_sinteticas o
       where o.concessionaria_id=new.concessionaria_id
        and o.lead_id=new.lead_id and o.canal_id=new.canal_id
        and o.finalidade='recontato_comercial_sintetico'
     )
     and exists(
       select 1 from public.evidencias_elegibilidade_sinteticas el
       where el.concessionaria_id=new.concessionaria_id
        and el.lead_id=new.lead_id and el.canal_id=new.canal_id
        and el.finalidade='recontato_comercial_sintetico'
        and el.estado='verificada_simulada'
     )
     and not exists(
       select 1 from public.planos_recontato_sinteticos prior_plan
       where prior_plan.concessionaria_id=new.concessionaria_id
        and prior_plan.lead_id=new.lead_id and prior_plan.estado='ativo'
     )
 ) then
  raise exception 'F02_POSTHUMAN_INTENT_SCOPE_DENIED_LOCAL' using errcode='42501';
 end if;
 return new;
end $$;
create trigger cfi01_f02_posthuman_intent_insert
before insert on prumo_private.cfi01_f02_posthuman_intents_local
for each row execute function prumo_private.cfi01_f02_posthuman_intent_guard_local();
create trigger cfi01_f02_posthuman_intent_immutable
before update or delete on prumo_private.cfi01_f02_posthuman_intents_local
for each row execute function prumo_private.cfi01_f02_posthuman_intent_guard_local();
alter table prumo_private.cfi01_f02_posthuman_intents_local enable row level security;
revoke all on prumo_private.cfi01_f02_posthuman_intents_local
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f02_posthuman_intent_guard_local()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on table prumo_private.cfi01_f02_posthuman_intents_local is
 'PG17 E04 S0-only audit of explicit post-human synthetic manager intent; NOT a plan, template send, Meta evidence, real consent, or permission';
