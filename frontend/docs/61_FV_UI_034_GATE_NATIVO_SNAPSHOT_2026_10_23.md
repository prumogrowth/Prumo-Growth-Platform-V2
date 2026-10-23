# FV-UI-034 — Gate nativo sequencial do snapshot verificado

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Área:** `frontend/` · **Tipo:** diagnóstico de código visual fictício, **não homologação**.

## Procedência e inventário

A amostra utilizada foi um ZIP **derivado localmente** da cópia visual previamente exportada e dos arquivos novos do FV-UI-034; os blobs alterados foram confrontados individualmente com a árvore publicada do repositório GitHub antes do diagnóstico. O pacote não é um ZIP oficial baixado do último commit nem inclui `.git`.

- Commit da implementação antes do repin: `491e0f5e790387af079f4cf40ff3428b07e735b3`.
- Commit após repin do manifesto: `0deae33f8db45eb9faa50f76c63ef2921d2fc8b7`.
- `source_head` registrado no manifesto: `491e0f5e790387af079f4cf40ff3428b07e735b3`. O manifesto preserva o commit de **conteúdo**, não o próprio commit que atualizou o verificador.
- Arquivos em `frontend/visual/`: **59**, sendo **58 blobs pinados** mais o verificador `tests/verify_offline_export.py`, comparado byte a byte ao GitHub (blob `b7b1f50507a081b62ae63130c8ba5d66284d12a0`).
- O ZIP derivado também preservou a nova suite `app.tablet.dom.test.mjs` e a classificação obrigatória da camada `interaction`.

## Resultado do diagnóstico executado

Comando executado sobre o snapshot ZIP:

```bash
python -B tests/verify_offline_export.py \
  --archive FV_UI_034_derived_snapshot.zip \
  --run-native --json-report native_report.json
```

| Gate | Resultado |
|---|---|
| Integridade do snapshot | **58/58 hashes de blobs válidos**; verificador corresponde ao arquivo do ZIP |
| Segurança adversarial ZIP Python | **20/20 PASS** · exit code 0 |
| Node nativo `--test` | **340/340 PASS** · exit code 0 |
| Chromium/Playwright real | **PASS** · exit code 0 |
| `native_snapshot_pass` | **true** |
| `git_checkout_verified` | **false** |
| `full_acceptance` | **false** |

O smoke Chromium executou as jornadas antigas e o novo cenário **FV-UI-034** nos tamanhos **900×780 e 1024×780**, com teclado Enter/Escape, foco devolvido ao botão de abertura, `aria-expanded`, preservação do rascunho de nota, ausência de overflow horizontal e de erros JS.

O ensaio adversarial de Python emitiu `UserWarning: Duplicate name` como parte do teste **intencional** de um ZIP com entrada duplicada, sem falha dos 20 testes.

## Auditoria intermediária e correção dos testes

No primeiro ensaio Node direcionado, uma das quatro novas regressões tablet falhou por **estado visual residual no mock entre cenários**: a etapa anterior deixava `details-hidden` aberto, e o clique seguinte inadvertidamente o fechava. Introduziu-se uma rotina `openDetails()` que só abre se oculto; os quatro testes passaram. A suite completa revelou ainda que o novo arquivo `app.tablet.dom.test.mjs` precisava ser classificado na matriz de camadas FV-UI-030. A classificação `interaction` e seu teste foram atualizados e, na execução completa após repin, **340/340 passaram**. Nenhum resultado negativo intermediário foi rotulado como aprovado.

## Limites

A evidência cobre o protótipo visual e a integridade do conteúdo presente no snapshot; **não** verifica checkout Git autenticado, RLS, Supabase, APIs Meta/OpenAI, S0/S1, integração bancária, operação real ou permissões de produção. Os pixels CSS equivalentes a reflow também **não** equivalem a zoom manual 200/400%, tecnologia assistiva humana, auditoria WCAG completa ou aceite FV-22. Não houve merge, deploy ou alteração fora de `frontend/`.

**Implementação:** [FV-UI-034](./60_FV_UI_034_FOCO_FECHAR_DETALHES_TABLET_2026_10_23.md). **Incremento anterior:** [FV-UI-033](./59_FV_UI_033_GATE_NATIVO_SNAPSHOT_2026_10_23.md).
