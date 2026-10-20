# WA-15A — IDs técnicos Meta vinculados ao cadastro privado da S0

**Data:** 20/10/2026. **PR #1:** Draft na branch `feat/s0-fundacao-prumo`. Somente fixtures PostgreSQL locais, sem merge/deploy, Graph ou banco hospedado.

## Implementação

A nova migration `supabase/migrations/202610200042_s0_wa15_meta_ids_tecnicos_fixture.sql` acrescenta IDs externos técnicos numéricos **às tabelas S0-030/040 existentes**, sem duplicar o cadastro de canais:
- `meta_apps_fixture_s0.app_technical_ref` (App numérico único);
- `meta_canais_fixture_s0.waba_technical_ref` e `phone_technical_ref` (par inseparável, emissor técnico globalmente único);
- bloqueio do vínculo de uma WABA técnica a Apps diferentes, permitindo dois emissores sob a mesma WABA/App;
- bloqueio de mudança de alias App/emissor já usado em vínculo técnico;
- funções privadas `registrar_vinculo_meta_tecnico_fixture_s0` e `consultar_vinculo_meta_tecnico_fixture_s0`, que exigem IDs numéricos técnicos Meta + UUIDs internos de canal e intenção, resolvem identidade do App na S0, e **delegam ao writer e leitor WA-14 já aprovados**.

A loja autorizada e o emissor interno são resolvidos pelo banco, não fornecidos como autoridade pelo solicitante. `current_user='postgres'`, `SECURITY INVOKER`, ACLs revogadas, sem qualquer possibilidade de ACK/Graph/retry/estado comercial. Evidências HTTP 2xx continuam **fictícias**.

## Evidência PostgreSQL 17

[GitHub Actions run 39398947528 — Prumo S0](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39398947528). Commit executado `12a23bac78310257d38fd33a9569b33b69e4330f`; job `s0-db-isolation` = **success**, contêiner `postgres:17` encerrado/removido após testes no banco `prumo_s0_test_ci`.

**WA15-01..16: 16/16 PASS**, marcadores individuais verificados nos logs. O mesmo job reexecutou **WA14-01..18: 18/18 PASS**, além do restante do executor S0, que encerrou com status zero.

Escopos testados: mapeamento App/WABA/phone; consulta exata e ausente sem autorização de retry; replay; tentativas/wamid conflitantes; correspondência loja/canal/intenção; múltiplos emissores legítimos; isolamento de tenants; congelamento de aliases vinculados; consulta após cancelamento sem novo registro; exclusividade do número emissor e proprietário de WABA; privilégios privados; par WABA/phone completo ou nulo.

**Defeito durante a execução:** uma substituição JS interpretou o literal `$'` e duplicou parte do SQL, gerando erro de sintaxe. Migration reconstruída a partir do blob original e substituição corrigida; este run **passou sobre o código corrigido**. Os testes anteriores não foram alterados.

## Limites

Este é um gate PostgreSQL de **persistência e escopo técnico de laboratório**, não uma integração de serviço de produção, validação HMAC da Meta, ACK durável, mensagem enviada, autenticação de principal, contrato comercial ou webhook real. A ponte WA-13 ainda precisa de um componente de execução parametrizada e teste cruzado de ponta a ponta. Nenhum dado real ou serviço externo foi usado.
