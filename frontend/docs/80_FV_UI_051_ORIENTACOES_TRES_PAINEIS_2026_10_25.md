# FV-UI-051 — Orientações de escopo consistentes entre os três painéis

**Data:** 25/10/2026 · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual`.

## Diagnóstico confirmado nas fontes GitHub

O FV-UI-050 foi aprovado no [GitHub Actions 40192925946](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40192925946) no SHA `8993979c87aac25cd586e7da53a2de9cd79dd6fe` (356/356 Node, 25/25 Python e Chromium PASS); um commit documental posterior preservou os 59 blobs visuais.

A lista já informava `Dados fictícios. Perfil de teste não autentica nem autoriza.` e a conversa já dizia `Nenhum envio pelo WhatsApp` na nota do compositor. Entretanto, as descrições não estavam vinculadas à busca/composição por `aria-describedby`. O Resumo do painel de detalhes continha alertas técnicos específicos (conclusão humana, banco, D3/D4), mas não apresentava uma mensagem curta e geral, equivalente, de escopo demonstrativo.

## Incremento técnico

- A descrição existente no rodapé da fila ganhou ID `list-demo-guidance` e `role=note`. O campo `#search-input` a referencia via `aria-describedby`. O texto e o significado comercial originais permanecem.
- A advertência junto à composição ganhou ID `composer-demo-guidance`, `role=note` e o prefixo `Dados fictícios.`. `#message-input` referencia a orientação. Mantidos os avisos de prévia, memória local e nenhum envio ao WhatsApp.
- Na aba **Resumo** do painel de detalhes, foi inserida uma nota breve: `Dados fictícios. Este painel apenas exibe informações ilustrativas e não executa operações externas.`, como `role=note` e ID `case-demo-guidance`; `#case-tab-panel` passa a referenciá-la via `aria-describedby` apenas quando a aba Resumo está selecionada. A apresentação usa 12px e fundo/contraste por tema.
- Alertas operacionais detalhados, restrições S0/S1, projeções de janela Meta e dados D3/D4 continuam explícitos e inalterados.

## Contratos e teste integrado

O contrato Node valida os vínculos semânticos e a presença do aviso. O novo roteiro Playwright testa **320×640, 390×844, 900×780, 1440×900 × claro/escuro**: busca associada à advertência da lista; abertura de conversa; mensagem ligada à advertência de não envio; abertura dos detalhes; nota contextual no Resumo e contraste ≥4,5:1; ausência de erros JavaScript ou overflow horizontal. Os testes não enviam mensagens nem ativam processos de negócio.

**Certificação:** somente declarar PASS quando GitHub Actions executar checkout nativo do SHA repinado, Python/Node/Chromium completos e `FULL LOCAL ACCEPTANCE: PASS`.

## Limites

Somente frontend demonstrativo e sintético, sem alteração de projeções de autorização, envio, AI, Meta/WhatsApp, banco, concessões, papéis, Auth, Supabase, integrações, S0/S1, `main`, merge ou deploy. Este trabalho não substitui uma auditoria completa de acessibilidade ou homologação produtiva.

**Anterior:** [FV-UI-050](./79_FV_UI_050_AVISOS_ESTADO_2026_10_25.md).
