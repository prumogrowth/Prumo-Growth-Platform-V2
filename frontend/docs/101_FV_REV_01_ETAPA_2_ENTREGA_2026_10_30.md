# FV-REV-01 v0.4 — Etapa 2: entrega para auditoria independente

30/10/2026. Repositório oficial: `prumogrowth/Prumo-Growth-Platform-V2`. Branch: `codex/fv-rev-01-modulos-20261030`, descendente de `17336799ddf4c8575c790f09eb64570d6460733c` (Etapa 1 aprovada). Sem merge, deploy, publicação de site ou integração produtiva.

A [fonte integral v0.4](FV_REV_01_v0_4_FONTE_2026_10_29.md) foi recebida e lida antes da implementação. SHA-256 do arquivo original: `1f4134397a2ffa677303e0b06203b772d986b97cda598dfbfec0fc193085c35b`. Seu estado histórico de autorização e seu antigo endereço de repositório não prevalecem sobre a missão posterior. O [mapa 100](100_FV_REV_01_ETAPA_2_MAPA_2026_10_30.md) registra o inventário, origem, perfis, destinos e testes antes da realocação.

## Resultado e realocação

A base existente de Conversas foi preservada. Banco reaproveita os renderizadores de Extração e Banco em diálogo próprio e rolável, acessível pela navegação e pelo Resumo. Sua seleção de caso é independente da conversa: consultar ficha não seleciona, lê, reabre ou inicia atendimento. O seletor contém somente casos já autorizados da concessionária corrente. Consulta, lacunas, conflitos, versões, processamento, aptidão, solicitação, comprovação e resultado permanecem separados. Nenhum campo cadastral pode ser editado; nenhuma remessa real pode ser solicitada.

`renderRegistration` conserva dados confirmados, fontes, versões, conflitos, ausências, falhas, cenas alternativas, cortes candidatos, dossiê e snapshots das funções existentes. `registrationProjectionFor`, `projectMockCustomerDossier` e `bankProjectionFor` mantêm suas restrições, inclusive a restrição atual de detalhes cadastrais ao titular de caso ativo. Uma eventual consulta produtiva mais ampla a histórico depende de projeção/autorização explícita do S0, não de flexibilização no browser. O Gestor supervisor não recebe D3/D4, versões de campos nem provas bancárias. Aptidão demonstrativa também exige a mesma versão confirmada da ficha e não habilita remessa.

O painel tem somente Resumo, Histórico e Notas. O nome repetido foi removido, preservando caso e estado comercial compactos. Resumo substitui a seção visual de regras por publicações acumulativas e expansíveis F01/F02 e resultados confirmados F03 autorizados. Solicitações técnicas locais aparecem como avisos, sem se tornarem publicações confirmadas ou conversa da F03 com o cliente. Rascunhos de notas ficam separados das notas submetidas, isolados por ator/loja/caso e limpos na troca de perfil/loja.

Histórico passa a mostrar acontecimentos operacionais e estados técnicos, sem repetir todas as mensagens. Vínculos pós-remessa e pós-venda usam as verificações recíprocas e de acesso já existentes; os botões apenas navegam entre casos previamente projetados. Há grupos separados de acontecimentos e planejamento, com linha interrompida antes do futuro. Estados de execução, envio confirmado, solicitação, falha, incerteza e cancelamento têm rótulos. Cancelamento projetado remove tentativas do futuro, mantendo o registro histórico e os envios comprovados anteriores. Nenhum prazo é calculado pelo relógio do navegador.

Gestão reaproveita sua superfície própria (`team-dialog`) e mantém equipe, supervisão, pausa/retomada, monitoramento, lotes e distribuição/fila compartilhada. A navegação móvel para módulos fica separada do cabeçalho de filtros da conversa. Nenhuma concessão, atribuição ou responsabilidade foi ampliada.

Arquivos centrais: `app.mjs`, `index.html`, `styles.css`, `view-model.mjs`. Novos `revision-fixtures.mjs` e `relationship-view.mjs` contêm somente cenas e projeções sintéticas. As fixtures originais, os oito estados, predicados de comunicação, autorização, banco, cadastro e continuidade não foram reescritos. O diff e a lista integral são registrados em `PROVENIENCIA.json` da prévia, comparados ao SHA aprovado.

