# WA-53 — Harmonização da ordem de bloqueios WA50 e concorrência entre rotas S0

**25/10/2026 — somente `prumo_s0_test_ci`, PostgreSQL 17 descartável, PR #2 Draft.**

## Alteração aplicada

A WA50 anterior tinha uma inversão potencialmente perigosa: obtinha a trava `wa48-key:<key>` durante a verificação HMAC e só depois a trava `wa39:<binding>:<event>`. A WA49, WA51 e WA52 adquirem o lock do evento antes da chave. Essa divergência permitiria espera circular se rotas coexistissem sobre o mesmo evento/chave.

A migration offline `202610230052_s0_meta_lock_order_repair_fixture.sql` substitui **apenas no fixture** o corpo de `meta_wa50_restricted_forensic_fixture_s0` mantendo o mesmo proprietário NOLOGIN/NOSUPERUSER, assinatura, OID, ACL e `SECURITY DEFINER`. Primeiro resolve o vínculo S0, **sem consumir nonce**, depois obtém o lock WA39 de vínculo/evento, então chama o verificador HMAC/nonce WA48 que obtém o lock da chave. Assim, WA49, WA50 e WA51 seguem evento → chave, enquanto WA52 segue outbox FOR SHARE → evento → chave. A lógica de recibo-sombra WA48 continua falhando fechada para conflitos de tipo, como documentado na WA50.

`supabase/tests/s0_wa_057_assert_lock_order_cross_routes_pg17.py` cria chaves HMAC sintéticas independentes em duas concessionárias e executa **32 provas**: proprietário e permissões da função substituída, ausência de acesso do cliente às tabelas, negação por escopo sem consumo de nonce, HMAC adulterado, replay, variante, conflito rejeitado na WA50, ausência de flags comerciais, concorrência WA50→WA49, WA50→WA51, WA50→WA52, WA51→WA50, isolamento entre concessionárias sob mesma referência de evento, revogação e impossibilidade de mutação/deleção. As esperas são verificadas por `pg_stat_activity` com sessões PostgreSQL independentes; o CI mantém todas as provas WA39–52.

## Limites e coordenação

A correção abrange essas rotas restritas de laboratório, **não** a chamada privilegiada histórica WA40, que também deve passar por auditoria de ordenação antes de qualquer integração. A WA50 não adquiriu lock de leitura da outbox (continua obsoleta como caminho de classificação de estado); somente a WA52 demonstra consistência de leitura sob cancelamento. Não há mudança na S1, principal IAM/M2M verdadeiro, webhook Meta produtivo, Graph, ACK, envio, mudança de caso, deploy hospedado nem merge. As provas não equivalem à segurança de produção.

**Coordenação com a S1:** nenhuma alteração é solicitada à S1 para concluir esta etapa. Uma futura integração deverá acordar contratos de cancelamento, aquisição de bloqueios e sinais de invalidade sem tocar diretamente os objetos S1 a partir desta branch.

**Próxima etapa proposta:** auditoria de inversão de locks da WA40 privilegiada e bloqueio explícito de rotas legadas inseguras antes de encadear a autenticação operacional end-to-end.
