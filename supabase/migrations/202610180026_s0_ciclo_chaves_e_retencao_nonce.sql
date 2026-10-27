-- S0 candidate: auditable key rotation and nonce retention; no real secrets.
-- Not an operational key-management system. Only trusted postgres can manage.
alter table prumo_private.gateway_chaves_assinatura_s0
 add column versao bigint not null default 1 check(versao>0),
 add column revogado_em timestamptz,
 add column motivo_revogacao text,
 add constraint gateway_chave_revogada_inativa check(
   (revogado_em is null and motivo_revogacao is null)
   or (revogado_em is not null and not ativo and
       length(btrim(motivo_revogacao)) between 10 and 300));

create table prumo_private.gateway_eventos_chave_s0(
 id bigint generated always as identity primary key,
 chave_id uuid not null references prumo_private.gateway_chaves_assinatura_s0(chave_id)
   on delete restrict,
 tipo text not null check(tipo in ('REGISTRADA','ATIVADA','REVOGADA')),
 versao_anterior bigint,
 nova_versao bigint not null check(nova_versao>0),
 registrado_em timestamptz not null default clock_timestamp()
);
revoke all on prumo_private.gateway_eventos_chave_s0
 from public,anon,authenticated,service_role,prumo_s0_gateway;

create function prumo_private.auditar_rotacao_gateway_s0()
returns trigger language plpgsql security invoker set search_path='' as $tg$
declare v_tipo text;
begin
 if current_user<>'postgres'
 then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if tg_op='UPDATE' then
   if new.chave_id is distinct from old.chave_id
      or new.segredo is distinct from old.segredo
      or new.valido_desde is distinct from old.valido_desde
      or new.valido_ate is distinct from old.valido_ate
      or new.versao<>old.versao+1
   then raise exception 'KEY_MATERIAL_IMMUTABLE' using errcode='42501';end if;
   if old.revogado_em is not null or (old.ativo=new.ativo)
   then raise exception 'KEY_TRANSITION_INVALID' using errcode='22023';end if;
   if old.ativo and not new.ativo then
     if new.revogado_em is null or new.motivo_revogacao is null
     then raise exception 'REVOCATION_REASON_REQUIRED' using errcode='22023';end if;
     v_tipo:='REVOGADA';
   elsif not old.ativo and new.ativo then
     if new.revogado_em is not null or new.motivo_revogacao is not null
     then raise exception 'ACTIVATION_INVALID' using errcode='22023';end if;
     v_tipo:='ATIVADA';
   else raise exception 'KEY_TRANSITION_INVALID' using errcode='22023';end if;
 end if;
 if tg_op='INSERT' then
   if new.versao<>1 or new.revogado_em is not null or new.ativo
   then raise exception 'KEY_REGISTRATION_INVALID' using errcode='22023';end if;
   v_tipo:='REGISTRADA';
 end if;
 insert into prumo_private.gateway_eventos_chave_s0(
  chave_id,tipo,versao_anterior,nova_versao)
 values(new.chave_id,v_tipo,
   case when tg_op='INSERT' then null else old.versao end,new.versao);
 return new;
end $tg$;
create trigger prumo_chave_eventos_s0
 after insert or update on prumo_private.gateway_chaves_assinatura_s0
 for each row execute function prumo_private.auditar_rotacao_gateway_s0();

create function prumo_private.alterar_estado_chave_gateway_s0(
 p_chave uuid,p_versao bigint,p_ativar boolean,p_motivo text
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_chave record;v_agora timestamptz;
begin
 if current_user<>'postgres'
 then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_chave is null or p_versao is null or p_versao<1
    or p_ativar is null or p_motivo is null
    or length(btrim(p_motivo)) not between 10 and 300
 then raise exception 'INVALID_KEY_CHANGE' using errcode='22023';end if;
 select * into v_chave from prumo_private.gateway_chaves_assinatura_s0
 where chave_id=p_chave for update;
 if not found then raise exception 'KEY_NOT_FOUND' using errcode='22023';end if;
 if v_chave.versao<>p_versao
 then raise exception 'CONFLICT_VERSION' using errcode='40001';end if;
 if v_chave.revogado_em is not null or v_chave.ativo=p_ativar
 then raise exception 'KEY_TRANSITION_INVALID' using errcode='22023';end if;
 v_agora:=clock_timestamp();
 if p_ativar and (v_chave.valido_desde>v_agora or v_chave.valido_ate<=v_agora)
 then raise exception 'KEY_VALIDITY_WINDOW_INVALID' using errcode='22023';end if;
 update prumo_private.gateway_chaves_assinatura_s0
 set ativo=p_ativar,versao=versao+1,
     revogado_em=case when p_ativar then null else v_agora end,
     motivo_revogacao=case when p_ativar then null else btrim(p_motivo) end
 where chave_id=p_chave;
 return pg_catalog.jsonb_build_object(
  'outcome','APPLIED','chave_id',p_chave,'nova_versao',p_versao+1,
  'ativo',p_ativar,'revogacao_definitiva',not p_ativar);
end $fn$;
revoke all on function prumo_private.alterar_estado_chave_gateway_s0(
 uuid,bigint,boolean,text)
 from public,anon,authenticated,service_role,prumo_s0_gateway;

create table prumo_private.gateway_limpezas_nonce_s0(
 id bigint generated always as identity primary key,
 corte_em timestamptz not null,
 quantidade bigint not null check(quantidade>=0),
 executado_em timestamptz not null default clock_timestamp()
);
revoke all on prumo_private.gateway_limpezas_nonce_s0
 from public,anon,authenticated,service_role,prumo_s0_gateway;

create function prumo_private.expurgar_nonces_gateway_s0(
 p_corte timestamptz
) returns jsonb language plpgsql security invoker set search_path='' as $fn$
declare v_n bigint;
begin
 if current_user<>'postgres'
 then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 -- Signatures last <=35 seconds with skew; retain nonce at least 10 minutes.
 if p_corte is null or p_corte>clock_timestamp()-interval '10 minutes'
 then raise exception 'RETENTION_WINDOW_NOT_MET' using errcode='22023';end if;
 delete from prumo_private.gateway_provas_usadas_s0
 where consumido_em<p_corte;
 get diagnostics v_n=row_count;
 insert into prumo_private.gateway_limpezas_nonce_s0(corte_em,quantidade)
 values(p_corte,v_n);
 return pg_catalog.jsonb_build_object('outcome','APPLIED','apagados',v_n);
end $fn$;
revoke all on function prumo_private.expurgar_nonces_gateway_s0(timestamptz)
 from public,anon,authenticated,service_role,prumo_s0_gateway;
