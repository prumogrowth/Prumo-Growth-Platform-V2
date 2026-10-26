-- E04 S0/F02 disposable PG17: a PRIVATE REVIEW DRAFT, never C04 queue.
-- Purely synthetic time window (24h..7d), not adopted commercial policy.
create table prumo_private.cfi01_f02_posthuman_draft_local (
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
 horario_proposto timestamptz not null,
 proposta_sha256 text not null check(proposta_sha256 ~ '^[0-9a-f]{64}$'),
 chave_idempotencia text not null check(chave_idempotencia ~ '^[A-Za-z0-9._:-]{8,128}$'),
 estado text not null default 'REVIEW_ONLY_C04_BLOCKED'
  check(estado='REVIEW_ONLY_C04_BLOCKED'),
 criado_em timestamptz not null default statement_timestamp(),
 unique(concessionaria_id,evento_fechamento_id),
 unique(concessionaria_id,chave_idempotencia),
 foreign key(concessionaria_id,evento_fechamento_id)
  references prumo_private.cfi01_f02_posthuman_intents_local
  (concessionaria_id,evento_fechamento_id) on delete restrict,
 foreign key(concessionaria_id,template_id)
  references public.catalogo_templates_sinteticos(concessionaria_id,id) on delete restrict
);
create function prumo_private.cfi01_f02_posthuman_draft_guard_local()
returns trigger language plpgsql security invoker set search_path='' as $$
begin
 if tg_op<>'INSERT' then
  raise exception 'F02_DRAFT_IMMUTABLE_LOCAL' using errcode='42501';
 end if;
 if current_user<>'postgres' or
  new.horario_proposto<statement_timestamp()+interval '24 hours' or
  new.horario_proposto>statement_timestamp()+interval '7 days' or
  not exists(
   select 1
   from prumo_private.cfi01_f02_posthuman_intents_local i
   join public.casos_humanos h on h.id=i.caso_id
    and h.concessionaria_id=i.concessionaria_id and h.lead_id=i.lead_id
   join public.ciclos_comerciais c on c.id=h.ciclo_id
    and c.concessionaria_id=h.concessionaria_id and c.lead_id=h.lead_id
   join auth.sessions s on s.id=i.sessao_id and s.user_id=i.gestor_id
   join public.equipe_prumo_s1 team on team.ator_id=s.user_id
    and team.estado='ativo'
   join public.vinculos_papel_escopo role on role.ator_id=i.gestor_id
    and role.concessionaria_id=i.concessionaria_id and role.papel='gestor'
    and role.valido_desde<=statement_timestamp()
    and (role.valido_ate is null or role.valido_ate>statement_timestamp())
   join public.canais_loja ch on ch.concessionaria_id=i.concessionaria_id
    and ch.id=i.canal_id and ch.modo='simulado'
   join public.catalogo_templates_sinteticos t
    on t.concessionaria_id=i.concessionaria_id and t.id=i.template_id
    and t.aprovado_simulacao
   join prumo_private.cfi01_f02_posthuman_template_policy_local policy
    on policy.concessionaria_id=t.concessionaria_id
    and policy.template_id=t.id and policy.finalidade='post_human'
   where i.concessionaria_id=new.concessionaria_id
    and i.evento_fechamento_id=new.evento_fechamento_id
    and i.caso_id=new.caso_id and i.lead_id=new.lead_id
    and i.canal_id=new.canal_id and i.template_id=new.template_id
    and i.gestor_id=new.gestor_id and i.sessao_id=new.sessao_id
    and i.tentativa_s2=new.tentativa_s2
    and i.versao_template=new.versao_template
    and i.categoria=new.categoria and i.versao_politica=new.versao_politica
    and policy.categoria=new.categoria
    and policy.versao_politica=new.versao_politica
    and ('v'||t.versao)=new.versao_template
    and i.estado='AUDIT_ONLY_C04_BLOCKED'
    and not exists(
      select 1 from public.planos_recontato_sinteticos prior
      where prior.concessionaria_id=i.concessionaria_id
       and prior.lead_id=i.lead_id
    )
    and not exists(
      select 1 from public.supressoes_contato_sinteticas o
      where o.concessionaria_id=i.concessionaria_id
       and o.lead_id=i.lead_id and o.canal_id=i.canal_id
       and o.finalidade='recontato_comercial_sintetico'
    )
    and exists(
      select 1 from public.evidencias_elegibilidade_sinteticas el
      where el.concessionaria_id=i.concessionaria_id
       and el.lead_id=i.lead_id and el.canal_id=i.canal_id
       and el.finalidade='recontato_comercial_sintetico'
       and el.estado='verificada_simulada'
    )
  )
 then
  raise exception 'F02_DRAFT_SCOPE_OR_POLICY_DENIED_LOCAL' using errcode='42501';
 end if;
 return new;
end $$;
create trigger cfi01_f02_posthuman_draft_insert
before insert on prumo_private.cfi01_f02_posthuman_draft_local
for each row execute function prumo_private.cfi01_f02_posthuman_draft_guard_local();
create trigger cfi01_f02_posthuman_draft_immutable
before update or delete on prumo_private.cfi01_f02_posthuman_draft_local
for each row execute function prumo_private.cfi01_f02_posthuman_draft_guard_local();
alter table prumo_private.cfi01_f02_posthuman_draft_local enable row level security;
revoke all on prumo_private.cfi01_f02_posthuman_draft_local
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f02_posthuman_draft_guard_local()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on table prumo_private.cfi01_f02_posthuman_draft_local is
 'E04 synthetic review-only draft: ZERO queue routing, ZERO Meta sending, cannot replace C04 scheduler, no legacy-chain approval';
