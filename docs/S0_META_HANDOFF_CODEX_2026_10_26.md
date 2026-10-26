# Handoff técnico ao Codex — S0/Meta forense (WA39–WA68)

**Proprietário da integração ao núcleo oficial: Codex/S0.** Origem: PR #2 experimental `feat/wa39-s0-meta-forensic-bridge-20261023` contra `feat/s0-fundacao-prumo`. Snapshot de código certificado: `cb4b27f2ec3ea77c0f8305c3c87387bddc5c7d6d`; CI [#40297190899](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40297190899), **823/823** no laboratório.

## 1. Objetivo da proposta

Oferecer evidência forense **não comercial** de callbacks de status WhatsApp/Meta, assinada sobre bytes brutos e vinculada à intenção/tentativa da S0 por registros técnicos locais. O laboratório **não** implementa webhook Meta de produção, autenticação IAM/M2M real, Graph API, envio, ACK público, controle de cobrança, entrega confirmada nem decisão comercial.

## 2. Contratos de interface a preservar/reconciliar

| Superfície | Contrato de laboratório | Fonte/código | Decisão que cabe ao Codex |
|---|---|---|---|
| Schema/base S0 | Reutiliza outbox `outbox_intencoes_s0` e registros Meta fixture 040–042; tenant/canal/tentativa/vínculo precisam corresponder | `supabase/migrations/202610230043_...sql`, S0-041/042 | Checar schema real e ownership; não duplicar tenant/canal |
| Ingestão/status | HMAC sobre bytes brutos precede ticket; evento SHA-256 de `[waba,phone,wamid,recipient,status,timestamp]`; hash do corpo bruto distinto | `s0_wa_050_meta_raw_hmac_gate.mjs`, `s0_wa_060_meta_raw_to_pg17_bridge.mjs` | Revisar proveniência, formato/política do evento, múltiplas instâncias |
| Ticket/identidade | WA44/45 assinatura de candidato interno; chave, binding, nonce, registry de portas internas sintéticas, não fornecidas pelo evento | `s0_wa_048_meta_handoff_adapter.mjs`, `s0_wa_049_meta_trusted_boundary.mjs` | Definir identidade de serviço real, KMS/secrets, TTL e revogação |
| Entrada única forense | `meta_wa55_single_entry_fixture_s0` delega a WA52 e sela EXECUTE legados **somente no fim da regressão** | `202610230054_...sql`, `s0_wa_059_assert_single_entry_sealed_pg17.py` | Projetar migração oficial idempotente, roles/RLS/ACL sem copiar a fixture |
| Concorrência | Ordem `outbox FOR SHARE → evento WA39 → chave WA48`; gravação + nonce atômicos; cancelamento não reabre estado | `202610230051–053_...sql`, WA52–54; WA60–66 testes | Validar com o contrato oficial de cancelamento/estado, lock order global e retries |
| HTTP | WA57 `127.0.0.1`/porta efêmera; 4 operações ativas; 262.144 bytes por body; resposta HTTP 202 apenas local de arquivo | `s0_wa_061_meta_http_loopback_transport.mjs`, WA57–68 testes | Definir gateway/webhook legítimo, ACK Meta e budgets multi-instância |
| JSON/Unicode | WA67 rejeita chaves duplicadas/alias por escape, BOM, surrogate órfão; WA68 cotas 48/2.048/4.096 | `s0_wa_072_strict_json_keys.mjs`, WA67/68 | Ratificar política Unicode e orçamentos CPU; não presumir compatibilidade Meta oficial |
| Resultados | `LAB_OBSERVED_UNVERIFIED`, `LAB_LATE_UNVERIFIED`, `LAB_EXACT_BODY_REPLAY`, `LAB_BODY_VARIANT_QUARANTINED`; flags comerciais sempre falsas | WA39/50/51/52/55; testes WA62–68 | Mapear estados reais, retenção/LGPD, monitoramento e critérios de triagem |

## 3. Dependências técnicas e riscos antes de incorporar

- **Não aplicar** nenhuma das 12 migrations de `supabase/migrations/202610230043–054_...sql` ao banco oficial sem redesenho e aprovação. Em particular **043–046 não validam explicitamente o nome do banco em seu DDL inicial** e **054 depende do estágio tardio da regressão**.
- Reproduzir a intenção dos testes (negação por ACL, locks, reversão de nonce, escopo, body raw), não transplantar `postgres`, usuário fictício `prumo_s0_meta_wa48_client_lab`, segredos sintéticos, tabelas de fixture ou `SECURITY DEFINER` sem análise de segurança oficial.
- Não inferir capacidade produtiva: limitações HTTP/sintaxe são cotas locais; teste WA68 não estabelece SLO de CPU/latência, disponibilidade, escalabilidade ou cobertura de rede real.
- Revisar fontes históricas: algumas primeiras docs WA39/42 contêm links ao repositório anterior `prumogrowth/Prumo-Growth---Platform`. O **repositório alvo deste handoff** é exclusivamente `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`.
- PR #2 ainda **Draft**, sem revisão formal registrada no snapshot de auditoria; 115 commits à frente da base, zero atrás, 84 arquivos alterados. Comparar novamente à base atual quando fizer integração.

