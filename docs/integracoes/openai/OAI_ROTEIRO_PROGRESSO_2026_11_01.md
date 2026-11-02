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
| 12 | Testes físicos/autenticados e aceites interfrentes | PENDENTE_CONTRATO | **12A testes transversais independentes FEITO_OFFLINE** ([908/908](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41309774616)), OFF-15, 12B/12C exigem contratos S0/Meta ratificados e evidências físicas |
| 13 | Merge, deploy e ativação produtiva | NAO_AUTORIZADO | Aguardar aprovação expressa competente |

## Incrementos posteriores (NÃO são etapas que substituem a lista original)

| Lote adicional | Por que foi acrescentado | Status | Evidência |
|---|---|---|---|
| OFF-09/10 | Recuperar código oficial, corrigir bloqueio DNS local, publicar com garantia de integridade | FEITO_OFFLINE | [GitHub CI 678/678](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41268436358); nenhuma alteração main |
| OFF-11 | Compatibilidade estrutural F02 com WA-39 Meta | FEITO_OFFLINE | [724/724](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41268914799), branch `feat/oai-off11-wa39-consumer-lab-20261101` |
| OFF-12 | Bloquear promoção indevida de metadados/recibos S0 preliminares à F03 | FEITO_OFFLINE | [CI 774/774](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41293073729), branch `feat/oai-off12-f03-s0-metadata-gate-20261101` (724 anteriores + 50) |
| OFF-13 | Comparação offline de posse/handoff F01 em duas leituras sintéticas S0; sem publicar mensagens | FEITO_OFFLINE | [CI 819/819](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41295745349), branch `feat/oai-off13-f01-s0-ownership-review-20261101` (774 anteriores + 45) | 
| OFF-14 | Fontes comerciais por concessionária F01: validade, correção, escopo e recheck sintético | FEITO_OFFLINE | [CI 864/864](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41296742136), branch `feat/oai-off14-f01-commercial-source-review-20261101` (819 anteriores + 45) | 
| OFF-15 / 12A | Testes transversais independentes de fronteiras F01/F02/F03 | FEITO_OFFLINE | [CI 908/908](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41309774616), 864 herdados + 44 novos; **etapa 12 ainda PENDENTE_CONTRATO** | 
| OFF-16 / 12A | Pré-validação Responses API em simulação, sem key, rede, tokens nem custo | FEITO_OFFLINE | [CI 950/950](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41312180063), 908 herdados + 42 novos; uso real exige missão e orçamento autorizados | 
| OFF-17 / 08B | Revisão de candidatos PG17 S0 F01/F02 e reprodução do acoplamento `cycle`/`assignment` na F02 | FEITO_OFFLINE | [CI 41322638549](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41322638549): 950/950 Node e 20/20 Python source-level **separados**; divergência F02 ainda não corrigida; aguardando decisão #7 | 
| OFF-18 / 08B | Reavaliar correção S0 de revisões independentes F02 | FEITO_OFFLINE | [CI 41328784758](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41328784758): 950/950 Node + 24/24 Python AST, suites distintas; **mapeamento tecnicamente compatível em laboratório**; aceite operacional ainda pendente | 
| OFF-19 / AUDITORIA GERAL | Revisão transversal OFF01..OFF18 e hardening legado de versões/relógio | FEITO_OFFLINE | [CI 41338979377](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41338979377): 968/968 Node (950+18), 24/24 Python AST pinados; 2 defeitos corrigidos, riscos operacionais documentados | 
| OFF-20 / REMEDIAÇÃO | Endurecimento de validadores legados + quarentena de resposta OpenAI sem campo bruto | FEITO_OFFLINE | [CI 41345415665](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41345415665): 990/990 Node (968+22), 24/24 Python AST separados, sem falhas; não há sink real nem autorização de produção | 
| OFF-21 / 12A | Ponte Responses → F01/F02/F03 com avaliadores existentes, sem rascunho externo | FEITO_OFFLINE | [CI 41357833214](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41357833214): 1028/1028 Node (990+38), 24/24 Python AST independentes, 0 falhas/ignorados; sem API real | 
| OFF-22 / 08B | Compatibilidade F02 com Meta M19 A/B v0.2 e M20 v0.2, sem atribuir `sent`/WDC13/C09 | FEITO_OFFLINE | [CI 41360087872](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41360087872): 1068/1068 Node (1028+40), 24/24 Python AST separados, 0 falhas/ignorados; S0 operacional não homologada | 
| OFF-23 / 08B | Auditoria pinada do controlador de ciclos S0 F02: readback de estado/ator | FEITO_OFFLINE | [CI 41370145342](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41370145342): 1068 Node + 24 Python antigos + 22 Python novos, suites separadas, sem falhas; **2 achados reproduzidos, NÃO corrigidos na S0; Issue #7 pendente** | 
| OFF-24 / 08B | Revalidar correção S0 dos achados OFF-23 do readback F02 | FEITO_OFFLINE | [CI 41379155585](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41379155585): 1068/1068 Node, 24/24 Python AST anteriores e 30/30 AST sobre correção S0, separados; aceite técnico candidato **somente do readback**, sem autorização F02 operacional | 
| FV-REV-021 / Issue #13 | Resumos **pequenos e objetivos** de F01/F02/F03 no histórico acumulativo do **Resumo** do Frontend | FUTURO | [Issue #13](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/13), **não desenvolver agora** |

