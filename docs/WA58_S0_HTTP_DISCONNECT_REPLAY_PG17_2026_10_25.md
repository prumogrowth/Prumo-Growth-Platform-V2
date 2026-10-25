# WA-58 — Queda de conexão, retransmissão e deduplicação PostgreSQL 17

**25/10/2026 — laboratório S0/Meta, execução local em loopback e PG17 descartável. Não aplicar a Supabase hospedado.**

## Definição da ambiguidade pós-gravação

Uma ligação HTTP pode se interromper **antes do arquivamento** (nenhuma evidência persistida) ou **depois do COMMIT no PostgreSQL** (evidência persistida, mas o cliente desconhece o resultado). A perda da resposta não é prova de falha da transação nem autoriza um novo envio comercial. No caso ambíguo, a retransmissão do mesmo evento deve usar os locks de evento WA39, HMAC/nonce WA48/51, outbox WA52 e ledger único S0/043, retornando `LAB_EXACT_BODY_REPLAY` internamente. A única resposta de sucesso da WA57 permanece `202 LAB_HTTP_FORENSIC_STORED_ONLY` **apenas no loopback**; não há ACK Meta real.

## Implementação

`supabase/tests/s0_wa_061_meta_http_loopback_transport.mjs`: após receber bytes completos com Content-Length correto e **antes** de chamar a ponte WA56, a WA58 verifica se a resposta HTTP já foi destruída ou encerrada; nesse caso, evita iniciar a operação forense. Uma vez iniciada a ponte, não pressupõe que a desconexão possa cancelar gravação em andamento. A única garantia de deduplicação é transacional no banco, não na memória do processo HTTP.

`supabase/tests/s0_wa_062_http_disconnect_replay_pg17.test.mjs`: 36 testes, com papéis, senhas, chaves e dados sintéticos. Primeira parte: requisições interrompidas com corpo incompleto (inclusive sem bytes e próximo do término), recuperação com requisição íntegra, transporte HTTP sem retry automático, indisponibilidade e retorno rejeitado, concorrência local com barreira, desconexão enquanto a ponte já está executando. Segunda parte: prova física HTTP→WA46→WA45/44→WA56→WA55, no mesmo banco PG17 após selagem WA55. A prova mede o ledger após:

- Corpo incompleto ou assinatura incorreta, sem chamada ao escritor.
- Falha **antes** do COMMIT, seguida de recuperação com exatamente uma observação forense.
- Falha de resposta **depois** do COMMIT; tentativa seguinte encontra `LAB_EXACT_BODY_REPLAY` e não insere nova observação.
- Cliente fecha o socket enquanto o escritor está suspenso por uma barreira; depois da liberação, o COMMIT ocorre e uma nova tentativa reconhece a observação.
- Quatro chamadas HTTP concorrentes para o mesmo evento: uma observação nova e três replays, com uma linha única no ledger.
- Corpo alternativo, mas mesma identidade lógica do evento: quarentena de variante e duas observações rastreáveis por hashes distintos (comportamento intencional, **não** duas cópias exatas).
- Revogação das permissões históricas e ausência de autorização comercial ou gravação na sombra WA48.

**Regressão anterior:** WA39–57 com 551 verificações. A WA58 adiciona 36; declarar **587/587** somente se todas as provas tiverem marcadores únicos e o CI no HEAD final terminar `SUCCESS`.

## Limitações

O teste HTTP utiliza somente `127.0.0.1` em porta efêmera e encerramento de socket; não é prova de falha de rede distribuída, reinicialização real de servidor ou cluster. A resposta HTTP 202 não é ACK da Meta. Chaves e identidades de serviço são fictícias. Não há webhook público, Graph, envio, retries comerciais, autorização de alterações na S1, Supabase hospedado nem merge. A S1 não precisa modificar nenhum contrato nesta etapa.

**Próxima WA-59 sugerida:** analisar exaustão de recursos e política de admissão sob múltiplas conexões lentas/disruptivas, com limites de concorrência de laboratório, antes de considerar identidade e implantação operacional.
