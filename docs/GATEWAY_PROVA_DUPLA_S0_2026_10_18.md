# Prumo — Gateway S0 com prova HMAC e nonce único (18/10/2026)

**Estado:** protótipo interno para desenvolvimento e testes **exclusivamente locais**; não há endpoint público, migrações comerciais no Supabase hospedado, login operacional nem chave real provisionada.

## 1. Por que esta alteração existe

A auditoria `docs/AUDITORIA_GATEWAY_S0_2026_10_17.md` identificou risco alto: as wrappers `SECURITY DEFINER` (migration 023) aceitam `ator_id` e `session_id` e só conferem que os dois formam uma sessão ativa. Quem roubasse a credencial SQL do gateway e soubesse um par de IDs ativo poderia invocar diretamente a função, **contornando GoTrue**. A restrição de escopo do gestor e do cliente multiloja continua necessária, mas não era defesa suficiente contra esse cenário.

## 2. Modelo incremental e limites

Migration **025** adiciona uma barreira **distinta da credencial de conexão SQL**:
- Tabela privada `gateway_chaves_assinatura_s0`: chaves HMAC-SHA256 com ID, janela de validade, flag de ativação e mínimo 32 bytes. A migration cria a estrutura **vazia**; nenhum segredo real é incluído no GitHub.
- `gateway_provas_usadas_s0`: registro transacional de UUID nonce de uso único. Uma prova idêntica não pode autorizar duas operações; uma nova prova permite que a idempotência comercial retorne `ALREADY_APPLIED`.
- `gateway_material_assinatura_s0`: codificação fixa `prumo-gw-v1` que vincula operação, ator, sessão, loja, alvo, versão, decisão, SHA-256 da justificativa, envio correlato, instante e nonce. A versão Python produz exatamente os mesmos bytes UTF-8.
- `gateway_validar_prova_s0`: valida HMAC com `pgcrypto`, origem da chave na tabela privada, validade de no máximo 30s (e 5s de tolerância para relógios), assinatura e nonce. Só após essa validação a wrapper assinada executa a função antiga de domínio, que continua revalidando **sessão ativa, gestor, loja, alvo e versão**.
- Duas entradas assinadas, com ACL restrita ao `prumo_s0_gateway`: `gateway_cancelar_plano_assinado_s0` e `gateway_conciliar_c07_assinado_s0`. **REVOKE da execução das wrappers antigas pelo gateway.**
- O `PsycopgGatewayDatabase` local agora exige `key_id` e `signing_key` separados do DSN restrito. Somente depois de `SupabaseGoTrueVerifier` verificar o usuário e a sessão ser validada pelo banco, a assinatura permite a mutação.

## 3. Limites explícitos de segurança

- Comprometimento **apenas da senha SQL** deixa de bastar para forjar operação sem a chave HMAC. **Comprometimento simultâneo da senha SQL e da chave HMAC continua crítico**; isolamento de segredos, rotação e runtime dedicado precisam de revisão independente.
- O material assinado é uma **autorização interna de comando**, não um JWT do Supabase, não um token para a Meta e não prova de consentimento do cliente.
- A proteção não resolve automaticamente: `SECURITY DEFINER` de propriedade `postgres`, log externo de recusas, armazenamento/rotação de segredos, retenção e poda dos nonces, recovery, TLS, limite de requisições, disponibilidade ou backup.
- **Não usar HMAC de testes em produção.** Os testes usam chave fixa sintética de 32 bytes, declarada explicitamente **só nas fixtures**; a migration não grava chaves nem cria login.
- Funções assinadas e tabelas de segredo ficam em `prumo_private` (não exposto pela Data API). O papel gateway não ganha SELECT/INSERT nas tabelas privadas e não pode chamar funções antigas sem prova.
- Regras de negócio intactas: cliente pode ter mesmo telefone em concessionárias A/B/C com históricos segregados, emissor Prumo exclusivo por loja. Nenhuma integração Meta/Banco/OpenAI/n8n, envio, retry automático, mudança comercial ou MCP foi acionada.

## 4. Testes e gates

`supabase/tests/s0_gateway_privilegios.sql` cobre senha SQL isolada, HMAC inválido, versão alterada, validade expirada, nonce reutilizado, idempotência comercial com novo nonce, sessão revogada, trilha transacional, owner/ACL e bloqueios de leitura de segredos. `backend/tests/test_identity_boundary.py` cobre assinatura canônica e negativa de chave ausente. `AUTH-14` foi acrescentado ao teste GoTrue/PostgREST descartável para negar chamada SQL às wrappers legadas e nova chamada sem HMAC.

**Gate 1 — PostgreSQL e testes unitários:** registrar resultado do workflow mais recente na prova `tests/S0_ACEITE.md` (antes de declarar sucesso).

**Gate 2 — GoTrue/REST integrado:** executar **uma vez**, via etiqueta explícita `run-auth-integration`, após estabilizar migrations e testes; nenhuma execução automática a cada commit. Até esse marco, `AUTH-14` estará apenas escrito, não aprovado.

**Gate de produção: NO-GO**, mesmo após testes locais, até revisão de ameaça de comprometimento combinado, funções privilegiadas, segregação dos segredos, política de rotatividade, logs de negativas, LGPD/retensão e autorização humana específica para homologação e eventual implantação.

## Evidências finais (18/10/2026)

**[PostgreSQL 17 #39083792469 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39083792469):** GW-01..07, 18 testes unitários e regressões anteriores. Primeira tentativa da migration 025 falhou pela sintaxe SQL de `EXTRACT`; a função foi corrigida antes do PASS.

**[Supabase local GoTrue/PostgREST #39083914275 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39083914275):** AUTH-01..14, incluindo verificação de credencial SQL sem assinatura e replay autorizado com nonce novo, sessão revogada e isolamento. Teste foi acionado uma única vez por etiqueta, retirada após conclusão. Projeto Supabase hospedado não recebeu tabelas, chaves ou migrations comerciais.

**Limite da conclusão:** dois fatores técnicos na mesma aplicação não fornecem independência se o processo for inteiramente comprometido. O novo desenho contém o cenário de roubo **apenas da credencial SQL**, não certifica proteção contra comprometimento do runtime, contra administrador PostgreSQL, ou operação real.
