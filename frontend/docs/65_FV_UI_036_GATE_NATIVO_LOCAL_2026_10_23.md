# FV-UI-036 — Validação da base visual com temas

**Data:** 23/10/2026 · **Escopo:** `frontend/` fictício · **Procedência:** ZIP visual derivado de arquivos e hashes conferidos, não checkout Git.

## Execução local

- Segurança adversarial Python do ZIP: **20/20 PASS**.
- Node nativo `--test`: **343/343 PASS**.
- Chromium/Playwright real: **PASS**, com alternância Claro/Escuro em 1440×900, 900×780, 390×844 e 320×640; testes de foco existentes; preferência de sistema escura e diálogo nativo.
- Inventário pinado: **58 arquivos** mais `verify_offline_export.py`; hash de conteúdo e tamanho confrontados com o manifesto atualizado.

**Atenção:** o artefato inicialmente ensaiado possuía `source_head` temporário local. O manifesto versionado no GitHub é repinado depois da publicação do código, com referência ao commit real pré-repin. Não considerar o campo temporário uma revisão publicada. A distinção entre commit de conteúdo e commit do próprio manifesto é obrigatória.

`native_snapshot_pass` refere-se somente ao ZIP e não confirma `git_checkout_verified` ou `full_acceptance`. Nenhuma integração, merge ou deploy foi realizado.
