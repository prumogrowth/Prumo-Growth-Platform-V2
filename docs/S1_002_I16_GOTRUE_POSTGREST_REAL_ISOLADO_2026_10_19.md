# S1-002/I16 — Ensaio integrado GoTrue + PostgREST em stack local (19/10/2026)

**Fronteira:** implementação de **testes de integração**, sem migration de produção, sem alterar políticas de equipe, sem expor `prumo_s1_interface` na Data API. Respeita a decisão I11: o gestor administra operadores da equipe e as concessões A/B/C continuam reservadas aos responsáveis.

## Objetivo

Complementar a evidência fake-auth do PostgreSQL 17 (I14/I15) com um teste efetivo de **login GoTrue, JWT assinado, HTTP PostgREST e exclusão de sessão**. `auth.sessions` e `auth.uid()` são os objetos reais do Supabase local; os scripts I16 não criam versões fictícias deles.

## Arquivos

- `.github/workflows/s1-002-auth-real.yml`: job segregado em GitHub Actions, com CLI Supabase fixada em `2.84.2` e Docker local. Usa diretório temporário, `supabase init`, `supabase start` com serviços não necessários excluídos e `supabase stop`; nenhuma chave ou senha comercial.
- `supabase/tests/s1_016_integracao_gotrue_fixture.sql`: **somente fixture do job**; cria `public.atores` mínima e três stubs para as dependências internas do I14, sem lógica comercial ou concessões.
- Migrations **reais** `051` e `052` são reaplicadas no banco local pela suíte, em ordem.
- `supabase/tests/s1_016_integracao_gotrue_probe.sql`: RPC **canário** de teste em `public` que chama **apenas** `prumo_private.s1_exigir_identidade_sessao()`, sem operações humanas. Esse canário é um objeto de teste, **não faz parte das migrations** e nunca deve ser implantado.
- `scripts/test_s1_002_real_auth.py`: 13 verificações via HTTP/SQL, com travas de ambiente (`CI=true`, `PRUMO_S1_I16_EPHEMERAL=YES`, URLs estritamente loopback e banco local `postgres`).

## Cenários planejados

1. GoTrue real efetua cadastro/login e retorna JWT com `role`, `sub` e `session_id`.
2. Sessão emitida consta em `auth.sessions` real.
3. Token de login real permite canário autenticado: helper 052 devolve o ator da sessão.
4. `anon` não executa o canário.
5. `service_role` não executa o canário.
6. Assinatura adulterada bloqueada pelo gateway.
7. Claims alteradas sem reassinatura bloqueadas.
8. Três fachadas I14 ausentes do schema público da API.
9. Tentativa de selecionar o schema `prumo_s1_interface` bloqueada pelo PostgREST.
10. `authenticated` mantém isolamento de `prumo_private` e não possui SELECT em `auth.sessions`.
11. Logout GoTrue remove a sessão.
12. JWT original ainda não expirado é rejeitado pelo helper depois do logout.
13. Novo login gera nova sessão e restaura acesso autenticado ao canário.

## Escopo probatório — estrito

Este ensaio **não executa movimentação ou pausa por HTTP**: a interface privada continua deliberadamente **não exposta** e as funções de negócios são stubs apenas na fixture. Regras de chefe/operador, concorrência e redistribuição seguem validadas pelas regressões PostgreSQL 17 separadas. Não simula HMAC forjado no PostgreSQL; usa a assinatura JWT do GoTrue e a verificação do PostgREST reais. Não prova expiração por relógio, refresh, MFA, sessão de usuário anônimo autenticado, escalabilidade ou políticas de gateway final. Não certificar produção com base exclusivamente neste teste.

**Implantação:** proibida. PR #5 permanece Draft, sem merge, Supabase hospedado, alteração de branches alheias, Meta, banco ou mudança de percentual de progresso global.

## Resultado da execução

**[GitHub Actions #39327934437 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39327934437)**, commit de código testado `11c82085068d0ab6825927960508d39b6efee87b`, job `118318490278`. Logs inspecionados: **S1HTTP-01..13 = 13/13 PASS**, sem erros inesperados nos marcadores e com teardown da stack concluído. GoTrue assinou JWT real; PostgREST chamou o helper privado **real** da migration 052 através de RPC canário criada apenas na fixture; assinatura e claims forjados bloqueados; `anon` e `service_role` sem acesso; `prumo_s1_interface` não exposto; logout removeu a linha de `auth.sessions` e impediu o uso do JWT ainda não expirado; novo login foi aceito.

**Limitação técnica explícita:** não foi exercitada uma pausa/reativação/movimentação verdadeira por HTTP, pois as três fachadas I14 permanecem não expostas; as dependências internas dessas fachadas são **stubs** nessa suíte. Não houve prova de `exp` com relógio, tokens assimétricos/JWKS, refresh, MFA, carga ou integração S0 real. As regressões da lógica de equipe continuam em CI PG17 separado. Nenhum serviço Supabase hospedado foi alterado.
