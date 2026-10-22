# FV-UI-017 — Reparação da integridade de contexto e mensagens (primeiro bloco da Etapa 2)
**Data:** 22/10/2026. **Branch:** `feat/frontend-plataforma-visual`. **Natureza:** aplicação visual local com **dados sintéticos**, sem autenticação, S0/S1, Meta/WhatsApp, GoTrue ou persistência. Este incremento decorre da [auditoria FV-AUD-01](./40_FV_AUD_01_AUDITORIA_ESTATICA_IMPLEMENTACAO_2026_10_22.md).

## Escopo realizado e rastreabilidade
| Fonte vigente / achado | Mudança | Evidência |
|---|---|---|
| D-NOM-01 / FV-22-02 / FV-AUD-01 | Rótulos dos perfis e da gestão atualizados para **Consultor, Gestor e Diretor**, sem renomear `role='operador'`, status comerciais, APIs ou migrations. | `frontend/visual/index.html`, `app.mjs`, `team-monitoring.mjs`, `README.md` |
| FV-DOC-03 §5 / FV-22-08 / FV-AUD-02 | Envio fictício direto foi substituído por **composição → prévia com cargo e nome do ator da fixture → confirmação exclusivamente local**. Prévia contém `Cargo Nome:\nMensagem`; o usuário não digita cabeçalho. | `app.mjs`, `index.html`, `styles.css` |
| FV-DOC-03 §5 / FV-22-10 | Mensagem confirmada **apenas na simulação** recebe `deliveryState='local_demo_not_sent'`, mostra **NÃO ENVIADA** na bolha e evita representar ACK, envio, entrega ou leitura da Meta. Isso não é comprovação S0. | `app.mjs`, teste DOM e teste de indicador |
| FV-DOC-03 §5 / FV-22-11 | A mensagem de demonstração **não apaga a pendência de resposta humana**, pois ela não foi realmente enviada. O marcador de supervisão permanece passivo. | `app.mjs`, `conversation-attention.mjs`, `attention-integration.test.mjs` |
| FV-DOC-03 §§2/5 / FV-22-07/08 / FV-AUD-05 | Ao trocar **caso, Consultor/Gestor, concessionária, inbox e relação O5**, o rascunho e a prévia do contexto anterior são apagados; confirmações tardias são rejeitadas. Cancelamento da prévia preserva o rascunho no mesmo contexto. | `app.mjs`, `app.dom.test.mjs` |

**Regra de contexto:** o campo local não transporta texto entre atendimentos. A UI opta por **descartar o rascunho** (não armazenar por caso): escolha conservadora no protótipo, sem persistência. Não representa política de drafts produtivos.

**Limite de autoria:** a identidade usada na prévia é a **fixture demonstrativa**; o navegador não assina ou valida uma mensagem real. Somente uma projeção futura autenticada do S0 poderá afirmar o cabeçalho efetivamente enviado. Templates e mensagens IA não recebem prefixo livre. A bolha inserida no histórico sintético continua sendo uma demonstração.

**Status técnicos/comerciais:** nenhuma enumeração comercial, transição, autorização bancária, roteiro F01/F02/F03, comando C13, grant ou distribuição foi alterado.

## Testes e evidências desta rodada
- Foram atualizados/adicionados cenários em `tests/app.dom.test.mjs` (preview/cancelamento/aceite, cargo Consultor/Gestor, supervisor, troca de caso/ator/loja/reset, confirmação obsoleta, texto mutado), `tests/attention-integration.test.mjs` (não envio não conclui resposta), `tests/source-contract.test.mjs` (restrições estáticas) e `tests/browser.smoke.py` (smoke ampliado para Chromium). `tests/dom-fixture.mjs` ganhou IDs do novo diálogo.
- **Execução realizada:** em avaliador JavaScript V8 temporário, com fontes atualizadas lidas do GitHub e mock DOM do repositório, **42/42 testes de `app.dom`, 10/10 de `app.mobile.dom` e 7/7 de `attention-integration`**, total **59/59**. Além disso, 14 verificações diretas de cenários de prévia/isolamento/transporte passaram nesse mesmo V8. Essa execução usa um emulador local do `node:test`/`node:assert` e **NÃO** é execução nativa do Node, Playwright, navegador real ou CI; contagens não devem ser reutilizadas como homologação.
- O checkout privado **não está montado** no ambiente de execução; GitHub externo não pôde ser acessado pelo terminal. Portanto, **`node --test` e `python tests/browser.smoke.py` não foram executados nativamente**. As rotinas foram adicionadas para futura execução no checkout autorizado.
- A prova física/visual de responsividade, zoom, leitores de tela, API Meta, autorização S0 e status de envio reais permanece **pendente**. FV-UI-013 segue sem homologação; referência histórica 19F=69/100 não foi atualizada.

## Próximos blocos da Etapa 2 (não executados aqui)
1. **Permissões/distribuição:** fila sem titular **compartilhada por Gestores autorizados à concessionária**, grants excepcionais por caso, distinção de pausa aplicada/redistribuição pendente/caso retido, com testes novos. A atual projeção gerencial é histórica e não se confunde com a fila vigente.
2. **Conclusão/extração/ficha viva:** segunda conclusão após esclarecimento, eventos/cutoff/versionamento rastreáveis, ficha contínua cliente+loja e snapshots bancários separados. Dependem de contratos S0/S1/OpenAI.
3. **Testes de integração:** somente após contratos reais acordados e ambiente autorizado. Não implantar frontend sintético como portal produtivo.

**Veredito:** primeiro bloco de reparação **implementado e verificado de modo sintético em V8**, ainda **não homologado**. Frentes externas preservadas; sem merge, deploy, acesso a clientes reais ou alterações em Auth/RLS.
