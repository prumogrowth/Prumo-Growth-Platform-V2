# WA-13 — conciliação compartilhada S0 → Meta com vínculo pré-confirmado (offline)

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Data:** 19/10/2026. **Estado:** entregue na branch do [PR #2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2). **Não** é persistência PostgreSQL, endpoint Meta, ACK real, homologação da S0 ou autorização de envio. Sem credenciais, CI acionado, Supabase hospedado, merge, deploy ou contato real.

## Lacuna de engenharia

A WA-11 criara um ledger bidirecional sintético de tentativa ↔ wamid. A WA-12 simulava resultado de commit incerto. O conciliador `FakeMetaStatusReconciler`, porém, mantinha **outra instância** do ledger e, ao tentar reaproveitar um vínculo já registrado pela WA-12, considerava `SAME` um conflito. Faltava um caminho integrado e **somente consulta** entre a recuperação exata da tentativa e a projeção técnica de callbacks.

A S0 já possui estruturas sintéticas de inbox/outbox/recuperação; por isso, não se introduziu nenhuma estrutura paralela de banco.

## Código implementado

- **`attempt-commit-simulation.ts`**: recebe opcionalmente a instância `FakeAttemptBindingLedger` compartilhada; sem mudança no comportamento padrão.
- **`technical-reconciliation.ts`**: recebe opcionalmente o mesmo ledger. Ao criar a projeção interna de um envio, aceita `SAME` apenas quando a tupla técnica é idêntica. `CONFLICT` e `INVALID` continuam recusados; o conciliador preserva as ocorrências de status e as verificações de App/WABA/emissor/destinatário.
- **`s0-binding-bridge.ts`** (**novo**): `FakeMetaS0BindingBridge` conecta WA-12 e conciliador usando um único ledger privado de laboratório. `recordAcceptedFixture` simula o registro da observação Graph no vínculo; `recoverAndLinkFixture` **somente consulta** a existência de vínculo exato antes de permitir projetá-lo para correlação. `LAB_COMMIT_ABSENT`, `LAB_BINDING_CONFLICT` e `LAB_INVALID` não criam um envio nem disparam retry externo. Entrada com escopo incoerente é rejeitada; objetos e evidências são lidos por snapshot de descritores de dados.
- **`s0-binding-bridge.test.ts`** (**novo**): 18 testes WA13-01..18, cobrindo sucesso, commit perdido antes e depois, callbacks pendentes e fora de ordem, App/loja/WABA/emissor/destino, unicidade nos dois sentidos, replays, snapshots hostis, nova instância sem durabilidade e ausência de autorização externa.
- **`run-offline-tests.sh`**: modo `--bridge`, modo `--focus` atualizado com WA-13, `--all` exige agora pelo menos **29** suítes e presença do arquivo `s0-binding-bridge.test.ts`.

## Evidências reais, executadas neste incremento

**Checkout parcial local** construído dos arquivos da branch do PR #2, usando o conector GitHub; hashes `git hash-object` dos originais `technical-reconciliation.ts`, `technical-reconciliation.test.ts`, `graph-outbound.ts` e `graph-outbound.test.ts` coincidiram com blobs publicados.

- **REC-01..39 (baseline do conciliador): 39/39 PASS**, incluindo REC-36..39 até então pendentes.
- **WA-09 até WA-12 (baseline): 46/46 PASS**.
- **WA-13 isolada:** `--bridge` **18/18 PASS**.
- **`--focus` integrado atualizado:** **120/120 PASS**, englobando seis suítes: `attempt-binding`, `attempt-commit-simulation`, `s0-binding-bridge`, `status-evidence`, `technical-reconciliation`, `graph-outbound`.
- **TypeScript estrito:** `tsc --strict --noEmit --skipLibCheck --target ES2022 --module NodeNext --moduleResolution NodeNext --allowImportingTsExtensions` **PASS** nos seis módulos correspondentes. **Limite:** a checagem local utilizou stubs *somente de tipos* para `inbound.ts` e `graph-template.ts`, com interfaces reproduzidas das definições do GitHub. Isso **não equivale** a typecheck do checkout integral. Arquivos de teste não foram totalmente typechecked.
- **Executor Bash:** `bash -n` **PASS**.
- **`--all` parcial:** **exit 66**, guardrail funcionando; 29 suítes completas **não executadas**.

### Identidade dos arquivos entregues

Blobs GitHub da versão testada localmente:

| Arquivo | Blob SHA |
|---|---|
| `s0-binding-bridge.ts` | `f14fd5dda2c9a0b2ed39929218b3aa032913e566` |
| `s0-binding-bridge.test.ts` | `5400e3cfc62917aa5be479e6f7e5f27361a4879b` |
| `attempt-commit-simulation.ts` | `ec302faf82640c5b35cbfc5e1f9d53cdb0662a10` |
| `technical-reconciliation.ts` | `181487e7da374f8f4a3349acffb59499dfe562a4` |
| `run-offline-tests.sh` | `ec33b81fc458c618f68c4c2c749520c5d05af406` |

## Auditoria de segurança e fronteiras

1. **`API_ACCEPTED` não comprova `sent`, `delivered` ou `read`.** Somente callbacks técnicos sintéticos podem atualizar a projeção técnica; nenhuma mudança de `vendido`, `perdido`, transferência ao operador ou elegibilidade.
2. **`COMMIT_UNKNOWN` não autoriza reenvio externo.** Mesmo uma consulta `LAB_COMMIT_ABSENT` não prova ausência de envio na Meta. O código da WA-13 nunca emite Graph HTTP nem ACK real.
3. O bridge supõe que o chamador real autenticou App e serviço, verificou o vínculo ativo e persistiu todas as ocorrências pertinentes. **O laboratório não autentica nem faz persistência física.** A recuperação consulta somente um `Map` compartilhado; uma nova instância perde o histórico.
4. O `wamid` é identidade técnica opaca; eventos repetidos em posições distintas não podem ser deduplicados por ele. Os índices utilizam App/WABA/emissor exatos e a identidade interna da tentativa.
5. A possibilidade de injetar um ledger em testes **não é autorização de escrita comercial**. Em produção será exigido um contrato privado S0 que comprove leitura e commit sob controle de acesso e transação.
6. Não foram alteradas migrations S0, PR #1 ou PR #5. O PR #2 segue Draft.

## Pendências e próximo gate

- **Regressão `--all`** de 29 suítes num checkout integral; testes PG17 locais WA-06D (20 cenários) e S0-040 (5 cenários) ainda sem evidência executada nesta retomada.
- Definir e testar na S0 uma associação bidirecional durável com unicidade por tentativa e por `[App,WABA,emissor,wamid]`, prova de commit e identidade de serviço confiável. Tratar estados incertos, conflito e preservação de ocorrência como parte da transação, antes de conectar Graph real.
- Validar compatibilidade em ambiente de testes com código integral da S0/S1 e contratos atuais; só depois, e com autorização, APIs reais.

**Resultado verificado:** WA-13 implementada, `--focus` **120/120 PASS**; persistência e homologação reais ainda não implementadas.
