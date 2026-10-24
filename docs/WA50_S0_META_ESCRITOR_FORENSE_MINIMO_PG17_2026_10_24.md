# WA-50 — Escrita forense S0 original com papel limitado (PG17 experimental)

**24/10/2026 · Somente PostgreSQL 17 descartável `prumo_s0_test_ci` · PR #2 Draft.**

## Implementação real de laboratório

A migration `202610230049_s0_meta_restricted_authoritative_forensic_fixture.sql` abre um caminho **alternativo, fechado** para registrar na tabela original `prumo_private.meta_status_forense_fixture_s0`, sem chamar a função arquivadora da WA39 pertencente a `postgres`. É uma implementação de ensaio apenas, e não substitui a WA39/WA40 nem ratifica qualquer credencial de Meta/Infra.

O novo `prumo_s0_meta_wa50_writer_lab` (NOLOGIN, NOSUPERUSER, NOBYPASSRLS) possui `SELECT` de colunas estritamente necessárias à resolução App/WABA/phone/canal/tenant/intent/attempt/recipient/wamid nas quatro tabelas S0 já existentes, além de `INSERT`/`SELECT` de colunas do ledger forense e de conflito. Não pode fazer `UPDATE` nem `DELETE` nesses objetos. A nova função é `SECURITY DEFINER` com `search_path` vazio e aceita somente a identidade TCP fictícia de laboratório `session_user=prumo_s0_meta_wa48_client_lab`. Reutiliza o HMAC/nonce/revogação WA48, no mesmo contexto transacional; usa o advisory lock WA39 de vínculo + evento antes da comparação forense original. Incidentes duplicados e variantes seguem o contrato WA39. **Exceção identificada:** a biblioteca WA48 rejeita tipos conflitantes para evento/corpo antes de a WA50 registrar o conflito no ledger de conflitos da S0; o teste exige rejeição sem escrita, e a recuperação desse registro permanece pendente. Nenhum estado comercial é alterado.

O gatilho existente `validar_meta_status_vinculo_fixture_s0()` executava como invocador e usa `FOR KEY SHARE`, que requer privilégio de bloqueio sobre vínculo. A migration altera o proprietário desse **gatilho compartilhado de laboratório** para `prumo_s0_meta_wa50_binding_guard_lab` (NOLOGIN e sem privilégios amplos), com `SECURITY DEFINER` e concessão excepcional de `UPDATE(id)` limitada à coluna usada no bloqueio. O escritor e o cliente não recebem esse privilégio. O gatilho de imutabilidade do vínculo permanece ativo; modificar IDs diretamente não é permitido. Essa separação é uma hipótese a ser validada com toda a regressão S0 antes de qualquer proposta de migração real.

**Atenção aos limites:** o escritor não utiliza `SELECT FOR SHARE` nas quatro tabelas S0 para evitar conceder `UPDATE` ao seu papel; logo a leitura do estado `CANCELADA` não está sincronizada com alterações simultâneas. O código registra observações não verificadas, sem autorizar envio/ACK/Graph ou mudança de caso. O gatilho compartilhado agora usa um definer mais restrito, mas essa alteração de laboratório precisa de auditoria de RLS/locks antes de ser integrada na S0. Os grants de leitura entre concessionárias existem somente no papel NOLOGIN de fixture e são restringidos pela igualdade da consulta. Sem ID real de principal IAM, sem webhook Meta real, sem S1 e sem Supabase hospedado.

## Provas

`supabase/tests/s0_wa_054_assert_restricted_forensic_pg17.py` verifica login, ACL de escritor e guard, append no ledger original, isolamento entre concessionárias, replay/variante/conflito, atomicidade de nonce, rollback, concorrência e revogação. É acrescentado às provas WA39–49 no CI; só contar o incremento como certificado quando o workflow PG17 do HEAD exato terminar `SUCCESS`.

**Próxima frente:** controle explícito de ordem de locks com S1/alterações de estado, isolamento de leitura por tenant dentro da sessão confiável, revisão do `SECURITY DEFINER` do trigger compartilhado e ligação a principal M2M autêntico. Não implantar fora do laboratório antes disso.
