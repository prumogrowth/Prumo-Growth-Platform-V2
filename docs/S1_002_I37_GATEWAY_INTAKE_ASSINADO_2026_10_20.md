# S1-002 / I37 — gateway gerencial assinado para pausa de ingresso (issue #10, 20/10/2026)

**Status: implementação de laboratório, aceite CI pendente.** PR #5 Draft em `feat/s1-002-equipe-prumo`, sem merge, deploy, Meta ou Supabase hospedado.

## Regra de negócio vigente

O gestor de equipe usa um único comando `POST /s1/intake`, com `operador_id`, `pausar` booleano e `versao_esperada` inteiro positivo. A pausa/retomada **não tem motivo obrigatório**, não suspende a conta, não remove acesso à plataforma, não revoga concessões e não altera titularidade de casos já iniciados. Todos os operadores pausados continuam podendo ler e responder nos casos que permanecem sob sua titularidade. O retorno da pausa/retomada contém `redistribution=DEFERRED_S0_PROOF`, deixando explícito que redistribuição seletiva não é sinônimo de aplicação da pausa.

A redistribuição automática é um fluxo **separado**, dependente de prova confiável S0 de que atendimento humano não começou, para colega ativo/disponível da **mesma equipe**, com concessão válida da loja. Sem substituto, caso permanece com titular. A mudança é local-only; não representar esse status como feature de produção já concluída.

## Cadeia técnica

- `backend/s1_gateway_intake_signed_local.py` aceita **somente** `intake`, valida exatamente três campos e tipos: UUID canônico, booleano verdadeiro/falso e versão PostgreSQL bigint positiva (tipo `bool` não aceito como inteiro). Confere token no GoTrue e monta prova HMAC da operação `INTAKE`, ator, session_id, operador, ação `P` ou `R`, revisão CAS, epoch e nonce UUID.
- `backend/s1_gateway_http_policy_local.py` agora aceita allowlist isolada `allowed_commands=("intake",)` na instância I37. Rotas legadas `/s1/pausar` e `/s1/reativar` retornam 404 no gateway I37, não uma pausa de conta. Conflito CAS recebe `HTTP 409\n{"outcome":"CONFLICT"}` sem expor versão de outro operador; os mesmos controles de Host, Bearer, tamanho, duplicação JSON, origens, rate-limit e loopback de I23 continuam ativos. Servidor de teste Python não é produção.
- `backend/s1_signer_mtls_authority_local.py` e `backend/s1_signer_process_local.py` reconhecem apenas a estrutura canônica extra `INTAKE|...|operador|P:versao/R:versao`, com versão dentro de 1..9223372036854775807 e GoTrue revalidado no processo separado que guarda o HMAC. A verificação de certificado TLS pelo witness I31 e autoridade I30 continua antecedendo assinatura. A assinatura é sobre campos todos, não cabe ao JSON alterar ação/versão fora da prova.
- `supabase/tests/s1_057_issue10_gateway_assinado_local_only.sql` cria uma única entrada estreita `prumo_s1_signed_i20.invocar_intake_v37`, **propriedade da role NOLOGIN `prumo_s1_i21_executor`**. Ela exige janela epoch, chama `verificar_hmac` do custodiante NOLOGIN I22, consome nonce uma única vez em tabela privada e, só então, chama ponte postgres-owned `s1_apply_intake_signed_v37`. A ponte reconfirma `auth.sessions` do GoTrue (com lock `FOR KEY SHARE`) e delega à regra de disponibilidade S1_053 com autorização de gestor/equipe e CAS. `authenticated`/anon/service_role não recebem execução de nenhuma rotina nova, e login assinado não recebe acesso às chaves, tabelas ou ao schema privado de negócio.
- A ponte reduz `22023` de versão obsoleta a `CONFLICT` sem vazar metadados de outro gestor, enquanto recusa de autorização ou HMAC inválida permanecem erros. Apenas retorno de sucesso ou idempotência tem `DEFERRED_S0_PROOF`.

## Escopo dos testes planejados

