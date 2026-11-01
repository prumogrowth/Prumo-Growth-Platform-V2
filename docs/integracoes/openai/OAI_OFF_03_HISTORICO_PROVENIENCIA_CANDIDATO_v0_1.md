# OAI-OFF-03 — Histórico F03, proveniência e extração offline (candidato v0.1)

**Data:** 31/10/2026. **Escopo:** somente frente OpenAI, lógica pura Node ESM, fixtures fictícias. Base funcional: OFF-01/S2, OFF-02 local. **Não ratificado pela S0; não é autenticação, homologação de E02, execução do modelo, aplicação de ficha ou autorização de envio.**

## Interfaces novas

Em `e04_offline_lab/f03-history-boundary.mjs`:

1. `prepareF03History(privateRequest)` valida dados estruturados e retorna `{status:'READY', privateContext}`. O contexto é cópia imutável; sua emissão é protegida por identidade interna de módulo. A S0 **ainda deve autenticar**, montar e atestar os dados em uma implementação posterior.
2. `projectF03History(prepared)` produz a única visão elegível a um **fornecedor hipotético**: catálogo de códigos de campos, alias de origem, classe de autor, tipo e conteúdo minimizado previamente autorizado; não transporta IDs internos, números de telefone, versões, recibos ou grants. O texto livre não é automaticamente anônimo: só a S0 pode decidir que conteúdo real pode sair.
3. `reviewF03Extraction(prepared,untrustedProposal,{currentScope?,prior?})` rejeita schemas desconhecidos, aliases inválidos, fontes indisponíveis, campos incompatíveis, claims inexistentes e condições de concorrência. Somente retorna `PROPOSED/S0_RECHECK_ONLY` ou `REVIEW_REQUIRED/S0_HUMAN_REVIEW` e **nunca aplica** nada. `currentScope` e `prior` são *fixtures* sintéticas, não checagem física.
4. `auditF03History(outcome)` redige apenas operação/schema/status, sem valores ou identificadores.

## Estrutura lógica privada — `prumo.openai.f03-history-private/0.1-candidate`

- `requestId`: correlacionador **interno** da solicitação.
- `scope`: flags sintéticas `authenticated`, `authorized`, `tenantAllowed`, `humanClosed`, `closureAuthenticated`, `identityAttested`, `historyCompletenessAttested`; quatro IDs internos `storeId/personId/caseId/closureId`; `expectedVersions/currentVersions` com **sete domínios** independentes `case,cycle,form,catalog,assignment,identity,policy`.
- `privacy`: `modelContentAuthorized:true`, `dataMinimized:true` — valores dados pela fixture, jamais verificados contra LGPD por este código.
- `cutoff`: `{sequence,closedAt,eventId}`; a sequência é **global por pessoa/loja** na hipótese do contrato candidato. A S0 ainda deve provar e fixar fisicamente esse domínio de ordenação.
- `cases`: identidades de casos da **mesma pessoa e loja**, com `s0IdentityBound:true` simulado. O código não faz resolução por nome/telefone nem une identidades.
- `records`: IDs privados, caso/pessoa/loja, sequência, data ISO, classe `customer|human|ai`, tipo `text|media`, disponibilidade, permissão de conteúdo, texto ou transcrição já autorizada e claims *exclusivamente sintéticas*.
- `catalog`: lista tipada de campos `code,type:string|number|boolean,essential:boolean`.

Registro fora do cutoff pode estar no envelope privado, mas **jamais** entra na projeção. Mídia indisponível não possui conteúdo ou claims; apenas uma contagem agregada é projetada. Texto de mídia nunca é transcrito ou inventado pelo laboratório. Não há autorização automática de fotos, PDFs, transcrição ou gravação.

Claims candidatas têm `id,code,value,explicit`, podendo conter `corrects` e `s0CorrectionAttested:true`. Correção aponta a claim anterior do mesmo código, disponível e dentro do cutoff; forks e ligações inválidas são recusados. Uma correção com flag verdadeira **não prova** veracidade semântica, identidade ou certificação S0. Correções não ratificadas não são inferidas da proximidade temporal. Conflito entre valores explícitos terminais obriga revisão humana mesmo quando a resposta omite conflito.

## Saída do fornecedor — `prumo.openai.f03-history-proposal/0.1-candidate`

A resposta fictícia deve conter **somente**:

```json
{
  "schemaVersion":"prumo.openai.f03-history-proposal/0.1-candidate",
  "fields":[{"code":"name","value":"Example","sourceAliases":["src_001"]}],
  "missingFields":[],
  "conflicts":[],
  "commercialAdvisory":null,
  "followupAdvisory":"none"
}
```

`followupAdvisory` é `none|consider`, sem disparar F02. `commercialAdvisory` é nulo ou sugestão `perdido` com referências a claims explícitas de desistência, **sempre** enviada para revisão; `vendido`, Banco/remessa e status comercial nunca são retorno executável. Falta de campo essencial ou conflito exige revisão; falta só de opcional não bloqueia a proposta. A saída pode conter valores privados apenas na **resposta destinada à S0**, nunca em log público.

## Limites técnicos

Validação: schemas fechados em cada nível, acesso sem getters, limites de tamanho/profundidade, payload determinístico, aliases efêmeros, rejeição de JSON duplicado pelo parser OFF-02, binding de tenant/pessoa/caso, separação de versão, fim humano expresso, entrada temporizada e comparação de claims. Os selos internos são somente de procedência de objeto **dentro do processo**: não autenticam S0, não substituem recibo e não sobrevivem a sessões.

A lista de casos, completude do histórico, correções e claims provêm de *fixtures*. O código não prova autenticidade de origem, tratamento de mídia, veracidade de frases, direitos sobre conteúdo ou aplicação transacional. Mesmo `PROPOSED` precisa da ratificação e checagens atuais da S0. A38 histórico permanece `HISTORICAL_SOURCE_UNRECOVERED`; os 70 SYN continuam sem homologação integral. Nenhuma nova autoridade administrativa ou IA autônoma foi criada.

## Reprodução

Na pasta `docs/integracoes/openai/e04_offline_lab` em Node 22+:

```sh
node --test tests/f03-history-boundary.test.mjs
npm test
```

A suíte OFF-03 possui 95 testes nativos. Com os 61 OFF-02 presentes neste pacote, `npm test` executa 156 testes. O conjunto de 342 casos antigos não está todo neste diretório de teste local e **não foi reexecutado nesta missão**.