## 4. Sequência sugerida ao Codex (sem execução automática)

1. Ler [auditoria de fechamento](./S0_META_AUDITORIA_DE_FECHAMENTO_2026_10_26.md), documentação WA39, WA42, WA55, WA67 e WA68, workflow e runner.
2. Comparar PR #2 com **HEAD atualizado** do núcleo oficial; fazer triagem de cada migration/role e dos contratos que se sobrepõem.
3. Escolher artefatos de teste reutilizáveis e adaptar interfaces necessárias em branch própria de integração; manter histórico da origem e reversibilidade.
4. Aprovar ou rejeitar explicitamente as decisões de política do parser e autenticação/segredos. Reexecutar regressão e testes de integração no SHA candidato e documentar resultados.
5. Só mediante autorização coordenada executar merge/deploy ou iniciar implementação de IAM, Meta Graph e webhook público. **Nenhuma autorização de envio/ACK/produção é inferida deste PR.**

## 5. Manifesto completo de arquivos alterados no PR #2 (snapshot cb4b27f2ec3e)

As contagens abaixo resultam de `list_pr_changed_filenames` no GitHub, referentes à comparação do PR #2. **O manifesto lista escopo de auditoria, não arquivos aprovados para cherry-pick.** Total: **84 arquivos**, sem contar este handoff e a auditoria criados posteriormente.

### Migracoes S0/Meta (fixtures; NAO publicar) — 12

- `supabase/migrations/202610230043_s0_meta_status_forense_fixture.sql`
- `supabase/migrations/202610230044_s0_meta_handoff_assinado_fixture.sql`
- `supabase/migrations/202610230045_s0_meta_isolar_verificador_fixture.sql`
- `supabase/migrations/202610230046_s0_meta_key_revocation_lock_fixture.sql`
- `supabase/migrations/202610230047_s0_meta_shadow_non_superuser_fixture.sql`
- `supabase/migrations/202610230048_s0_meta_scoped_non_superuser_fixture.sql`
- `supabase/migrations/202610230049_s0_meta_restricted_authoritative_forensic_fixture.sql`
- `supabase/migrations/202610230050_s0_meta_forensic_conflict_parity_fixture.sql`
- `supabase/migrations/202610230051_s0_meta_outbox_lock_cancel_race_fixture.sql`
- `supabase/migrations/202610230052_s0_meta_lock_order_repair_fixture.sql`
- `supabase/migrations/202610230053_s0_meta_wa40_lock_order_fixture.sql`
- `supabase/migrations/202610230054_s0_meta_single_entry_seal_fixture.sql`

### Modulos, utilitarios e testes de laboratorio — 40

- `supabase/tests/s0_wa_043_status_forense_fixture.sql`
- `supabase/tests/s0_wa_044_assert_meta_handoff_pg17.py`
- `supabase/tests/s0_wa_044_meta_handoff_setup.sql`
- `supabase/tests/s0_wa_045_meta_signer_privilegios.sql`
- `supabase/tests/s0_wa_046_assert_key_revocation_race_pg17.py`
- `supabase/tests/s0_wa_046_meta_revocation_contract.sql`
- `supabase/tests/s0_wa_047_assert_handoff_canonical_pg17.py`
- `supabase/tests/s0_wa_048_meta_handoff_adapter.mjs`
- `supabase/tests/s0_wa_048_meta_handoff_adapter.test.mjs`
- `supabase/tests/s0_wa_049_meta_trusted_boundary.mjs`
- `supabase/tests/s0_wa_049_meta_trusted_boundary.test.mjs`
- `supabase/tests/s0_wa_050_meta_raw_hmac_gate.mjs`
- `supabase/tests/s0_wa_050_meta_raw_hmac_gate.test.mjs`
- `supabase/tests/s0_wa_051_dual_wire_agreement.mjs`
- `supabase/tests/s0_wa_051_dual_wire_agreement.test.mjs`
- `supabase/tests/s0_wa_052_assert_non_superuser_pg17.py`
- `supabase/tests/s0_wa_053_assert_authoritative_scope_pg17.py`
- `supabase/tests/s0_wa_054_assert_restricted_forensic_pg17.py`
- `supabase/tests/s0_wa_055_assert_forensic_parity_pg17.py`
- `supabase/tests/s0_wa_056_assert_outbox_cancel_race_pg17.py`
- `supabase/tests/s0_wa_057_assert_lock_order_cross_routes_pg17.py`
- `supabase/tests/s0_wa_058_assert_legacy_handoff_lock_order_pg17.py`
- `supabase/tests/s0_wa_059_assert_single_entry_sealed_pg17.py`
- `supabase/tests/s0_wa_060_meta_raw_to_pg17_bridge.mjs`
- `supabase/tests/s0_wa_060_meta_raw_to_pg17_bridge.test.mjs`
- `supabase/tests/s0_wa_061_meta_http_loopback_transport.mjs`
- `supabase/tests/s0_wa_061_meta_http_loopback_transport.test.mjs`
- `supabase/tests/s0_wa_062_http_disconnect_replay_pg17.test.mjs`
- `supabase/tests/s0_wa_063_http_admission_limits_pg17.test.mjs`
- `supabase/tests/s0_wa_064_pg17_restart_worker.mjs`
- `supabase/tests/s0_wa_065_http_process_restart_pg17.test.mjs`
- `supabase/tests/s0_wa_066_forensic_revocation_restart_pg17.test.mjs`
- `supabase/tests/s0_wa_067_key_revoke_race_pg17.test.mjs`
- `supabase/tests/s0_wa_068_triple_race_pg17.test.mjs`
- `supabase/tests/s0_wa_069_dual_event_revocation_pg17.test.mjs`
- `supabase/tests/s0_wa_070_cross_key_variant_pg17.test.mjs`
- `supabase/tests/s0_wa_071_admission_canonical_pg17.test.mjs`
- `supabase/tests/s0_wa_072_strict_json_keys.mjs`
- `supabase/tests/s0_wa_073_json_ambiguity_pg17.test.mjs`
- `supabase/tests/s0_wa_074_guard_budget_pg17.test.mjs`

