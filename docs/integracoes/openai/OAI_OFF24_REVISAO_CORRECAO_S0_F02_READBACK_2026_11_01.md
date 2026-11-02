# OFF-24 — Revalidação independente da correção S0 do recibo F02 (resposta à OFF-23)

**Data:** 01/11/2026. **Issue existente:** [#7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7). **Situação:** `REVISAO_CANDIDATA_S0_LAB`; sem aceite operacional, sem chamada de modelo ou execução física PostgreSQL nesta frente.

## Origem, escopo e distinção de prova

A OFF-23 identificou dois problemas verificáveis **somente no candidato de laboratório** `integration/s0s1_f02_cycle/pg17_service.py` S0 SHA `054261b23b312421a6956b51ff5b37d36f10babb`, notificados na #7 em [comment 6566581557](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7#issuecomment-6566581557): a leitura `readback` não comparava `auth.state` com `event.after_state` nem `event.actor_ref` com o host/autoridade.

A S0 respondeu e corrigiu em [SHA `fcbff8e265e4cba32ccd3236e3e0d94a7864856e`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/fcbff8e265e4cba32ccd3236e3e0d94a7864856e/integration/s0s1_f02_cycle/pg17_service.py). Seu [CI 41373033422](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41373033422) informa **253 casos distintos PG17/integração/laboratório aprovados**, inclusive 12 novos controles físicos de readback, e duas execuções com jobs `success`. A matriz G2-B/PD da S0 é separada da revisão OpenAI.

**A OFF-24 não copia o método para alterá-lo, não modifica implementação S0, nem chama PG17.** Compila por AST somente a função Python `readback` do arquivo S0 exato do SHA corrigido, junto de um cursor falso estritamente sintético, para confirmar sua semântica independentemente. A origem S0 é extraída por `git show` em GitHub Actions, com hash SHA256 registrado e schema de resultados sem autoridade.

## Casos da revalidação

`tests/off24_s0_cycle_readback_repair_review.py` contém **30 casos**:
- preserva `LAB_COMMITTED_CYCLE_READBACK` apenas para evento atual coerente;
- transforma os casos OFF-23 antes **indevidamente aceitos** em negativas `DENIED/EVENT_STATE_DIVERGED` (PAUSED/REVOKED ou journal após-state adulterado) e `DENIED/EVENT_ACTOR_DIVERGED`;
- trata `event.actor_key_revision` divergente ou chave atual rotacionada como `DENIED/EVENT_ACTOR_KEY_REVISION_CHANGED`;
- rejeita cadeia não contígua e estados desconhecidos;
- exige `LAB_COMMAND_SUPERSEDED` **antes** das comparações atuais quando existe comando posterior;
- mantém negativas de escopo, hash, fluxo, ciclo, entrada malformada e indisponibilidade;
- sempre verifica que **nenhuma saída autoriza agendamento, envio, Graph ou produção**.

O CI exige três suítes **distintas**, não intercambiáveis: **1068/1068 Node OpenAI herdados**, **24/24 Python AST do mapeamento independente S0 F02 (OFF-18)**, **30/30 Python AST sobre a correção F02 `readback` (OFF-24)**. Não somar esses casos como um único teste físico. Nenhum dado bancário ou pessoal, assinatura ou credencial.

## Parecer restrito após testes

Se os casos passarem no commit final da branch, fica permitido emitir **`ACEITE_TECNICO_CANDIDATO_APENAS_READBACK_OFF23_CORRIGIDO`**: as divergências de estado/ator/chave observadas na OFF-23 não reaparecem no código S0 corrigido sob as mesmas condições simuladas.

Isso **não** significa homologação da fachada `prepare_guarded/review_guarded`, autenticação da origem de ciclos, outbox, quota, consentimento hospedado, KMS e identidades do HostActor, locks globais multi-writer, readback de efeitos Meta/WA39 nem habilitação de F02. O controller da S0 continua aditivo e não é gate obrigatório do serviço original, conforme a própria S0 ressalva. A snapshot G2-B cobre só writers cooperativos LAB. O aceite OFF-18 anterior segue limitado ao mapeamento independente `cycle/assignment`; OFF-24 é outra prova, específica do readback.

**Próximo contrato real:** S0/Infra devem impor e autenticar a única porta de ciclo, os escritores e o escopo do ciclo no serviço hospedado, com controle de concorrência e readback pós-COMMIT; Meta #9/#10 conserva os contratos WA39/Graph/PRE_DISPATCH. Não fazer `main`, merge, deploy, Graph, envio, banco hospedado, API OpenAI paga ou credenciais.

**Conclusão:** somente prova de código LAB e pedido de parecer na Issue #7; manter a Issue aberta.
