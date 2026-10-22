# FV-AUD-01 — Auditoria estática da implementação Frontend contra decisões de 22/10/2026
**Data da leitura:** 22/10/2026. **Branch:** `feat/frontend-plataforma-visual`. **HEAD auditado:** `b9b16619e04fad3c46eb8d6521ecf3190ba702ff`.
**Tipo:** inspeção de código, contratos, fixtures, testes e árvore GitHub. **Não é:** execução Node/Chromium, teste de segurança autenticado, homologação, validação Meta/Supabase/OpenAI/Banco ou medição de progresso.
**Gate:** nenhum código alterado nesta auditoria; não declarar integração real. Prioridade dos documentos: índice 00 → FV-DOC-03/38 → D-AL/35 e D-NOM/37 → contratos históricos FV-01/02/03. FV-DOC-04/39 foi somente documental.

## Inventário confirmado
- `frontend/visual/`: 41 arquivos (18 itens principais e 23 arquivos em `tests/`, dos quais 19 `*.test.mjs`), HTML/CSS/ESM/fixtures sem backend de produção.
- Os módulos principais incluem `app.mjs`, `fixtures.mjs`, `view-model.mjs`, `cf-op-02.mjs`, `registration-view.mjs`, `bank-view.mjs`, `postmark-view.mjs`, `team-operations.mjs`, `team-pause-preview.mjs`, `team-monitor.mjs`, `team-monitoring.mjs`, `batch-monitor.mjs`, `conversation-attention.mjs`, `s0-read-contract.mjs`, `s0-command-result.mjs`.
- `frontend/docs/`: 40 arquivos Markdown no SHA auditado. 19 testes de unidade/DOM/inspeção de fonte e rotinas opcionais de Chromium/aceite; não executados nesta rodada.
- GitHub: commit consultado era o HEAD informado; consulta de workflows de PR e status combinados desse SHA não retornou execuções/status. Falha de acesso Git local (`Could not resolve host: github.com`) impediu checkout privado nativo na sessão.

## Escala e regra de interpretação
- **ALTA:** incompatibilidade contratual de fluxo/segregação importante para correção na frente visual antes de avançar.
- **MÉDIA:** dívida de contrato, testes, ergonomia ou risco operacional ainda não materializado na demo.
- **BLOQUEANTE PARA PROD:** integração/autorização inexistente, mas NÃO incidente de exposição real neste protótipo local com fixtures sintéticas.
- Não confundir regra de produto aplicada visualmente, hipótese de simulação, autorização S0 nem contrato externo ratificado.

