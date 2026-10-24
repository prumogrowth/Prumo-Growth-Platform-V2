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
