-- Prumo S0: canais, lotes, histórico, casos e conversa SIMULADOS; nunca produção sem revisão.
create table public.canais_loja (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null references public.concessionarias(id) on delete restrict,
 identificador_emissor text not null unique,
 modo text not null default 'simulado' check (modo='simulado'),
 criado_em timestamptz not null default now(),
 unique(concessionaria_id,id)
);
create table public.lotes_importacao (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null references public.concessionarias(id) on delete restrict,
 chave_importacao text not null check(length(trim(chave_importacao))>0),
 origem text not null default 'simulado' check(origem='simulado'),
 criado_em timestamptz not null default now(),
 unique(concessionaria_id,id),
 unique(concessionaria_id,chave_importacao)
);
create table public.itens_lote (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 lote_id uuid not null,
 ordinal_linha integer not null check(ordinal_linha>0),
 lead_id uuid not null,
 criado_em timestamptz not null default now(),
 foreign key(concessionaria_id,lote_id) references public.lotes_importacao(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,lead_id) references public.leads_loja(concessionaria_id,id) on delete restrict,
 unique(concessionaria_id,lote_id,ordinal_linha)
);
create table public.reencontros_lote (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 lote_id uuid not null,
 lead_id uuid not null,
 motivo text not null default 'reimportacao' check(motivo='reimportacao'),
 criado_em timestamptz not null default now(),
 foreign key(concessionaria_id,lote_id) references public.lotes_importacao(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,lead_id) references public.leads_loja(concessionaria_id,id) on delete restrict,
 unique(concessionaria_id,lote_id,lead_id)
);
create table public.eventos_status_comercial (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 ciclo_id uuid not null,
 versao_ciclo_apos bigint not null check(versao_ciclo_apos>1),
 status_anterior text not null,
 status_posterior text not null,
 tipo_origem text not null default 'simulacao' check(tipo_origem='simulacao'),
 criado_em timestamptz not null default now(),
 foreign key(concessionaria_id,ciclo_id) references public.ciclos_comerciais(concessionaria_id,id) on delete restrict,
 unique(concessionaria_id,ciclo_id,versao_ciclo_apos),
 check(status_anterior in ('aguardando primeiro disparo','primeiro disparo enviado','em atendimento pela IA','em atendimento pelo operador','cadastro enviado ao operador','cadastro enviado ao banco','vendido','perdido')),
 check(status_posterior in ('aguardando primeiro disparo','primeiro disparo enviado','em atendimento pela IA','em atendimento pelo operador','cadastro enviado ao operador','cadastro enviado ao banco','vendido','perdido'))
);
create table public.casos_humanos (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 lead_id uuid not null,
 ciclo_id uuid not null,
 origem text not null default 'simulacao' check(origem='simulacao'),
 criado_em timestamptz not null default now(),
 unique(concessionaria_id,id),
 foreign key(concessionaria_id,lead_id) references public.leads_loja(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,ciclo_id) references public.ciclos_comerciais(concessionaria_id,id) on delete restrict
);
create table public.atribuicoes_humanas (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 caso_id uuid not null,
 operador_id uuid not null references public.atores(id) on delete restrict,
 atribuida_em timestamptz not null default now(),
 encerrada_em timestamptz,
 foreign key(concessionaria_id,caso_id) references public.casos_humanos(concessionaria_id,id) on delete restrict,
 check(encerrada_em is null or encerrada_em>=atribuida_em)
);
create unique index uma_atribuicao_ativa_por_caso
 on public.atribuicoes_humanas(concessionaria_id,caso_id) where encerrada_em is null;
create index atribuicoes_ativas_operador on public.atribuicoes_humanas(operador_id,concessionaria_id,caso_id) where encerrada_em is null;
-- Concessão do operador deve ser vigente NA LOJA e papel operador/gestor.
create function public.s0_verificar_atribuicao()
 returns trigger language plpgsql security invoker set search_path=''
as $$
begin
 if not exists(
  select 1 from public.vinculos_papel_escopo v
  where v.ator_id=new.operador_id and v.concessionaria_id=new.concessionaria_id
  and v.papel in ('gestor','operador')
  and v.valido_desde<=pg_catalog.statement_timestamp()
  and (v.valido_ate is null or v.valido_ate>pg_catalog.statement_timestamp())
 ) then
  raise exception 'operador sem concessao ativa na loja' using errcode='23514';
 end if;
 return new;
end $$;
create trigger trg_s0_verificar_atribuicao before insert or update of operador_id,concessionaria_id,caso_id
 on public.atribuicoes_humanas for each row execute function public.s0_verificar_atribuicao();
revoke execute on function public.s0_verificar_atribuicao() from public, anon, authenticated;
create table public.conversas (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 lead_id uuid not null,
 canal_id uuid not null,
 caso_id uuid,
 origem text not null default 'simulado' check(origem='simulado'),
 criada_em timestamptz not null default now(),
 unique(concessionaria_id,id),
 unique(concessionaria_id,id,canal_id),
 unique(concessionaria_id,id,caso_id),
 foreign key(concessionaria_id,lead_id) references public.leads_loja(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,canal_id) references public.canais_loja(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,caso_id) references public.casos_humanos(concessionaria_id,id) on delete restrict
);
create table public.mensagens (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 conversa_id uuid not null,
 canal_id uuid not null,
 caso_id uuid,
 direcao text not null check(direcao in ('entrada','saida')),
 origem text not null default 'simulado' check(origem='simulado'),
 conteudo_sintetico text not null check(length(conteudo_sintetico)>0),
 id_externo text,
 enviada_por uuid references public.atores(id) on delete restrict,
 criada_em timestamptz not null default now(),
 foreign key(concessionaria_id,conversa_id,canal_id) references public.conversas(concessionaria_id,id,canal_id) on delete restrict,
 foreign key(concessionaria_id,conversa_id,caso_id) references public.conversas(concessionaria_id,id,caso_id) on delete restrict,
 check (direcao <> 'entrada' or (id_externo is not null and enviada_por is null)),
 check (direcao <> 'saida' or (caso_id is not null and enviada_por is not null and id_externo is null))
);
create unique index mensagens_inbound_unique
 on public.mensagens(concessionaria_id,canal_id,id_externo)
 where direcao='entrada' and id_externo is not null;
create index mensagens_por_conversa on public.mensagens(concessionaria_id,conversa_id,criada_em);
-- RLS deny-by-default até aplicação da migration de grants/policies.
alter table public.canais_loja enable row level security;
alter table public.lotes_importacao enable row level security;
alter table public.itens_lote enable row level security;
alter table public.reencontros_lote enable row level security;
alter table public.eventos_status_comercial enable row level security;
alter table public.casos_humanos enable row level security;
alter table public.atribuicoes_humanas enable row level security;
alter table public.conversas enable row level security;
alter table public.mensagens enable row level security;
revoke all on public.canais_loja, public.lotes_importacao, public.itens_lote,
 public.reencontros_lote, public.eventos_status_comercial, public.casos_humanos,
 public.atribuicoes_humanas, public.conversas, public.mensagens from anon, authenticated;
