# Prumo Growth / E04 A38 — Contingência Codex e diagnóstico do Actions (28/10/2026)

**Estado:** Investigação de runner e plano de execução **não executado** em Codex.
**F02 branch:** `feat/oai-s0-f03-history-port-20261023`.
**Commit A38 a certificar:** `6950bf377e913d47300e33c72efa039db96ecc1b` (A38 implementado + evidência de bloqueio).
**Último baseline efetivamente certificado:** A37 `24d39a72aaec6218a1563d5d8e75c1db011abe44`, GitHub Actions #40722180768, 1.373/1.373 testes.

## Evidências verificadas: NÃO é reprovação dos testes

Repositório GitHub **privado**, executor definido pela workflow `.github/workflows/s0-f03-pg17.yml`: `ubuntu-latest`. Na run #40770948621, três tentativas acabaram com `conclusion=failure`, **`steps=[]`**, sem runner atribuído (`runner_id=0`, `runner_name=""`) e com tempo faturável da job registrado como **0 milissegundos**. Run #40771347989 reproduziu o mesmo sintoma.

No mesmo repositório, outras branches independentes (por exemplo `feat/meta-s0-ed25519-receipt-interop-20261028`) começaram a falhar antes das etapas por volta de 21h15 UTC / 18h15 BRT, enquanto outras haviam executado com sucesso antes, como #40722180768 e #40731718955. Isso é consistente com restrição de runner/conta/billing, **não demonstra consumo real da franquia**.

O conector GitHub atual não autoriza consultar os endpoints pessoais de cobrança. Confirmar em `https://github.com/settings/billing` → `Usage` (Actions, período outubro/2026), `Budgets and alerts` e banners específicos de pagamento/cota. Não cadastrar pagamento nem aumentar orçamento automaticamente. Uma falha com `steps=[]` não valida, nem invalida, o código A38.

## Executor alternativo independente: Codex Cloud

O Codex Cloud pode executar testes no próprio sandbox quando o ambiente estiver preparado com o repositório privado da conta correta. **Não** substitui a execução automática de PR checks nem a autoridade da S0. O ambiente de teste deve ser isolado e sintético.

### Contrato do trabalho solicitado ao Codex

1. Abrir `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`, branch `feat/oai-s0-f03-history-port-20261023`, conferir SHA `6950bf377e913d47300e33c72efa039db96ecc1b`. Se HEAD mudou, não executar silenciosamente outro código; registrar diferença.
2. **Somente leitura do código para fins de certificação.** Não editar fontes, migrações, S0, Meta, frontend, não publicar, não fazer commit, merge nem deploy. Se um teste falhar, devolver traceback exato e causa antes de sugerir qualquer patch.
3. Configurar Python **3.12**, Node.js (versão estável compatível), `psycopg[binary]>=3.2,<4`, `psql` e PostgreSQL **17** local, descartável. O serviço pode ser nativo ou containerizado **se** o ambiente Codex fornecer o recurso; não presumir suporte ao Docker. Não apontar variáveis de banco para hospedagem, produção ou outro projeto.
4. Garantir checkout separado `.s2-e04-source` apontando ao SHA **exato** `ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c`. Conferir `git -C .s2-e04-source rev-parse HEAD` e o arquivo `.s2-e04-source/docs/integracoes/openai/e04_offline_lab/core.mjs`. A suíte F02 depende **do JS original**, não stub.
5. Executar inicialmente `python3 -m unittest backend.tests.test_f02_s0_recovery_sequence_candidate -v`. Esse teste usa fixtures sintéticas e chama validadores em Python; o checkout da S2 também é necessário para os módulos de jornada.
6. Executar `node --test .s2-e04-source/docs/integracoes/openai/e04_offline_lab/tests/*.test.mjs`.
7. Criar **exclusivamente** a base local descartável `prumo_s0_test_cfi01` no PostgreSQL 17 do próprio sandbox, seguindo a workflow; definir:
   - `PRUMO_TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/prumo_s0_test_cfi01` (somente o servidor descartável),
   - `PGPASSWORD=postgres` apenas para fixture local,
   - `PRUMO_S2_F03_GATE_PATH=$PWD/.s2-e04-source/docs/integracoes/openai/e04_offline_lab/f03-commit-gate.mjs`,
   - `PYTHONDONTWRITEBYTECODE=1`.
   Checar PostgreSQL 17: `psql -X -A -t "$PRUMO_TEST_DATABASE_URL" -c 'show server_version_num'`.
8. Executar **sem alterar** o runner existente: `bash scripts/run-s0-f03-pg17-local.sh`. Esse runner já inicia testes de fechamento S0 assinados, fixture PG17, suites Python F01/F02/F03 e A38; contém limites de host/schema, verificações de SHA S2 e anti-ambient PG*. Não simplificar pulando passos físicos.
9. Capturar comandos, exit codes, versões de Python/Node/Postgres, SHAs dos checkouts, contagem real de testes por suíte, erros, trecho relevante de logs e divergências entre resultado esperado e observado. **Nunca** reportar aprovação sem executar os testes. Manter `F02-A38=LAB_PARTIAL` até evidência suficiente.
10. Encerrar o banco descartável ao final; não manter custos em execução. Não copiar dados reais de leads, Meta, credenciais ou clientes.

**Referência do fluxo original:** `.github/workflows/s0-f03-pg17.yml`. O baseline continha 1.373 testes; A38 acrescenta 39, portanto **1.412 é apenas expectativa aritmética**, nunca um total certificado antes da execução.

## Critérios de aceite para uma homologação alternativa

Resultado apenas `OFFLINE_REPRODUCED` quando houver log de todos os testes com exit code zero, os dois SHAs confirmados, PostgreSQL 17 e Node originais. Registrar que este resultado **não** é a run GitHub Actions com check obrigatório nem G01–G07 homologados. Uma execução somente da A38 não substitui a regressão física PG17, mas já oferece diagnóstico útil.

**NÃO inferir:** cota Actions esgotada apenas de `steps=[]`; origem autenticada de S0 a partir de snapshots sintéticos; possibilidade de reenvio, agendamento ou autorização comercial a partir de `UNAVAILABLE` ou resultado de revisão. Nenhuma modificação de código S0 sem demanda concreta documentada e autorização própria.
