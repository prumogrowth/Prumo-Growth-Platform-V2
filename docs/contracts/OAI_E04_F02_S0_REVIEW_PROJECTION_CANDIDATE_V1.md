# F02 E04 — adaptador de projeção S0 para solicitação de revisão (0.1-candidate)

**Data:** 26/10/2026. **Branch F02:** `feat/oai-s0-f03-history-port-20261023`; PR #1 continua Draft. Esta alteração **não importa** o módulo S0 de `exp/s0-f02-revisao-autoritativa-20261026`, não edita sua branch, banco nem workflow. Não há transporte S0 → F02 pronto para uso real.

## Entrega S0 efetivamente localizada

A S0 publicou o registro PG17/GoTrue/CFI para pedidos de revisão e `ReviewResult.projection()` em `backend/s0_f02_review_registry_local.py`, contrato `prumo.s0.f02.review.result/0.1-candidate`, aprovado em seu próprio CI [#40414847271](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40414847271). A S0 revalida sessão, escopo e CFI, conserva o estado persistente, retira por CAS e impede reabertura de tombstones. **Mas as quatro provas F03/C08/origem/intenção continuam alegadas**; decisão humana S1, opt-out, Meta, TTL produtiva, transporte UI e scheduling continuam pendentes. O próprio contrato S0 é candidato, sem aprovação de integração geral.

A fonte pinada deste laboratório é `OAI_E04_F02_S0_REVIEW_PROJECTION_PIN.json`, com branch/SHA/CI/schema e todos os estados. Ela registra a referência do schema publicada na S0 para revisão manual, **não traz identidade autenticada para dentro da F02**.

## Adaptador isolado da F02

`backend/f02_s0_review_projection_candidate.py` expõe `inspect_s0_review_projection(projection, handoff, window, previous=None)`, uma verificação pura (somente padrão Python) de dicionários, sem S0, GoTrue, SQL, HMAC, Meta, rede, filas ou mutações.

- Rejeita campos extras, omissões, versões inesperadas, permissões booleanas positivas, escopo de evidência e ratificação falsamente elevadas.
- Exige valores por tipo e formato compatíveis com `result.schema.json`: UUID de referência, revisão numérica decimal de PG `1..2147483647`, hash SHA-256 em minúsculas e horários timezone-aware.
- Vincula `request_sha256` ao `HandoffResult` local e `expires_at` à janela apresentada; compara instantes absolutos mesmo em fusos diferentes. **Esses dados continuam sujeitos à autenticação pela S0 no transporte futuro.**
- Estados `RECORDED` / `REPLAY` / `CURRENT` geram exclusivamente `PERSISTED_REVIEW_STATE_ONLY`; `WITHDRAWN` / `EXPIRED` geram `TERMINAL_REVIEW_STATE_ONLY`; recusas/erros geram `NEGATIVE_RESULT_RECHECK_ONLY`. Não expõe `review_ref`, token nem flags de ação no retorno.
- Quando dois envelopes são fornecidos, detecta identidade de registro alterada, revisão ou relógio regressivo e tentativa de reabrir `WITHDRAWN`/`EXPIRED`. Resposta negativa não apaga uma observação persistida anterior.
- Este adaptador **não** comprova que os envelopes vieram realmente da S0: um chamador pode forjar todos os campos. A validação serve apenas a contratos de laboratório; binding vivo, autenticação de serviço, lookup e provas cabem à S0/Frontend.

**Diferenças intencionais:** prazo candidato S0 é limite voluntário do pedido, sem teto 48h; os 48h da fixture F02 não viram política S0. A unicidade S0 é por `(loja, ator, chave)`, **não** por encerramento; o adaptador não inventa exclusividade comercial. Revogação de pedido técnico não é cancelamento Meta. Não substituir `evaluate_bound_review_lifecycle` ou `evaluate_review_recovery` por uma aprovação S0 imaginária.

**Cobertura:** `backend/tests/test_f02_s0_review_projection_candidate.py` acrescenta 28 testes unitários para envelope, estados, contradições, digest, datas, revisão, continuidade e proibição de capacidades comerciais. Matriz F02-A21, nova entrada do runner experimental. Todos permanecem sujeitos a CI da própria branch; não declarar certificação antes de SUCCESS.

**Gates de integração para Codex/S0:** ratificar ou versionar schema; definir transporte autenticado e lookup/binding D3; ligar encerramento real F01/F03/C08/origem; gestores S1 distintos e ratificação formal; política temporal, retenção/opt-out/template e decisão Meta. A F02 consome estados read-only somente após ratificação do contrato, sem converter resposta técnica em execução.

**Sem** merge, deploy, main, Supabase hospedado, contato real, Meta ou migrações de produção.
