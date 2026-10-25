# I66 — Quarentena SQL da interface legada S1 (ACL-only)

**25/10/2026 — apenas PG17 e GoTrue/PostgREST descartáveis; nunca hosted.**

O I65 identificou que o schema `prumo_s1_interface` não está exposto no PostgREST, **mas** continua a conceder `USAGE` e `EXECUTE` de três fachadas `SECURITY DEFINER` diretamente a `authenticated`. Essas permissões de execução SQL existiam desde a migration I51, antes da consolidação dos gateways assinados I53/I62. O isolamento via lista de schemas do Data API é defesa importante, porém não justifica manter uma capacidade legada ampla.

O candidato `supabase/tests/s1_092_legacy_interface_acl_quarantine_local_only.sql` não remove funções nem altera seus corpos, donos, gatilhos, RLS ou tabelas. Ele **revoga todas as concessões de funções** desse schema para `PUBLIC`, `anon`, `authenticated` e `service_role` e revoga seus acessos ao próprio schema. Antes de modificar, exige exatamente os três wrappers esperados, todos com owner `postgres` e `SECURITY DEFINER`; desvios causam falha fechada. Depois, verifica matriz de privilégios, I61 privado e as quinze políticas de histórico I63/I64.

A RLS e os gateways assinados **não dependem de chamadas SQL diretas aos três wrappers I51**. O objetivo é que o token do navegador jamais invoque as fachadas antigas; a autorização operacional continua no executor especializado com GoTrue + HMAC e nonce. O I66 é uma **quarentena candidata**, não promoção de migração: a interface antiga pode ser investigada e restaurada apenas em um rollout auditado.

O aceite PG17 `supabase/tests/s1_093_legacy_interface_acl_quarantine_aceite.sql`, transacional, prova a execução antiga chegando até seu validador (bloqueada por sessão) e, depois da revogação, que o mesmo papel já não consegue **entrar nas três funções**. Mantém RLS de Supervisor, segurança das funções privadas e a propriedade dos wrappers intactas. A prova GoTrue executa a mesma quarentena na stack efêmera, assegura a negação da interface por role `authenticated` e exercita novamente comando canônico assinado I62 sem alterar a concessão do usuário.

**Limites:** I66 não é análise de todas as operações legadas restantes fora de `prumo_s1_interface`, nem desativa schemas por configuração da plataforma. Possíveis consumidores SQL internos desses wrappers ainda exigiriam inventário adicional antes de rollout, embora nenhum dependa deles nos testes I53/I62–I65. Os bloqueios de tabelas administrativas I64 permanecem candidatos.

## Prova complementar GoTrue real

O ensaio `scripts/test_s1_002_i66_legacy_interface_acl_e2e.py` executa-se após o I65, quando as provas de exposição da interface anterior já estão concluídas. Aplica exatamente o candidato `s1_092` ao PostgreSQL efêmero de GoTrue, compara privilégios antes/depois para três roles e três wrappers, tenta entrada SQL sob a própria role `authenticated`, tenta as três RPCs em `public` com token GoTrue real e confirma a chamada assinada I62 (revogação idempotente) com o mesmo Gestor e chave independente. Por fim, confirma que as RLS I63/I64 e a validade da sessão não foram modificadas. Até a CI concluir, este é roteiro, **não evidência certificada**.
