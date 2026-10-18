-- S1-002/I1: equipe Prumo, sem alterar estruturas multiloja S0.
-- Exclusivo para PostgreSQL descartavel; NAO aplicar em Supabase hospedado.
create table public.equipe_prumo_s1 (
 ator_id uuid primary key references public.atores(id) on delete restrict,
 estado text not null default 'pendente' check (estado in ('pendente','ativo','suspenso','desligado')),
 registrado_em timestamptz not null default statement_timestamp(),
 atualizado_em timestamptz not null default statement_timestamp()
);
create table public.equipe_prumo_eventos_s1 (
 id uuid primary key default gen_random_uuid(),
 ator_id uuid not null references public.atores(id) on delete restrict,
 estado_anterior text,
 estado_posterior text not null,
 ocorrido_em timestamptz not null default statement_timestamp()
);
create index equipe_eventos_ator_s1 on public.equipe_prumo_eventos_s1(ator_id,ocorrido_em);
alter table public.equipe_prumo_s1 enable row level security;
alter table public.equipe_prumo_eventos_s1 enable row level security;
revoke all on public.equipe_prumo_s1, public.equipe_prumo_eventos_s1 from public, anon, authenticated;
grant select on public.equipe_prumo_s1 to authenticated;
create policy equipe_self_s1 on public.equipe_prumo_s1
 for select to authenticated using (ator_id=(select auth.uid()));

-- Trilha SQL transacional. Nao equivale a prova do aprovador/admissão pela Prumo.
create function prumo_private.s1_equipe_before_update()
returns trigger language plpgsql security invoker set search_path=''
as $$
begin
 if new.ator_id is distinct from old.ator_id or new.registrado_em is distinct from old.registrado_em
 then raise exception 'identidade/data de criacao imutaveis' using errcode='23514'; end if;
 new.atualizado_em=pg_catalog.statement_timestamp();
 return new;
end $$;
create trigger s1_equipe_before_update before update on public.equipe_prumo_s1
 for each row execute function prumo_private.s1_equipe_before_update();

create function prumo_private.s1_equipe_auditar()
returns trigger language plpgsql security invoker set search_path=''
as $$
begin
 if tg_op='INSERT' then
  insert into public.equipe_prumo_eventos_s1(ator_id,estado_anterior,estado_posterior)
   values(new.ator_id,null,new.estado);
 elsif new.estado is distinct from old.estado then
  insert into public.equipe_prumo_eventos_s1(ator_id,estado_anterior,estado_posterior)
   values(new.ator_id,old.estado,new.estado);
 end if;
 return new;
end $$;
create trigger s1_equipe_auditar after insert or update of estado on public.equipe_prumo_s1
 for each row execute function prumo_private.s1_equipe_auditar();
create function prumo_private.s1_equipe_no_delete()
returns trigger language plpgsql security invoker set search_path=''
as $$
begin
 raise exception 'nao apagar historico organizacional' using errcode='23514';
end $$;
create trigger s1_equipe_no_delete before delete on public.equipe_prumo_s1
 for each row execute function prumo_private.s1_equipe_no_delete();
revoke execute on function prumo_private.s1_equipe_before_update(),
 prumo_private.s1_equipe_auditar(),prumo_private.s1_equipe_no_delete()
 from public,anon,authenticated;

-- Somente tabelas public/RLS existentes agora; novos objetos exigem revisao.
-- Gate restritivo: exige equipe ativa E todos os grants/atribuicoes preexistentes.
-- Funcoes comerciais SECURITY DEFINER postgres continuam fora do escopo.
do $$
declare r record;
begin
 for r in
  select c.relname from pg_catalog.pg_class c
  join pg_catalog.pg_namespace n on n.oid=c.relnamespace
  where n.nspname='public' and c.relkind in ('r','p') and c.relrowsecurity
  and c.relname not in ('equipe_prumo_s1','equipe_prumo_eventos_s1')
 loop
  execute format(
   'create policy s1_equipe_ativa_gate on public.%I as restrictive for all to authenticated
    using (exists (select 1 from public.equipe_prumo_s1 e
                   where e.ator_id=(select auth.uid()) and e.estado=''ativo''))
    with check (exists (select 1 from public.equipe_prumo_s1 e
                       where e.ator_id=(select auth.uid()) and e.estado=''ativo''))',
    r.relname);
 end loop;
end $$;
