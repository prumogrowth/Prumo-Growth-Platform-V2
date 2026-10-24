# E04/S0-F03 — 251 testes PG17 e bloqueio CAS por pendência de identidade S0/028

**Data:** 24/10/2026. **Repositório oficial único:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`. Desenvolvimento apenas na branch `feat/oai-s0-f03-history-port-20261023`, PR Draft #1 contra `feat/s0-cfi01-f03-auth-preflight-20261020` (nunca diretamente na `main`). Toda a validação usa dados fictícios, PostgreSQL 17 local descartável no GitHub Actions, sem chamada OpenAI, Meta, banco, Supabase hospedado ou implantação.

## Evidência executada

- [**GitHub Actions #40081896755**](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40081896755), commit `1b10f05e3d591377f406efcd7fb91c9c3a907556`: **245/245 PASS** no PostgreSQL **17.11**, incluindo 16 novos testes físicos de aliases e evento de identidade S0/028.
- [**GitHub Actions #40082164368**](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40082164368), commit `1e790b17c614f84253a23d7e681917c973334299`: **251/251 PASS**, sendo `Ran 84 tests ... OK` da S0 e `Ran 167 tests ... OK` da F03; **79 testes físicos PG17 da F03**. Os novos testes 74–79 efetivamente executados cobrem bloqueio de reserva quando existe conflito S0 sem pessoa ratificada para número exato, variante brasileira ou alias conhecido, exceção para telefone não relacionado, isolamento entre concessionárias e bloqueio do replay de reserva anterior.

## Alterações de código e fixture (E04 exclusivamente)

No [relatório da primeira rodada](./S0_F03_ALIASES_S0_028_CAS_PG17_245_TESTES_2026_10_24.md) estão os gatilhos de invalidação de `versao_identidade` nas tabelas existentes `prumo_private.aliases_identidade_s0` e `prumo_private.eventos_identidade_s0`, carregando a **migração sintética S0/028 real** no runner, com dois papéis NOLOGIN auxiliares de laboratório. Confirmado que o resolvedor S0/028 `resolver_contato_s0` registra alias+evento e que isso invalida uma reserva com versão antiga.

O [`backend/s0_f03_version_reservation_local.py`](../backend/s0_f03_version_reservation_local.py) passou também a consultar **`prumo_private.pendencias_identidade_s0`** durante a transação de reserva, depois das travas e conferência do vetor. É `CONFLICT_REVIEW_REQUIRED` se uma pendência daquela concessionária corresponde ao telefone principal ou a qualquer alias já associado ao lead, por correspondência exata ou pela chave de variante brasileira implementada pela S0. **Não determina nem sugere que a pendência pertence ao lead; apenas recusa a decisão F03 para contatos potencialmente afetados.** A busca de pendência é limitada ao escopo da mesma loja. A proposta não é persistida quando é recusada. Uma reserva consultiva que já exista também deixa de passar pelo recheck enquanto a pendência corresponder. O bloqueio não altera o status comercial, não mescla clientes e não escreve dados da ficha.

## Lacunas e próximos gates obrigatórios

1. A tabela S0 de pendências contém telefone, canal, motivo e evidência sintética, mas **não dispõe de estado de resolução ratificado ou identidade vinculada**. Este gate é conservador e pode continuar bloqueando uma pessoa até que a S0 implemente uma resolução imutável/auditável; **F03 não deve resolver ambiguidades autonomamente**.
2. Alias versão e o gate de pendências valem para a S0/028 coberta pelos testes; mudanças introduzidas por outros escritores, concursos de inserção de pendência durante uma reserva e novos padrões de telefone precisam de transação/ledger de encerramento completo antes de qualquer gravação real. A reserva é **consultiva, `REVIEW_ONLY`**, não aplicação de cadastro.
3. Ainda faltam fonte operacional de ficha/catálogo, garantia de integridade de mídias/transcrições, política de segredo/rotação HMAC, acesso mínimo LGPD, reconciliação completa de identidade e transação única de aplicação com CAS e auditoria de valores campo a campo sob responsabilidade da S0.
4. S0 tem governança compartilhada: a frente OpenAI desenvolve a adaptação do portão da F03, mantendo F01/F02/F03 sob sua responsabilidade e sem tocar em branches de outras frentes. Não houve merge, deploy, mudança de `main`, E05, dados reais, API paga nem publicação de segredo.

**Necessidade externa hoje:** nenhuma. O PostgreSQL 17 descartável do GitHub Actions está funcionando. Um sistema de resolução humana de pendências da S0 será desenhado/testado antes de permitir a F03 em produção.
