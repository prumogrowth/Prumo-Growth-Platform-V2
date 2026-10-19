# S1-002/I15 — Verificação de sessão ativa para comandos privados (19/10/2026)

**Estado:** implementado e validado em PostgreSQL 17 DESCARTÁVEL, não homologado em GoTrue/PostgREST real. **Não implantar nem adicionar `prumo_s1_interface` à lista de schemas da Data API**.

## Continuidade do I14 / achado de auditoria

No HEAD `a8971aa0`, o I14 já restringia `EXECUTE` das três fachadas a `authenticated`, isolava as funções em `prumo_s1_interface` e preservava `prumo_private` sem `USAGE` pelo cliente. Todavia, o helper `s1_exigir_identidade_sessao()` consultava o GUC legado `request.jwt.claim.role` e `auth.uid()` sem verificar `session_id` presente numa sessão vigente.

PostgREST moderno fornece um JSON `request.jwt.claims`; GoTrue registra sessões em `auth.sessions`, associando o JWT à linha por `session_id`. Uma sessão encerrada pode deixar JWT previamente emitido utilizável até `exp`; a existência do registro ajuda a bloquear operações sensíveis após o encerramento (não substitui assinatura nem expiração do JWT no gateway).

**Fontes consultadas:**
- https://supabase.com/docs/guides/auth/sessions
- https://supabase.com/docs/guides/auth/jwt-fields
- https://docs.postgrest.org/en/v13/references/transactions.html
- https://supabase.com/docs/guides/database/functions

## Incremento aplicado

Migration `supabase/migrations/202610190052_s1_verificacao_sessao_gotrue.sql` faz `CREATE OR REPLACE` apenas do helper privado já chamado pelas três fachadas I14.

- Lê `request.jwt.claims` (JSON moderno), exige `role=authenticated`, `sub` UUID e `session_id` UUID.
- Compara `sub` com `auth.uid()` e exige a existência do ator.
- Verifica `auth.sessions.id=session_id` e `auth.sessions.user_id=auth.uid()`; lê a linha `FOR KEY SHARE` para serializar uma exclusão de sessão concorrente com o comando.
- Nega ausência de JSON, dados inválidos, usuário divergente ou sessão inexistente/revogada com SQLSTATE `42501`.
- Mantém `SECURITY INVOKER` no helper e `SECURITY DEFINER` com `search_path=''` e nomes qualificados nas fachadas I14.
- Não amplia `USAGE`, `EXECUTE`, DML, esquemas expostos ou autorização de responsável/gestor/operador. A identidade do solicitante continua derivada da sessão e nunca de parâmetro do navegador.

**Pré-condição:** a tabela **real** `auth.sessions` precisa existir, gerenciada pelo GoTrue, com `id` e `user_id`. O arquivo da migration **não** cria nem replica essa tabela. Ausência de tabela é falha fechada na execução; não tentar instalá-la diretamente em Supabase hospedado sem ensaio real.

## Testes e evidências

Apenas o runner PG17 descartável cria uma **substituta mínima** da tabela `auth.sessions` em `supabase/tests/s1_015_fake_gotrue_bootstrap.sql`. O arquivo de produção nunca é usado para criar essa substituta. A suíte `supabase/tests/s1_015_verificacao_sessao.sql` verifica: contexto legacy sem claims JSON, session_id ausente, divergência de sub, sessão inexistente, sessão de outra pessoa, papel indevido, pausa legítima A/B, bloqueio após DELETE da sessão, nova sessão para retorno, falsa metadata de responsável/gestor, session_id malformado, isolamento de schema e tabela.

**CI verificado:** [#39311622892 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39311622892), SHA ensaiado `6834f6ab05ef4142e782cd513562d6a599c2c311`, job `118262398361`, logs de execução inspecionados: **S1V-01..13 = 13/13 PASS**, **S1S-01..14 + S1S-02B = 15/15 PASS** (executados antes da migration 052). Regressões no mesmo job: S1AG 5/5, S1MR 4/4, S1M 24 marcadores em duas passagens de 12, S1T 14/14, S1A 9/9, S1H 8/8, S1R 27 marcadores em três passagens de 9, AUD1 7/7 e AUD2 5/5. Nenhum erro SQL inesperado nesses marcadores. Os scripts anteriores do runner S0/S1 também concluíram no job `SUCCESS`.

## Limites / gates abertos (não declarar produção)

1. **GoTrue + PostgREST de verdade, isolados:** subir componentes descartáveis e validar JWT assinado, `exp`, login, logout, claims `session_id`, token adulterado, `anon`, `authenticated` e `service_role` por HTTP; jamais reutilizar credenciais de produção. A suíte I15 não faz qualquer validação criptográfica.
2. **Contrato gateway:** somente gateway confiável pode estabelecer contexto JWT a partir de token validado; sem conexão SQL concedida a usuários, sem aceitar GUC/identidade do solicitante em parâmetros externos, e sem acrescentar `prumo_s1_interface` à Data API automaticamente. Exposição futura requer revisão formal.
3. **Sessão versus timeout:** a existência em `auth.sessions` detecta remoção de sessão; não substitui `exp`, política de tempo máximo, inatividade ou controle do provedor, pois algumas sessões expiradas não são removidas imediatamente.
4. **Integração funcional:** sincronização S0 de conclusão humana/titular, UI de gestores, capacidade/escala, política de destinatário de outra equipe e RH de responsáveis seguem fora do escopo I15.

Branch `feat/s1-002-equipe-prumo`, PR #5 mantido **Draft**; sem merge, deploy, dados reais, migrations hospedadas, alterações noutras frentes ou elevação do progresso global.
