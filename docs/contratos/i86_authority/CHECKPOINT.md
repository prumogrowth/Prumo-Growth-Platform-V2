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
