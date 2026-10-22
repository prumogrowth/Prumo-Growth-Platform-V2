# FV-UI-020 — Estados técnicos, fronteiras de integração e matriz de aceitação
**Data:** 22/10/2026. **Branch:** `feat/frontend-plataforma-visual`. **Estado:** incremento sintético de Frontend, **NÃO HOMOLOGADO**. Referência normativa: [FV-DOC-03](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md), especialmente FV-22-03/04/05/08/10/11/15 e D-AL-04. Continua a [FV-UI-019](./43_FV_UI_019_CONCLUSOES_F03_FICHA_VIVA_2026_10_22.md).

## Implementação e correções
| Frente | Evidências | Limites |
|---|---|---|
| Estados do transporte | `frontend/visual/transport-state-view.mjs`, `app.mjs`, fixtures de mensagem e testes: distinguir **solicitado, API aceitou, incerto, enviado comprovado, entregue, lido e falha definitiva comprovada**, sem confundir ACK com envio. Selo de prova, caso, loja, versão e titular precisam ser consistentes na fixture. Gestor supervisor sem atribuição não vê detalhes individuais de recibos. | Nada é enviado/recebido por Meta ou S0. As provas são **apenas sintéticas** e não criam autoridade. Mensagem adicionada localmente continua **NÃO ENVIADA**. |
| Estados de erro da extração | Novo `operation-feedback.mjs`: pedido local, parcial, falhou, obsoleto, incerto, negado e indisponível. Cópias não exibem erro bruto, PII, causa interna ou falsa confirmação; indicam preservação do estado, consulta a projeção confiável e **nenhuma retentativa automática**. | Não há polling, retry, confirmação F03, aplicação cadastral ou transição comercial. Cenários alternados na tela são demonstração, não respostas de uma API. |
| Exclusão de C13 | `s0-command-result.mjs` não aceita mais C13 no conjunto **candidato de ações humanas visuais**, preservando contrato antigo apenas como registro histórico. Teste específico de negação adicionado. | Não altera comando, schema ou contrato S0/S1. O Consultor nunca edita a ficha na UI. |
| Contexto de profissional | `app.mjs` descarta `processing` local ao trocar de ator, para não projetar pedidos do profissional anterior como se fossem do seguinte. | Isolamento de fixture, não autenticação/RLS. |
| Aceitação verificável | `frontend/visual/tests/acceptance-matrix.json` relaciona os **16 critérios FV-22-01..16** aos arquivos de teste, com `prototype_only`, `partial` ou `external_blocked`; `acceptance-matrix.test.mjs` valida IDs/arquivos/declaração de não homologação. `run_acceptance.py` enumera agora **24 suítes .test.mjs**, rejeita suites não registradas e exige checkout correto e Chromium para `full_acceptance`. | Resultado de `node --test`/Chromium **não foi obtido** nesta sessão por falta de checkout Git autenticado no ambiente de execução. Matriz é rastreabilidade, não aprovação. |

## Verificações executadas nesta rodada
- **V8 + mock DOM com código consultado diretamente no GitHub:** `app.dom.test.mjs` **56/56 PASS** após reparo das cópias de solicitação e erro.
- **V8 com funções puras:** `transport-state-view.test.mjs` **9/9**, `operation-feedback.test.mjs` **5/5**, `s0-command-result.test.mjs` **8/8**, `s0-read-contract.test.mjs` **7/7**, total **29/29**.
- **Regressões adicionais da interface em V8 + mock DOM:** `app.mobile.dom.test.mjs` **10/10 PASS** e `attention-integration.test.mjs` **7/7 PASS**. Total das verificações V8 mencionadas: **134/134** (56 DOM + 29 módulos de erro/contrato + 32 testes estáticos + 17 mobile/atenção); não é execução nativa Node/Chromium.
- **Testes estáticos de fonte no V8:** `source-contract.test.mjs` **32/32**; corrigida duplicidade de declaração `transport` encontrada durante a rodada.
- **Validação do inventário e matriz de aceitação:** **16/16 IDs** na ordem certa, referências a testes existentes e **24/24** arquivos .test.mjs registrados no runner; distribuição: **13 protótipos**, **2 parciais** e **1 dependência externa**. Esses valores são **categorias de cobertura**, não porcentagens de conclusão.
- **Não executado aqui:** Node nativo, Playwright/Chromium, testes de teclado/leitor de tela em navegador real, servidor HTTP da aplicação, Supabase/GoTrue/RLS, Meta, F01/F02/F03, S0/S1, banco, MCP e produção.

## Gates futuros (não resolver unilateralmente)
1. **S0/S1:** contratos ratificados de autenticação, escopo D2/D3/D4 e concessão por caso, versões, envelopes de leitura minimizada, idempotência, rejeições, erro/timeout incerto, leitura autoritativa após conflito e resultado persistido.
2. **Meta:** correlação entre aceite, envio provado, entrega, leitura e falha definitiva; autoria/autenticação real e indicador de atenção pertencem às projeções confiáveis do núcleo.
3. **OpenAI F03:** processamento só após conclusão humana expressa confirmada, cutoff e histórico da mesma concessionária, evolução da ficha/versão e falha técnica sem editor C13.
4. **Qualidade:** executar `python3 frontend/visual/tests/run_acceptance.py --expected-head SHA_COMPLETO` no checkout autorizado, com Chromium acessível. Não usar `--skip-browser` como homologação. Realizar revisão de responsividade/zoom/acessibilidade e depois testes integrados conforme contratos.

**Sem deploy, merge, banco, dados reais ou alteração de branch/código/documentos de outras frentes.** Referência 19F=69/100 e ausência de homologação FV-UI-013 permanecem; não foi criada nova porcentagem de avanço.
