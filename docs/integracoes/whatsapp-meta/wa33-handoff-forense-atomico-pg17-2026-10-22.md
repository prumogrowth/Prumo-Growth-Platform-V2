# WA-33 — Handoff forense atômico em PostgreSQL 17 descartável

**22/10/2026 · [PR #2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2) · Laboratório estritamente fictício da frente WhatsApp/Meta.** Continua a cadeia [WA-31](./wa31-evidencia-tardia-pos-revogacao-forense-pg17-2026-10-22.md) e [WA-32](./wa32-webhook-assinado-escopo-s0-forense-offline-2026-10-22.md): WA32 demonstra verificação HMAC + *lookup/recheck* de tentativa apenas em portas simuladas, mas **não** fechava a corrida entre o último recheck e o COMMIT. WA33 propõe uma fronteira transacional **somente interna à fixture**, não um serviço produtivo S0.

## Resultado físico verificado

[GitHub Actions #39879135486](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39879135486), commit `50d229a131fdec4ed76a9e7411eb9895a8b0c644`: **3/3 jobs SUCCESS**; regressão **627/627 Node 22 PASS**; WA-33 **30/30 marcadores PASS** no PostgreSQL 17 real e descartável, incluindo **quatro disputas de bloqueio efetivamente observadas por `pg_blocking_pids`**. Os logs mostram os marcadores `WA33-01` a `WA33-30` uma vez cada. Regressões WA06D/WA15C/WA16/WA27–32 continuam aprovadas. As duas primeiras execuções de desenvolvimento tiveram erros de sintaxe SQL (regex e trecho duplicado), **corrigidos antes dessa execução verde**; não constituem evidência positiva.

## Implementação

- `integrations/whatsapp-meta/lab/wa33_pg17_atomic_forensic_handoff.sql` — **schema próprio `wa33_lab`, jamais migrável como parte da S0**. A tabela `bindings` conserva vínculos fictícios entre concessionária/caso/tentativa e App/WABA/número remetente/`wamid`/destinatário/revisão, com unicidade do identificador técnico por App/WABA/número. Nenhum vínculo foi extraído de Meta real; todos são valores sintéticos provisionados pelo dono da fixture.
- `append_fixture` — para registrar um único sinal técnico forense, procura o binding pelo escopo técnico, trava `wa29_lab.authority` com `FOR UPDATE`, relê o binding sob bloqueio e compara com o snapshot inicial, verifica destinatário e revisão, trava a claim existente e a chave do evento. Tudo isso acontece **na mesma transação PostgreSQL**. Permite arquivar um sinal **após uma revogação** com marca `after_invalidation=true`, mas nunca reativa claim nem reserva. A falta de claim ou mismatch de destinatário, App, WABA, remetente, `wamid` ou revisão nega o registro.
- `events` — chave `(shop,case,attempt,event_ref)` para replay exato `LAB_REPLAY_NO_RETRY` sem segundo append; o mesmo identificador com tipo conflitante grava **quarentena separada**, sem sobrescrever a primeira evidência. Constraints SQL exigem `send_authorized=false`, `production_authorized=false`, `ack_allowed=false` e `definitive_failure_count_increment=false`.
- `change_binding_fixture` — mutação fictícia de destinatário/revisão sob o **mesmo lock de autoridade**, exclusivamente para testar leituras desatualizadas; não representa gestão real de vínculos e não autentica seu invocador.
- `integrations/whatsapp-meta/lab/wa33-assert-atomic-handoff-pg17.py` — 30 verificações com sessões PostgreSQL independentes, incluindo evidências anteriores, duplicadas, conflitantes e posteriores à revogação, escopo errado, tentativa inexistente, revisão antiga, estado preservado e ausência de autorização. Recusa DSN que não seja o banco descartável local da CI.
- `.github/workflows/whatsapp-meta-offline.yml` — gate WA-33 após WA-32, comparando cada marcador individualmente e falhando se faltar ou duplicar.

### Quatro conflitos físicos demonstrados

1. **Revogação primeiro:** `revoke_fixture` mantém bloqueio da autoridade. A gravação forense aguarda; após COMMIT, arquiva **apenas como evidência tardia**. A claim e a reserva seguem canceladas.
2. **Gravação primeiro:** o append mantém bloqueio; a revogação aguarda. O registro anterior permanece histórico após COMMIT de revogação, sem alterar o estado autorizado.
3. **Duas gravações com mesma referência de evento:** a segunda aguarda a primeira e termina em replay idempotente, mantendo uma única linha.
4. **Troca de binding primeiro:** alteração de destinatário/revisão mantém bloqueio; a tentativa que leu o binding antigo espera e **é recusada**, sem registrar no escopo desatualizado. Um novo append com revisão/destinatário atualizados funciona apenas como evidência fictícia, sem direito de Graph.

## Limites explícitos e decisão pendente

**WA-33 ainda não fecha a cadeia criptografia Meta → S0 autenticada → commit real.** O banco sintético recebe argumentos textuais e resolve um binding **plantado pela fixture**, sem principal GoTrue/JWT, autorização S1, RLS/tenant real, credenciais, assinatura Meta validada dentro do banco, canal de ingressão autenticado, idempotência de HTTP ACK ou integração com outbox. A assinatura em WA-32 foi provada isoladamente, e **não existe prova de que o remetente dessa transação SQL é o processo que autenticou o HMAC**. Essa lacuna é bloqueadora para produção; combinar passes de laboratório não a elimina.

A ordenação demonstrada é **autoridade fictícia → binding fictício → claim fictícia → evento**. Ela **não homologa** a ordem de locks real [S1 equipe → S0 caso](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-cfi01-f03-auth-preflight-20261020/docs/S0_CFI01_S1_TRANSACAO_ORDEM_LOCKS_2026_10_21.md), não garante isolamento RLS real nem ausência de deadlocks interfrentes. Para futura implementação, S0/S1 precisam ratificar principal de serviço, escopo de concessão, protocolo de handoff autenticado, binding durável, estratégia de concorrência, transação forense, retenção/minimização LGPD e momento/condição de ACK. Os sinais `SENT_REPORTED`/`FAILED_REPORTED` aqui são **dados fabricados de teste**, não confirmação de envio, entrega nem falha definitiva WDC-13.

**Restrições respeitadas:** nenhuma chamada Graph, webhook hospedado, serviço de produção, segredo, envio, migração S0/S1, merge, deploy, alterações OpenAI/F02/F03/frontend. PR #2 segue **Draft**.
