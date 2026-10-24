-- I59: block case-history cross-contact through canonical S0 conversations.
-- No special SELECT grant, public RPC, messages, customer data or RLS expansion.
-- This validated FK deliberately FAILS on legacy mismatches; never auto-repair.
begin;
alter table public.conversas
 add constraint s0_conversa_caso_lead_i59
 foreign key (concessionaria_id,caso_id,lead_id)
 references public.casos_humanos(concessionaria_id,id,lead_id)
 on update restrict on delete restrict
 deferrable initially immediate;
commit;
