# S1-002/I20 — Prova HMAC e nonce do gateway privado (19/10/2026)

**Estado:** candidato em teste; não autorizado em produção e não constitui migração operacional. Branch `feat/s1-002-equipe-prumo`, PR #5 Draft. Não modificar as migrações efetivas nem o Supabase hospedado.

## Motivação

I19 confirmou em GoTrue real e PostgreSQL descartável que movimentar caso, pausar globalmente e reativar são operações viáveis por gateway privado e sem RPC `public`, mas deixou o risco de um **login SQL comprometido** injetar o próprio contexto `request.jwt.claims`. Embora o gateway I19 verificasse o token com GoTrue, tal decisão ocorria fora do banco; `auth.sessions` e o GUC são insuficientes quando a credencial SQL pode simular `authenticated`.

O I20 **elimina essa rota de execução no protótipo local**: o login SQL de teste `prumo_s1_signed_login_ci` não herda nem pode assumir `authenticated`; não pode chamar `prumo_s1_interface`, consultar sessões, ler a chave de assinatura ou dados de domínio. Recebe `EXECUTE` apenas de `prumo_s1_signed_i20.invocar` em schema privado não exposto, uma única fachada `SECURITY DEFINER` de teste com `search_path=''`.

## Contrato de segurança

- Antes de assinar, o gateway confirma o Bearer com o GoTrue confiável; rejeita `actor_id`, `session_id`, SQL e role inseridos pelo cliente. Permite somente as três operações fixas `MOVER`, `PAUSAR`, `REATIVAR` e seus argumentos estritos.
- Assina com HMAC-SHA256 a string canônica `prumo-s1-i20-v1|op|ator|sessao|loja|caso|atribuicao|destino|operador|motivo|epoch|nonce`, com UUIDs canônicos, campos opcionais `-` e motivo em enum, nunca texto médico livre.
- O PostgreSQL verifica a chave ativa/validade, assinatura, timestamp (até 30s antes e 5s depois do relógio local) e nonce único em transação. Só **depois** estabelece `request.jwt.claims` e chama as fachadas reais I14/051, que usam `auth.uid()` e verificam `auth.sessions` via I15/052.
- O nonce é consumido na mesma transação do comando; rollback desfaz nonce e operação, e dupla execução aceita no máximo uma prova.
- Chave HMAC aleatória de 32 bytes é gerada **durante o CI** e inserida apenas no banco efêmero por `postgres`; jamais há segredo embutido nas migrações ou exportado no registro de logs.
- `supabase/tests/s1_020_signed_gateway_local_only.sql` define schema, papel e funções **apenas para testes**; `backend/s1_gateway_signed_local.py` é o adapter local, invocado pelo servidor HTTP loopback de smoke test; `scripts/test_s1_002_signed_gateway_local.py` exerce fluxos positivos e adversariais.

## Escopo de testes I20

Repetir os 14 cenários I19 com GoTrue real e 50 migrations S0/S1, agora através do comando assinado e role SQL sem `authenticated`, e acrescentar: HMAC adulterado, autoria ou alvo alterado, timestamp vencido/adiantado, replay exato de nonce após execução bem-sucedida, prova HMAC válida com sessão GoTrue revogada, tentativas de `SET ROLE authenticated` ou leitura de chave, revogação da chave bloqueando novos comandos. O teste é seguro apenas em GitHub Actions/Docker local descartável; nenhuma credencial ou segredo real é usado.

## Segurança residual — NO-GO

Aprovação dos testes não valida comprometimento conjunto do servidor assinador e da credencial SQL, exfiltração do segredo HMAC no processo, nem infraestrutura TLS, reverse proxy, controle de origem, rate limiting, proteção contra CSRF quando relevante, gerenciamento/rotação automatizados de segredo, alertas de negativas, backup/retenção e failover. A função do ensaio continua `SECURITY DEFINER` proprietária de `postgres`, e não uma implementação definitiva de menor privilégio. Em produção, será necessário provisionamento operacional isolado, ownership mínimo, auditoria de superfície de execução e aprovação explícita. Não reutilizar a senha sintética da role de teste nem o servidor `http.server`.

A política automática de destinatário entre equipes, escalas, credenciais RH/responsáveis, UI real e integração completa do encerramento humano S0 ainda aguardam seus gates. I20 não altera essa governança nem incrementa percentual global.

**Resultados:** preencher após inspeção de CI; não marcar GO antes dos logs.
