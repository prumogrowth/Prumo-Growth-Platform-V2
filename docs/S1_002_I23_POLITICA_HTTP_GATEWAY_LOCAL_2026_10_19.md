# S1-002/I23 — Auditoria da borda HTTP e contrato de operações (19/10/2026)

**Escopo:** apenas testes no GitHub da branch `feat/s1-002-equipe-prumo`, PR #5 Draft. Nunca executar este servidor em ambiente operacional. Sem mudança em migrations de produção, Supabase hospedado, clientes, Meta ou Google.

## Propósito e delimitação

I22 comprovou **33/33** provas de segregação entre `prumo_s1_i22_custodio` (HMAC/chaves) e `prumo_s1_i21_executor` (comandos/nonce) usando um servidor `http.server` demonstrativo. O I23 reforça especificamente a **fronteira HTTP** no mesmo perímetro local; não altera o validador GoTrue, a prova assinada, a transação PostgreSQL nem a governança I11/I13.

O novo `backend/s1_gateway_http_policy_local.py` é uma implementação *somente loopback e CI* com política fechada:

1. **Roteamento e métodos:** três URLs literais `POST /s1/mover`, `/s1/pausar`, `/s1/reativar`; nenhum query string, redirect, método GET, OPTIONS, PATCH, DELETE, PUT ou seleção SQL pelo cliente. Sem CORS e sem suporte a cookies; browser/SPA de produção exigirá desenho próprio de origem, CSRF e pré-flight.
2. **Host e proxy:** exigir Host literal da instância loopback, cliente loopback e rejeitar Host duplicado, `Forwarded`, `X-Forwarded-*`, `X-Real-IP`, `Proxy-Authorization` e `Transfer-Encoding` enviados pelo cliente. Essa decisão é válida **somente sem proxy confiável**; jamais presumir que cubra ambiente atrás de ingress.
3. **Identidade:** único cabeçalho Authorization com formato `Bearer` estrito; não se aceitam autorizações ambíguas, e a identidade continua validada pelo GoTrue + helper I15/052. Rejeição não invoca SQL/assinador.
4. **Body:** somente `application/json` literal, `Content-Length` único, corpo entre 2 e 1024 bytes, decodificação UTF-8, JSON objeto, sem campos JSON repetidos, `NaN`/`Infinity` ou outros valores não JSON. A whitelist por operação continua em `_fields`, antes de GoTrue/SQL.
5. **Respostas:** erros de autorização e falhas inesperadas sem SQL, DSN, token ou stack trace; `Cache-Control: no-store`, `Pragma: no-cache`, `X-Content-Type-Options: nosniff`, `CSP: default-src 'none'`, `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY`. Sem `Access-Control-Allow-Origin`.
6. **Limite simples:** contador in-memory por endereço remoto diretamente observado, com trava de thread. É **apenas controle de demonstração**: não distribuído, não resiste a múltiplos proxies, não garante cotas por usuário nem substitui WAF / rate limiting global.
7. **Auditoria:** apenas categoria fixa e comando allowlisted enviados ao `security_events.emit` opcional, sem corpo/JWT/segredo ou endereço de cliente. Falha da auditoria não transforma negação em aceite; produção requer sink durável, correlação e alertas.

## Plano de verificação

`tests/test_s1_002_i23_http_policy.py` executa 30 cenários de parsing/transporte com fake de domínio, isolando a política HTTP dos efeitos SQL; `scripts/test_s1_002_i23_http_e2e_local.py` reproduz as 33 provas I22 com GoTrue, 50 migrations reais S0/S1, assinatura HMAC, revogação e segregação, e acrescenta 7 testes de fronteira HTTP sobre **gateway real assinado**, assegurando que requests malformados não causem pausa.

## Requisitos operacionais ainda abertos: não copiar este servidor

| Área | Gate antes de qualquer deploy |
|---|---|
| Servidor e rede | Framework/servidor auditado com TLS e terminador confiável, timeouts robustos de cabeçalho/corpo, limitação de tamanho e conexões, WAF/gateway e identificação segura do peer; `http.server` é proibido |
| Sessões | Verificação GoTrue confiável, revogação de `auth.sessions` no banco, Bearer sem cookies salvo nova política de CSRF, política de origem/headers robusta |
| Chaves | Gerar fora do banco/CI; segredos entregues ao assinador por secret manager com escopo de leitura mínimo, sem chave no repo, logs ou cliente; TLS para banco e assinador |
| Rotação HMAC | Provisionar nova chave com ID e validade; trocar assinador apenas após confirmar disponibilidade no verificador; manter janela de sobreposição `≤` vida máxima da prova+skew; revogar chave antiga sob lock, alertar recusas, confirmar rollback/fail-close |
| Governança/observabilidade | Auditoria estruturada com categoria, código operacional permitido, request-id opaco e timestamp (nunca Bearer, HMAC, UUID de cliente), limites distribuídos, alarmes, métricas e retenção definida |
| Ownership DB | I20/I21/I22 são fixtures, não migrations; revisar SECURITY DEFINER I14, `EXECUTE`/USAGE, HMAC/nonce concorrente, escalonamento e segregação de custódia em Vault/KMS/HSM conforme plataforma |
| Testes de aceite pendentes | Autenticação UI real, gerentes/responsáveis e grants administrativos, escalas, transições S0 humanas, operações concorrentes em ambiente de homologação, recovery e chave comprometida |

**Parecer:** desenvolvimento em sandbox permitido, **NO-GO para produção/merge/deploy**. Um CI verde somente comprova os cenários listados; não representa auditoria externa nem comprova TLS, WAF, CSRF, multiinstância ou gestão operacional de segredos.

**CI I23:** preencher após conferir os dois jobs e logs; nunca anunciar aceite sem evidência.
