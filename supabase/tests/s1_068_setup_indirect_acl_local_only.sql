\set ON_ERROR_STOP on
-- I47: S0 synthetics deliberately created AFTER S1 038, only in I44 disposable stack.
-- Demonstrates that the old gate is NOT auto-applied to newly created objects.
-- Compatibilidade pontual da migration S0/006 omitida na base reduzida I44:
-- S0/011 exige FK (concessionaria_id,mensagem_id). S0/006 original cria
-- esta UNIQUE em mensagens; reproduzimos APENAS esse DDL no laboratorio.
alter table public.mensagens
 add constraint mensagens_loja_id_unique unique(concessionaria_id,id);
\ir ../migrations/202610170011_s0_c02_ambiguous_inbox.sql
\ir ../migrations/202610170012_s0_recontatos_sinteticos.sql
\ir ../migrations/202610170019_c07_callbacks_sinteticos.sql
\ir ../migrations/202610170020_c07_reconciliacao_falhas_sintetica.sql
notify pgrst, 'reload schema';
\echo 'I47: four S0 synthetics loaded AFTER S1 038 only in disposable CI'
