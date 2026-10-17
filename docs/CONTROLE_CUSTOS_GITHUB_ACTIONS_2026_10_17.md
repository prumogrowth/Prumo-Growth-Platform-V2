# Política de economia GitHub Actions — Prumo (17/10/2026)

**Objetivo:** proteger a franquia mensal do GitHub da organização `prumogrowth` enquanto o repositório é privado e o trabalho ocorre em S0 com dados sintéticos.

## Problema encontrado
O workflow PostgreSQL recebia gatilhos `push` **e** `pull_request` para os mesmos commits da branch, executando a mesma regressão mais de uma vez. O Supabase local (GoTrue/REST/Postgres) também inicializava containers em toda alteração de migrations, custando mais minutos e sendo cancelado/reiniciado por commits sucessivos.

## Controles efetivamente configurados
1. `.github/workflows/s0-postgres.yml`:
   - Somente `pull_request` com mudanças em `supabase/**`, `scripts/**` ou o próprio workflow, e `workflow_dispatch`. **Removido `push` duplicado.**
   - `concurrency` por PR/branch e `cancel-in-progress=true`. Substitui teste antigo por novo em um commit mais recente.
   - `timeout-minutes: 5` para terminar jobs travados.
   - Gatilho por paths evita execução devido a simples correção da documentação.
2. `.github/workflows/s0-auth-rest.yml`:
   - Executa job caro **somente com etiqueta `run-auth-integration` presente no PR**, ou com `workflow_dispatch`, se o fluxo manual estiver disponível pelo GitHub. Sem opt-in, o job é `skipped`; esse estado **não significa teste aprovado**.
   - `concurrency` cancela execução antiga substituída; `timeout-minutes: 12`.
   - Para validar uma mudança crítica com Auth/REST, habilitar a etiqueta, executar/verificar o resultado e **retirar a etiqueta**. A automação ainda exige controle humano do gatilho; nunca declarar uma alteração nova aprovada pela API porque um teste anterior passou.
3. Todos os workflows usam `ubuntu-latest`/Postgres descartável local. Nenhum script de teste aceita `DATABASE_URL` remota; sem `supabase link` ou `db push` ao Supabase hospedado.

## Contabilidade e limites
Os **2.000 minutos mensais** são franquia típica do **GitHub Free** para repos privados em runners hospedados, conforme documentação GitHub; minutos são computados ao dono do repositório, e não são 2.000 minutos próprios de cada usuário. A franquia real, o uso mensal e qualquer forma de pagamento **só podem ser conferidos em Billing da organização**, não por inferência dos logs de uma branch.

**Ação recomendada ao responsável:** na organização `prumogrowth`, abrir **Settings → Billing & licensing → Usage / Budgets and alerts** (texto do GitHub pode variar); conferir saldo de Actions; ativar alertas e orçamento aplicável com **Stop usage when budget limit is reached**, se disponível, para evitar excedentes pagos. Um orçamento de US$ 0 para uso adicional pode ser adequado somente após confirmar como o plano trata a franquia; ajuste é exclusivamente humano. Não alteramos cobrança, forma de pagamento ou configuração da conta.

## Políticas para os próximos incrementos
- Consolidar arquivos de uma mesma feature antes de cada rodada e verificar somente o último commit candidato.
- Não fazer mais de uma execução completa de Auth/REST por marco técnico, exceto reparos quando um teste falhar.
- Manter revisões de C07, C09, D3/D4 e MCP fechadas à produção até aprovação humana.
- Estado `skipped` é custo evitado, não prova de RLS.

Referências GitHub:
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/how-tos/monitor-workflows/view-job-execution-time
- https://docs.github.com/pt/billing/how-tos/set-up-budgets
