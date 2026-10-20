# S0-041 / WA-14 — Vínculo técnico Meta tentativa ↔ wamid (PostgreSQL sintético)

**Data:** 19/10/2026. **Branch:** `feat/s0-fundacao-prumo`, PR #1 **Draft**. Foco na continuação da frente WhatsApp/Meta após WA-13, mantendo S0 como autoridade. Nenhum merge, produção, Meta Graph, clientes, credenciais, banco hospedado ou instituição financeira foi usado.

## Necessidade concreta

WA-11/12/13 possuem um único `FakeAttemptBindingLedger` em memória, com duas direções de unicidade, recuperação exata e bloqueio de reenvios em caso de commit desconhecido. A S0 possui `outbox_intencoes_s0` e `meta_apps_fixture_s0` / `meta_canais_fixture_s0` (S0-030/040), mas ainda não tinha uma associação persistida para esses vínculos. Não recriar as entidades existentes.

## Código preparado

1. `supabase/migrations/202610190041_s0_meta_vinculo_tentativa_fixture.sql` adiciona **somente um ledger técnico privado** `prumo_private.meta_vinculos_tentativa_fixture_s0`, usando FKs compostas para o mapeamento App/WABA/emissor/loja/canal existente e para `outbox_intencoes_s0`. As duas unicidades independentes são `(app_ref,concessionaria_id,attempt_ref)` e `(app_ref,waba_ref,phone_number_ref,provider_message_id)`.
2. O registro interno `registrar_vinculo_meta_fixture_s0` é `SECURITY INVOKER` restrito por `current_user='postgres'`; resolve loja, WABA e número **na tabela confiável da S0**, não em parâmetros do chamador; exige intenção interna com `BLOQUEADA_GATES` e verifica formato de wamid, destinatário e HTTP 2xx **fictício**. Usa `INSERT ... ON CONFLICT DO NOTHING` e, quando existe colisão, lê ambos os índices e só admite replay da tupla integral idêntica. Uma colisão divergente falha com SQLSTATE `23505`. A escrita não altera o estado comercial nem libera envio. 
3. A consulta `consultar_vinculo_meta_fixture_s0` apenas recupera `LAB_FOUND_EXACT`, `LAB_ABSENT` ou `LAB_CONFLICT`, sempre `ack_allowed:false`, `retry_external:false` e `production_authorized:false`. **`LAB_ABSENT` depois de timeout NÃO autoriza novo POST Graph.**
4. Ambos os contratos não são endpoints/RPC pública; ACLs de `anon`, `authenticated`, `service_role`, `prumo_s0_gateway` e `prumo_s0_signer` explicitamente revogadas, RLS habilitada como camada adicional.
5. `supabase/tests/s0_wa_041_meta_tentativa_binding.sql`: 16 cenários WA14-01..16, todos transacionais e encerrados por `ROLLBACK`, com lojas e emissores sintéticos, idempotência, dois sentidos de unicidade, tentativa de reassociação de App, recuperação ausente/conflitante, transação atômica simulada, cancelamento da intenção, FK e privilégios.
6. `scripts/run-s0-local.sh` foi atualizado **explicitamente** para aplicar a migration 041 após 040 e executar os 16 cenários após WA40, mantendo a guarda de URL exclusivamente local descartável. Não foi usado `apply_migration` no Supabase hospedado.

## Evidências realizadas nesta retomada

- **Código publicado no PR #1 Draft**, blobs verificados por leitura posterior do GitHub.
- **Auditoria estática do conteúdo publicado**: pares de delimitadores `$wa14$` balanceados, parênteses e strings balanceados, identificação dos 16 cenários, existência das duas unicidades, das duas FKs, de RLS, revogações, `ROLLBACK`, e inserção exatamente uma vez de migration e suíte no executor.
- Comparação com o esquema vigente S0-030/040 e checagem do comportamento esperado de `ON CONFLICT DO NOTHING` na documentação PostgreSQL 17.

**NÃO executado:** PostgreSQL 17 não estava disponível no ambiente local e a preparação de instalação não concluiu; portanto **0/16 cenários WA14 executados**, **nenhuma migration 041 aplicada/testada em um servidor**, **nenhum ensaio concorrente PostgreSQL**. Auditoria estática não substitui compilação SQL, execução de transações, verificação de locks/índices nem revisão de permissões efetivas. Testes históricos PG WA-06D (20) e S0-040 (5) também permanecem sem execução confirmada nesta retomada. Não afirmar um gate PostgreSQL PASS.

