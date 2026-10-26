# I74 — assinatura independente e replay atômico do executor exportador

**Escopo**: S1-002 apenas, branch `feat/s1-002-equipe-prumo`, laboratório descartável (26/10/2026). I73 certificada é pré-requisito. Sem migração hospedada, alteração de `main`, deploy, Issue #3 ou alteração de contrato oficial S0.

## Problema

Na I73 o login SQL ainda tinha membership SET ROLE para `prumo_s1_export_executor`. A obtenção das credenciais desse login permitiria falsificar o contexto GUC, chamar a RPC invocadora diretamente e registrar reservas, independentemente do gateway GoTrue.

## Solução candidata implementada

A fixture `s1_108` **revoga** a membership do antigo login I73. Cria `prumo_s1_export_signed_login_ci` sem membership em `authenticated` ou executor, apenas com `USAGE` no schema privado e `EXECUTE` na função `prumo_export_auth.exportar_assinado_i74`. A função é `SECURITY DEFINER` **privada** e de propriedade da role `prumo_s1_export_executor` (não postgres), sujeita a RLS comercial existente quando executa a RPC I71 `SECURITY INVOKER`. Usuários finais, papéis anon e service_role não têm acesso.

A chamada exige HMAC-SHA256 válida, identificador de chave ativa, timestamp limitado, ator, sessão, tipo, loja, cursor, limite e nonce, todos incluídos no material canônico `prumo-s1-i20-v1|EXPORT74|...`. O nonce é consumido por INSERT sob chave única **na mesma transação** da reserva e exportação. Se a assinatura ou sessão ativa falhar, nenhuma reserva é registrada. Segredo HMAC e nonces ficam em tabelas privadas com RLS; somente a função defensiva com owner restrito tem acesso.

`backend/s1_signer_process_local.py` reconhece a operação `EXPORT74` no assinador I26, processo separado que valida autonomamente o JWT em GoTrue antes de assinar; a chave não integra o objeto gateway. `backend/s1_gateway_export_signed_local.py` aceita somente o contrato de exportação, verifica GoTrue, obtém assinatura por IPC e invoca a função privada por SQL parametrizado. Não publica HTTP.

## Arquivos e fronteira com S0 / Codex

Arquivos S1 novos:
- `supabase/tests/s1_108_export_signed_executor_local_only.sql`, `s1_109_export_signed_executor_aceite.sql`;
- `backend/s1_gateway_export_signed_local.py`, `scripts/test_s1_002_i74_signed_export_e2e.py`, `tests/test_s1_002_i74_export_signed.py`.

Arquivos S1 alterados: `backend/s1_signer_process_local.py`, runner PostgreSQL sintético `s1_090_s0_indirect_read_boundary_aceite.sql`, driver E2E I73 e workflow da própria frente. **Nenhuma migration e nenhum arquivo pertencente ao núcleo S0 modificados.** Contrato S0 consumido: verificação de vínculos e RLS do Gestor/concessionária, dados de exportação do domínio e `auth.sessions`. Para promover, o Codex/S0 deve revisar o ponto de integração, padrões de segurança, rate limit, retenção, LGPD e eventuais alterações concorrentes no núcleo.

## Segurança residual e critérios de certificação

O laboratório protege contra vazamento isolado das credenciais do login SQL, não contra invasão conjunta do processo assinador e da conta SQL, roubo de JWT, comprometimento do host/OS, administração do PostgreSQL ou acesso ao segredo em custódia. O assinador por IPC local não é HSM/KMS, os testes não habilitam TLS operacional na borda e o segredo de ensaio é efêmero.

Critérios: PostgreSQL 17 **6 provas**, GoTrue real + PostgREST **8 provas**, regressões antigas sem falhas, log explícito confirmando a execução (não apenas job verde), e rollback no ensaio PG17. **Certificação pendente da execução do CI.**
