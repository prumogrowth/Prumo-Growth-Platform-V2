-- S1-002/I9: fronteira administrativa fail-closed em PostgreSQL ficticio.
-- Nao define QUEM e aprovador RH, nem habilita RPC publica. O comando
-- administrativo real continua SEM implementacao ate contrato e prova Auth.
-- A mutacao de equipe fica reservada ao dono tecnico postgres deste sandbox.
-- Nunca aplicar automaticamente em Supabase hospedado.
revoke all on public.equipe_prumo_s1,public.equipe_prumo_eventos_s1
 from anon,authenticated,service_role;
grant select on public.equipe_prumo_s1 to authenticated;

create function prumo_private.s1_exigir_executor_interno_equipe()
returns trigger language plpgsql security invoker set search_path='' as $guard$
begin
 if current_user<>'postgres' then
  raise exception 'S1_EQUIPE_ADMIN_NAO_HABILITADO' using errcode='42501';
 end if;
 if tg_op='INSERT' or tg_op='UPDATE' then return new;end if;
 return old;
end $guard$;

-- Mesmo que um novo GRANT ou BYPASSRLS acidental apareça, não deve
-- haver escrita pela Data API. Trigger permanece invocado no banco.
create trigger s1_equipe_proteger_escrita
 before insert or update or delete on public.equipe_prumo_s1
 for each row execute function prumo_private.s1_exigir_executor_interno_equipe();
create trigger s1_eventos_proteger_insert
 before insert on public.equipe_prumo_eventos_s1
 for each row execute function prumo_private.s1_exigir_executor_interno_equipe();

revoke all on function prumo_private.s1_exigir_executor_interno_equipe()
 from public,anon,authenticated,service_role;
