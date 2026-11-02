# G2 S0/S1 — Snapshot histórico consistente e manifesto de contratos Meta/OpenAI/Frontend

**Data:** 01/11/2026. **Status:** `LAB_ONLY / CANDIDATO_PARA_REVISAO`. **Issue principal:** [#10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10).

## Origem e objetivo

A [auditoria geral S0/S1](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/ca74079d78a9819e1c869cb597a7e43d9b4cb3b4/docs/auditorias/S0S1_AUDITORIA_GERAL_2026-11-01.md) identificou **AUD-ARQ-01** (múltiplas leituras `READ COMMITTED` sem uma fotografia consistente), versões potencialmente divergentes entre os contratos S0 v0.1/v0.2, M09 e Meta M18, e ausência de vínculo autenticado de tentativa. Os cinco achados concretos **AUD-PD-01..05** foram corrigidos anteriormente em `fb06741b16eee9f9709acaed412daf5ea73a6d19`, preservando toda a autorização `false`. Esta entrega G2 **não reabre** esses achados nem cria endpoint de envio.

**Base exata:** `fb06741b16eee9f9709acaed412daf5ea73a6d19`. **Branch de laboratório:** `exp/s0s1-g2-snapshot-contract-pg17-20261101`. **Pins de consumo:** Meta M18 `2a535ceb543418a76bb753a368eabc45bdbe4b0f` e ingresso original S0/M09 `01ffdb093013664b73b18d23f92aac2202578210`. Não foi alterado um único arquivo das frentes OpenAI, Meta, Frontend, Infra, Supabase ou do PRE_DISPATCH v0.2 anterior; somente arquivos aditivos do laboratório G2.

## 1. Novo contrato, tipado e não autoritativo

`prumo.s0.pre-dispatch.g2.snapshot/0.1-lab` é implementado em `integration/s0s1_pd_g2/snapshot.py`. A entrada `classify_historical_snapshot(connection,request,scope,principal,m09_versions)` exige conexão administrativa **nova e sem transação ativa**, PG17 descartável identificado pelo nome do banco, role e schema, e `M09_PG17_DISPOSABLE=YES`. Usa `BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY` e estabelece a fotografia MVCC com `pg_current_snapshot()` antes de chamar a função **pré-existente** `readback` v0.2 em **uma mesma transação**. Cada consulta subsequente de registro M09, caso, consentimento, supressão, template, campanha, grant e quota enxerga o **mesmo estado MVCC**. Ao terminar a observação, executa `ROLLBACK` intencional, já que é somente leitura.

O objeto de resposta contém o estado classificado **historicamente**, `transaction_isolation=REPEATABLE_READ_READ_ONLY`, `snapshot_consistent_during_read`, `snapshot_current_authority=false` e todos os flags de autenticação, lease, Graph, send, retry, produção e outbox `false`. Não devolve ID de mensagem, nonce de cliente, payload, segredos nem um `m18_dispatch_candidate`. Casos incorretos, erro do banco ou chamada dentro de transação já ativa falham fechados. O gancho `_lab_interleave` existe **somente para testes**; não confere autoria e não deve integrar qualquer API hospedada.

**Propriedade demonstrada, e somente ela:** a fotografia de múltiplas tabelas é internamente consistente em uma transação `REPEATABLE READ READ ONLY`. **Não há linearização com escritores reais:** outra transação pode revogar consentimento ou cancelar a reserva **depois da criação do snapshot e antes do resultado**. Uma resposta `LAB_HISTORICAL_SNAPSHOT_NO_DISPATCH` contendo internamente `LAB_COMMITTED_RECEIPT_NO_DISPATCH` pode portanto já estar superada. Uma nova consulta em transação separada verá a revogação. Esse resultado **não pode ser usado como autorização de publicação, nem mesmo imediatamente após retorno**. A fase G2 de consistência com **escritores hospedados, recheck de ponto de uso, lock/CAS, ordenação e outbox** permanece pendente e exige contrato cooperativo de Infra/Meta.

## 2. Manifesto de versões / contratos

Arquivo `integration/s0s1_pd_g2/contract_manifest.json`, versão `prumo.s0.pd.g2.contract-manifest/0.1-lab`:

- **M09:** cinco revisões independentes `route/app/binding/grant/principal` não podem ser colapsadas no escalar Meta `registry_revision`.
- **PRE_DISPATCH:** oito revisões de caso, atribuição, política, supressão, consentimento, template, campanha e grant devem permanecer distintas; `cycle_revision` F02 e `assignment_revision` não são intercambiáveis.
- **Identidades:** o identificador fictício `store-A` **não equivale** a um UUID de `concessionaria_id` validado pela Meta.
- **Conteúdo:** `body_sha256`/`destination_sha256` S0 não devem ser renomeados para `content_sha256`/`recipient_sha256` Meta sem contrato de canonização, semântica de payload e revisão de finalidade.
- **Versões Meta:** `prumo.s0.pre-dispatch.readback/0.2-lab` e `prumo.s0.pre-dispatch.g2.snapshot/0.1-lab` **não** são `prumo.s0.pre-dispatch.pg17/0.1-lab-only` nem `wa18-dispatch-intent.lab.v0.1`. O M18 original permanece intocado e não aceita esses novos tipos como lease.
- **Autoridades:** `m18_dispatch_candidate=null`, `may_issue_graph_lease=false`, `may_send_message=false`, `may_auto_retry_commit_unknown=false`. Não há `attested attempt/intent/selection`, fonte de consentimento real, principal M2M hospedado, rate budget operacional, token KMS nem reconciliação WA39.

O manifesto serve como **matriz de compatibilidade candidata** para revisão entre frentes, não substitui acordo explícito com Meta e OpenAI nem fonte hospedada de verdade.

## 3. Provas e limites da CI

O workflow `.github/workflows/exp-s0s1-g2-snapshot-pg17.yml` testa 14 casos físicos novos de snapshot, incluindo interleaving de revogação/alteração M09/cancelamento, readback depois de COMMIT, transação pré-ativa negada, fonte ausente, instrução `UPDATE` na mesma transação read-only negada, lock físico de recibo aguardado por `cancel`, e `COMMIT_UNKNOWN` sem retry. Também executa 10 casos de manifesto de versões, os 11 casos AUD-PD corrigidos, 27 regressões v0.2, 24 da v0.1, 18 M09 PG17, 34 de interoperabilidade com evidência física e 62 testes originais M18. **Total alvo: 200 casos distintos**; testes offline de interop são repetidos no job físico e não contam duas vezes. O reporte definitivo deve registrar a execução **no SHA final com este documento**, com skips separados. Todas as bases externas são pinadas e verificadas; evidência temporária em `/tmp` é removida após os testes.

## 4. Decisões restantes para fechar o G2 operacional

1. **S0/Infra:** acordar disciplina de escritores, `FOR UPDATE`/CAS sob o mesmo snapshot e fluxo de publicação, compatibilidade de isolamento `SERIALIZABLE`/timeout/deadlock e tratamento tipado de `UNKNOWN`; readback histórico não satisfaz autorização atual. Sem autenticação/ACL hosted o `HostScope` continua apenas fixture.
2. **Meta #10:** ratificar nova entrada M18-D vinculada a `attempt/intent/selection/nonce`, UUID de tenant, digest canônico, quota operacional, principal e validade, com prova pós-COMMIT consumível apenas dentro de uma janela/controlador de uso; preservar separação de `API_ACCEPTED`, `sent`, `delivered` e falha com WA39/#9.
3. **OpenAI F02 #7:** respeitar mapeamento cycle/assignment aceito como candidato, sem inferir agendamento ou autorização a partir de `LAB_HISTORICAL_SNAPSHOT_NO_DISPATCH`.
4. **Frontend #14:** não propagar confirmação histórica de envio como resposta humana publicada nem como evento de leitura atribuível ao titular; projeções de fila/histórico têm contrato e permissões distintos.
5. **Governança:** matriz de SHAs e critérios de merge/rebase deverão ser aprovados separadamente, dado o desvio da `main` documentado na auditoria.

**Decisão:** este incremento atende somente **G2-A: consistência de leitura histórica e matriz de versões em PG17**. **G2-B: coordenação efetiva com escritores/autorização continua ABERTO**. Não fechar Issue #10 nem liberar M18-D. Sem merge, deploy, Graph, credenciais reais, Supabase hospedado, dados pessoais ou mensagens.
