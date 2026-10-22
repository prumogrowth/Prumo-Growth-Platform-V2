# FV-UI-019 — Conclusões humanas sucessivas, F03 e ficha viva (Frontend)
**Data:** 22/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Natureza:** UI e fixtures sintéticas, NÃO integração operacional ou homologação.

**Fontes normativas:** [FV-DOC-03 §§3–5, FV-22-04/05/06/07](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md); [FV-AUD-01](./40_FV_AUD_01_AUDITORIA_ESTATICA_IMPLEMENTACAO_2026_10_22.md); [FV-UI-018](./42_FV_UI_018_PERMISSOES_DISTRIBUICAO_2026_10_22.md). Mantêm-se R-SIGLA-01, R-CFI-01, R-RETENCAO-01 e dependências S0/S1/OpenAI, sem decisão unilateral.

## Entrega no protótipo
| Requisito | Evidência | Separação de autoridade |
|---|---|---|
| FV-22-05: conclusões distintas | Caso `A-108` exibe **dois eventos de conclusão já confirmados na fixture**, com `completionId`, `requestId`, `cutoffMessageRef`, `cutoffVersionRef` e `resultVersionRef` diferentes (`a108-1`/`a108-2`; resultado `v0-ficticia`/`v1-ficticia`). | Os cutoffs são referências **opacas pré-projetadas** pela fixture; navegador não os calcula como prova S0 nem mistura versões de caso com versões de formulário. Mensagens posteriores não mudam evento anterior. |
| FV-22-06: esclarecimento pós-extração | Na aba Extração do caso `A-108`, titular Rafael pode **visualizar um cenário alternativo fictício** de retorno do cliente. A etapa de atendimento é representada como pendente só nesta cena, preservando a ficha parcial anterior. | Não se cria reabertura efetiva, fluxo F02, editor C13, permissão ou pedido F03 em rede. O botão é de **exibição de cenário** projetado, não de ação transacional. Supervisão não recebe esta opção. |
| FV-22-05: nova conclusão após esclarecimento | O botão humano expresso “Concluir atendimento” na cena alternada registra **somente pedido local** com `candidateCutoffRef=a108-3`, versão fictícia da cena e `confirmedByS0:false`, `persisted:false`. O pedido não é apresentado como execução F03 ou gravação. | O S0 será responsável por verificar ator, versão, recorte imutável, evento, idempotência, autorização e disparo da F03. Mensagem não enviada no protótipo não prova resposta nem muda cutoff selado. |
| FV-22-07: ficha contínua | Novo `human-cycle-view.mjs` projeta o dossiê `customerRef + shopId` pré-reconciliado pela fixture, versões e histórico de cortes, **sem recompor identidade a partir de telefone/CPF/nome**. O3 segue somente leitura. | O dossiê é visível somente ao titular ativo com acesso ao caso; Gestor supervisor não recebe versões/campos. Outra concessionária não compartilha identidade, vínculo ou conteúdo. |
| FV-22-07: remessas imutáveis | Caso `A-114` contém versão viva de demonstração `live-form-v2-demo` e snapshot de remessa anterior de `A-105`, referenciado por `bank-demo-v1`. A evolução da ficha não altera snapshot bancário. | Nenhuma remessa, resposta bancária, venda ou transição comercial é aplicada; são referências da fixture, não eventos bancários reais. |

**Implementação:** `frontend/visual/human-cycle-view.mjs` (novo), `cf-op-02.mjs` (fixtures A-108/A-114), `app.mjs` (jornada e telas), mantendo `registration-view.mjs` como projetor de campos efetivamente persistidos na fixture. Sem mudança de contratos ou código externo.

## Testes e evidências
- `tests/human-cycle-view.test.mjs` — **11 testes**: eventos e recortes distintos, imutabilidade do corte antigo, duplicidade/malformação rejeitadas, acesso e retorno autorizados só na fixture, não persistência e snapshots da mesma concessionária.
- `tests/app.dom.test.mjs` — 5 cenários novos: linha do tempo, segundo clique, preservação de versão, supervisor sem dados, reset/troca de perfil.
- `tests/source-contract.test.mjs`, `tests/source-module-graph.test.mjs`, `tests/browser.smoke.py` e `tests/run_acceptance.py` atualizados para contemplar o módulo e a jornada de navegador.
- **Execução da rodada em avaliador JavaScript V8 temporário com fontes GitHub e mocks da frente:** `app.dom` **51/51**, `app.mobile.dom` **10/10**, `attention-integration` **7/7**, `distribution-view` **10/10**, `human-cycle-view` **11/11**, `registration-view` **12/12**, `postmark-view` **16/16**, `source-contract` **30/30**: **147 verificações aprovadas**. Isto é inspeção/teste sintético; não equivale a `node --test`, compilação nativa, browser/Chromium, teste de segurança ou homologação.
- `browser.smoke.py` contém novo percurso Playwright de A-108/A-114, **não executado** nesta rodada; acesso a checkout privado e browser nativo continua indisponível neste contexto. Histórico `19F = 69/100` permanece sem recálculo e FV-UI-013 não homologada.

## Bloqueios de integração e próximo gate
1. S0/S1 deve expor **evento de conclusão real**, versão e cutoff imutável, seleção do histórico lógico autorizado por concessionária, autorização, idempotência e transição para nova etapa de esclarecimento.
2. OpenAI F03 só pode atuar depois de confirmação pelo S0; retorno e aplicação de campos requerem versão/prova e política de erros. **F02 continua planejadora**, sem automação de esclarecimento por lacuna.
3. S0 deve expor ficha viva por cliente+loja, reconciliação de identidade protegida, proveniência, versões e snapshots bancários desvinculados da versão viva. Regras de retenção de mídia, identidade multitelefone e status comercial continuam dependências.
4. Antes de homologação: checkout autorizado, `node --test frontend/visual/tests/*.test.mjs`, smoke Chromium em larguras previstas, acessibilidade e testes de integração S0/S1/OpenAI somente com contratos ratificados.

**Conclusão:** FV-UI-019 implementado **apenas como demonstração segura de estados**, sem merge, deploy, dados reais ou alterações noutras frentes.