## Matriz de achados rastreáveis
| ID | Gravidade | Achado e evidência de implementação | Fonte vigente / recomendações |
|---|---|---|---|
| FV-AUD-01 | ALTA | Nomenclatura UI ainda mostra **Operador/Responsável** em `visual/index.html` (gestão, ajuda), `visual/app.mjs` (`updateSelectors`, `renderTeamSummary`, indicadores G3), `visual/team-monitoring.mjs`; nomes de status/roles técnicos também são legados. | D-NOM-01; FV-22-02. Trocar **somente rótulos visíveis**, preservar `role='operador'`, status comerciais e contratos internos. Atualizar testes de DOM/texto. |
| FV-AUD-02 | ALTA | `visual/app.mjs`, handler `#composer`: faz `item.messages.push({side:'out',body:text})` sem prévia `Cargo Nome:\nMensagem`, autoria projetada e feedback de status de transporte. `visual/styles.css` `.message p{margin:0}` não garante quebra de linha para assinatura. | FV-DOC-03 §5, FV-22-08/10. Implementar prévia explicitamente sintética com autor real da fixture e estado local separado; nunca fingir assinatura S0 nem envio Meta. Templates não devem receber prefixo livre. |
| FV-AUD-03 | ALTA | `visual/fixtures.mjs`, `visibleConversations`: caso `assignedTo == null` é visível ao Gestor apenas se `teamManagerId === actorId`. `visual/team-monitoring.mjs` repete `inTeamQueue` com esse vínculo. `tests/fixtures.test.mjs` matriz combinatória de 7.168 asserts codifica a regra antiga. | D-AL-04/05/06, FV-22-13. Separar projeção de fila compartilhada por **concessionária autorizada** da supervisão dos casos da equipe; assunção atômica depende de S1. Atualizar fixtures/testes com dois gestores e mesma loja. |
| FV-AUD-04 | ALTA | `visual/app.mjs` bloqueia composição/conclusão quando existe `state.processing[caseId]`; `cf-op-02.mjs` trata qualquer conclusão simulada como impeditivo de texto; há cenário parcial mas não UX de **esclarecer e concluir novamente**. O teste `app.dom.test.mjs` verifica só o primeiro bloqueio. | FV-DOC-03 §3 itens 6/8; FV-22-05/06. Modelar estados técnicos por **evento de conclusão**, retomada de atendimento autorizada e novo pedido independente, sem supor endpoint/cutoff físico. |
| FV-AUD-05 | ALTA | `visual/app.mjs` limpa modais ao trocar ator/loja/caso, mas `changeActor`, mudança de loja e clique em card não limpam explicitamente `#message-input.value`; o rascunho pode permanecer ao mudar contexto. | FV-DOC-03 §§2/5 (isolamento/autoria); FV-22-07/08. Descartar ou segregar rascunhos por contexto e testar troca de concessionária, cliente, Consultor e modal. **Risco prospectivo de mensagem ao caso errado**, sem envio real na demo. |
| FV-AUD-06 | ALTA | `visual/fixtures.mjs` e helpers `currentlyAssigned`/`canWriteNote`/`registrationProjectionFor` exigem `actor.shops.includes(shopId)` sempre; não representam caso transferido com acesso excepcional limitado ao caso sem grant geral. A UI tampouco apresenta ato de transferência. | D-AL-03, FV-22-12. Criar projeção sintética distinguindo grant geral e vínculo excepcional confirmado somente por S0/S1; jamais conceder acesso localmente. |
| FV-AUD-07 | MÉDIA | `visual/s0-command-result.mjs` exporta `HUMAN_COMMAND_IDS` incluindo `C13`, e `tests/s0-command-result.test.mjs` exige C13. Não há editor C13 em O3 e o módulo é classificador candidato isolado, mas a constante é convite a reintroduzir ação antiga. | FV-DOC-03 §3; FV-22-03. Remover C13 da lista de **ações de Consultor na UI** ou isolar com semântica de comando externo não acessível; preservar histórico/contrato alheio. |
| FV-AUD-08 | ALTA | Ficha em `visual/registration-view.mjs` está projetada como propriedade de um `record`/caso (`registrationProjection`), sem projeção consolidada de **cliente + concessionária + versões/snapshots de remessa** em várias conversas; `postmark-view.mjs` só representa vínculo par de casos. | FV-DOC-03 §3 itens 4/8/9; FV-22-07. Planejar view-model para identidade de ficha e histórico autorizados por loja, mantendo snapshots bancários separados; dependência da S0. |
| FV-AUD-09 | MÉDIA | `visual/index.html` + `app.mjs` têm apenas botão de simulação de pausa/retomada e prévia de carteira; não representam ciclo completo `pausa aplicada / redistribuição pendente / caso retido` com resultados/versionamentos externos; falta tela de assunção compartilhada e retorno de leads sem titular. | D-AL-01..09; FV-22-12/13. Evoluir estados de apresentação com fixtures reaisistas independentes e serviços falsos tipados; sem atribuição decidida no navegador. |
| FV-AUD-10 | MÉDIA | `visual/cf-op-02.mjs` protege composer por janela projetada e diferencia pedido de template de envio. Porém o fio da conversa em `app.mjs` só mostra `body/time`; não tem estágios por mensagem `API_ACCEPTED/UNCERTAIN/SENT/DELIVERED/READ/FAILED` nem autoria fixa histórica. | FV-DOC-03 §5; FV-22-08/10. Criar apresentação de status técnico de transporte sem confundir status comercial e sem inferir ACK=envio. Integração exige Meta/S0. |
| FV-AUD-11 | MÉDIA | `visual/README.md` ainda menciona correções excepcionais C13 como pertencentes às frentes responsáveis, sem registrar claramente que Consultor jamais edita ficha. Algumas cópias históricas no visual dizem “responsável/operador”. | FV-DOC-03/D-NOM-01; atualizar README atual, preservando docs históricos 18–20/10 como evidência da época. |
| FV-AUD-12 | MÉDIA | Testes de `fixtures.test.mjs`, `app.dom.test.mjs`, `source-contract.test.mjs` e smoke Chromium verificam premissas legadas; não há evidência nova de execução dos 16 critérios FV-22-01..16. | FV-DOC-03 §8; criar matriz de rastreabilidade requisito→testes e regressões de rascunho, assinatura, fila compartilhada, caso-grant e segunda conclusão. Não reutilizar PASS histórico como homologação atual. |
| FV-AUD-13 | MÉDIA | `visual/styles.css` define `html,body` com `min-width:320px`, `.visual-app{min-height:500px}` e `body{overflow:hidden}`; existe suporte a mobile, skip link, tablist/foco, mas não há ensaio atual de leitor de tela/zoom/baixa altura e pode haver conteúdo inacessível em tela menor. | Critérios de usabilidade FV-01/02 e FV-22; revalidar 320px, zoom 200/400%, altura pequena, foco, teclado, contraste e mensagens de erro. É risco a testar, não defeito visual confirmado. |
| FV-AUD-14 | BLOQUEANTE PARA PROD | `visual/app.mjs` declara aplicação local sem autenticação/rede; seletores de ator/loja são fixtures. `s0-read-contract.mjs` e `s0-command-result.mjs` são classificadores **candidatos**, não Auth/RLS/Meta/S1. O3/O4/G2/G3/G4 não fazem chamadas reais. | FV-DOC-03 §9, FV-DOC-04. Isolar o modo demo; não publicar como operação real. Integrações exigem contratos S0/S1/Meta/OpenAI/Banco, autenticação/autorização e testes externos. |

