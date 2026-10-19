# S1-002/I17 — Expiração JWT e refresh em GoTrue/PostgREST descartáveis (19/10/2026)

**Status:** código de testes proposto; considerar validado **somente após** inspecionar os logs do novo CI. Nenhuma migration de produção, nenhuma API gerencial publicada, PR #5 permanece Draft.

## Continuidade após I16

I16 validou login GoTrue, assinatura e revogação contra `auth.sessions` num canário da função privada I15, mas não cobriu JWT vencido com **assinatura ainda correta**, a manutenção de `session_id` após refresh e o bloqueio de versões antigas do JWT após logout.

I17 amplia **apenas** `scripts/test_s1_002_real_auth.py` e reutiliza a stack local da suíte I16. O runner `.github/workflows/s1-002-auth-real.yml` continua isolado, com CLI Supabase pinada, URLs loopback e teardown. O segredo da stack `JWT_SECRET` vem do comando local `supabase status -o env`; é efêmero e **não pode ser impresso**. O GoTrue da stack observada em CI não emite necessariamente JWT HS256. O teste não tenta reassinar um JWT assimétrico com segredo HMAC: fabrica token HS256 **somente com a chave efêmera legacy local**, e exige primeiro que PostgREST aceite esse token vinculado à sessão real, como testemunha positiva. Assim, a negação do token expirado não pode ser confundida com rejeição de assinatura inválida.

## Casos I17 planejados (S1JWT-01..08)

1. Confirmar via HTTP que PostgREST aceita o token **HS256 de teste** assinado com segredo legado efêmero, baseado nas claims de um login GoTrue real (testemunha positiva de validação de assinatura).
2. Reassinar uma variação de JWT com `exp` no passado e a **mesma sessão existente**; PostgREST deve negar com HTTP 401.
3. Reassinar JWT com `session_id` inexistente e `sub` correto; helper 052 deve negar mesmo se a assinatura for válida.
4. Reassinar JWT com `sub` de outro ator (que existe em `public.atores`) e `session_id` do ator original; a vinculação de `auth.sessions.user_id` deve negar.
5. Trocar `refresh_token` verdadeiro com GoTrue por novo JWT e confirmar `sub`/`session_id` originais.
6. PostgREST e helper I15 devem aceitar o JWT renovado da mesma sessão.
7. Logout remove a sessão e faz helper negar **tanto token original como token renovado**.
8. Confirmar que o ensaio não ampliou ACL do schema privado, `auth.sessions` nem RPC canário a `anon`/`service_role`.

**Limitações:** o token positivo de teste HS256 não é o JWT assimétrico emitido pelo GoTrue (que continua sendo testado pelo I16); ambos são verificados pelo mesmo PostgREST local, mas apenas o segundo representa token GoTrue de usuário. O segredo HS256 e a chave de teste são exclusivos do Supabase local pinado, e não equivalem a prova de rotação ES256/JWKS nem segurança contra vazamento de chaves de produção. Manipular e reassinar JWT é uma técnica de teste privilegiado **somente em CI efêmero**; não adiciona capacidade de assinatura à aplicação. A RPC canário `public.s1_i16_prova_sessao` existe apenas no banco de testes e não é migration. I17 não executa pausa, movimento ou reativação reais via HTTP; governança I11 e concorrência seguem provas separadas em PostgreSQL 17 sintético.

**Segurança:** sem Supabase hospedado, produção, dados reais, merge, ou alteração do progresso global. Permanecem pendentes gateway de autorização definitivo, assinatura assimétrica, política para profissionais responsáveis, conclusão humana S0 e interface gerencial.

Referências: [Sessões Supabase](https://supabase.com/docs/guides/auth/sessions), [Comando `supabase status`](https://supabase.com/docs/reference/cli/supabase-status), [I16](S1_002_I16_GOTRUE_POSTGREST_REAL_ISOLADO_2026_10_19.md).

**Ensaio inicial não aceito:** [CI #39329660951](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39329660951) confirmou I16 13/13, mas falhou antes do I17 ao exigir incorretamente que o JWT emitido pelo GoTrue fosse HS256. A suíte foi corrigida; a falha não demonstrou acesso indevido e não conta como validação I17.
