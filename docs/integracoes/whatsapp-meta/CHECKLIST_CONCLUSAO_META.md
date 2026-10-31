# Checklist de conclusão — Frente WhatsApp/Meta

**Plataforma:** Prumo Growth Platform V2 (software sem marca própria; LiberaCred é produto da instituição financeira).  
**Atualização inicial:** 31/10/2026. **Proprietário da lista:** coordenação Meta.  
**Branch de trabalho:** `feat/meta-s0-physical-interop-ack-guard-20261031`. **Não representa merge, deploy nem autorização produtiva.**

## Como acompanhar

**Comunicação interfrentes:** adotar [protocolo operacional #4](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/4) e [mapa de dependências Meta](MAPA_INTERFRENTES_ISSUE4_2026-10-31.md). Consultar comentários/status das Issues no início de cada ciclo; entregas/aceites e autorização produtiva são estados diferentes. Não criar solicitações duplicadas nem inferir ratificação por silêncio.

- `[x]`: marco **específico** concluído com evidência; marcos marcados como *offline/lab* NÃO significam operação real.
- `[ ]`: pendente (pode haver código preliminar ou testes parciais).
- Só marcar um item depois de satisfazer seu critério de aceite e anexar commit/teste ou ratificação correspondente.
- Este arquivo é a lista canônica para atualizações, sem porcentagem. Dependências alheias permanecem atribuídas aos seus donos.

## A. Base técnica e testes

- [x] **M01 — Decisões vigentes consolidadas:** WDC-01 a WDC-22, especificação e precedência disponíveis. Evidência: `00-decisoes-vigentes-precedencia-documental-2026-10-21.md` + `01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md`.
- [x] **M02 — Entrada Cloud offline:** HMAC, GET, roteamento App/WABA/phone e leitores de eventos com testes sintéticos. Evidência: `integrations/whatsapp-meta/` + CI 1183; **sem webhook real**.
- [x] **M03 — Saída Cloud offline:** construtores de texto, templates, mídia/interações e observação técnica sintéticos. Evidência: `graph-outbound.ts`, `graph-template.ts`, demais módulos + CI 1183; **sem Graph real**.
- [x] **M04 — Verificação de recibo Ed25519 sintético:** consumidor Meta com chave pública confiada separadamente e regressões negativas. Evidência: `cloud-s0-ed25519-receipt-interop.ts` e 36 testes; **não é recibo do PG17**.
- [x] **M05 — CI offline integral rastreável ao SHA:** 1.183/1.183, zero falhas/skips; checkout/GITHUB_SHA conferidos no job. Evidência: [run 41187216781](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41187216781), SHA `a91b0dac2c332ef5ebbe07fb7884ed5137d60484`.
- [x] **M06 — Interoperabilidade física S0→Meta (laboratório):** PG17 da S0 em checkout imutável gerou recibo assinado após readback, consumido pelo verificador Meta com chave confiada independentemente, 12 testes positivos/negativos e cleanup. Evidência: [run 41188097646](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41188097646), código Meta `b1828b1db7ad653608606916209a1f25ad57e7fe`, S0 `01ffdb093013664b73b18d23f92aac2202578210`. **Somente lab; sem HTTP ACK.**
- [ ] **M07 — Proteção completa contra ACK sintético:** hardening Meta e testes concluídos; **ratificação operacional S0/Meta/Infra pendente**, sem HTTP ACK liberado.
  - [x] M07-A — Função legada `decideBatchAck` agora retorna exclusivamente `DENIED_NO_HTTP_AUTHORITY`, sem status HTTP, mesmo diante de `COMMITTED` forjado.
  - [x] M07-B — Scanner CI detecta referências legadas, ações ACK, sinais positivos de autoridade e código POST com HTTP 200 não ratificado. Diferencia GET challenge e resposta da Graph.
  - [x] M07-C — Testes positivos/negativos e auditoria reforçada: **1.210/1.210** testes offline e PG17 aprovados; evidência: [CI auditado 41194019498](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41194019498), SHA `dd27a01d6a44bd8496d52d9cc2455c8b5752f886`. Scanner com exceção GET delimitada e regressões de comentário/literal.
  - [ ] M07-D — Contrato operacional de ACK/HTTP ratificado por S0/Meta/Infra: autoridade, transação, códigos, replay e falhas. Decisão solicitada na [issue #2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2); minuta em [M07 segurança e aceite](M07_SEGURANCA_RECIBOS_E_HTTP_ACK_2026-10-31.md).
- [ ] **M08 — Escopo de lote multicanais/ACK ratificado:** provas cruzadas Meta↔S0 concluídas em PG17 descartável; **aceite S0/Meta/Infra pendente**, nenhum ACK parcial/HTTP autorizado.
  - [x] M08-A — HMAC Meta + recibo Ed25519 S0/PG17 cobrindo **um POST físico**, 2 WABAs, 1 App, 1 tenant, 4 ocorrências, 1 transação. Evidência: [CI 41189393878](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41189393878).
  - [x] M08-B — Cinco casos negativos provam rejeição **de lote inteiro** sem commit parcial: tenant, App, WABA desconhecida, evento inválido e grant ausente.
  - [x] M08-C — Replay do mesmo nonce negado, recuperação com novo nonce retornando mesmo recibo e conflito de bytes sem novo lote; Meta rejeita HMAC adulterado/revogação/alteração de escopo. Auditoria: **prova e trust fixture separadas**, 18 verificações físicas aprovadas no [CI 41194019498](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41194019498).
  - [ ] M08-D — Homologação dos donos S0/Meta/Infra de unidade transacional, multicanal, estados HTTP, retry e replay. [Issue canônica #2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) (a #3 foi fechada como duplicata, sem aceite); evidências: [M08 laboratório e pendências](M08_LOTE_MULTICANAL_ATOMICO_2026-10-31.md).

## B. Patrimônio Meta e fronteira operacional

- [ ] **M09 — Cadastro e onboarding por concessionária:** reconciliação de inventário **offline** avançou; titularidade/delegação Meta, cadastro S0 confiável e onboarding real ainda **não comprovados**. Dependência canônica: [Issue #8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8).
  - [x] M09-A — Validador M09 de inventário sintético confronta registry, expectativa S0 de `canal_id`/App/loja/rota/revisão e assets Meta de App/WABA/número/catálogo/delegação **sem atribuir autoridade a nenhuma fixture**. [Código](../../../integrations/whatsapp-meta/wa09-asset-onboarding-audit.ts).
  - [x] M09-B — 38 testes negativos/positivos de isolamento, revogação, não duplicação, catálogo/owner de loja, alteração de canal, schema malformado e ausência de privilégios; **1.248/1.248** testes offline e 18 físicas PG17 aprovadas: [CI 41209617874](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41209617874), SHA `1cfe4f4bd76d970de8b6b935244447943c4d08d4`.
  - [x] M09-C — Dependência S0/S1 formalizada na [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8), parecer preliminar recebido e respondido pela Meta; [matriz M09 e limites](M09_AUDITORIA_OFFLINE_ASSETS_ONBOARDING_2026-10-31.md). **Não é aceite do contrato.**
  - [ ] M09-D — Ratificar fonte S0 persistente, autenticação M2M, grants e revogação; comprovar propriedade e delegação Meta reais, inscrição, contas/números/catálogos/templates privados e E2E autorizado; sem interpretação de aprovação por silêncio.
- [ ] **M10 — Credenciais e identidade de serviço:** laboratório de preflight de chaves/escopo concluído; **custódia, autenticação M2M, âncoras S0, HMAC/segredos e rotação/revogação operacionais ainda não homologadas** por S0/Infra.
  - [x] M10-A — Guard offline [`wa10-service-trust-pin-audit.ts`](../../../integrations/whatsapp-meta/wa10-service-trust-pin-audit.ts) combina pin Ed25519 fornecido pelo host + contexto M2M sintético + [verificador de recibo S0 lab existente](../../../integrations/whatsapp-meta/cloud-s0-ed25519-receipt-interop.ts), **sem auto-pinning nem principal autenticado**. Retorno sempre com `ack_allowed:false` e `production_authorized:false`.
  - [x] M10-B — Matriz [39 testes M10](../../../integrations/whatsapp-meta/wa10-service-trust-pin-audit.test.ts) cobre pin alterado/revogado/expirado, janela de dupla chave, falso ID de rotação, cross-App, principal M2M reutilizado, revisão stale, payload alterado, HMAC/cadastro não inferidos, acesso por getter e dados malformados. **1.287/1.287 offline** e **18 verificações físicas PG17** em [CI 41212816731](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41212816731), SHA `9c256e9b6c44f06059b14f4e2b176d17b31bf478` (2 jobs aprovados).
  - [x] M10-C — Fronteira e pendências documentadas em [M10 confiança/rotação offline](M10_TRUST_PINS_M2M_ROTACAO_REVOGACAO_2026-10-31.md), encaminhadas **nas Issues já existentes** [#2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) e [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8), conforme protocolo #4; sem criar demanda duplicada.
  - [ ] M10-D — S0/Infra/Proprietário ratificar identidade M2M autenticada, fonte de chaves independente do recibo, custódia/rotação/revogação produtivas, vault, segregação GET/HMAC/Graph, grants mínimos, revisão transacional e E2E real autorizado; nenhum aceite por silêncio.
- [ ] **M11 — Webhook GET/POST operacional:** pré-validação estrita de envelope implementada e testada **somente offline**; endpoint real, persistência e HTTP GET/POST conforme política S0/Infra ainda **não autorizados**.
  - [x] M11-A — [`wa11-offline-webhook-envelope.ts`](../../../integrations/whatsapp-meta/wa11-offline-webhook-envelope.ts) reutiliza `routed-webhook.ts` e `cloud-batch-scope-preflight.ts` para preservar bytes físicos, exigir rota/revisão confiada, inspecionar headers sem colapsar duplicatas, separar GET de POST e negar framing/assinatura/canal inválidos. **Nenhum código HTTP, status ou ACK é retornado.**
  - [x] M11-B — [44 testes M11](../../../integrations/whatsapp-meta/wa11-offline-webhook-envelope.test.ts) de GET challenge, HMAC, lote multicanal, comprimento/codificação, duplicatas de headers, rotas revogadas e alterações concorrentes. **1.331/1.331** testes offline (zero falhas/skips), scanner ACK e **18 PG17** aprovados: [CI 41214703461](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41214703461), SHA `eeff623f22d4ac12c002bfa2f52a94034246fc92` (2 jobs `success`).
  - [x] M11-C — [Matriz M11 de fronteira e limitações](M11_ENVELOPE_WEBHOOK_GET_POST_PREFLIGHT_OFFLINE_2026-10-31.md) e dependências de ingresso/HTTP já formalizadas na [Issue canônica #2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2), com fonte de registry S0 na [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8); **não abrir solicitações duplicadas**.
  - [ ] M11-D — S0/Infra/Proprietário ratificar endpoint hospedado, GET challenge externo, política de resposta HTTP POST/ACK, autenticação de serviço, vault, persistência durável, tratamento de redelivery/rate limit/erros, retenção e E2E real autorizado, sem presumir aceite por laboratório.
- [ ] **M12 — Ingresso durável integrado:** idempotência, concorrência, readback/recuperação e segregação por canal/tenant comprovados no serviço autorizado, não apenas PG17 lab.
- [ ] **M13 — Catálogo de assets e templates confiável:** fonte vigente com estados/aprovações/versões e sincronização com Meta, S0 e tenant.

## C. Envio e política comercial

- [ ] **M14 — Elegibilidade e opt-out:** consentimento, finalidades múltiplas, grants, supressão por concessionária e revisão no instante do envio com fonte S0 real. Contrato PRE_DISPATCH: [Issue #10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10).
- [ ] **M15 — Contrato F02 de planejamento:** fornecer somente templates ativos/autorizados; F02 não dispara nem inventa template e mantém contexto de campanha verificável. Reusar pedido F02 da OpenAI [Issue #7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7), sem duplicata.
- [ ] **M16 — Preparação segura de templates:** conteúdo, botões, mídia, variáveis congeladas por versão, snapshot auditável e integração de administração com frente MCP autorizada.
- [ ] **M17 — Assinatura de mensagem humana:** `Consultor/Gestor/Diretor Nome:\nMensagem` por autor autenticado na S0, somente texto livre permitido; prova de envio separada da assinatura.
- [ ] **M18 — Despacho Graph API homologado:** operação real somente com autorização específica, política de janela, revalidação, idempotência, rate limit e condição de recuperação.
- [ ] **M19 — Status e evidências reais reconciliados:** wamid/tentativa/tenant, callbacks duplicados e fora de ordem, estados incertos, leitura e entrega sem inferência comercial. Solicitação recebida [OpenAI→Meta #9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9) e [contrato WA-39 v0.1 candidato](WA39_CONTRATO_CANDIDATO_EVIDENCIA_OUTBOUND_F02_S0_v0_1.md) em análise offline; sem integração real.
- [ ] **M20 — Regra WDC-13 integrada à S0:** evidência de `sent` e falha definitiva, reset e duas consecutivas processados pela autoridade S0 sem confundir timeout/ACK com envio. A evidência Meta é coordenada na [#9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9); a aplicação comercial permanece exclusiva S0.
- [ ] **M21 — Handoff humano e integração F01/F03:** impedir retomada F01 após handoff definitivo, preservar cutoff F03 e não conceder transições comerciais à Meta.

## D. Robustez, privacidade e controle

- [ ] **M22 — Logs/auditoria/observabilidade:** rastros sem PII/segredos, métricas por canal, status de saúde e alarmes operacionais.
- [ ] **M23 — Segurança e LGPD:** retenção, minimização, acesso, exclusão, mídias e tratamento de dados financeiros homologados com os donos.
- [ ] **M24 — Falhas externas e escala:** throughput, backpressure, redelivery, quarentena, recuperação pós-restart, timeouts e limites da Meta testados.
- [ ] **M25 — Política externa vigente da Meta:** validar janela de atendimento, templates/categorias, mídia, regras aplicáveis a crédito e consentimento antes de ativação.
- [ ] **M26 — Fluxos administrativos com S1/MCP e frontend:** capacidades e auditoria autorizadas, sem promover IA/MCP a administrador de Diretores.

## E. Homologação e conclusão real

- [ ] **M27 — Contratos interfrentes ratificados:** decisões WA-36/WA-37 atualizadas com aceite expresso S0/S1/Meta/Infra em suas competências e testes cruzados.
- [ ] **M28 — E2E autorizado em homologação:** webhook real, fluxo de cliente de teste, template aprovado, Graph, persistência S0, reconciliação, handoff e casos negativos documentados.
- [ ] **M29 — Segurança operacional final:** revisão de privilégios, casos adversariais, runbooks, rollback, incidentes e evidências de recuperação.
- [ ] **M30 — Liberação de produção:** merge/deploy explicitamente autorizados, ativos e credenciais reais homologados, monitoramento e aceite final dos responsáveis.

## Próximo marco

**AUDITORIA M07/M08:** [parecer técnico e pendências por responsável](AUDITORIA_M07_M08_2026-10-31.md). **M08-D e M07-D continuam pendentes** de ratificação S0/Meta/Infra. As correções de auditoria passaram nos testes offline e físicos; nenhum ACK HTTP foi autorizado. Próximo trabalho Meta: M09 apenas offline.

## Limites permanentes

Nenhum sucesso offline autoriza HTTP 200, Graph real, envio, S0 write, privilégio humano, transição de venda, merge ou produção. S0/S1 não podem ser alteradas unilateralmente. Decisions WDC são preservadas. Os itens pendentes que exigem aceite humano serão destacados quando chegarem à etapa correspondente.
