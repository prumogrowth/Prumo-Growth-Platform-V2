# M11 — Pré-validação do envelope GET/POST de webhook Meta (somente offline)

**Data:** 31/10/2026. **Status:** candidata técnica Meta, não endpoint, não handler hospedado, não autorizada para produção. **Issue interfrentes canônica:** [#2 — ingresso, recibos e ACK](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2), complementada por [#8 — registry S0](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8). A [#4](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/4) proíbe solicitação duplicada.

## Objetivo específico

Após M09 (inventário de ativos) e M10 (pin/identidade sintéticos), M11 prepara uma **borda de normalização e checagem** do pedido GET/POST recebível pelo futuro runtime privilegiado, sem presumir qual endpoint o receberá, como autenticará o serviço ou quando devolverá HTTP.

Esta implementação não faz HTTP, não escuta porta, não consulta Graph/Meta, não persiste em S0 e não emite **nenhum status HTTP** nem ACK, mesmo após GET/POST aceitos em laboratório.

## Componentes já existentes reutilizados, sem reimplementar

- [`verify-get.ts`](../../../integrations/whatsapp-meta/verify-get.ts): desafio GET, comparação de verify token específico da App, proíbe parâmetros duplicados, GET 200 apenas como diagnóstico de desafio em código próprio; distinto de POST.
- [`routed-webhook.ts`](../../../integrations/whatsapp-meta/routed-webhook.ts): seleção por rota/revisão confiadas e segredo em slot por propósito, HMAC POST dos bytes brutos, vínculo de cada ocorrência a App/WABA/número/canal e recheck de revogação; retorna `ack_allowed:false`.
- [`cloud-batch-scope-preflight.ts`](../../../integrations/whatsapp-meta/cloud-batch-scope-preflight.ts): um POST assinado completo, contagem multicanais, SHA-256 do POST físico e negação de lote misto inválido, sem partição/commit/ACK.
- [`cloud-ack-runtime-guard.mjs`](../../../integrations/whatsapp-meta/cloud-ack-runtime-guard.mjs): scanner conservador que evita promoção indevida de HTTP POST 200; não substitui revisão de código compilado/deploy.

## Entrega M11

- [`wa11-offline-webhook-envelope.ts`](../../../integrations/whatsapp-meta/wa11-offline-webhook-envelope.ts): função `inspectWa11OfflineWebhookEnvelope`. Recebe um registro sintético **somente com** `method`, `route`, `raw_query`, `raw_body` e `headers` como **lista de ocorrências**, não Map ou objeto que possa colapsar duplicatas.
- [`wa11-offline-webhook-envelope.test.ts`](../../../integrations/whatsapp-meta/wa11-offline-webhook-envelope.test.ts): **44 testes M11**, positivos/negativos e concorrência de mutação.
- Código testado no commit `eeff623f22d4ac12c002bfa2f52a94034246fc92` da branch `feat/meta-s0-physical-interop-ack-guard-20261031`. [CI 41214703461](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41214703461): 1.331/1.331 Meta offline, 44 novos testes M11, 0 falhas/skips, scanner de ACK aprovado. Confirmar resultado dos dois jobs no GitHub para declarar física cruzada aprovada.

### Regras negativas e invariantes testadas

1. Rejeita método fora de GET/POST, campos extras, origem sem rota confiada/revisão, GET com body, POST com query GET, POST vazio/maior que 256 KiB ou convertido em texto.
2. Os cabeçalhos são inspecionados como **ocorrências individuais**, detectando duplicidade case-insensitive, incluindo `X-Hub-Signature-256` e `Content-Type`; getters/proxies e CRLF não geram parse privilegiado. O perfil de nomes é propositalmente **restrito de laboratório**; a política HTTP hospedada e padrões de proxy ainda devem ser ratificados pela Infra.
3. POST exige assinatura HMAC com prefixo `sha256=` e 64 hexadecimais minúsculos, `Content-Type` JSON UTF-8 restrito, ausência de `Content-Encoding`, `Transfer-Encoding` e `X-HTTP-Method-Override` no envelope recebido. Comprimento declarado, quando presente, deve coincidir exatamente com o buffer físico. **Não declarar que toda requisição Meta real obrigatoriamente usará esses headers ou ordem**: o futuro host normalizará framing de transporte de forma segura e testará os contratos de rede antes de ativar.
4. O buffer POST e a seleção de assinatura/rota/ports são capturados antes de operações assíncronas, evitando troca de bytes e assinatura pelo chamador durante validação.
5. A checagem HMAC usa slot POST, nunca token GET ou Graph. Um POST com múltiplas WABAs **da mesma App** é analisado inteiro; canal de outra App ou canal inválido nega o lote completo sem resposta parcial.
6. GET usa token de desafio por App e devolve apenas **`challenge` no resultado tipado de laboratório**, não um status de rede. O GET não prova cadastro de canal nem autoriza o POST.
7. Resultado positivo POST traz somente `LAB_SIGNED_SINGLE_CHANNEL_UNCOMMITTED` ou `LAB_SIGNED_MULTICHANNEL_UNRATIFIED`, contagens de ocorrências/canais e `raw_sha256`; **sem eventos, conteúdo, telefones, segredo, autorização, commit ou recibo durável**.
8. Todo resultado, inclusive positivo, possui `ack_allowed:false`, `http_ack_allowed:false`, `http_response_authorized:false`, `partial_ack_allowed:false`, `m2m_verified:false`, `service_identity_verified:false`, `persisted:false`, `commit_verified:false`, `durable_receipt_verified:false`, `send_authorized:false` e `production_authorized:false`.

## Interdependências não resolvidas

- [ ] **S0/S1 na #2 e #8:** definição e verificação de principal M2M, porta persistente, cadastro/grants/recheck de rota e canal, atomicidade do POST físico, tratamento de desconhecidos/conflito/replay/recuperação, readback e serviço S0 instalado. O preflight não consome status durável da S0.
- [ ] **Infra/S0/Proprietário na #2:** titularidade e operação do endpoint, interpretação de cabeçalhos por proxy/gateway, política GET e POST HTTP externa, erros temporários/permanentes, redelivery, timeout, rate limit, observabilidade, retenção e regras de ACK. O GET challenge lógico é distinto de POST 200.
- [ ] **Meta/Infra:** verificação com recursos de teste realmente delegados da Meta, HMAC sobre raw bytes em gateway hospedado, limites reais e casos de canal revogado. Sem acesso/permite real não inferir que o laboratório representa integração com fornecedor.
- [ ] **S0/Infra:** integração segura de vault para verify token GET, App Secret POST e credencial Graph, sem confundir segredos e sem registrar tokens no código.
- [ ] **M27/M28/M29/M30:** aceite interfrentes, E2E autorizado, runbooks e implantação explícita. Nenhum fechamento automático da M11.

**Resultado:** preparação offline do envelope e 44 regressões estão concluídas; M11 completa continua `[ ]`. Nenhuma decisão de transporte ou efeito comercial autorizado. Sem merge, deploy ou Graph real.


## Adendo pós-vistoria de segurança — 31/10/2026

Os **44 testes M11** e o CI inicial informados acima são o recorte histórico anterior à auditoria retrospectiva. Foram acrescentadas 4 regressões de revogação de App entre leituras GET/POST, getter em lista de cabeçalhos e tentativas de compartilhar slot GET/POST. A M11 tem **48 testes próprios**, sem alteração da política de não ACK. [CI 41222509935](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41222509935): 1.344/1.344 Meta offline + 18 PG17, fonte funcional `60f789df841485e8cce41525f4517f00c6975e91`. [Auditoria unificada M01–M11](AUDITORIA_RETROSPECTIVA_M01_M11_2026-10-31.md). M11-D continua `[ ]`, pois não existe endpoint ou decisão HTTP/ACK ratificada.
