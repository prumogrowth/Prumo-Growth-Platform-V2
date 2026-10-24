-- E04 F03 lab-only: automatically track selected existing S0 writers.
-- This is NOT a hosted migration, not a production form/catalog writer.
-- Existing base tables remain unchanged; triggers are loaded after fixtures.
create table prumo_private.cfi01_f03_form_fields_local (
 concessionaria_id uuid not null,
 lead_id uuid not null,
 campo_sintetico text not null check (campo_sintetico ~ '^[a-z_]{2,48}$'),
 valor_sintetico text not null check (char_length(valor_sintetico) between 1 and 512),
 primary key (concessionaria_id,lead_id,campo_sintetico),
 foreign key (concessionaria_id,lead_id)
  references public.leads_loja(concessionaria_id,id) on delete restrict
);
create table prumo_private.cfi01_f03_catalog_entries_local (
 concessionaria_id uuid not null references public.concessionarias(id) on delete restrict,
 codigo_sintetico text not null check (codigo_sintetico ~ '^[A-Z0-9_-]{2,48}$'),
 descricao_sintetica text not null check (char_length(descricao_sintetica) between 1 and 128),
 ativo_sintetico boolean not null default true,
 primary key (concessionaria_id,codigo_sintetico)
);
create function prumo_private.cfi01_f03_source_key_guard_local()
returns trigger language plpgsql security invoker set search_path=''
as $sourceguard$
begin
 if tg_table_name='cfi01_f03_form_fields_local' then
  if old.concessionaria_id is distinct from new.concessionaria_id
   or old.lead_id is distinct from new.lead_id
   or old.campo_sintetico is distinct from new.campo_sintetico then
   raise exception 'F03_FORM_SOURCE_ID_CHANGE_LOCAL' using errcode='42501';
  end if;
 elsif tg_table_name='cfi01_f03_catalog_entries_local' then
  if old.concessionaria_id is distinct from new.concessionaria_id
   or old.codigo_sintetico is distinct from new.codigo_sintetico then
   raise exception 'F03_CATALOG_SOURCE_ID_CHANGE_LOCAL' using errcode='42501';
  end if;
 else
  raise exception 'F03_SOURCE_UNKNOWN_LOCAL' using errcode='42501';
 end if;
 return new;
end $sourceguard$;
create trigger f03_form_field_scope_guard
 before update on prumo_private.cfi01_f03_form_fields_local
 for each row execute function prumo_private.cfi01_f03_source_key_guard_local();
create trigger f03_catalog_entry_scope_guard
 before update on prumo_private.cfi01_f03_catalog_entries_local
 for each row execute function prumo_private.cfi01_f03_source_key_guard_local();

