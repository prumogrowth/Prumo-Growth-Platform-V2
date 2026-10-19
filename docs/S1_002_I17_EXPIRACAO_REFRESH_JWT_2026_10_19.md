# S1-002/I17 — Expiração JWT e refresh em GoTrue/PostgREST descartáveis (19/10/2026)

**Status:** código de testes proposto; considerar validado **somente após** inspecionar os logs do novo CI. Nenhuma migration de produção, nenhuma API gerencial publicada, PR #5 permanece Draft.

## Continuidade após I16

I16 validou login GoTrue, assinatura e revogação contra `auth.sessions` num canário da função privada I15, mas não cobriu JWT vencido com **assinatura ainda correta**, a manutenção de `session_id` após refresh e o bloqueio de versões antigas do JWT após logout.

I17 amplia **apenas** `scripts/test_s1_002_real_auth.py` e reutiliza a stack local da suíte I16. O runner `.github/workflows/s1-002-auth-real.yml` continua isolado, com CLI Supabase pinada, URLs loopback e teardown. O segredo da stack `JWT_SECRET` vem do comando local `supabase status -o env`; é efêmero e **não pode ser impresso**. O teste compara a assinatura de JWT verdadeiro emitido pelo GoTrue à chave efêmera antes de fabricar cenários; dessa forma não se produz um falso positivo causado somente por HMAC errado.

## Casos I17 planejados (S1JWT-01..08)

1. Confirmar assinatura **HS256 verdadeira** emitida pelo GoTrue com a chave local efêmera.
2. Reassinar uma variação de JWT com `exp` no passado e a **mesma sessão existente**; PostgREST deve negar com HTTP 401.
3. Reassinar JWT com `session_id` inexistente e `sub` correto; helper 052 deve negar mesmo se a assinatura for válida.
4. Reassinar JWT com `sub` de outro ator (que existe em `public.atores`) e `session_id` do ator original; a vinculação de `auth.sessions.user_id` deve negar.
5. Trocar `refresh_token` verdadeiro com GoTrue por novo JWT e confirmar `sub`/`session_id` originais.
6. PostgREST e helper I15 devem aceitar o JWT renovado da mesma sessão.
7. Logout remove a sessão e faz helper negar **tanto token original como token renovado**.
8. Confirmar que o ensaio não ampliou ACL do schema privado, `auth.sessions` nem RPC canário a `anon`/`service_role`.

**Limitações:** assinatura HS256 e chave de teste são exclusivas do Supabase local pinado, não equivalem a prova ES256/JWKS ou segurança contra vazamento de chaves de produção. Manipular e reassinar JWT é uma técnica de teste privilegiado **somente em CI efêmero**; não adiciona capacidade de assinatura à aplicação. A RPC canário `public.s1_i16_prova_sessao` existe apenas no banco de testes e não é migration. I17 não executa pausa, movimento ou reativação reais via HTTP; governança I11 e concorrência seguem provas separadas em PostgreSQL 17 sintético.

**Segurança:** sem Supabase hospedado, produção, dados reais, merge, ou alteração do progresso global. Permanecem pendentes gateway de autorização definitivo, assinatura assimétrica, política para profissionais responsáveis, conclusão humana S0 e interface gerencial.

Referências: [Sessões Supabase](https://supabase.com/docs/guides/auth/sessions), [Comando `supabase status`](https://supabase.com/docs/reference/cli/supabase-status), [I16](S1_002_I16_GOTRUE_POSTGREST_REAL_ISOLADO_2026_10_19.md).
