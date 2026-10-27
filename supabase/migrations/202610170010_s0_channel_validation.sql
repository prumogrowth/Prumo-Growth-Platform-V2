-- Auditoria S0/C02: nao aceitar canal emissor sem identificador confiavel.
-- Meta ID/número canônico ainda deverá ser validado no adaptador autenticado.
alter table public.canais_loja
 add constraint canais_identificador_emissor_nao_vazio
 check (
   length(btrim(identificador_emissor)) > 0
   and identificador_emissor = btrim(identificador_emissor)
   and identificador_emissor !~ '[[:cntrl:]]'
 );
-- A exclusividade global ja existe desde a migration 003:
-- `identificador_emissor text NOT NULL UNIQUE`.
-- Nenhuma UNIQUE global sobre telefone de cliente.
