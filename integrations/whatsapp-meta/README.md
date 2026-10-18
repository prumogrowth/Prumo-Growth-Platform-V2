# WA-01A — Adaptador Meta inbound isolado (candidato)

**Situação:** engenharia sintética, não implantado; contrato técnico proposto. Não altera a POC
`whatsapp-webhook-sandbox`, as migrations S0, o projeto Supabase hospedado ou canais comerciais.

`inbound.ts` fornece apenas `inspectMetaWebhook(rawBody, signatureHeader, trustedAppSecret, options)`.
Recebe bytes brutos e um segredo selecionado por configuração confiável; aplica limite de tamanho;
verifica a assinatura `X-Hub-Signature-256` via WebCrypto HMAC-SHA256 **antes** de fazer parse;
percorre todos os `entry[]`, `changes[]`, `messages[]` e `statuses[]` e extrai eventos técnicos.

O resultado é `{ok:true, events}` ou `{ok:false, failure:{code, position?}}`. Um erro de
qualquer item invalida o lote inteiro (sem sucesso parcial). `position` contém índices, nunca
conteúdo ou telefone. Os eventos preservam o identificador de participante recebido, mas **não**
resolvem identidade comercial, não associam tenant/loja/canal, não escolhem destino para envio e
não deduplicam status. O `statuses[].id` é ID de mensagem enviada, não ID único de callback.

**Não há endpoint GET/POST, HTTP 200, ACK, conexão à Graph API, banco, outbox, worker, fila,
credenciais reais, tokens em código ou deploy.** Um resultado `ok:true` só significa assinatura
válida e forma conhecida; não significa ingresso durável. O futuro webhook só poderá ACK 200
após aceite durável de **todos** os eventos relevantes pela interface aprovada do núcleo S0.

## Testes locais sem dependências ou serviços externos

Node.js >= 22: `node --experimental-strip-types --test integrations/whatsapp-meta/inbound.test.ts`

Testes sintéticos: assinatura válida/alterada/ausente/app errado, POST agregado, múltiplos `entry`,
callbacks repetidos, lote parcialmente inválido, campo não contratado, payload inválido, limite
por tamanho/eventos e ausência de dados sensíveis nos erros. A execução é local; não habilitamos
GitHub Actions para evitar custo não aprovado.

## Integração pendente da frente principal

- Revisar o envelope e regras de quarentena/rejeição para eventos Meta não contratados.
- Fornecer mapeamento autenticado Meta app/WABA/phone_number_id → canal/loja vigente.
- Homologar API interna de persistência transacional (inbox + trabalho durável), dedupe e ACK.
- Definir limites e retenção via DEC-WA-06 e ambiente definitivo via DEC-WA-04.
- Resolver identidade 8↔9, autorizações e estados comerciais exclusivamente no núcleo.

Referência: `docs/integracoes/whatsapp-meta/interface-compartilhada-s0-meta-v0_1.md`.

## WA-01B/C/D + WA-02A — módulos adicionais sintéticos

- `durable-receipt.ts`: guarda de ACK de lote **não operacional**; não considera a migration 029/030 prova de commit Meta.
- `technical-keys.ts`: pistas de correlação para IDs de mensagem/status, **não autoritativas** para dedupe.
- `verify-get.ts`: decisão isolada de GET `hub.challenge` por token confiável de App, sem endpoint.
- `graph-outbound.ts`: construtor **inerte** de payload de texto C03/C12 da Graph API e classificador de aceite, recusa e incerteza; **sem fetch, token ou envio**. C06 requer construtor específico de template.

Rodar apenas WA-02A: `node --experimental-strip-types --test integrations/whatsapp-meta/graph-outbound.test.ts`.

**IMPORTANTE:** nem strings de intento marcadas `authorized` nem o request preparado concedem permissão comercial real. A frente principal deverá revalidar autorização imediatamente antes de qualquer envio, persistir tentativa, limitar credenciais por concessionária, reconciliar timeout e tratar callbacks. Não logar `request.body` que contém destinatário e conteúdo. Referência: `docs/integracoes/whatsapp-meta/wa02a-graph-outbound-texto-v0_1.md`.

## WA-02B — template WhatsApp C06, offline

`graph-template.ts` prepara somente templates textuais **posicionais** (body e header de texto opcional), com correspondência estrita entre intenção C06 e manifesto confiável de template/idioma/revisão/status, sem mídia/botões/Graph/token/HTTP. Não concede elegibilidade nem envia; `trustedSnapshot` deve ser fornecido e revalidado pelo núcleo. Não registrar em logs o destinatário nem as variáveis de texto.

Testes locais: `node --experimental-strip-types --test integrations/whatsapp-meta/graph-template.test.ts` (**WA-TPL-01..18 PASS**). Compilação TypeScript estrita do módulo **PASS**; o teste foi executado mas não typechecked por ausência local de `@types/node`. Referência: `docs/integracoes/whatsapp-meta/wa02b-graph-templates-c06-v0_1.md`.


## Reparos auditados WA-02A/B — 18/10/2026

Os construtores Graph continuam **inertes** e não concedem direito de envio. Após a auditoria, `graph-outbound.ts` trata 408/425 como `UNCERTAIN_EXTERNAL` sem retry cego e admite IDs `wamid` opacos com padding `=`, rejeitando controles. `graph-template.ts` agora exige contexto autenticado fornecido de fora e catálogo de componentes completo, rejeitando cross-tenant e formatos não suportados.

