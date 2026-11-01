# OFF-16 — Preparação da API OpenAI com teste sintético Responses (sem chave)

**Data:** 01/11/2026. **Estado:** candidato para validação OFFLINE. **Origem:** usuário informou poder disponibilizar API OpenAI quando útil; **isso não constitui autorização para emitir chamadas pagas, criar secrets no GitHub ou enviar dados reais.**

## Decisão técnica

**A chave da OpenAI ainda NÃO é necessária** para executar os testes de fronteira e segurança atuais. É útil numa etapa posterior, com uma avaliação controlada da **qualidade e formato reais do modelo**, mas não resolve os contratos operacionais pendentes da S0 e Meta. Não pedir chave pelo chat nem colocar credenciais em Issues, commits, ZIPs ou logs.

A documentação pública da OpenAI registra **Responses API** como interface para novas integrações (Assistants API descontinuada em 26/08/2026): https://platform.openai.com/docs/api-reference/responses e https://platform.openai.com/docs/guides/migrate-to-responses . Esta suíte modela apenas uma **projeção mínima sintética** do objeto de resposta; não garante conformidade automática com todo SDK ou modelo vigente.

## Implementação sem rede

- Módulo `e04_offline_lab/responses-shape-preflight-lab.mjs`: `inspectResponsesShape`, sem `fetch`, SDK, chave, carregamento de arquivo, relógio ou cobrança. Entrada `prumo.openai.responses-preflight/0.1-lab` com `F01/F02/F03`, correlação `providerTag`, modelo esperado, timestamps injetados e `response` **normalizado artificialmente pelo teste**.
- Suíte `e04_offline_lab/tests/responses-shape-preflight-lab.test.mjs`: 42 casos (3 positivos sem autoridade e 39 negativos) para atrasos, estados queued/incomplete/failed, erro/refusal, uso de ferramenta inesperado, mensagens múltiplas, esquemas trocados, JSON duplicado/inválido, payload adversarial, getters e ciclos.
- O único retorno positivo é `UNTRUSTED_JSON_CANDIDATE` com `candidateRaw` **não confiável**. A validação de estrutura de cada F01/F02/F03 e autorização S0 permanece obrigatória. `candidateRaw` nunca deve ser logado nem enviado a clientes.
- Todo resultado inclui `providerAuthenticated=false`, `sourceS0Authenticated=false`, `modelInvocationAuthorized=false`, `modelOutputTrusted=false`, `responseSemanticsValidated=false`, `modelContentAuthorized=false`, `publishAuthorized=false`, `schedulingAuthorized=false`, `sendAuthorized=false`, `fieldApplicationAuthorized=false`, `productionAuthorized=false`, `costApproved=false`, `liveApiCalled=false`, `requiresS0Recheck=true`.

**Não há adaptador HTTP real, interpretação semântica do modelo, processamento de tool calls, token accounting, retry idempotente, produção, stream, áudio ou autorização.** Não converter saída sintética em ação comercial.

## Quando pedir o uso controlado da API

Somente depois de definir uma missão de prova isolada com:
1. Autorização explícita para **efetuar chamadas reais pagas**, modelo escolhido, orçamento máximo e duração/volume limites;
2. Entrada 100% sintética, gabarito para F01/F02/F03, taxas de recusa/JSON inválido, latência, limite de tokens e critério de aprovação;
3. Chave com privilégios mínimos e orçamento/projeto separado, guardada no **secrets manager** autorizado (ou GitHub Actions secrets em ambiente protegido com aprovação), nunca na conversa, documentação ou código;
4. Worker/host confiável que projeta o conteúdo minimizado e mantém o recheck S0 separado; limites de retry, rate limiting, logging seguro e não persistência/retention por padrão;
5. Registro de evidências redigidas (sem prompt ou resposta sensível), com run e custos medidos; **não** publicar ou enviar a clientes mesmo se os canários passarem.

Se não existir orçamento/autorização, todos os testes OFF-16 continuam passando sem API e a função não tem capacidade de gerar tráfego.

## Marco de progresso

**Etapa 12A (testes independentes):** lote OFF-16 é preparação adicional, não conclui 12B/12C. **Etapa 08B/08C (contratos interfrentes):** continua pendente, e não é acelerada por API key. As etapas 09–11 de integração operacional também continuam pendentes de S0.

Base OFF-15: [commit `ff871525b9817246dafce243af6f67afd756f4d8`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/commit/ff871525b9817246dafce243af6f67afd756f4d8), [CI 908/908](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41309842839). **Meta OFF-16:** 950/950 = 908 herdados + 42 novos, confirmados apenas quando CI concluir no mesmo commit.

**Nenhum merge, deploy, chamada real à OpenAI/Meta/Banco, dado de cliente ou acesso a segredo.**
