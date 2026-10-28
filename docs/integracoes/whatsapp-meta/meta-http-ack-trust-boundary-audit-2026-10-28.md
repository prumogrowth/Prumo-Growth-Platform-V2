# Auditoria Meta Cloud — fronteira de confiança do ACK HTTP (offline)

**Execução:** 28/10/2026. **Base:** PR #46 (`audit/meta-physical-replay-receipt-20261028`), commit `d2828cd87fd554362085747f9b827d79f3fec764`. **Branch:** `audit/meta-cloud-http-ack-authority-20261028`. **Governança:** S0 e S1 estritamente em leitura. Nenhum HTTP/Graph, credencial produtiva, Supabase, merge ou deploy.

## Resultado da auditoria

**Risco M-ACK-01 previamente reproduzido no PR #46:** `integrations/whatsapp-meta/durable-receipt.ts` oferece o helper histórico `decideBatchAck()`, que pode retornar o objeto sintético `{status:200,action:'ACK'}` com base somente no formato de um recibo alegado `COMMITTED` e nos contadores. O helper documenta que pressupõe uma **porta interna S0 autenticada e durável** não implementada ali; não se trata de endpoint HTTP. Portanto, reuso direto sem provar origem/autorização/commit poderia criar ACK indevido. Não foi demonstrado endpoint vulnerável, nem corrigida S0 por esta frente.

Os candidatos S0 [META-S0-ACK-03 / PR #14](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/14) continuam não ratificados e exigem principal M2M independente, validação de escopo/tenant e revisão, nonce, prova de commit durável do POST físico e política HTTP. Os contratos da S0 não são substituídos por flags do webhook, HMAC da Meta, `raw_sha256`, `lab_ack_ready` ou uma alegação `COMMITTED`. A decisão multicanais S0-A1 dos PRs #44/#45 também segue pendente.

## Implementação exclusiva da frente Meta

`integrations/whatsapp-meta/cloud-http-ack-authority-audit.ts` introduz `auditHttpAckClaimsOffline(input)`: um **inspector puro para auditorias**, não um adaptador HTTP e não um verificador criptográfico de prova M2M. A função:

- aceita apenas um envelope de auditoria com seis campos explícitos e data-only, recusando propriedades extras, accessors e objetos sem estrutura fechada;
- trata `signed_batch` como **alegação de um resultado técnico**, não como prova autônoma de assinatura HMAC. Confere estrutura e flags negativas, sem promovê-las a autoridade;
- compara o candidato e o recibo alegado por `reviewAllegedS0ReceiptWithoutAck()` do PR #46, incluindo revisão/rota explicitamente fornecidas, integridade de canais, posições, hash e contadores;
- diferencia `CLAIMED_RECEIPT_ABSENT`, `CLAIMED_RECEIPT_INCONSISTENT`, `S0_COMMIT_AUTHORITY_NOT_VERIFIED` e `M2M_CLAIM_NOT_VERIFIED`. Nenhuma dessas classificações autoriza ACK;
- sinaliza `MULTICHANNEL_POLICY_NOT_RATIFIED` mesmo quando o recibo multicanais parece estruturalmente completo; não autoriza particionamento ou ACK por canal;
- rejeita qualquer `alleged_http_decision` (incluindo o `200/ACK` do helper legado, `503/RETRY` ou apenas a palavra ACK). A saída não contém campo `status`, `http_status`, `action` ou método de emitir HTTP;
- retorna **sempre** `disposition:'NO_HTTP_ACTION_AUTHORIZED'`, com todas as flags de produção, persistência/commit/M2M, HTTP/ACK, envio, retry e efeito comercial `false`, sem logar qualquer segredo, mensagem ou telefone de cliente.

Um `M2M` com estrutura plausível e até hashes convincentes não comprova a fonte: **a função não possui fonte de confiança para autenticar o principal e o commit S0**. A futura borda HTTP somente poderá decidir sobre a resposta após implementação/ratificação independente da autoridade de ingress, readback de estado durável e regras de transporte. A leitura de candidatos sintéticos não representa a execução desse futuro serviço.

## Proteção estática adicional do CI

O workflow `.github/workflows/meta-cloud-http-ack-trust-audit-offline.yml` executa `integrations/whatsapp-meta/cloud-ack-runtime-guard.mjs`, que percorre arquivos de código versionados `.ts/.tsx/.js/.mjs/.py` e impede **referências executáveis diretas** ao helper `decideBatchAck` fora do módulo legado e de testes. O scanner retira comentários antes da verificação, para não tratar a documentação negativa do harness `transactional-ingress.ts` como um uso operacional. A primeira versão (grep literal) registrou um **falso positivo** nessa referência de comentário e foi substituída sem alterar a S0. Esta política heurística não prova ausência de chamadas indiretas, importação dinâmica, usos via string, integrações não versionadas ou runtime externo; permanece necessária revisão da futura borda HTTP.

## Evidência offline

`integrations/whatsapp-meta/cloud-http-ack-authority-audit.test.ts` contém **30 casos adversariais** sobre:

1. recibo fabricado idêntico ao esperado, resposta ausente, injeção `200/ACK` do helper antigo, `503/RETRY`, strings e status numéricos;
2. prova M2M fabricada, JWT, alegações de papel/diretor e URL de recibo;
3. falso resultado HMAC, flags de produção e ACK promovidas, candidato S0 ausente ou digest discordante;
4. revisão/rota incompatível, propriedades extras/getters, primitivas, arrays, `batch_ref` falso;
5. `ALREADY_ACCEPTED`, quarentena, lote multicanais sem ratificação e repetibilidade de resultados.

**Workflow:** 30 novos testes + 339 regressões focadas herdadas da cadeia PR #46 = **369 testes esperados**; mais verificação estática. Certificação somente se todos passarem e o GitHub Actions registrar **SUCCESS no SHA final exato**.

## Encaminhamentos e limites

| Destino | Achado | Situação |
|---|---|---|
| Meta/Infra — **M-ACK-01** | Proibir ligação direta de `decideBatchAck()` a handler HTTP; exigir verificação de origem e commit | Mitigado por auditoria/CI offline, **não** por endpoint operacional |
| S0 — META-S0-ACK-03 | Ratificar identidade M2M, nonce/replay, commit/recibo durável, política HTTP e tratamento de queda após commit | **Pendente anterior**, nenhuma edição S0 |
| S0/Meta — S0-A1 | Ratificar unidade do POST físico multicanais e atomicidade do lote | **Pendente anterior**, nenhuma edição S0 |
| S0/Meta — CATALOG-05 | Fonte autenticada de catálogo para futuros envios | **Pendente anterior**, fora do ACK |

**Sem novo defeito demonstrado na S0.** Esta entrega não deve ser interpretada como autorização produtiva ou certificação de um endpoint público. Nenhuma migração, política, branch, PR, teste ou código S0/S1 foi alterado. Somente arquivos novos e o CI da frente Meta foram modificados; o histórico do helper `durable-receipt.ts` foi preservado.
