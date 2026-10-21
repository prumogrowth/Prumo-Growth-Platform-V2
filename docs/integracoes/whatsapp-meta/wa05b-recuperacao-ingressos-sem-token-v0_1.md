# WA-05B — recuperação sintética de ingressos e efeitos | 18/10/2026

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Estado [P/V local]:** laboratório offline na branch Draft do PR #2, sem credenciais Meta, sem Supabase hospedado, sem transporte real e sem implantação. O token segue pendente de verificação por terceira pessoa.

## 1. Objetivo e limites

A WA-05A simulou a revalidação de vínculo App/WABA/emissor/loja **antes de uma gravação fictícia integral**. A WA-05B complementa a modelagem de **crash, resposta de commit perdida, reentrega, leases de processamento e reconciliação após falha**. Essas funções não constituem uma camada de persistência S0, nem devem ser conectadas diretamente ao webhook.

Módulo `integrations/whatsapp-meta/recovery-journal.ts`:
- `FakeS0RecoveryJournal`: um **único objeto em memória** compartilhado entre execuções de um trabalhador fictício. A criação de outra instância **perde tudo**, como testado explicitamente em RECOV-13. Não é journal durável, não é banco e não armazena um payload criptografado.
- `admit(batch, fault)`: aceita **apenas descritores sintéticos presumidamente autenticados de fora**, incluindo `batch_ref`, App, loja, canal, referência de payload, digest e array de posições `messages|statuses`. Não verifica HMAC, segredo, hash contra bytes, JWT ou vínculo S0; `payload_digest` é somente texto com formato validado. Falha ANTES da gravação → `LAB_NOT_COMMITTED` sem estado; falha DEPOIS da gravação em memória → `LAB_RESULT_UNKNOWN` mas os marcadores permanecem. Nenhuma resposta prova transação remota.
- `recover(batch)`: permite consulta por mesmo identificador **e todos os campos de escopo/payload/ocorrência**, rejeitando colisões; devolve apenas contagens de trabalho concluído/pendente e `ack_allowed:false`. É um ensaio de como a S0 poderia consultar seu estado **confiável**, não uma rota pública de readback.
- Repetição do **mesmo batch interno** com conteúdo idêntico resulta `LAB_ALREADY_COMMITTED`, sem inserir mais ocorrências; ID igual e conteúdo divergente resulta `LAB_CONFLICT`. Dois batches diferentes com callbacks de mesmo `wamid` preservam **duas** observações. O ID da mensagem **não é** o ID da ocorrência, nem identifica univocamente callback, como requerido na WA-03A.
- `claim(owner,tick,duration)` representa reserva com lease fictício para um único trabalhador; outro trabalhador não o assume até expiração. O lease vencido pode ser recuperado, mas um token antigo não conclui o trabalho. `finish(..., after_apply)` simula perda da confirmação **depois de contabilizar efeito estritamente interno ao mesmo Map**. A marca de `done` e o contador são atualizados juntos nesse cenário local: replay não duplica o efeito **fictício**.
- **Não modela exatamente-once externo**: uma chamada Graph, IA, mensagem humana, cobrança ou alteração em outro sistema pode ter sido executada antes de perder resposta. Esses efeitos exigem idempotência de negócio específica e/ou `UNCERTAIN_EXTERNAL` + conciliação, nunca retry automático.

**Toda decisão de ingresso/recuperação** contém `ack_allowed:false` e `production_authorized:false`. O resultado de processamento contém `retry_external:false`. Não se produz `DurableBatchReceipt` com `commit_state:COMMITTED` e o módulo **nunca invoca `decideBatchAck`**, mesmo quando a simulação usa a palavra `COMMITTED` com prefixo `LAB_`.

## 2. Critérios necessários para implementação real [R — S0]

