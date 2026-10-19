# WA-12 — recuperação de resultado incerto na vinculação tentativa ↔ wamid (offline)

**Data:** 19/10/2026. **Escopo:** PR #2 Draft, sem deploy, banco remoto, CI acionado, Meta Graph, tokens reais ou mensagens. Este documento descreve **somente código e testes efetivamente realizados** nesta retomada.

## Lacuna verificada

A WA-10/11 já protege associações contraditórias entre `attempt_id` e `wamid`, porém ainda não existia uma simulação específica da incerteza da **gravação do vínculo da resposta Graph na S0**. O módulo `recovery-journal.ts` cobre o ingresso de webhook (outra fase). O `offline-dispatch.ts` protege reservas e falhas de observação; nenhum deles fornece consulta exata **somente leitura** sobre o índice WA-11.

Não confundir: `API_ACCEPTED` da Graph **não é status `sent` ou `delivered`**. E perda da resposta da escrita interna não autoriza retransmissão externa.

## Implementação

1. `integrations/whatsapp-meta/attempt-binding.ts` foi ampliado, preservando os dois índices WA-11. A API nova `lookup(value)` consulta sem criar associação e retorna `SAME`, `CONFLICT`, `ABSENT` ou `INVALID`. `snapshotAttemptIdentity` passou a ser exportada e seu resultado é um snapshot de dados validado, congelado e independente do objeto de origem.
2. `integrations/whatsapp-meta/attempt-commit-simulation.ts` cria `FakeAttemptCommitBoundary`, sem rede ou escrita persistente. Exige evidência Graph `API_ACCEPTED`, HTTP 2xx e os três identificadores (`attempt_id`, `correlation_id`, `provider_message_id`) coincidentes com a identidade técnica. O retorno nunca contém telefone, wamid, segredo, permissão de ACK ou retry.
3. Modos `before_commit_response_lost` e `after_commit_response_lost` retornam **o mesmo** `LAB_COMMIT_UNKNOWN`. O primeiro deixa a memória sem vínculo; o segundo grava a associação no ledger fake mas perde a confirmação da chamada. `recoverExactFixture` apenas lê o ledger: `LAB_ABSENT`, `LAB_FOUND_EXACT`, `LAB_CONFLICT` ou `LAB_INVALID`, sem reenviar mensagem nem assumir estado comercial.
4. `integrations/whatsapp-meta/attempt-commit-simulation.test.ts` acrescenta **WA12-01..17**, incluindo compatibilidade WA-11, adversários `Proxy`, trocas de escopo, tentativas e IDs contraditórios, consulta sem efeito colateral, imutabilidade e nova instância sem durabilidade.
5. `run-offline-tests.sh` incorpora `--commit`; `--focus` inclui WA-12; `--all` exige ao menos **28 arquivos de suíte** e a existência da nova suíte obrigatória. Sem afrouxar o bloqueio de checkout parcial.

## Evidências executadas no ambiente local

- Node.js **v22.16.0**.
- `run-offline-tests.sh --unit` (WA-09): **11/11 PASS**.
- `run-offline-tests.sh --binding` (WA-10/11): **18/18 PASS**.
- `run-offline-tests.sh --commit` (WA-12): **17/17 PASS**.
- Testes locais combinados das três suítes: **46/46 PASS**, `node --experimental-strip-types --test --test-concurrency=1`.
- `tsc --strict --noEmit --skipLibCheck --target ES2022 --module NodeNext --moduleResolution NodeNext --allowImportingTsExtensions` nos três módulos `attempt-binding.ts`, `status-evidence.ts` e `attempt-commit-simulation.ts`: **PASS**. Os arquivos `*.test.ts` não passaram por typecheck completo.
- `bash -n run-offline-tests.sh`: **PASS**.
- `run-offline-tests.sh --all` com checkout parcial: **exit 66**, mensagem de falta de pelo menos 28 suítes. **NÃO É PASS da regressão integrada**.
- O `--focus` **não foi executado**, pois o checkout completo e as dependências não estavam disponíveis.

Blobs GitHub confirmados iguais aos arquivos testados localmente (`git hash-object`):
- `attempt-binding.ts`: `67b2d0bdb716c6b216781199f317b9a98f362aa0`.
- `attempt-commit-simulation.ts`: `598a4a1b702e52d8626ab116fa3507007358ea67`.
- `attempt-commit-simulation.test.ts`: `db4c6d514948116f6f8e00f50a57f73b46047a74`.
- `run-offline-tests.sh`: `33e282ffe3fba11f65ca49c5fb54644fd55eb132`.
- `attempt-binding.test.ts` legado (inalterado): `e5ae026a1de80891db614fb83afbda6b70f821c6`.
- `status-evidence.ts` e `status-evidence.test.ts` legados (inalterados): `50095d75216f13686782476e8f6143d64933f42d`, `bde56f1245b0ee635bc2874950599fc1bd941dd4`.

## Limites, auditoria e próximos gates

- WA-12 é **apenas teste de contrato e comportamento da incerteza**, não transação PostgreSQL; nova instância perde todas as associações. O `COMMIT_UNKNOWN` real requer fonte durável confiável e confirmação S0, nunca simples consulta a memória.
- A identidade de serviço, versão da autorização, escopo App/WABA/emissor e prova de persistência precisam vir de portas internas confiáveis da S0. Não se deduz autorização de um objeto enviado pela Meta ou pelo navegador.
- `REC-01..39` continuam **sem reexecução integrada comprovada nesta retomada**. Executar `--focus` e `--all` após checkout completo, antes de considerar pronta a integração com o conciliador. WA-06D PostgreSQL (20) e S0-040 PostgreSQL (5) ainda pendentes.
- A S0 possui inbox/outbox sintéticos e migrações C07; não foi criado esquema paralelo, migration, RPC, HTTP ACK ou endpoint. O vínculo durável bidirecional ainda exige desenho e testes transacionais PostgreSQL com `COMMIT_UNKNOWN`, locks/índices, isolamento e tratamento de falhas.
- Os oito estados comerciais, S0 e S1 não foram alterados. PR #2 permanece Draft; **nenhum merge, deploy ou uso de API real**.

**Resultado:** código funcional adicional validado em laboratório, com regressão de módulos correlatos 46/46 PASS, porém sem validação integrada completa ou certificação de persistência real.
