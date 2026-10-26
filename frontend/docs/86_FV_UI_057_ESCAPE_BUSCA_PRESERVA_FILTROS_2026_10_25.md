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

## Certificação GitHub Actions — 25/10/2026

- Commit visual inicial: `155f1ce908f74d7ba9b203c2feccd0ac37c882c6`.
- Primeira execução de teste: [40255654928](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40255654928), **não aprovada**: o ensaio Node supunha um número fixo de conversas não lidas (um) enquanto a fixture real disponibilizava duas. Chromium permaneceu bloqueado pelo gate.
- Correção da suposição do teste, sem modificar o comportamento de busca: `4b6e37687457713ea5ff99d107a0aac431c2929d`, manifesto repinado. Segunda execução [40255859149](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40255859149): Node **369/369 PASS**, mas o Chromium bloqueou o aceite porque uma asserção antiga do FV-UI-053 exigia metadados `Control+K Meta+K` sem `Escape`.
- Atualização de contrato antigo de navegador: `2e669da716741661425d76aefcfadbae71cc5608`, manifesto repinado.
- **SHA efetivamente aprovado:** `8de0a27f37f7050d986b12b691bb03364387ee0b`.
- **[Run 40256225951](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40256225951): completed / success.** Preflight de **59 arquivos PASS**; Python adversarial **25/25 PASS**; Node ESM **369/369 PASS**; Chromium/Playwright **PASS**, inclusive `FV-UI-053 atalho de busca teclado e reflow em 8 cenarios: PASS` e `FV-UI-057 Esc limpa somente busca em 8 cenarios: PASS`.
- Evidência terminal: **`FULL LOCAL ACCEPTANCE: PASS`**.
- Certificação técnica de **protótipo sintético**; não comprova autenticação produtiva S0/S1, WhatsApp, IA, operação bancária, segurança de backend ou testes com leitores de tela humanos.
- Este commit posterior modifica **exclusivamente esta documentação**, preservando o código testado. A branch `main` não é alterada; sem PR, merge ou deploy.