## Visibilidade de bloqueios

- **08A:** compatibilidade estrutural offline concluída até OFF-14.
- **08B:** **houve avanço externo verificável**: S0 publicou candidatos PG17 F01 posse [#11](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/11), fontes [#12](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/12) e pedido F02 [#7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7), todos com interop e CI próprios. OpenAI OFF-17 identificou o acoplamento `cycle/assignment`; **S0 respondeu na #7 com correção laboratório em `31e88ec`**, criando `case_cycles`/`cycle_revision` independentes. **OFF-18 comprovou em laboratório que o mapeamento pinado diferencia ciclo e atribuição** (950 Node + 24 Python source-level), sem aceite operacional. Ainda não há interface hospedada ratificada.
- **08B / Meta M19–M20:** os contratos Meta de saída v0.2 têm estado LAB não autenticado; OFF-22 ensaia o consumo fail-closed dos formatos atuais, sem inferir status definitivo/WDC-13/C09. Issue #9 continua aberta.
- **08B / S0 controlador de ciclos:** após OFF-18, S0 entregou controlador PG17 aditivo `054261b...`; OFF-23 audita o `readback` e encontrou contraprovas de estado atual e ator do evento não comparados, ainda sujeitas a correção S0 #7. **OFF-24 analisa o reparo S0 do recibo corrente**, sem aceitar o controlador completo até homologação operacional.
- **08C:** aceite dos contratos e integração autorizada pendente; **não** progredir com credenciais ou dados reais.
- **12A:** OFF-15 e OFF-16 concluídas offline, sem API real. Regressão transversal OFF-15 validada no [CI 41309774616](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41309774616) (908 PASS, 0 FAIL, 0 SKIP); **12B** (física/autenticada) depende de S0/Meta; **12C** (aceite) não iniciado.

## Cobertura da visão conceitual maior (não confundir funções F0x com IAs)

A concepção do projeto inclui **IA Vendedora**, **IA Analista/Otimizadora** (melhora somente configurações externas autorizadas de atendimento; jamais altera pesos próprios ou grants), **IA Gestora** para administradores e orquestração determinística. A linha OFF01–OFF19 prepara **funções F01/F02/F03**, não implementa integralmente os agentes Analista/Gestora. É necessário manter esses dois papéis como trilhas FUTURAS explícitas do produto, com aprovação, trilhas de auditoria, rollback de configurações e matrizes de permissão antes da afirmação de plataforma completa. Fonte conceitual: `projeto_liberacred_consolidacao_ideias_v0_2_auditada.md` §7–10.

## Auditoria corretiva OFF-19

[Relatório geral da frente](./OAI_OFF19_AUDITORIA_GERAL_CORRETIVA_2026_11_01.md) registra AUD19-01 (chaves de versões herdadas), AUD19-02 (relógio implícito em oferta), bloqueios e cobertura parcial. **Marcada FEITO_OFFLINE após CI 41338979377 verde**; nenhuma permissão produtiva foi concedida. Compatibilidade operacional F01/02/03, dados reais, Meta/Graph, modelos reais e implantação seguem condicionados a contratos e homologação.

## Remediação OFF-20 antes de novas integrações

A [correção pós-auditoria OFF-20](./OAI_OFF20_CORRECOES_POS_AUDITORIA_2026_11_01.md) trata AUD19-P2/P3: `core.mjs` rejeita entradas hostis antes de acessar campos de negócio; o preflight Responses deixa de devolver `candidateRaw` (resultado `0.2-lab`). CI da OFF-20 passou com 990/990 Node e 24/24 Python AST (separados). Isso **não** cria sink de execução autorizado nem fornece uma API OpenAI real. Manter 08B/08C, 09–11 e 12B/12C como pendentes de homologação externa.

## OFF-21 — passagem Responses → F01/F02/F03 (laboratório)

A [OFF-21](./OAI_OFF21_RESPONSES_DOMAIN_REVIEW_2026_11_01.md) encadeia preflight sem exposição de conteúdo → avaliador F0x já existente → apenas parecer genérico sem dados/autoridade. Não implementa envios, autenticação S0, validação semântica ou commit de ficha. É preparação da **etapa 12A** validada em [CI 41357833214](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41357833214), sem alterar o estado das etapas 08C/09–11/12B–C.

## OFF-22 — compatibilidade Meta M19/M20 com F02

[OFF-22](./OAI_OFF22_F02_META_M19_M20_CONTRATOS_2026_11_01.md) verificou em [CI 41360087872](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41360087872) os snapshots M19 Graph, M19 binding e M20 cadence v0.2 junto ao OFF-11 WA39, bloqueando qualquer promoção de alegações para a F02 sem correlacionamento e autenticação S0. Não altera status principal 08/10.

## OFF-23 — auditoria do readback do controlador de ciclos S0

[Relatório OFF-23](./OAI_OFF23_AUDITORIA_S0_F02_CYCLE_READBACK_2026_11_01.md): 22 contraprovas/regressões source-level aprovadas em [CI 41370145342](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41370145342) sobre a função S0 pinada, sem PostgreSQL real e sem alterar implementação de outras frentes. Enquanto não forem sanadas, manter a porta de ciclo **em revisão** e F02 operacional pendente. Os testes da auditoria registram o comportamento observado; CI verde não significa que os achados foram corrigidos.

## OFF-24 — retorno da correção de readback F02

[Relatório da revalidação OFF-24](./OAI_OFF24_REVISAO_CORRECAO_S0_F02_READBACK_2026_11_01.md). A S0 respondeu aos dois achados OFF-23 em SHA `fcbff8e...` com comparações de estado/ator/chave e regressões PG17. [CI 41379155585](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41379155585) confirmou a revalidação independente do código exato, mas **não** promove a fachada do controlador nem libera modelo/send. Etapa 08 segue em revisão.

## Gate futuro de uso da API OpenAI

A chave da API não é necessária para 12A/contratos. Eventual teste do modelo (E05) exige autorização expressa para chamadas pagas, modelo/orçamento, canários 100% sintéticos e segredo no gerenciador autorizado, nunca em commit/chat/Issue. Testes do modelo não suprem 08B/08C nem dispensam S0.

## Regra de atualização

A cada lote, registrar branch, commit exato, run GitHub Actions, testes executados, falhas e escopo. Nunca somar testes executados em bases diferentes como se fossem regressão conjunta; **CI 678, CI 724, CI 774, CI 819, CI 864, CI 908, CI 950, CI 968, CI 990, CI 1028 e CI 1068 são cumulativos em bases sucessivas**; OFF-17 acrescenta 20 verificações Python distintas sobre fonte S0 pinada e não devem ser apresentadas como 970 casos de integração física, não adicionais. OFF-12 foi atualizado para `FEITO_OFFLINE` após confirmar no log do GitHub Actions 774/774 PASS, 0 FAIL, 0 SKIP no run 41293073729. A OFF-13 foi atualizada para `FEITO_OFFLINE` após [819/819 no CI](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41295745349), zero falhas e ignorados. O CI da OFF-14 comprovou 864/864 PASS, zero falhas e ignorados, mas **não ratifica** S0/Meta nem autoriza produção.

**Próxima obrigação externa:** ratificar contratos operacionais S0 autenticados F02 #7, fontes/autoridade F01 #11/#12 e prosseguir com manifesto/commit F03 #5/#6, WA39 e PRE_DISPATCH #9/#10. Sem inventar interfaces autoritativas nem criar Issues duplicadas.
