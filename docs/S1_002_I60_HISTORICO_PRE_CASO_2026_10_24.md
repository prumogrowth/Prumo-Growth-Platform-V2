# I60 — Contextualização de conversas anteriores ao caso (RLS candidata)

**24/10/2026. Apenas ambiente descartável.**

I41/I42/I43 bloqueavam toda conversa/mensagem de `caso_id=NULL`, incluindo histórico anterior ao primeiro caso humano (já registrado como pendência nos ensaios I45/I48). O novo candidato em `supabase/tests/s1_084_proto_rls_contexto_sem_caso_local_only.sql` autoriza SELECT dessas conversas somente quando o mesmo par `concessionaria_id/lead_id` tem algum caso S0 que o JWT atual pode ler por equipe/titularidade I41 ou exceção ativa I42; a loja também precisa estar ativa. O contexto de mensagem exige conversa exata e `caso_id=NULL`, sem conferir acesso só por telefone ou grant genérico de loja.

A composição faz uma PERMISSIVE adicional e substitui a RESTRICTIVE de conversas/mensagens por um predicado único OR: caso regular/excepcional ou histórico sem caso contextual autorizado. Não autoriza envio de mensagens sem caso, leitura de contato sem caso autorizado, outro time ou outra loja. Testes PG17 em BEGIN/ROLLBACK e GoTrue real-local após I44 e antes dos ensaios I45–I50, com rollback lógico integral dos objetos e linhas fictícios de I60 verificam usuário, equipe, histórico, exceção, revogação, isolamento e ausência de DML. Nenhuma policy I60, função SECURITY DEFINER ou exceção sintética foi promovida a migration operacional.

A homologação futura exige persistir um contrato de exceção por caso sob autorização de executor real e compor regras finais S0/S1 para todos os objetos D2/D3/D4. Esse ensaio não homologa produção nem os demais dados pessoais e indiretos.

**Evidências CI:** adicionar somente após conclusão e inspeção de logs.

## Revisão da sequência de testes

A execução GoTrue inicial #40143950998 falhou em HTTP 403 ao reabrir uma exceção depois das mutações de equipe/RLS das regressões I45–I50. O isolamento foi corrigido, sem mudança no candidato SQL: o novo ensaio roda antes dessas mutações e faz teardown completo de policies, schema, mensagens, conversas e contato sintéticos, mantendo o comportamento negativo original de I45/I48. A homologação dependerá dos novos logs.
