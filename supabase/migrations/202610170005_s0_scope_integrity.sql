-- S0: a identidade comercial do ciclo e do caso precisa corresponder ao mesmo lead
-- mesmo dentro da mesma concessionaria. FKs compostas complementam RLS.
alter table public.ciclos_comerciais
 add constraint ciclos_tenant_id_lead_unique
 unique(concessionaria_id,id,lead_id);
alter table public.casos_humanos
 add constraint casos_ciclo_lead_consistente
 foreign key(concessionaria_id,ciclo_id,lead_id)
 references public.ciclos_comerciais(concessionaria_id,id,lead_id) on delete restrict;
alter table public.casos_humanos
 add constraint casos_tenant_id_lead_unique
 unique(concessionaria_id,id,lead_id);
alter table public.conversas
 add constraint conversas_caso_lead_consistente
 foreign key(concessionaria_id,caso_id,lead_id)
 references public.casos_humanos(concessionaria_id,id,lead_id) on delete restrict;