15 testes unitários novos `tests/test_s1_002_i37_intake_gateway.py` após 123 do I23–I31: whitelist exclusiva, campos estritos, versões inválidas, ação e revisão diferentes resultando em assinaturas HMAC diferentes, DSN loopback. Integração `scripts/test_s1_002_i37_intake_e2e_local.py` mantém os 132 cenários GoTrue+HMAC+mTLS+witness anteriores e soma **S1INTAKE-133..148**: fixture aplicada após regressão, pausa em conta ativa, concessões preservadas, replay idempotente, HTTP 409 para CAS obsoleto, gestor externo recusado, razão e tipos rejeitados, rotas legadas não publicadas, retomada, proof HMAC real e nonce consumido uma vez, adulteração da ação detectada pelo custodiante, ausência de mutação após falhas, revogação da chave do assinador e falha fechada se assinador estiver indisponível.

Workflow dedicado `.github/workflows/s1-002-i37-intake-signed-local.yml` preserva GoTrue/PostgREST reais **somente na stack Docker descartável**, 50 migrations e fixtures anteriores; **não** executa mudanças contra serviço remoto.

## Limitações / gates de produção e pausa para revisão

I37 **não** promove nenhuma fixture PG17 ISSUE10 a migration operacional, não cria botão no frontend, não comprova interação real Meta nem entrega de mensagens, não resolve anexo/projeções de outros microserviços. Token GoTrue é real no Docker de CI, não token hospedado. Signer/witness estão separados em processos mas compartilham runner e segredos sintéticos. A evidência de ausência de início humano segue sintética, e seleção de redistribuição permanece um segundo comando/contrato S0/S1 não incluído no ACK de pausa.

**Próximo marco planejado:** se os jobs passarem e a documentação de dependências for consistente, interromper novos incrementos funcionais para realizar as três atividades autorizadas: perguntas de alinhamento, auditoria geral S1/S0 e higiene/consolidação documental. Não promover para produção; NO-GO merge/deploy, sem porcentagem global.

## Evidências conferidas — homologado somente no sandbox

**[GitHub Actions #39526190841 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39526190841)**, SHA do **código testado** `bb1e61bb4bd9c0d65f1cc33d17530fe689a6c57c`. Os dois jobs concluíram em `success` e seus logs foram inspecionados:

- `118981274648` (`http-policy-unit`): **138/138 testes PASS** (123 I23–I31 + 15 I37), incluindo parser sem motivo, revisão estrita, HMAC que vincula ação/versão, e HTTP allowlist exclusivo.
- `118981274428` (`e2e-gerencia-local`): **S1WITNESS-01..132 = 132/132** e **S1INTAKE-133..148 = 16/16** marcadores distintos PASS, com migrations reais S0/S1, GoTrue real e PostgreSQL/PostgREST descartáveis, custódia I22, signer mTLS, autoridade MAC I30 e witness I31. Verificados: pausa autenticada sem suspender conta, grants intactos, resposta `DEFERRED_S0_PROOF`, idempotência, stale CAS `HTTP 409`, gestor cruzado recusado, payload sem motivo, rotas legadas não expostas, retomada sem suspensão de conta, comando assinado e commit, replay nonce recusado, adulteração HMAC bloqueada, ausência de mutação após falha, revogação de chave e indisponibilidade do assinador fechada.

**Falhas históricas corrigidas (não contabilizar como aceite):**
- [#39525595164](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39525595164) teve falha no novo teste unitário porque o UUID de exemplo possuía apenas dígitos; o teste pretendia avaliar rejeição de maiúsculas, mas `.upper()` não modificou o valor. Código/teste corrigido.
- [#39525804908](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39525804908) passou 138 unitários e os 132 E2E históricos, mas falhou na fixture I37 devido ao `GRANT EXECUTE` executado fora do contexto de proprietário da função. O DDL foi corrigido para a role dona `prumo_s1_i21_executor`, **sem conceder acesso direto a chave/nonce/negócio ao login SQL**.

**Parecer:** gateway I37 pronto para ser submetido ao **marco de alinhamento/auditoria/documentação da frente**, não para deploy. Código ensaiado no SHA identificado; commits posteriores de documentação não substituem nem invalidam esse SHA. O produtor S0 de prova humana real e a integração Meta/front permanecem pendentes; proteção de witness fora da conta do runner também.

