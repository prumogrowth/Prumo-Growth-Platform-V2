# S0 — auditoria preliminar das dependências de privilégios comerciais (incremento 028, sem migração)

**Escopo:** revisão estática do código vigente no HEAD d31f990465989adbe11b699ddcdb447061890adb. Sem execução SQL comercial, sem alteração da arquitetura, sem deploy e sem aceite de redução de privilégios. Esta revisão prepara, mas NÃO implementa, a transferência de ownership das funções comerciais.

## Cadeia de execução identificada

1. O papel limitado `prumo_s0_gateway` executa apenas `prumo_private.gateway_cancelar_plano_assinado_s0` e `prumo_private.gateway_conciliar_c07_assinado_s0` (migration 025).
2. Essas funções `SECURITY DEFINER`, ainda de propriedade `postgres`, chamam `prumo_private.gateway_validar_prova_s0`, verificador de propriedade `prumo_s0_signer` desde a migration 027, com acesso mínimo a HMAC/nonce.
3. Após prova válida, as entradas assinadas chamam `gateway_cancelar_plano_s0` e `gateway_conciliar_c07_s0` (migration 023), ainda `SECURITY DEFINER` de `postgres`.
4. As funções intermediárias consultam `auth.sessions` (`FOR KEY SHARE`), invocam respectivamente `cancelar_plano_gestor_sintetico` e `conciliar_pendencia_c07_sintetica`, e inserem em `prumo_private.auditoria_gateway_s0`.
5. A migration 023 documenta dependência explícita: funções de domínio existentes verificam `current_user='postgres'`. Mudar somente o owner das wrappers sem revisar essas verificações poderá causar negação legítima; conceder privilégios indiscriminados seria regressão de segurança.

## Matriz preliminar (verificar nos catálogos em banco efêmero)

| Objeto/área | Executor/owner atual | Dependência | Risco e condição para refatorar |
|---|---|---|---|
| Entrada assinada C08/C07 | `SECURITY DEFINER postgres` | verificador HMAC e wrapper legada | não rebaixar antes de provar ACL e execução encadeada |
| Verificador HMAC | `SECURITY DEFINER prumo_s0_signer` | colunas específicas de chave, nonce, pgcrypto | manter isolamento e revogação já aprovados |
| Wrappers legadas | `SECURITY DEFINER postgres` | `auth.sessions`, domínio, inserção de auditoria | exigir sessão viva, manter revogação de EXECUTE ao gateway |
| Domínio C08/C07 | conferir owner e `current_user` no SQL vigente | tabelas comerciais, verificações de gestor/loja, versão, concorrência | dependência de postgres documentada em 023; não conceder BYPASSRLS |
| Trilha de sucesso do gateway | escrita via wrapper | FK atores, concessionárias, inserts | preservação de atomicidade/idempotência; negativas não são trilha durável |
| Runtime externo | backend interno sem API pública | GoTrue, chave de assinatura, senha SQL | segredo combinado e coleta de negativas permanecem pendentes |

## Plano para migration candidata posterior (não implementado neste incremento)

- Enumerar com `pg_proc`, `pg_roles`, `pg_auth_members`, `information_schema.role_table_grants` e `pg_class` os owners, flags `prosecdef`, ACL de EXECUTE, dependências de tabela/sequence, `search_path`, RLS e `relforcerowsecurity` em PostgreSQL 17 efêmero e Supabase local gerenciado.
- Revisar integralmente os SQLs das funções de domínio, especialmente comparações de `current_user`, travas `FOR UPDATE`, efeitos colaterais, sequences e triggers. `SECURITY DEFINER` muda o effective current_user para o owner; para migrar com segurança, separar *identidade técnica* de *autorização do ator GoTrue*, sem permitir que parâmetros fornecidos pelo cliente se tornem prova de identidade.
- Selecionar um papel de negócio sem LOGIN/CREATEROLE/CREATEDB/SUPERUSER/BYPASSRLS; definir GRANTs mínimos e isolamento de esquema. Verificar limitações do `postgres` não-superuser do Supabase local, `SET ROLE`, `CREATE` temporário para `ALTER OWNER` e ordem REVOKE→ALTER OWNER→GRANT, conforme aprendizado da 027.
- Registrar testes negativos para `anon`, `authenticated`, `service_role`, gateway chamando wrappers legadas, outro gestor/loja, operador sem atribuição, sessão revogada, HMAC inválido/expirado/reutilizado, versão obsoleta e concorrência. Confirmar também fluxo legítimo sem elevação indevida.
- Somente após aprovação PostgreSQL sintética avaliar, mediante gatilho deliberado, o teste pesado Auth/REST; não usar o ambiente Supabase hospedado.

## Critério de aceite

Este documento é **auditoria estática, não validação executável**. Não foram criados papéis novos, alteradas funções, aplicadas migrações ou executados testes novos neste incremento. CI 027 anterior permanece referência histórica válida apenas para aquele código. **GO** para engenharia sintética de uma migration candidata cuidadosamente limitada; **NO-GO** para merge, ambiente hospedado ou operação real.
