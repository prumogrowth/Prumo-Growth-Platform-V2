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
