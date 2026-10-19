# S1 — Registro de aceite e limites

## S1-001 — Central de operações humana sintética (18/10/2026 UTC)

**Resultado:** [GitHub Actions S1 #39133454184 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39133454184). Commit testado `6bd187148da74da6906493b0e2a97d817ffe84ba`, workflow `.github/workflows/s1-synthetic-ui.yml`. Foram executados `node --check`, **24 testes Node 22 (18 de domínio, 6 de montagem fake-DOM), 24 PASS e 0 FAIL**, e verificações de arquivos HTML/CSS/README. Antes dos smoke tests, [#39133175311 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39133175311) passou nos 18 primeiros testes. O workflow foi restringido a PR/manual para evitar duas rodadas por commit.

**Código:** `frontend/s1/index.html`, `styles.css`, `app.mjs`, `domain.mjs`, `tests/domain.test.mjs`, `tests/app.smoke.test.mjs`, `README.md`. Primeira UI de gestor e operador em memória de navegador, sem pacotes terceiros ou solicitações externas. O HTML referencia apenas CSS e módulos locais. A app renderiza conteúdo dinâmico via `textContent`. Não há tokens, dados pessoais verdadeiros, login, cookies, `fetch`, `localStorage`, Supabase ou Graph.

**Aceites específicos:** mesma identidade telefônica fictícia A/B sem cruzamento de leads; gestor vê apenas concessionária própria; operador vê somente os próprios casos com atribuição vigente; atribuição exclusiva para operador da mesma loja; handoff humano suspende IA; versão otimista bloqueia comando stale; notas internas não se tornam outbound; primeiro disparo/triagem IA/remessa ao banco são explícitas simulações; venda somente após estado cadastrado no banco e evidência manual fictícia; perda com motivo humano; exatamente oito estados comerciais.

**Limitações:** teste de fake DOM não é teste em navegador nem screenshot; nenhuma homologação visual, mobile, WCAG, foco de teclado, sessão GoTrue, RLS, acesso D2 real, D3/D4, banco, n8n, Meta, OpenAI API, worker ou persistência. As duas wrappers comerciais legadas da S0 continuam `SECURITY DEFINER postgres`. S1-001 não significa fase S1 completa. Em especial, alternar perfil com um `select` é somente encenação e **não autentica ninguém**.

**Documentos:** `docs/S1_001_JORNADA_HUMANA_VISUAL_2026_10_18.md`, `docs/MAPA_MENTAL.md`, este arquivo de aceite e `frontend/s1/README.md`.

**Governança:** PR #1/#2 Draft, sem merge. Não houve migrations no Supabase hospedado, instalação de frontend público, chave real, tráfego Meta/Banco ou operação produtiva. **GO para revisar visualmente a demo local e planejar S1-002 com backend autenticado; NO-GO para publicação/uso com clientes reais.**


## Auditoria retroativa S1-001 — handoff antes do primeiro disparo

[**GitHub Actions Node 22 #39134672559 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39134672559), SHA `360b1a8d2c5bbfa6ae239344ee5d011583c815a4`: **27 testes PASS, 0 FAIL** (21 domínio, seis DOM simulado). **AUD-S1-01:** a atribuição de caso ainda aguardando primeiro disparo gerava suspensão de IA e um caminho humano inacessível; no protótipo, essa atribuição agora é negada até projeto de handoff inicial real. **AUD-S1-02:** o primeiro disparo não pode ocorrer se a IA estiver suspensa. **AUD-S1-03:** perfil inválido, loja errada e versão obsoleta não alteram estado. A S1 ainda carrega todas as fixtures fictícias no navegador: filtro visual **não é confidencialidade**. Não houve browser/screenshot real, login, RLS ou backend persistente. Ver `docs/AUDITORIA_S0_037EF_S1_001_2026_10_18.md`. **GO para desenho controlado S1-002; NO-GO para uso com clientes reais.**


## D-ORG-01 — governança organizacional do demonstrador

**Alinhamento organizacional D-ORG-01 (18/10/2026):** gestores e operadores são profissionais **da Prumo**, inclusive quando dedicados exclusivamente a uma concessionária. Loja é escopo de atendimento, não vínculo empregatício. Uma pessoa pode ter múltiplas lojas por concessão explícita; gestor pode autoatribuir caso segundo D41-04. Ver `docs/D_ORG_01_EQUIPE_PRUMO_2026_10_18.md`. A demo ainda não implementa múltiplas concessões por usuário nem gestor atuando como operador autoatribuído, funcionalidades aprovadas/necessárias para futura S1-002. Não interpretar os perfis exclusivos dos testes como funcionários das lojas. Validar o próximo commit S1 antes de acrescentar números de aceite.


## AUD-ORG-01 — equipe Prumo e escopo de concessionária (18/10/2026)

[GitHub Actions S1 #39136909717 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39136909717), SHA `806d6465c1ec28c64cc67cc5154977a49b48f538`: **28 testes PASS, 0 FAIL**, incluindo `AUD-ORG-01` para os cinco atores fictícios de `frontend/s1/domain.mjs`. Cada um tem `organizationId: "prumo"`; `shopId` representa apenas **escopo de concessionária selecionado na demonstração**, nunca vínculo profissional com a loja. UI atualizada para exibir “Gestor/Operador da Prumo · escopo [concessionária]”. Ver norma [D-ORG-01](../docs/D_ORG_01_EQUIPE_PRUMO_2026_10_18.md) e [auditoria documental](../docs/AUDITORIA_EQUIPE_PRUMO_DOCUMENTAL_2026_10_18.md). S1-002 ainda necessita autorizações multi-loja e gestor autoatribuído D41-04, com autenticação/RLS persistentes. **Sem novos grants, migration, merge ou produção.**


## S1-002/I1 — Portão de equipe Prumo (candidato 18/10/2026)

**CI ainda não verificado neste registro.** Os testes candidatos `S1E-01..07` cobrem cobertura das políticas RLS existentes, gestor Prumo A+B sem C, operador A+B apenas por caso, concessão sem pertencimento à equipe, tentativa de autoconcessão, suspensão da leitura/escrita via role `authenticated`, histórico SQL e a lacuna explícita de atribuições ainda ativas após desligamento. Runner `scripts/run-s1-002-local.sh` executa S0 antes da 038, sem provar regressão completa S0 após 038 nem Auth/REST pós-038. Fonte de admissão Prumo, política de reativação e remanejamento continuam pendentes. **NO-GO para implantação.** Ver `docs/S1_002_EQUIPE_PRUMO_PORTAO_INICIAL_2026_10_18.md`.

**Execução confirmada:** [GitHub Actions #39145994842 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39145994842), SHA `bbe123aa18098848d9f9c936f4f0e02be57447af`, PostgreSQL 17 descartável. Logs conferidos: **S1E-01..07 PASS**; regressão S0 pré-038 também concluída. O cenário S1E-07 comprova explicitamente que duas atribuições continuam ativas após desligamento: **isso é lacuna, não aceite de remanejamento**. Auth/REST pós-038, revalidação de wrappers privileged, remanejamento e origem administrativa continuam NO-GO.


## S1-002/I2 — Remanejamento transacional sintético (18/10/2026)

**Implementação proposta, evidência CI pendente:** migration 039, trigger de suspensão/desligamento e revogação da última concessão por loja, guarda para novas atribuições, redistribuição somente a profissionais Prumo ativos e autorizados da mesma loja, e fila privada protegida quando não há operador elegível. Atributos e status comerciais não são alterados; venda/perda histórica apenas encerra atribuição residual. Gestores não são autoatribuídos automaticamente; continuam sujeitos a D41-04. O S0 continua dono do caso e da decisão comercial, OpenAI/Meta/Frontend não recebem SQL novo.

**Testes candidatos S1R-01..08:** escopos independentes A/B/C, profissional pendente, revogação B sem afetar A, suspensão com redistribuição para 2 operadores, fila protegida, status terminal preservado, gestor supervisor, RLS de suspenso, reativação sem reocupar caso, bloqueio de nova atribuição e execução privada negada para `authenticated`. Runner executa I1 primeiro e I2 depois, somente em PG17 fictício. **Nenhum PASS deve ser declarado antes dos logs do job.** Não há teste integrado GoTrue/REST após 039 nem prova concorrente intersessões.

**Lacunas reais:** autoridade administrativa confiável de suspensão; regras de escala/capacidade; expiração FUTURA de grant pelo relógio (sem update SQL não chama trigger); interoperabilidade com eventos de conversa/Meta e planos, mitigação de corridas intersessões, cobertura de wrappers S0 privilegiadas, revisão de carga total e catálogo bancário. Todos são gates de produção [R/V]. **Sem merge, deploy, credenciais reais ou incremento artificial da régua global.**


**Evidência CI efetivamente verificada:** [GitHub Actions PostgreSQL 17 #39159483920 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39159483920), SHA `2435264f56f36a572382b7e27d5c773e0e921453`, job `117769573687`. Logs inspecionados: S1E-01..07 PASS (**I1 antes da migração 039**), S1R-01..08 PASS (**I2 após 039**) e execução da regressão S0 **antes da 038/039**. O teste S1R-04 verificou 3 casos da loja A repartidos entre 2 operadores, 1 caso de C em fila protegida, história preservada e caso vendido sem reabertura. S1R-03 confirmou revogação de B sem tocar A; S1R-05/08 negaram acesso de suspenso e executor privado. **Não é prova de login GoTrue/REST pós-039, de corrida intersessões ou de segurança das wrappers S0.** O status do incremento é **PASS somente no escopo sintético registrado; NO-GO produção**.


**Evidência adicional de guarda de atribuições:** [CI PG17 #39159745461 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39159745461), SHA `47a9dd80b12ee874bd9cc4aeb680196f6acd1dc8`, job `117770353279`, logs conferidos: **S1R-01..09 PASS (9/9)**, S1E-01..07 PASS antes da migração 039, regressão S0 também pré-038/039. S1R-09 é teste NEGATIVO com caso C sem atribuição ativa e suspenso tentando assumi-lo, isolando efetivamente o guard de elegibilidade da simples restrição de unicidade. Permanece NO-GO em produção, GoTrue/REST e prova de concorrência de duas sessões.


## S1-002/I3 — Reconciliação de concessões vencidas pelo relógio [ensaio pendente]

A migration `202610180040_s1_concessoes_expiradas_reconciliacao.sql` acrescenta **somente uma função interna de varredura limitada e idempotente**: detecta atribuições que ficaram ativas após expirar, sem UPDATE SQL, o último vínculo permitido por loja ou após falta de pertencimento ativo à Prumo. Reaproveita o mecanismo privado e auditado de I2; **não implementa cron, scheduler, API pública nem alteração no Supabase hospedado**.

Cenários `S1X-01..07` no PG17 fictício abrangem A preservada, B redistribuída, C em fila protegida, RLS negando lojas com concessão vencida antes da varredura, execução em lotes, idempotência, bloqueio de `authenticated` e rejeição de lote inválido. **Provas/CI ainda pendentes nesta redação; não considerar concluído até conferir os logs.**

A varredura **não acontece automaticamente pela simples passagem do tempo**: futuramente requer executor confiável autorizado (agendamento não decidido). Não altera status de venda, roteamento S0, modelo Meta ou OpenAI. Escala e gestão administrativa, integração Auth/REST, testes de corrida e projeto de scheduler permanecem [R/V].


**Evidência executada de I3:** [CI PostgreSQL 17 #39161092070 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39161092070), commit `2a800609acfc3aaf151c29dc0c89a45bfebde9c9`, job `117774376189`; logs auditados: **S1X-01..07 = 7/7 PASS**. O mesmo runner também exercitou S1R-01..09 e S1E-01..07 no seu escopo sintético. Não há cron nem execução automática do reparo pela passagem do tempo; função exige acionamento por executor interno confiável. Sem Auth/REST integrado nem teste intersessões. **NO-GO para produção.**


## S1-002/I4 — ensaios de duas sessões PostgreSQL [P; aguardando execução]

Script `scripts/test_s1_002_concurrency.sh` usa apenas banco `localhost/prumo_s0_test_*` e dados fictícios. Os cenários S1C-01..05 abrangem: atribuição nova concorrendo com suspensão, duas transições de equipe no mesmo profissional, duas reconciliações simultâneas de concessão B vencida, histórico único e rejeição de executor autenticado. A etapa usa o contrato de I2/I3, sem novas migrações, sem API pública, sem chamadas Meta/OpenAI/Banco e sem Supabase hospedado. **Não marcar PASS antes do GitHub Actions.**

**Fora do escopo:** GoTrue real, fluxo REST, execução com worker/scheduler, dupla suspensão de dois operadores distintos e política formal de expediente/plantão; requerem ensaios e revisão separados.


## I4 — Primeira evidência de concorrência entre sessões

[GitHub Actions PG17 #39163239631 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39163239631), SHA `b0b5b5509107b15b4b42b7adeacc1695ff11c11d`, job `117780772360`: logs verificados **S1C-01..05, 5/5 PASS**. Suspensão versus nova atribuição, dupla mudança do mesmo profissional, reconciliação simultânea de concessão B, escopo privado negado a authenticated. A linha ERROR PROFISSIONAL_PRUMO_INELEGIVEL é **erro esperado e validado do teste negativo**; o job terminou SUCCESS. Não foi simulada suspensão simultânea de **dois** profissionais distintos neste ensaio.


## I5 — Proteção contra interbloqueio de duas suspensões [P; ensaio pendente]

Nova migration sintética `202610180041_s1_prevenir_deadlock_remanejamento.sql` reimplementa **somente** `prumo_private.s1_remanejar_ator` com `FOR SHARE ... SKIP LOCKED`: candidato cuja equipe/concessão esteja bloqueada em outra transação **não pode ser destinatário naquele momento**; selecionar outro operador Prumo ativo e desbloqueado, ou conservar em fila protegida se não houver alternativa. Evita aguardar outro operador simultaneamente suspenso e provocar deadlock mútuo. Não muda a elegibilidade comercial ou status do caso e não executa RLS/ação no browser.

`scripts/test_s1_002_simultaneous_suspensions.sh` exercita S1D-01..05: A com terceiro profissional e carteira carregada; dois suspensos simultâneos migrando para terceiro; B com apenas dois suspensos e fila protegida; RLS; rerun sem duplicidade. **Ainda não executar/homologar fora do PG17 descartável.** Fila protegida após corrida exige política/worker de reatribuição futura [R] — a função 040 atual reconcilia atribuições ativas inválidas, não consome pendências sem titular. Sem autorização RH, cron ou API real.


## Evidência integrada S1-002/I4–I5 — 18/10/2026

[**GitHub Actions PG17 #39164266141 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39164266141), commit `326b1713196e510c0f48760e6e368e0677a263ec`, job `117783812725`; logs verificados: **S1E-01..07 (7 PASS), S1R-01..09 (9 PASS em cada uma das duas execuções), S1X-01..07 (7 PASS em cada uma das duas execuções), S1C-01..05 (5 PASS), S1D-01..05 (5 PASS)**. Regressão S0 de base rodou antes da 038; a suíte I2/I3 foi **reexecutada após a migration 041** e passou. Nenhum deadlock/erro inesperado no log; a recusa `PROFISSIONAL_PRUMO_INELEGIVEL` nos testes negativos é esperada. Os testes anteriores #39163601666/#39163765511 falharam por consulta de coluna inexistente ou contagens não isoladas; foram corrigidos e retestados, não são evidência de código produtivo aprovado.

**Limites:** testes locais/sintéticos apenas. Não há GoTrue/REST real após 041, autorização RH confiável, regras de escala/turno, job que drena fila protegida, cron de validade, concorrência distribuída ou cargas reais. Migração 041 evita interbloqueio por candidato de equipe/concessão temporariamente bloqueado usando `SKIP LOCKED`; se não existe destinatário desbloqueado, o caso permanece protegido, sem perda de história. **Sem merge, Supabase hospedado ou alteração das demais frentes; percentual global não atualizado.**


## I6 — Recuperação de fila após ativação/concessão (18/10/2026)

Migr. `202610180042_s1_recuperacao_fila_protegida.sql` e teste `s1_004_recuperacao_fila_protegida.sql` (S1Q-01..10). A rotina privada retira casos da fila quando **novo profissional elegível da mesma loja** surge por ativação ou novo grant, sem devolver automaticamente ao operador anterior, sem atribuir gestor supervisor, sem tocar status comercial e sem abrir dados de outra loja. Pendência terminal ou já reatribuída recebe auditoria e remoção sem segundo titular. Os triggers são limitados a 25 por evento; lote maior exige executor futuro e alerta gestor [R]. **Proposta de teste, ainda sem CI validado.** Ver [contrato I6](../docs/S1_002_I6_RECUPERACAO_FILA_PROTEGIDA_2026_10_18.md). Não rodar em ambiente real.


## S1-002/I6 — Evidência executada e limites (18/10/2026)

**CI funcional PG17:** [GitHub Actions #39167477859 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39167477859), SHA `a438106ecf9e07eecb45a1c7b568d790638854ef`, log do job `117793341159` verificado: **S1Q-01..10, 10/10 PASS** (recuperação em ativação/concessão, ex-operador não reocupa, gerente não autoatribui, ciclo vendido intocado, stale sem duplicação, RLS e executor privado).

**CI concorrência PG17:** [GitHub Actions #39167842391 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39167842391), SHA `2b50344206fff68b30b2a5afc4e5e13c292fe20f`, job `117794451583`; log verificado: **S1QC-01..04, 4/4 PASS** com duas conexões PostgreSQL; uma única atribuição e trilha com dois recuperadores; concorrência com atribuição externa fecha pendência stale; suspenso sem leitura. O mesmo job executou **S1E 7/7, S1R 9/9 duas vezes, S1X 7/7 duas vezes, S1C 5/5, S1D 5/5, S1Q 10/10, S1QC 4/4**.

O ensaio inicial de S1QC [#39167719374](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39167719374) parou após S1QC-02 por comentário Bash incorreto (`--` em lugar de `#`); falha do script corrigida e toda a bateria retestada em #39167842391. **Não** equivale a prova GoTrue/REST, carga, scheduler, integração S0 de fila gerencial ou produção.

**Gates abertos:** alerta/reapresentação da fila ao gestor via projeção S0, processamento de backlog com lote excedente ao gatilho 25, limites de escala/capacidade, identidade real de aprovador RH, grants expirados sem novo evento exigem executor 040, Auth/REST integrado, encerramento/venda/cadastro bancário interfrentes, custo/concorrência de workers, RLS entre equipe/serviço. Sem merge/deploy/Supabase hospedado e sem incremento de percentual global.


## S1-002/I7 — Backlog acima do lote automático [proposta, testes pendentes]

Migração 043: `ultima_inspecao_em` na fila privada, rotação justa de pendências sem operador e entrada interna `s1_drenar_backlog_protegido(loja,max_lotes)` limitada a 10 lotes de 25. Isso elimina o bloqueio por 25 pendências antigas sem candidato, sem atribuir caso a profissional inválido. Não cria cron, worker ou permissão REST, e não altera as outras frentes. Testes S1B-01..10 com 100 registros fictícios, isolamento multiloja e estado vendido. Evidência [P] até PG17. [Descrição I7](../docs/S1_002_I7_BACKLOG_PROTEGIDO_2026_10_18.md).


## Evidência I7 — 100 casos sintéticos, 18/10/2026

[**GitHub Actions PostgreSQL 17 #39168767820 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39168767820), SHA testado `a3313e1de6b72a1284f37b481dcba294c8037a37`, job `117797244695`. Logs conferidos: **S1B-01..10 (10/10 PASS)** em 100 pendências fictícias e duas concessionárias; baseline no mesmo job: S1E 7/7, S1R 9/9 duas vezes, S1X 7/7 duas vezes, S1C 5/5, S1D 5/5, S1Q 10/10, S1QC 4/4. A hipótese de bloqueio das primeiras 30 pendências foi mitigada: 10 posteriores recuperáveis foram processadas. Vendas mantidas como terminais e nenhuma atribuição a operador inválido.

A execução inicial [#39168641246](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39168641246) falhou somente na expectativa do teste sobre **número de inspeções**: uma mesma pendência sem destinatário pode ser inspecionada mais de uma vez em lotes distintos, sem duplicar casos ou histórico. O teste foi corrigido para distinguir total de tentativas de inspeção de casos exclusivos, e toda a suíte passou em #39168767820.

**Limites persistentes:** rotinas de ativação/concessão ainda processam até 25 registros por evento; o saldo maior requer **chamada interna explícita à função de drenagem**, não há scheduler nem automação contínua implantada. Não é prova de serviço REST/GoTrue hospedado, regra de escala/plantão, performance com dados reais ou autorização RH. Sem merge/deploy/progresso global.


## Resultado após revisão: problema corrigido e testes verificados

**[PG17 #39192614838 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39192614838)**, SHA `74d03faee0c4a0bc04877c9be8cbb7b83b73da61`, job `117868497833`: logs conferidos, **AUD1-01..07 = 7/7 PASS** e regressões anteriores também executadas após aplicar 044 (S1R 9/9 terceira passagem; S1Q 10/10 segunda; S1B 10/10 segunda). **[PG17 #39192862292 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39192862292)**, SHA `38bc2223d49f0b556f0f859a8c8ee744ed37409b`, job `117869238276`: **AUD2-01..05 = 5/5 PASS**, usando a função real de *inbound sintético* S0 `receber_mensagem_sintetica` (sem Graph API) e depois suspensão/redistribuição S1-002. Testes de replay de mesma mensagem, mesmo caso, venda histórica preservada e retorno de cadastro enviado ao banco confirmados. A mensagem de rejeição `PROFISSIONAL_PRUMO_INELEGIVEL` no log é ensaio negativo esperado, **não falha de CI**.

**Veredito documental:** correção específica confirmada no PG17 descartável. Nenhum novo status comercial; nenhuma ramificação S0, WhatsApp/Meta, OpenAI ou Frontend foi editada; progresso geral não aumenta por teste local. Os *gates de produção* do texto acima continuam [R/V] — principalmente conclusão efetiva da conversa, gestor/escala e permissão GoTrue/REST.


## Incremento I8 — trilhas imutáveis e corridas com status [testes pendentes]

Migration `202610190045_s1_historicos_append_only.sql`, teste `s1_008_historicos_append_only.sql` (S1H-01..08) e duas sessões SQL `scripts/test_s1_002_status_race.sh` (S1SC-01..04). O objetivo é impedir edição/apagamento/truncamento acidental de três históricos S1 mesmo em operações privilegiadas comuns, sem bloquear inserções legítimas, e verificar sincronização com transição comercial S0 **simulada por SQL**. Não altera workflow Meta/OpenAI/FV. **Nenhum PASS antes do log do job.** [Documento I8](../docs/S1_002_I8_AUDITORIA_IMUTAVEL_E_RACE_2026_10_19.md).


## Resultado verificado do incremento I8 — 19/10/2026

[**GitHub Actions PostgreSQL 17 #39229666792 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39229666792), commit ensaiado `51025c6e578dc67031c23bf7233d9866da017440`, job `117984297521`: logs consultados e marcadores conferidos: **S1H-01..08 = 8/8 PASS**, **S1SC-01..04 = 4/4 PASS**; também passaram regressões S1E 7/7, S1R 9/9 em 3 passagens, S1X 7/7 em 2 passagens, S1C 5/5, S1D 5/5, S1Q 10/10 em 2 passagens, S1QC 4/4, S1B 10/10 em 2 passagens, AUD1 7/7 e AUD2 5/5. Ausência de erros SQL inesperados nos marcadores; corridas no script representam UPDATE comercial sintético e não API bancária real.

**Conclusão estrita:** proteção append-only aplicada e testada nas três trilhas S1, permitindo inserts legítimos; simultaneidade demonstrada somente nas duas ordenações construídas. **Não certifica isolamento contra superuser que desabilite triggers, tráfego distribuído, serviço GoTrue/REST de verdade, segredo de produção ou autorização de RH.** Status comercial do ciclo permanece S0. Sem merge, deploy, Supabase hospedado ou dados reais.

## S1-002/I9 — bloqueio administrativo local [P; pendente de CI]

Migração `046` e teste `s1_009_fronteira_administrativa_local.sql` com S1A-01..09. Nenhum gestor de concessionária, operador, `authenticated`, `anon` ou `service_role` tem autoridade de modificar `equipe_prumo_s1`. Mesmo diante de GRANT acidental/BYPASSRLS simulado, trigger de escrita exige executor local `postgres`; histórico RH não aceita INSERT do cliente. O papel de aprovador administrativo **não foi escolhido**, conforme contrato. Não confundir esse mock PostgreSQL com GoTrue, token JWT assinado ou REST. [Documento I9](../docs/S1_002_I9_FRONTEIRA_ADMINISTRATIVA_2026_10_19.md).


## Resultado executado I9 — PostgreSQL 17 descartável (19/10/2026)

[**CI #39230800805 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39230800805); commit ensaiado `4a83f82b71d2dd72e8640cfc0b4e8851e1690019`; job `117987994582`. Logs auditados: **S1A-01..09, 9/9 PASS**. Confirmados leitura RLS apenas do próprio estado, proibição de mutação de equipe por gestor/operador, metadados de teste sem elevação, acesso `service_role` recusado **mesmo quando recebe artificialmente GRANT e BYPASSRLS**, eventos RH inalterados e inserções legítimas pelo executor interno do banco. Regressões PG17: S1H 8/8, S1SC 4/4, S1E 7/7, S1R 9/9 em três passagens, S1X 7/7 em duas passagens, S1C 5/5, S1D 5/5, S1Q 10/10 em duas passagens, S1QC 4/4, S1B 10/10 em duas passagens, AUD1 7/7 e AUD2 5/5. A exceção esperada `PROFISSIONAL_PRUMO_INELEGIVEL` nos ensaios negativos não constitui falha do job.

**Limitação explícita:** esse teste é role/PostgreSQL local com `auth.uid()` simulado por `request.jwt.claim.sub`. Não houve JWT criptograficamente validado, login GoTrue, chamada PostgREST, revogação efetiva de sessão nem homologação da autoridade administrativa. O administrador definitivo de RH segue [R] para decisão humana futura; não foi assumido por gestor de concessionária. Nenhum dado real, merge ou implantação.
