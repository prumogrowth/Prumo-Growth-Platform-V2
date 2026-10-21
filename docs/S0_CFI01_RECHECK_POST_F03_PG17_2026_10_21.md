# S0 CFI-01 — rechecagem real do recibo de conclusão no PostgreSQL 17

**21/10/2026. Estado:** IMPLEMENTADO e TESTADO em PostgreSQL 17 descartável; **NÃO** é integração autenticada com GoTrue real, autorização de produção, aplicação de campos, conexão à IA F03 nem contrato homologado.

## Problema resolvido

O fluxo anterior registrava o fechamento humano em `prumo_private.cfi01_human_closure_events_local` mas **não tinha uma operação S0 posterior** para verificar que esse mesmo fechamento continua autorizado **após** a análise F03. Sem ela, uma resposta de modelo obtida antes da revogação de uma sessão, reatribuição do caso ou novo inbound poderia ser interpretada indevidamente como apta a persistir.

Implementado `backend/s0_human_closure_recheck_local.py` com `S0LocalClosureRecheck`, `RecheckRequest` e `recheck_human_closure_local`. O consumidor fornece referência de evento, caso, versão do ciclo e chave de idempotência que **o serviço S0 futuro precisa manter ligados à solicitação original**; nenhum deles se torna grant, credencial ou argumento do modelo. O operador é identificado apenas por `IdentityProvider.verify` (no CI, `Principal` sintético); não aceita `actor_id` ou `concessionaria_id` no request.

## Rechecagem física feita dentro de UMA transação

1. Revalida sessão em `auth.sessions` sob `FOR KEY SHARE`.
2. Trava equipe S1 e valida `ativo` **ANTES do caso**, respeitando ordem S1/S0; requer `S1TransactionAuthority.lock_team`.
3. Trava caso/ciclo/loja/atribuição humana atuais `FOR UPDATE`; checa versão `ciclos_comerciais.versao_registro` e estado comercial permitido.
4. Revalida concessão de loja e relação exata S1 operador+caso+atribuição na mesma transação.
5. Trava conversas `FOR UPDATE` e lê mensagens `FOR SHARE`; recalcula SHA-256 do mesmo recorte ordenado.
6. Lê o recibo por `evento_id + loja + caso` sob `FOR SHARE`; compara **ator, sessão, atribuição, versão, chave de idempotência, hash, última mensagem e quantidade**.

`DENIED`, `BLOCKED_S1`, `STALE`, `UNAVAILABLE` encerram sem liberar conteúdo. O retorno positivo é somente `VERIFIED_REVIEW_ONLY_LOCAL`, sem campos, snapshot, poderes de escrita, efeito comercial ou `APPLIED`. A função rejeita exceções operacionais e permissões ausentes de forma conservadora. A exceção S1 por caso sem concessão global permanece **fora deste contrato**.

## Evidências verificadas

**[Execução GitHub Actions #39581597781 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39581597781)**, branch `feat/s0-cfi01-f03-auth-preflight-20261020` no [PR #12 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/12):

- **113/113 testes unitários PASS** — 97 anteriores + 16 novos para entrada, isolamento do retorno, negação e falha segura.
- **26/26 testes físicos PostgreSQL 17 PASS** — 12 anteriores + 14 novos, inclusive recibo íntegro, falta de recibo, inbound/edição de mensagem, suspensão S1, revogação de sessão/grant, reatribuição, chave divergente, outra sessão, alteração de versão/status e **inbound concorrente com a rechecagem**.
- Fixture `auth.sessions` e `Principal` do CI são sintéticos; a migração S1 038 é referência exata copiada para teste (não foi mesclada na S0 de produção). A instância PostgreSQL 17 é física e isolada.
- Não há prova real de token JWT/GoTrue, HMAC/nonce/least privilege, schema de F03 completo, D3/D4, banco, Meta, perfil S1 excepcional ou aplicação de campos.
- As rotinas S0 de laboratório continuam com DSN local privilegiado por razões do teste; **não são executores que podem ser publicados num servidor de produção**.

## Próximos passos sem delegação

1. Implementar o transporte backend S0 autenticado e de privilégios mínimos para fechamento/rechecagem; vincular identidade verificada por GoTrue real a sessão + caso + atribuição; manter negativa após logout/transferência e auditar quem solicitou.
2. Conciliar `expected_cycle_version` que EXISTE na S0 com `expected_case_version` ainda proposto pelo Frontend/porta OpenAI (CFI-01), e ratificar o envelope técnico de `begin/recheck`.
3. Ligar o modelo ao **recorte minimizado** e autorizado das mensagens sem fornecer o snapshot S0 completo; validação OAI-05/OAI-07 do payload antes de qualquer operação com efeitos.
4. Implementar catálogo mestre e atualização de ficha somente por transação S0 idempotente, com recheck na mesma operação. Prova bancária continua exclusivamente do domínio bancário/S0, jamais da classificação F03.
5. Expandir testes de segurança/concorrência com as operações S1 reais e regressão histórica da F03; **não tratar 26 testes como homologação de produção**.

**Governança:** continuamos nos dois marcos combinados (conciliação contratual e substituição das autorizações fictícias). A pausa para dúvidas e auditoria documental geral acontecerá somente quando esses marcos estiverem efetivamente concluídos. Sem merge, deploy, dados reais de clientes, chamadas OpenAI/Meta/Banco ou Supabase hospedado.
