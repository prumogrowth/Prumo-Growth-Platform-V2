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
