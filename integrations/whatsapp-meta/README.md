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