**Assinatura atual [P]:** `prepareGraphTemplateRequest(intent, trustedSnapshot, trustedScope, apiVersion)` — quatro argumentos. Os três objetos coincidentes não comprovam autorização; `trustedScope` e `trustedSnapshot` devem vir de backend interno confiável, que revalida C06 no instante do envio.

Executados localmente: **41/41 testes PASS** para `graph-outbound.test.ts` + `graph-template.test.ts` e TypeScript estrito PASS dos dois módulos. Os arquivos de teste não passaram typecheck completo por ausência de tipos Node; sem CI remoto. Relatório: `docs/integracoes/whatsapp-meta/wa02-reparos-pos-auditoria-2026-10-18.md`.


## WA-02C — Despacho S0 → Meta inteiramente simulado

`offline-dispatch.ts` conecta **somente em memória** o classificador WA-02A e o construtor de template WA-02B a `FakeS0Outbox` e `ScriptedFakeGraph`. Verifica escopo e versão atuais da fixture antes de reservar uma única tentativa. Revogação, divergência entre concessionárias, destinatário alterado, template suspenso e erro de preparação bloqueiam sem chamada fake; timeout e falha de registro permanecem incertos, sempre `retry_automatically=false`.

Este módulo **não é um serviço backend**, não possui `fetch`, Graph API, HTTP, segredo, banco ou autorização comercial. A ficha `allowed_now` é exclusivamente fictícia, não comprova elegibilidade e não pode ser usada como porta de produção.

**Testes reexecutados localmente:** 23 SIM novos + 17 WA-OUT + 24 WA-TPL = **64/64 PASS**, TypeScript estrito dos três módulos PASS. Sem CI GitHub e sem typecheck completo de `*.test.ts`. Documento: `docs/integracoes/whatsapp-meta/wa02c-simulacao-despacho-s0-meta-v0_1.md`.


## WA-02D — conciliação de callbacks técnicos Meta (somente fixture)

`technical-reconciliation.ts` oferece `FakeMetaStatusReconciler` **somente em memória**. Correlaciona um `wamid` previamente aceito pela Graph API com callbacks `sent/delivered/read/failed` por **App confiável + WABA + Phone Number ID + destinatário exato**; eventos fora de ordem não diminuem progresso técnico, e callbacks repetidos são preservados, sem dedupe automático por `statuses[].id`. Callback antes de envio registrado fica pendente, com limites sintéticos explícitos, sem HTTP 200 ou efeito comercial.

O nome do método `observeAuthenticatedFixture` pressupõe HMAC comprovado e aceite durável **fora** desse módulo; não valida assinatura, não cria inbox nem autoriza C07/Graph. Destino BR 8↔9 não é inferido. O log dos resultados não contém telefones/tokens/texto.

Testes: **24/24 REC PASS** e **88/88 PASS** com regressões WA-02A/B/C locais; TypeScript estrito do módulo PASS. Documentação: `docs/integracoes/whatsapp-meta/wa02d-conciliacao-status-meta-sintetica-v0_1.md`. PR Draft, sem deploy nem chamadas de rede.


## WA-03A — Auditoria integrada e correção de isolamento técnico

Foram acrescentados `cross-contract.test.ts` (14 testes entre HMAC/parser → guarda hipotética de ACK → fake Graph → fake callbacks) e `scope-isolation.test.ts` (3 regressões adversariais). Um defeito do **laboratório** foi corrigido em `technical-reconciliation.ts`: agora consultas a projeções e pedidos `ALREADY_LINKED` precisam manter **concessionária e canal originais**, além de App/WABA/Phone/recipient. Antes da correção, os três testes de isolamento falhavam; depois, **105/105 testes PASS** com as 88 regressões anteriores. TypeScript estrito dos seis módulos PASS, sem CI remoto ou typecheck integral dos testes.

O identificador **interno de ocorrência** de callback deve ser criado/guardado pelo ingresso durável S0, não derivado de `statuses[].id` ou de `status+timestamp`. O `occurrence_ref` dos ensaios é só um exemplo gerado em memória; não prova persistência ou idempotência real. Ver `docs/integracoes/whatsapp-meta/wa03a-auditoria-integrada-e-ocorrencias-v0_1.md`. **Nenhum módulo de laboratório emite ACK real ou envia mensagens.**


## WA-03B — auditoria complementar e reparos em módulos anteriores

Revisados WA-01A/B/C/D e contratos residuais da WA-02C/D. Cinco falhas adversariais reproduzidas e corrigidas: posições `messages[0]`/`statuses[0]` ambíguas (agora `position.array_kind`), buffer HMAC mutável antes do parse (agora snapshot), recibo com `outcome` não textual aceito, projeção sem `intent_id` exato e falsa duplicata com `correlation_id` diferente. Nenhum destes reparos implementa autorização ou persistência operacional.

Testes locais **120/120 PASS**, TypeScript estrito dos oito módulos **PASS**. Somam 105 testes anteriores de integração/saída e 15 adversariais novos, `preaudit-gaps.test.ts` e `wa01-audit.test.ts`. Os quatro arquivos de testes unitários originais WA-01 não foram reexecutados nesta rodada e os testes Node não foram integralmente typechecked; sem CI remoto. Blobs reparados e testes novos conferidos no GitHub.

Relatório: `docs/integracoes/whatsapp-meta/wa03b-auditoria-pendencias-e-reparos-v0_1.md`. Para C07 real: `position.array_kind` por evento, mais `ingestion_batch_ref`/`occurrence_ref` e payload protegido conferidos pelo ingresso S0. Não conectar a uma operação Meta, Graph, webhook ou Supabase hospedado sem gates.
