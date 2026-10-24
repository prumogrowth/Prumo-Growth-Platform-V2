-- I57 S0/S1: after-lock grant revalidation at canonical assignment boundary.
begin;
create or replace function public.s0_verificar_atribuicao()
returns trigger language plpgsql security invoker set search_path='' as $f$
begin
 if tg_op='UPDATE'
   and new.operador_id is not distinct from old.operador_id
   and new.caso_id is not distinct from old.caso_id
   and new.concessionaria_id is not distinct from old.concessionaria_id
 then return new;end if;
 -- Acquire locks WITHOUT a time predicate: a committed revocation which
 -- happened during a wait must be visible after acquiring the row lock.
 perform 1 from public.vinculos_papel_escopo v
 where v.ator_id=new.operador_id
 and v.concessionaria_id=new.concessionaria_id
 and v.papel in ('operador','gestor')
 order by v.papel,v.valido_desde for share of v;
 if not found then raise exception 'S0_DESTINO_SEM_CONCESSAO_ATIVA'
 using errcode='23514';end if;
 -- A separate read uses wall-clock time AFTER acquiring grant locks.
 perform 1 from public.vinculos_papel_escopo v
 join public.concessionarias l on l.id=v.concessionaria_id
 where v.ator_id=new.operador_id and v.concessionaria_id=new.concessionaria_id
 and v.papel in ('operador','gestor') and l.ativo
 and v.valido_desde<=pg_catalog.clock_timestamp()
 and (v.valido_ate is null or v.valido_ate>pg_catalog.clock_timestamp())
 for share of l;
 if not found then raise exception 'S0_DESTINO_SEM_CONCESSAO_ATIVA'
 using errcode='23514';end if;
 return new;
end $f$;
revoke all on function public.s0_verificar_atribuicao()
 from public,anon,authenticated,service_role;
commit;
