-- Decisao posterior do responsavel (17/10/2026): telefone comercial do cliente
-- nao pode ser cadastrado em concessionarias diferentes na Prumo.
-- ALTERA as propostas historicas 25/30/38/43; nao unifica historicos existentes.
-- Caso nao haja proprietario do telefone definido, reprovar importacao em nova loja,
-- jamais mover lead/historico ou revelar a concessionaria de origem.
alter table public.leads_loja
 add constraint leads_numero_cliente_exclusivo_global
 unique (telefone_cliente_normalizado);
alter table public.leads_loja
 add constraint leads_telefone_e164 check
 (telefone_cliente_normalizado ~ '^\+[1-9][0-9]{9,14}$');
-- FK compostas e RLS por loja continuam obrigatorios.
