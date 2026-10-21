> **LEITURA ATUALIZADA — 21/10/2026:** A prévia sintética de carteira pausa mantém sua validade **somente para casos existentes e mesma equipe**, mas não representa a distribuição de novos leads entre equipes nem a fila gerencial compartilhada aprovada depois. Nenhuma regra real da S1 foi validada por esta prévia. Para decisões vigentes de pausa, distribuição, filas, acesso por caso, comprovação humana e IA, consultar **[FV-DOC-01](./35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md)**; divergências descritas em **[FV-DOC-02](./36_FV_DOC_02_AUDITORIA_AMBIGUIDADES_E_PRECEDENCIA_2026_10_21.md)**. Trechos abaixo permanecem como histórico técnico da sua data, sem substituir decisões posteriores.

# FV-UI-016 — Marco funcional fechado: prévia seletiva da carteira G2
**Data:** 20/10/2026. **Situação:** demonstração funcional sintética, não homologação. **Branch:** `feat/frontend-plataforma-visual`. Nenhuma operação real, nenhuma alteração na S1 e nenhum deploy.

## Objetivo delimitado
Fechar um incremento que permita ao gestor da Prumo **consultar** o destino proposto dos casos de um operador antes da pausa, sem redistribuir, suspender contas ou elevar permissões. O trabalho não antecipa a auditoria geral do projeto nem a limpeza integral da documentação: ambas devem ocorrer em encontros de alinhamento posteriores, por etapas, após uma interrupção técnica controlada.

## Decisões do responsável respeitadas
- Pausa por botão e confirmação, sem razão/data obrigatória; **pausa de entrada não suspende conta** e vale a todas as lojas autorizadas.
- Somente casos **sem contato humano comprovado** podem ser candidatos à redistribuição automática; só para **a mesma equipe**, com grants válidos para a loja e destinatário recebendo novos leads.
- Se ninguém cumprir essas condições, o caso **permanece com o operador pausado**. Caso iniciado permanece até eventual decisão individual do gestor.
- Caso histórico, vendido ou em ciclo bancário protegido não pode ser movimentado automaticamente pela prévia; ausência/invalidade de prova de início de contato resulta em **manter sem transferir**.
- Transferência manual excepcional para membro da equipe sem grant geral permanece pendência de autorização **restrita a um caso** da S0/S1, não uma permissão concedida por UI.
- A lista operacional continua com **um só badge**, numerado para não lidas e sem número/aparência distinta para lidas sem resposta; sem cronômetros/SLA em destaque. Nenhuma mudança estética definitiva nesta entrega.

## Implementação limitada à demonstração
- `frontend/visual/team-pause-preview.mjs`: contrato puro `projectManagerPausePreview` para ordenar resultados previstos da carteira ativa **visível na fixture** do gestor. Exige evidências sintéticas e versionadas por caso/loja/titular, nunca deduz contato humano a partir de mensagens. Classificações: `retain_started`, `retain_no_recipient`, `retain_unverified`, `retain_protected`, `proposed_same_team`.
- `frontend/visual/app.mjs`: cartão G2 apresenta **seção `details` inicialmente recolhida** intitulada 'Prévia da carteira durante pausa', com contagens e registros técnicos minimizados (referência do caso, loja, condição), sem mensagens/cliente, sem indicador de tempo.
- `frontend/visual/styles.css`: aparência neutra somente para legibilidade.
- `frontend/visual/tests/team-pause-preview.test.mjs`: 9 testes de isolamento entre equipes, preservação de casos iniciados/históricos, destinatário elegível, ausência de elegibilidade e sem mutações.
- `frontend/visual/tests/browser.smoke.py`, `source-module-graph.test.mjs` e `source-contract.test.mjs`: novo módulo incluído no bundle de ensaio e cobertura de prévia na jornada G2.

**Atenção:** caso sem substituto NÃO vira automaticamente 'fila sem titular'. Continua atribuído. Não há seleção definitiva de algoritmo de distribuição, autenticação real nem contrato S1 aprovado para a transação.

## Evidências efetivamente obtidas
- **Node.js local nativo**: `node --test tests/team-pause-preview.test.mjs` executado e **9/9 PASS**, sem falha, sobre código novo cujos **hashes de blobs Git foram comparados** com a branch. `fixtures.mjs` extraído do ZIP autenticado corresponde à SHA da branch (sem alteração na fixture). O comportamento relevante de `copyCFDemoFixtures` foi exercitado localmente.
- **Integração em V8 com DOM sintético**: fontes reais consultadas na branch, concatenadas na mesma ordem do roteiro Chromium, **compilação sem colisão**; foram comprovados dois painéis de prévia gerencial, presença de classificação de falta de substituto, ausência de nome de clientes na prévia e isolamento de equipe.
- O roteiro Playwright foi **atualizado para executar em Chromium no checkout**, mas um **novo Chromium nativo integral da branch não foi executado nesta rodada**; não declarar aprovação desse teste nem do aceite formal sem log. O teste nativo completo da suíte anterior não foi repetido aqui.

## Questões reservadas para o momento de alinhamento (não decidir por inferência)
1. Como comprovar o primeiro contato humano por canais futuros diferentes de mensagem, sem classificar leitura/abertura ou conversa só da IA como contato humano?
2. Política e expiração de autorização **específica por caso** para transferência manual sem concessão geral, incluindo anexos D3/D4 e revogação.
3. Comportamento operacional dos casos que permanecem com operador pausado por muito tempo, **sem colocar cronômetros/SLA na lista** e sem esvaziar sua carteira automaticamente.
4. Critérios de aceite do S0/S1, evidências de transação concorrente e dos testes RLS/GoTrue antes da ligação real do frontend.

## Encerramento e próxima cadência acordada
**Marco FV-UI-016 fechado como incremento sintético de consulta.** O próximo momento recomendado é **alinhamento de dúvidas com o responsável**, isoladamente. Em encontros seguintes, **auditoria geral** (regras, segurança, cobertura e divergências), e depois **higiene de documentação** (fontes vigentes, precedência, arquivos históricos, referências e índice canônico). **Não executar as três revisões em uma única etapa**, nem tratá-las como já realizadas.

**Gates preservados:** S1 é mantida sob outra frente, branch intocada por este incremento. S0 permaneceu sem alterações nesta rodada. Sem Supabase remoto, Meta, Banco, merge ou deploy. FV-UI-013 não homologada no gate Git. 19F permanece 69/100.