## Matriz FV-REV-001 a 037

“Implementado” abaixo significa apresentação/interação sintética, não integração produtiva ou ratificação de contratos. COR-01..06 permanecem cobertas pela suíte anterior `browser.revision.py` e pelos testes Node de conversas.

| Item | Atendimento nesta entrega | Evidência principal |
| --- | --- | --- |
| 001 | Preservado P superior único e navegação extensível; Banco/Gestão acrescentados | `browser.revision`, `browser.modules`, markup |
| 002 | Banco independente, ficha read-only sem iniciar conversa; etapas distintas | `modules.dom`, `browser.modules`, `bank-view` |
| 003 | Preservados três pontos/tema e laboratório demonstrativo separado | `browser.revision`, `browser.communication` |
| 004 | Preservados filtro junto a configurações, identificação da loja e escopo | COR-01/02, `browser.revision` |
| 005 | Estados canônicos preservados; filtros do Consultor continuam simplificados | `revision-conversations`, `fixtures`, `browser.revision` |
| 006 | Busca preservada sem Ctrl/⌘ K | `browser.smoke`, `revision-conversations` |
| 007 | Lista contínua ativos/históricos e filtros diretos preservados | `browser.revision` |
| 008 | Duas linhas e última mensagem confirmada preservadas | COR-02, `conversation-attention`, `browser.revision` |
| 009 | Sem avatares decorativos; janela Meta independente | `browser.revision` |
| 010 | Indicadores do titular, verde/quente e identificação não só por cor | COR-03, `attention-integration`, `browser.revision` |
| 011 | Etiquetas redundantes continuam ausentes; marcos aparecem em Histórico/Banco | `browser.revision`, `browser.modules` |
| 012 | Nome acessível abre informações, preservado | `browser.revision` |
| 013 | Conclusão verde autorizada no cabeçalho e confirmação preservadas | COR-04, `browser.revision`, `app.dom` |
| 014 | Avisos de erro/impedimento/incerteza preservados | `browser.smoke`, `transport-state-view` |
| 015 | Texto, emoji e áudio local preservados quando elegíveis | `browser.communication`, `local-audio`, `communication-composer` |
| 016 | Substituição efetiva por 0/1/2 ações; negativas conservadoras | COR-05, `browser.revision` |
| 017 | Faixas terminais verde/vermelha sem composer residual, preservadas | COR-06, `browser.revision` |
| 018 | Nome/avatar repetidos removidos; contexto compacto de caso/status mantido | `modules.dom`, `browser.modules` |
| 019 | Rótulos/valores alinhados; quebra organizada no responsivo | `browser.smoke`, capturas Etapa 2 |
| 020 | Seção visual Regras da experiência removida; predicados mantidos | `modules.dom`, regressões de domínio |
| 021 | Histórico acumulativo de comunicações F01/F02/F03 no Resumo | `relationship-view`, `modules.dom`, `browser.modules` |
| 022 | Exatamente Resumo, Histórico, Notas | `view-model`, `modules.dom`, `browser.modules` |
| 023 | Extração realocada integralmente para Banco e feedback Resumo/Histórico | O3/FV-UI-019/032 em `app.dom` e `browser.smoke` |
| 024 | Banco realocado para módulo próprio; marcos no Histórico | O4 em `app.dom`, `browser.smoke`, `browser.modules` |
| 025 | Vínculos no Histórico; retorno humano pós-remessa/venda sem reativar F01 | `postmark-view`, O5 em `browser.smoke`, `browser.modules` |
| 026 | Recontatos no Histórico, estados e futuro separados | `relationship-view`, `browser.modules` |
| 027 | Notas e permissões mantidas; rascunho não submetido preservado | `modules.dom`, `app.dom`, `browser.modules` |
| 028 | Eventos operacionais, atribuição e transferência; sem replicar mensagens | `relationship-view`, `browser.modules` |
| 029 | Continuidade contextual por vínculos explícitos da mesma loja | `postmark-view`, `relationship-view`, `browser.modules` |
| 030 | Futuro distinto; cancelamento não continua agendado | `relationship-view`, `browser.modules` |
| 031 | Claro/escuro preservados nas três superfícies | `browser.smoke`, `browser.modules`, capturas |
| 032 | Base neutra e cores operacionais, sem substituir semântica por cor | `browser.revision`, `browser.modules` |
| 033 | Verde/vermelho/cinza/quente e contraste nos dois temas | `browser.revision`, `browser.modules` |
| 034 | Círculos/linha reaproveitados; futuro sem prolongar a linha realizada | `browser.modules`, capturas histórico/recontatos |
| 035 | Largura estável do painel preservada; Banco também usa gutter estável | `browser.revision`, `browser.modules` |
| 036 | Conversas compartilhada; Gestão própria, módulos e permissões mantidos | suítes de equipe/distribuição/lotes, `browser.modules` |
| 037 | X, reabertura, foco e dados não submetidos preservados | `browser.revision`, `browser.communication`, `browser.modules` |

