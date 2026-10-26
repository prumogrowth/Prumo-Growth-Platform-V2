# FV-UI-059 — Auditoria de fechamento do protótipo visual, critérios FV-22 e próximos marcos

**Data:** 26/10/2026 · **Frente:** frontend visual da plataforma Prumo, ainda **sem nome comercial aprovado**. LiberaCred é o produto da instituição financeira, não o nome da plataforma.

**Branch de escrita:** `feat/frontend-plataforma-visual` — **sem alteração de S0, S1, `main`, deploy, PR ou integração produtiva**.

## 1. Decisões aplicáveis e forma de medir

- **Fontes prioritárias:** `frontend/docs/00_COMECE_POR_AQUI_DECISOES_VIGENTES_2026_10_21.md`, `38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md` (FV-22-01..16), `11_CRITERIO_APRESENTACAO_E_HOMOLOGACAO_VISUAL_v0_1.md` e `40_FV_AUD_01_AUDITORIA_ESTATICA_IMPLEMENTACAO_2026_10_22.md` (diagnóstico anterior).
- **Evidência recente:** [GitHub Actions 40294929672](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40294929672), SHA técnico `e2bfc9c297b9163bea7d3f3e60510c08759029e8`, `completed/success`, preflight **59 arquivos**, Python **25/25**, Node **372/372** e Playwright/Chromium **PASS**, inclusive FV-UI-058 8 cenários. Certificação documentada no commit `2e5437ead0732c2341ae9933a73ccec69b8a8e9a`.
- **Limite da evidência:** esses testes atestam funcionalidades **sintéticas locais** e compatibilidade da interface. Não significam prova de autenticação, isolamentos de dados reais, persistência, Meta, OpenAI, banco, leitor de tela humano, desempenho em dispositivos reais ou aceite do responsável.
- **Interpretação das colunas:** `Representação sintética` significa que há código, testes e/ou demonstração local do comportamento; `condicionada` significa que o comportamento verdadeiro depende de contrato/implementação S0/S1/Meta/OpenAI/Banco. Esta matriz não marca aceites de produção.

## 2. Matriz do contrato vigente de 16 critérios

| FV-22 | Critério resumido | Situação na branch visual / evidência observável | Aceite operacional |
| --- | --- | --- | --- |
| 01 | Plataforma sem marca LiberaCred | Representada no HTML e documentação; não promove LiberaCred a nome da plataforma. | Não se aplica ao protótipo; marca futura exige decisão. |
| 02 | Papéis Diretor, Gestor, Consultor | Rótulos visíveis corrigidos em FV-UI-017; testes DOM e `source-contract.test.mjs`; identificadores técnicos legados mantidos. | Roles/grants reais dependem de S0. |
| 03 | Ficha O3 somente leitura | `registration-view.mjs`, testes de acesso D3 e navegação; sem editor C13 ao Consultor. | Dados, versões e grants reais vêm de S0. |
| 04 | Conclusão humana não muda status sozinha | Diálogo e eventos sintéticos com confirmação; `app.dom.test.mjs` e `human-cycle-view.test.mjs`. | Comando real, idempotência e autorização por S0/S1. |
| 05 | Duas conclusões, cutoffs/versionamento | `human-cycle-view.test.mjs` contém testes FV-22-05 e demonstra recortes distintos sem mutar corte antigo. | Cutoffs, versões e extração F03 reais requerem S0/OpenAI. |
| 06 | Esclarecimento de lacuna pós-F03 | FV-UI-019 e testes FV-22-06 apresentam cenário fictício de esclarecimento sem edição nem reabertura verdadeira. | Handoff e conclusão nova dependem de S0/S1. |
| 07 | Ficha viva loja/cliente + snapshots | Cenários `human-cycle-view` FV-22-07 cobrem versões e snapshot bancário preservado; isolamento simulado. | Identidade e armazenamento autorizado por loja dependem de S0. |
| 08 | Assinatura/prévia da mensagem humana | FV-UI-017 e smoke Chromium validam `Consultor Nome:` em prévia, rascunho e não-envio. | Autoria autenticada, assinatura final e retry pelo serviço/Meta. |
| 09 | Janela Meta ≠ conclusão humana | `cf-op-02.mjs` e `app.dom.test.mjs` representam bloqueio de texto livre e template separado. | Relógio/provas/política de janela reais vêm de Meta/S0. |
| 10 | ACK/UNCERTAIN ≠ SENT | `conversation-attention.mjs`/`transport-state-view.mjs`, FV-UI-020, testes DOM e browser. | Confirmação de transporte e auditoria reais dependem de serviço. |
| 11 | Indicador COUNT/DOT/NONE; supervisor ≠ leitura | Testes da FV-UI-014/020 e contrato de atenção distinguem responsabilidades no cenário local. | Sem aceite de herança de leitura na transferência; S0/S1 pendentes. |
| 12 | Pausa efetiva ≠ redistribuição pendente | `team-operations.mjs`, `team-pause-preview.mjs`, `app.dom.test.mjs` e FV-UI-016 representam solicitações sem aplicação local. | Efeitos, provas/versionamento e fila real pendentes S0/S1; verificar UX da sequência completa. |
| 13 | Fila sem titular compartilhada e assunção única | FV-UI-018 e testes DOM representam fila, intenção de claim e escopo por loja sem mutação. | Concorrência e assunção atômicas apenas S0/S1. |
| 14 | IA de melhoria fora da V1; F01 sem quadro de pessoas | Não há interface ativa para IA de melhoria; demo não alimenta F01 com listas de consultores. | Validar integração F01 separadamente com frente de IA. |
| 15 | F03/status somente após S0; banco prova real | `bank-view.mjs`, `modelExtraction`, `app.dom.test.mjs` não fazem venda/remessa automática. | Catálogo de transições e prova de venda/remessa são de S0/Banco. |
| 16 | Não criar admin de campanha/MCP por inferência | Navegação sintética não oferece editor administrativo produtivo inventado. | Eventual UI administrativa requer escopo/contrato próprios. |

