-- S1-002/I2: SOMENTE sandbox descartavel; nao aplicar no Supabase hospedado.
-- Nenhum novo privilegio REST, envio, alteracao de status ou autoridade RH.
create table prumo_private.s1_remanejamento_pendencias(
 concessionaria_id uuid not null, caso_id uuid not null,
 operador_anterior uuid not null references public.atores(id),
 motivo text not null check(motivo in ('EQUIPE_INATIVA','ESCOPO_REVOGADO')),
 registrado_em timestamptz not null default statement_timestamp(),
 primary key(concessionaria_id,caso_id),
 foreign key(concessionaria_id,caso_id) references public.casos_humanos(concessionaria_id,id)
);
create table prumo_private.s1_remanejamento_historico(
 id bigint generated always as identity primary key,
 concessionaria_id uuid not null, caso_id uuid not null,
 atribuicao_anterior_id uuid not null unique references public.atribuicoes_humanas(id),
 operador_anterior uuid not null references public.atores(id),
 operador_novo uuid references public.atores(id),
 motivo text not null check(motivo in ('EQUIPE_INATIVA','ESCOPO_REVOGADO')),
 resultado text not null check(resultado in ('REDISTRIBUIDO','FILA_PROTEGIDA','ENCERRADO_HISTORICO')),
 registrado_em timestamptz not null default statement_timestamp(),
 foreign key(concessionaria_id,caso_id) references public.casos_humanos(concessionaria_id,id),
 check((resultado='REDISTRIBUIDO' and operador_novo is not null)
 or (resultado in ('FILA_PROTEGIDA','ENCERRADO_HISTORICO') and operador_novo is null))
);
alter table prumo_private.s1_remanejamento_pendencias enable row level security;
alter table prumo_private.s1_remanejamento_historico enable row level security;
revoke all on prumo_private.s1_remanejamento_pendencias, prumo_private.s1_remanejamento_historico
 from public,anon,authenticated,service_role;
revoke all on sequence prumo_private.s1_remanejamento_historico_id_seq from public,anon,authenticated,service_role;

-- Bloqueio de elegibilidade da atribuicao: trava contra suspensao simultanea.
create function prumo_private.s1_validar_nova_atribuicao()
 returns trigger language plpgsql security invoker set search_path='' as $fn$
declare v_ok boolean;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501'; end if;
 select true into v_ok from public.equipe_prumo_s1 e
 join public.vinculos_papel_escopo v on v.ator_id=e.ator_id
 join public.concessionarias l on l.id=v.concessionaria_id
 where e.ator_id=new.operador_id and e.estado='ativo' and l.ativo
 and v.concessionaria_id=new.concessionaria_id
 and v.papel in ('gestor','operador')
 and v.valido_desde<=statement_timestamp()
 and (v.valido_ate is null or v.valido_ate>statement_timestamp())
 limit 1 for share of e,v,l;
 if not coalesce(v_ok,false) then
  raise exception 'PROFISSIONAL_PRUMO_INELEGIVEL' using errcode='23514';
 end if;
 return new;
end $fn$;
create trigger s1_guard_atribuicao_nova
 before insert or update of operador_id,concessionaria_id,caso_id
 on public.atribuicoes_humanas for each row
 execute function prumo_private.s1_validar_nova_atribuicao();

