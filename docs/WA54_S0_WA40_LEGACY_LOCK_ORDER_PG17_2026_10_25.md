# WA-54 — Auditoria e harmonização do handoff privilegiado WA40 (PG17)

**25/10/2026. Exclusivamente PostgreSQL 17 descartável `prumo_s0_test_ci`, PR #2 Draft.**

## Inversão documentada

WA40/045, mesmo após separar o verificador criptográfico WA41/046, chamava o validador de chave WA42 antes do arquivador WA39; só o arquivador travava registros S0 com `FOR SHARE OF a,m,b,o` e adquiria advisory lock WA39 por vínculo/evento. Rotas WA49–53 já serializam pelo evento antes da chave, e a WA52 também bloqueia primeiro a intenção na outbox. Essa divergência prejudicava a garantia de ordem global para execução paralela.

## Reparo experimental

`supabase/migrations/202610230053_s0_meta_wa40_lock_order_fixture.sql` faz **CREATE OR REPLACE** apenas do wrapper fictício `meta_arquivar_handoff_assinado_fixture_s0`, no PostgreSQL 17 local e pelo seu proprietário preexistente `postgres`. O wrapper:

- Preserva checagens de papel sintético `SET ROLE`, campos, contrato e flags comerciais falsas.
- Resolve todos os vínculos reais S0/041–042, com igualdade canônica de App/WABA/phone/canal/intent/attempt/correlation/recipient/wamid, usando `FOR SHARE OF a,m,b,o` antes de verificação de chave.
- Adquire o mesmo lock WA39 por vínculo/evento, **depois** chama o verificador WA41/042 (advisory key lock + HMAC SHA-256 + nonce).
- Chama o arquivador WA39 original, que reobtém locks já possuídos na transação e grava no ledger original. Falhas revertem nonce e arquivamento.

A rotina S0/043 original de arquivamento e os verificadores WA41/042 **não** foram alterados. É um reparo da ordenação em laboratório, não uma migração de produção, nem redução do owner privilegiado.

## Provas

`supabase/tests/s0_wa_058_assert_legacy_handoff_lock_order_pg17.py` incorpora **32 marcadores**: ACL, owner, SOURCE/WA39/key order, revisão da função WA39, HMAC/nonce, variante, replay, conflito, escopo negado sem gastar nonce, corrida WA40↔WA52, WA40↔WA50 com esperas por bloqueio real, independência de concessionárias, revogação e flags comerciais falsas. CI mantém as 407 provas anteriores; somar 32 apenas com CI `SUCCESS` no SHA exato.

## Bloqueios e dependências

Ainda não existe credencial M2M produtiva nem prova de validação de webhook Meta real, autorização S0↔S1, envio ou ACK. A WA40 continua `SECURITY DEFINER` pertencente a `postgres`, apenas em fixture offline. A WA50 não possui snapshot protegido por `FOR SHARE` e continua inadequada como rota de classificação sob cancelamento; a WA52 é a rota específica testada para isso. O uso de `SET ROLE` simulado e a permissão excepcional de bloqueio de linha em outros papéis não são contratos produtivos.

**Solicitação à S1 nesta WA-54: nenhuma.** Revisão dos contratos reais de cancelamento e credenciais exigirá coordenação antes de habilitar qualquer operação.

**Próxima etapa:** revisar o conjunto de rotas antigas e escolher um único caminho elegível para futura autenticação operacional; a convergência exigirá aprovação dos responsáveis S0/S1.
