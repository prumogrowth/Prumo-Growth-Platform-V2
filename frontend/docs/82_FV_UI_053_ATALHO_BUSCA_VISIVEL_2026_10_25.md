# FV-UI-053 — Atalho de busca descobrível com acesso por teclado

**Data:** 25/10/2026 · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch exclusiva:** `feat/frontend-plataforma-visual`.

## Justificativa

O Ctrl/Cmd+K para navegar à busca já existia em `app.mjs`, mas não possuía indicação visual nem semântica `aria-keyshortcuts`. O fluxo do usuário pelo teclado permanecia pouco descobrível.

## Implementação

- O próprio campo de busca anuncia `aria-keyshortcuts="Control+K Meta+K"`, sem alterar seu nome, `aria-describedby` ou conteúdo fictício.
- Uma dica discreta `Ctrl/⌘ K`, marcada `aria-hidden=true` para não duplicar a descrição falada, aparece no campo em telas acima de 760 px; no celular ela é omitida para preservar espaço e a busca.
- Cores e contornos acompanham os temas claro/escuro, mantendo o foco e o fluxo existente. O atalho já implementado continua levando à lista e concentrando o foco na busca, inclusive a partir da conversa.
- Novo contrato Node de fonte e regressão Playwright em 320×640, 390×844, 900×780, 1440×900, ambos os temas: visibilidade responsiva, Ctrl+K, retorno de foco, integridade da contagem e ausência de overflow/erros.

## S0 e limites de autoridade

A frente visual também assume, por determinação expressa do responsável nesta retomada, a identificação e o desenvolvimento das dependências S0 necessárias à plataforma, conforme os contratos vigentes. **FV-UI-053 não exige alteração S0**: é melhoria de apresentação de um atalho local existente, sem consulta a serviços. Nenhuma mudança em S1, auth, permissões, projeção comercial, dados bancários, IA, Meta/WhatsApp ou persistência.

**Gate obrigatório:** execução GitHub Actions no SHA final repinado; conferir Python, Node, Chromium e `FULL LOCAL ACCEPTANCE: PASS` antes de certificar. Sem PR, merge, mudança de `main` ou deploy.

**Anterior:** [FV-UI-052](./81_FV_UI_052_CONTAGEM_ACESSIVEL_FILA_2026_10_25.md).
