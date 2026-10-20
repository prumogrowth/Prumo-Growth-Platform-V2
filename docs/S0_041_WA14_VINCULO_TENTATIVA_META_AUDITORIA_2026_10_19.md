# S0-041 / WA-14 — Vínculo técnico Meta tentativa ↔ wamid (PostgreSQL sintético)

**Data:** 19/10/2026. **Branch:** `feat/s0-fundacao-prumo`, PR #1 **Draft**. Foco na continuação da frente WhatsApp/Meta após WA-13, mantendo S0 como autoridade. Nenhum merge, produção, Meta Graph, clientes, credenciais, banco hospedado ou instituição financeira foi usado.

## Necessidade concreta

WA-11/12/13 possuem um único `FakeAttemptBindingLedger` em memória, com duas direções de unicidade, recuperação exata e bloqueio de reenvios em caso de commit desconhecido. A S0 possui `outbox_intencoes_s0` e `meta_apps_fixture_s0` / `meta_canais_fixture_s0` (S0-030/040), mas ainda não tinha uma associação persistida para esses vínculos. Não recriar as entidades existentes.

## Código preparado

1. `supabase/migrations/202610190041_s0_meta_vinculo_tentativa_fixture.sql` adiciona **somente um ledger técnico privado** `prumo_private.meta_vinculos_tentativa_fixture_s0`, usando FKs compostas para o mapeamento App/WABA/emissor/loja/canal existente e para `outbox_intencoes_s0`. As duas unicidades independentes são `(app_ref,concessionaria_id,attempt_ref)` e `(app_ref,waba_ref,phone_number_ref,provider_message_id)`.
2. O registro interno `registrar_vinculo_meta_fixture_s0` é `SECURITY INVOKER` restrito por `current_user='postgres'`; resolve loja, WABA e número **na tabela confiável da S0**, não em parâmetros do chamador; exige intenção interna com `BLOQUEADA_GATES` e verifica formato de wamid, destinatário e HTTP 2xx **fictício**. Usa `INSERT ... ON CONFLICT DO NOTHING` e, quando existe colisão, lê ambos os índices e só admite replay da tupla integral idêntica. Uma colisão divergente falha com SQLSTATE `23505`. A escrita não altera o estado comercial nem libera envio. 
3. A consulta `consultar_vinculo_meta_fixture_s0` apenas recupera `LAB_FOUND_EXACT`, `LAB_ABSENT` ou `LAB_CONFLICT`, sempre `ack_allowed:false`, `retry_external:false` e `production_authorized:false`. **`LAB_ABSENT` depois de timeout NÃO autoriza novo POST Graph.**
4. Ambos os contratos não são endpoints/RPC pública; ACLs de `anon`, `authenticated`, `service_role`, `prumo_s0_gateway` e `prumo_s0_signer` explicitamente revogadas, RLS habilitada como camada adicional.
5. `supabase/tests/s0_wa_041_meta_tentativa_binding.sql`: 18 cenários WA14-01..18, todos transacionais e encerrados por `ROLLBACK`, com lojas e emissores sintéticos, idempotência, dois sentidos de unicidade, tentativa de reassociação de App, recuperação ausente/conflitante, transação atômica simulada, cancelamento da intenção, FK e privilégios.
6. `scripts/run-s0-local.sh` foi atualizado **explicitamente** para aplicar a migration 041 após 040 e executar os 18 cenários após WA40, mantendo a guarda de URL exclusivamente local descartável. Não foi usado `apply_migration` no Supabase hospedado.

## Evidências realizadas nesta retomada

- **Código publicado no PR #1 Draft**, blobs verificados por leitura posterior do GitHub.
- **Auditoria estática do conteúdo publicado**: pares de delimitadores `$wa14$` balanceados, parênteses e strings balanceados, identificação dos 18 cenários, existência das duas unicidades, das duas FKs, de RLS, revogações, `ROLLBACK`, e inserção exatamente uma vez de migration e suíte no executor.
- Comparação com o esquema vigente S0-030/040 e checagem do comportamento esperado de `ON CONFLICT DO NOTHING` na documentação PostgreSQL 17.

**NÃO executado:** PostgreSQL 17 não estava disponível no ambiente local e a preparação de instalação não concluiu; portanto **0/18 cenários WA14 executados**, **nenhuma migration 041 aplicada/testada em um servidor**, **nenhum ensaio concorrente PostgreSQL**. Auditoria estática não substitui compilação SQL, execução de transações, verificação de locks/índices nem revisão de permissões efetivas. Testes históricos PG WA-06D (20) e S0-040 (5) também permanecem sem execução confirmada nesta retomada. Não afirmar um gate PostgreSQL PASS.

