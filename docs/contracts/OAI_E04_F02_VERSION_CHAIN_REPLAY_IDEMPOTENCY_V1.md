# E04 A36 — Rastreabilidade e idempotência candidata de cadeias F03→F02

**28/10/2026.** Referência: F02 A35 `99be210`, CI #40669035426 SUCCESS, 1.308/1.308. A36 não altera S0, não repete auditoria e não implanta serviços.

## Implementação efetiva

`backend/f02_version_chain_replay_candidate.py` adiciona `classify_version_chain_replay_candidate(..., prior_observations=())`. O procedimento reutiliza **primeiro** a validação integral A35: controlador não linear, vínculo F02, quatro provas alegadas, todos os validadores JS S2 originais executados por Node, episódios humanos e cadeia de alterações de versão.

Somente após esses gates positivos, ele cria um identificador determinístico **de laboratório** baseado na serialização canônica JSON e SHA-256 do pedido alegado: contexto de loja/lead/caso/rota, todos os eventos e instantes normalizados para UTC, episódios de fechamento, atualizações de versão, declarações de evidência e proposta F02, janela de revisão, entradas S2 e identificador sintético da pessoa.

`ReplayObservation` contém somente IDs, digest do pedido, digest por alteração pertencente ao **último** episódio humano, versão do esquema, chave de idempotência e canal. Um evento de episódio humano anterior pode reaparecer legitimamente no histórico de uma nova etapa; por isso, seus IDs não entram na comparação de reutilização de eventos do episódio mais recente.

Contra observações anteriores **fornecidas explicitamente pelo chamador**, o classificador devolve:

- `NEW_CHAIN_CANDIDATE_ONLY`: pacote coerente sem colisão estrutural detectada **nesse histórico parcial**; não executa nenhuma ação.
- `IDENTICAL_REPLAY_NO_NEW_ACTION`: repetição idêntica de um mesmo pedido; não reabre, reenvia ou agenda nada.
- `REQUEST_CONFLICT_RECHECK_REQUIRED`: mesmo pedido/identidade com conteúdo diferente, inclusive versão ou proposta S2.
- `EVENT_ID_REUSE_RECHECK_REQUIRED`: evento de atualização reutilizado sob outra identidade de pedido.
- `IDEMPOTENCY_KEY_RECHECK_REQUIRED`: mesma chave de idempotência dentro da concessionária e canal, para pedido diferente.
- `PRIOR_OBSERVATIONS_RECHECK_REQUIRED`: registros de histórico contraditórios, malformados ou fingindo autoridade.
- `ROUTE_OR_VERSION_RECHECK_REQUIRED` / `DENIED_MALFORMED`: gate A35 não passou ou entrada inadequada.

O snapshot tem limite de 256 KiB e o histórico de laboratório aceita até 64 observações. São limites técnicos contra entradas exageradas, **não políticas comerciais**.

## Limites essenciais

**Isto não implementa idempotência operacional real.** A função é pura, sem armazenamento transacional, bloqueio de concorrência, assinatura, MAC ou consulta às fontes S0; se o chamador não fornecer histórico, a repetição não será reconhecida. Um histórico falso pode gerar falso positivo ou falso negativo. O SHA-256 comprova somente igualdade de bytes canônicos alegados, **não** que fatos ou usuários sejam reais. O identificador e os digests não devem ser usados como recibos autorizativos, consentimento, comprovação Meta, permissão humana ou instrução de envio. O próprio retorno não contém qualquer botão/ação/sinal de envio.

A verificação de chave é escopada à **concessionária + canal**, não assume unicidade global entre concessionárias. O mesmo `idempotency_key` sob outro canal/loja não é automaticamente conflito. Esse escopo é experimental, não uma ratificação de regra S0.

Para idempotência física futura seriam necessários armazenamento atômico, constraint de unicidade da S0, reconciliação de eventos reais e avaliação de concorrência/distribuição e retry. Nada disso é alegado aqui e mudanças nessas fontes só devem ser efetuadas pelo responsável S0.

## Aceitação e segurança

`backend/tests/test_f02_version_chain_replay_candidate.py` acrescenta 30 testes com repetições idênticas, normalização de instantes UTC equivalentes, divergência de snapshots com a mesma identidade, reuso de IDs de evento, conflito de chave, fonte histórica malformada, ausência de checkout JS S2, duas fases humanas e verificação da ausência de autorização operacional. A suíte já existente permanece na execução manual de PostgreSQL 17 descartável e no CI.

G01–G07 não são homologados. Nenhuma mudança na S0, Supabase hospedado, Meta, cobrança, OpenAI API real, envio, agendamento, merge ou deploy. O PR #1 permanece Draft.
