# Auditoria corretiva M19 — reconciliação de status e ocorrências WA-39 (offline)

**Data:** 01/11/2026. **Frente:** Meta/WhatsApp. **Escopo:** os dois módulos LAB M19, testes e contratos WA-39; *não* é autenticação de POST, endpoint Meta, porta de S0, reconciliação de produção ou autorização comercial. Responsáveis externos e dependências: [Issue #9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9), [Issue #2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) e [Issue #10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10).

## Parecer e correções

**AUD-M19-01 — perda de bytes conflitantes no snapshot do vínculo S0 (corrigido).** Em `wa19-status-reconciliation-offline.ts` a deduplicação usava apenas `occurrence_ref` como chave de mapa. O segundo evento de mesma referência e conteúdo divergente colocava o estado em quarentena, mas seu `body_sha256`, status, timestamp e erro **não entravam no hash**. Trocar a evidência conflitante por outra poderia preservar `snapshot_sha256`, `status` e contagens, fazendo o recheck aceitar como se fosse a mesma fotografia. A correção mantém em memória todas as variantes **distintas por conteúdo integral de campos**; repetições idênticas continuam contadas, e colisões de referência continuam em quarentena. O hash inclui **todas** as variantes, duplicações, estado e contexto, com ordem determinística. Flags `saw_*` também refletem as variantes em conflito, sem confirmação de status.

**AUD-M19-02 — efeito “primeiro vencedor” na conciliação Graph/callback (corrigido).** Em `wa19-status-evidence-reconciliation-offline.ts` uma colisão por posição física (`batch_ref/entry_index/change_index/item_index`) ou `occurrence_ref` descartava a variante posterior antes do cálculo. Permutar a chegada das mesmas variantes podia alterar a base da fotografia, as flags observadas ou o hash. Reorganizamos em duas etapas: deduplicar apenas tuplas **idênticas**, ordenar canonicamente as variantes e, depois, marcar colisões por posição/referência, incluindo **todas** as variantes na fotografia. O progresso conflitante permanece `CONFLICT`, `LAB_QUARANTINED_CONFLICT`, sem `sent` verificado. `unique_occurrences` neste laboratório representa o número de **variantes distintas**, não a quantidade de mensagens Meta confirmadas.

**AUD-M19-03 — mudança semântica sem contrato distinto (corrigido).** Como o significado de ambos os hashes mudou, os dois snapshots de **saída** passam a `wa19-status-snapshot.lab.v0.2` (ensaio binding S0) e `wa19-graph-status-snapshot.lab.v0.2` (ensaio Graph/callback). Os esquemas de entrada `wa19-status-request.lab.v0.1` e `wa19-graph-status-request.lab.v0.1` permanecem LAB; rechecks de candidatos de saída `v0.1` são negados. Os contratos continuam **independentes e não intercambiáveis**, sem ratificação S0/OpenAI.

**AUD-M19-04 — lacuna de identidade física não resolvida e explicitada.** O ensaio S0 possui `occurrence_ref` e `position_index`, mas **não** contém `batch_ref` nem posição completa de `entry/change/item`; portanto **não prova unicidade física global** nem pode determinar se duas referências diferentes apontam ao mesmo item do mesmo POST. O ensaio Graph possui campos físicos sintéticos, mas tampouco valida o POST original ou o ledger S0. Uma futura interface WA-39 ratificada deve resolver a identidade durável da ocorrência, HMAC, dedupe e vínculo S0; nenhuma das duas propostas pode conceder autoridade por dedução ou por coincidência de hash.

## Testes e validação

A partir da base verificada de **1.882/1.882 testes Meta offline**, com **115 testes M19** (57 do módulo S0 e 58 do Graph), foram adicionados:

- **10 testes `AUD-M19-S0-58..67`**: alteração de corpo/erro de evento já em conflito com as mesmas contagens; inversão de ordem; inclusão de terceira variante; replay; retenção de todas as flags e negativa de snapshot antigo.
- **10 testes `AUD-M19-GRAPH-59..68`**: alteração de variante conflitante; igualdade de hash com ordem invertida; colidir simultaneamente posição e `occurrence_ref`; diferenciação de erro; preservação do conflito; bloqueio de `v0.1`.

**Evidência funcional:** SHA `3311caaa91034e93da533ce7748370e239538ecb`, [GitHub Actions 41338646961](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41338646961): **1.902/1.902 testes Meta offline (135 M19 no total)**, scanner ACK estático aprovado e dois jobs `success`. As **18/18 verificações PG17** são históricas, executadas em job separado de **ingresso S0/Meta**: não autenticam a origem da M19, não executam Graph nem comprovam `sent`/entrega. Runs intermediários com `v0.1` nos testes tiveram falhas que foram corrigidas no SHA funcional; não são apresentados como aprovação.

## Decisões de segurança preservadas

- `sent_verified`, `delivered_verified`, `read_verified`, `definitive_failure_verified`, `attempt_correlation_verified`, `callback_hmac_verified`, `durable_persistence_verified`, `retry_external`, `ack_allowed`, `production_authorized`, `case_transition_authorized`, `commercial_transition_authorized`, `wdc13_increment_authorized`, `c09_window_authorized` ou equivalentes **permanecem false**.
- `API_ACCEPTED` não vira `sent`; `read`/`delivered` isolados não inventam o callback `sent`; `failed` e código `131049` não fazem contagem de falha definitiva ou desistência. Evidência contraditória permanece quarentenada, inclusive depois do recheck. Não há reenvio automático.
- Hashes são apenas resumos de **alegações locais** sem chave, sem MAC/assinatura e sem vinculação a fonte autenticada. A ordenação em memória não garante serialização durável nem protege ABA.
- S0/S1/Infra precisam fornecer recibo HMAC de POST original e de tentativa, vinculação tenant/App/WABA/número/`wamid`, identidade de ocorrência por lote físico, persistência/ordem/cursor/readback e projeção F02 ratificada. WDC-13/C09 permanecem **exclusivamente S0**. A autorização Graph real M18-D ainda é bloqueada.

**Parecer:** M19-A/B/C **auditados somente offline**. M19-D e marco principal **[ ]** até contrato interfrentes e prova E2E autenticada. Sem chamadas Meta reais, envio, SQL de produção, HTTP ACK, alteração S0, merge ou deploy.