Agressividade de CI evitada: nenhum workflow remoto foi disparado **manualmente**; commits de integração do executor usam `[skip ci]`. Não presumir que isso altera execuções disparadas automaticamente por commits anteriores.

## Limites técnicos importantes

- O estado `BLOQUEADA_GATES` da outbox não autoriza transmissão. Os registros aqui são **observações fictícias inseridas pelo teste**, não provenientes de Meta Graph.
- As funções são internas ao laboratório: `postgres` e fixtures não constituem autenticação de serviço aprovada; falta desenho de principal privilegiado, revogação/rotação, auditoria de comandos, proof-of-commit independente e contrato físico final.
- Uma operação que perca a resposta do commit PostgreSQL só poderá reconhecer o vínculo por leitura exata **após confirmar a transação no mesmo armazenamento**; não inferir envio ausente nem retentar externamente se não encontrou o vínculo.
- O fechamento de política de retenção, tratamento de backfill e eventual imutabilidade de histórico depende de DEC-WA-06 e revisão S0. O ledger sintético não substitui as entidades comerciais nem decide `vendido` ou `perdido`.
- Sem alteração na S1, sem fusão de branches e sem alteração dos oito estados comerciais.

## Gate seguinte

1. Executar `scripts/run-s0-local.sh` somente contra PostgreSQL 17 descartável, com URL `localhost` e banco `prumo_s0_test_*`, para obter evidência real dos 18 cenários e detectar SQL/ACL incompatíveis; corrigir imediatamente falhas antes de fechar WA-14.
2. Executar `scripts/test_s0_wa_041_concurrency.sh` com PostgreSQL 17 descartável, incluindo WA14C-01..03 em sessões independentes: duas tentativas por um mesmo `wamid`, um `attempt_ref` com dois `wamid` e replay idêntico com verificação pós-commit.
3. Reexecutar os 5 cenários S0-040, 20 WA-06D e a regressão Meta `--all` de 29 suítes em checkout integral.
4. Somente depois revisar integração física Meta → S0 em torno do ledger e das validações de identidade. Credenciais, produção e Meta Graph real seguem fora de escopo sem autorização específica.

## WA-14A — correção da auditoria de código (19/10/2026)

Duas falhas descobertas após a primeira publicação foram corrigidas **antes de qualquer execução PostgreSQL**:

1. A suíte tinha uma variável `r record` reutilizada tanto para o JSONB retornado por `registrar_vinculo_meta_fixture_s0` quanto para o resultado de um `FOR ... SELECT`. A versão atual separa `r jsonb` e `v_change record`, evitando atribuição escalar a record. **Ainda requer confirmação por PL/pgSQL em execução real.**
2. A migration utilizava `{1,1024}` em expressões regulares PostgreSQL para `wamid`. A [documentação oficial PostgreSQL 17](https://www.postgresql.org/docs/17/functions-matching.html) especifica limite **255** para os valores dos quantificadores de repetição. A validação foi trocada por regex `+` e limite explícito `length(...)` de 7 a 1030 caracteres, na tabela e nas duas funções. O novo cenário **WA14-16** cobre `wamid.` com sufixos de 1.024 caracteres (aceito), 1.025 (negado) e vazio (negado).

**Auditoria estática repetida sobre blobs publicados no GitHub**:
- Migration `c9677e2de91261460f9d4a76584d8422f56e24c5`: strings, parênteses e delimitadores de função balanceados; sem quantificadores acima de 255; FKs, duas unicidades, guarda postgres, RLS, revogações e três validações de comprimento presentes.
- Suíte `9afb852adb1d21cf1630a22393fb368b8733eb16`: strings, parênteses e delimitadores balanceados; 18 IDs WA14-01..18 presentes; variáveis JSONB/record distintas; rollback ao final.
- Executor `89b7893ac3b15ee53f4d7ddfa20c06f3b8d2e970`: migration e suíte referenciadas exatamente uma vez.

**Estado após correções: 0/18 testes WA14 executados.** Não há PostgreSQL local/descartável nem foi enviado comando SQL a banco remoto. Os 18 cenários preparados podem revelar novas falhas quando o gate de execução ocorrer.

## WA-14C — ensaios PostgreSQL concorrentes preparados, ainda sem execução

Adicionado `scripts/test_s0_wa_041_concurrency.sh` e incluído **uma única vez** em `scripts/run-s0-local.sh`, sem alterar o isolamento pré-existente do executor. O script realiza autenticação exclusiva de URL `localhost` / `prumo_s0_test_*` e limpa variáveis libpq que poderiam redirecionar a conexão. O teste **não** chama Graph, Meta, Banco, Supabase remoto ou operação comercial.

- **WA14C-01:** duas sessões tentam associar um mesmo `attempt_ref` a dois `wamid`; espera uma gravação e uma rejeição de conflito explícita.
- **WA14C-02:** duas tentativas reivindicam o mesmo `wamid` no mesmo App/WABA/emissor; espera uma gravação e uma rejeição de conflito explícita.
- **WA14C-03:** replay *exatamente igual* de duas sessões concorrentes; espera `LAB_BOUND` seguido de `LAB_REPLAY` e verifica apenas três linhas persistidas no escopo sintético, com recuperação exata sem retry externo.

**Auditoria estática do artefato GitHub:** oito here-docs SQL balanceados, um here-doc Python balanceado, dois caminhos de conflito, três cenários distintos, URL local estrita, `PGHOSTADDR` limpo, ausência de chamadas à rede e referência única no executor. Blobs `test_s0_wa_041_concurrency.sh` `fbab0b1648152d3c4c8ef4b788aa45d7c762a7a1` e `run-s0-local.sh` `4bc7f6784f60a304ee65a01026f418573c1740f6`.

**Estado:** testes de concorrência **0/3 executados**; casos PostgreSQL WA14-01..18 **0/18 executados**. A estrutura do script **não equivale** a execução de comandos em PostgreSQL nem prova lock, serialização ou isolamento. Falta `bash -n` verificado sobre a cópia do GitHub, e execução real em banco descartável.

## WA-14D — imutabilidade em nível de tabela, ainda não homologada

Em inspeção da S0-041, foi identificada uma lacuna real: a unicidade bidirecional garante que uma gravação conflitante **não crie outra linha**, mas não impede um operador privilegiado de realizar `UPDATE` ou `DELETE` direto e alterar/apagar o vínculo original. Isso comprometeria a recuperação `COMMIT_UNKNOWN`.

A migration passou a incluir função `prumo_private.bloquear_mutacao_meta_vinculo_fixture_s0()` (`SECURITY INVOKER`) e dois triggers: **BEFORE UPDATE OR DELETE FOR EACH ROW** e **BEFORE TRUNCATE FOR EACH STATEMENT**, ambos recusando com SQLSTATE `42501` / `IMMUTABLE_TECHNICAL_BINDING`. Os privilégios públicos/técnicos de execução da função foram explicitamente revogados. A referência para esse comportamento é a [documentação PostgreSQL 17 sobre funções de trigger](https://www.postgresql.org/docs/17/plpgsql-trigger.html) e [CREATE TRIGGER](https://www.postgresql.org/docs/17/sql-createtrigger.html).

**Novo WA14-17**: utiliza uma linha já presente no fixture, tenta `UPDATE`, `DELETE` e `TRUNCATE`, exige o erro de imutabilidade esperado em cada tentativa, compara a contagem inicial/final e confirma a associação original por consulta exata.

### Evidências nesta rodada

- Migration publicada Git blob `f92436846e32a162f61509663d704153b29cb55e`.
- Suíte publicada Git blob `59fc57e54f823ef3223eb0c0f94c5d91c72b2ce8`.
- Auditoria estática dos blobs: parênteses/aspas/delimitadores balanceados, três operações de mutação abrangidas, função revogada, preservação de duas unicidades, 18 IDs WA14, encerramento em `ROLLBACK`, migration/suíte/concorrência referenciadas exatamente uma vez pelo runner.
- PostgreSQL e `psql` **não instalados** no ambiente. `apt-get update` tentou acessar a fonte de pacotes, mas a resolução de `deb.debian.org` falhou. Não foi acessado banco remoto.

**Resultado verificável: 0/18 testes WA14 SQL e 0/3 testes concorrentes executados.** Nenhuma migration foi aplicada/compilada no PostgreSQL; esta é auditoria estática, não gate PG PASS. Um administrador superusuário ainda pode desabilitar/remover triggers: o endurecimento não equivale a armazenamento contra adulteração absoluta.

## WA-14E — recuperação exige propriedade da intenção S0

Foi encontrada e corrigida uma lacuna no contrato `consultar_vinculo_meta_fixture_s0`: o SQL validava o App/canal consultado, mas não exigia que `p_intencao` pertencesse àquele mesmo canal/concessionária. Isso permitia obter o resultado genérico `LAB_ABSENT` para uma intenção inexistente ou de outro escopo. Em uma recuperação de commit desconhecido, a ausência só deve ser avaliada **após o vínculo de autoridade S0 ser estabelecido**.

O `SELECT` da função passou a incluir `JOIN prumo_private.outbox_intencoes_s0 o` pela chave composta `(concessionaria_id,canal_id,id=p_intencao)`. Quando essa relação não existe, a função falha com `UNTRUSTED_FIXTURE_SCOPE` (SQLSTATE 42501), em vez de afirmar ausência de vínculo.

**Novo cenário WA14-18:** três consultas inválidas (intenção de outro canal, de outra concessionária e inexistente) devem falhar por escopo; uma consulta sem vínculo, mas com intenção pertencente ao mesmo canal, continua retornando `LAB_ABSENT` **sem retry**, e sem alterar a tabela. Uma consulta de histórico não depende do status atual da intenção para autorizar transmissão; ela **jamais** autoriza envio.

**Evidência realizada:** arquivos GitHub conferidos; migration blob `eade2d459e3f61b0788e831d19a9502a4bc8d96a`, testes blob `193c3f17c4fbe12953aa8d66181c4058f9f269c4`. Auditoria estática de parênteses, strings, delimitadores de função, relacionamento de escopo composto, 18 IDs de teste, rollback e referência única do executor passou. **Não há evidência de compilação/aplicação PostgreSQL:** 0/18 casos SQL e 0/3 testes de concorrência executados.

## S0-PG17-PREFLIGHT — ambiente verificado antes de migrations

Após esclarecer que **não é necessário banco definitivo**, foi adicionado `scripts/check_s0_pg17.sh` ao início de `scripts/run-s0-local.sh`. O novo verificador:

- Recusa URLs que não identifiquem **host estritamente local** (`localhost`, `127.0.0.1` ou `::1`), nome `prumo_s0_test_*`, caminhos/queries inesperados e variáveis libpq que poderiam redirecionar o host.
- Executa uma consulta **somente leitura** para conferir a versão **PostgreSQL 17** e o **nome exato do banco conectado**; só então permite iniciar migrations.
- Recusa `psql` ausente, falhas de conexão, versões diferentes e divergência no banco; não contém instruções para produção nem Graph API.

A suíte independente `scripts/test_s0_pg17_preflight.sh` usa um `psql` **sintético** em diretório temporário, sem rede ou banco. Foi executada nesta sessão local: **10/10 PASS**, incluindo PG16, outro banco, host remoto, query com `hostaddr`, nome não-descartável, `PGHOSTADDR`/`PGSERVICE`, falha de conexão, ausência de `psql` e saída de versão inválida. Ambos os scripts passaram em `bash -n`. **Hashes Git Blob** da cópia exata executada: `check_s0_pg17.sh` `b849f1aaf7ad0379b842f174d9cc988466e2460f`; `test_s0_pg17_preflight.sh` `16d74e911c3b1c40d67f6968a3ca9ea2a4823579`.

**Importante:** o retorno positivo com `psql` sintético é apenas prova de que o *pré-requisito* protege o ambiente. **WA14-01..18 = 0/18 executados em PostgreSQL; WA14C-01..03 = 0/3.** Sem aplicação real da migration.

### Como viabilizar a execução efetiva

O repositório possui `.github/workflows/s0-postgres.yml` na **branch `feat/s0-fundacao-prumo`**, provisionando `postgres:17` e `prumo_s0_test_ci` descartável, chamando o executor completo. **Não existe** esse arquivo na branch `main` conforme leitura GitHub nesta sessão.

Pela [documentação oficial do GitHub](https://docs.github.com/pt/actions/how-tos/manage-workflow-runs/manually-run-a-workflow), `workflow_dispatch` só é recebido quando o arquivo do workflow está no branch padrão; portanto **não presumir que o botão `Run workflow` esteja disponível agora**. O arquivo na branch S0 também declara gatilho `push` na própria branch. Para executar o CI isolado será necessário disparo elegível permitido pelas políticas da conta, não suprimido por `[skip ci]`, e verificar logs/resultado da execução. Este passo pode consumir minutos de GitHub Actions em repositório privado e **não foi acionado nesta sessão**; nenhuma afirmação de CI PASS.

[Referência GitHub — acionamento de workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).

**Classificação honesta:** migration e testes entregues e auditados estaticamente; **persistência PostgreSQL não validada em execução**.
