# Prumo — Gateway de menor privilégio e auditoria S0 (17/10/2026)

**Estado:** implementação **sintética e privada** no GitHub. Não existe servidor HTTP, instalação comercial no Supabase hospedado, conexão Meta/Banco ou autorização para produção.

## Escopo normativo

Decisões **D41-01 a D41-06** da matriz aprovada: identidade individual autenticada, gestor limitado às concessionárias vinculadas; operador atua apenas nos casos atribuídos; MCP inicial permite somente importar lote e atribuir/remanejar casos, com dupla confirmação do mesmo ator. **Este gateway NÃO é MCP.** Apenas viabiliza as funções internas simuladas de cancelamento C08 e reconciliação C07 já existentes. Não amplia as permissões comerciais aprovadas.

Documentos 26/39/40: ator de origem auditável; idempotência, versão, concorrência e isolamento; callbacks incertos não autorizam retry ou mudança de status comercial.

## Modelo de privilégios implementado

Migration `202610170023_s0_gateway_minimo_e_auditoria.sql`:

- Papel Postgres `prumo_s0_gateway`: **NOLOGIN/NOINHERIT** (não aceita autenticação direta) com USAGE do esquema não exposto `prumo_private` e EXECUTE apenas de **duas** funções de entrada controladas. O papel não recebe SELECT, INSERT, UPDATE, DELETE, acesso direto a `auth.sessions` ou EXECUTE nas funções comerciais originais.
- `prumo_private.gateway_cancelar_plano_s0` e `prumo_private.gateway_conciliar_c07_s0` são wrappers `SECURITY DEFINER`, **somente no esquema privado** e com `search_path=''`. Sua execução foi explicitamente revogada de PUBLIC, anon, authenticated e service_role. Ações verificam `auth.sessions(id,user_id)` sob lock; chamam as funções comerciais existentes, que revalidam o vínculo atual de gestor, loja, alvo, versão e estado.
- As wrappers são uma exceção intencional ao padrão `SECURITY INVOKER` porque as funções comerciais antigas estão restritas ao usuário `postgres`. Elas continuam de propriedade privilegiada; portanto **não tornam todo o banco de dados intrinsecamente imune a um servidor comprometido**. Uma futura revisão poderá substituir essa compatibilidade por funções de menor alçada sem elevação.
- `prumo_private.auditoria_gateway_s0` registra **somente comandos concluídos ou replays idempotentes**, na mesma transação que seu efeito: ator, **fingerprint SHA-256 da sessão**, loja, operação, alvo, versão e resultado (migração 024; a estrutura original da 023 guardava UUID bruto e foi corrigida posteriormente); **não armazena JWT, senha, CPF, telefone ou texto de atendimento**. Falhas rejeitadas fazem rollback e **não** ficam nessa tabela; a auditoria de recusas requer infraestrutura de logs segura própria. A tabela não é trilha criptograficamente imutável para o proprietário/admin do PostgreSQL.
- Uma credencial de login de aplicação **não é criada** pela migration. O teste integrado provisiona um login `prumo_gateway_ci` somente no ambiente local descartável, com senha sintética, e concede associação ao papel `prumo_s0_gateway`. Senhas reais devem vir futuramente de gestor de segredos fora do GitHub. Sem gestão segura de segredos/rotação não há deploy.

## Adapter Python

`backend/identity_boundary.py` acrescenta `PsycopgGatewayDatabase`. A fronteira continua obtendo ator pelo GoTrue confiável e rejeitando `ator_id` no corpo da operação, IDs/versões fora do contrato e SQL arbitrário. O novo adapter aceita DSN **apenas em loopback e base descartável** com login de prefixo `prumo_gateway_`, seleciona `SET LOCAL ROLE prumo_s0_gateway` dentro da transação e usa **SQL parametrizado fixo** para chamar as duas wrappers, transmitindo `actor_id` e `session_id` já verificados.

O `PsycopgTrustedDatabase` anterior permanece **somente por compatibilidade com testes S0** (uso local privilegiado); não é recomendado para implantação. Nenhum DSN de produção é aceito pelo novo adapter; uma versão hospedada exigirá arquitetura de credenciais e conectividade aprovada em gate separado.

## Critérios e evidência

