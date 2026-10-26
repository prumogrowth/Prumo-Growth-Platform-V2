# FV-UI-058 — Foco no primeiro resultado pela seta para baixo

**Data:** 26/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`.

## Necessidade e mudança

Os atalhos anteriores permitem localizar a busca (Ctrl/⌘ K), pesquisar sem exigir acentos exatos e limpar a consulta (Esc). Era necessário percorrer outros controles para chegar à primeira conversa filtrada. Agora, pressionar **↓ na busca** foca o primeiro cartão realmente disponível em `#conversation-items`.

- **Somente foco**: não selecionar, marcar lido, abrir, encaminhar ou alterar o caso.
- Respeitar filtros, aba, perfil e concessionária fictícios; nenhum acesso a registros além dos projetados.
- Na ausência de cartões, com modal aberto, durante composição IME ou com Ctrl/Meta/Alt, manter foco e ação padrão.
- O atalho da busca passa a `Control+K Meta+K Escape ArrowDown`; orientação em português vinculada via `aria-describedby`.
- O fluxo nativo de Tab/Enter dos botões permanece preservado, incluindo dispositivos móveis.

## Responsabilidades e integração com S0

Codex é o responsável principal pela S0. **FV-UI-058 não modifica nem depende do núcleo oficial**: nenhum contrato S0, banco, API, autenticação, WhatsApp ou autorização é alterado. Arquivos afetados: `frontend/visual/app.mjs`, `frontend/visual/index.html`, testes DOM/contrato/Chromium, manifesto e este documento. Se surgir dependência futura, desenvolver proposta isolada, informar contratos e aguardar coordenação do Codex antes da integração. Desenvolvimentos/PRs existentes preservados.

## Aceite

- Node DOM: foco restrito ao primeiro resultado; nada aberto ou marcado; filtro mantido; zero resultados/modificadores/IME/modal.
- Node de contrato: texto de orientação, metadados de atalho, condicionais de segurança da interação.
- Playwright real: 320×640, 390×844, 900×780, 1440×900 em claro/escuro, verificando foco, seleção, lista vazia, overflow e erros JS.
- GitHub Actions: preflight, Python, Node e Chromium, `FULL LOCAL ACCEPTANCE: PASS` no manifesto repinado.
- Sem alteração de `main`, merge, PR ou deploy. A certificação da interface fictícia não constitui teste de segurança, integração ou leitor de tela humano.

**Anterior:** [FV-UI-057](./86_FV_UI_057_ESCAPE_BUSCA_PRESERVA_FILTROS_2026_10_25.md).

**Status:** implementação candidata, certificação pendente.

## Otimização do teste após primeira execução

Na execução inicial, o preflight e Node **372/372** passaram, mas o script Chromium excedeu o limite de execução de 180 s ao abrir oito páginas adicionais. O roteiro FV-UI-058 foi incorporado às mesmas oito páginas já abertas pela FV-UI-057, sem remover cobertura de viewport/tema nem alterar o timeout ou o código de negócio. Novo aceite completo obrigatório.
