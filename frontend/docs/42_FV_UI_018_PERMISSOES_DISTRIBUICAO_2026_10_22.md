# FV-UI-018 — Reparação de projeções de permissão e distribuição (Etapa 2)
**Data:** 22/10/2026. **Frente:** somente Frontend, branch `feat/frontend-plataforma-visual`. **Estado:** implementado em protótipo sintético, **NÃO HOMOLOGADO**. Fontes: [FV-DOC-03](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md) §2/6 e FV-22-12/13; [D-AL-01..10](./35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md), [FV-AUD-01](./40_FV_AUD_01_AUDITORIA_ESTATICA_IMPLEMENTACAO_2026_10_22.md), [FV-UI-017](./41_FV_UI_017_INTEGRIDADE_CONTEXTO_MENSAGENS_2026_10_22.md).

## Implementado nesta rodada
| Regra | Aplicação visual e código | Limite |
|---|---|---|
| D-AL-05/06/07, FV-22-13 | Novo módulo `frontend/visual/distribution-view.mjs`, aba **Fila compartilhada** em G2 (`index.html`, `app.mjs`): lead novo **sem titular** projetado por concessionária, visível a Marina/Daniel autorizados à mesma loja, independentemente de vínculo a equipe. Estados sintéticos distintos: `unassigned`, `claimed`, `redistributed`. | Fotografia **alternativa T0** ilustrativa, separada da carteira atual; **não é roteamento real** nem altera caso/cliente. A distribuição regular entre equipes é regra **S0/S1**, sem algoritmo no frontend. |
| D-AL-06/07, FV-22-13 | Botões **Solicitar assunção** e **Solicitar atribuição à equipe** com confirmação; a segunda opção lista somente Consultores ativos da equipe do Gestor. A versão do caso e a projeção são revalidadas localmente. Pedidos mostram `requested_demo`, `applied:false` e **NÃO ATRIBUÍDO**. | Concorrência não é resolvida pela UI: Marina e Daniel podem pedir simultaneamente, mas nenhum pedido se transforma em titular. S0/S1 deve garantir **único vencedor atômico**, idempotência, auditoria e versionamento. Um ator pausado/suspenso não é declarado elegível pelo browser. |
| D-AL-03, FV-22-12 | `fixtures.mjs` acrescenta `hasMockCaseOnlyScope`, `hasMockCaseScope` e `visibleMockShops`. Um cenário `A-117` em `cf-op-02.mjs` representa autorização **fictícia confirmada** de Lia àquele caso em Aurora, **sem grant geral de Aurora**. Lista/filtro, mensagem, conclusão, nota, ficha e banco aplicam escopo por caso. | Só aceita a projeção `s0_fixture` com ator, caso, loja, versão, motivo, escopo e confirmação consistentes. Não cria autorização real ou RLS; caso troque de titular ou perca confirmação, o acesso excepcional desaparece. |
| D-AL-02/03 | Projeção de supervisão da equipe reconhece caso transferido com escopo individual sem tornar visíveis casos de equipe alheia; a prévia de pausa continua separada da fila de leads novos. | Redistribuição automática de casos existentes continua **somente na própria equipe** e exige prova de primeiro contato; ausência da prova ou de substituto preserva o titular. |
| FV-22-12 | Gestão de pausa exibe claramente **entrada pausada na fixture ≠ casos efetivamente redistribuídos**; pedido local não altera o estado nem transfere casos. | `DEFERRED_S0_PROOF` **não** equivale a remanejamento confirmado. Estados físicos e prova dependem S0/S1. |

**Não alterado:** oito status comerciais canônicos, regras de autoria/cadastro F03, APIs S0/S1, Supabase/GoTrue/RLS, Meta/WhatsApp, OpenAI, MCP e documentos normativos de outras frentes. Sem merge, deploy ou produção.

## Arquivos principais
- `frontend/visual/distribution-view.mjs` (novo); `fixtures.mjs`, `cf-op-02.mjs`, `app.mjs`, `index.html`, `styles.css`.
- Projeções de caso e gestão: `registration-view.mjs`, `bank-view.mjs`, `postmark-view.mjs`, `view-model.mjs`, `team-operations.mjs`, `team-pause-preview.mjs`, `team-monitoring.mjs`.
- Testes: `tests/distribution-view.test.mjs` (novo, **10 cenários**), `tests/app.dom.test.mjs` (4 cenários novos), `tests/team-monitoring.test.mjs` (expectativas atualizadas), `tests/dom-fixture.mjs`, `tests/browser.smoke.py`, `tests/source-module-graph.test.mjs`, `tests/source-contract.test.mjs`, `tests/run_acceptance.py`.

## Execuções verificadas e limites
- Avaliador **V8**, usando código atual recuperado pelo GitHub e mock DOM da própria frente: `app.dom` **46/46**, `app.mobile.dom` **10/10**, `attention-integration` **7/7** e `distribution-view` **10/10**: **73/73 verificações**. Em rodada complementar de funções puras, passaram `team-monitoring` 11/11, `fixtures` 7/7, `team-operations` 10/10, `view-model` 6/6, `cf-op-02` 17/17, `registration-view` 12/12, `bank-view` 10/10, `postmark-view` 16/16, `team-pause-preview` 9/9, `team-monitor` 13/13 e `batch-monitor` 11/11. `conversation-attention` teve **5 aprovações e uma execução bloqueada por falta de `structuredClone` nesse avaliador**, não caracterizada como falha da implementação.
- **29/29** verificações de `source-contract.test.mjs` foram realizadas anteriormente nesta rodada, antes do ajuste final de labels. Teste nativo Node e Chromium/Playwright **não** executados; smoke atualizado mas ainda não homologado. `verify_offline_export.py` tem manifesto historicamente fixado em SHA antigo e **não** valida este incremento até regeneração segura do manifesto.
- Nenhuma dessas execuções comprova autorização de servidor, transação atômica real, acessibilidade por leitor de tela, consentimento, retorno bancário ou integração produtiva. O índice histórico 19F=69/100 permanece sem nova medição.

## Contratos pendentes para S0/S1 (sem decisões unilaterais)
1. Projeção confiável por loja da fila `unassigned`, operação de assunção/atribuição, controle de concorrência e compensação de conflitos/retomada de Consultores elegíveis.
2. Escopo operacional por caso `case_only`, término da concessão na troca do titular, vinculação às sessões GoTrue/RLS, permissões D2/D3/D4/anexos e revalidação de versão.
3. Evidência de contato humano efetivamente iniciado e estado de pausa/redistribuição por evento; a interface não cria nenhum desses eventos.

**Próximo bloco:** FV-22-05/06/07 — segunda conclusão humana após esclarecimento, extração versionada e ficha contínua por cliente/concessionária, preservando snapshots bancários.
