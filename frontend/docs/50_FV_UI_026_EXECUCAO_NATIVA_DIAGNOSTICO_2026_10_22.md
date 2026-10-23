# FV-UI-026 — Primeira execução nativa Python, Node e Chromium do Frontend

**Data da rodada:** 22/10/2026 (Horário de Recife) · **Branch de trabalho:** `feat/frontend-plataforma-visual`
**Escopo:** `frontend/` · **Natureza da evidência:** diagnóstico de ZIP com fontes verificadas; **não equivale a homologação integral nem a checkout Git autenticado**.

## Origem controlada

- O usuário forneceu arquivo ZIP `Prumo-Growth---Platform-83d5f4df1d411d1499a5295e5d642db682ecf861.zip`, exportado do commit `83d5f4df1d411d1499a5295e5d642db682ecf861`.
- O verificador offline encontrou **54/54 blobs com Git SHA-1 e tamanho conformes** ao manifesto interno `source_head=94a3f34d2cea5f0df2fe884c79463f88f83c8e12`, sem arquivos extras na árvore `frontend/visual`.
- Ambiente nativo de diagnóstico: **Python 3.13.5**, **Node v22.16.0**, **Chromium 144.0.7559.96** e Playwright Python instalado. Testes só sobre dados sintéticos da frente visual, sem endpoints de negócio.
- Por desenho, `full_acceptance=false` no relatório de ZIP: inexiste checkout Git com verificação de branch/HEAD/árvore limpa, nem homologação com autorizações reais.

## Execução 1 — ZIP original pinado

| Gate | Resultado | Evidência |
|---|---|---|
| Integridade do ZIP | PASS | 54 arquivos, sem mismatch de blob |
| Segurança Python | **20/20 PASS** | `unittest` nativo |
| Node ESM | **316/317 PASS, 1 FAIL** | Matriz FV-22: `acceptance-matrix.test.mjs` rejeitava o nome legítimo `app.dom.test.mjs` por usar regex sem ponto no segmento base |
| Chromium | **BLOQUEADO** | Gate falhou fechado por causa do teste Node, conforme contrato FV-UI-025 |

## Correções aplicadas na branch

1. **Matriz FV-22:** `tests/acceptance-matrix.test.mjs` altera a regex de nomes `^[a-z0-9-]+\.test\.mjs$` para aceitar segmentos separados por ponto e hífen, sem aceitar barra de diretório ou caminhos relativos. Falha específica observada deixou de ocorrer.
2. **Chromium, fluxo de cancelamento:** na execução manual do navegador sobre cópia temporária corrigida, `browser.smoke.py` revelou condição assíncrona no `close` do diálogo: consulta imediata `document.activeElement.id` acontecia antes de `focusin` do compositor. Inspeção de foco após finalização do evento confirmou `message-input`. O teste passou a usar `expect(...).to_be_focused()`, com espera nativa de Playwright. Não foi necessário mudar regra de atendimento no `app.mjs`.

## Execução 2 — ZIP derivado local de diagnóstico

Para verificar a solução antes do commit, foi criada uma **cópia local do ZIP**, preservando o conteúdo originalmente verificado e substituindo **somente** os dois testes corrigidos e seu manifesto revalidado. O ZIP derivado é uma evidência de diagnóstico, **não é o ZIP oficial originalmente enviado nem um checkout Git**.

| Gate | Resultado |
|---|---|
| Integridade em `verify_offline_export.py` | **PASS, 54/54 blobs** do manifesto da cópia derivada |
| Segurança Python | **20/20 PASS** |
| Node ESM (`node --test`) | **317/317 PASS** |
| Chromium/Playwright em navegador real | **PASS**, com roteiro concluído: 1440×900, 900×780, 390×844 e 320×640, fluxo de equipe, histórico, F03 sintético, estados técnicos, foco e Escape |
| `native_snapshot_pass` | **true** no diagnóstico local derivado |
| `git_checkout_verified` / `full_acceptance` | **false / false** — corretamente |

**Validade da evidência:** o resultado `317/317` se aplica à **cópia local corrigida**, não ao ZIP original (`316/317`). A versão oficial da branch recebeu o mesmo ajuste dos dois testes e o manifesto deve ser repinado **após a última edição em `frontend/visual`**. O novo SHA oficial poderá ser baixado para repetir o diagnóstico.

## Pendências que esta rodada não elimina

- Não foi executado o `run_acceptance.py` em checkout Git autorizado e limpo. Portanto **não declarar homologação FV-UI-013** nem alterar a nota histórica de avaliação `19F=69/100`.
- Chromium smoke nativo não substitui auditoria manual em leitores de tela, contrastes, zoom de 200–400% nem testes e2e com serviços reais.
- S0/S1, GoTrue, grants/RLS, Meta/WhatsApp, OpenAI, F03 persistente, banco, automações, migrações, deploy, merge e produção permanecem **fora do escopo**.

## Próximo passo

Repetir `verify_offline_export.py --archive <ZIP_DA_NOVA_REVISAO> --run-native` sobre exportação fresca da branch; para aceite final, usar `run_acceptance.py --expected-head <SHA_COMPLETO>` em checkout autenticado com árvore limpa e documentação de evidências de navegador/acessibilidade. Manter bloqueio de etapas após falha no gate Python/Node.
