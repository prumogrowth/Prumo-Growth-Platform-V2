# FVA-01 — Auditoria cruzada de jornadas e segregação visual

**26/10/2026 · Frente visual Prumo · branch `feat/frontend-plataforma-visual`**.

## Objetivo e escopo da execução

Abrir a etapa FVA definida em `88_FV_UI_059_FECHAMENTO_CRITERIOS_FV22_E_PROXIMOS_MARCOS_2026_10_26.md` com testes novos de **sequências de contexto**, complementares às regressões unitárias independentes. Não multiplicar pequenos ajustes estéticos. Não alterar núcleo S0/S1 sob responsabilidade do Codex.

A auditoria parte do contrato vigente FV-DOC-03 (FV-22-01..16) e distingue cada afirmação abaixo de autenticação/segurança real:

| Jornada encadeada nova | Contratos investigados | Critério de reprovação |
| --- | --- | --- |
| O2 rascunho → O3 versão F03 → Gestora supervisora → outro Gestor → suspenso → Consultor original | FV-22-02/03/05/06/08/10 e minimização D2/D3/D4 | O texto local, F03 privilegiado ou composer da atribuição anterior reaparecem após mudar ator; supervisor ganha ação de titular |
| G2 fila sem titular → pedido de assunção fictício por Marina → Daniel → Marina | FV-22-12/13; sem mutação sem versão/prova S0 | Intenção local é exibida a outro Gestor como atribuição aplicada; retorno ao primeiro Gestor herda pedido de sessão anterior |
| Consultora Lia na loja Horizonte → concessão excepcional ao caso A-117 em Aurora → Daniel/Rafael → Lia | FV-22-02/03/13 e concessão apenas por caso | Acesso excepcional dá visibilidade de carteira inteira, sobrevive troca de perfil ou aparece a operador não autorizado |

## Modificações tecnicamente permitidas

- `frontend/visual/tests/app.dom.test.mjs`: três novas regressões de jornada cobrindo combinação de módulos O2/O3/G2, leitura/atendimento e contexto.
- `frontend/visual/tests/verify_offline_export.py`: manifesto de hash/tamanho repinado para o arquivo de testes.
- Esta documentação. **Sem alteração em HTML/CSS, módulos de domínio, banco, APIs, migrations, S0/S1, Meta ou operações reais.**
- Reaproveitar suíte Chromium/Playwright existente com seus cenários abrangentes; **não abrir 8 sessões Chromium novas**, para respeitar o limite nativo de tempo. A nova evidência cruzada é Node DOM, não novo teste humano ou autenticado.

## Evidências e pendências

- Baseline antes da mudança: `e2bfc9c297b9163bea7d3f3e60510c08759029e8`, [run 40294929672](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40294929672), Python 25/25, Node 372/372, Chromium PASS.
- Resultado dos testes novos: **pendente do GitHub Actions**; não declarar aprovação sem observar `FULL LOCAL ACCEPTANCE: PASS`.
- **Bloqueios de integração mantidos:** grants, autorização D2/D3/D4, idempotência de assunção, cutoff F03, persistência/versões e transporte real pertencem a S0/S1/Meta/IA. Nenhum teste de interface substitui sua prova.
- Após FVA-01, conduzir **FVA-02 — matriz de estados de erro/ação** e uma auditoria de apresentação, priorizando defeitos descobertos e não criando uma lista indefinida de microincrementos.

## Regra de governança

Codex é responsável principal pelo S0. Propostas que afetem o núcleo ficam isoladas e documentadas, sem implementação no núcleo oficial antes da coordenação. `main`, PRs/branches existentes e deploy preservados. A interface e a plataforma seguem sem nome comercial aprovado (LiberaCred é o produto bancário).

## Certificação GitHub Actions — FVA-01

- **Execução:** [40300012152](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40300012152), `completed / success`.
- **SHA técnico completo testado:** `c9e7dd75f3a50dd0727eaeac808c412e26de9258`; conteúdo de regressão: `a9f56031bfe6d8f8bd2bca2c94daf2815ef4cdb3`.
- **Preflight:** 59 arquivos PASS; **Python:** 25/25 PASS; **Node:** 375/375 PASS (três testes cruzados novos FVA-01, todos `ok`); **Chromium/Playwright:** PASS; `FV-UI-058 foco do primeiro caso pela seta em 8 cenarios: PASS`.
- **Gate final:** `FULL LOCAL ACCEPTANCE: PASS`.
- A conclusão refere-se ao **modelo local de dados fictícios** e ao escopo visual; não é teste de autenticação, RLS, Supabase, simultaneidade real de Gestores, OpenAI/F03 efetiva, Meta ou banco. Sem alteração ao núcleo S0.
- Próximo marco de FVA: **FVA-02, estados de erro/ação e recortes de jornada**, evitando novas sessões Chromium desnecessárias. Esta atualização é documental, não altera o SHA técnico testado nem a `main`.
