# FV-UI-055 — Ação única para limpar filtros na fila

**Data:** 25/10/2026 · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual`.

## Problema detectado após a FV-UI-054

Quando filtros causavam zero resultados, o controle fixo `#clear-list-filters` coexistia com `.empty-reset` no aviso de lista vazia. Dois botões com mesmo texto e ação confundiam navegação por teclado e tecnologia assistiva. Não havia efeito comercial, mas havia redundância real de interface.

## Correção

- Com **resultados filtrados**, mostrar o botão de limpeza superior, introduzido na FV-UI-054.
- Com **zero resultados e possibilidade de restaurar a lista**, ocultar o botão superior e manter **somente** a ação contextual no aviso vazio.
- Com escopo sem atendimentos ou perfil suspenso, preservar o botão superior para limpar qualquer refinamento, sem sugerir que o reset concede acesso.
- Os dois fluxos reutilizam `resetListRefinements()`, preservando identidade fictícia, concessionária, aba, detalhes e regras existentes. Foco retorna à busca.
- Nenhum ajuste de S0/S1, autenticação, canais, dados reais ou permissões.

## Testes e critérios de aceite

- Node DOM: com resultados, ação superior única; com lista vazia, somente botão contextual, identidade e foco preservados.
- Node contrato: condicional de visibilidade consistente com o estado vazio e com a função compartilhada.
- Chromium/Playwright: 320×640, 390×844, 900×780, 1440×900 nos dois temas, contando botões visíveis pelo papel acessível, limpando filtros em ambos estados, sem overflow ou erros.
- GitHub Actions deve verificar o SHA repinado, testes Python, Node, Chromium e `FULL LOCAL ACCEPTANCE: PASS` antes da certificação. Não é homologação produtiva nem teste humano assistivo.

**Anterior:** [FV-UI-054](./83_FV_UI_054_LIMPEZA_FILTROS_CONTEXTUAL_2026_10_25.md).
