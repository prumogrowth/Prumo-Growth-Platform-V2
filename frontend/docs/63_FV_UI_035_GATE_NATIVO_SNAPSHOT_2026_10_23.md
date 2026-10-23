# FV-UI-035 — Gate nativo do snapshot visual repinado

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Classe de evidência:** testes sobre ZIP local derivado e blobs Git conferidos, **sem checkout autenticado**.

## Amostra e hashes

- Fontes iniciais: snapshot visual fornecido anteriormente e consolidado no FV-UI-034; neste incremento apenas quatro arquivos visuais receberam alterações antes do repin.
- Commit de conteúdo: `f787fa3b1cad838ed6b1a26d75b5645d79a8ef60`.
- Commit com `verify_offline_export.py` repinado: `350e3e5011089f6727ca4dc79477cd0bf1406958`.
- `source_head` dentro do manifesto: `f787fa3b1cad838ed6b1a26d75b5645d79a8ef60`. Esse campo referencia o commit **antes** de repinar o verificador, e não seu próprio commit de atualização.
- Arquivos de `frontend/visual/`: **59**, incluindo **58 blobs pinados** e o próprio verificador. SHA Git do verificador final confrontado com publicação: `478bef2922ec16120fdbf72cd3cbc5c9593ba32a`.
- Os quatro arquivos modificados foram comparados por hash Git com os blobs que o GitHub publicou; o ZIP de teste foi reconstruído a partir dos bytes locais conferidos. **Não é o ZIP oficial do GitHub desse commit e não contém histórico `.git`.**

## Execução nativa real

Comando:

```bash
python -B tests/verify_offline_export.py \
  --archive FV_UI_035_derived_snapshot.zip \
  --run-native --json-report native_report.json
```

| Gate | Resultado observado |
|---|---|
| Hashes Git do ZIP | **58/58 verificados**; verificador tem bytes conferidos |
| Segurança ZIP, Python | **20/20 PASS** · exit code 0 |
| Node nativo, `*.test.mjs` | **341/341 PASS** · exit code 0 |
| Chromium/Playwright real | **PASS** · exit code 0 |
| `snapshot_verified` | `true` |
| `git_checkout_verified` | `false` |
| `full_acceptance` | `false` |

A suíte real de Chromium executou as quatro novas jornadas de **390→900** e **390→1440** CSS px com `thread-back` e `detail-back` inicialmente focados. Foram checados foco em elemento visível, ausência de overflow horizontal, preservação do caso A-102 e ausência de erros JS. As jornadas pré-existentes de 1440, 900, 390 e 320 pixels também permaneceram PASS.

A suíte Python inclui teste adversarial que gera um `UserWarning: Duplicate name` ao inserir deliberadamente entrada duplicada no ZIP. A execução terminou com `OK`, não falha.

## Observações e limites de aceite

O Node nativo foi inicialmente rodado ainda com manifesto do FV-UI-034: **340/341**, com falha de hash/tamanho esperada; o repin foi realizado somente após conferir o código publicado, e a suíte no novo snapshot retornou **341/341**. O último relatório válido é o do gate sequencial após repin.

O diagnóstico confirma integridade e comportamento **dos arquivos presentes no ZIP**, mas não comprova checkout Git limpo, automações S0/S1, APIs externas, estados bancários de produção, autenticação/RLS ou interfaces com serviços reais. Viewport estreita e automação Chromium **não** substituem zoom manual real, teste com tecnologia assistiva, WCAG completa ou aceite FV-22. `run_acceptance.py` com `--expected-head` em checkout Git verificado ainda está pendente. Nenhum merge ou deploy foi realizado.

**Implementação:** [FV-UI-035](./62_FV_UI_035_FOCO_MOBILE_PARA_DESKTOP_2026_10_23.md).