## Matriz AT-01 a AT-07

| AT | Atendimento | Limite preservado |
| --- | --- | --- |
| AT-01 | Consulta independente, somente leitura, dados F01/F03 e versões; preparação/remessa/resultado distintos | Nenhuma API bancária; aptidão não é comando ou prova de remessa |
| AT-02 | Conteúdo de Extração reutilizado em Banco, avisos no Resumo e eventos no Histórico | Falha, parcial, obsoleto e incerto não sobrescrevem ficha confirmada |
| AT-03 | Publicações acumulativas, origem e momento; resultados F03 só pela projeção confirmada autorizada | Sem publicação externa, persistência inventada ou F03 conversacional |
| AT-04 | Escopo pré-filtrado, vínculos recíprocos e casos da mesma loja | Nunca associa por nome/CPF/telefone; não concede acesso por consulta |
| AT-05 | Rótulos e grupos para planejamento/solicitação/execução/confirmação/falha/incerteza/cancelamento | Pedido local não vira enviado; cancelamento preserva evidências históricas |
| AT-06 | Preservação integral COR-05/06 e das negativas de janela/permissão | Sem capacidades novas ou inferência de janela expirada |
| AT-07 | Mapa 100, destinos redirecionados e testes anteriores mantidos; foco nos novos controles persistentes | Gates nativos, inventário e proveniência não flexibilizados |

## Pendências P01 a P13

| Pendência | Situação visual/técnica | Dependência externa ou futura |
| --- | --- | --- |
| P01 — filtros | Preservados e cobertos por COR-01/02 e regressões por perfil | Autorização produtiva do S0 |
| P02 — Banco | Organização e consulta read-only demonstradas; aptitude versionada | Contratos, permissões e provas de remessa/resultado ratificados por S0/Banco |
| P03 — comunicações | Apresentação acumulativa sintética e minimizada implementada | Publicação, armazenamento, autorização e leitura reais de S0/F01/F02/F03 |
| P04 — Histórico | Ordenação por sequência explícita da fixture; sem inventar horários ausentes | Catálogo/versionamento/ordenação autoritativa de eventos S0 |
| P05 — recontatos | Estados, cancelamento e futuro demonstrados/testados | Projeções reais F02/S0/Meta e evidências de envio/cancelamento |
| P06 — cores | Tratamentos acessíveis nos dois temas; contraste verificado no Chromium | Aceite visual humano e tecnologias assistivas |
| P07 — composer | Preservadas todas as capacidades/negativas e faixas terminais | Canal real e permissões produtivas, fora desta missão |
| P08 — responsividade | Desktop/tablet/celular, 320px e paisagem baixa no Chromium; reflow anterior mantido | Dispositivos físicos, zoom nativo e tecnologias assistivas continuam validações humanas |
| P09 — Gestor | Módulos existentes preservados em Gestão; nenhuma ampliação operacional | Revisão funcional/visual futura mais ampla não foi antecipada |
| P10 — Diretor | Fora do escopo; nenhuma interface nova ou permissão criada | Missão futura específica |
| P11 — distribuição das informações | Mapa e destinos concluídos antes da remoção das abas | Aceite da orquestração/auditoria independente |
| P12 — navegação/acessibilidade | X, teclado, foco, ciclos e destinos cobertos no navegador | Avaliação com leitores de tela/dispositivos físicos |
| P13 — regressão | Suítes antigas preservadas, expectativas de destino atualizadas e regressões novas | Conferência independente de logs/artefatos no SHA final |

