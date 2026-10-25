# I66 — Quarentena SQL da interface legada S1 (ACL-only)

**25/10/2026 — apenas PG17 e GoTrue/PostgREST descartáveis; nunca hosted.**

O I65 identificou que o schema `prumo_s1_interface` não está exposto no PostgREST, **mas** continua a conceder `USAGE` e `EXECUTE` de três fachadas `SECURITY DEFINER` diretamente a `authenticated`. Essas permissões de execução SQL existiam desde a migration I51, antes da consolidação dos gateways assinados I53/I62. O isolamento via lista de schemas do Data API é defesa importante, porém não justifica manter uma capacidade legada ampla.

O candidato `supabase/tests/s1_092_legacy_interface_acl_quarantine_local_only.sql` não remove funções nem altera seus corpos, donos, gatilhos, RLS ou tabelas. Ele **revoga todas as concessões de funções** desse schema para `PUBLIC`, `anon`, `authenticated` e `service_role` e revoga seus acessos ao próprio schema. Antes de modificar, exige exatamente os três wrappers esperados, todos com owner `postgres` e `SECURITY DEFINER`; desvios causam falha fechada. Depois, verifica matriz de privilégios, I61 privado e as quinze políticas de histórico I63/I64.

A RLS e os gateways assinados **não dependem de chamadas SQL diretas aos três wrappers I51**. O objetivo é que o token do navegador jamais invoque as fachadas antigas; a autorização operacional continua no executor especializado com GoTrue + HMAC e nonce. O I66 é uma **quarentena candidata**, não promoção de migração: a interface antiga pode ser investigada e restaurada apenas em um rollout auditado.

O aceite PG17 `supabase/tests/s1_093_legacy_interface_acl_quarantine_aceite.sql`, transacional, prova a execução antiga chegando até seu validador (bloqueada por sessão) e, depois da revogação, que o mesmo papel já não consegue **entrar nas três funções**. Mantém RLS de Supervisor, segurança das funções privadas e a propriedade dos wrappers intactas. A prova GoTrue executa a mesma quarentena na stack efêmera, assegura a negação da interface por role `authenticated` e exercita novamente comando canônico assinado I62 sem alterar a concessão do usuário.

**Limites:** I66 não é análise de todas as operações legadas restantes fora de `prumo_s1_interface`, nem desativa schemas por configuração da plataforma. Possíveis consumidores SQL internos desses wrappers ainda exigiriam inventário adicional antes de rollout, embora nenhum dependa deles nos testes I53/I62–I65. Os bloqueios de tabelas administrativas I64 permanecem candidatos.

## Prova complementar GoTrue real

O ensaio `scripts/test_s1_002_i66_legacy_interface_acl_e2e.py` executa-se após o I65, quando as provas de exposição da interface anterior já estão concluídas. Aplica exatamente o candidato `s1_092` ao PostgreSQL efêmero de GoTrue, compara privilégios antes/depois para três roles e três wrappers, tenta entrada SQL sob a própria role `authenticated`, tenta as três RPCs em `public` com token GoTrue real e confirma a chamada assinada I62 (revogação idempotente) com o mesmo Gestor e chave independente. Por fim, confirma que as RLS I63/I64 e a validade da sessão não foram modificadas. Até a CI concluir, este é roteiro, **não evidência certificada**.

## Certificação final — 25/10/2026

**PostgreSQL 17 descartável: SUCCESS.** [Workflow #40190799418](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40190799418), job `121161191549`. Conferido `PASS I66-01` a `PASS I66-08`, **8/8**, preservadas as provas anteriores I64/I65 e a regressão S0+S1 em `PASS S0+S1 I52-I66 canonical and candidate stages after legacy regression`. O fixture executa em `BEGIN/ROLLBACK` e não deixa nenhuma alteração persistente de ACL.

**GoTrue real + PostgREST + HMAC: SUCCESS.** [Workflow #40190799375](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40190799375), jobs `121161191471` (E2E) e `121161191595` (unitários), ambos sucesso. Logs `PASS I66-E2E-01` a `PASS I66-E2E-08`, **8/8**: ACL antiga aberta reproduzida antes do candidato; três funções e schema revogados para as roles cliente; tentativa SQL real negada antes do corpo; três RPCs ausentes no PostgREST público; assinatura GoTrue/mTLS/HMAC do I62 continua executável sem permissão para interface legada; leitura autorizada de histórico e negação de outra equipe mantidas; JWT real não é revogado pelo corte de ACL.

**Falha diagnóstica inicial, corrigida:** [workflow PG17 #40190664139](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40190664139) parou no código da auditoria por tentar consultar a permissão como se `PUBLIC` fosse uma role PostgreSQL comum. Foi corrigido em `cc79b44f39e9ce2a1c3e99f7a50198a9b8cba9de`: `REVOKE ... FROM PUBLIC` permanece explícito, e `has_schema_privilege/has_function_privilege` verifica `anon/authenticated/service_role` concretamente.

**Status:** I66 certificado **somente como candidato de laboratório**. Não foi criada migration de produção, o banco hospedado não foi tocado, a branch `main` não foi alterada e o gateway legado não foi excluído. Para eventual rollout, falta avaliar consumidores legados fora dos testes, credenciais e roles adicionais, políticas de default grants e a configuração de schemas expostos do ambiente real. O bloqueio de cinco tabelas administrativas do I64 continua pendente de um modelo operacional próprio.
