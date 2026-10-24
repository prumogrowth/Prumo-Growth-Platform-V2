# FV-UI-039 — Alvos de toque do tema claro/escuro

**Data:** 24/10/2026 · **Repositório oficial:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** apenas `frontend/`.

## Achado reproduzido

O seletor Claro/Escuro introduzido no FV-UI-036 tinha botões com altura computada de aproximadamente **26px**, medida no Chromium no snapshot de base em 320, 390, 900 e 1440px. Isso restringia a área de toque de uma preferência usada por vários perfis. O cenário foi reproduzido em HTML/CSS local; não altera uma regra de negócio.

## Correção visual

- `.theme-option` recebe `min-height:44px; min-width:44px` e padding apropriado.
- Até 400px o cabeçalho `.list-topline` permite quebra, e `.list-header-actions` organiza o seletor com os outros controles sem impor rolagem lateral.
- Continuam apenas **duas opções**, com `aria-pressed` e tema existente. A responsividade é visual e não muda atores, concessionárias, conversas, mensagens ou permissão.

## Testes

Foi executado Chromium real com a mudança aplicada a uma cópia local da UI, em **320, 390, 900 e 1440px**. Os dois botões permaneceram visíveis, responderam ao clique, mantiveram `aria-pressed=true` após seleção, apresentaram ao menos **44×44 CSS px** e não causaram overflow horizontal. O smoke completo local retornou **PASS**.

A suíte Node local com novo teste de contrato retornou **343/344** antes do repin: o único teste não aprovado confrontava tamanho/hash de `styles.css` com o manifesto anterior. A regressão comportamental e os demais testes passaram. A aferição final dos hashes é realizada sobre os arquivos publicados no GitHub após atualização do manifesto. Não apresentar 343/344 como gate completo.

## Limitações e segurança

O snapshot local deriva de um export anterior à branch oficial atual, portanto os ensaios Chromium são **evidência local de comportamento**, não checkout autenticado nem aceite integral do HEAD remoto. A verificação de hashes remotos é separada da execução dos testes. Medições de pixels CSS e alvos de 44px não substituem teste com dedo/dispositivo, zoom real, leitor de tela ou auditoria WCAG completa. Nenhum backend, S0/S1, autenticação, WhatsApp/Meta, OpenAI, Supabase, dados bancários, merge ou deploy foi acionado.

**Anterior:** [FV-UI-038](./67_FV_UI_038_CONTRASTE_MODAL_GERENCIAL_DARK_2026_10_24.md).

## Auditoria remota final após repin

- Commit de implementação, testes e documentação: `780ec1bcc110df349c92c03f4e790e9635dc5f1e`.
- Commit do manifesto de integridade: `c6bc2a9af263cfa760f385675f1490377e4339a1`.
- Compare com FV-UI-038: **2 commits e 7 arquivos alterados**, **zero fora de `frontend/`**.
- Manifesto oficial repinado com `source_head=780ec1bcc110df349c92c03f4e790e9635dc5f1e`: **58/58 hashes Git e tamanhos idênticos aos blobs da árvore remota**, nenhuma divergência. SHA Git do próprio verificador: `85359a7fe5a10f3345dc9c4e5257ca8fc29858bc`.
- Controles e regressões verificados no HEAD remoto: CSS dos alvos de 44px, quebra de cabeçalho até 400px, smoke Chromium nas quatro larguras e contrato estático.
- Branch `main` permaneceu em `dace737ab7afb7ae3f5a3a6f5cb522e6def8b43a`, sem merge ou deploy.
- **Limite:** o Chromium local passou, mas usou snapshot derivado do FV-UI-036 com a alteração visual. A suíte Node local teve **343/344**, falhando somente no manifesto pré-repin desse snapshot local. O repin remoto foi verificado por hashes, **não** por execução nativa de checkout autenticado do novo HEAD; não afirmar aceite integral.
