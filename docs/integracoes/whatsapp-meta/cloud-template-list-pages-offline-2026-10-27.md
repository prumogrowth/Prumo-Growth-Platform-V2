# WhatsApp/Meta — listagem paginada de templates (offline)

**27/10/2026 · Frente Meta · Contrato experimental.** Branch `feat/meta-template-list-pages-offline-20261027`, derivada da branch do [PR #21](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/21). Não modifica os PRs #19 (catálogo candidato), #15 (quick replies), #14 (S0/Meta), núcleo S0/S1, migrations, produção, credenciais ou qualquer serviço real.

## Problema real abordado

O módulo `graph-template-provider-observation.ts`, certificado no PR #21, somente aceita um registro individual de template por ID, sem autenticar sua origem. A documentação Meta prevê listagem `GET /{WABA-ID}/message_templates`, cuja resposta pode ser paginada. A coleção oficial WhatsApp Cloud API documenta a presença de `paging.previous`/`next` para coleções, mas **a URL do fornecedor não deve ser seguida por um parser**. Fontes:
- https://www.postman.com/meta/whatsapp-business-platform/request/qtgr0i7/get-all-templates-default-fields
- https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api

Uma resposta de lista — mesmo contendo um campo textual `status=APPROVED` — não pode ser confundida com catálogo Meta autenticado, manifesto completo, consentimento, aprovação de envio ou garantia de que a paginação foi exaurida.

## Implementação efetiva

`integrations/whatsapp-meta/graph-template-list-page.ts` fornece duas funções puras:

- `inspectMetaTemplateListPage(raw)`: valida forma limitada `{data:[...],paging?}` e extrai **somente** `provider_template_id`, `template_name`, `language_code` e `needs_detail_by_id:true`; evita repassar status, corpo, conteúdo, PII, URL completa e cursor. A presença de `next` só vira booleano informativo, não comando de rede nem continuidade validada.
- `inspectMetaTemplateListPageSet(rawPages)`: junta um conjunto limitado de páginas **já fornecidas** pelo teste; exige que páginas intermediárias declarem `next` e a última declare ausência de `next`, verifica duplicidade de ID e de par nome/idioma entre páginas e **nega todo o conjunto** se há lacunas declaradas ou conflitos. Esse encadeamento **não comprova** que as páginas vieram da mesma WABA, que URLs/cursores eram autênticos, ou que não há páginas omitidas por um emissor não confiável.

Limites locais de laboratório: até 100 candidatos por página, 10 páginas e 500 candidatos no conjunto; budget de estrutura até 4096 nós, profundidade 16 e strings até 8192 caracteres UTF-16. Dados com getters, propriedades simbólicas, arrays esparsos ou protótipos incompatíveis são negados. Identidades são tratadas sem equivalência por normalização: IDs decimais, nome técnico ASCII e idioma `pt_BR`/compatíveis; variantes fora da gramática requerem decisão explícita antes de consumo.

**Todas as saídas**, inclusive sucesso estrutural, têm `meta_approval_verified=false`, `waba_binding_verified=false`, `page_chain_authenticated=false`, `page_set_complete_verified=false`, `send_authorized=false`, `s0_write_authorized=false`, `production_authorized=false`, `ack_allowed=false`, `retry_external=false`, `commercial_effect_authorized=false`.

Uma informação `reported_last_page_without_next:true` descreve **somente o que o JSON fictício declarou**, não a conclusão autenticada do catálogo. Não usar resultado como `CatalogBundle` S0, snapshot aprovado ou sinal para envio. Cada ID descoberto exige consulta individual `GET /<TEMPLATE-ID>` por transporte **futuro, confiável e vinculado à WABA**, seguida dos controles T1–T6 do PR #19. Este trabalho não desenvolve nem autentica esse transporte.

## Reuso e independência

Não altera `graph-template-provider-observation.ts` (PR #21), `graph-template.ts` e `graph-template-interactive.ts` (PRs #8/#15) ou `integration/meta_s0_template_catalog` (PR #19). O novo leitor de lista é uma etapa anterior de **descoberta de candidatos**, não uma implementação de catálogo S0. Não duplica os quatro contratos do PR #14, WA39–WA68 ou a auditoria funcional da outra frente.

`graph-template-list-page.test.ts`: 20 cenários focados, cobrindo paginação declarada, página faltante, repetição conflitante, idioma, ausência de identificação, metadata `APPROVED` ou falsa autorização, URL de paginação maliciosa, cursor privado, getters, tamanho e resposta parcial. Workflow `.github/workflows/meta-template-list-pages-offline.yml` valida o módulo e regressões selecionadas do próprio conjunto de templates, sem realizar chamadas de rede.

## Handoff S0

**Nenhum novo pedido à S0.** Ainda dependemos de T1–T6 já identificados e não ratificados no PR #19: origem administrativa Meta autenticada, vínculo de App/WABA, paginação/consulta de fonte, catálogo com versões persistidas, payload Prumo, invalidação/recheck, ACL e autorização separada de envio. A decisão de como buscar e atestar a sequência de URLs da Meta compete ao backend autorizado/S0/Infra, não ao parser inerte.

**Condição explícita de parada:** sem merge, deploy, Graph GET/POST real, endpoints, tokens, webhook público, ACK operacional, banco hospedado ou evidência falsa de aprovação. Este CI comprova apenas inspeção de objetos fictícios e lógica de falha fechada.
