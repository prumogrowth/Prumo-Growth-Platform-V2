# M20 — WDC-13, análise de duas falhas consecutivas (somente laboratório)

**Data:** 01/11/2026. **Frente:** WhatsApp/Meta (diagnóstico exclusivamente offline). **Estado:** M20-A/B/C preparados para auditoria; **M20-D e marco principal [ ]**, sem efeitos na S0, em vendas ou na cadência real.

## Fonte da regra e fronteira de decisão

A seção 4 do [contrato candidato WA-39](WA39_CONTRATO_CANDIDATO_EVIDENCIA_OUTBOUND_F02_S0_v0_1.md), originado pela [Issue #9 — OpenAI→Meta](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9), exige **duas falhas definitivas, correlacionadas em tentativas consecutivas da mesma cadência** antes de S0 avaliar WDC-13. Um `sent` comprovado na tentativa seguinte **zera** a contagem mesmo sem resposta do cliente. `API_ACCEPTED`, timeout, ACK, `UNKNOWN`, `read`/`delivered` isolados ou erro `131049` por si só **não** se tornam prova de envio, de falha definitiva ou de desistência.

**Autoridade:** S0/S1 é a única frente que pode verificar evidência/correlação definitiva, incrementar contador, reiniciar contagem comercial, encerrar/interromper cadência ou gerar projeção para F02. **Meta não aplica WDC-13**; o diagnóstico abaixo **não é endpoint de S0**, não lê um ledger autenticado e não executa transição. A regra C09 é **distinta**: só um `sent` comprovado do *template final* pode subsidiar a janela pós-humano de 24h, com elegibilidade ratificada por S0. Este módulo não calcula nem abre janela C09.

## M20-A — Simulador fail-closed da sequência

`integrations/whatsapp-meta/wa20-wdc13-cadence-preflight-offline.ts` implementa duas funções **puras**, sem I/O:

- `inspectWa20Wdc13Offline(contextClaim, attemptClaims)`
- `recheckWa20Wdc13Offline(previousSnapshot, freshContextClaim, freshAttemptClaims)`

A entrada `wa20-cadence-claim.lab.v0.1` é uma **alegação injetada**, com concessionária, App/WABA/phone, caso, fluxo, plano, cadência, revisões de plano/caso/evidência, estado da cadência e idade da leitura. Quatro campos de verificação de autoridade permanecem **obrigatoriamente falsos**: `s0_source_authenticated`, `attempt_correlation_verified`, `definitive_classification_verified`, `durable_evidence_verified`. Não se aceita um valor `true` inventado por cliente/IA.

Cada item `wa20-attempt-claim.lab.v0.1` tem **o mesmo** escopo (concessionária, App/WABA/phone, caso, fluxo, plano, cadência) e identifica tentativa, intenção, número sequencial, template/versão, `is_final_template`, referência/digest do evento alegado e relógio. **Não** há `wamid`/HMAC autenticado nem chave operacional. Até 40 itens, sequência completa 1..N sem saltos, tentativas e intenções distintas, observações recentes/sem data futura e rejeição de getters, campos extras ou estrutura esparsa. Referência e digest de evidência continuam **sintéticos e não autenticados**; um arquivo que declare duas falhas não prova nenhuma.

Os estados de entrada são `LAB_SENT_CLAIM`, `LAB_DEFINITIVE_FAILURE_CLAIM`, `LAB_UNKNOWN_CLAIM`, `LAB_PENDING_CLAIM` e `LAB_CONFLICT_CLAIM`. Eles representam **cenários hipotéticos de S0**, não uma classificação que a Meta possa afirmar para uso comercial.

- Duas falhas alegadamente definitivas e consecutivas **no final da sequência corrente**, cadência alegadamente ativa, sem trecho desconhecido anterior não resolvido → `LAB_TWO_FAILURES_CANDIDATE_UNVERIFIED`. Um terceiro fracasso alegado mantém apenas esse diagnóstico.
- Um `LAB_SENT_CLAIM` alegadamente correlacionado zera o contador provisório (sem mensagem de cliente) e também limpa a pendência anterior de `UNKNOWN/CONFLICT` **somente dentro da simulação**.
- `UNKNOWN`, `PENDING` e `CONFLICT` geram `LAB_HOLD_UNCERTAIN_OR_CONFLICT` até um `LAB_SENT_CLAIM` posterior; falhas que venham depois de uma incerteza ainda não resolvida não dão passagem.
- Cadência `LAB_PAUSED/LAB_REVOKED` gera `LAB_INACTIVE_HOLD` mesmo se a lista trouxer falhas em sequência. Ausência de tentativa → `LAB_NO_ATTEMPTS_UNVERIFIED`; abaixo do limiar → `LAB_BELOW_TWO_UNVERIFIED`.
- Uma tentativa externa de retry com a **mesma intenção** não vira automaticamente segunda falha; duplicação de `attempt_ref` ou `intent_ref`, gap de ordem ou troca de loja/caso/plano/canal resulta em `DENIED`.

**Nota de segurança:** o reset depois de `LAB_SENT_CLAIM` só descreve o comportamento que a S0 poderá aplicar após autenticação. Ele **não** atesta que uma mensagem foi efetivamente enviada. A política para reclassificação retroativa e efeito WDC-13 já aplicado deve ser ratificada pela S0; o módulo não reescreve histórico.

O resultado contém apenas decisão sintética, contagens e `snapshot_sha256` de contexto/sequência completa ordenada; **não** expõe loja, mensagem, WAMID, telefone ou tentativa no retorno. Esse SHA-256 não é assinatura, token nem prova de correlação. `recheck` exige o snapshot íntegro e a mesma fotografia, mas duas leituras LAB não impedem concorrência/ABA ou revogação após o check. A saída é `wa20-wdc13-snapshot.lab.v0.1`.

**Todas as permissões continuam falsas:** `s0_source_authenticated=false`, `attempt_correlation_verified=false`, `definitive_classification_verified=false`, `sent_verified=false`, `failure_verified=false`, `wdc13_increment_authorized=false`, `wdc13_transition_authorized=false`, `c09_window_authorized=false`, `f02_replan_authorized=false`, `automatic_retry_authorized=false`, `send_authorized=false`, `production_authorized=false`.

## M20-B — Testes adversariais

`integrations/whatsapp-meta/wa20-wdc13-cadence-preflight-offline.test.ts`: **60 cenários M20-01..60**, cobrindo duas falhas alegadas, uma falha isolada, `sent` sem inbound, reset entre falhas, incerteza/pendência/conflito, reabertura só por `sent` hipotético, cadência pausada/revogada, `131049` não autoritativo, erro em `sent`, duplicidade de tentativa/intenção, perda de ordenação, scope/tenant/WABA/phone/caso/plano/fluxo incorretos, alteração de revisões e digest, campo oculto de autoridade, getter, array esparso/capacidade e recheck. Um cenário com template final alegadamente `sent` **não abre C09**.

**CI da branch:** inserir a URL do run validado para o SHA funcional exato após confirmação dos dois jobs. A suíte baseline anterior tinha **1.902 testes Meta offline** e 18 PG17 históricos (laboratório isolado de ingresso, *não* execução WDC-13). A inclusão de 60 cenários prevê **1.962 Meta offline**. Não considerar previsão aprovação.

## M20-C — Contratos exigidos da S0 e encaminhamento

- **#9, WA-39, S0/S1:** estado de tentativa e finalização validado em **fonte autenticada**, `attempt_ref/intent_ref` com idempotência e relação exclusiva a `cadence_ref/plan_ref` versionados, status `sent` e falha definitiva correlacionados ao recibo durável, dedupe por ocorrência, classificação do provedor, ordenação/cursor e replay sem dupla contagem. Resolver o que fazer com falha tardia depois de sucesso e com transição já aplicada — o LAB **não** decide esse conflito.
- **S0/F02:** transação S0 com CAS/estado comercial, regra e audit trail para *duas consecutivas*, reset por `sent`, reentrada/replanejamento autorizado, corte F01 e WDC-13; Meta e OpenAI apenas recebem projeção minimizada ratificada, sem inferir desistência. Ao persistir uma transição, não reescrever histórico por callback atrasado.
- **C09:** contrato separado de `sent` do template final, elegibilidade e janela pós-humano de 24h (não a janela Meta de atendimento); nunca inferir de `API_ACCEPTED` ou `delivered/read`. Implementação/efeitos **somente S0**.
- **#10 / #8:** autorização PRE_DISPATCH operacional e vault/ativos Meta não foram homologados; os laboratórios M18/M19 continuam sem fonte real. A M20 não preenche essas lacunas e não herda autoridade dos seus snapshots.

**Conclusão:** M20-A/B/C **somente LAB offline**; **M20-D e marco principal permanecem [ ]**. Nenhum contador real WDC-13, janela C09, mudança comercial, serviço S0, Graph, HTTP ACK, dado real, merge ou deploy foi realizado.

**Validação funcional após execução:** [CI 41344917062](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41344917062) — commit `457e50faa1b6cdb02d7d4574d58bae364ef0435a`, 60 M20, 1.962/1.962 Meta offline, dois jobs `success`, 18/18 PG17 históricos independentes e scanner ACK aprovado. O registro de previsão acima foi substituído por este resultado.


## Adendo de auditoria corretiva — 01/11/2026

A [auditoria M20](AUDITORIA_M20_WDC13_CADENCIA_2026-11-01.md) reforçou a origem das alegações antes da contagem simulada:

- `event_ref` agora tem unicidade por sequência, além de `attempt_ref` e `intent_ref`; a mesma referência de observação não pode fornecer duas falhas nem reset por `sent`.
- `attempt.observed_at_ms` deve ser anterior ou igual a `context.observed_at_ms`, não apenas anterior ao relógio do pedido.
- `claimed_sent_reset_count` só incrementa quando existe falha provisória ou `UNKNOWN/PENDING/CONFLICT` a resolver, e não para um `sent` isolado.
- O snapshot de **saída** é agora `wa20-wdc13-snapshot.lab.v0.2` com novo domínio de hash e recheck de `v0.1` recusado. Entradas continuam LAB v0.1.

**Evidência funcional:** SHA `d314d7bd1f1c87b366544c1eb6afc88c3080ecb3`, [CI 41351099767](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41351099767): **80/80 M20** e **1.982/1.982 Meta offline**, **18/18 PG17 históricos** de ingresso S0/Meta em job independente, dois jobs `success`, scanner ACK aprovado. O número 60/1.962 acima corresponde à implementação inicial.

**M20-A/B/C auditadas em LAB; M20-D e marco principal [ ]**. Não há S0 autenticada, contador/efeito WDC-13, janela C09, execução Graph ou licença de produção.
