# E04 F01/F02/F03 — versão por encerramento em jornadas com múltiplos ciclos humanos

**28/10/2026 — incremental A33.** Base fixada: `55d8d5a`, GitHub Actions #40663021036 SUCCESS, 1.218 testes. A etapa anterior A32 já chama os validadores JavaScript S2 originais diretamente a partir da F02 Python. Este incremento não repete auditorias nem altera S0.

## Problema concreto

Uma mesma jornada pode seguir `F01 → F02 → F01 → humano → F03 → F02 → cliente responde → humano novamente → F03 → F02`. O controlador de rota e o gate de provas existentes já verificam o **último encerramento**; faltava uma relação explícita das propostas F03 e F02 de **cada** episódio humano com as versões de dados alegadas naquele ciclo. Caso contrário, uma proposta de um ciclo antigo pode ser copiada para o segundo e continuar internamente válida se o validador S2 receber versões esperadas e atuais iguais, porém antigas.

## Solução implementada em laboratório

`backend/f02_multihuman_epoch_candidate.py`: `check_multi_human_epoch_candidate` aceita a mesma jornada, visita S2 e prova F02 já validadas pela A32, além de uma lista exata e ordenada de `HumanEpochClaim`. Cada episódio vincula `closure_id`, ID do evento de encerramento, ID do evento F03 e ID do pedido F02 pós-humano, mais o conjunto de versões **reivindicadas** nos domínios `case/cycle/form/catalog/assignment`. Essas versões precisam coincidir com os escopos `expected/current` da **F03 e da F02** do episódio correspondente.

A implementação exige um ticket por encerramento, sem lacunas, duplicações, reutilização de IDs ou permutação entre ciclos; exige coerência da sequência já validada pela rota, e impede **regressão numérica de versões alegadas** entre os ciclos. Entretanto, **não exige incremento automático** em todo fechamento humano: a S0 não ratificou essa regra. Versões iguais podem ser coerentes, especialmente quando não há mutação de dados. Alterações legítimas entre F03 e F02 no mesmo ciclo deverão ter novo mapeamento/ratificação contratual antes de uma integração real; a regra experimental é deliberadamente conservadora.

A camada reusa `check_routed_proof_with_pinned_s2` (A32), que por sua vez chama `check_routed_posthuman_proof` e os quatro validadores S2 JavaScript do commit `ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c`. Não duplica a lógica da F01, F02 ou F03; os tickets são **descrições sintéticas de consistência**, não provas assinadas.

## Negativas importantes

As 25 verificações em `backend/tests/test_f02_multihuman_epoch_candidate.py` cobrem dois encerramentos humanos positivos, igualdade de versões admitida, troca/omissão/reuso de ticket, reuso de prova do encerramento anterior, F03 ou F02 com versões antigas, mutações sem atualização de escopo, falta de retomada humana autorizada, desistência e revisão humana, `opt-out`, incerteza Meta, cruzamento de concessionária/caso e versão fixada de Node/S2 indisponível.

**Nenhum status significa autorização comercial.** Mesmo a resposta `MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY` não confirma identidade S0, existência dos eventos/recibos, vínculo de pessoa/lead, origem das versões ou integridade criptográfica. Todos os dados de entrada podem ser forjados. O domínio `policy` não entra no vetor A33; política, revogação de permissão e janela continuam sujeitas aos próprios validadores S0. Não há banco, WhatsApp, API OpenAI, Meta, deploy, migração ou alteração de front.

**G01–G07 permanecem abertos**, sobretudo G03 (proveniência) e G07 (jornada física integrada). Os únicos trabalhos aqui são de OpenAI F01/F02/F03 em branch experimental; o PR #1 permanece Draft.

## Próximo incremento indicado

Quando oportuno, acrescentar contratos candidatos explícitos para **mudanças autorizadas de versão entre F03 e F02 do mesmo episódio**, conciliando o evento S0 de atualização e revalidação da ficha. Não inventar evento S0 nem exigir trabalho da outra frente até localizar dependência concreta de edição.