## Pontos positivos observados estaticamente
- **O3 sem editor cadastral:** `registration-view.mjs` e renderização `extraction` em `app.mjs` apresentam campos aplicados com fonte/versão e lacunas, sem formulário C13; supervisor vê somente resumo sintético D2. Concorda com FV-22-03 no protótipo.
- **Separação de autoridade bancária:** `bank-view.mjs` requer prova/versão sintéticas, não oferece envio nem venda. `postmark-view.mjs` conserva ciclo original e requer vínculo S0 fictício coerente.
- **Pausa conservadora:** `team-pause-preview.mjs` não reatribui e requer prova explícita; mesma equipe e grant previstos para caso existente, sem substituto mantém titular.
- **Janela Meta:** `cf-op-02.mjs` usa projeção externa fictícia em vez de relógio do navegador e separa template individual de cadeia F02. Não considera expiração conclusão humana.
- **Indicador único:** `conversation-attention.mjs` implementa `COUNT/DOT/NONE` e a leitura de supervisor não altera o titular em simulação; política após transferência permanece aberta.
- **Escopo primeira versão:** não existe painel ativo para IA de melhoria ou administração MCP inventada, e a marca da aplicação não é LiberaCred.
- **Defesas de UI:** textos inseridos via `textContent`/`createElement`; limpeza de modais no contexto antigo; abas de detalhes têm `role=tablist`, foco por teclado, skip-link e pontos de responsividade.

