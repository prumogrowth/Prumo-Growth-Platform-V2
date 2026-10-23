# FV-UI-029 — Foco e anúncio após confirmação de ações em diálogos aninhados

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** somente `frontend/`, dados sintéticos. **Não homologado**.

## Problema verificado no Chromium

Ao abrir a visão da equipe no perfil **Gestor fictício Marina**, confirmar uma solicitação de pausa de novos leads ou uma intenção de assunção na fila compartilhada produzia o seguinte resultado:

- O modal filho (`intake-dialog` ou `queue-action-dialog`) fechava corretamente e o modal pai `team-dialog` permanecia aberto.
- O botão que originou a ação era **substituído pelo renderizador** depois da confirmação. O retorno de foco nativo não encontrava mais esse elemento.
- No navegador real, `document.activeElement` era **`BODY`** após a confirmação (reproduzido em 390×844 CSS px). Esse estado prejudica a navegação por teclado e a orientação de tecnologia assistiva.
- O cancelamento por Escape ou por botão já restaurava foco adequadamente; por isso **não foi alterado**.

## Implementação da correção

1. **`frontend/visual/index.html`**: adiciona `#team-action-announcement` dentro do modal de equipe, com `role="status"`, `aria-live="polite"` e `aria-atomic="true"` para anunciar apenas pedidos fictícios.
2. **`frontend/visual/app.mjs`**: função `announceTeamActionAndRestoreFocus` só atua se o modal maior estiver aberto e o perfil continuar elegível. Após a confirmação, atualiza o anúncio e move foco para a aba persistente:
   - `#team-show-members` depois de pausa/retomada;
   - `#team-show-queue` depois de solicitar assunção/atribuição.
   O anúncio é limpo ao reabrir a visão de equipe. Não altera titulares, concessões, distribuição nem estado comercial.
3. **`frontend/visual/tests/dom-fixture.mjs`**: mock adiciona o novo nó de anúncio.
4. **`frontend/visual/tests/app.dom.test.mjs`**: dois testes de confirmação, foco, anúncio e permanência do modal pai.
5. **`frontend/visual/tests/source-contract.test.mjs`**: contrato de origem para guardas, controles de foco, status e cobertura de navegador.
6. **`frontend/visual/tests/browser.smoke.py`**: confirma as jornadas em 390×844 e 1366×768, com `to_be_focused()` nos controles persistentes após as duas confirmações, sem overflow horizontal.

## Resultados executados — cópia derivada do ZIP

A reprodução e correção foram realizadas sobre uma **cópia local derivada** do ZIP fornecido pelo usuário, que já incorporava FV-UI-026 a FV-UI-028. O manifesto dessa cópia foi recalculado segundo os bytes locais. Isso **não equivale a checkout Git autenticado nem a prova da revisão posterior da branch**.

| Verificação | Resultado |
|---|---|
| Python `unittest`, integridade adversarial de ZIP | **20/20 PASS** |
| Node, 26 suítes `*.test.mjs` | **323/323 PASS** |
| Playwright/Chromium no smoke integral | **PASS**, incluindo FV-UI-029 em viewport móvel e desktop |
| `verify_offline_export.py --run-native` no ZIP derivado | **PASS**: 54/54 blobs locais e três gates `zip_security_python`, `node`, `chromium` aprovados |
| Campos `git_checkout_verified` e `full_acceptance` | **false / false**, corretamente |

O resultado de integridade da cópia derivada atesta apenas a correspondência de seu manifesto com seus arquivos. A checagem dos blobs efetivamente publicados na branch é feita separadamente após os commits e o repin final do manifesto oficial.

## Fora do escopo e próximos gates

- Não foram executadas integrações com S0/S1, autenticação, Supabase/RLS, Meta/WhatsApp, OpenAI, dados de clientes ou banco. Sem envio, atribuição ou alteração comercial real.
- Os testes de Chromium são automações com DOM real; **não** substituem leitores de tela humanos, zoom de sistema operacional e auditoria manual de toda a navegação.
- Permanece pendente executar `run_acceptance.py --expected-head <SHA_COMPLETO>` sobre checkout Git **autorizado, na branch exata e com árvore limpa**. Uma exportação ZIP oficial do novo HEAD também deve ser revalidada.
- Sem merge ou deploy; nenhum critério do FV-22 ou nota histórica 19F foi reclassificado por este incremento.

**Referência anterior:** [FV-UI-028](./52_FV_UI_028_ARIA_EXPANDED_FOCO_TECLADO_2026_10_23.md).
