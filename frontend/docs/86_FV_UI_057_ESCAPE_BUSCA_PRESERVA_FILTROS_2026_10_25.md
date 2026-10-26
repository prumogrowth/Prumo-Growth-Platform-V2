# FV-UI-057 — Escape contextual para limpar somente a busca

**Data:** 25/10/2026 · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual`.

## Motivação e comportamento

A central sintética já aceita a busca por `Ctrl/⌘ K`, fornece limpeza conjunta dos filtros e reconhece textos com acentos opcionais. No entanto, o comando Escape dentro do campo de busca não tinha uma regra própria estável entre navegadores.

O FV-UI-057 implementa **Escape para limpar somente o texto da busca** quando esse campo tem o foco e a consulta está preenchida. Os demais refinamentos — filtro Não lidas/Atribuídas a mim, etapa comercial, aba Ativas/Histórico —, assim como identidade fictícia, concessionária e conversa, não são redefinidos. O foco permanece no campo.

- Diálogos modais nativos são verificados primeiro: Escape não executa limpeza por trás de modal.
- Não interceptar Escape com Ctrl/Meta/Alt ou fora da busca; preservar Escape de fechamento de detalhes flutuantes e navegação responsiva existente.
- Vincular `aria-keyshortcuts="Control+K Meta+K Escape"` ao campo e uma indicação textual em `#list-demo-guidance`, já referenciada por `aria-describedby`.
- Nenhuma chamada externa, alteração de banco, permissão S0/S1, IA ou WhatsApp; interface fictícia.

## Testes e aceitação

- Node DOM: limpa apenas termo, mantém filtro Não lidas e contexto, ignora Escape sem texto e respeita modal.
- Node contrato de fonte: atalho, orientação acessível, guarda de foco e instrução de limpeza.
- Chromium real: 320×640, 390×844, 900×780, 1440×900 em claro/escuro; Esc no campo após zero resultados, preserva filtro, retorna uma conversa, mantém foco e identidade; sem overflow/erros.
- Gate GitHub Actions: Python adversarial, Node, Chromium e `FULL LOCAL ACCEPTANCE: PASS` no SHA do manifesto repinado. Não constitui teste de leitor de tela humano ou de autenticação real.

**Anterior:** [FV-UI-056](./85_FV_UI_056_BUSCA_PTBR_ACENTOS_ESPACOS_2026_10_25.md).

**Certificação:** pendente até aprovação nativa. `main` não deve ser alterada; sem PR, merge ou deploy.
