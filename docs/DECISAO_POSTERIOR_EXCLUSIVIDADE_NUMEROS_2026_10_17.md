# REGISTRO RETRATADO — interpretação incorreta de números

**Status: RETRATADO / NÃO VIGENTE.** Este documento registrou uma interpretação equivocada sobre a unicidade do telefone do cliente e NÃO deve ser usado como requisito técnico.

## Esclarecimento final de 17/10/2026, confirmado pelo responsável

1. **Telefone do cliente:** pode constar em concessionárias A, B e C simultaneamente, cada uma com seu lead, ciclo, conversas e histórico próprios e isolados. A unicidade é `(concessionaria_id, telefone_cliente_normalizado)`.
2. **Número de atendimento da Prumo (emissor/receptor WhatsApp):** não pode ser vinculado a duas concessionárias distintas. `canais_loja.identificador_emissor` mantém unicidade global.

## Reparação

- A migração 007 que criava índice UNIQUE global de cliente foi **excluída da branch antes de qualquer implantação**.
- A função interna de importação 006 voltou a deduplicar telefone por concessionária, não por plataforma.
- Os testes de mesma pessoa nas lojas A/B e de isolamento entre elas foram restaurados.
- O teste de concorrência multiloja deve aprovar dois leads/ciclos da mesma pessoa e nenhum cruzamento de dados.
- A migração 008 de acesso limitado do operador permanece, por ser um reparo independente e válido.

Este registro retratado permanece apenas para rastreabilidade dos commits. **Documento vigente de substituição:** `docs/REGRA_NUMEROS_ATENDIMENTO_CLIENTE_2026_10_17.md`.

Nenhuma migração comercial foi aplicada ao Supabase remoto; não foram afetados dados reais.