## Matriz preliminar de FV-22-01..16 (não é resultado de aceite)
| Critério | Resultado da inspeção estática |
|---|---|
| 01 Identidade plataforma | COMPATÍVEL NO VISUAL |
| 02 Nomes Diretor/Gestor/Consultor | INCOMPATÍVEL: FV-AUD-01 |
| 03 Ficha sem edição manual | COMPATÍVEL NA DEMO; autorização S0 pendente |
| 04 Clique conclusão isolado de status | PARCIAL: demo correta, comando real não existe |
| 05 Múltiplas conclusões e cutoff | INCOMPLETO: FV-AUD-04 |
| 06 Esclarecimento pós-extração | INCOMPLETO: FV-AUD-04 |
| 07 Ficha por cliente/loja/snapshots | INCOMPLETO: FV-AUD-08 |
| 08 Assinatura/previsualização/retry | INCOMPATÍVEL: FV-AUD-02/05/10 |
| 09 Janela Meta versus conclusão | PARCIAL: guarda visual sintética |
| 10 ACK e transporte técnico | INCOMPLETO: FV-AUD-10 |
| 11 COUNT/DOT/NONE e leitura supervisor | PARCIAL: demo correta, herança/servidor pendentes |
| 12 Pausa e redistribuição | PARCIAL: prévia correta, demais estados faltantes |
| 13 Fila compartilhada/assunção/retomada | INCOMPATÍVEL/INCOMPLETO: FV-AUD-03/09 |
| 14 IA melhoria excluída e F01 sem quadro humano | SEM MENU INDEVIDO; tráfego real F01 não avaliável |
| 15 Status após F03 e provas bancárias | PARCIAL: nenhum efeito indevido na demo, sem integração |
| 16 Sem menus inventados para MCP/campanhas | COMPATÍVEL NA DEMO |

## Plano recomendado de reparação na frente Frontend
1. **P1 – segurança de contexto e aderência de UX:** limpar/segregar rascunho em trocas; ajustar títulos e rótulos atuais; modelar composição/prévia/assinatura humana candidata com testes e estados de envio, sem chamada real.
2. **P1 – isolamento e distribuição:** separar projeções de supervisor de equipe da fila sem titular por concessionária; representar grants gerais versus exceção por caso; atualizar testes e simulações de concorrência/assunção/retomada, sem atribuir no browser.
3. **P1 – conclusão/extração:** representar eventos de conclusão distintos, revisão de lacunas, histórico de solicitações/cutoffs técnicos e ciclo da ficha por cliente+loja, com resultados originados de projeção autorizada.
4. **P2 – higienização contratual e testes:** restringir C13 visível, atualizar README e suíte conforme 16 cenários; executar Node, Chromium, acessibilidade e revisão de responsividade em checkout privado autorizado.
5. **Integrações bloqueadas:** acertar contratos S0/S1 para versão de caso/ciclo, fila/assunção/grant, prova de envio/leitura, autorização D2/D3/D4 e extração F03; não simular nada como produção.

## Limitações e aceitação
- Este diagnóstico foi produzido por leitura direta de GitHub conectado no SHA acima. Nenhuma suíte Node/Chromium foi reexecutada; não afirmar regressão verde nem A11y homologada. GitHub Actions/status para HEAD não retornaram execuções na consulta; isso não prova inexistência de outros pipelines.
- Não se auditou execução real de GoTrue/RLS/Supabase, chamadas Meta, OpenAI, MCP ou Banco. Os achados de risco de autorização são **bloqueios prospectivos de integração**, não evidência de vazamento real de clientes.
- **19F=69/100 permanece referência histórica, não nova medição. FV-UI-013 não está homologada.** Esta auditoria habilita planejamento de Etapa 2, não certifica conclusão de Etapa 1 de homologação.
- R-SIGLA-01, R-CFI-01, R-S1-01, R-LEITURA-01, R-CAD-01 e R-RETENCAO-01 continuam pendências de contrato entre frentes e não devem ser decididas unilateralmente pelo Frontend.

## Referências
- [Índice vigente](./00_COMECE_POR_AQUI_DECISOES_VIGENTES_2026_10_21.md); [FV-DOC-03](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md); [FV-DOC-04](./39_FV_DOC_04_AUDITORIA_DOCUMENTAL_FRONTEND_2026_10_22.md); [D-AL](./35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md); [D-NOM](./37_D_NOM_01_NOMENCLATURA_DIRETOR_GESTOR_CONSULTOR_2026_10_21.md).