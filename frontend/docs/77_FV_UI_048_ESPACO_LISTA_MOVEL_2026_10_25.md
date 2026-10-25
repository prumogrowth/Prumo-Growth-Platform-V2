# FV-UI-048 — Melhor distribuição de espaço na fila móvel

**Data:** 25/10/2026 · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch autorizada:** `feat/frontend-plataforma-visual`.

## Base auditada

O FV-UI-047 foi certificado em [GitHub Actions 40188680770](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40188680770) no commit `4c2e56e3d06d92a5337c2f9ac874f62bc55ae6f5`: **353/353 Node, 25/25 Python e Chromium PASS**. A versão final documental `25222d555d4ab6e0cc860a78f2b57dc05403c1f2` preservou idênticos os 59 blobs visuais.

A fila no celular apresenta diversos controles legítimos: título, tema, perfil fictício, concessionária, busca, tipo de lista, filtros rápidos, etapa comercial, três cartões-resumo, cabeçalho de atendimentos, conversas e aviso final. Em alturas baixas (até 700px), uma regra anterior do FV-UI-027 permite a rolagem **do painel completo**, necessária para não esconder atendimentos; a mudança atual não substitui nem desativa esse comportamento.

## Modificação exclusivamente visual

- Até 760px: espaços verticais reduzidos no cabeçalho e entre blocos, sem ocultar nenhum elemento.
- Até 400px: margem interna lateral mais ajustada e chips compactados somente horizontalmente, preservando altura mínima 44px do FV-UI-047.
- Até 760px e altura até 700px: `scroll-padding-block:12px` no painel rolável e `min-height:170px` para a área de conversas, sem colapsar a fila.
- O CSS usa seletores restritos a `.list-pane` e `@media`, com suporte a temas claro/escuro existente. Nenhum elemento novo, nenhum `hidden`, nenhuma modificação em `app.mjs`, estado ou semântica de negócio.

## Novo contrato de regressão

Ensaio Playwright no GitHub Actions em 320×640, 390×844, 900×780 e 1440×900 × claro/escuro, verificando: cabeçalho e resumo preservados, campos e abas acessíveis, 44px nos filtros, redução de espaçamento nas telas móveis, rolagem da lista na tela baixa, primeira conversa e rodapé alcançáveis, ausência de overflow horizontal/erros de página. Contrato Node confere as regras de CSS e marcadores do roteiro. **Somente marcar PASS depois da execução real no SHA publicado.**

## Fronteiras

Apenas frontend demonstrativo com dados fictícios. Não se modificam concessões, permissões, atendimento, mensagens, Meta/WhatsApp, OpenAI, Supabase, S0/S1, pagamentos, autenticação, `main`, produção, merge ou deploy.

**Antecessor:** [FV-UI-047](./76_FV_UI_047_FILTROS_DA_FILA_2026_10_25.md).


## Evidência de aprovação real — GitHub Actions

- Commit de estilo e testes: `aa105bc3360146a4dc501705816b5f046db85df2`.
- Repin do manifesto (58 blobs): `6189fe256df5b7f2842fc3fc5f555823794bb360`, com `source_head=aa105bc3360146a4dc501705816b5f046db85df2`.
- [GitHub Actions run 40189686784](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40189686784), executado no SHA de repin, concluído com status **completed / success**.
- Logs confirmam: **preflight Git de 59 arquivos PASS**, **25/25 testes Python PASS**, **354/354 testes Node PASS, 0 falhas**, e **Chromium/Playwright integral PASS**.
- O browser incluiu `FV-UI-048 lista compacta e conteudo acessivel em oito cenarios: PASS`, além de FV-UI-040 até FV-UI-047, fluxo de atendimento, escopo, teclado e responsividade.
- Resultado do executor: `FULL LOCAL ACCEPTANCE: PASS` no ambiente GitHub-hosted, sobre o checkout oficial do commit indicado. Relatório JSON publicado como artifact com retenção de um dia.
- Comparação com FV-UI-047: **2 commits de implementação/manifesto e 7 arquivos alterados**, todos em `frontend/`, sem alteração de `main`.
- O aceite cobre apenas o protótipo com dados sintéticos e não constitui homologação de produção, API, acessibilidade humana completa ou integração bancária.
