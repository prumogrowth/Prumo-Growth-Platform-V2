# FVB-01 — Provas visuais consolidadas antes da avaliação humana

**26/10/2026 · Entrega para revisão de UX, não para publicação.**

## Origem certificada

O runtime sintético completo foi aprovado no [GitHub Actions run 40405009482](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40405009482) (`FULL LOCAL ACCEPTANCE: PASS`, 379 Node, 25 Python e Chromium). Em FVB-01, só se adiciona captura de evidência **após gate nativo**, sem alterar JS/CSS/HTML do frontend, S0, main ou integração.

## Matriz de 9 cenários reais de viewport

| Largura × altura | Tema | Perfil fictício | Cena |
| --- | --- | --- | --- |
| 1440 × 900 | Claro | Rafael / Consultor | Lista |
| 1440 × 900 | Escuro | Rafael / Consultor | Conversa |
| 1366 × 768 | Claro | Marina / Gestora | Equipe |
| 1366 × 768 | Escuro | Rafael / Consultor | Extração |
| 390 × 844 | Claro | Rafael / Consultor | Lista |
| 390 × 844 | Claro | Rafael / Consultor | Conversa |
| 390 × 844 | Escuro | Rafael / Consultor | Detalhes |
| 320 × 640 | Claro | Rafael / Consultor | Lista |
| 320 × 640 | Escuro | Rafael / Consultor | Conversa |

**Prova exigida:** HTML/CSS/JS da mesma raiz visual carregados em Chromium real, sem rede de negócios; seletor de perfil e de tema; abertura de conversa, detalhes, extração e equipe; sem erros JS ou rolagem horizontal na captura. A execução deve criar PNGs e `INDEX.json` no artefato privado `fv-visual-review-screenshots`, disponível somente após `FULL LOCAL ACCEPTANCE: PASS`.

## Limites

Esta coleta não constitui aceite estético, não valida leitor de tela real, toque em aparelho físico, desempenho mobile real, segurança S0, serviços externos, dados comerciais nem implantação em Sites. O responsável e avaliadores farão uma **única revisão visual consolidada**, reunindo comentários antes de refinamentos finais. Não solicitar aprovações fracionadas ao responsável nem publicar o Site automaticamente.

## Estado

**Aguardando CI da captura FVB-01.** Após criação do artefato, reunir os resultados e propor checklist de correções materiais. A etapa seguinte FVC organizará contrato + preview/handoff **para ChatGPT Work → ChatGPT Sites**, com aprovação explícita do responsável.

## Certificação de capturas e pré-handoff — 26/10/2026

GitHub Actions [40406051248](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40406051248), SHA `5b36ac7ba125666c23355336004164f4eb2dd503`, **completed/success**:

- 59 arquivos verificados, 25 testes Python, 379 testes Node, Chromium Playwright aprovado e **`FULL LOCAL ACCEPTANCE: PASS`**.
- `FVB-01 screenshot evidence: PASS (9 scenes)`; os PNGs foram gerados em navegador Chromium real a partir do mesmo frontend sintético, sem alterar `frontend/visual`.
- [**Baixar 9 capturas de revisão**](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40406051248/artifacts/12691307610) — ZIP de artefato, cerca de 1,04 MB, retenção 30 dias; inclui `INDEX.json`.
- [**Baixar ZIP de demonstração sintética**](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40406051248/artifacts/12691342751), criado após todos os testes.
- Empacotamento rápido atualizado para a base FVA-02 certificada no commit `f72ac2f7f3eacf6a5dd51ac0b60ff56c986c53e3`: [run 40406216028](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40406216028) **completed/success**.

**Estado FVB:** cobertura automatizada de navegação em Chromium e **capturas prontas**; **revisão estética e teste de toque por pessoas ainda não ocorreram**. Esses são objetivos da prévia no ChatGPT Sites, não requisitos para declarar que o Chromium capturou a interface. Não apresentar screenshots como homologação humana.
