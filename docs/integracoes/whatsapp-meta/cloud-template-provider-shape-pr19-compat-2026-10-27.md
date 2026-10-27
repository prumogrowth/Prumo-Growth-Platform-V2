# WhatsApp/Meta — observação independente de template por ID

**27/10/2026 — frente Meta / somente laboratório.**
Branch: `feat/meta-template-provider-observation-20261027`. Base: PR #15 (`45618df4fc135c33d59b087a98efd5ef53f30c04`). PR #19 (`aux/meta-s0-template-catalog-05-20261026`), S0/S1 e demais branches **inalterados**.

## 1. Resultado da compatibilidade PR #19 × PR #15

Recuperamos `docs/contratos/meta_s0_template_catalog/CONSUMO_FUTURO_META.md`, o contrato candidato e seu adaptador. O PR #19 **já importa sem mudanças** os preparadores `graph-template.ts` e `graph-template-interactive.ts` do PR #15; projeta TEXT e QUICK_REPLY **a partir do mesmo registro** e conserva o literal `prumo.meta.quickreply.catalog.offline.v1`. Suas 42 provas novas e 120 regressões são evidências daquele PR, **não repetidas nesta etapa**.

**Não se identificou incompatibilidade estrutural que exija alteração do builder.** O bloqueio material é de origem confiável: `readProductionTemplateCatalog()` do contrato candidato devolve **SOURCE_NOT_IMPLEMENTED**. A fixture pode alegar `APPROVED`, mas `meta_approval_verified=false`; hash/TTL/WeakMap locais não autenticam Meta nem uma decisão S0.

As decisões **T1–T6** seguem abertas: identidade/fonte autenticada e recibo; revisões locais persistidas; manifesto normalizado completo; política estática/dinâmica de payload; invalidação e atualidade distribuída; integração com reserva, direitos e segurança S0/S1. Sem ratificação ou ativação por conta própria.

## 2. Lacuna nova e implementação efetiva da frente Meta

A documentação oficial da Meta mantém endpoints de **consulta**, incluindo:

- [Get template by ID](https://www.postman.com/meta/whatsapp-business-platform/request/llkzy9g/get-template-by-id-default-fields), `GET /<TEMPLATE_ID>`.
- [Get all templates](https://www.postman.com/meta/whatsapp-business-platform/request/qtgr0i7/get-all-templates-default-fields), `GET /<WABA-ID>/message_templates`.
- [Get template by name](https://www.postman.com/meta/whatsapp-business-platform/request/7whkjje/get-template-by-name-default-fields), que pode retornar coleção.

A fonte do PR #19 continuará precisando de transporte autenticado. A nossa frente pode adiantar **sem rede** o tratamento de **um registro individual completo**, após futura consulta por ID, incluindo componentes TEXT + QUICK_REPLY. A normalização não deve confiar em registros parciais nem converter um campo `status=APPROVED` em aprovação verificada.

Arquivo: `integrations/whatsapp-meta/graph-template-provider-observation.ts`. Exporta `inspectMetaTemplateProviderRecord(raw, expected)`:

- Exige **ID numérico, nome e idioma exatos**, conferidos contra seleção independente fornecida pelo host confiado. A identidade WABA **não está no registro individual**, portanto é impossível atestá-la por esse componente; o futuro transporte/serviço de catálogo deve vincular a rota/credencial à WABA.
- Aceita apenas um subconjunto deliberado de registros: `id/name/language/status/category/components`, metadados opcionais limitados, componente HEADER TEXT opcional, BODY obrigatório, FOOTER TEXT opcional e BUTTONS com 1–3 QUICK_REPLY. Componentes fora de ordem, duplicados, URL, mídia, carrossel e campos estruturais desconhecidos são recusados; o código não elimina elementos para fingir compatibilidade.
- Copia dados próprios sem getters/protótipos especiais, limita nós/profundidade/tamanho de strings, não aceita arrays esparsos ou propriedades ocultas. Extrai apenas a forma técnica do manifesto e nunca extrai payload S0, autorização, política comercial ou revisão local.
- Retorna `SHAPE_ONLY_UNVERIFIED` **inclusive se o campo observado disser `APPROVED`**; mantém sempre `meta_approval_verified=false`, `provider_source_authenticated=false`, `provider_manifest_complete_verified=false`, `production_authorized=false`, `send_authorized=false`, `ack_allowed=false` etc. O campo `approved_components_candidate` significa apenas **manifesto candidato observado**, não `CatalogBundle` validado pela S0.
- Não percorre paginação, não busca campos adicionais, não realiza `fetch`, não autentica origem, não cria serviço S0, não chama Graph e não prepara envio. A fonte de dados falsa só exercita **parsing de um shape estreito**; campos opcionais e variações futuras da Meta requerem amostras oficiais e ampliação expressa do contrato.

A saída observada contém textos de template, potencialmente sensíveis: uso **exclusivo em memória no laboratório**, não registrar corpo/manifesto em logs de produção.

## 3. Testes e critérios

`graph-template-provider-observation.test.ts`: **18 cenários exclusivos**, incluindo componente Meta texto+botões, status APPROVED/PENDING/PAUSED/REJECTED/DISABLED sem autoridade, vínculo exato de ID/nome/idioma, noções de completude, URL/mídia/carrossel negados, botão quarto ou dinâmico, getters, protótipos, UTF-16 e paginação não suportada. Regressão focada do builder de texto, quick reply e biblioteca WA17B. Não duplicamos WA39–WA68 nem o PR #19.

## 4. Encaminhamento S0

**Nenhuma solicitação nova ao Codex/S0 nesta execução.** Os requisitos reais encontrados são justamente os pendentes **T1–T6** do PR #19. O próximo integrador autorizado deverá:

1. Obter por rota e credencial confiáveis uma resposta Meta atual vinculada a App/WABA/provider ID; tratar HTTP e paginação/fields realmente disponíveis.
2. Reconciliar o manifesto completo, status e recibo técnico, preservando componentes desconhecidos como bloqueio, e registrar revisões locais duráveis.
3. Passar os dados normalizados sob autenticação/ACL S0 e política de payload Prumo, sem reutilizar respostas `SHAPE_ONLY_UNVERIFIED` como aprovadas.
4. Só autorizar envio após os controles de finalidade, janela, consentimento, direitos S1 e contratos de reserva M2M previamente ratificados.

**Critério de compatibilidade:** o output deste observador **não** tem nem deve ter o tipo `CatalogBundle`, `TrustedTemplateSnapshot` ou `TrustedQuickReplyCatalog` operativo. Somente o serviço S0 futuro poderia emitir essas projeções após origem, revisão e política verificadas.

**Governança:** nenhum merge, deploy, endpoint, migração, token, Graph GET real, envio ou aprovação Meta foram realizados.
