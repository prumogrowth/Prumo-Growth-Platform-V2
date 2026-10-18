# WA-05A — handoff S0 simulado com revalidação no commit | 18/10/2026

**Estado:** [P/V local], **sem Supabase real e sem ACK HTTP**. A etapa implementa e testa em memória a fronteira entre o roteamento autenticado Meta WA-04B e a futura inbox transacional da S0. O token definitivo continua aguardando verificação de uma terceira pessoa.

## 1. Cadeia simulada

`integrations/whatsapp-meta/transactional-ingress.ts` expõe duas fixtures sintéticas e nenhuma porta de produção:

1. `FakeProtectedPayloads`: mantém uma **cópia local de bytes fictícios**, indexada por referência privada de teste. O nome não significa criptografia, proteção LGPD ou retenção durável. A inbox exige correspondência **exata dos bytes verificados** com esse conteúdo; metadados sem corpo não passam.
2. `FakeTransactionalInbox.inspectAndCommitFixture()`: executa a inspeção **real de código, mas com segredos fictícios** `inspectRoutedMetaPost()` (rota selecionada pelo host fake, App Secret fake, HMAC SHA-256 sobre bytes imutáveis, parsing e escopo dos eventos). Antes de simular o commit, calcula SHA-256 do corpo, confere a referência fake de payload, revê um **novo snapshot** do `FakeVersionedMetaRegistry` e revalida App/revisão/vigência e vínculo exato concessionária/canal/WABA/phone para **todos** os eventos do lote.
3. Se houver revogação de App/canal, staging de rotação ou inconsistência de configuração antes do commit, **nenhum item é gravado**. No laboratório, a inserção de todos os marcadores de ocorrência e do registro de lote ocorre sem `await` (em **um processo Node**), mas não equivale a transação ACID nem sobrevive ao reinício.
4. Cada item recebe um **identificador de ocorrência fictício e diferente**; a posição incorpora `entry_index`, `change_index`, `array_kind=messages|statuses` e `item_index`. Dois callbacks iguais recebidos em **lotes distintos** não são confundidos nem deduplicados automaticamente por `wamid/status/timestamp`. O prefixo sequencial da fixture é só para teste: um futuro `occurrence_ref` deve ser criado pelo ingresso confiável da S0.
5. `batch_ref` é uma referência fictícia assumida como gerada por ingresso protegido. Repetir a mesma referência com conteúdo e contexto idênticos não duplica marcadores; reutilizá-la com outro conteúdo gera `CONFLICT`. **A Meta não fornece esse batch_ref; o valor da fixture não comprova uma entrega única do provedor**.
6. Retorna `SIMULATED_COMMIT`, `SIMULATED_REPLAY`, `BLOCKED`, `CONFLICT` ou `SIMULATED_WRITE_FAILURE`, além de contagens e códigos não sensíveis. **`ack_allowed:false` e `production_authorized:false` em todas as saídas**. O módulo propositalmente NÃO fornece `DurableBatchReceipt` (`commit_state: COMMITTED`) nem invoca `decideBatchAck()`, para evitar uma falsa prova de persistência.

**Limites de laboratório:** 100 lotes, 1.000 marcadores e até 100 eventos por POST. O estado é um `Map` privado de memória local, sem isolamento entre processos, transação SQL, prova de persistência/recovery, armazenamento protegido de clientes, autenticação real da origem do registry, autorização comercial C02/C07, fila ou reprocessamento. Não deve ser associado ao webhook público da Meta.

## 2. Revalidação transacional exigida da S0 para integração futura [R]

O simulador demonstra o gate lógico, mas a implementação operacional deverá fazer em uma **transação privilegiada e durável**:

- Confirmar origem e identidade da rota selecionadas **antes** de interpretar o POST (validadores da frente Meta); consumir material autenticado por uma interface interna com origem confiável, não campos de cliente escolhidos pelo caller.
- Ler com bloqueio/versão estável o vínculo vigente **App/WABA/Phone Number ID → concessionária/canal**, no mesmo domínio transacional que controla revogação/rotação. Rejeitar mudanças de revisão, canal ou titularidade até o commit; a simples releitura do registro no JavaScript não dá essa garantia.
- Preservar o **corpo integral protegido/replayable**, seu hash/integridade e a referência do lote, e inserir cada `occurrence_ref` com posição `array_kind` e uma intenção durável de processamento, **atomically**, sem ACK antes da confirmação da transação. Status sem correlação devem permanecer recuperáveis.
- Diferenciar **deduplicação do lote por identidade interna protegida** da idempotência de efeito; não usar apenas `statuses[].id` (ID de mensagem) ou `status+timestamp` para descartar observações.
- Resolver política de ACK/HTTP, quarentena e replay somente com o gate DEC-WA-06 e retorno autenticado da S0. Um 200 da Graph é aceite de envio, não entrega; um status `read` não é venda.
- Não permitir envio C03/C06/C12 sem a **autorização comercial atual** da S0; este módulo trata somente ingresso técnico, não libera o Graph.

**Dependências explícitas:** DEC-WA-04 (ambiente), DEC-WA-06 (segredos, retenção, falhas, ACK), origem autenticada do registry, capacidade de armazenamento protegido e mecanismo transacional no núcleo. DEC-WA-05 determina ativos Meta por concessionária, não libera operação. POC `whatsapp-webhook-sandbox` hospedada permanece intacta.

## 3. Evidência de execução

Node.js v22.16.0: `node --experimental-strip-types --test *.test.ts` em **18 arquivos de testes** → **268/268 PASS** (250 testes anteriores + 18 novos `TX-01..TX-18`), incluindo HMAC válido/inválido, lote agregado, revogação durante handoff, staging de rotação, payload ausente/divergente, duplicidade/colisão de lote, repetição legítima de status, falha de gravação sem parcial, entrada mutável e isolamento entre Apps.

TypeScript 5.8.3: `tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck --esModuleInterop --types node *.ts` → **PASS** nos 13 módulos e 18 suítes locais.

**Integridade GitHub confirmada:** `transactional-ingress.ts` blob `d621b2c23c65bb91449809b9b9801388619ae855`; `transactional-ingress.test.ts` blob `7afa821432516564f4a3a0be3f5062922a2b5ec3`. Os arquivos locais executados e versionados são idênticos. Bibliotecas WA-01..WA-04 usadas nos testes correspondem aos blobs anteriores da branch.

**Não houve:** GitHub Actions remoto, conexão Supabase hospedado, migration, webhook Meta real, valor de segredo definitivo, Graph, número comercial, merge, deploy ou custo.

## 4. Mapa mental e continuidade

O **primeiro diagrama** do `docs/MAPA_MENTAL.md` S0 já apresenta o componente `Inbox durável antes do ACK [R S0]`. **Não acrescentar novo nó** só para esta simulação; atualizar a linha WA-05A no acompanhamento e preservar o significado de [R] até existir transação real. Próxima etapa independente: desenhar a interface contratual de recibo assinado do serviço S0 e testes de redelivery/recovery, **sem gerar respostas HTTP reais**.
