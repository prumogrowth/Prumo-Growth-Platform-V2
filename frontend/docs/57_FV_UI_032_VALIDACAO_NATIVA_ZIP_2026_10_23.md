# FV-UI-032 — Diagnóstico nativo do ZIP do commit 138bf641

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Tipo de evidência:** snapshot ZIP verificado, **não** checkout Git autenticado.

## Identificação da amostra

- Arquivo: `Prumo-Growth---Platform-138bf641a1cbdf943efaac953b9f8541fed467c5.zip` (fornecido pelo responsável).
- **Commit exato exportado:** `138bf641a1cbdf943efaac953b9f8541fed467c5`.
- **`source_head` do manifesto:** `3faed223617f72f935c18bb4c201d87391beec84`. Este é o commit de conteúdo pinado imediatamente **antes do repin** do arquivo `verify_offline_export.py`; o commit exportado subsequente `138bf641` contém a atualização do próprio manifesto. Não confundir esses SHAs nem afirmar que o verificador autopina seus bytes.
- A amostra foi lida diretamente do ZIP; `verify_offline_export.py` foi recuperado do próprio ZIP para executar sua validação. O executor recusaria diferenças entre o verificador externo e aquele arquivado.

## Execução real dos gates sequenciais

Comando utilizado:

```bash
python -B verify_offline_export.py \
  --archive Prumo-Growth---Platform-138bf641a1cbdf943efaac953b9f8541fed467c5.zip \
  --run-native --json-report native_report.json
```

| Etapa | Resultado obtido |
|---|---|
| Integridade do ZIP | **PASS** · 57/57 blobs conforme hashes Git pinados e mesmo verificador |
| Python (segurança adversarial ZIP) | **20/20 PASS** · exit code 0 |
| Node nativo, 27 arquivos `*.test.mjs` | **334/334 PASS** · exit code 0 |
| Playwright/Chromium real | **PASS** · exit code 0 |
| Gate `native_snapshot_pass` | **true** |
| Campos `git_checkout_verified` / `full_acceptance` | **false / false** |

O smoke Chromium incluiu asserções de FV-UI-032 sobre foco na Extração após retorno técnico, foco após esclarecimento e navegação O5 em desktop e 390px móvel. Também percorreu os tamanhos 1440×900, 900×780, 390×844 e 320×640 e cenários históricos de equipe, janela Meta sintética, responsividade e acessibilidade. **O diagnóstico foi executado**, não apenas especificado.

Na suíte de segurança Python surgiu um `UserWarning: Duplicate name` produzido pelo caso adversarial de arquivo ZIP duplicado; a suíte terminou com `OK` e nenhuma falha.

## Limites e decisões

- Este resultado valida **somente** os arquivos contidos na amostra e a integridade dos **57 blobs de `frontend/visual/`** perante o manifesto pinado. Não comprova por si só checkout Git íntegro, branch local ou histórico Git autenticado. A documentação fora de `frontend/visual/` não faz parte do manifesto.
- **Não** houve acesso real a Supabase/RLS, S0/S1, Meta/WhatsApp, OpenAI, instituição financeira, autenticação, remessa, atribuição, concessão ou comunicação.
- Chromium automatizado não substitui leitor de tela humano, auditoria manual em zoom real ou aceite do responsável pelo design; nenhuma nota 19F/FV-22 foi promovida automaticamente.
- O script de checkout `run_acceptance.py --expected-head <SHA>` segue pendente em checkout Git autenticado e limpo. Não rodá-lo sobre a exportação ZIP como se fosse um checkout aprovado.

**Implementação relacionada:** [FV-UI-032](./56_FV_UI_032_FOCO_EXTRACAO_NAVEGACAO_O5_2026_10_23.md).

**Próxima prioridade:** auditoria de acessibilidade/zoom e definição do redesign, mantendo gates por camadas; novos arquivos em `frontend/visual/` exigirão novo repin e validação do novo snapshot.
