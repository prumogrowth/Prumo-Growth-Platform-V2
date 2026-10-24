# E04 / S0–F03 — Terceiro fechamento humano de pendência e prova HMAC — 307 testes PG17

**Data:** 24/10/2026. **Repositório oficial único:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`. Desenvolvimento exclusivo na branch `feat/oai-s0-f03-history-port-20261023`, [PR #1 Draft](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/1), baseado em `feat/s0-cfi01-f03-auth-preflight-20261020` (nunca `main`). Todas as operações foram sintéticas, com PostgreSQL descartável; nenhum dado, login, API ou banco de produção.

## Evidência física

**[GitHub Actions #40131714426](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40131714426)**, commit `efdeca81d41995a8fbf9f9df6e90c1864b5cc684`: **SUCCESS no PostgreSQL 17.11**.

| Suíte | Resultado |
|---|---:|
| S0 CFI-01 / fechamento assinado e pré-requisitos | **84/84 OK** |
| F03 leitor, manifesto, HMAC, CAS, identidade, revisão e fechamento | **223/223 OK** |
| Dentro da F03: testes físicos PG17 | **135/135 OK** |
| **Total** | **307/307 PASS** |

Os **20 cenários físicos novos `test_116` a `test_135`** passaram, cobrindo independência da terceira pessoa, integridade HMAC da pendência, versão de chave, replay, concorrência, chave inválida, autenticação/S1, papel, ciclo, versão de identidade, alteração do telefone, não liberação de F03, imutabilidade, ACL e negação de gestor com papel expirado. `Ran 84 tests ... OK` e `Ran 223 tests ... OK` foram observados nos logs.

## Três atos independentes

1. **Revisão humana:** operador S0/S1 autorizado registra `CANDIDATE_NOT_RELATED` sob contexto, sessão, atribuição e versão de identidade. Recibo na tabela `cfi01_f03_identity_human_reviews_local`.
2. **Ratificação:** outro gestor, diferente do operador, com sessão e papel ativo valida o parecer negativo e gera `RATIFIED_AUDIT_ONLY`. Recibo na `cfi01_f03_identity_ratifications_local`.
3. **Fechamento de resolução em espera:** um **terceiro gestor** diferente dos dois anteriores emite `CLOSED_HOLD_ONLY` somente se o caso/atribuição continua válido, os dois recibos anteriores são coerentes, a versão do ciclo e da identidade não mudou, a pendência continua correspondendo ao lead candidato e seu conteúdo pode ser comprovado por HMAC interno da S0.

Arquivos adicionados na mesma branch:
- [Porta S0 Python](../backend/s0_f03_identity_resolution_local.py): autenticação no lado servidor, trava da equipe S1 antes do contexto, conferência de escopo do gestor, pendência e versões em transação, HMAC-SHA256 com chave de pelo menos 32 bytes entregue em runtime (testes usam chave fictícia), idempotência estrita e concorrência de tentativas de fechamento.
- [Fixture de ledger SQL](../supabase/tests/s0_f03_identity_resolution_local_only.sql): tabela privada com referências a revisão, ratificação, lead, terceiro ator, sessão, versões, identificador da chave, HMAC de conteúdo da pendência, hash da evidência e chave idempotente; não contém o conteúdo da pendência. Trigger impõe a separação dos três atores, os vínculos e versões atuais. Uma linha por loja+pendência+caso, somente append; UPDATE/DELETE proibidos; RLS e privilégios negados a `authenticated` e `service_role`. **Apenas fixture, não migration hospedada.**
- [Executor PG17](../scripts/run-s0-f03-pg17-local.sh), atualizado para incluir a fixture nova.
- [Testes de integração](../backend/tests/test_s0_f03_pg17_integration.py), agora com 135 testes PG17 para F03.

## O que é e o que NÃO é resolução definitiva

Este terceiro ato **conclui a cadeia de revisão humana e captura um recibo verificável**, mas o estado resultante é deliberadamente `CLOSED_HOLD_ONLY`. **A pendência S0/028 não é excluída, marcada como resolvida nem associada definitivamente a uma pessoa**. Isso é intencional: nenhum dos três atos, isolado ou em conjunto, constitui confirmação suficiente de identidade civil, consentimento, completude de conflitos entre leads ou autorização para enviar conteúdo ao modelo F03. O CAS da F03 **continua retornando `CONFLICT_REVIEW_REQUIRED`** quando encontra a pendência, mesmo após o fechamento. O teste 131 comprova isso.

A prova HMAC do material sintético vincula IDs, escopo, caso, versões e os campos da pendência ao comprovante. Detecta edição posterior quando reprocessada pela mesma chave. Porém **não substitui política operacional de chaves e rotação**, proteção de novos escritores de pendências e alias, conciliação de possíveis clientes concorrentes, nem fechamento transacional de todo o conjunto de contatos. O teste injeta identidades S0 de laboratório, **não usa GoTrue hospedado**.

## Próximos gates

- Criar **verificador S0 de vigência do terceiro recibo**, capaz de comparar conteúdo atual e versões com HMAC, detectando revogação/alteração e protegendo leituras mesmo após fechamento.
- Integrar a versão/estado de conflitos ao conjunto de fontes S0 com garantias sob transações concorrentes; exigir comprovação de que **todos os leads candidatos** relevantes foram verificados, não só um.
- Só após revisão de segurança e contrato de negócio, criar um gate explícito S0 de liberação de pendência — **independente de F03**, revogável, autenticado e sujeito a CAS. Até então, todos os retornos permanecem `*_HOLD_ONLY` ou `*_REVIEW_ONLY`.
- Depois conectar ficha e catálogo operacionais, prova de mídia, LGPD, política de chave HMAC, aplicação campo a campo com CAS e E05, caso especificamente autorizada. Nada disso foi implementado nesta rodada.

**Restrições cumpridas:** sem modificações no repositório anterior, sem merge, sem deploy, sem `main`, sem alterar a branch S0 de base, sem dados reais e sem chamadas a OpenAI/Meta/Supabase hospedada. Não é necessário nenhum recurso adicional do responsável para continuar E04.
