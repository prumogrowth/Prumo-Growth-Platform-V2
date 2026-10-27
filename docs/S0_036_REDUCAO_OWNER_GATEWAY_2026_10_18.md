# S0-036 — redução incremental do proprietário das duas entradas assinadas

**Escopo autorizado:** GitHub privado PR #1 Draft, PostgreSQL 17 descartável e Supabase local gerenciado. Não aplicar migrações ao Supabase hospedado. Não usar usuários, telefones, tokens, segredos ou mensagens operacionais. Não mesclar PRs.

## Motivação e mapa de privilégios antes da migration

A S0/027 isolou **somente** o validador de HMAC em `prumo_s0_signer`, proprietário `NOLOGIN/NOINHERIT`, sem ler leads ou sessões. A S0/023–025 manteve duas entradas assinadas `SECURITY DEFINER` sob proprietário `postgres`. O gateway limitado só pode chamá-las com HMAC de curta duração e nonce de uso único. O validador por si não cancela planos e não reconcilia C07.

Dependências reais, verificadas no código:

| Entrada assinada | Validação | Encaminhamento comercial | Proprietário comercial residual |
| --- | --- | --- | --- |
| `gateway_cancelar_plano_assinado_s0` | `gateway_validar_prova_s0` (owner `prumo_s0_signer`) | `gateway_cancelar_plano_s0` → `cancelar_plano_gestor_sintetico` | `postgres` |
| `gateway_conciliar_c07_assinado_s0` | `gateway_validar_prova_s0` (owner `prumo_s0_signer`) | `gateway_conciliar_c07_s0` → `conciliar_pendencia_c07_sintetica` | `postgres` |

As duas wrappers legadas validam `auth.sessions` ativa e vínculo do gestor/loja antes de chamar funções comerciais `SECURITY INVOKER`, que exigem `current_user='postgres'`. A escrita comercial faz consultas `FOR UPDATE` e altera entidades do domínio sob RLS. **Transferir os proprietários legados diretamente para uma role técnica com permissões mínimas quebraria o guard atual e exigiria nova modelagem de políticas e grants; não fazer isso por tentativa cega.**

## Implementação S0/036

`supabase/migrations/202610180036_s0_owner_gateway_assinado.sql` adiciona `prumo_s0_signed_executor` como `NOLOGIN, NOINHERIT, NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOREPLICATION, NOBYPASSRLS`; recusa papel pré-existente inseguro ou membro não administrativo. A única associação SET/NOINHERIT é ao administrador `postgres`; tolera `supabase_admin` como associação administrativa gerenciada, sem conceder essa role explicitamente.

O novo proprietário recebe **apenas** `USAGE` no esquema privado e `EXECUTE` nas duas wrappers legadas `postgres SECURITY DEFINER`, além de `EXECUTE` no verificador HMAC concedido por seu real proprietário `prumo_s0_signer` usando `SET LOCAL ROLE`. `CREATE` no esquema privado é concedido apenas durante o bloco transacional de `ALTER FUNCTION OWNER` e revogado imediatamente. Antes da transferência, as entradas assinadas têm grants públicos revogados; preserva-se a concessão já existente exclusivamente ao `prumo_s0_gateway`.

**Nenhuma função comercial, assinatura HMAC, parâmetro, estrutura de chave, regra de sessão, estado, idempotência ou nonce foi reescrito.** Não há nova credencial SQL ou chave HMAC na migration.

### Fronteira resultante

`gateway SQL com HMAC` → `entrada assinada (owner: prumo_s0_signed_executor)` → `validador de prova (owner: prumo_s0_signer)` → `wrapper comercial legada (owner: postgres)` → `domínio SECURITY INVOKER (current_user=postgres)`.

**Esta não é uma redução integral do privilégio comercial.** `prumo_s0_signed_executor` pode invocar as duas wrappers comerciais `SECURITY DEFINER` legadas, que ainda operam com `postgres` depois das verificações de sessão e escopo. Não é autorizado criar login para o executor, nem usá-lo como worker de produção ou API RPC.

## Verificações e regressão

