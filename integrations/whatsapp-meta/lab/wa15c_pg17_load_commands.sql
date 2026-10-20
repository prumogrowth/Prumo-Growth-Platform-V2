-- Shared loader: \set wa15_payload MUST come from the real WA15B TypeScript
-- generator. Safe psql quoted literal -> JSONB value, never SQL identifiers.
create temp table wa15c_commands(
 label text primary key, action text not null, function_name text not null,
 args jsonb not null, ack_allowed boolean not null,
 retry_external boolean not null, production_authorized boolean not null
) on commit preserve rows;
insert into pg_temp.wa15c_commands(
 label,action,function_name,args,ack_allowed,retry_external,production_authorized)
select e->>'label',e->>'action',e->>'function_name',e->'args',
 (e->>'ack_allowed')::boolean,(e->>'retry_external')::boolean,
 (e->>'production_authorized')::boolean
from jsonb_array_elements(:'wa15_payload'::jsonb) as t(e);
do $wa15c_loader$
begin
 if (select count(*) from pg_temp.wa15c_commands)<>8
 or exists(select 1 from pg_temp.wa15c_commands where
   ack_allowed or retry_external or production_authorized
   or jsonb_typeof(args)<>'array'
   or (action='REGISTER_FIXTURE' and
       (function_name<>'prumo_private.registrar_vinculo_meta_tecnico_fixture_s0'
         or jsonb_array_length(args)<>10))
   or (action='RECOVER_FIXTURE' and
       (function_name<>'prumo_private.consultar_vinculo_meta_tecnico_fixture_s0'
         or jsonb_array_length(args)<>9))
   or action not in ('REGISTER_FIXTURE','RECOVER_FIXTURE'))
 then raise exception 'WA15C_INVALID_TYPESCRIPT_CONTRACT';end if;
end $wa15c_loader$;

-- Fixed allow-listed private SQL functions and positional JSONB value casts.
-- Never execute arbitrary SQL from the JSON command. Only test fixtures.
create function pg_temp.wa15c_call(p_label text)
returns jsonb language plpgsql security invoker set search_path='' as $wa15c_call$
declare c record;
begin
 select * into c from pg_temp.wa15c_commands where label=p_label;
 if not found then raise exception 'WA15C_MISSING_COMMAND' using errcode='22023';end if;
 if c.action='REGISTER_FIXTURE' and
 c.function_name='prumo_private.registrar_vinculo_meta_tecnico_fixture_s0'
 then
 return prumo_private.registrar_vinculo_meta_tecnico_fixture_s0(
   c.args->>0,c.args->>1,c.args->>2,(c.args->>3)::uuid,(c.args->>4)::uuid,
   c.args->>5,c.args->>6,c.args->>7,c.args->>8,(c.args->>9)::integer);
 elsif c.action='RECOVER_FIXTURE' and
 c.function_name='prumo_private.consultar_vinculo_meta_tecnico_fixture_s0'
 then
 return prumo_private.consultar_vinculo_meta_tecnico_fixture_s0(
   c.args->>0,c.args->>1,c.args->>2,(c.args->>3)::uuid,(c.args->>4)::uuid,
   c.args->>5,c.args->>6,c.args->>7,c.args->>8);
 else raise exception 'WA15C_DISALLOWED_ACTION' using errcode='22023';end if;
end $wa15c_call$;
