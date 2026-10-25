-- E04 S0-only physical PG17 fixture: human-approved synthetic form CAS.
-- Not a hosted migration, production interface, identity resolution, F03 grant.
create table prumo_private.cfi01_f03_form_application_local (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 evento_fechamento_id uuid not null,
 caso_id uuid not null,
 lead_id uuid not null,
 gestor_id uuid not null references public.atores(id) on delete restrict,
 sessao_id uuid not null references auth.sessions(id) on delete restrict,
 referencia_requisicao text not null,
 proposta_sha256 text not null check(proposta_sha256 ~ '^[0-9a-f]{64}$'),
 cas_condicoes_sha256 text not null check(cas_condicoes_sha256 ~ '^[0-9a-f]{64}$'),
 evidencia_aprovacao_sha256 text not null check(evidencia_aprovacao_sha256 ~ '^[0-9a-f]{64}$'),
 chave_idempotencia text not null check(chave_idempotencia ~ '^[A-Za-z0-9._:-]{8,128}$'),
 versao_ficha_antes bigint not null check(versao_ficha_antes>0),
 versao_ficha_depois bigint not null check(versao_ficha_depois>versao_ficha_antes),
 quantidade_campos integer not null check(quantidade_campos between 1 and 12),
 decisao text not null check(decisao='EXPLICIT_APPROVE_SYNTHETIC_FIELDS'),
 registrado_em timestamptz not null default statement_timestamp(),
 foreign key(concessionaria_id,evento_fechamento_id)
  references prumo_private.cfi01_f03_reservations_local
    (concessionaria_id,evento_fechamento_id) on delete restrict,
 foreign key(concessionaria_id,caso_id)
  references public.casos_humanos(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,lead_id)
  references public.leads_loja(concessionaria_id,id) on delete restrict,
 unique(concessionaria_id,evento_fechamento_id)
);
create table prumo_private.cfi01_f03_form_application_items_local (
 aplicacao_id uuid not null references
  prumo_private.cfi01_f03_form_application_local(id) on delete restrict,
 campo_sintetico text not null check(campo_sintetico ~ '^[a-z_]{2,48}$'),
 antigo_sha256 text check(antigo_sha256 ~ '^[0-9a-f]{64}$'),
 novo_sha256 text not null check(novo_sha256 ~ '^[0-9a-f]{64}$'),
 primary key(aplicacao_id,campo_sintetico)
);
create function prumo_private.cfi01_f03_application_guard_local()
returns trigger language plpgsql security invoker set search_path=''
as $guard$
begin
 if tg_op<>'INSERT' then
  raise exception 'F03_APPLICATION_IMMUTABLE_LOCAL' using errcode='42501';
 end if;
 if tg_table_name='cfi01_f03_form_application_local' then
  if not exists(
   select 1 from prumo_private.cfi01_f03_reservations_local r
   join public.casos_humanos h on
    h.concessionaria_id=r.concessionaria_id and h.id=r.caso_id and h.lead_id=r.lead_id
   join auth.sessions ses on ses.id=new.sessao_id and ses.user_id=new.gestor_id
   join public.equipe_prumo_s1 team on team.ator_id=new.gestor_id and team.estado='ativo'
   join public.vinculos_papel_escopo role on role.ator_id=new.gestor_id
     and role.concessionaria_id=r.concessionaria_id and role.papel='gestor'
     and role.valido_desde<=statement_timestamp()
     and (role.valido_ate is null or role.valido_ate>statement_timestamp())
   where r.concessionaria_id=new.concessionaria_id
    and r.evento_fechamento_id=new.evento_fechamento_id
    and r.caso_id=new.caso_id and r.lead_id=new.lead_id
    and r.referencia_requisicao=new.referencia_requisicao
    and r.proposta_sha256=new.proposta_sha256
  ) then raise exception 'F03_APPLICATION_SCOPE_DENIED_LOCAL' using errcode='42501';
  end if;
 elsif tg_table_name<>'cfi01_f03_form_application_items_local' then
  raise exception 'F03_APPLICATION_SOURCE_DENIED_LOCAL' using errcode='42501';
 end if;
 return new;
end $guard$;
create trigger f03_application_guard
before insert or update or delete on prumo_private.cfi01_f03_form_application_local
for each row execute function prumo_private.cfi01_f03_application_guard_local();
create trigger f03_application_items_guard
before insert or update or delete on prumo_private.cfi01_f03_form_application_items_local
for each row execute function prumo_private.cfi01_f03_application_guard_local();
alter table prumo_private.cfi01_f03_form_application_local enable row level security;
alter table prumo_private.cfi01_f03_form_application_items_local enable row level security;
revoke all on prumo_private.cfi01_f03_form_application_local,
 prumo_private.cfi01_f03_form_application_items_local
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
revoke execute on function prumo_private.cfi01_f03_application_guard_local()
 from public,anon,authenticated,service_role,prumo_s0_gateway,prumo_s0_signer;
comment on table prumo_private.cfi01_f03_form_application_local
is 'Local E04 S0-only synthetic form CAS human action, no F03 grant, no production data';
