-- C02 simulado: preservar inbound cujo ciclo nao pode ser desambiguado.
-- Nao adivinhar ciclo, nao acionar IA e nao criar falso caso humano.
create table public.pendencias_inbound_simulado (
 id uuid primary key default gen_random_uuid(),
 concessionaria_id uuid not null,
 canal_id uuid not null,
 lead_id uuid not null,
 mensagem_id uuid not null,
 motivo text not null check(motivo='MULTIPLOS_CICLOS'),
 criado_em timestamptz not null default now(),
 unique(concessionaria_id,mensagem_id),
 foreign key(concessionaria_id,canal_id)
   references public.canais_loja(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,lead_id)
   references public.leads_loja(concessionaria_id,id) on delete restrict,
 foreign key(concessionaria_id,mensagem_id)
   references public.mensagens(concessionaria_id,id) on delete restrict
);
create index pendencias_inbound_loja_idx
 on public.pendencias_inbound_simulado(concessionaria_id,criado_em);
alter table public.pendencias_inbound_simulado enable row level security;
revoke all on public.pendencias_inbound_simulado from public,anon,authenticated;
grant select on public.pendencias_inbound_simulado to authenticated;
create policy pendencias_inbound_select_gestor
 on public.pendencias_inbound_simulado for select to authenticated
 using (exists(
  select 1 from public.vinculos_papel_escopo v
  where v.ator_id=(select auth.uid()) and v.concessionaria_id=pendencias_inbound_simulado.concessionaria_id
    and v.papel='gestor' and v.valido_desde<=statement_timestamp()
    and (v.valido_ate is null or v.valido_ate>statement_timestamp())
 ));
-- Esta pendencia precisa de tratamento HUMANO autorizado antes de qualquer
-- associacao a ciclo ou resposta; nao representa caso atribuido automaticamente.
