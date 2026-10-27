# Política de economia GitHub Actions — Prumo (17/10/2026)

**Objetivo:** proteger a franquia mensal do GitHub da organização `prumogrowth` enquanto o repositório é privado e o trabalho ocorre em S0 com dados sintéticos.

## Problema encontrado
O workflow PostgreSQL recebia gatilhos `push` **e** `pull_request` para os mesmos commits da branch, executando a mesma regressão mais de uma vez. O Supabase local (GoTrue/REST/Postgres) também inicializava containers em toda alteração de migrations, custando mais minutos e sendo cancelado/reiniciado por commits sucessivos.

## Controles efetivamente configurados
1. `.github/workflows/s0-postgres.yml`:
   - Somente `push` da branch de desenvolvimento quando o commit realmente modifica `supabase/**`, `scripts/**` ou o próprio workflow, e `workflow_dispatch`. **Removido `pull_request` duplicado e seu filtro de diff acumulado**, que podia disparar testes em commits apenas documentais.
   - `concurrency` por branch e `cancel-in-progress=true`. Substitui teste antigo por novo em um commit mais recente.
   - `timeout-minutes: 5` para terminar jobs travados.
   - O filtro de `push` por paths olha os arquivos do commit, evitando regressão após simples correção de documentação.
2. `.github/workflows/s0-auth-rest.yml`:
   - O workflow de Auth reage **somente ao evento de adicionar a etiqueta `run-auth-integration` ao PR** (evento `labeled`) ou a `workflow_dispatch`, se o fluxo manual estiver disponível. Isso evita até os eventos `skipped` gerados por alterações de código e documentos. Sem opt-in, **nenhum teste Auth é executado**, portanto não há novo aceite de Auth/REST. A etiqueta pode precisar ser criada pelo responsável no repositório antes do primeiro uso.
   - `concurrency` cancela execução antiga substituída; `timeout-minutes: 12`.
   - Para validar uma mudança crítica com Auth/REST, adicionar a etiqueta **após consolidar o commit candidato**, conferir a execução e **retirar a etiqueta**. Para rodar novamente, adicionar a etiqueta outra vez. A automação ainda exige controle humano do gatilho; nunca declarar uma alteração nova aprovada pela API porque um teste anterior passou.
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
