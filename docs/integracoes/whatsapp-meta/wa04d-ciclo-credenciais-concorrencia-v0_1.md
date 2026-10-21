# WA-04D — simulação de ciclo versionado e fechamento de corrida no roteamento

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Data:** 18/10/2026. **Estado [P/V local]:** engenharia sintética no PR #2, sem conexão com Meta/Supabase, sem uso de credenciais reais, sem HTTP operacional ou ACK, sem merge/deploy. O token definitivo depende da verificação de terceira pessoa.

## 1. Defeito real encontrado em código isolado e reparado

**WA-04D-SEC-01 (alto para eventual integração; sem exposição operacional):** `inspectRoutedMetaPost()`, depois de autenticar HMAC e mapear os canais, usava uma variável `registry` capturada **antes** da iteração para fazer a conferência final. Se houvesse revogação da App durante a checagem de um canal, a verificação final ainda examinava a configuração anterior e podia devolver `ok: true` com os eventos técnicos.

**Demonstração antes do reparo:** teste `LIFE-D-15`, com alteração do registro durante a chamada ao relógio injetado no mapeamento final, **falhou (14/15 PASS, 1 FAIL)**: a App já estava inativa, mas a função aceitou o lote.

**Reparo publicado em `routed-webhook.ts`:** após montar o lote, a função solicita **novo snapshot** de `currentRegistry()`, verifica revisão, App, referência do segredo e vigência e repete, no snapshot recém-obtido, o mapeamento exato de cada evento para loja/canal/App/WABA/emissor. Mudanças incompatíveis produzem `ROUTING_CHANGED` e não liberam o conjunto. O teste `LIFE-D-15` passou depois.

**Limite técnico indispensável:** novas leituras de configuração **não fornecem atomicidade contra mudança imediatamente posterior** à última checagem. Uma futura função de ingresso S0 deverá revalidar o vínculo e gravar o lote em transação atômica/durável, ou definir política consistente para revogação concorrente. Este é um **simulador**, nunca um serviço de ingestão apto a retornar HTTP 200.

## 2. Novo módulo WA-04D

`integrations/whatsapp-meta/lifecycle-simulation.ts` contém `FakeVersionedMetaRegistry`:

- O registro é mantido **somente em memória** como cópia do catálogo fictício, evitando mutação acidental da fonte original.
- `proposeAndSwap(request)` chama o planejador WA-04C, compara revisão corrente, verifica loja/App e produz snapshot alterado **apenas dentro da classe fake**.
- Cada `operation_ref` possui um registro em memória. Reapresentar pedido equivalente sinaliza `REPLAYED_SIMULATED`; reutilizar o identificador com outra operação dá `OPERATION_CONFLICT`. Ações obsoletas negam e não substituem revisão posterior.
- `REVOKE_APP`, `REVOKE_CHANNEL` e `STAGE_ROTATION` propagam-se apenas aos testes da WA-04A/B. Após staging da rotação, a App permanece **desativada** até existir processo separado de verificação externa e reativação autorizada — **não implementado aqui**.
- O resultado retorna códigos técnicos, App ref e revisão, **nunca** corpo de webhook, segredo, texto de cliente ou dados completos do registro. `production_authorized: false` e `retry_automatically: false`.

**Não implementado:** autenticação de administradores, RLS/JWT, persistência, transação Supabase, registro de auditoria durável, locks distribuídos, expiração de operações, recuperação após crash, revogação de token na Meta, realocação física de emissor ou qualquer ação remota. `APPLIED_SIMULATED` significa apenas alteração de um `Map` e objeto privados na fixture Node.

## 3. Evidências técnicas executadas

- Node.js `v22.16.0`: **250/250 testes PASS** nos **17 arquivos de testes** selecionados (235 regressões pré-existentes + **15 LIFE-D**); testes incluem GET/POST HMAC, roteamento por App, identidade técnica, ACK hipotético, Graph fake, revogação, rotação e idempotência simulada.
- TypeScript `v5.8.3`: `tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck --esModuleInterop --types node *.ts` → **PASS** em 12 módulos e seus 17 arquivos de teste.
- Git blobs **idênticos** entre os arquivos executados localmente e os publicados:
  - `lifecycle-simulation.ts`: `3ec084fe84aea3c7e20fb220c61cc796a017b516`.
  - `lifecycle-simulation.test.ts`: `f881ed81cf234c2724d8395f6b1b243e62926d23`.
  - `routed-webhook.ts` corrigido: `d9b0666e7ac65e46528524769a6837f840a9448c`.
- **Não houve** GitHub Actions remoto, teste Meta real, consulta de token, utilização de segredo definitivo, credencial Supabase, recepção de webhook comercial, validação de armazenamento durável ou prova de atomicidade S0.

## 4. Impacto no mapa mental e gates

O `docs/MAPA_MENTAL.md` da branch `feat/s0-fundacao-prumo` será atualizado em sua **tabela de evolução**, registrando WA-04D, teste e correção; **não** será acrescentado nó ao diagrama principal, porque ciclo de vida e revogação já estão representados pela relação de App/credenciais e não surgiu um novo subsistema. Preserva-se o objetivo do usuário de que o desenho cresça **seletivamente**.

**GO somente para continuidade sintética. NO-GO operacional:** verificação externa do token, ambiente DEC-WA-04, política DEC-WA-06, autorização da S0, vínculo App/loja confiável e revalidação durável/atômica antes de qualquer ACK ou Graph real. PR #1 e #2 mantidos abertos em Draft, sem merge/deploy; POC concessionária de demonstração intocada.
