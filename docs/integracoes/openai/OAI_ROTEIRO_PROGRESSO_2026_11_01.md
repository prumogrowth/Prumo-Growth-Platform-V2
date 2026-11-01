# Frente OpenAI — roteiro mestre de acompanhamento (01/11/2026)

**Objetivo:** acompanhar a lista original e os incrementos posteriores sem confundir **desenvolvimento offline concluído** com **integração homologada**. A referência versionada é o GitHub, não o chat. Status válidos neste quadro: `FEITO_OFFLINE`, `EM_TESTE`, `PENDENTE_CONTRATO`, `FUTURO`, `NAO_AUTORIZADO`.

## Etapas principais (lista original, consolidada)

| ID | Etapa acompanhável | Status | Evidência / responsável |
|---|---|---|---|
| 01 | Base técnica OFF-01 e guardas S2 | FEITO_OFFLINE | Base `394512327cd3756dfbe61ff970a6279c354b6565`; [342/342](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41261591040) |
| 02 | OFF-02 — fronteira tipada do adaptador | FEITO_OFFLINE | Branch candidata OFF-08 `1f8157838c11a7b59456a3b178a8ade21a17b42b` |
| 03 | OFF-03 — F03 histórico, correção e proveniência | FEITO_OFFLINE | Mesma branch, 101 testes F03 na regressão |
| 04 | OFF-04 — F02 planejadora, templates e continuidade | FEITO_OFFLINE | Mesma branch |
| 05 | OFF-05 — F01 atendimento e handoff | FEITO_OFFLINE | Mesma branch |
| 06 | OFF-06 a OFF-08 — auditorias, reparos, integridade e reprodutibilidade | FEITO_OFFLINE | Mesmo commit/manifesto de SHA-256 |
| 07 | Consolidação, branch GitHub e regressão da OFF-01 a OFF-08 | FEITO_OFFLINE | [678/678, pré e pós-commit](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41268436358) |
| 08 | Revisão de contratos OpenAI↔S0/Meta e definição das lacunas | EM_TESTE | Issues [#5](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/5), [#6](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/6), [#7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7), [#9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9), [#11](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/11), [#12](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/12) |
| 09 | Consumo real F01 — posse IA, handoff, recheck e fontes por loja | PENDENTE_CONTRATO | S0/S1, Issues #11 e #12 |
| 10 | Consumo real F02 — pedido autorizado, catálogo, evidências Meta e despacho | PENDENTE_CONTRATO | S0/S1, Meta, Issues #7, #9, #10 e #8 |
| 11 | Consumo real F03 — fechamento/histórico multicases e aplicação de ficha | PENDENTE_CONTRATO | S0/S1, Issues #5 e #6 |
| 12 | Testes físicos/autenticados e aceites interfrentes | PENDENTE_CONTRATO | S0/Meta/Infra + responsável, versões ratificadas e evidências reais |
| 13 | Merge, deploy e ativação produtiva | NAO_AUTORIZADO | Aguardar aprovação expressa competente |

## Incrementos posteriores (NÃO são etapas que substituem a lista original)

| Lote adicional | Por que foi acrescentado | Status | Evidência |
|---|---|---|---|
| OFF-09/10 | Recuperar código oficial, corrigir bloqueio DNS local, publicar com garantia de integridade | FEITO_OFFLINE | [GitHub CI 678/678](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41268436358); nenhuma alteração main |
| OFF-11 | Compatibilidade estrutural F02 com WA-39 Meta | FEITO_OFFLINE | [724/724](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41268914799), branch `feat/oai-off11-wa39-consumer-lab-20261101` |
| OFF-12 | Bloquear promoção indevida de metadados/recibos S0 preliminares à F03 | FEITO_OFFLINE | [CI 774/774](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41293073729), branch `feat/oai-off12-f03-s0-metadata-gate-20261101` (724 anteriores + 50) |
| OFF-13 | Comparação offline de posse/handoff F01 em duas leituras sintéticas S0; sem publicar mensagens | FEITO_OFFLINE | [CI 819/819](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41295745349), branch `feat/oai-off13-f01-s0-ownership-review-20261101` (774 anteriores + 45) | 
| OFF-14 | Fontes comerciais por concessionária F01: validade, correção, escopo e recheck sintético | FEITO_OFFLINE | [CI 864/864](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41296742136), branch `feat/oai-off14-f01-commercial-source-review-20261101` (819 anteriores + 45) | 
| FV-REV-021 / Issue #13 | Resumos **pequenos e objetivos** de F01/F02/F03 no histórico acumulativo do **Resumo** do Frontend | FUTURO | [Issue #13](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/13), **não desenvolver agora** |

## Regra de atualização

A cada lote, registrar branch, commit exato, run GitHub Actions, testes executados, falhas e escopo. Nunca somar testes executados em bases diferentes como se fossem regressão conjunta; **CI 678, CI 724, CI 774, CI 819 e CI 864 são cumulativos em bases sucessivas**, não adicionais. OFF-12 foi atualizado para `FEITO_OFFLINE` após confirmar no log do GitHub Actions 774/774 PASS, 0 FAIL, 0 SKIP no run 41293073729. A OFF-13 foi atualizada para `FEITO_OFFLINE` após [819/819 no CI](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41295745349), zero falhas e ignorados. O CI da OFF-14 comprovou 864/864 PASS, zero falhas e ignorados, mas **não ratifica** S0/Meta nem autoriza produção.

**Próxima obrigação externa:** contratos S0 de posse/conteúdo F01, planejamento/evidência F02 e manifesto/commit F03. Sem inventar interfaces autoritativas nem criar Issues duplicadas.