**Conclusão verificável:** existe representação sintética ampla dos 16 temas no acervo atual. Isto **não** é o mesmo que 16 critérios homologados; FV-22-11 e FV-22-12 têm fronteiras contratuais/UX que devem ser revisitadas na auditoria final. Matriz é análise documental/estática apoiada nos testes já aprovados, não nova suíte de aceite FV-22 completa.

## 3. Estado de fechamento da frente — sem porcentagem artificial

| Marco de saída | Estado verificado | Próxima ação responsável |
| --- | --- | --- |
| Jornada visual O1–O5 / G2–G4 sintética | **Implementação extensa e testes automatizados aprovados**; não há inventário de experiência assinado. | Frontend: auditoria E2E cruzando matriz FV-22, estados vazios, erros, escopo e casos extremos. |
| Gate automatizado da última versão | **PASS** (59 arquivos, Python 25, Node 372, Chromium real). | Frontend: manter o gate verde a cada correção, sem reexecutar artificialmente trabalho homologado. |
| Acessibilidade e UX final | **Parcialmente cobertas** por Chromium em larguras/temas e testes DOM. Sem teste humano assistivo, avaliação estética consolidada ou aceite do responsável. | Frontend: uma auditoria de navegação integral desktop/mobile, contraste, foco e usabilidade; preparar apresentação única. |
| Conciliação funcional com contratos S0/S1 | **Candidata**, contratos/versões finais ainda sem aceite interfrentes. | Codex/S0 coordena integração; Frontend entrega dependências e implementa apenas proposta isolada. |
| Sistema de produção (Auth, grants, banco de dados, transporte WhatsApp, IA, banco) | **Fora do escopo homologado da FV**; nenhuma demonstração de serviço produtivo deve ser interpretada como integração. | S0/S1/Meta/IA/Banco, testes de segurança, privacidade e autorização específicos. |
| Publicação/merge | **Não autorizado e não executado**. | Somente após coordenação e aprovação explícita. |

## 4. Lista priorizada de encerramento, não uma sequência infinita de pequenos retoques

1. **Marco FVA — Regressão integral de jornadas e 16 critérios:** montar um checklist executável por critério e simular cenários cruzados O1–O5/G2–G4: ator, loja, equipe, autorização sintética, janela Meta, falha F03, pausa, histórico, banco, escopo D2/D3/D4, estados vazios. Não inventar endpoints. Priorizar defeitos de alta gravidade em vez de microajustes cosméticos.
2. **Marco FVB — Revisão visual consolidada:** coletar evidências de todas as principais telas em desktop/mobile e dois temas, verificar percepção de navegação, touch/teclado/contraste e acessibilidade básica; fazer correções identificadas, não abrir incrementos infinitos sem critério.
3. **Marco FVC — Pacote de entrega ao usuário/Codex:** índice atualizado de jornadas, matriz FV-22 com evidências e ressalvas, vídeo/capturas ou instruções de prévia, contratos candidatos S0/S1, pendências/responsáveis e gate aprovado. Apresentar para **uma revisão UX/estética consolidada** conforme FV-GATE-01; integrar apenas após coordenação.
4. **Dependência externa após FVC:** integrar com S0/S1 e demais provedores, executar testes de autorização/dados reais e aceite produtivo. Essa etapa **não** pode ser considerada concluída apenas porque o frontend sintético está pronto.

### Estimativa condicional

A interface sintética está **muito mais perto de um pacote de revisão visual do que de um lançamento operacional**. Se a auditoria FVA não revelar novos problemas graves, há **três marcos principais** de fechamento da frente demonstrativa (FVA, FVB, FVC), mas não é possível converter isso em número fixo de execuções ou porcentagem sem passar por FVA. Integração produtiva é um projeto dependente de outras frentes e não está coberto por esta estimativa.

## 5. Governança de branches

- Codex é o principal responsável pelo **S0**. Qualquer mudança necessária no núcleo será proposta e testada em isolamento, com contratos, arquivos e dependências, **sem incorporação no núcleo oficial** até coordenação.
- Commits, branches e PRs existentes das demais frentes **continuam válidos**. Não reconstruir funcionalidades já demonstradas nem promover o protótipo a produção.
- Próximo passo recomendado nesta branch: **FVA — auditoria cruzada de jornadas FV-22**, corrigindo lacunas concretas e verificáveis. FV-UI-059 é documento de planejamento/triagem, **não** nova certificação de código.
