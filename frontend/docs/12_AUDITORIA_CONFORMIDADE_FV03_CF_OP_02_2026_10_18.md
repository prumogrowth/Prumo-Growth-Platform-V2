# FV-AUD-03 — Auditoria da frente visual após contrato CF-OP-02/FV-03

**Data:** 18/10/2026. **Objeto:** confrontar o contrato vigente da frente visual com o trabalho já realizado em `frontend/visual/`, reparar divergências dentro da propriedade da interface e documentar o que ainda não é aceite. **Veredito:** direção do produto e fronteiras de responsabilidade **coerentes após reparos sintéticos**, mas contrato físico/interfrentes, navegadores reais e produção **não homologados**.

## 1. Fontes e precedência

**Atualização consultada:** `frontend/docs/09_CF_OP_02_CONTRATO_VISUAL_JANELA_CADEIAS_v0_1.md` (FV-03); diretriz de coordenação `docs/revisoes/CF_OP_02_DIRETRIZ_CADEIAS_JANELA_HUMANA_2026_10_18.md` na branch `docs/cf-op-02-cadeias-contextuais-20261018`, contrato S0 `docs/CF_OP_02_CONTRATO_NUCLEO_RECONTATO_HUMANO_v0_1.md`, OAI-08, WA-07 e S1-002/I2. Referências contratuais de antes: FV-01/FV-02, OAI-05, CFI-01 (issue #4), oito status, normas 13A/21–23/41 e D-ORG-01. **Coordenação atual:** issue #6 / PR #7 (não equivalem a aceite ou merge).

**[D-negócio]** três acontecimentos independentes: janela Meta 24h desde **inbound do cliente**; conclusão humana com análise/extrator; relógio C09 de 24h **após comprovação de envio do template final**, apenas em ciclo elegível. A perda por silêncio não equivale à recusa definitiva do banco. Sem reativar IA Vendedora após handoff, sem dado de uma loja cruzar outra, sem transformar Prumo em marca comercial final.

**[P/R/V]** contratos de request/response, `allowed_actions`, catálogo Meta, templates elegíveis, regra de concorrência de plano/manual, política C09 por fase, prova sent, baixa de atribuição, LGPD/Meta/Banco e autorização de produção permanecem com seus donos.

## 2. Achados do código anterior e tratamento

| ID | Severidade | Evidência anterior | Reparo nesta branch | Situação |
| --- | --- | --- | --- | --- |
| FV3-A01 | Alta | `canMockMessage` autorizava mensagem baseada sobretudo em atribuição/status, sem projetar janela Meta válida | `mayMockFreeText` exige indicação **open** e `allowedActionsProjection.free_text`, posse e etapa pendente; sem relógio no browser | Corrigido na **simulação** |
| FV3-A02 | Alta | Não havia lista ativa separada de histórico, contrariando conclusão+janela vencida | Filtros de `active/history` pela projeção `inboxProjection`; histórico retido sem apagá-lo | Corrigido na **simulação** |
| FV3-A03 | Alta | Sem ações diferentes para template manual e cadeia contextual | Botões separados com `single_template` / `request_chain`, diálogo de template **fictício** pré-listado, sem API nem envio | Corrigido na **simulação** |
| FV3-A04 | Alta | Não distinguia solicitação/planejamento/prova de envio do template final | Aba Recontatos com estados `requested`, `scheduled`, `queued`, `sent_confirmed` **somente conforme fixture**; C09 nunca é calculado nem executado pelo frontend | Corrigido na **simulação** |
| FV3-A05 | Alta | Profissional suspenso ainda podia ser representado como operador comum | `visibleConversations`, conclusão, notas, equipe e ações de acompanhamento negam atores `suspended/removed` nas fixtures; fila protegida exibida para gestor, sem redistribuir | Corrigido na **simulação**, S1-002 real [R] |
| FV3-A06 | Média | Uma conversa já concluída sem retorno de extração aparecia equivocadamente como “ainda não solicitada” | Estado explícito “etapa concluída, retorno não disponível”, sem afirmar execução/persistência | Corrigido |
| FV3-A07 | Média | A ação de equipe existia apenas na barra desktop, oculta no mobile | Entrada móvel “Equipe” para gestor fictício, usando o mesmo painel sem ampliar autorização | Corrigido, teste mobile novo [P] |
| FV3-A08 | Média | Script de navegador referenciava só arquivos FV-UI-002 e contadores antigos | `browser.smoke.py` atualizado com `cf-op-02.mjs`, cenários/contadores e navegação active/history/template | Corrigido **no script**; reexecução após FV-03 pendente |
| FV3-A09 | Média | Painel de extração e conversa não separava estado comercial de janela/conclusão | Resumo exibe janela/projeção, etapa humana, situação da lista; venda e recusa protegidas | Corrigido |
| FV3-A10 | Observação | FV-UI-002 havia somente 12 ensaios de regras | `tests/cf-op-02.test.mjs` com 12 cenários adicionais, cobrindo autorização visual, janelas, histórico e proteção C09 | Verificado por harness V8 |

**Revisão adicional da auditoria (mesma data):** (FV3-A11) o seletor inicial oferecia o catálogo global de dois templates fictícios; foi restringido à **lista de template ID+versão projetada como elegível para o caso**. Um modelo presente no catálogo geral mas ausente da elegibilidade do caso não pode ser solicitado, inclusive no simulador. (FV3-A12) projeções ausentes de atividade, conclusão ou estado do profissional agora seguem **deny-by-default**: não tornam automaticamente a conversa ativa, não a incluem no histórico, não liberam ações e não presumem profissional ativo. Dois testes adicionais foram incluídos, totalizando **24/24** no harness V8. Esses ajustes evitam normalizar no frontend concessões que pertencem à S0 e S1-002.

Os reparos não criam tabelas, RLS, mensagens ou status novos. `inboxProjection`, `metaWindowProjection`, `humanCompletionProjection`, `allowedActionsProjection` e `followupProjection` são **fixtures ilustrativas de uma futura projeção S0**, não APIs aprovadas. Ausência de projeção implica **não habilitar** texto livre/templates, em vez de supor autorização.

## 3. Verificação diretamente sobre código recuperado do GitHub

- Arquivos JS de `frontend/visual/` e três arquivos `tests/*.test.mjs`: **sintaxe analisada sem erros** no ambiente JavaScript V8.
- Conteúdo dos três conjuntos de testes de lógica das fixtures (`fixtures.test.mjs`, `view-model.test.mjs`, `cf-op-02.test.mjs`) executado sobre os módulos **recuperados da branch GitHub**, com `import/export` adaptados apenas para um **harness JavaScript V8 de asserções equivalentes**: **24 testes passaram / 0 falharam**. **Não** equivale a afirmar que Node CI foi executado nesta revisão.
- Inspeção estática do frontend: diálogo de template, alternância ativa/histórico, botão de equipe no mobile, estados de recontato e controles de texto livre presentes. **Nenhum cálculo de prazo com `Date.now()` ou `new Date()` no código de aplicação**, nenhuma chamada `fetch/XMLHttpRequest/WebSocket`, nem `localStorage/sessionStorage`, segredos, credenciais ou integração OpenAI/Meta na interface.
- **Não foi reexecutado o navegador Chromium após FV-03.** A suíte de navegador existente foi atualizada, mas permanece pendente executar, em ambiente apto, `python frontend/visual/tests/browser.smoke.py` com Playwright e Chromium. Os ensaios browser anteriores, FV-UI-002, não são reclassificados como prova das funcionalidades novas.
- Nenhum teste do núcleo S0, RLS, Meta, OpenAI, prova bancária, equipe real ou LGPD foi executado pela frente FV.

## 4. Matriz mínima de rastreabilidade FV3-01..14

| Critérios do contrato FV-03 | Cobertura nesta frente | Status |
| --- | --- | --- |
| FV3-01/02/03/04: pendente vencido, template único, cadeia e sem reabrir livre | Fixtures, controles condicionais e testes puros | [P] Simulado/ensaiado |
| FV3-05: inbound posterior renova janela e roteia humano | Somente cenário e obrigação S0/Meta, **sem evento inbound real** | [R] Não executado |
| FV3-06/07: concluído aberto visível e concluído vencido histórico | Duas fixtures e alternância ativa/histórico | [P] Simulado/ensaiado |
| FV3-08/09: final provado+24h elegível, Banco/vendido protegidos | Projeções distintas `sent_confirmed` versus `queued`; status `perdido` apenas pré-fixado em fixture, nunca calculado | [P] Simulado; C09 S0 [R] |
| FV3-10/11: gestor sem atribuição e profissional revogado | Guardas artificiais, perfil suspenso e fila protegida | [P] Simulado; revogação S1-002 [R] |
| FV3-12: histórico mantido, lojas separadas | Casos históricos, filtros e cenários A/B | [P] Testes de lógica |
| FV3-13: mobile/tablet/teclado/feedback | CSS e controle móvel revistos; bateria browser pós-reparo não rodada | [R] Verificação final pendente |
| FV3-14: erro/retry/atraso sem falso sucesso | Separação de estados técnicos e feedback sintético; não há API/retentativa real | [P/R] Parcial |

## 5. Pendências que não devem ser resolvidas dentro desta branch

1. **S0 (issue #4 e #6):** contratos físicos dos comandos de concluir, template manual, cadeia e consulta de progresso; fonte oficial de `allowed_actions`, janela Meta, snapshots/versões e expiração; idempotência/concorrência e elegibilidade de perda C09.
2. **OpenAI OAI-05/OAI-07/OAI-08:** contrato unificado e extração, avaliação e planejamento somente sob autorização do S0, sem provedor real aqui.
3. **Meta WA-07:** templates oficialmente aprovados, opt-in/opt-out, prova de envio, relógio desde inbound, callbacks/retries, categoria e custos [V].
4. **S1-002/I2:** redistribuição automática real e revogação transacional por mesma loja. A fixture `Fila protegida` não implementa distribuição.
5. **Normas bancárias, LGPD e catálogo D3:** nenhuma mídia, PII real ou prova bancária pode entrar na demonstração.
6. **Frontend:** rodar smoke browser atualizado, revisão de teclado/leitor de tela, responsividade física e ampliação progressiva do inventário O1–O5/G1–G4. Ações bancárias, atribuição e correção excepcional C13 permanecem fora da demo, não declaradas implementadas.

## 6. Veredito e limites

**Auditoria documental e de lógica, com reparos FV-03: CONCLUÍDA.** Não foi constatada incompatibilidade remanescente nas **projeções simuladas cobertas** pelas verificações executadas. **Homologação funcional de integração, renderização final, contratos canônicos e liberação da plataforma: PENDENTES.**

Todos os commits desta revisão pertencem a `frontend/` na branch `feat/frontend-plataforma-visual`. Sem deploy, sem merge, sem escolha de domínio/hospedagem, sem mudança de infraestrutura e **sem incremento automático do índice auditado 19F (69/100)**. A avaliação visual do responsável permanece adiada até a interface estar substancialmente madura, como estabelecido no documento 11.
