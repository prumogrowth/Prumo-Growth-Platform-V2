# S0-040/AUD1 — auditoria de vínculo Meta, testes e runner local

**Data:** 19/10/2026. **Conclusão:** corrigidos **dois defeitos adicionais de qualidade/segurança** no incremento S0-040; não há evidência suficiente para afirmar que a migration e os cinco testes SQL funcionam em PostgreSQL 17, pois não foram executados. Código limitado ao PR #1 Draft (S0) para subsidiar a frente Meta/PR #2; sem alterar produção.

## Escopo e objetivo

O contrato DEC-WA-05 exige App/WABA/número pertencentes à concessionária, sem canal técnico ambíguo ou vazamento entre lojas. Na migration sintética S0-030, `prumo_private.meta_canais_fixture_s0` já restringia `phone_number_ref` globalmente, porém **não havia unicidade do canal interno**. A S0-040 acrescenta apenas `UNIQUE(concessionaria_id,canal_id)`, mantendo **múltiplos canais distintos da mesma loja e App**. É fixture de teste, não controle de ingressão Meta operacional, credencial, reautorização ou histórico de revogação.

## Achados da auditoria e reparos

| Severidade | Achado | Correção publicada |
|---|---|---|
| Alta — qualidade do gate | WA40-01..03 verificavam só a classe geral `unique_violation` / `foreign_key_violation`. Uma outra constraint poderia causar a falha e o caso ser marcado como PASS sem comprovar **qual** vínculo foi rejeitado. | `supabase/tests/s0_wa_040_meta_binding.sql`: nos handlers, `GET STACKED DIAGNOSTICS ... CONSTRAINT_NAME` exige precisamente `meta_canais_fixture_canal_emissor_unico_s0`, `meta_canais_fixture_s0_phone_number_ref_key` e `meta_canais_fixture_s0_app_ref_concessionaria_id_fkey`, respectivamente. |
| Média — isolamento incompleto no teste | WA40-04 verificava duas ocorrências/canais, mas não afirmava explicitamente que ambas permaneciam **na concessionária A**, apesar de usarem emissor App A. | WA40-04 também rejeita qualquer ocorrência da fixture com `concessionaria_id` diferente da loja A. Não muda regras comerciais. |
| Alta — possibilidade de fuga no runner | `scripts/run-s0-local.sh` validava apenas o **hostname textual** da URI, mas `?hostaddr=<endereço-remoto>` ou um `PGHOSTADDR` herdado poderiam direcionar libpq a outro servidor. Além disso, `startswith('prumo_s0_test_')` permitia caminho com sufixo extra codificado. | Validador agora exige nome completo por `re.fullmatch`, recusa toda query/fragment/params da URI e limpa `PGHOSTADDR/PGSERVICE/PGOPTIONS` e afins antes de chamar `psql`. A URL atual do GitHub CI (`127.0.0.1:5432/prumo_s0_test_ci`) ainda satisfaz a regra. A proteção **não detecta um túnel externo do próprio localhost**, portanto execução deve usar banco genuinamente descartável. |
| Integração — S1 em PR próprio | A frente S1 publicou migrations 038–047 (incluindo `202610180040...` e `202610190045...`) em outro PR Draft. Não existe colisão de **timestamp completo** com a S0 `202610190040...`, mas também não há teste combinado desses PRs. | Documentada dependência de validação cruzada antes de merge. Não alterar arquivos nem migrar código da S1 unilateralmente. |

## Evidência verificável nesta revisão

- **S0-040:** a migration publicada permanece aditiva, com `UNIQUE(concessionaria_id,canal_id)`, sem `GRANT`, API pública, credenciais e sem alterações às migrations históricas.
- **Testes SQL WA40-01..05:** continuam **0/5 executados em PostgreSQL**. Os negativos agora verificam o constraint exato; o teste multicanal verifica loja. Isso melhora o poder de detecção, mas **não é execução SQL** nem garante ausência de bugs em PL/pgSQL.
- **Runner de teste (offline):** 8/8 verificações Python PASS no ambiente local **sobre uma fixture que reproduz o bloco validador embutido no runner**. Casos: URL local do CI permitida; host remoto, `hostaddr` na query, `service` na query, caminho de banco codificado indevido, banco não-descartável e fragmento rejeitados; existência/ordem da limpeza de ambiente. `bash -n` da fixture PASS. O arquivo de testes versionado `scripts/test_s0_040_runner_guard.py` foi comparado byte a byte por hash Git à cópia executada: `7942e7a685ef89c54994f6d2f2814561eceaf9dd`. O runner **completo publicado não foi executado**, pois falta `psql`; não atribuir 8 PASS a banco/CI.
- Blobs Git da revisão: migration `399acdf65f1ccbd9fa141e2b7a9ff23baf23e0c7`, SQL WA40 `e9ac653198002aef1982f8b51bbfc16e9d41ea39`, runner `5c6b50f3eda7d11cab3121ea0c60be9d086fbd2e`; relatório anterior S0-040 é histórico.
- Não há binários `postgres`, `initdb`, `pg_ctl` ou `psql` neste ambiente. O GitHub reportou apenas workflow S1 sintético bem-sucedido no HEAD da branch S0; isso **não comprova** a migração S0-040 nem os cinco testes PostgreSQL. Históricos de CI S0 anteriores pertencem a outros commits.

## Gate para retomada após a auditoria

1. Executar `python3 -m unittest -v scripts/test_s0_040_runner_guard.py` no checkout real para verificar o bloco exato da branch, além dos testes offline já feitos com fixture local.
2. Executar `scripts/run-s0-local.sh` **somente em PG17 descartável e local sem túnel**, coletando o log do SHA testado. Confirmar WA40-01..05 e o restante da regressão S0.
3. Rodar regressão combinada S0/S1, conferir ordenação de migrations 038–047 e S0-040 e verificar Auth/REST local, isolamento e menor privilégio; não assumir que resultado de PR #1 aprova PR #5.
4. Só depois considerar ponte Meta→S0 real: identidade externa ao corpo, vínculo ativo por App/WABA/número/loja, nonce/HMAC, payload protegido, recibo pós-commit e `COMMIT_UNKNOWN`. As fixtures WA-06D/A-B na Meta seguem sem execução PG (`0/20`) e independentes desta correção.

**Resultado:** **GO limitado à continuidade de desenvolvimento isolado e revisão**, **NO-GO para considerar S0-040 homologada, integrar Meta real, HTTP ACK, merge ou produção**. Nenhum segredo, Supabase hospedado, Meta Graph, instituição financeira, POC concessionária de demonstração, custo de CI deliberado ou deploy foi utilizado.
