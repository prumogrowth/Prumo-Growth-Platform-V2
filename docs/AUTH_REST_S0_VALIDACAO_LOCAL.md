# Prumo S0 — Integração local Supabase Auth + Data API

Data-base: 17/10/2026. Teste de GoTrue (identidades reais **da instância local efêmera**), JWT e PostgREST contra migrações candidatas S0, com dados 100% sintéticos.

## Como executar sem afetar o projeto hospedado

- `supabase/config.toml` tem `project_id` **somente local** e `db.major_version=17`.
- Workflow `.github/workflows/s0-auth-rest.yml` usa Supabase CLI v2.84.2 fixada no GitHub Actions e sobe GoTrue/PostgREST/Postgres isolados via Docker. Não executa `supabase link`, `supabase db push` nem usa `SUPABASE_ACCESS_TOKEN` do projeto hospedado.
- Script `scripts/test_s0_auth_rest_local.py` lê apenas as URLs/chaves criadas por `supabase status --output env` e verifica se DB e API apontam para localhost. Não imprime tokens/senhas; não usa PII.
- Usuários de teste são criados via `/auth/v1/signup` e autenticados por `/auth/v1/token`. Fixture de concessões/atribuições é inserida por SQL no PostgreSQL descartável; as consultas e escritas sob teste usam somente os JWTs desses usuários pela `/rest/v1`.

## Evidência real já verificada

[GitHub Actions — Auth/REST local #39067714447](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39067714447): **PASS AUTH-01 até AUTH-06**, logs inspecionados.

| Prova | Status | Verificação |
|---|---|---|
| AUTH-01 | PASS | Gestor A/B visualiza apenas sua loja apesar do mesmo telefone de cliente |
| AUTH-02 | PASS | Operador designado só lê caso A; ator sem vínculo não obtém dados |
| AUTH-03 | PASS | Leitura anônima de registros comerciais negada |
| AUTH-04 | PASS | Operador designado grava resposta sintética; outros atores e escrita direta em leads negados |
| AUTH-05 | PASS | Remanejamento retira leitura e escrita do operador com JWT antigo ainda válido |
| AUTH-06 | PASS | Revogação do vínculo de gestor suprime leitura com JWT antigo ainda válido |
| AUTH-07 | AVALIDAR na execução ampliada | Pendência C02 visível só ao gestor A, não a B/OP/sem vínculo |

## Delimitação do aceite

O teste **não** é feito contra o projeto Supabase hospedado. Não cobre sessão revogada no GoTrue, MFA, configurações corporativas, verificações por campo D3/D4, Storage, carga grande ou provedores externos. Revogação por vínculo/atribuição na base foi testada com JWT válido, o que é diferente de revogar o JWT inteiro. Ainda precisamos definir política de sessões e autenticação de responsáveis.

O teste local permite cadastro de usuários fictícios porque `auth.email.enable_confirmations=false` está definido **somente na configuração efêmera de testes**; isso não autoriza alterar configurações de produção nem provisionar usuários comerciais.

**Gate:** GO apenas para continuidade de engenharia local e sintética; NO-GO para migrações comerciais no Supabase hospedado, merge automático, operação real ou integração Meta/Banco. Revalidar todos os testes em ambiente de homologação exclusivo antes de ativar usuários reais.
