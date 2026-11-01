# Remediação AUD-PD-01..05 — S0/S1 PRE_DISPATCH v0.2 em PostgreSQL 17

**Data:** 01/11/2026 · **Status:** `AUD_PD_01_05_CORRIGIDOS_PG17_LAB`, **não homologado operacionalmente**.  
**Issue:** [#10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10)  
**Base congelada:** `45f15c831c3f6a7479a686622d92247f07005000`  
**Relatório de origem:** [Auditoria geral S0/S1](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/ca74079d78a9819e1c869cb597a7e43d9b4cb3b4/docs/auditorias/S0S1_AUDITORIA_GERAL_2026-11-01.md) e [contraprovas físicas](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41352714481), 5 lacunas demonstradas.  
**Branch exclusiva de correção:** `fix/s0s1-pd-v02-audit-invariants-20261101`.

## Escopo e evidência

Remediação **apenas da porta física de laboratório S0 PRE_DISPATCH v0.2**. A porta antiga `prumo.s0.pre-dispatch.pg17/0.1-lab-only`, adaptador M18, código Meta original, M09/Ingresso S0, OpenAI e Frontend permanecem **imutáveis**. A alteração da assinatura de `cancel()` é deliberada: agora exige os objetos privados `principal` e `m09_versions`. Chamadores antigos que forneçam somente `HostScope` recebem `DENIED/INVALID_REQUEST`; não há fallback inseguro. O consumidor físico anterior e o emissor de evidência M18 foram exercitados com a nova fixture.

## Matriz de correção por contraprova

| Achado | Antes (auditado) | Depois (candidato) | Verificação |
|---|---|---|---|
| AUD-PD-01 — finalidade de template | `LAB_COMMITTED_RECEIPT_NO_DISPATCH` mesmo após mudança silenciosa `templates.template_purpose_ref` | `LAB_STALE_NO_DISPATCH/TEMPLATE_CAMPAIGN_GRANT_STALE` | `test_aud_pd_01` |
| AUD-PD-02 — finalidade do grant | `LAB_COMMITTED_RECEIPT_NO_DISPATCH` apesar de divergência em `grants.template_purpose_ref` | Revalidação da finalidade original, estado/revisão e vínculo `campaign.case_ref/template_ref/template_version`; retorna STALE | `test_aud_pd_02` |
| AUD-PD-03 — vínculo M09 | Alteração de `s0_m09_lab.grants.phone_number_id` não detectada | Readback reconfere identidade da rota, binding, principal/issuer/chave, App/tenant/validade, grant com route/App/WABA/phone e unicidade observada de canal/phone/WABA; retorna STALE | `test_aud_pd_03`, `test_09` |
| AUD-PD-04 — reset de quota | `consumed` podia diminuir para zero sem revision bump, preservando recibo | Trigger PG17 nega decremento; índice `UNIQUE(store_ref,app_ref,phone_ref,window_ref,quota_slot)` impede reutilização do slot; readback exige `quota.consumed >= receipt.quota_slot` e `quota.capacity >= receipt.quota_slot` | `test_aud_pd_04`, `test_11` |
| AUD-PD-05 — cancelamento com WABA divergente | Apenas store/App/route/channel/phone conferidos | Confere também WABA, serviço e `scope_digest` calculado de escopo + principal/issuer/key_revision + cinco revisões M09 originais; ausência de principal ou desvio de WABA/key nega sem mutação | `test_aud_pd_05`, `test_06`, `test_07` |

## Observações de desenho e limites

1. A checagem M09 do readback é **read-only**, não faz segunda reserva nem gera novo registro de point-of-use. Mantém seis tipos de escopo sob a mesma transação e exige datas de validade do principal/App. A identidade M2M/HostScope ainda é **fixture injetada**, não prova de autenticação de sistema hospedado.
2. O trigger de quota protege `UPDATE` que diminua `consumed`, inclusive durante ensaio admin. Não converte uma tabela de quota simulada em rate limit real do gateway, nem impede um administrador superprivilegiado de executar DDL ou `TRUNCATE`. Segurança de produção exige ACL, journal/outbox imutável e custódia externa. O índice único protege slots de uma mesma janela; não prova entrega ou send. Estados de cancelamento **não reembolsam** quota.
3. Rechecks com múltiplos `SELECT` sob `READ COMMITTED` continuam **não linearizáveis** diante de escritores hospedados não cooperativos. A correção de cinco invariantes **não** encerra `AUD-ARQ-01` (snapshot/lock), `AUD-ARQ-02` (attestation de tentativa), `AUD-ARQ-03` (contrato M18-D), `AUD-ARQ-04` (divergência da main) ou `AUD-ARQ-05` (REVOKE hosted). Esses itens seguem como bloqueadores anteriores à integração operacional.
4. A assinatura de `cancel` foi alterada propositalmente para falhar fechado em consumidores antigos. Antes de promover qualquer API, Meta/S0 devem acordar nova versão formal para chamadas de cancelamento; não fingir compatibilidade retroativa e não expor admin fixtures.
5. A versão semântica `prumo.s0.pre-dispatch.readback/0.2-lab` continua **exclusivamente LAB**. Todos os retornos preservam `host_authenticated=false`, `m09_host_authenticated=false`, `provider_approval_verified=false`, `external_lease_issued=false`, `send_authorized=false`, `graph_dispatch_authorized=false`, `automatic_retry_authorized=false`, `ack_allowed=false`, `production_authorized=false` e `commercial_transition_authorized=false`. `LAB_COMMITTED_RECEIPT_NO_DISPATCH` não é lease nem permissão Graph.

## CI e prova de inversão

[CI funcional de correção `41359259953`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41359259953), SHA de código `c9fd266a754b28c67b2151e87dfbc2ae65f63786`: **2/2 jobs success, zero falhas**:

- **11/11 testes físicos novos de inversão das cinco contraprovas**, incluindo WABA, revisão de chave de principal, cancelamento sem principal e unicidade de quota.
- **27/27 PRE_DISPATCH v0.2 PG17**, **24/24 PRE_DISPATCH v0.1 PG17**, **18/18 M09 point-of-use PG17** intactos.
- **34/34 testes de interoperabilidade S0 → Meta M18 v0.2** usando a evidência PG17 física e **62/62 testes originais M18 da Meta** no SHA pinado `2a535ceb543418a76bb753a368eabc45bdbe4b0f`.
- **176 testes distintos PASS**; no job offline 25 interop são executados e 9 pulados por requerer PG17; esses nove **passaram posteriormente no job físico**. Não somar execuções duplicadas.

Rodadas intermediárias com falha ocorreram no instalador de trigger (delimitador SQL) e nos dados auxiliares de um teste de WABA (colisão de chave, depois incompatibilidade de dono App). O instalador e as fixtures foram ajustados; essas rodadas **não** compõem a evidência de sucesso. A CI funcional de código passou após as correções. **O commit final com esta auditoria requer uma nova CI própria e sucesso integral.**

## Etapa recomendada após esta remediação

**G1 (os cinco achados) corrigido e testado em laboratório**, sem produção. **Antes de prosseguir para a identidade/handoff operacional M18-D**: realizar G2 — contrato de leitura/cancelamento transacional consistente com escritores reais, política de nonce/UNKNOWN, estado e outbox e assinatura de `attempt_ref/intent_ref/selection_ref` por principal autorizado; homologar matriz de contratos/SHAs com Meta; só então propor migrações/infra sob autorização separada. Os cinco casos já não devem ser usados como justificação de lease, envio ou liberação geral de implantação.

**Solicitação à Meta #10:** revisar as correções da porta v0.2 e o impacto do `cancel` com `principal/m09_versions` obrigatórios, mantendo M18-D **bloqueado** até aceite explícito de contrato de handoff e dependências de origem. Nenhum merge, deploy, dados reais, credenciais, Graph, HTTP ACK ou WhatsApp enviados.