### Documentos de evolucao WA39-WA68 — 30

- `docs/WA39_S0_META_STATUS_FORENSE_2026_10_23.md`
- `docs/WA40_S0_META_HANDOFF_ASSINADO_OFFLINE_2026_10_23.md`
- `docs/WA41_S0_META_VERIFICADOR_ISOLADO_2026_10_23.md`
- `docs/WA42_S0_META_REVOGACAO_CHAVES_E_CONTRATO_INTERFRENTES_2026_10_23.md`
- `docs/WA43_S0_META_VETOR_CANONICO_INTEROPERABILIDADE_PG17_2026_10_24.md`
- `docs/WA44_S0_META_ADAPTADOR_JAVASCRIPT_PG17_2026_10_24.md`
- `docs/WA45_S0_META_FRONTEIRA_CONFIAVEL_OFFLINE_2026_10_24.md`
- `docs/WA46_S0_META_HMAC_BRUTO_FRONTEIRA_OFFLINE_2026_10_24.md`
- `docs/WA47_S0_META_DUPLA_ASSINATURA_COMPATIBILIDADE_OFFLINE_2026_10_24.md`
- `docs/WA48_S0_META_PRINCIPAL_MINIMO_SHADOW_PG17_2026_10_24.md`
- `docs/WA49_S0_ESCOPO_AUTORITATIVO_LEITURA_PRIVILEGIO_MINIMO_2026_10_24.md`
- `docs/WA50_S0_META_ESCRITOR_FORENSE_MINIMO_PG17_2026_10_24.md`
- `docs/WA51_S0_META_PARIDADE_CONFLITO_NONCE_PG17_2026_10_25.md`
- `docs/WA52_S0_META_OUTBOX_LOCK_CANCEL_RACE_PG17_2026_10_25.md`
- `docs/WA53_S0_META_LOCK_ORDER_CROSS_ROUTE_PG17_2026_10_25.md`
- `docs/WA54_S0_WA40_LEGACY_LOCK_ORDER_PG17_2026_10_25.md`
- `docs/WA55_S0_META_SINGLE_ENTRY_SEAL_PG17_2026_10_25.md`
- `docs/WA56_S0_META_RAW_TO_WA55_PG17_2026_10_25.md`
- `docs/WA57_S0_META_HTTP_LOOPBACK_PG17_2026_10_25.md`
- `docs/WA58_S0_HTTP_DISCONNECT_REPLAY_PG17_2026_10_25.md`
- `docs/WA59_S0_META_HTTP_RESOURCE_ADMISSION_PG17_2026_10_25.md`
- `docs/WA60_S0_META_PROCESS_RESTART_PG17_2026_10_25.md`
- `docs/WA61_S0_META_REVOCATION_RESTART_PG17_2026_10_25.md`
- `docs/WA62_S0_META_KEY_REVOKE_RACE_PG17_2026_10_25.md`
- `docs/WA63_S0_META_TRIPLE_RACE_PG17_2026_10_25.md`
- `docs/WA64_S0_META_DUAL_EVENT_REVOCATION_PG17_2026_10_25.md`
- `docs/WA65_S0_META_CROSS_KEY_VARIANTS_PG17_2026_10_25.md`
- `docs/WA66_S0_META_ADMISSION_CANONICAL_PG17_2026_10_25.md`
- `docs/WA67_S0_META_STRICT_JSON_UNICODE_PG17_2026_10_26.md`
- `docs/WA68_S0_META_JSON_BUDGET_HANDOFF_2026_10_26.md`

### Runner e workflow — 2

- `.github/workflows/wa39-s0-meta-offline.yml`
- `scripts/run-s0-local.sh`

## 6. Estado recomendado para fechamento da frente

**S0/Meta experimental: pacote pronto para avaliação do Codex; desenvolvimento novo congelado por padrão.** Solicitar nova execução apenas para lacuna/falha concreta, ou decisão de contrato que demande retrabalho. **Núcleo S0 oficial/S1/produção: não incorporados nem validados por este handoff.**
