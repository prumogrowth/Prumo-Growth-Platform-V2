# E04 — F01/F02/F03: cadeia de mudanças de versão entre F03 e F02 (A35)

**28/10/2026.** Ponto de partida: `9bb50d0`, CI #40667099541 SUCCESS (1.275 testes). Incremento da frente OpenAI sem alteração S0, implantação ou chamada a modelos reais.

## Incremento

O A34 aceitava uma única alegação `S0_VERSION_UPDATE_CLAIM` por episódio entre a F03 e o pedido de recontato F02. O A35 estende o mesmo validador `backend/f02_multihuman_epoch_candidate.py` para **cadeias ordenadas de revisões**, com este formato de exemplo:

`F03 (v1) → atualização alegada v1→v2 → atualização alegada v2→v3 → F02 (v3)`.

Cada `VersionTransitionClaim` precisa estar na mesma ordem exata do evento `S0_VERSION_UPDATE_CLAIM` correspondente no ledger da rota. Cada etapa reivindica uma identidade de evento distinta, concessionária, lead, caso, encerramento humano, visita F03 e pedido F02 compatíveis. A versão de origem do primeiro passo deve coincidir com a captura F03; a origem de cada passo seguinte deve coincidir **exatamente** com o destino anterior. A F02 deve usar o destino da última etapa, com `expected` e `current` verificáveis pelo **validador original da S2** já conectado ao controlador.

A sequência rejeita ausência de evento ou alegação, duplicatas, permuta de passos, origem trocada, versões regressivas ou sem mudança, mudança de escopo/encerramento e revisão registrada fora da fase F03. O resultado final de um episódio continua sendo comparado com a versão inicial do episódio humano seguinte, sem impor incremento artificial no fechamento.

**Preservação de compatibilidade:** continuam válidas as rotas sem revisão e com revisão única do A34. Há limite **exclusivamente técnico de laboratório** de 16 etapas por episódio para evitar sequências sintéticas exageradas; esse número **não é parâmetro de negócio nem decisão aprovada pela S0**.

## Proteções mantidas

`S0_VERSION_UPDATE_CLAIM` e `E04_UNVERIFIED_S0_VERSION_CLAIM_ONLY` identificam alegações não autenticadas. O código não cria ou verifica uma assinatura da S0, não prova que a atualização aconteceu, não aplica revisão na ficha, não libera permissão humana, não cancela Meta, não marca envio nem devolve a conversa à F01 automaticamente. O sucesso `MULTI_HUMAN_EPOCH_SHAPE_RECHECK_ONLY` significa somente coerência de formato, sequência e snapshots **fornecidos pelo chamador**, que podem ser falsos.

A integração depende dos validadores S2 JavaScript originais fixados em `ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c` via Node, além dos verificadores Python da F02. O projeto mantém sua arquitetura-alvo Supabase backend e API OpenAI direta, n8n opcional, sem hospedagem/deploy nesta etapa. Os bloqueios G01–G07 continuam não homologados. O PR #1 segue Draft.

## Cobertura

`backend/tests/test_f02_version_chain_candidate.py`: 33 testes adicionais com casos positivos de dois e três passos, duas revisões em dois encerramentos humanos diferentes, limite 16/17, replays, interrupções, origem e destino não coincidentes, F02 com versão errada, timestamps fora de ordem, troca de locatário, condições de desistência na F03 e inexistência do checkout fixado S2. O runner de PostgreSQL 17 descartável executa também essa suíte.

**Próxima dependência real:** eventual ligação a uma origem S0 autenticada para cada alteração, com ordenação transacional e política aprovada, pertence à fase futura de integração e não é simulada como já concluída por este pacote.
