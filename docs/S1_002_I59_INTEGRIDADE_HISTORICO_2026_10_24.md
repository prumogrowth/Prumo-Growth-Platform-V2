# S0/S1-002 — I59: integridade do histórico por contato e concessionária

**Data:** 24/10/2026. **Local de desenvolvimento:** branch `feat/s1-002-equipe-prumo`; sem merge e sem deploy.

## Constatação

A S0 possui FK composta `casos_humanos(concessionaria_id,id,lead_id)` via migration `202610170005`, mas `conversas` mantinha FKs independentes: `(concessionaria_id,lead_id)` e `(concessionaria_id,caso_id)`. Era possível associar uma conversa do contato B ao caso do contato A **dentro da mesma loja** sem violar as constraints anteriores. As policies candidatas I41/I42/I43 autorizam conversas e mensagens por caso e contato; uma associação desse tipo enfraquece a fronteira do histórico. Também é relevante para acesso D2/D3/D4, ainda não totalmente integrado.

## I59 implementado

A migration incremental `202610190058_s0_conversa_integridade_contato.sql` instala **FK composta validada** `(concessionaria_id,caso_id,lead_id)` contra `casos_humanos(concessionaria_id,id,lead_id)`. Proíbe gravação e alteração de vínculos caso/contato inconsistentes, preservando `caso_id=NULL` na conversa ainda sem atendimento humano. A validação padrão do PostgreSQL é intencional: se houver dados anteriores inconsistentes, a migration falha sem corrigir registros automaticamente.

Não amplia nenhuma RLS, grant, exposição Data API, função SECURITY DEFINER, sessão ou permissão para exceções. Não cria tabela de histórico separada. As policies I43/I44 continuam **candidatas de laboratório**: não foram promovidas a contrato operacional porque a tabela de exceções I55 ainda é fixture, exigindo homologação conjunta.

## Evidências obrigatórias

- PG17: `s1_083_integridade_conversas_i59_aceite.sql`, 7 testes (válido, contato trocado, caso trocado, multi-loja, caso nulo e constraint verificada).
- GoTrue/PostgREST: `test_s1_002_i59_real_auth_read.py`, importado pelo runner I44; 4 testes no ambiente de autenticação real descartável, sem permitir associação cruzada e preservando histórico por equipe.
- Regressão I52–I58 e I44/I45–I50 sem alargar escopos.

## Limites

A FK reforça integridade referencial, **não** substitui a RLS, a autenticação real, nem revisa acesso a mídia/anexos, D3/D4 e documentos financeiros. Em produção, executar preflight de `conversas` que referenciam `casos_humanos` com `lead_id` diferente antes de aplicar constraint; nenhuma migração ou correção de dados hospedados é autorizada agora.

## Evidências de CI certificadas — 24/10/2026

- **PostgreSQL 17 — SUCCESS:** [workflow #40138406969](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40138406969), job `121004763301`, commit de código `37811fbc975bfbb7ea6448a34df365a3b64be310`. Logs inspecionados: `PASS I59-01` a `PASS I59-07` **7/7**; `PASS S0+S1 I52-I59 canonical stages after legacy regression`. A restrição é `convalidated` no catálogo e recusa mudar caso ou contato mesmo dentro da mesma loja.
- **GoTrue + PostgREST local — SUCCESS:** [workflow #40138602605](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40138602605), job `121005341078`, SHA `0fc98f364e82b58e213ab150dfd6dffedd47d127`. Logs conferidos: `I59-REST-01..04` **4/4**; `I44-01..06` **6/6**, com regressões `I45-01..06`, `I46-01..06`, `I47-01..06`, `I48-01..06`, `I49-01..06` e `I50-01..06`.
- **Falha de fixture preservada:** [workflow I44 #40138406910](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40138406910) concluiu com falha porque o teste I59 esperava três mensagens históricas do Gestor, mas o próprio I44-04 tinha inserido uma quarta mensagem legítima. A asserção foi corrigida em `0fc98f3` sem mudar a FK canônica ou o código de autorização. A execução #40138602605 é o aceite GoTrue definitivo.

**Situação de fechamento:** I59 implementado e testado em laboratório PG17 e GoTrue real-local. Não houve merge, deploy, migração hospedada, clientes reais, mensagens Meta ou ação bancária. A promoção de RLS I41/I42/I43, mecanismos completos de exceção por caso e D3/D4 continuam exigindo integração formal com S0 e política final de segurança.
