# WA-02A — adaptador de saída Graph API, texto e classificação de resultado

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Estado:** código e testes sintéticos isolados na branch do PR #2; contrato [P] em revisão. **Não é um serviço de envio, não acessa a Meta, Supabase, números reais ou secrets e não autoriza disparos.**

## Base técnica verificada (18/10/2026)

A coleção oficial da Meta descreve `POST /{Phone-Number-ID}/messages` e corpo `messaging_product=whatsapp`. Em caso de aceite, a API retorna `messages[].id` com prefixo `wamid.`; isso **não significa entregue/lido** — a entrega depende dos callbacks assinados posteriores.

- [Coleção oficial Meta — Cloud API](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api)
- [Meta — Send Reply to Text Message](https://www.postman.com/meta/whatsapp-business-platform/request/73yi2uj/send-reply-to-text-message)
- [Referência do projeto — interface S0 ↔ Meta v0.1](interface-compartilhada-s0-meta-v0_1.md)

O Graph API usa autenticação Bearer em transporte real. **Este módulo não recebe nem insere token**; a gestão de credenciais por concessionária e o transporte permanecem para implementação controlada, depois dos gates.

## Entrega implementada

`integrations/whatsapp-meta/graph-outbound.ts` exporta:

- `prepareGraphTextRequest(intent, apiVersion)`: forma **apenas uma descrição inerte de POST relativo**, para texto individual; não há `fetch`, URL absoluta, rede ou header de autorização. Exige contrato `meta-s0.v0.1-proposed`, IDs de intenção/tentativa/correlação, versão de estado positiva, phone number ID e destino `recipient_verified`. **Esses campos não autenticam a autorização:** o futuro backend S0 deve revalidar canal, destinatário, opt-out, atribuição, sessão e handoff imediatamente antes do transporte.
- Aceita `C03` (IA) e `C12` (humano) como origem documental de texto, mas **não aceita C06** neste construtor: C06 é contrato de templates, a implementar separadamente e com regras próprias. Não transforma números BR 8↔9 nem tenta destinatários alternativos.
- `classifyGraphSendResult(attempt_id, correlation_id, observation)`: trata respostas HTTP e erros de transporte que venham de um transporte futuro autorizado. Um `2xx` **com `wamid` inequívoco** resulta `API_ACCEPTED`; sem id reconhecível = `UNCERTAIN_EXTERNAL`. HTTP `4xx` definitivo, exceto `429`, resulta `PROVIDER_REJECTED`. Timeout/erro de rede, `429` e `5xx` resultam `UNCERTAIN_EXTERNAL`. Todos os estados têm `retry_automatically=false`.
- Metadados retornados incluem somente `attempt_id`, `correlation_id`, `http_status`, ID externo se confiável e `meta_error_code`/`meta_error_subcode` quando numéricos. Não se propagam `error.message`, `error_data`, `fbtrace_id`, números ou tokens. O objeto da requisição **contém texto e destinatário**, portanto jamais deve entrar em log/telemetria.

O valor `v24.0` e demais versões usados em fixtures **não configuram a versão operacional** — são exemplos. A versão liberada deve ser escolhida e validada com o fornecedor no rollout.

## Testes realmente executados

Ambiente **local** Node.js `v22.16.0` e TypeScript `5.8.3`:

- `node --experimental-strip-types --test graph-outbound.test.ts` → **14/14 PASS**.
- `tsc --noEmit --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck --esModuleInterop --types node graph-outbound.ts graph-outbound.test.ts` → **PASS**.
- SHA Git dos arquivos conferidos contra GitHub: módulo `b414612ed9bff1df3b30920f82ef05c212da4311`, testes `05d67778d8375cace2b8b37ad055236ce4a2474d`.

Os testes cobrem payload, escopo C03/C12/C06, dados inválidos, recusa de variantes automáticas, aceite `wamid`, resposta ambígua, timeout, erro 4xx/401, 429/5xx e supressão de detalhes de erros. **Não há teste HTTP Meta real nem prova de autorização comercial, retry, reconciliação ou webhook callback.**

## Próximos incrementos independentes e dependências

**WA-02B (próximo candidato):** formar templates C06 com idiomas/componentes permitidos, ainda sem envio real. **WA-02C (posterior):** porta de transporte injetável com fake HTTP, revalidação de backend mockada e classificação `UNCERTAIN_EXTERNAL`, sem URL operacional nem token.

A frente principal deverá fornecer a autorização comercial revalidável de C03/C06/C12, identidade de canal e destino Meta verificado, mecanismo de reserva de tentativa, resultado persistido e política de reconciliação/retry. DEC-WA-04 e DEC-WA-06 pendentes; DEC-WA-05 aprova a titularidade por concessionária, **não** operação comercial.

**Proteções:** PR #1 e PR #2 Draft; sem merge, migrations remotas, `whatsapp-webhook-sandbox`, Meta comercial, segredo, número real, deploy ou custo adicional.
