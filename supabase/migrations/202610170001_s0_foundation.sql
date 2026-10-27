-- S0 candidato; auth.users Supabase. Executar primeiro apenas em PG descartável.
create extension if not exists pgcrypto;
create table public.concessionarias (
 id uuid primary key default gen_random_uuid(),
 nome_operacional text not null check (length(trim(nome_operacional))>0),
 ativo boolean not null default true,
 criado_em timestamptz not null default now(),
 versao_registro bigint not null default 1 check (versao_registro>0)
);
create table public.atores (
 id uuid primary key references auth.users(id) on delete restrict,
 criado_em timestamptz not null default now()
);
create table public.vinculos_papel_escopo (
 id uuid primary key default gen_random_uuid(),
 ator_id uuid not null references public.atores(id) on delete restrict,
 concessionaria_id uuid not null references public.concessionarias(id) on delete restrict,
 papel text not null check (papel in ('gestor','operador','responsavel')),
 valido_desde timestamptz not null default now(),
 valido_ate timestamptz,
 criado_em timestamptz not null default now(),
 check (valido_ate is null or valido_ate > valido_desde)
);
create index vinculos_ativos_idx on public.vinculos_papel_escopo(ator_id,concessionaria_id,papel,valido_ate);
create table public.leads_loja (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null references public.concessionarias(id) on delete restrict,
 telefone_cliente_normalizado text not null check (length(telefone_cliente_normalizado)>0),
 criado_em timestamptz not null default now(),
 unique(concessionaria_id,id),
 unique(concessionaria_id,telefone_cliente_normalizado)
);
create table public.ciclos_comerciais (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 lead_id uuid not null,
 status_comercial text not null default 'aguardando primeiro disparo' check (status_comercial in (
 'aguardando primeiro disparo','primeiro disparo enviado','em atendimento pela IA',
 'em atendimento pelo operador','cadastro enviado ao operador',
 'cadastro enviado ao banco','vendido','perdido')),
 aberto_em timestamptz not null default now(),
 ultima_transicao_em timestamptz not null default now(),
 versao_registro bigint not null default 1 check(versao_registro>0),
 unique(concessionaria_id,id),
 foreign key(concessionaria_id,lead_id) references public.leads_loja(concessionaria_id,id) on delete restrict
);
create index ciclos_loja_lead_idx on public.ciclos_comerciais(concessionaria_id,lead_id,aberto_em);
alter table public.concessionarias enable row level security;
alter table public.atores enable row level security;
alter table public.vinculos_papel_escopo enable row level security;
alter table public.leads_loja enable row level security;
alter table public.ciclos_comerciais enable row level security;
revoke all on public.concessionarias,public.atores,public.vinculos_papel_escopo,public.leads_loja,public.ciclos_comerciais from anon, authenticated;
