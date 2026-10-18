# Auditoria cruzada S0-035/S0-036 e reparo S0-036A — 18/10/2026

## Escopo / fontes conferidas

Revisão de leitura das migrations S0 001–034/036, chamadas e grants das wrappers comerciais/assinadas, testes de proprietário, resultados CI PG17 e Supabase GoTrue/PostgREST, documentação das etapas 033/034A/034B/035/036 e estado dos PRs Draft. **Não avançamos para a transferência das wrappers comerciais legadas (S0-037 de escopo), não fazemos merge, deploy ou escrita no Supabase hospedado.**

A S0-035 não introduziu migration: seus AUTH-15/16 conferem explicitamente objetos recentes e ausência de RPC; S0-036 trocou apenas o proprietário das entradas assinadas para `prumo_s0_signed_executor`. Os testes OWNER-04..06, GW-01..07, AUTH-17 e os testes de negócio comprovaram a execução autorizada, revogação de sessão, HMAC e nonce. Os commits após esses CIs continham somente documentação.

## Achado concreto AUD-036A-01 — ACL implícita em auxiliar de trigger

A função `prumo_private.auditar_rotacao_gateway_s0()` foi criada na migration 026 sem `REVOKE EXECUTE` explícito. Como o PostgreSQL concede `EXECUTE` a `PUBLIC` por padrão na criação de funções, e `prumo_s0_gateway` recebeu `USAGE` de `prumo_private` na migration 023, sua ACL inicial permite `has_function_privilege(..., 'EXECUTE')` mesmo não sendo uma das **duas** entradas comerciais assinadas. Trata-se de função `RETURNS trigger`, que normalmente não admite invocação SQL direta; portanto **não há prova de execução comercial não autorizada**, mas a ACL está mais ampla que o princípio declaradamente adotado e o teste GW-06 examinava apenas assinaturas específicas.

**Correção aditiva** na migration cronológica `202610180037_s0_036a_acl_audit_repair.sql`: revogar `EXECUTE` dessa função para PUBLIC/anon/authenticated/service_role/gateway/signer/executor. O arquivo leva número técnico 037 para manter a ordem de migrations, mas seu escopo de entrega é **S0-036A (reparo de auditoria)**, não a futura migração das wrappers comerciais legadas. A revogação de execução explícita não altera a trigger instalada, seu owner, seus eventos de rotação nem regras de negócio.

## Auditoria automática reforçada

`supabase/tests/s0_036a_auditoria_acl_completa.sql` adiciona asserções:
- **AUD-036A-01:** percorrer efetivamente **todas** as funções de `prumo_private`, exigindo EXECUTE ausente de anon/authenticated/service_role e que `prumo_s0_gateway` tenha exatamente duas entradas assinadas;
- **AUD-036A-02:** verificar o conjunto fechado de funções executáveis por `prumo_s0_signer` (HMAC/material) e `prumo_s0_signed_executor` (assinadas, verificador e duas wrappers comerciais delegadas), sem acesso inadvertido às demais;
- **AUD-036A-03:** todas as funções `SECURITY DEFINER` privadas precisam de `search_path` fixado explicitamente em vazio;
- **AUD-036A-04:** invocação direta da função auxiliar, com `SET ROLE prumo_s0_gateway`, deve falhar por **permissão** antes de tratar a semântica `RETURNS trigger`.

`scripts/test_s0_auth_rest_local.py` recebe **AUTH-18**: repetir na instância Supabase local gerenciada o inventário geral de ACL do gateway/papéis da Data API e conferir `search_path` de todas as funções privadas privilegiadas. Continuam valendo AUTH-01..17 e regressões PG S0/001–036; nenhum teste de produção real.

## Pendências preservadas

- Mesmo após a correção, as duas wrappers comerciais legadas continuam `SECURITY DEFINER postgres`, e as funções do domínio chamam `current_user='postgres'`. Acesso ao executor restrito é **delegado**, não privilégio mínimo ponta a ponta.
- Nenhum worker real C02/C07, Meta HMAC/webhook, payload protegido, segredo de produção, ACK 200, Graph, instituição financeira ou OpenAI foi ativado.
- DEC-WA-01/02/03 aprovadas como direção e DEC-WA-05 aprovada para propriedade de App/WABA/emissor **por concessionária**. DEC-WA-04/06 e política de dedupe de eventos C07 continuam pendentes.
- O Supabase hospedado não recebeu migrations comerciais; PR #1 e PR #2 permanecem Draft. A compatibilidade PostgreSQL/Supabase **da correção** deve ser registrada apenas após execução efetiva dos dois CIs.

## Fechamento de auditoria — evidência final (18/10/2026 UTC)

**Reparo final:** migration `202610180037_s0_036a_acl_audit_repair.sql` e teste `supabase/tests/s0_036a_auditoria_acl_completa.sql`, no commit de código `af6a21926eb36dc33dc5150c4943f26f3a1e500d`.

- [PG17 #39122872136 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122872136): `AUD-036A-01..04` PASS, `OWNER-01..06`, `GW-01..07`, demais regressões SQL/concorrência e 24 testes unitários Python OK. Confirmado que somente as duas entradas assinadas são executáveis por `prumo_s0_gateway`; validador/owner técnico têm conjuntos fechados de funções executáveis.
- [Supabase local GoTrue/PostgREST #39122948236 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122948236): `AUTH-01..18` PASS, incluindo novo inventário `AUTH-18` de EXECUTE público/gateway e `search_path` nas rotinas `SECURITY DEFINER`. Teardown do Supabase efêmero concluído, nenhum erro nos logs.
- **Histórico de teste, corrigido:** [PG17 #39122774143 — FAILURE](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122774143) teve `AUD-036A-01/02` PASS, mas `AUD-036A-03` comparava o `search_path` vazio somente com `search_path=`. O catálogo PostgreSQL representa também como `search_path=""`, embora as cinco rotinas já definissem `SET search_path=''` no SQL. O teste foi ajustado para aceitar ambas as representações, **sem alteração de função comercial**. A execução intermediária #39122866007 foi cancelada pela política de concorrência do CI quando o último commit foi publicado.
- Etiqueta `run-auth-integration` removida após o sucesso. A correção cobre apenas ACL de um auxiliar de trigger e acrescenta testes; **não** rebaixa o owner das wrappers comerciais legadas nem constitui homologação operacional.
- A migration recebe timestamp técnico 037 para sequenciamento, mas seu conteúdo é exclusivamente o reparo de auditoria **S0-036A**. O projeto da futura transferência comercial segue pendente de escopo/validação independente.