Agressividade de CI evitada: nenhum workflow remoto foi disparado **manualmente**; commits de integração do executor usam `[skip ci]`. Não presumir que isso altera execuções disparadas automaticamente por commits anteriores.

## Limites técnicos importantes

- O estado `BLOQUEADA_GATES` da outbox não autoriza transmissão. Os registros aqui são **observações fictícias inseridas pelo teste**, não provenientes de Meta Graph.
- As funções são internas ao laboratório: `postgres` e fixtures não constituem autenticação de serviço aprovada; falta desenho de principal privilegiado, revogação/rotação, auditoria de comandos, proof-of-commit independente e contrato físico final.
- Uma operação que perca a resposta do commit PostgreSQL só poderá reconhecer o vínculo por leitura exata **após confirmar a transação no mesmo armazenamento**; não inferir envio ausente nem retentar externamente se não encontrou o vínculo.
- O fechamento de política de retenção, tratamento de backfill e eventual imutabilidade de histórico depende de DEC-WA-06 e revisão S0. O ledger sintético não substitui as entidades comerciais nem decide `vendido` ou `perdido`.
- Sem alteração na S1, sem fusão de branches e sem alteração dos oito estados comerciais.

## Gate seguinte

1. Executar `scripts/run-s0-local.sh` somente contra PostgreSQL 17 descartável, com URL `localhost` e banco `prumo_s0_test_*`, para obter evidência real dos 16 cenários e detectar SQL/ACL incompatíveis; corrigir imediatamente falhas antes de fechar WA-14.
2. Executar testes de concorrência em sessões independentes: duas tentativas competindo por `wamid` e duas observações tentando alterar o `wamid` de uma única tentativa, com verificação pós-commit.
3. Reexecutar os 5 cenários S0-040, 20 WA-06D e a regressão Meta `--all` de 29 suítes em checkout integral.
4. Somente depois revisar integração física Meta → S0 em torno do ledger e das validações de identidade. Credenciais, produção e Meta Graph real seguem fora de escopo sem autorização específica.

## WA-14A — correção da auditoria de código (19/10/2026)

Duas falhas descobertas após a primeira publicação foram corrigidas **antes de qualquer execução PostgreSQL**:

1. A suíte tinha uma variável `r record` reutilizada tanto para o JSONB retornado por `registrar_vinculo_meta_fixture_s0` quanto para o resultado de um `FOR ... SELECT`. A versão atual separa `r jsonb` e `v_change record`, evitando atribuição escalar a record. **Ainda requer confirmação por PL/pgSQL em execução real.**
2. A migration utilizava `{1,1024}` em expressões regulares PostgreSQL para `wamid`. A [documentação oficial PostgreSQL 17](https://www.postgresql.org/docs/17/functions-matching.html) especifica limite **255** para os valores dos quantificadores de repetição. A validação foi trocada por regex `+` e limite explícito `length(...)` de 7 a 1030 caracteres, na tabela e nas duas funções. O novo cenário **WA14-16** cobre `wamid.` com sufixos de 1.024 caracteres (aceito), 1.025 (negado) e vazio (negado).

**Auditoria estática repetida sobre blobs publicados no GitHub**:
- Migration `c9677e2de91261460f9d4a76584d8422f56e24c5`: strings, parênteses e delimitadores de função balanceados; sem quantificadores acima de 255; FKs, duas unicidades, guarda postgres, RLS, revogações e três validações de comprimento presentes.
- Suíte `9afb852adb1d21cf1630a22393fb368b8733eb16`: strings, parênteses e delimitadores balanceados; 16 IDs WA14-01..16 presentes; variáveis JSONB/record distintas; rollback ao final.
- Executor `89b7893ac3b15ee53f4d7ddfa20c06f3b8d2e970`: migration e suíte referenciadas exatamente uma vez.

**Estado após correções: 0/16 testes WA14 executados.** Não há PostgreSQL local/descartável nem foi enviado comando SQL a banco remoto. Os 16 cenários preparados podem revelar novas falhas quando o gate de execução ocorrer.

**Classificação honesta:** migration e testes entregues e auditados estaticamente; **persistência PostgreSQL não validada em execução**.
