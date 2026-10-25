# FV-UI-050 — Mensagens de orientação e avisos de estado

**Data:** 25/10/2026 · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual`.

## Base inspecionada

O FV-UI-049 está certificado pelo GitHub Actions [40191190235](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40191190235) com **355/355 Node, 25/25 Python e Chromium PASS** no SHA `a40c715f18600e3f6e4b298d3681492d3aa9d702`; a documentação posterior não alterou os blobs visuais.

A interface já possuía `#toast` com `role=status`, `aria-live=polite` e `aria-atomic=true`, mas o aviso era removido após **3.700 ms**, até mesmo para textos longos. Sua posição fixa inferior podia disputar o espaço da barra operacional/compositor, sobretudo em celulares. Os textos das notificações contêm restrições importantes, como **não envio por WhatsApp** e **nenhuma API chamada**; tais mensagens não devem ser encurtadas, disfarçadas ou omitidas.

## Implementação

- `showToast()` mantém a mesma mensagem original e usa duração adaptativa `min(9000, max(5000, comprimento*70))` milissegundos, sem alteração de eventos, funções ou autorização.
- Aviso é ancorado na parte superior da tela (18px no desktop; `safe-area-inset-top + 72px` em até 760px) para não cobrir o campo e a ação de prévia no rodapé da conversa. Continua transitório, sem clique, com aviso acessível e cronômetro que reinicia quando chega outro aviso.
- Fonte de 13px, entrelinha 1,5, largura máxima móvel, quebra de palavras e contraste branco sobre `#193e48`; o aviso de dados fictícios no rodapé da lista sobe para 11px, com contraste específico no modo escuro.
- A região `role=status` existente é preservada; não ocorre nova captura de foco nem anúncio duplicado. A alteração não implementa validação WCAG integral.

## Testes incorporados

Contrato Node para semântica original, tempo adaptativo e CSS. Roteiro Playwright Chromium em **320×640, 390×844, 900×780, 1440×900 × claro/escuro**, verificando: presença da conversa, semântica ARIA, duração simulada sem espera, posição do aviso acima do compositor sem sobreposição, limites horizontais, tipografia, cores, comportamento não interativo e ausência de erros de página.

**Aceite obrigatório:** somente marcar aprovação após execução real do GitHub Actions sobre o SHA com manifesto repinado e com `FULL LOCAL ACCEPTANCE: PASS`, Python e Node íntegros e navegador realmente executado.

## Escopo e restrições

Alterações unicamente em `frontend/` (mensagem, orientação e testes). Nenhuma mudança em dados sintéticos, lógica comercial, Auth/RLS, Meta/WhatsApp, banco, APIs, Supabase, IA, backend, redistribuição, regras de negócio, acesso, merge em `main` ou deploy.

**Anterior:** [FV-UI-049](./78_FV_UI_049_ESTADOS_VAZIOS_DA_FILA_2026_10_25.md).


## Certificação nativa e correção da regressão

- Implementação, CSS, contratos, roteiro e documentação: commit `8439cc510f4923aa95fa052ecee2d0a903497515`. Manifesto inicial: `8576342f4690edd99b5521b55cdf20e8c51d9bcf`.
- [Primeiro GitHub Actions 40192563219](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40192563219): **failure**, com **356/356 Node PASS** e Chromium bloqueado pelo ensaio FV-UI-050, linha 1115: o teste exigia que `getComputedStyle(toast).bottom` retornasse literalmente `auto`. O navegador retorna um valor resolvido para a posição fixa, mesmo que o CSS defina `bottom:auto`. Não houve evidência de falha das regras funcionais neste ensaio.
- A correção removeu **apenas a dependência da representação computada**. Permanece a validação geométrica real do aviso totalmente acima do compositor (`toast_rect.y + height + 12 < composer_rect.y`), visibilidade, limite da viewport, tempo de exibição, tipografia, cores, semântica ARIA, `pointer-events:none` e ausência de erro JavaScript. Commit: `e94fffe608f5093ba55e69ee7fa93929829c0417`.
- Manifesto repinado após a correção: `8993979c87aac25cd586e7da53a2de9cd79dd6fe`, `source_head=e94fffe608f5093ba55e69ee7fa93929829c0417`.
- [Segundo GitHub Actions 40192925946](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40192925946): **completed / success**, sobre o SHA repinado exato. Os logs atestam **preflight Git 59 arquivos PASS, Python 25/25 PASS, Node 356/356 PASS, Chromium/Playwright integrado PASS**, com marcador `FV-UI-050 avisos acessiveis, tempo de leitura e compositor livre em 8 cenarios: PASS` e `FULL LOCAL ACCEPTANCE: PASS`.
- Um relatório JSON foi publicado no workflow com retenção de um dia. A avaliação ainda está limitada ao frontend demonstrativo, sem homologar operações bancárias, fornecedores, autorização real, integração Meta/WhatsApp ou produção.
