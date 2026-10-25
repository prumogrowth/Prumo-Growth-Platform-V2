# CI/S1 — inventário objetivo de redundância e limite do experimento

Data: 2026-10-25. Somente análise de arquivos GitHub Actions em `exp/ci-s1-consolidacao-20261025` (fonte congelada S1 no commit `1b56375739017eeb5f3608f1bad2b294eb6c89dc`).

## Achado em 12 workflows I21–I31 e I37
- **12** workflows possuem inicialização própria de `supabase start`, com GoTrue/PostgREST locais descartáveis.
- **50** invocações explícitas de suítes unitárias `python3 -m unittest discover`; **13** nomes de arquivos de teste distintos. Repetição pode ser intencional, mas custa preparação e execução adicionais.
- Invocações cumulativas especialmente repetidas: I23 em 10 workflows; I25 em 8; I26 em 7; I27 em 6; I28 em 5; I29 em 4; I30 em 3; I31 em 2.
- Cada workflow da amostra também executa um **script E2E próprio**, e esses cenários **não devem ser omitidos** só porque outra suíte unitária os referencia.

## Prova controlada I27/I28
Experimento: `.github/workflows/exp-s1-i27-i28-serial.yml`, branch experimental somente.

| Item | Atual, dois workflows independentes | Candidato |
|---|---|---|
| `test_s1_002_i23_http_policy.py` | 2 invocações | 1 |
| `test_s1_002_i25_signer_process.py` | 2 | 1 |
| `test_s1_002_i26_independent_auth.py` | 2 | 1 |
| `test_s1_002_i27_mtls.py` | 2 | 1 |
| `test_s1_002_i28_cert_lifecycle.py` | 1 | 1 |
| I27 E2E | 80 marcadores e cenários da suíte I27 | **80/80 exigidos** |
| I28 E2E | 93 marcadores e cenários da suíte I28 | **93/93 exigidos** |
| Ambiente de autenticação e PostgreSQL | Um banco descartável por suíte | **Um banco descartável por suíte**, para impedir falso positivo por estado compartilhado |
| Ferramenta CLI, `pip`, checkout | Inicialização repetida em jobs diferentes | Preparação única em um job |

Base histórica pontual para comparação: commit `c50af9de`, workflows I27 [40193208331](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40193208331) e I28 [40193208343](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40193208343). Juntos: **4 jobs, aprox. 5,55 runner-minutes** calculados por diferença de timestamps de jobs (não minutos faturados). A comparação final exigirá testes em SHA idêntico e mais de uma execução de cada candidato.

## Cuidados
- **Não** compartilhar o mesmo banco entre suítes. Scripts E2E reaplicam migrations e criam as mesmas contas/evidências; repetir sem limpeza invalidaria o ensaio.
- **Não** considerar esta prova restrita a I27/I28 como validação dos 12 workflows nem como autorização de desligar os originais.
- Se o experimento falhar ou não economizar tempo, manter fluxo original; investigar consolidação apenas dos testes unitários ou geração automática de relatório.
- As frentes permanecem isoladas; sem escrita em `feat/s1-002-equipe-prumo`, `main` ou qualquer outra frente.

**Estado:** experimento submetido ao GitHub Actions; resultado a conferir. Não há certificação de economia ainda.
