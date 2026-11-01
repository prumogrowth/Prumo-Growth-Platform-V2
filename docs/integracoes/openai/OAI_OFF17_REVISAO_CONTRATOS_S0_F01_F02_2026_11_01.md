# OFF-17 — Revisão OpenAI dos candidatos físicos S0 F01/F02 em PG17

**Data:** 01/11/2026. **Status:** revisão técnica de **LABORATÓRIO**; não é aceite de integração operacional nem homologação do contrato S0.

## Motivo

A S0/S1 publicou **novas entregas reais de código de laboratório** após a OFF-16. Em vez de criar outro guard sintético redundante, a frente OpenAI analisou os **contratos/código exatos**, confrontou sua interoperabilidade com OFF-04/OFF-13/OFF-14 e desenvolveu uma matriz de regressão de 20 casos executada a partir do arquivo Python S0 pinado. A etapa 08B deixa de estar apenas sem retorno: há **revisão de candidatos concretos em andamento**.

### Fontes S0 e evidência independente

| Issue | Fonte S0 (imutável e isolada) | Provas S0 já publicadas | Parecer OpenAI |
|---|---|---|---|
| [#7 F02](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7) | [S0 F02 PG17, `5b619c7779fb8b6595c72da696a4aa7faec128d1`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/5b619c7779fb8b6595c72da696a4aa7faec128d1/integration/s0s1_f02/pg17_service.py) | [CI `41303121569`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41303121569): 130 casos distintos: 25 PG17, 10 interop OFF-04, 71 OFF-04 e 24 PRE_DISPATCH | **Compatibilidade candidata parcial; 1 divergência de versões a resolver antes de aceite de shape** |
| [#11 F01 posse](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/11) | [S0 F01 owner PG17, `caf58eac889481bb96354bdcdaa740c8e48d9755`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/caf58eac889481bb96354bdcdaa740c8e48d9755/integration/s0s1_f01_ownership/pg17_service.py) | [CI `41312816390`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41312816390): 103 casos distintos, 8 interop OFF-13 | **Aderência estrutural de laboratório** para handoff humano irreversível e `NO_PUBLISH`, sem autenticação real |
| [#12 F01 fontes](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/12) | [S0 F01 fontes PG17, `b32d42bd4a204a2852e2ab21514436ee7e24e822`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/b32d42bd4a204a2852e2ab21514436ee7e24e822/integration/s0s1_f01_sources/pg17_service.py) | [CI `41318311078`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41318311078): 98 casos distintos, 8 interop OFF-14 | **Aderência estrutural de laboratório** para aliases, fonte histórica/atual e recheck, sem prova comercial/semântica |

**Atenção:** esses números são de **CI separadas executadas nas branches próprias S0**; não somá-los aos testes OpenAI como se fossem regressão conjunta nem tomar resultado de PostgreSQL descartável como readback hospedado.

## Divergência concreta OFF17-F02-VERSIONS-01

O contrato OFF-04/S0 F02 declara **sete versões** `case, cycle, catalog, assignment, policy, consent, chain`; o próprio [documento S0 F02](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/5b619c7779fb8b6595c72da696a4aa7faec128d1/docs/contratos/s0_f02/S0_F02_PG17_OFF04_20261101.md) refere-se a versões independentes. Contudo, na função Python `_sources`, de `integration/s0s1_f02/pg17_service.py`, encontra-se a seguinte comparação:

```python
case['assignment_revision']==expected['cycle'] and
case['assignment_revision']==expected['assignment']
```

O **mesmo** `assignment_revision` físico é exigido para ambas as revisões. Logo, na implementação candidata atual, um conjunto com `expected['cycle'] != expected['assignment']` é rejeitado, mesmo que `case_revision`, `assignment_revision`, consentimento e catálogo estejam estáveis. Os testes físicos anteriores exercitam negativos por versão stale, mas não demonstram sucesso legítimo com `cycle` e `assignment` distintos.

**Reprodução transparente:** `tests/off17_s0_f02_pinned_source_review.py` extrai o AST **da função `_sources` do arquivo exato S0 no commit pinado**, sem importá-lo como biblioteca nem executar qualquer outra parte da S0; aplica cursor falso em memória com `case_revision=1`, `assignment_revision=1`. Com `expected.cycle=1` e `expected.assignment=1`, a consulta aprova a seleção sintética. Com `expected.cycle=2` e `expected.assignment=1`, retorna `STALE_OR_CHANGED`. Com `expected.cycle=1` e `expected.assignment=2`, também rejeita. São observações do código, **não** ensaio em PostgreSQL real e **não** prova de que uma revisão 2 seja autorizada.

**Decisão solicitada à S0 na #7:** ou separar a fonte física de `cycle_revision` da de `assignment_revision`, testando um caso legítimo de revisões distintas, **ou** publicar contrato canônico que explicite por que esses dois índices devem ser idênticos no contexto F02 e ajustar o contrato/expectativa da OpenAI antes de aceite. **Não** fazer a OpenAI eliminar silenciosamente `cycle` nem alterar a S0 unilateralmente. Em qualquer caso preservar recheck, aliases, grants e idempotência.

## Outras fronteiras preservadas

- O envelope S0 F02 privado contém `requestId`, loja/caso/principal e templates originais, com `authenticated=true` **somente na fixture**. Ele **NÃO** pode ir ao fornecedor; apenas `f02ProviderView` deve gerar aliases minimizados. S0 já tem 10 testes de interop, incluindo esse isolamento.
- O `LAB_REQUEST_RECORDED_NO_MODEL` e o `LAB_PROPOSAL_RECORDED_REVIEW_ONLY` **não** autorizam modelo, agendamento, Graph, C09, venda ou despacho. Recheck pós-inferência e pré-despacho são portas distintas.
- S0 F01 posse fixa `HUMAN` como irreversível no PG17 e registra recheck `NO_PUBLISH`; OFF-13 só verifica estrutura de observações. Handoff S0 não autentica dados de conhecimento.
- S0 F01 fontes usa mapeamento interno `source_ref → src_###`, revisão do catálogo inteiro e recheck de posse; OFF-14 só examina **metadados de fixture**, não prova conteúdo, preço, condição ou vigência real. Não remeter `source_ref` ao provedor.
- As três portas foram testadas sobre **PG17 descartável** com identidade/consentimento/templates falsos e credenciais de instalador; continuam pendentes fonte hospedada autenticada, autorização semântica, outbox/eventos Meta e aceite interfrentes. A Meta [#9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9)/[#10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10) ainda não permite despacho real.

## Testes e escopo

O novo teste Python executa 20 casos **sem banco, modelo, rede ou chave de API**: seleção com revisões iguais, duas negativas demonstrando a divergência `cycle/assignment`, revisão case/policy/catalog/chain/consent e bloqueios de opt-out, cross-store, supressão, grant, catálogo duplicado, expiração e ausência de aprovação/mídia. O workflow também executa **950 testes cumulativos OpenAI Node** herdados da OFF-16 em árvore íntegra.

**Meta a comprovar nesta branch:** dois resultados independentes: **950/950 Node** e **20/20 Python AST source-level**. São conjuntos distintos e **não** 970 testes integrados Node/PG17. O workflow usa `git show` para obter `pg17_service.py` do SHA exato da S0; nenhuma cópia editada do código S0 é publicada.

## Próximas decisões

1. S0 responde à #7 sobre independência `cycle` versus `assignment` e fecha o mapeamento físico/contratual.
2. OpenAI revisa a resposta, implementa ajuste **somente no próprio consumidor** se necessário e repete interop com código exato ratificado S0.
3. S0/Comercial/Infra continuam responsáveis pela autenticação, fontes reais/consentimento/grants, provedores, homologação e operação.
4. API OpenAI: **ainda não requerida** para auditoria de contratos e regressão, e não cura esse bug. Nenhuma chave, cobrança, merge ou produção.

**Este documento não declara ACEITE operacional de F01/F02.**