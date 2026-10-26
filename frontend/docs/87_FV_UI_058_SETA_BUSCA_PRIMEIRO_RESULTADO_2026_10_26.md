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

## Reparo de regressão de navegador

A primeira otimização eliminou as oito páginas adicionais, mas o teste reutilizado ainda supunha incorretamente que o painel de conversa começaria com o texto `Selecione uma conversa`. A seleção inicial não faz parte do contrato de seta. O teste foi corrigido para comparar antes/depois de `aria-pressed` e do título, comprovando ausência de seleção/abertura nova. Oito cenários de foco por seta continuam presentes (4 viewports × 2 temas); a ausência de resultados é coberta no Chromium em uma largura e no Node com modificadores, IME e modal, sem expandir o tempo do gate.

## Checkpoint de validação — execução pendente (26/10/2026)

- Commit de implementação original: `167c1261e679c8d8e0fa642579126f04de05a740`.
- [Run 40293552813](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40293552813): inventário e Node **372/372 PASS**; Chromium excedeu timeout nativo de 180 s devido a oito novas sessões de página.
- [Run 40294237964](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40294237964): inventário e Node **372/372 PASS**; Chromium revelou asserção incorreta sobre nome de conversa inicialmente selecionada; regressão corrigida para comparar estado antes/depois sem assumir seleção inicial.
- Código de ensaio corrigido em `68d9cbbb1487da4b1c603eb685b079e7c698b06e`, manifesto repinado e commit de candidato `e2bfc9c297b9163bea7d3f3e60510c08759029e8`.
- [Run 40294929672](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40294929672): **in_progress / sem conclusão na última consulta**; permanecia na instalação de Chromium. **NÃO certificada**. Conferir primeiro o resultado desta execução antes de modificar testes ou retomar FV-UI-059.
- As duas falhas anteriores são dos próprios testes/tempo da suíte, não de um efeito comercial. Isso não equivale à aprovação do Chromium. Nenhum merge, deploy, S0 ou `main`.
