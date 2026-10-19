# S1-002/I19 — Gateway de gestão local sem RPC pública (19/10/2026)

**Estado:** candidato exclusivamente em **CI com Supabase descartável**; não é gateway homologado de produção. Mantém PR #5 Draft. Não se alteram migrations de produção, roles existentes, Supabase hospedado, frontend ou lógica I11/I13.

## Por que o I19 existe

O I18 provou a execução das operações gerenciais reais por HTTP, mas precisou criar pontes temporárias `SECURITY DEFINER` em `public`. Essas pontes nunca são adequadas ao ambiente operacional. O I19 substitui a topologia do teste por uma camada local privada: navegador de teste -> serviço gateway loopback -> validação GoTrue `/auth/v1/user` -> conexão SQL limitada -> fachadas `prumo_s1_interface` não expostas.

O adapter `backend/s1_gateway_local.py` reutiliza `SupabaseGoTrueVerifier` já auditado no S0, valida JWT via GoTrue confiável e extrai `actor_id/session_id` somente da identidade devolvida; recusa qualquer `actor_id`, `session_id`, SQL ou role no corpo. Define GUC `request.jwt.claims` e `request.jwt.claim.sub` **somente depois** de verificação GoTrue, numa transação Postgres, para invocar uma das três assinaturas allowlisted I14/051 que usam o helper I15/052. O cliente não seleciona a função SQL, a role, o sujeito, a sessão nem o contexto JWT. SQL usa parâmetros, `SET LOCAL ROLE authenticated` e rollback transacional normal. A conexão é exclusivamente `prumo_s1_gateway_ci`, em loopback/`postgres`; o teste cria essa role efêmera com somente a capacidade de assumir `authenticated`, não `postgres`.

O arquivo `scripts/test_s1_002_gateway_local.py` usa as **50 migrations S0/S1 reais**, GoTrue e `auth.sessions` da stack, cinco usuários fictícios e as mesmas invariantes operacionais do I18. Verifica negação por outra chefia, replay, pausa global e redistribuição da loja B sem alterar concessões A/B, retorno sem recuperar carteira, JWT após logout, campos não autorizados, `service_role` e ausência de RPC de teste I18.

## Limitação de segurança NÃO RESOLVIDA

**A conexão SQL da aplicação é uma fronteira diferente da sessão GoTrue.** O papel `prumo_s1_gateway_ci` pode assumir `authenticated` e definir os próprios GUC `request.jwt.claims`; em caso de comprometimento do login SQL, um invasor que obtenha `sub/session_id` de sessão vigente pode reproduzir contexto autenticado sem passar pelo GoTrue. A simples leitura de `auth.sessions` e a conferência dos GUC por helper 052 não fornecem prova criptográfica de que o contexto foi estabelecido por um componente confiável. Portanto **NÃO classificar I19 como gateway definitivo ou pronto para produção**.

A evolução obrigatória, à semelhança da segurança S0/025, é introduzir uma prova independente (HMAC/assinatura ligada a operação, ator, sessão, alvo, timestamp curto e nonce de uso único) validada dentro do banco, de preferência com role e ownership de menor privilégio. Credencial SQL e segredo de assinatura devem ter domínios independentes; proteger contra vazamento conjunto permanece requisito de operação. Além disso, auditar logs de negativas sem tokens, rate limiting, TLS, CSRF caso passe a utilizar cookies, restrição de rede, segurança de segredos, controle de custos, provisionamento de responsáveis e integração UI/S0.

## Gates e governança

- `backend/s1_gateway_local.py` **não** é servidor operacional; `http.server` serve apenas o smoke test na interface loopback e não oferece hardening web.
- A role de teste e senha sintética são criadas **somente** no banco descartável no CI; não transportar para Supabase hospedado.
- Nenhuma RPC nova em `public` e `prumo_s1_interface` nunca adicionada à Data API.
- O S0 já dispõe de prova dupla assinada mais forte; nenhuma alteração ou regressão ao S0 é autorizada por I19.
- Sem merge, deploy, tráfego de terceiros ou ampliação do progresso global.

**CI e marcadores:** pendentes de inspeção antes do registro de aceite.