Antes de operar a Meta, a frente principal precisa definir uma transação Postgres ou serviço privilegiado que:
1. Receba o lote **efetivamente autenticado e escopado** pelo gateway Meta; faça validação da origem do serviço S0 e vínculo canal/loja atual, sem confiar em flags de objetos de entrada.
2. Em uma mesma transação durável, associe **corpo original protegido e íntegro**, batch interno, `occurrence_ref` de cada item, tarefas recuperáveis e versão do vínculo da loja. O parser bruto e a autenticidade HMAC continuam responsabilidade de WA-01/04, não deste módulo.
3. Em falha/crash após commit mas antes da resposta, consulte a **fonte durável** com credenciais mínimas e retenha `COMMIT_UNKNOWN` até obter prova de persistência, sem assumir que a operação não ocorreu.
4. Diferencie **deduplicação de admissões do mesmo batch interno** de idempotência dos efeitos C02/C07. Não usar `wamid+status+timestamp` como chave universal; conservar callbacks técnicos legítimos.
5. Use claims/leases persistidos com bloqueio ou compare-and-swap, geração de lease, fencing e reprocessamento após expiração; operações externas com aceitação possivelmente incerta exigem conciliação antes de qualquer retry.
6. Retorne recibo interno autenticado somente após commit durável; políticas de 200/503/quarentena/replay permanecem **DEC-WA-06 [R]**. A decisão estrutural `decideBatchAck` WA-01B não autentica por si só um recibo.

A janela entre confirmação do commit S0 e resposta HTTP/Meta também necessita política de redelivery aprovada. Nenhum módulo atual oferece esse contrato operacional.

## 3. Evidência reproduzida

**Node.js v22.16.0**: `node --experimental-strip-types --test *.test.ts` sobre **19 suítes** → **294/294 PASS**, sendo **268 regressões WA-01 a WA-05A** + **26 testes RECOV novos**. Os casos novos cobrem antes/depois de commit, resposta perdida, replay compatível/conflitante, escopo App/loja/canal, recuperação após reinício lógico, callbacks iguais em batches diferentes, leases, fencing, crashes após efeito fictício, validação de entradas e retorno sem ACK.

**TypeScript v5.8.3**: `tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck --esModuleInterop --types node *.ts` → **PASS**, contemplando **14 módulos e 19 arquivos de teste**.

**Correspondência dos blobs Git locais versus PR #2**, verificada após publicação:
- `recovery-journal.ts`: `45e296be9ea63d971b9853179d57fb9afb1af14b`
- `recovery-journal.test.ts`: `0d956e0c467179f63704722a3f35bce1fe49310c`

Nenhum CI remoto, dado de cliente, segredo, webhook Meta real, banco Supabase hospedado, migration, Graph API, número comercial, deploy ou merge foi acionado.

## 4. Mapa mental e gate

O `docs/MAPA_MENTAL.md` na branch `feat/s0-fundacao-prumo` acompanha a WA-05B como **proposta e teste local**, sem declarar durabilidade real. O diagrama principal **não ganhou um nó novo**, pois `Inbox durável antes do ACK [R S0]` e `Revisão do gestor/versão/justificativa` já contemplam os subsistemas relevantes; detalhes de recuperação pertencem a este documento.

**GO** para auditoria cruzada do contrato simulado e especificação de interfaces S0; **NO-GO** para conectar a WA-05B ao webhook operacional, emitir ACK 200, migrar banco hospedado ou testar Meta real. DEC-WA-04 (ambiente), DEC-WA-06 (segredos/retenção/recovery/ACK), origem autenticada dos registros e verificação externa do token continuam pendentes.

**Auditoria adicional WA-05B:** RECOV-25/26 corrigiram o filtro de ID `wamid` (agora admite caracteres opacos/padding `=` sem whitespace/controles, coerente com a WA-02A) e a exceção por metadado de fixture não clonável (agora `LAB_INVALID` sem inserir lote parcial). Ambas as regressões integram o total **294/294**. Nenhum ID Meta foi recebido de uma API real.
