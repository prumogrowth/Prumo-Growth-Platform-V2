# Entrega para coordenação Codex/S0 — contratos experimentais F02/F03

**Referência de 26/10/2026.** Nova responsabilidade: o Codex é o responsável principal pelo **núcleo oficial S0**. Este documento foi criado **somente na branch experimental** F02/F03; não modifica o núcleo nem delega aprovação ao autor do PR. Fonte legível por máquina: `docs/contracts/OAI_E04_F02_S0_CODEX_HANDOFF_V1.json`.

## Estado de corte (checkpoint real)

- Repositório: `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · Branch: `feat/oai-s0-f03-history-port-20261023` · Draft PR [#1](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/1) (base `feat/s0-cfi01-f03-auth-preflight-20261020`).
- HEAD de corte antes deste documento: `631d8eca3a5ba93c1d7ce40f1a9eb555071b7104`; PR Draft **não** fundido.
- Comparação GitHub da branch com sua base: **146 commits à frente, 0 atrás, 90 arquivos adicionados** (7 módulos F02, 15 módulos experimentais S0/F03, 17 arquivos Python de testes, 18 arquivos SQL em `supabase/tests/`, 31 docs anteriores, 1 runner e 1 workflow). Estes números são um inventário de candidatos, **não um pacote autorizado para merge indiscriminado**.
- Último CI verificado antes da nova orientação: [#40258297937 — SUCCESS](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40258297937) em `631d8eca`: **84 Python S0 + 514 Python F02/F03 (328 testes físicos PG17) + 269 Node pinned**. São **867 verificações em suítes distintas**, não 867 casos operacionais ponta a ponta nem homologação dos 70 SYN E02.

## Divisão de responsabilidades desde esta orientação

**F02 nesta branch:** mantém propostas tipadas, tratamento fail-closed dos resultados JS, pré-validação, intenção sintética do gestor, comprovantes locais C08, ledger de origem sintético, conciliação da cadeia cancelada e minuta não executável. Pode editar/testar esses adaptadores **isoladamente**, mas não incorporar seu comportamento ao núcleo oficial S0 nem tratar fixtures como decisões de produção.

**Codex/S0 oficial:** decide contratos de identidade/sessão S0, esquema/autoridade dos recibos, auditoria e integridade, autorização humana, versionamento transacional, migrações de produção, políticas S0, compatibilidade com C04/C08 e API operacional definitiva. Todo consumo dos módulos propostos da branch deve passar por coordenação e review do Codex.

**S1/Meta/S2 e outras frentes:** mantêm suas próprias branches e contratos; alterações cruzadas só depois de ratificação. A Issue #3 continua apenas auditoria inicial de otimização, não autoriza editar workflows de outras frentes. A S2 permanece fixada num SHA de referência do CI. Sem acesso a hosted Supabase, APIs Meta/OpenAI ou clientes reais.

## Inventário explícito de arquivos com dependência S0

### Propostas adaptadoras F02 (não são núcleo S0 oficial)

- `backend/s0_f02_posthuman_compatibility_local.py`
- `backend/s0_f02_posthuman_preview_local.py`
- `backend/s0_f02_posthuman_intent_local.py`
- `backend/s0_f02_legacy_cancellation_witness_local.py`
- `backend/s0_f02_legacy_observed_origin_local.py`
- `backend/s0_f02_posthuman_legacy_reconciliation_local.py`
- `backend/s0_f02_posthuman_draft_local.py`

### Propostas experimentais S0/F03 existentes no PR — exigem revisão Codex antes de incorporação

- `backend/s0_f03_bound_content_seal_local.py`
- `backend/s0_f03_content_integrity_local.py`
- `backend/s0_f03_crossfront_contract_local.py`
- `backend/s0_f03_crossfront_evidence_local.py`
- `backend/s0_f03_field_application_local.py`
- `backend/s0_f03_history_manifest_local.py`
- `backend/s0_f03_history_seal_local.py`
- `backend/s0_f03_identity_human_review_local.py`
- `backend/s0_f03_identity_ratification_local.py`
- `backend/s0_f03_identity_resolution_local.py`
- `backend/s0_f03_identity_resolution_verify_local.py`
- `backend/s0_f03_identity_uniqueness_local.py`
- `backend/s0_f03_media_attestation_local.py`
- `backend/s0_f03_operational_contracts_local.py`
- `backend/s0_f03_version_reservation_local.py`

### SQL privado somente de laboratório — NÃO tratar como migrações de produção

- `supabase/tests/s0_f02_posthuman_template_policy_local_only.sql`
- `supabase/tests/s0_f02_posthuman_intent_local_only.sql`
- `supabase/tests/s0_f02_legacy_cancel_witness_local_only.sql`
- `supabase/tests/s0_f02_c04_origin_ledger_local_only.sql`
- `supabase/tests/s0_f02_posthuman_draft_local_only.sql`

Além disso, existem outras fixtures `supabase/tests/s0_f03_*`, testes Python e o runner `scripts/run-s0-f03-pg17-local.sh`. A branch **já continha** o workflow próprio `.github/workflows/s0-f03-pg17.yml` (não criado/alterado por esta atualização); a sua existência **não** concede autorização para otimização de workflows da S1 ou integração no S0 oficial.

## Interfaces que precisam de coordenação

1. **S0 authenticated identity/session, immutable F03 signed close and snapshot.** Origem: `backend/identity_boundary.py; backend/s0_cfi01_f03_receipt_bridge_local.py; backend/s0_human_closure_event_local.py`. Ratificação exigida: Codex S0 validation of physical source authority, HMAC key custody, session lifetime, immutable history cutoff.
2. **S1 active team, gestor role, concessionaria scope.** Origem: `auth.sessions; public.equipe_prumo_s1; public.vinculos_papel_escopo`. Ratificação exigida: S0/S1 coordinated validation and production permission model.
3. **C04 synthetic eligibility and C08 local cancellation.** Origem: `public.planos_recontato_sinteticos; public.envios_template_sinteticos; public.eventos_envio_template_sinteticos; prumo_private.cancelar_recontatos_sinteticos`. Ratificação exigida: S0 owner approves event provenance, atomicity and no bypass; transport proof separate.
4. **S2 F02/F03 proposal shape.** Origem: `pinned S2 commit ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c`. Ratificação exigida: versioned adapter handshake; JS never owns identity, template approval, real scheduling or send.
5. **Template policy/consent.** Origem: `public.catalogo_templates_sinteticos; prumo_private.cfi01_f02_posthuman_template_policy_local`. Ratificação exigida: Meta category, approved template, scoped opt-out and real lawful basis verified separately.
6. **Operational plan & dispatch.** Origem: `future independent posthuman scheduler/transport not implemented`. Ratificação exigida: Explicit S0/S1 approval, retry/idempotence, business windows, authorization, runtime logs before implementation.

## Estados seguros e incompatibilidades intencionais

- `LOCAL_LEGACY_EVIDENCE_REVIEW_ONLY`: comprova somente consistência **local sintética** de plano e tentativa C04 observados antes do handoff e cancelados fisicamente por C08 após o caso. **Não** comprova que Meta cancelou mensagens já reservadas.
- `RESERVED_EXTERNAL_UNKNOWN`/`EXTERNAL_DISPATCH_UNKNOWN`: exige evidência independente do provedor, sem conversão booleana de JS para permissão.
- `DRAFT_RECORDED_REVIEW_ONLY`: minuta privada sem fila, sem escrita de plano C04 e sem envio. Exige que não exista plano antigo detectável; **continua bloqueada mesmo após conciliação C08**.
- `LOCAL_OBSERVED_ORIGIN_REVIEW_ONLY`: resultado de ledger PG17, não WORM contra superusuário, sem backfill de fatos anteriores à instalação e sem confiança real em horário de transporte externo.
- As linhas de teste e as políticas temporais experimentais (24h–7d) não são políticas comerciais aprovadas.

## Protocolo de incorporação proposto para Codex

1. Inventariar diferenças em relação ao HEAD da S0 oficial **no momento da futura integração**; esta lista não substitui o estado persistido mais recente. Conferir se outras conversas/branches alteraram contratos equivalentes.
2. Aceitar/rejeitar individualmente as interfaces de F02 e os contratos F03; evitar cherry-pick amplo dos 146 commits, que trazem laboratório, documentos, workflow e SQL local que não pertencem à migração.
3. Com o Codex, definir uma API de capacidades S0 versionada com estados *review-only* sem poder de agendamento; escopo da concessão sempre tenant/lead/caso/template; falhar fechado em versões divergentes, opt-out e provas ausentes.
4. Definir contratos de autorização humana reais, políticas Meta/consentimento, provas de cancelamento remoto, idempotência e trilha de auditoria. Não converter aprovações sintéticas em autorização real.
5. Testar interfaces separadamente e depois numa **branch de integração própria** aprovada. Executar os oráculos E02 originais e validações multi-frente antes de qualquer merge à main; Supabase hospedado apenas em fase posterior expressamente autorizada.

**Status:** inventário técnico para coordenação, **não aprovação**; nenhuma ação real sobre S0 oficial ou outras frentes foi executada nesta atualização.
