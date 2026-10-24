# WA-48 — Laboratório PG17 de identidade de máquina limitada

Execução apenas no banco descartável prumo_s0_test_ci. Nenhum deploy, token real, Meta Graph, ACK, merge ou S1.

## Implementação

O arquivo 202610230047_s0_meta_shadow_non_superuser_fixture.sql cria executor PostgreSQL NOLOGIN e NOSUPERUSER, cliente com login temporário de laboratório e tabelas-sombra separadas. O executor SECURITY DEFINER verifica HMAC S0/044, expiração, revogação e nonce no mesmo contexto transacional que o registro forense sombra. O cliente não possui SELECT de segredos nem INSERT direto das tabelas; a resposta não concede autorização comercial.

O teste s0_wa_052_assert_non_superuser_pg17.py valida login com senha criada na execução, papéis limitados, rollback, replay, duas sessões concorrentes, adulteração, revogação, bloqueio de permissões e isolamento do caminho original.

## Limites

A função de arquivamento WA40 original permanece sob postgres. O novo caminho NÃO valida os bindings autoritativos S0 ou regras S1 e não é endpoint de produção. Identidade de login PostgreSQL local não comprova IAM produtivo. Os dados são sintéticos. Somente CI do mesmo HEAD pode certificar as provas.

Próxima etapa: migração gradual da operação forense existente para papéis escopados, com consulta de vínculos autoritativos e contrato interfrentes de locks e autenticação.