-- Only a recorded/initialized F03 vector is bumped. Existing S0 workflows
-- with NO F03 version record continue unharmed; the CAS denies missing source.
create function prumo_private.cfi01_f03_source_version_bump_local()
returns trigger language plpgsql security invoker set search_path=''
as $sourcebump$
declare v_shop uuid;v_lead uuid;v_case uuid;
begin
 if tg_op='UPDATE' and pg_catalog.to_jsonb(old)=pg_catalog.to_jsonb(new) then
  return new;
 end if;
 if tg_table_schema='public' and tg_table_name='leads_loja' then
  if tg_op<>'UPDATE' then
   raise exception 'F03_LEAD_TRIGGER_OP_LOCAL' using errcode='42501';
  end if;
  if old.telefone_cliente_normalizado is distinct from new.telefone_cliente_normalizado
     or old.concessionaria_id is distinct from new.concessionaria_id then
   update prumo_private.cfi01_f03_lead_versions_local
     set versao_identidade=versao_identidade+1
     where concessionaria_id=old.concessionaria_id and lead_id=old.id;
  end if;
 elsif tg_table_schema='public' and tg_table_name='casos_humanos' then
  if tg_op<>'UPDATE' then
   raise exception 'F03_CASE_TRIGGER_OP_LOCAL' using errcode='42501';
  end if;
  update prumo_private.cfi01_f03_case_versions_local
    set versao_caso=versao_caso+1
    where concessionaria_id=old.concessionaria_id and caso_id=old.id;
 elsif tg_table_schema='public' and tg_table_name='atribuicoes_humanas' then
  v_shop:=case when tg_op='DELETE' then old.concessionaria_id else new.concessionaria_id end;
  v_case:=case when tg_op='DELETE' then old.caso_id else new.caso_id end;
  if tg_op='UPDATE' and
     (old.concessionaria_id is distinct from new.concessionaria_id
      or old.caso_id is distinct from new.caso_id) then
   update prumo_private.cfi01_f03_case_versions_local
    set versao_atribuicao=versao_atribuicao+1
    where concessionaria_id=old.concessionaria_id and caso_id=old.caso_id;
  end if;
  update prumo_private.cfi01_f03_case_versions_local
    set versao_atribuicao=versao_atribuicao+1
    where concessionaria_id=v_shop and caso_id=v_case;
 elsif tg_table_schema='prumo_private' and tg_table_name='cfi01_f03_form_fields_local' then
  v_shop:=case when tg_op='DELETE' then old.concessionaria_id else new.concessionaria_id end;
  v_lead:=case when tg_op='DELETE' then old.lead_id else new.lead_id end;
  update prumo_private.cfi01_f03_lead_versions_local
    set versao_ficha=versao_ficha+1
    where concessionaria_id=v_shop and lead_id=v_lead;
  if not found then
   raise exception 'F03_FORM_VERSION_NOT_INITIALIZED_LOCAL' using errcode='42501';
  end if;
 elsif tg_table_schema='prumo_private' and tg_table_name='cfi01_f03_catalog_entries_local' then
  v_shop:=case when tg_op='DELETE' then old.concessionaria_id else new.concessionaria_id end;
  update prumo_private.cfi01_f03_catalog_versions_local
    set versao_catalogo=versao_catalogo+1
    where concessionaria_id=v_shop;
  if not found then
   raise exception 'F03_CATALOG_VERSION_NOT_INITIALIZED_LOCAL' using errcode='42501';
  end if;
 else
  raise exception 'F03_SOURCE_UNKNOWN_LOCAL' using errcode='42501';
 end if;
 if tg_op='DELETE' then return old;end if;
 return new;
end $sourcebump$;

create trigger f03_lead_identity_version_bump
 after update of telefone_cliente_normalizado,concessionaria_id on public.leads_loja
 for each row execute function prumo_private.cfi01_f03_source_version_bump_local();
create trigger f03_case_version_bump
 after update on public.casos_humanos
 for each row execute function prumo_private.cfi01_f03_source_version_bump_local();
create trigger f03_assignment_version_bump
 after insert or update or delete on public.atribuicoes_humanas
 for each row execute function prumo_private.cfi01_f03_source_version_bump_local();
create trigger f03_form_version_bump
 after insert or update or delete on prumo_private.cfi01_f03_form_fields_local
 for each row execute function prumo_private.cfi01_f03_source_version_bump_local();
create trigger f03_catalog_version_bump
 after insert or update or delete on prumo_private.cfi01_f03_catalog_entries_local
 for each row execute function prumo_private.cfi01_f03_source_version_bump_local();

alter table prumo_private.cfi01_f03_form_fields_local enable row level security;
alter table prumo_private.cfi01_f03_catalog_entries_local enable row level security;
revoke all on prumo_private.cfi01_f03_form_fields_local,
 prumo_private.cfi01_f03_catalog_entries_local
 from public,anon,authenticated,service_role;
revoke execute on function prumo_private.cfi01_f03_source_key_guard_local(),
 prumo_private.cfi01_f03_source_version_bump_local()
 from public,anon,authenticated,service_role;
comment on function prumo_private.cfi01_f03_source_version_bump_local()
 is 'LOCAL E04 only: after-write version bump for actual S0 lead/case/assignment and synthetic form/catalog sources';
