# I86 — checkpoint de desenvolvimento e evidências

28/10/2026, America/Sao_Paulo. Estado inicial: I86_LAB_BLOCKED, provas físicas
ainda não executadas. Nenhum PASS de integração é inferido das unidades.

Base: 3cab3d57619cc1157698a08ac26f34e0c363f6dd, tree
09e597b763bd6026fe6fb9686e3471e42f87bd3a.
Branch: exp/s1-i86-governanca-autoridade-20261028.

Implementação experimental: verificador de escopo obrigatório, diagnóstico
transacional da competência ordinária, evidências SQL privadas/idempotentes,
gates de governança PENDING_DECISION, provas reais e cópia exata em runner
exclusivo para não sujar fontes protegidas com estado do CLI.

Unidades locais: 11 de escopo e cinco de DTO/modelo já passaram; SQL aceito pelo
parser PostgreSQL. Isso não é execução SQL nem E2E. CI, resultados finais,
artefatos, hashes, manifesto, matriz de regressão e recomendação serão
registrados aqui somente após execução efetiva.

Decisões externas D01–D05 e novas operações de nomeação/substituição/reativação/
revogação organizacional continuam bloqueadas. A I85 não se torna rebootstrap.
Sem merge, deploy, usuário real, Supabase hospedado ou incorporação Meta.

Primeira rodada CI40731027793: gate de escopo/modelos PASS, mas ambos os jobs físicos falharam na preparação. Invocação do preflight por caminho de script em uma cópia isolada não incluiu a raiz no import path (ModuleNotFoundError: integration). Zero casos reais executados; não houve PASS físico. A correção usa a mesma ferramenta herdada por python -m, sem editar I83. O hash SQL passa a usar sha256 nativo PG17, eliminando suposição desnecessária sobre o schema de pgcrypto; a semântica do digest é a mesma. Limpeza acrescenta hash de identidade física, sem revelar credenciais.