`supabase/tests/s0_owner_gateway_assinado.sql` (OWNER-04..06) verifica: papel estritamente não-login, ausência de membresia não administrativa, função assinada proprietária e ACL fechada, falta de acesso direto a `auth.sessions`, leads, planos, material HMAC, nonce e auditoria; dependências restritas `EXECUTE`; wrappers legadas permanecem `postgres` mas inacessíveis ao gateway sem assinatura. Os testes OWNER-03 e GW-06 pré-existentes foram atualizados para refletir **a nova arquitetura**, sem eliminar cenários negativos. `scripts/run-s0-local.sh` aplica 036 e toda a regressão.

`scripts/test_s0_auth_rest_local.py` inclui **AUTH-17**: na instância Supabase local gerenciada, as duas funções assinadas devem pertencer ao executor, as ACL privadas devem ser verificadas e RPCs privilegiadas devem permanecer inacessíveis pela API REST pública mesmo com JWT de gestor. A suíte anterior AUTH-01..16 permanece.

**Evidência PostgreSQL:** [GitHub Actions #39120829358 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39120829358) no commit `77062a5047e57c212dff51bad844ae990b3cdcea`, com `OWNER-01..06`, `GW-01..07`, demais regressões S0 e 24 testes unitários Python PASS.

**Supabase Auth/REST:** registrar somente após confirmar a execução integrada e seus logs. Não presumir sucesso com base no PostgreSQL isolado.

## Próxima decisão de engenharia — owner comercial residual

Antes de rebaixar `gateway_cancelar_plano_s0` e `gateway_conciliar_c07_s0`, mapear cada tabela, trigger, função e grant efetivamente necessários sob Supabase gerenciado, preservando simultaneamente RLS de usuário, verificação de sessão, operação escopada, concorrência, HMAC, nonce, idempotência e auditoria. Uma role `BYPASSRLS` ou ampla concessão `UPDATE` comercial não é atalho aceitável. Um novo `SECURITY DEFINER postgres` chamado por wrappers rebaixadas **não** demonstraria remoção da confiança privilegiada do domínio, apenas deslocamento.

Faltam ainda: cofre de produção, isolamento de credenciais SQL/HMAC, auditoria externa durável de negativas, LGPD, restore e observabilidade. DEC-WA-04/06 permanecem pendentes; DEC-WA-05 aprovada quanto à titularidade Meta por concessionária. Contrato C07 de ocorrência da WA-01C ainda não homologado; `statuses[].id` não pode ser suposto identificador de observação único.

**GO** exclusivamente para evolução e testes S0 com dados sintéticos. **NO-GO** para API privilegiada pública, integração Meta/Banco real, migrações no Supabase hospedado, produção ou merge dos PRs.

## Fechamento — compatibilidade Supabase local gerenciado (18/10/2026)

**[GitHub Actions Supabase Auth/REST #39120910939 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39120910939)** no mesmo commit de código `77062a5047e57c212dff51bad844ae990b3cdcea`. Logs efetivamente verificados: `AUTH-01..17` PASS (incluindo `AUTH-13-REVOKE`), sem traceback ou erro; inicialização, execução das migrações e teardown da instância Supabase **local** concluídos. `AUTH-17` validou owner `prumo_s0_signed_executor` nas funções assinadas com `SECURITY DEFINER`, negativas de acesso às tabelas/sessões/segredos e ausência de RPC pública. O fluxo assinado de cancelamento e reconciliação continua coberto por AUTH-12..14.

O [CI PostgreSQL #39120829358 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39120829358) já havia comprovado OWNER-01..06, GW-01..07 e as demais regressões (24 unitários Python). A etiqueta cara `run-auth-integration` foi **retirada** após o teste.

**Conclusão precisa:** compatibilidade da transferência das **duas entradas assinadas** está aprovada em PostgreSQL 17 e Supabase GoTrue/PostgREST local gerenciado. **Não foi reduzido o privilégio efetivo do código comercial legado**, que continua acessível a partir das funções `postgres SECURITY DEFINER` sob assinatura/sessão/escopo, e isso precisa de outro projeto de migração. Nenhuma implantação no Supabase hospedado.
