# Auditoria corretiva M14 — consentimentos, supressões e recheck offline

**Data:** 31/10/2026. **Responsável:** frente WhatsApp/Meta. **Escopo:** `integrations/whatsapp-meta/wa14-purpose-consent-preflight.ts` e suíte própria; comparação com WA25/WA26, M13 e limites das Issues #10/#8/#7. **Nenhum contrato S0 real ou integração física foi aceito.**

## Parecer técnico

**AUD-M14-01 — deriva silenciosa de ledger com revisões iguais: falha corrigida.** A versão inicial de `recheckWa14ConsentOffline` comparava requisição, `observed_at_ms`, revisões globais `policy/consent/suppression/grant_revision` e a elegibilidade da finalidade atual. Um ledger com consentimento `MARKETING` alterado enquanto a seleção corrente requeria `SERVICE` poderia produzir `LAB_RECHECKED_UNVERIFIED` mesmo sem incremento de revisões. Da mesma forma, supressão de outra finalidade poderia mudar, ou grants extras aparecer/desaparecer, sem serem detectados. Isso não é autorização de envio, mas enfraquecia a afirmação de que o recheck compara a mesma fotografia de políticas.

**Correção Meta:** após as duas leituras injetadas serem validadas estruturalmente, a nova `stableLedgerState` serializa em memória a projeção de todo o ledger relevante (identidade de loja/WABA/lead/caso, revisões, autorização de caso/audiência, elegibilidade de campanha e **todos** os consentimentos, supressões e grants). As listas são ordenadas por sua serialização canônica, de forma que permutar a ordem não representa mudança de política. O campo `observed_at_ms` é intencionalmente ignorado nessa comparação, mas é ainda validado quanto a monotonicidade/freshness. O resultado **positivo** só é admitido se essa projeção permanecer idêntica; alteração de conteúdo sem versão incrementada devolve `DENIED / REVISION_OR_CONTEXT_CHANGED`. O digest/texto privado não é exposto na saída. Negativas explícitas como `CONSENT_DENIED`, `SUPPRESSED`, `GRANT_DENIED` e `CASE_OR_AUDIENCE_DENIED` permanecem priorizadas para revogação da seleção atual.

Essa comparação é **apenas prova de consistência entre fixtures**, sem assinatura, autenticação de fonte, readback independente, persistência, sincronização entre tabelas, intervalo serializável, evento externo, lock ou proteção contra mudança ABA ou posterior ao recheck. A S0 permanece responsável por usar uma revisão monotônica genuína e, principalmente, uma decisão transacional `PRE_DISPATCH` junto à reserva da tentativa de envio.

## Regressões

- `M14-01..50` — cobertura anterior preservada.
- `AUD-M14-51..66` — **16 novas regressões**: alteração de consentimento de outra finalidade com mesma revisão, ativação de opt-out de outra finalidade, adição/remoção e revogação de grant alheio, mudança de prazo de consentimento e de revisão individual, inserção de supressão, permissões de audiência, ordenação inócua de listas, preservação de razões de denegação explícitas e ausência de dados pessoais na resposta.
- A suíte Meta deve aumentar de **1.497 para 1.513** casos offline, com **66 M14 específicos**. Registrar SHA e CI exatos confirmados após execução. Os testes PG17 históricos são uma prova **separada do ingresso S0↔Meta**, não exercitam este ledger M14.

## Limites e dependências irredutíveis

1. O ledger `wa14-s0-ledger.lab.v0.1` é alegação recebida: pode omitir revogações, eventos atrasados ou registros de outras lojas. A ausência de uma linha em `suppressions` só representa ausência de supressão **na fixture**, não uma prova operacional de opt-in.
2. Um campo `state: 'GRANTED'` sem origem de consentimento comprovada não legitima contato. A categoria Meta `UTILITY`/`MARKETING` e o status `APPROVED` do template também não substituem o consentimento por finalidade.
3. Rechecks sucessivos são inúteis como autorização se ambos consultarem um cache não autenticado. A validade real exige fonte S0, M2M, RLS, trilha de eventos, versionamento monotônico, concorrência/ABA protegida, reserva/recibo/readback e política de timeout.
4. Nenhum desses controles é conectado automaticamente à WA26, M13, F02 ou Graph; o contrato entre frentes segue aberto nas [#10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10), [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8) e [#7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7). Os laboratórios recentes M09-01..04 da S0 não significam aceite desse contrato PRE_DISPATCH.

**Status:** M14-A/B/C continuam `[x]` **somente no laboratório**, agora com auditoria corretiva; **M14-D e marco M14 principal `[ ]`**. Todas as flags `send_authorized`, `production_authorized`, `consent_verified`, `s0_source_authenticated`, `graph_dispatch_authorized`, `ack_allowed` permanecem `false`. Sem merge, deploy, Graph, SQL, HTTP ACK, envio real ou efeito comercial.
