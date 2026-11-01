# OFF-04 — Planejamento e continuidade F02, contrato candidato offline v0.1

**Data:** 31/10/2026 | **Frente:** OpenAI | **Status:** CANDIDATO OFFLINE / SEM AUTORIDADE PRODUTIVA

## Objeto

Novo módulo puro `e04_offline_lab/f02-plan-boundary.mjs`, com API:

- `prepareF02Plan(envelope)` valida entrada privada da fixture S0 e devolve handle emitido somente neste processo;
- `f02ProviderView(handle)` produz payload mínimo do simulador de fornecedor;
- `evaluateF02Model(handle,raw,{nowMs,scope})` valida retorno JSON estrito, provê IDs reais somente ao **consumidor interno S0** e reavalia versões/autorização simuladas;
- `reviewF02Continuity({scope,plan,events,prior})` classifica eventos de continuidade sintéticos sem gerar autorização de tentativa, despacho, C09 ou decisão comercial.

Versões candidatas: `prumo.openai.f02-plan-private/0.1-candidate`, `prumo.openai.f02-plan-provider/0.1-candidate`, `prumo.openai.f02-plan-response/0.1-candidate`. Todas as flags da fixture (`authenticated`, `authorized`, `tenantAllowed`, `verified`) são **alegações de dados fictícios do teste**. Um handle em WeakSet não autentica operador, sessão ou processo. Resultados de sucesso significam `S0_RECHECK_ONLY`, com `sendAuthorized=false`, `schedulingAuthorized=false`, `commercialTransitionAuthorized=false`.

## Fronteiras

O envelope privado recebe IDs de loja, pessoa, caso, cadeia, versão de política e consentimento, refs de sessão/recibo, solicitação S0 separada, elegibilidade de templates e versão de instrução. O payload fornecedor inclui **apenas** `providerTag` opaco, texto das instruções F02 e aliases de templates com versão, finalidade interna, janela e limite de tentativas. Não inclui `storeId`, `personId`, `caseId`, `requestId`, `sessionRef`, `authorizationRef`, `consentRef`, recibo, cadeia nem IDs originais dos templates.

O fornecedor não define consentimento, categoria Meta, slots, nomes do cliente, texto de template, IDs de canal, aprovação, política, fonte, status nem instante de envio. Sua resposta pode escolher apenas `attempts[]` e `finalTemplate` em formatos e janela determinados. Campos desconhecidos, JSON duplicado, aliases inválidos, versão não disponível e horários não crescentes são rejeitados.

`handoffDefinitive=true` exige `ownerRoute=human` e `priorAiPlanCancelled=true`. `post_human` exige rota humana. A janela Meta do último inbound, o instante de encerramento humano e o C09 após `sent` final são relógios **distintos**, não derivados do plano.

## Continuidade sintética

A entrada `plan` contém escopo, `requestId`, versão, `fingerprint` e tentativas fornecidas pela fixture S0; a trilha `events` exige `storeId/personId/caseId/chainRef`, evento, sequência, tipo e `verified` sintético. IDs duplicados com dados idênticos são deduplicados; colisões, sequência duplicada, eventos de outro escopo e status contraditórios são bloqueados. Um `prior` com a mesma chave/versão/fingerprint retorna `ALREADY_HANDLED_REVIEW_ONLY` sem permitir nova execução; divergências exigem revisão.

`API_ACCEPTED`, `QUEUED` e `UNKNOWN` significam `AWAITING_META_PROOF`; `SENT` **não libera** nova tentativa e retorna `ALREADY_SENT_EVIDENCE_ONLY` (nunca comprova envio físico). `META_131049` exige revisão do ecossistema. `OPT_OUT`, `CANCEL`, `TEMPLATE_REVOKED` e handoff de plano de IA impedem continuidade. O estado técnico final só pode ser decidido pela S0/Meta autoritativas; não há contador comercial `perdido` nem timer de 24h fictício.

## Reutilização da base S2 e diferenças

Este módulo **não substitui** `core.mjs:validateF02`, `plan-lifecycle.mjs:reconcileF02Plan`, `template-frequency.mjs:assessTemplateFrequency` e `transport-evidence.mjs:summarizeTransportEvidence`. Esses guardas existentes continuam úteis e devem ser executados no laboratório com a base S2 preservada quando a regressão completa for realizada. A OFF-04 acrescenta borda F02 com aliases/privacidade, JSON estrito, versão separada de consentimento e continuidade de requisições; não estabelece nova autoridade S0 nem adota regra de frequência universal.

**Limite de integração:** os campos de versões, assinatura da requisição, consentimento, identidade, retomada de binding entre sessões, catálogo real e prova Meta ainda exigem ratificação. A definição de eventos reais do Meta não deve ser substituída por esta enumeração local.

## Testes e evidências

`node --test docs/integracoes/openai/e04_offline_lab/tests/f02-plan-boundary.test.mjs`: 69/69 PASS neste ambiente Node 22.16.0. Não foi reproduzida a regressão completa S2+OFF-01 (342) nem OFF-02/03 (162 esperados), pois os pacotes locais continuam incrementais e não incluem a árvore oficial completa. NÃO declarar 573/573 executados. Nenhum SYN de E02 é homologado; A38 histórica permanece bloqueada.

## Dependências interfrentes (não duplicar)

- [#7 OpenAI→S0/S1](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7): solicitação autenticada, catálogo filtrado, autorização, versões e recuperação F02.
- [#10 Meta→S0/S1](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10): recheck no instante PRE_DISPATCH; **não** é autorização que venha da F02.
- [#9 OpenAI→Meta](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9): evidência outbound `sent`/falha e correspondência de tentativa.
- [#8 Meta→S0/S1](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8): cadastro de App/WABA/número e grants por loja.
- [#2 Meta→S0/S1](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2): ACK de ingresso; outro domínio.

Nenhuma Issue é aprovação. Sem cliente OpenAI real, credenciais, Graph, SQL, dados reais, merge, deploy, nem mudanças S0/Meta/Frontend.