-- Em cada transacao: encerra atribuicao anterior, escolhe apenas operador
-- ativo da mesma loja, registra trilha ou fila protegida.
create function prumo_private.s1_remanejar_ator(p_ator uuid,p_loja uuid,p_motivo text)
returns integer language plpgsql security invoker set search_path='' as $fn$
declare a record; v_destino uuid; n integer:=0;
begin
 if current_user<>'postgres' then raise exception 'INTERNAL_ONLY' using errcode='42501';end if;
 if p_ator is null or p_motivo not in ('EQUIPE_INATIVA','ESCOPO_REVOGADO')
 then raise exception 'INVALID_REASSIGN_INPUT' using errcode='22023';end if;
 for a in
  select x.id,x.atribuida_em,x.caso_id,x.concessionaria_id,c.status_comercial
  from public.atribuicoes_humanas x
  join public.casos_humanos h on h.id=x.caso_id and h.concessionaria_id=x.concessionaria_id
  join public.ciclos_comerciais c on c.id=h.ciclo_id and c.concessionaria_id=h.concessionaria_id
  where x.operador_id=p_ator and x.encerrada_em is null
   and (p_loja is null or x.concessionaria_id=p_loja)
  order by x.concessionaria_id,x.caso_id for update of x
 loop
  update public.atribuicoes_humanas set
   encerrada_em=greatest(a.atribuida_em,statement_timestamp())
   where id=a.id and encerrada_em is null;
  if a.status_comercial in ('vendido','perdido') then
   insert into prumo_private.s1_remanejamento_historico(
    concessionaria_id,caso_id,atribuicao_anterior_id,operador_anterior,motivo,resultado)
   values(a.concessionaria_id,a.caso_id,a.id,p_ator,p_motivo,'ENCERRADO_HISTORICO');
   n:=n+1;continue;
  end if;
  v_destino:=null;
  select v.ator_id into v_destino
  from public.vinculos_papel_escopo v
  join public.equipe_prumo_s1 e on e.ator_id=v.ator_id
  join public.concessionarias l on l.id=v.concessionaria_id
  where v.concessionaria_id=a.concessionaria_id and v.ator_id<>p_ator
   and v.papel='operador' and e.estado='ativo' and l.ativo
   and v.valido_desde<=statement_timestamp()
   and (v.valido_ate is null or v.valido_ate>statement_timestamp())
  order by (select count(*) from public.atribuicoes_humanas z
   where z.operador_id=v.ator_id and z.concessionaria_id=a.concessionaria_id
   and z.encerrada_em is null),v.ator_id
  limit 1 for share of e,v,l;
  if v_destino is null then
   insert into prumo_private.s1_remanejamento_pendencias(
    concessionaria_id,caso_id,operador_anterior,motivo)
   values(a.concessionaria_id,a.caso_id,p_ator,p_motivo)
   on conflict(concessionaria_id,caso_id) do update
   set operador_anterior=excluded.operador_anterior,motivo=excluded.motivo,
       registrado_em=statement_timestamp();
  else
   insert into public.atribuicoes_humanas(concessionaria_id,caso_id,operador_id)
   values(a.concessionaria_id,a.caso_id,v_destino);
   delete from prumo_private.s1_remanejamento_pendencias
   where concessionaria_id=a.concessionaria_id and caso_id=a.caso_id;
  end if;
  insert into prumo_private.s1_remanejamento_historico(
   concessionaria_id,caso_id,atribuicao_anterior_id,operador_anterior,
   operador_novo,resultado,motivo)
  values(a.concessionaria_id,a.caso_id,a.id,p_ator,v_destino,
   case when v_destino is null then 'FILA_PROTEGIDA' else 'REDISTRIBUIDO' end,p_motivo);
  n:=n+1;
 end loop;
 return n;
end $fn$;
create function prumo_private.s1_equipe_remanejar()
 returns trigger language plpgsql security invoker set search_path='' as $fn$
begin
 if old.estado='ativo' and new.estado<>'ativo' then
  perform prumo_private.s1_remanejar_ator(new.ator_id,null,'EQUIPE_INATIVA');
 end if;
 return new;
end $fn$;
create trigger s1_equipe_remanejar after update of estado on public.equipe_prumo_s1
 for each row when(old.estado is distinct from new.estado)
 execute function prumo_private.s1_equipe_remanejar();

-- Apenas quando cessou a ULTIMA concessao operacional de uma loja.
create function prumo_private.s1_escopo_remanejar()
 returns trigger language plpgsql security invoker set search_path='' as $fn$
begin
 if old.papel in ('operador','gestor')
 and old.valido_desde<=statement_timestamp()
 and (old.valido_ate is null or old.valido_ate>statement_timestamp())
 and not exists(select 1 from public.vinculos_papel_escopo v
  where v.ator_id=old.ator_id and v.concessionaria_id=old.concessionaria_id
  and v.papel in ('operador','gestor')
  and v.valido_desde<=statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>statement_timestamp()))
 then
  perform prumo_private.s1_remanejar_ator(old.ator_id,old.concessionaria_id,'ESCOPO_REVOGADO');
 end if;
 if tg_op='DELETE' then return old;end if;
 return new;
end $fn$;
create trigger s1_escopo_revogado_remanejar
 after update of ator_id,concessionaria_id,papel,valido_desde,valido_ate or delete
 on public.vinculos_papel_escopo for each row
 execute function prumo_private.s1_escopo_remanejar();
revoke execute on function prumo_private.s1_validar_nova_atribuicao(),
 prumo_private.s1_remanejar_ator(uuid,uuid,text),
 prumo_private.s1_equipe_remanejar(),prumo_private.s1_escopo_remanejar()
 from public,anon,authenticated,service_role;
