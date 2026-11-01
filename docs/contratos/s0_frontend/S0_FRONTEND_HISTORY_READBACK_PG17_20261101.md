# S0/S1 → Frontend: leitura de histórico e readback pós-COMMIT — PG17 LAB

**01/11/2026 · [Issue #14](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/14) · Status: CANDIDATO PARA REVISÃO FRONTEND / LAB_ONLY, sem aceite operacional.**

## Origem e escopo

A revisão consumidora do Frontend [6558813067](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/14#issuecomment-6558813067) apontou dois bloqueios concretos no contrato `prumo.s0.frontend.attention/0.1-lab`: (1) `active=false` não era consultável na fila do titular e não podia ser aberto para marcar leitura histórica; (2) `LAB_READ_RECORDED_BEFORE_COMMIT` não permite à UI afirmar confirmação sem COMMIT/readback independente. A S0 assumiu ambos na resposta [6559576977](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/14#issuecomment-6559576977).

A entrega cria porta aditiva `prumo.s0.frontend.history-readback/0.2-lab`, separada do contrato anterior, utilizando **as tabelas PG17 sintéticas já existentes**, sem migração de produção e sem alterar o contrato anterior. Branch `exp/s0s1-frontend-history-readback-pg17-20261101`, base S0/F01 comercial `b32d42bd4a204a2852e2ab21514436ee7e24e822`.

Pins imutáveis: Frontend original `ca262179e180c635fb7f44aaa37e4c1214f9ba12`, `frontend/visual/conversation-attention.mjs` e seus testes originais; ingresso técnico S0 `01ffdb093013664b73b18d23f92aac2202578210`. Só seis arquivos novos no escopo: `integration/s0s1_frontend_v02/pg17_service.py`, `test_pg17_service.py`, `emit_frontend_v02.py`, `test_frontend_interop.mjs`, workflow `.github/workflows/exp-s0s1-frontend-history-readback-pg17.yml` e este documento. CI verifica delta exato; nenhum original OpenAI/Meta/Frontend/Ingress/Supabase/main foi editado.

## Regra de histórico, titular e supervisor

`owner_history` retorna apenas casos `active=false OR actionable=false` da **mesma loja e titular atual**. Expõe `human_reply_pending=COUNT|DOT|NONE`, `unread_inbound_count`, revisões e `last_activity_at` somente quando fonte temporal sintética marcada `source_verified`; casos sem relógio confiável mantêm `UNKNOWN`, sem recência inventada. Todo resultado histórico tem `historical_read_only=true` e `composer_enabled=false`.

`open_owned` exige titular atual, loja, role `OWNER`, `assignment_revision/case_revision/inbox_revision`, `open_ref` idempotente. **Abertura pelo titular de caso histórico arquivado conta como leitura imediatamente na transação**, exatamente como ativo; não exige dwell, scroll ou composição. Supervisor retorna `LAB_SUPERVISORY_VIEW_NO_READ`, sem gravar cursor; outro titular, outra loja ou revisão obsoleta são negados. Reatribuição exclui o histórico do antigo titular e invalida sua tentativa/readback; o novo titular não herda seu direito de consulta.

## Separação de estágio, commit e readback

O resultado de `open_owned`, mesmo após INSERT bem-sucedido, é exclusivamente `LAB_OPEN_STAGED_BEFORE_COMMIT` (ou `LAB_OPEN_REPLAY_STAGED_NOT_COMMIT_PROOF`), com `read_confirmation_state=NOT_CONFIRMED` e `display_read_confirmed=false`. **Nunca é prova de commit, leitura confirmada nem autorização real.** A UI só pode considerar o resultado do `readback` independente **após** COMMIT da transação original.

`readback` em nova transação consulta `open_attempts` durável e case/owner/revisões; prova a existência da tentativa com `read_through_seq` original somente se loja/titular/atribuição/caso/cutoff persistidos correspondem, e cursor não está abaixo do cutoff. Se não houver linha, devolve `LAB_COMMIT_UNRESOLVED/UNKNOWN` (não presume rollback: pode haver atraso, transação ainda em andamento ou falha). Se titular ou versões de atribuição/caso mudaram, nega `STALE_OR_REASSIGNED` mesmo que o registro antigo exista. Um retry idêntico usa **o mesmo cutoff**, sem elevar cursor apesar de inbox posterior.

Se chegou um novo `INBOUND` visível após a tentativa, inclusive se outra abertura posterior já o leu, a prova antiga retorna `original_open_committed=true`, `newer_inbound_after_open=true`, `display_read_confirmed=false`, `read_confirmation_state=COMMITTED_OLD_CUTOFF_WITH_NEW_INBOUND_LAB`, e o contador/pendência é reconstituído **pelo cutoff original**. Para provar leitura da nova mensagem, é necessário **novo** `open_ref` e nova revisão `inbox_revision`. Assim, idempotência não vira leitura retroativa.

**Os métodos não realizam COMMIT por conta própria**; a aplicação chamadora é responsável por fechar a transação e por invocar readback em transação independente. A UI não deve desenhar um estado confirmado com base no retorno da primeira função.

## Prova física, controle de escopo e limitações

[CI funcional no SHA `f8d638b31ba1d3442274542c732deed0abb82c3a`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41323030576): `completed/success`, 2/2 jobs; **28/28 novos testes físicos PG17**, **8/8 testes de compatibilidade Frontend** (7 offline e 1 com arquivo temporário de PG17), **27/27 regressões originais de atenção/interação do Frontend** e **25/25 regressões físicas da S0 #14** = **88 casos distintos**, sem dupla contagem dos sete testes offline reexecutados no job físico. Testa ativo/histórico, COUNT→DOT, sem compositor, supervisor, escopo por loja, relógio UNKNOWN, rollback/commit incerto, readback após COMMIT, retry, novo inbound, leitura posterior independente, reatribuição, múltiplas aberturas concorrentes e corrida entre abertura/inbound. Arquivo de integração é gerado somente no runner e removido.

CI do commit final com este documento deve ser novamente aprovada e referenciada na Issue #14. Nenhuma prova operacional é inferida da CI.

**Limites fortes:** `actor_ref`, `allowed_stores`, role, `source_verified`, eventos e conexões de admin são apenas fixtures; não existe atestação hospedada de identidade S0, política real de ACL D3/D4, API HTTP, outbox, evento do ingresso Meta autenticado, assinatura de readback, confiança distribuída ou garantia de ordem entre serviços. A trava local só serializa eventos cujos escritores cooperem com o mesmo lock de caso. `display_read_confirmed=true` significa somente **observação durável no banco descartável**, não afirmação ao cliente final. A fila de histórico não deve ser lida como concessão geral de acesso: apenas titular atual da loja, na fixture.

## Pedido de aceite da frente Frontend

Revisar a porta `prumo.s0.frontend.history-readback/0.2-lab` e devolver **aceite técnico candidato ou incompatibilidades tipadas**: (a) histórico sem compositor e leitura imediata; (b) estágio `NOT_CONFIRMED` versus readback `COMMITTED_ORIGINAL_CUTOFF_LAB`; (c) `UNKNOWN` em commit incerto, timeout e retry; (d) reatribuição; (e) novo inbound após `open_ref` e readback restrito ao próprio cutoff; (f) recência `UNKNOWN` e minimização gerencial herdada. A integração visual na branch Frontend é responsabilidade da frente consumidora; nenhuma alteração foi feita nela.

**Próximas dependências S0/Infra:** readback autenticado no serviço hospedado e ACL, criação de eventos e locks reais com Meta #2; decisões de produção separadas. Não houve dados pessoais, credenciais, mensagens reais, merge, deploy ou publicação.
