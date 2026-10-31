# M09 — execução direta e evidência de laboratório (31/10/2026)

**Implementado e publicado para revisão técnica, não para aceite operacional.** Sem Codex. Branch: `exp/s0s1-m09-snapshot-lab-20261031`; base: `af3c7a16f777eb0d9b37e96f5ac496f1afc03913`.

Publicado em `integration/s0s1_m09_registry/`: `port.py`, `test_port.py`, `snapshot.schema.json`, `__init__.py`. Workflow dedicado: `.github/workflows/exp-s0s1-m09-registry.yml`.

Blobs auditados contra o pacote local:
- port.py `ff66deca580014cd9fca08e6eae636c9174b774f`
- test_port.py `68d5b56066fd8d56c98c0d785962b70299ac57bf`
- snapshot.schema.json `c6ca9c3854153af960ebf8eeb30e119c34d33c55`
- __init__.py `20d3d1b1daa4a11498ef3f12bd522fb3baec7445`

**Evidências:** 32/32 testes locais PASS, repetidos com Python otimizado; três respostas validadas localmente contra JSON Schema. Workflow GitHub Actions [run 41246374823](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41246374823) no SHA `0118b26092b264a0575594422fad03892948791e`, `success`: escopo do diff, 32 testes normais, 32 repetidos com otimização e sintaxe. Não contabilizar as duas execuções como testes distintos. O commit de atualização documental requer CI própria.

**Limites:** sintético em memória, com verificador M2M e host resolver injetados; sem PG17 físico, fonte S0 canônica, KMS, Graph, tokens, HTTP, migração, deploy, merge, integração hospedada ou permissão de envio/ACK. `source_revision`/digest não é prova de confiança externa. Titularidade/delegação reais reservadas a Infra/Proprietário.

**Próximo:** revisão de consumo pela Meta na Issue #8; S0/S1 integra provider S0 autenticado e testes físicos em etapa separada.