- `supabase/tests/s0_gateway_privilegios.sql`: GW-01 nega leitura direta de leads/sessões/auditoria e execução da função original; GW-02 nega sessão cruzada e gestor de outra loja; GW-03 aplica os dois comandos por papel NOLOGIN via sessão simulada; GW-04 valida trilha de operações e replay; GW-05 verifica revogação da sessão sem nova escrita/auditoria.
- `backend/tests/test_identity_boundary.py`: testes do adapter para negar DSN/admin remotos, SQL não autorizado e usuário sem associação, sem expor segredos.
- `scripts/test_s0_auth_rest_local.py`: **AUTH-13** provisiona login sintético em Supabase local efêmero, testa login SQL limitado, bloqueio de leitura direta, identificação GoTrue, decisão autorizada por gestor, isolamento de outra loja, auditoria e recusa após revogar a sessão. Resultado real da CI indicado no arquivo `tests/S0_ACEITE.md`.

## Gates antes de produção

- Nenhum endpoint HTTP exposto. Construir proxy de autenticação seguro, proteção CSRF conforme arquitetura, TLS, rate limiting, registro de recusas sem dados pessoais, métricas sem tokens, rotação/isolamento de segredos, exceções genéricas e proteção contra brute force.
- **Modelo de service identity** ainda depende de revisão de autorização humana (D41-05/D41-06), controles do pool de conexões e análise de risco de `SECURITY DEFINER`; não usar a credencial `postgres` no runtime.
- Segurança funcional testada com dados sintéticos **não** significa permissões Meta/Banco, decisão DEC-13–18, base legal LGPD, retenção/recovery ou envio real.
- Respeitar cliente com mesmo telefone em A/B/C (histórico isolado); **emissor da Prumo exclusivo por loja**.
- **Proibido merge, migração ao Supabase hospedado, uso de dados reais e integração externa sem autorização específica.**

**Gate técnico:** GO apenas para continuar desenvolvimento e auditoria do sandbox; NO-GO para ambiente operacional.

## Resultado CI auditável

- [PostgreSQL 17 #39082041958 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39082041958): GW-01..05, 15 testes unitários e regressões S0.
- [Supabase local GoTrue/PostgREST #39082125663 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39082125663): AUTH-01..13 e AUTH-13-REVOKE. Papéis de aplicativo criados **somente** no banco efêmero da CI, sem alterações no hospedado. A etiqueta `run-auth-integration` foi retirada após o teste.

**Observação sobre segurança:** a função `SECURITY DEFINER` ainda constitui uma fronteira privilegiada. A senha sintética de teste está no roteiro CI e nunca é uma senha operacional. Não configurar autenticação desse papel em ambiente público sem desenho final de credenciais, revisão de funções e autorização humana.

## Auditoria corretiva posterior — 17/10/2026

- [PostgreSQL 17 #39082947695 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39082947695): **GW-01..GW-07** e 16 testes unitários. Migration 024 substitui UUID bruto da sessão pelo fingerprint SHA-256 no registro; wrappers continuam exigindo sessão ativa para autorização. Proprietário, EXECUTE e ausência de DML na auditoria foram explicitamente revalidados.
- O login do gateway restrito **não** é suficiente para autenticar o usuário sozinho: as wrappers recebem `p_ator/p_sessao` e só verificam que o par existe. Uma credencial SQL comprometida mais um par válido permitiria contornar o GoTrue do backend. **NO-GO para produção** até arquitetura revisada, proteção/rotação de segredo e threat model.
- Ver análise detalhada: `docs/AUDITORIA_GATEWAY_S0_2026_10_17.md`. Suíte Auth/REST integrada da migração 024 ainda não foi repetida para poupar minutos; baseline 023 previamente aprovado.

## Evolução posterior — assinatura obrigatória (18/10/2026)

A migração 025 removeu o EXECUTE do papel `prumo_s0_gateway` nas wrappers legadas sem assinatura, mantendo-as apenas para uso interno pelo proprietário. O gateway agora possui EXECUTE somente nas entradas `gateway_cancelar_plano_assinado_s0` e `gateway_conciliar_c07_assinado_s0`. Os novos comandos exigem HMAC-SHA256 separado do login SQL, validade curta e nonce único; ainda revalidam sessão e gestor. Os testes SQL/GoTrue passaram em [#39083792469](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39083792469) e [#39083914275](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39083914275).

O risco anterior de **login SQL + par ator/sessão** foi mitigado para uso sem HMAC válido; permanece **NO-GO** contra comprometimento conjunto de senha SQL e segredo HMAC, e `SECURITY DEFINER` continua privilegiada. Arquitetura detalhada em `docs/GATEWAY_PROVA_DUPLA_S0_2026_10_18.md`.
