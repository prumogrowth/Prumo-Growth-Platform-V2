# F01/F02/F03 — mudança de versões entre F03 e F02 no mesmo ciclo (A34)

**28/10/2026.** Checkpoint anterior `cba585d`, CI #40665400236 SUCCESS (1.243 testes, 33 critérios). Esta execução é desenvolvimento da frente OpenAI. Não altera a S0 nem repete auditoria geral.

## Situação corrigida

A regra A33 preservava o mesmo vetor `case/cycle/form/catalog/assignment` entre F03 e F02 de um episódio humano. Isso impede o uso de versões ultrapassadas, mas também recusa uma situação possível: a ficha ou uma atribuição é atualizada **depois** da análise F03 e **antes** da proposta de recontato F02.

O incremento A34 permite **um evento de atualização declarado por episódio**, caso essas versões mudem. Esse evento aparece no ledger F01/F02/F03 como `S0_VERSION_UPDATE_CLAIM`, exclusivamente enquanto a jornada ainda está na etapa F03. Ele **não provoca transição**, não invoca S0, não atualiza banco e não inicia F02. A etapa F02 segue dependente de `S0_F02_POSTHUMAN_REQUEST`, e a sequência inteira continua sendo validada pelas funções originais da S2 (JS executado em Node) mais o controlador de provas F02 (Python).

`VersionTransitionClaim` relaciona ID do evento, concessionária, lead, caso, encerramento, proposta F03 e solicitação F02. Também confronta dois vetores **alegados**: `from_versions` da F03 e `to_versions` da F02. Sem atualização, a regra anterior A33 continua exigindo igualdade. Com o evento intermediário, os vetores devem diferir e ser não decrescentes campo a campo, e o pedido F02 deve usar exatamente o resultado. Alterações entre ciclos humanos continuam sendo verificadas contra a versão final do ciclo anterior; novas conclusões humanas não exigem incremento automático.

Todas as verificações são **consistência de declarações não autenticadas**: o nome `S0_VERSION_UPDATE_CLAIM` não é um novo contrato autorizado da S0. A fonte real, revisão do estado persistido, assinatura/HMAC, aprovação humana e causalidade transacional só poderão ser ratificadas pela S0 no processo futuro de integração. Alegar uma alteração, mesmo com event ID correto, não confere autorização comercial nem garantia de procedência.

## Negativas e compatibilidade

`backend/tests/test_f02_intraepoch_version_candidate.py` acrescenta 32 testes sintéticos para: caso positivo de versões atualizadas; preservação dos fluxos A33; falta de evento/testemunho, dupla declaração, versões antigas, troca de loja/lead/caso/closure/evento, evento antes de F03 ou depois de F02, revisão sem alteração, regressão, tipos inválidos, opt-out, aconselhamento F03 de desistência/perda, saída sem autoridade e execução da S2 original.

O código adicionado não modifica módulos S0, GoTrue, RPC, Meta nem credenciais; não há deploy, chamadas à OpenAI real, escrita no Supabase hospedado, emissão de mensagens ou merge. Todos os gates G01–G07 permanecem pendentes de homologação operacional, e o PR #1 permanece Draft.

**Limitação assumida:** o laboratório aceita uma única alteração intermediária por episódio. Caso uma situação real envolva mais de uma atualização entre F03 e F02, será necessário modelar uma cadeia de versões verificável com fonte S0 ratificada — não inferir que múltiplos eventos sintéticos legitimam recontato.
