-- E04 S0-only policy fixture for post-human template PREVIEW, PG17 disposable.
-- Complements but DOES NOT override existing C04 post-human scheduling prohibition.
create table prumo_private.cfi01_f02_posthuman_template_policy_local (
 concessionaria_id uuid not null,
 template_id uuid not null,
 finalidade text not null check(finalidade='post_human'),
 categoria text not null check(categoria in ('MARKETING','UTILITY','AUTHENTICATION')),
 versao_politica text not null check(versao_politica ~ '^[A-Za-z0-9_.:-]{4,80}$'),
 classificado_em timestamptz not null default statement_timestamp(),
 primary key(concessionaria_id,template_id),
 foreign key(concessionaria_id,template_id)
  references public.catalogo_templates_sinteticos(concessionaria_id,id) on delete restrict
);
create function prumo_private.cfi01_f02_template_policy_guard_local()
returns trigger language plpgsql security invoker set search_path=''
as $$
begin
 if tg_op<>'INSERT' then
  raise exception 'E04_F02_POLICY_IMMUTABLE_LOCAL' using errcode='42501';
 end if;
 if current_user<>'postgres' or not exists (
   select 1 from public.catalogo_templates_sinteticos c
    where c.id=new.template_id
      and c.concessionaria_id=new.concessionaria_id
      and c.aprovado_simulacao=true
 ) then
  raise exception 'E04_F02_POLICY_SCOPE_DENIED_LOCAL' using errcode='42501';
 end if;
 return new;
end $$;
create trigger cfi01_f02_policy_guard_insert
before insert on prumo_private.cfi01_f02_posthuman_template_policy_local
for each row execute function prumo_private.cfi01_f02_template_policy_guard_local();
create trigger cfi01_f02_policy_guard_immutable
before update or delete on prumo_private.cfi01_f02_posthuman_template_policy_local
for each row execute function prumo_private.cfi01_f02_template_policy_guard_local();
alter table prumo_private.cfi01_f02_posthuman_template_policy_local enable row level security;
revoke all on prumo_private.cfi01_f02_posthuman_template_policy_local
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f02_template_policy_guard_local()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on table prumo_private.cfi01_f02_posthuman_template_policy_local
 is 'E04 only: trusted synthetic post-human template category/purpose fixture, not Meta approval or permission to send';
