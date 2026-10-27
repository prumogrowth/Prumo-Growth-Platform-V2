-- I82: same I81 owners/privileges; serialize schema review with admin COMMIT.
begin;
set local lock_timeout='3s';
do $guard$
declare r record;p record;
begin
 if current_user<>'postgres' or session_user<>'postgres' or current_database()<>'postgres'
 or current_setting('server_version_num')::int/10000<>17
 or current_setting('prumo.i82_disposable',true) is distinct from 'YES'
 then raise exception 'I82_DISPOSABLE_ONLY' using errcode='42501';end if;
 for r in select * from(values
 ('prumo_private.s1_i79_admin_bridge(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid)','ecbe3e7c9e4f9729320b896abd293fbb8c218b61498316848dec56fff91a250e'),
 ('prumo_private.s1_i80_bridge(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid)','5c6c608b5efde5b4a12f3bb65e1d97fec981f2a534c19496dc14eb87788668bb')
 ) v(signature,digest)
 loop
  select prosrc,prosecdef,pg_get_userbyid(proowner) as owner into p from pg_proc where oid=to_regprocedure(r.signature);
  if not found or p.owner<>'prumo_s1_admin_domain_local' or not p.prosecdef
   or encode(sha256(convert_to(p.prosrc,'UTF8')),'hex')<>r.digest
  then raise exception 'I82_I81_PREREQUISITE_DRIFT' using errcode='42501';end if;
 end loop;
 if (select pg_get_userbyid(proowner) from pg_proc where oid='prumo_private.s1_i79_consistencia()'::regprocedure)
  <>'prumo_s1_professional_validator_local'
 then raise exception 'I82_I81_OWNER_REQUIRED' using errcode='42501';end if;
end $guard$;

create function prumo_private.s1_i82_metadata_fence()
returns void language plpgsql security invoker set search_path='' as $f$
begin
 if current_user<>'prumo_s1_admin_domain_local' then raise exception 'I82_DOMAIN_ONLY' using errcode='42501';end if;
 -- Existing I81 SELECT privileges suffice. ACCESS SHARE is compatible with
 -- ordinary domain writers and survives the DEFINER return until COMMIT;
 -- ALTER TABLE ACCESS EXCLUSIVE cannot slip between review and application.
 lock table public.atribuicoes_humanas,public.casos_humanos in access share mode;
 if (select array_agg(attname::text order by attnum) from pg_attribute
     where attrelid='public.atribuicoes_humanas'::regclass and attnum>0 and not attisdropped)
    is distinct from array['id','concessionaria_id','caso_id','operador_id','atribuida_em','encerrada_em']
 or (select array_agg(attname::text order by attnum) from pg_attribute
     where attrelid='public.casos_humanos'::regclass and attnum>0 and not attisdropped)
    is distinct from array['id','concessionaria_id','lead_id','ciclo_id','origem','criado_em','motivo_simulado']
 then raise exception 'I82_SCHEMA_REVIEW_REQUIRED' using errcode='42501';end if;
end $f$;
revoke all on function prumo_private.s1_i82_metadata_fence()
 from public,anon,authenticated,service_role,prumo_cfi01_pgtest_login,prumo_s0_g1_executor_local;
grant execute on function prumo_private.s1_i82_metadata_fence() to prumo_s1_admin_domain_local;

-- Add ONE guard call; restore exact prior body by removing that prefix when
-- comparing catalog evidence. No business logic, signature or owner changes.
grant create on schema prumo_private to prumo_s1_admin_domain_local;
grant prumo_s1_admin_domain_local to postgres with inherit false,set true;
set local role prumo_s1_admin_domain_local;
do $patch$
declare signature text;d text;
begin
 foreach signature in array array[
 'prumo_private.s1_i79_admin_bridge(uuid,uuid,text,uuid,text,uuid,bigint,text,uuid)',
 'prumo_private.s1_i80_bridge(uuid,uuid,text,uuid,text,uuid,text,uuid,uuid,integer,text,uuid)']
 loop
  d:=pg_get_functiondef(to_regprocedure(signature));
  d:=regexp_replace(d,'\mbegin\M','begin'||chr(10)||' perform prumo_private.s1_i82_metadata_fence();');
  execute d;
 end loop;
end $patch$;
reset role;
revoke prumo_s1_admin_domain_local from postgres;
revoke create on schema prumo_private from prumo_s1_admin_domain_local;
commit;
