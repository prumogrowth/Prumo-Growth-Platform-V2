# WA-02B — Templates C06 na Graph API | contrato isolado v0.1

**Estado: [P], implementação sintética e não operacional.** A aprovação arquitetural DEC-WA-01/02/03 não equivale a permissão de envio ou campanha. DEC-WA-05 definiu a titularidade de App/WABA/número **por concessionária**, mas não liberou onboarding. DEC-WA-04/06 permanecem pendentes.

## 1. Protocolo Meta consultado em 18/10/2026

Conforme a coleção oficial da Meta, o envio de template usa `POST /{Phone-Number-ID}/messages`, `type=template`, `template.name`, `template.language.code` e `components[]` conforme os parâmetros do modelo. O exemplo oficial `hello_world` não tem componentes; exemplos interativos contêm header/body/button e parâmetros diferentes.

Fontes:
- [Meta — WhatsApp Cloud API (coleção)](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api)
- [Meta — Send Message Template Interactive](https://www.postman.com/meta/whatsapp-business-platform/request/lwtlz1k/send-message-template-interactive)

**Recorte deliberadamente restrito do WA-02B:** apenas parâmetros **posicionais do tipo texto** no `body`, cabeçalho de texto com uma variável opcional e templates estáticos sem variáveis. **Não implementado:** mídia, botões, parâmetros nomeados, currency/date_time, templates com formatos especiais, cadastro/aprovação de templates na Meta ou verificação da categoria e finalidade comercial. Esses formatos devem falhar por registro de catálogo incompatível, nunca ser enviados parcialmente.

## 2. Contratos do módulo

`integrations/whatsapp-meta/graph-template.ts` exporta `prepareGraphTemplateRequest(intent, trustedSnapshot, apiVersion)`.

- `intent` exige contrato candidato `meta-s0.v0.1-proposed`, origem **C06**, IDs de intenção/tentativa/correlação, versão de autorização, `phone_number_id` e `recipient_verified` já resolvidos pelo núcleo, referência de template + revisão, locale, texto do cabeçalho opcional e valores do body em ordem.
- `trustedSnapshot` **deverá** vir do catálogo autorizado e escopado do backend S0. A função exige `status=APPROVED`, mesmo template/idioma/revisão, formato `POSITIONAL_TEXT_ONLY` e quantidades exatamente iguais de parâmetros. A presença dessa estrutura no teste **não** comprova aprovação atual na Meta; o backend terá que consultar/validar vigência antes de cada transmissão.
- O resultado descreve `POST` **relativo e inerte**, com `messaging_product=whatsapp`, `recipient_type=individual`, `to`, `type=template` e componentes somente quando necessários. Não possui `fetch`, token, segredo, URL absoluta, persistência, assinatura, fila ou endpoint; **não realiza envios**.
- O módulo não decide elegibilidade C06, opt-in/opt-out, janela, preço, plano, autoria humana, takeover, retomada, status comercial nem habilita `BLOQUEADA_GATES` da S0. Isso permanece no núcleo. Não converte número BR 8↔9 nem envia para duas variantes.
- O objeto preparado contém destinatário e texto que podem identificar clientes: jamais persistir ou registrar indiscriminadamente em logs/CI. `TemplatePreflightError.code` usa códigos sem repetir dados ou secrets.
- Resposta, callback, `wamid`, aceite incerto e ausência de retry automático continuam tratados somente pelo classificador isolado da WA-02A, a ser acoplado após gate.

## 3. Evidência testada (ambiente local, sem CI remoto)

- Node.js **v22.16.0**: `node --experimental-strip-types --test graph-template.test.ts` → **WA-TPL-01..18: 18/18 PASS**.
- TypeScript **v5.8.3**: `tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck graph-template.ts` → **PASS** no módulo.
- Limite da verificação: nesta sessão o ambiente de TypeScript não dispõe de `@types/node` para typecheck integral do **arquivo de testes**. Ele foi **executado**, mas não verificado pelo `tsc`. Não afirmar CI completo.
- Git blobs da branch publicados e conferidos contra os arquivos efetivamente executados: módulo `c49dc884d960982282927afcf2180dc8f9234b5c` e testes `200371623e67e4ac20d02b1f93984726386d90b2`.

## 4. Próxima etapa técnica independente

**WA-02C:** simular, com porta de transporte **injetável**, a revalidação final C03/C06/C12, envio autorizado e classificação `API_ACCEPTED / PROVIDER_REJECTED / UNCERTAIN_EXTERNAL`, usando somente transporte fake sem rede. Evitar atalho de autorização; revalidar no backend antes de qualquer entrega a um transporte operacional.

**Dependência do núcleo S0 para integração:** autorização atual e versionada para C06 (opt-in/out, template aprovado por loja, janela, caso/handoff, contrato comercial, bloqueios), registro de tentativa e resposta, segredo e destination vinculados ao App da concessionária, e política de envio incerto/reconciliação. Nenhuma credencial ou canal comercial autorizado por documentação.

**Proteções preservadas:** sem migrations, Supabase hospedado, webhook `whatsapp-webhook-sandbox`, número comercial, Meta Graph real, contratação, merge ou deploy. PRs Draft.


## Adendo corretivo pós-auditoria — 18/10/2026

A interface descrita acima foi **endurecida** após auditoria. Substituir, para qualquer implementação futura, a assinatura antiga pela atual:

`prepareGraphTemplateRequest(intent, trustedSnapshot, trustedScope, apiVersion)`

`intent` e `trustedSnapshot` incluem `concessionaria_id`, `canal_id`, `meta_app_ref`, `meta_waba_id`, `phone_number_id`; o quarto parâmetro formal é `apiVersion`, e o terceiro `trustedScope` deve vir do backend S0 autenticado. O módulo verifica correspondência exata desses cinco campos entre três fontes, sem se declarar autorizador do negócio. O catálogo passa a exigir `schema_complete=true` e manifesto `components[]` dos componentes originais, nunca inferidos apenas por contagens. Componentes não suportados ou campos adicionais recusam a construção. Isso **não significa** que haja catálogo Meta real validado nem App comercial habilitado.

A nova evidência de regressão para WA-02A/B é **41/41 PASS local**, incluindo WA-TPL-19..24, e verificação TypeScript estrita dos dois módulos. Ver `wa02-reparos-pos-auditoria-2026-10-18.md` para hashes, limitações e bloqueios remanescentes. Os 18 testes antigos continuam dentro dos 24 WA-TPL. Nenhuma alteração operacional foi autorizada.
