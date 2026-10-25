# I61 — Exceções canônicas por caso: transferência, revogação e auditoria

**24/10/2026. Branch experimental `feat/s1-002-equipe-prumo`. Não implantar ou mesclar em produção.**

## Contrato integrado

A migração incremental `supabase/migrations/202610190059_s0_s1_excecao_caso_canonica.sql` acrescenta às estruturas S0/S1 uma tabela privada de exceções por **um `caso_id`, `atribuicao_id`, `operador_id` e `concessionaria_id` exatos**, acompanhada de eventos `CRIADA/REVOGADA` protegidos contra alteração. Não concede um `vinculos_papel_escopo` por loja, não cria endpoint público e não altera as políticas públicas RLS ou a matriz financeira.

Ao transferir caso na mesma equipe, o executor interno valida gestor e duas relações ativas de supervisão, loja/caso e titularidade anterior, trava os atores e as concessões, exige destino **sem concessão vigente à loja** (caso contrário é usado o caminho normal), revalida a pausa A2 e o ID da atribuição esperada, registra o entitlement apenas para a nova atribuição, encerra a anterior e insere a nova através da tabela **canônica** `public.atribuicoes_humanas`. As triggers S0 I57 e S1 I2 são adaptadas para aceitar a prova excepcional identificada pela chave exata; ambas continuam rejeitando atribuições sem grant e sem exceção. O guard I52 de intake permanece inalterado.

Revogação formal pelo mesmo gestor autorizado corta imediatamente o entitlement, sem fechar automaticamente o caso. O fechamento posterior da atribuição também revoga automaticamente uma exceção ainda válida. Consultores não podem alterar o registro ou acessar a trilha bruta; teste sintético somente com role postgres. D2/D3/D4 não são liberados neste incremento: I61 é pré-requisito de integração com as RLS candidatas I41–I60, não o ato de publicá-las.

## Limitações intencionais

- O `p_gestor` é parâmetro do **executor interno PostgreSQL de laboratório**, ainda não uma identidade autenticada vinculada à sessão GoTrue/HMAC. É proibido expor esta função ao REST sem uma camada assinada que derive o gestor de sessão confiável.
- Não dá acesso a dados Meta/financeiros nem à interface operacional.
- O caminho excepcional para ciclos comerciais terminais fecha por padrão; modalidades `retorno_pos_venda` ou `revisao_humana` requerem contrato específico posterior.
- A migração é aplicada somente no PG17 descartável. `supabase/tests/s1_085_excecao_caso_canonica_aceite.sql` prova os principais limites dentro de BEGIN/ROLLBACK.

## CI

Registrar os resultados apenas após a execução do GitHub Actions e a inspeção dos logs.

## Aceites de CI — inspecionados

- **Versão final PG17 SUCCESS:** [workflow #40145749776](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40145749776), job `121026590257`, commit de código e testes `16e9b3086fb3d3aaf0b5053caf4fc10bde5f15a4`. Logs: `PASS I61-01` até `PASS I61-09` (**9/9**), mais `PASS S0+S1 I52-I61 canonical stages after legacy regression`. Todos os dados de teste rolaram back.
- **Versão prévia PG17 SUCCESS:** [workflow #40145560409](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40145560409), job `121026010305`, `I61-01..07` (**7/7**) com a regressão anterior. A versão final acrescentou dois testes: negação de reaproveitamento da exceção em outro caso e revogação automática após encerramento da atribuição.
- **Falha inicial preservada:** [workflow #40145376743](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40145376743) falhou em uma expectativa muito estreita do teste negativo, pois a trigger S1 rejeitou antes da trigger S0. Em `e2122760c3c20f760f1129d1717856df536c11b2`, o teste passou a aceitar ambos os resultados de negação e a migração preservou explicitamente locks de concessão da origem e da loja. **Nenhum acesso indevido foi liberado.**

**Certificação restrita ao PG17 descartável.** A migration canônica está na branch, mas a migração em Supabase hospedado, o executor atrelado a uma sessão GoTrue real, a trilha de assinatura/HMAC e a promoção de RLS de histórico ainda não estão integrados/homologados. O próximo incremento deve cobrir essas fronteiras antes de qualquer abertura operacional.

## Estado

I61: **código concluído e 9/9 testes canônicos PG17 aprovados**; integração de produção e autenticação real da operação excepcional **pendentes**.
