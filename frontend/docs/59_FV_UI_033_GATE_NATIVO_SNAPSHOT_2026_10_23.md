# FV-UI-033 — Gate nativo sobre snapshot visual derivado

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Tipo:** integridade Git blob + testes nativos sobre ZIP local derivado.

## Identificação e procedência

O responsável entregou a exportação GitHub do commit `138bf641a1cbdf943efaac953b9f8541fed467c5` na etapa anterior. Para este diagnóstico, a cópia visual local foi modificada exclusivamente com o código/testes do FV-UI-033, tendo as versões de `frontend/visual/` conferidas pelos blobs publicados via conector GitHub.

O commit técnico que antecede o repin é **`6eb2df3433e88375317e682cdbdc279b6f4f5c38`**. Seu SHA foi registrado como `source_head` no manifesto. O commit do repin é **`ebd7f60e34ca9a786d156985a08ec813c92ba4b9`**. O próprio `verify_offline_export.py` é o único arquivo visual excluído da pinagem para evitar autocircularidade e foi comparado byte a byte com o ZIP.

Este ZIP derivado **não é** download oficial do GitHub do último commit e **não possui** pasta `.git` ou prova de checkout limpo. As fontes visuais foram verificadas pelos **57 hashes Git** esperados; a diferença entre a procedência dos arquivos não deve ser confundida com aceite de checkout.

## Gates sequenciais executados

Comando sobre o ZIP derivado:

```bash
python -B tests/verify_offline_export.py \
  --archive fv_ui_033_derived_snapshot.zip \
  --run-native --json-report native_report.json
```

| Etapa | Evidência real |
|---|---|
| Manifesto de fontes | **57/57 blobs Git correspondentes** e verificador idêntico |
| Python, segurança adversarial ZIP | **20/20 PASS**, código de saída 0 |
| Node `--test` nativo | **335/335 PASS**, código de saída 0 |
| Chromium/Playwright | **PASS**, código de saída 0 |
| Agregador `native_snapshot_pass` | **true** |
| `git_checkout_verified` | **false** |
| `full_acceptance` | **false** |

O novo smoke verificou **1440→360→1440**, **320→1440**, preservação de foco em Lista/Conversa ao reduzir para **320 px**, teclado Home/End, `aria-expanded`, ausência de overflow global e não perda da aba de Detalhes. O restante dos cenários Chromium do protótipo também terminou com PASS.

## Falha intermediária e correção

Um primeiro gate sequencial sobre snapshot já pinado passou integridade/Python/Node, mas **falhou no Chromium** por ler `data-mobile-view` antes da conclusão do evento `resize`. A asserção foi substituída por `expect(...).to_have_attribute`, que aguarda a mudança observável. Uma execução isolada posterior identificou uma segunda falha real no retorno do foco do móvel ao desktop; corrigimos o foco com restauração para o elemento de Detalhes ainda conectado. O **segundo gate completo** passou em todas as etapas.

## Limitações e próximo gate

A validação só compreende Frontend demonstrativo local; não inclui URL do produto, autenticação, Supabase, serviços S0/S1, janela Meta real, remessa instituição financeira ou estado comercial de produção. Reflow em viewport estreita **não é** zoom manual 200/400%, leitor de tela real ou aferição WCAG de ponta a ponta. O runner `run_acceptance.py` com `--expected-head` em checkout Git íntegro e limpo continua **pendente**.

**Implementação:** [FV-UI-033](./58_FV_UI_033_REFLOW_FOCO_BREAKPOINT_2026_10_23.md). **Referência anterior:** [FV-UI-032](./57_FV_UI_032_VALIDACAO_NATIVA_ZIP_2026_10_23.md).
