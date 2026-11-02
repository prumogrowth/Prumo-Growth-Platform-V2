# Auditoria corretiva M21 — handoff humano, F01 e cutoff F03 (somente laboratório)

**Data:** 01/11/2026. **Frente:** WhatsApp/Meta. **Escopo:** código e regressões `wa21-human-handoff-f01-f03-offline.ts`; contrato WA-21, handoff F01 terminal, fechamento humano F03, fonte S0 simulada. **Não é** integração com S0/S1, autenticação do autor, envio Meta, acesso a histórico protegido ou operação da F03.

## Parecer

A M21 anterior preservava o bit `handoff_ever_definitive` e bloqueava a reabertura alegada da F01, mas tinha uma lacuna na candidatura F03: bastava a fixture do caso alegar `LAB_HUMAN_CLOSED` e um evento independente alegar `LAB_HUMAN_CLOSURE_EXPLICIT` com um identificador de autor e cutoff coerente **com o próprio evento**. Não havia qualquer `closure_ref`, `closure_actor_ref`, `closure_at_ms` ou `closure_cutoff_ms` no contexto S0 alegado para comparar. Portanto, um evento com referência/autor/horário arbitrários, desde que sintaticamente válidos, podia obter `LAB_F03_CUTOFF_CANDIDATE_UNVERIFIED`. O resultado já tinha **todas as flags de execução falsas**, mas a classificação era excessivamente permissiva para análise/consumo futuro.

### Achados e correções

**AUD-M21-01 — fechamento F03 não correlacionado ao contexto (corrigido).** A fixture `wa21-s0-case-state.lab.v0.2` de caso agora informa obrigatoriamente `closure_revision`, e o caso `LAB_HUMAN_CLOSED` precisa de `closure_ref`, `closure_actor_ref`, `closure_at_ms` e `closure_cutoff_ms` válidos. O evento explícito deve coincidir **exatamente** com a referência, o autor e o instante da conclusão no contexto, além de coincidir com o cutoff. Divergência retorna `DENIED/CLOSURE_CONTEXT_MISMATCH`. Um caso F01 ativo/em handoff não pode trazer campos de fechamento escondidos; retorna `CLOSURE_IN_WRONG_STATE`.

**AUD-M21-02 — causalidade e cutoff historicamente coerentes (corrigido).** Para o caso alegadamente fechado, o fechamento precisa acontecer entre `handoff_at_ms` e `observed_at_ms`, e o cutoff entre o handoff e o instante do fechamento. O código anterior exigia `closure_cutoff_ms === event_at_ms`; essa equivalência era uma hipótese rígida, e não um contrato S0 homologado. A auditoria permite um cutoff anterior à conclusão, se tanto o evento quanto o contexto concordarem e o corte estiver dentro da janela causal. Um cutoff posterior à conclusão, anterior ao handoff ou divergente da fotografia é recusado. O `cutoff_ref` real/manifesto congelado e a ordem global entre casos/mídias **continuam dependências da S0 (#5)**, não são produzidos por este timestamp sintético.

**AUD-M21-03 — versionamento de esquema e snapshots (corrigido).** Mudou o contrato **de entrada de contexto** para `wa21-s0-case-state.lab.v0.2` (novo vínculo de fechamento e revisão), mantendo o evento `wa21-case-event.lab.v0.1` porque sua forma não mudou. A saída/hash foi versionada como `wa21-human-handoff-snapshot.lab.v0.2` e usa domínio `WA21_HANDOFF_LAB_V0_2`. Contextos/snapshots v0.1 não são reinterpretados silenciosamente pelo recheck; esse resultado não é um contrato de operação S0.

### Testes adicionados

**20 casos AUD-M21-61..80**, em `integrations/whatsapp-meta/wa21-human-handoff-f01-f03-offline.test.ts`, cobrem fechamento com referência/ator/tempo/cutoff divergentes, campos de fechamento ausentes, causalidade futura/passada, fechamento alegado em F01/handoff, cutoff anterior coerente, invalidação de snapshot por revisão/autor, rejeição das versões v0.1, getter hostil e flags de execução F03/comércio permanentemente falsas.

**Evidência funcional:** SHA do código/testes `b84c5972a2705901433b91e885a01a28c5e3485f`, [CI 41370100369](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41370100369): **80/80 M21; 2.092/2.092 Meta offline** (2.012 baseline até M20 + 80 M21), **377/377 interface**, scanner ACK lexical aprovado. O job **PG17 de ingresso S0/Meta**, quando verde, verifica **18/18 casos históricos independentes**, não handoff F01/F03. A conclusão do CI/documentação final deve ser conferida no SHA exato.

### Invariantes de segurança preservadas

- O bit `handoff_ever_definitive` permanece uma **alegação de laboratório**, que não pode reabrir F01 no mesmo caso. Nenhum inbound, timeout da janela Meta, clique, template ou evento técnico retorna permissão `f01_invocation_authorized`.
- A candidatura `LAB_F03_CUTOFF_CANDIDATE_UNVERIFIED` **não** é `closure_verified`, invocação F03 ou manifest. Autor e cutoff são alegados sem autenticação S0. Um hash SHA-256 sem chave não é recibo transacional nem assinatura do ator.
- `source_authenticated`, `case_verified`, `closure_verified`, `f01_invocation_authorized`, `f03_invocation_authorized`, `human_dispatch_authorized`, `graph_dispatch_authorized`, `human_closure_apply_authorized`, `commercial_transition_authorized`, `c09_window_authorized`, `ack_allowed` e `production_authorized` permanecem **false** em todos os caminhos.
- Janela livre Meta por inbound, ato humano/cutoff F03 e relógio C09 de 24 horas após `sent` do template final confirmado são **três operações independentes**. Nenhuma é inferida das outras.

### Pendências M21-D

A **S0/S1** deve ratificar seu próprio esquema de fechamento/handoff, identidade/competência e atribuição humana, irreversibilidade por caso, autorização de comando, `closure_ref`/cutoff histórico durável, readback/CAS, concorrência/replay e isolamento de concessionária/caso. Os novos campos LAB são **proposta de vínculo para teste**, não exigência de renomear colunas canônicas. A **OpenAI F01** deve respeitar handoff terminal autorizado pela S0; **F03** apenas consome manifesto histórico completo/cutoff ratificado (#5) e devolve proposta a aplicar exclusivamente por S0 (#6). **Infra/Meta** aguardam origem HMAC e ingresso/ACK #2, atribuição/autoria M17 e limites de Graph/dispatch #10. Nenhum fluxo real foi acionado.

**Status:** M21-A/B/C **auditadas somente em laboratório**; **M21-D e marco principal [ ]**. Sem Graph, modelo, mensagem, credencial, banco hosted, envio, HTTP ACK, merge ou deploy.