## Validação, incidentes e evidências

As 405 regressões Node anteriores foram mantidas e acrescentadas 24: 429 verificações. As jornadas O3/O4/FV-UI-019/032 da antiga Extração/Banco agora usam o destino Banco; Novo contato/Recontatos usam Histórico. O foco que antes retornava à aba Extração agora retorna ao seletor persistente do Banco. End na lista de abas agora alcança Notas. Tipografia antes verificada no perfil duplicado agora é verificada no contexto compacto. Asserções de valores, fontes, versões, cortes, isolamento, negativa de permissões e ausência de edição não foram removidas.

A matriz nova de Chromium exercita 20 combinações: 1440×900, 900×780, 390×844, 320×640 e 740×390, Consultor/Gestor, claro/escuro. Verifica geometria, visibilidade real, contraste, read-only, leitura do titular intacta durante consulta, três abas, publicações acumulativas, notas, retorno de foco, vínculos pós-venda/remessa, recontatos e Gestão. Casos adicionais injetados no runtime sintético verificam solicitação bancária sem prova, resultado sem prova e cancelamento projetado de plano. Não há force-click para superar problemas de layout.

O gate obrigatório continua: Git limpo/branch exata → inventário/bytes pinados → segurança Python → todas as suítes Node → Chromium legado + comunicação + COR-01..06 + módulos. O workflow só acrescenta a branch exata, a nova matriz e os artefatos documentais; versões de ferramentas, limites e proteções existentes foram mantidos. A execução certificada e o SHA final constam do JSON/log do run associado a esta entrega. Um diagnóstico inicial foi bloqueado pela allowlist ainda não atualizada; não foi contado como execução das suítes. Uma execução local teve timeout de navegação HTTP loopback (6500ms); o diagnóstico foi inconclusivo. Uma execução longa de smoke foi interrompida para inspecionar progresso e também não equivale a PASS. O run intermediário 41099511633 identificou uma corrida na preparação da jornada da segunda conclusão: o helper escolhia o painel antigo antes do callback nativo abrir Banco. A jornada agora exige a abertura visível de Banco antes de verificar o corte candidato; nenhuma asserção ou timeout foi reduzido/relaxado. Somente a execução completa certificada pode ser declarada aprovada no relatório à orquestração.

A prévia integral inclui HTML único e ZIP ESM, sem rede de negócio ou publicação. `PROVENIENCIA.json` vincula HEAD/branch/base, lista de arquivos alterados e hashes dos pacotes. Mantêm-se 108 capturas da Etapa 1 e 22 cenas legadas, e acrescentam-se 132 capturas da Etapa 2 com índice por SHA/hash: Resumo/IA, Histórico, Notas, ficha/remessa/versões, continuidade, recontatos realizados/futuros e quatro painéis gerenciais. Todas são geradas somente depois do gate completo no workflow.

## Auditoria independente recomendada

Conferir ancestralidade no commit aprovado, diff restrito, SHA do run e proveniência dos pacotes. Revisar especialmente ausência de D3/D4 no DOM do supervisor, consulta bancária sem leitura da conversa, aptidão vinculada à versão atual, manutenção dos snapshots, cancelamento fora do futuro, comunicação F03 não conversacional e retorno humano por vínculos recíprocos. Comparar as capturas com a fonte integral e avaliar navegação por leitor de tela/dispositivo físico. Foi corrigida somente a descrição de continuidade em `postmark-view.mjs` para distinguir pós-venda de pós-remessa; os predicados e vínculos permanecem. Eventos terminais do Histórico também utilizam verde/vermelho com contraste verificado. A próxima fase é auditoria: esta entrega não autoriza correção automática posterior, merge, integração ou publicação.
