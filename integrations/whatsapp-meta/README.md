# WA-01A — Adaptador Meta inbound isolado (candidato)

**Situação:** engenharia sintética, não implantado; contrato técnico proposto. Não altera a POC
`whatsapp-webhook-sandbox`, as migrations S0, o projeto Supabase hospedado ou canais comerciais.

`inbound.ts` fornece apenas `inspectMetaWebhook(rawBody, signatureHeader, trustedAppSecret, options)`.
Recebe bytes brutos e um segredo selecionado por configuração confiável; aplica limite de tamanho;
verifica a assinatura `X-Hub-Signature-256` via WebCrypto HMAC-SHA256 **antes** de fazer parse;
percorre todos os `entry[]`, `changes[]`, `messages[]` e `statuses[]` e extrai eventos técnicos.

O resultado é `{ok:true, events}` ou `{ok:false, failure:{code, position?}}`. Um erro de
qualquer item invalida o lote inteiro (sem sucesso parcial). `position` contém índices, nunca
conteúdo ou telefone. Os eventos preservam o identificador de participante recebido, mas **não**
resolvem identidade comercial, não associam tenant/loja/canal, não escolhem destino para envio e
não deduplicam status. O `statuses[].id` é ID de mensagem enviada, não ID único de callback.

**Não há endpoint GET/POST, HTTP 200, ACK, conexão à Graph API, banco, outbox, worker, fila,
credenciais reais, tokens em código ou deploy.** Um resultado `ok:true` só significa assinatura
válida e forma conhecida; não significa ingresso durável. O futuro webhook só poderá ACK 200
após aceite durável de **todos** os eventos relevantes pela interface aprovada do núcleo S0.

## Testes locais sem dependências ou serviços externos

Node.js >= 22: `node --experimental-strip-types --test integrations/whatsapp-meta/inbound.test.ts`

Testes sintéticos: assinatura válida/alterada/ausente/app errado, POST agregado, múltiplos `entry`,
callbacks repetidos, lote parcialmente inválido, campo não contratado, payload inválido, limite
por tamanho/eventos e ausência de dados sensíveis nos erros. A execução é local; não habilitamos
GitHub Actions para evitar custo não aprovado.

## Integração pendente da frente principal

- Revisar o envelope e regras de quarentena/rejeição para eventos Meta não contratados.
- Fornecer mapeamento autenticado Meta app/WABA/phone_number_id → canal/loja vigente.
- Homologar API interna de persistência transacional (inbox + trabalho durável), dedupe e ACK.
- Definir limites e retenção via DEC-WA-06 e ambiente definitivo via DEC-WA-04.
- Resolver identidade 8↔9, autorizações e estados comerciais exclusivamente no núcleo.

Referência: `docs/integracoes/whatsapp-meta/interface-compartilhada-s0-meta-v0_1.md`.

## WA-01B/C/D + WA-02A — módulos adicionais sintéticos

- `durable-receipt.ts`: guarda de ACK de lote **não operacional**; não considera a migration 029/030 prova de commit Meta.
- `technical-keys.ts`: pistas de correlação para IDs de mensagem/status, **não autoritativas** para dedupe.
- `verify-get.ts`: decisão isolada de GET `hub.challenge` por token confiável de App, sem endpoint.
- `graph-outbound.ts`: construtor **inerte** de payload de texto C03/C12 da Graph API e classificador de aceite, recusa e incerteza; **sem fetch, token ou envio**. C06 requer construtor específico de template.

Rodar apenas WA-02A: `node --experimental-strip-types --test integrations/whatsapp-meta/graph-outbound.test.ts`.

**IMPORTANTE:** nem strings de intento marcadas `authorized` nem o request preparado concedem permissão comercial real. A frente principal deverá revalidar autorização imediatamente antes de qualquer envio, persistir tentativa, limitar credenciais por concessionária, reconciliar timeout e tratar callbacks. Não logar `request.body` que contém destinatário e conteúdo. Referência: `docs/integracoes/whatsapp-meta/wa02a-graph-outbound-texto-v0_1.md`.

## WA-02B — template WhatsApp C06, offline

`graph-template.ts` prepara somente templates textuais **posicionais** (body e header de texto opcional), com correspondência estrita entre intenção C06 e manifesto confiável de template/idioma/revisão/status, sem mídia/botões/Graph/token/HTTP. Não concede elegibilidade nem envia; `trustedSnapshot` deve ser fornecido e revalidado pelo núcleo. Não registrar em logs o destinatário nem as variáveis de texto.

Testes locais: `node --experimental-strip-types --test integrations/whatsapp-meta/graph-template.test.ts` (**WA-TPL-01..18 PASS**). Compilação TypeScript estrita do módulo **PASS**; o teste foi executado mas não typechecked por ausência local de `@types/node`. Referência: `docs/integracoes/whatsapp-meta/wa02b-graph-templates-c06-v0_1.md`.


## Reparos auditados WA-02A/B — 18/10/2026

Os construtores Graph continuam **inertes** e não concedem direito de envio. Após a auditoria, `graph-outbound.ts` trata 408/425 como `UNCERTAIN_EXTERNAL` sem retry cego e admite IDs `wamid` opacos com padding `=`, rejeitando controles. `graph-template.ts` agora exige contexto autenticado fornecido de fora e catálogo de componentes completo, rejeitando cross-tenant e formatos não suportados.

**Assinatura atual [P]:** `prepareGraphTemplateRequest(intent, trustedSnapshot, trustedScope, apiVersion)` — quatro argumentos. Os três objetos coincidentes não comprovam autorização; `trustedScope` e `trustedSnapshot` devem vir de backend interno confiável, que revalida C06 no instante do envio.

Executados localmente: **41/41 testes PASS** para `graph-outbound.test.ts` + `graph-template.test.ts` e TypeScript estrito PASS dos dois módulos. Os arquivos de teste não passaram typecheck completo por ausência de tipos Node; sem CI remoto. Relatório: `docs/integracoes/whatsapp-meta/wa02-reparos-pos-auditoria-2026-10-18.md`.


## WA-02C — Despacho S0 → Meta inteiramente simulado

`offline-dispatch.ts` conecta **somente em memória** o classificador WA-02A e o construtor de template WA-02B a `FakeS0Outbox` e `ScriptedFakeGraph`. Verifica escopo e versão atuais da fixture antes de reservar uma única tentativa. Revogação, divergência entre concessionárias, destinatário alterado, template suspenso e erro de preparação bloqueiam sem chamada fake; timeout e falha de registro permanecem incertos, sempre `retry_automatically=false`.

Este módulo **não é um serviço backend**, não possui `fetch`, Graph API, HTTP, segredo, banco ou autorização comercial. A ficha `allowed_now` é exclusivamente fictícia, não comprova elegibilidade e não pode ser usada como porta de produção.

**Testes reexecutados localmente:** 23 SIM novos + 17 WA-OUT + 24 WA-TPL = **64/64 PASS**, TypeScript estrito dos três módulos PASS. Sem CI GitHub e sem typecheck completo de `*.test.ts`. Documento: `docs/integracoes/whatsapp-meta/wa02c-simulacao-despacho-s0-meta-v0_1.md`.


## WA-02D — conciliação de callbacks técnicos Meta (somente fixture)

`technical-reconciliation.ts` oferece `FakeMetaStatusReconciler` **somente em memória**. Correlaciona um `wamid` previamente aceito pela Graph API com callbacks `sent/delivered/read/failed` por **App confiável + WABA + Phone Number ID + destinatário exato**; eventos fora de ordem não diminuem progresso técnico, e callbacks repetidos são preservados, sem dedupe automático por `statuses[].id`. Callback antes de envio registrado fica pendente, com limites sintéticos explícitos, sem HTTP 200 ou efeito comercial.

O nome do método `observeAuthenticatedFixture` pressupõe HMAC comprovado e aceite durável **fora** desse módulo; não valida assinatura, não cria inbox nem autoriza C07/Graph. Destino BR 8↔9 não é inferido. O log dos resultados não contém telefones/tokens/texto.

Testes: **24/24 REC PASS** e **88/88 PASS** com regressões WA-02A/B/C locais; TypeScript estrito do módulo PASS. Documentação: `docs/integracoes/whatsapp-meta/wa02d-conciliacao-status-meta-sintetica-v0_1.md`. PR Draft, sem deploy nem chamadas de rede.


## WA-03A — Auditoria integrada e correção de isolamento técnico

Foram acrescentados `cross-contract.test.ts` (14 testes entre HMAC/parser → guarda hipotética de ACK → fake Graph → fake callbacks) e `scope-isolation.test.ts` (3 regressões adversariais). Um defeito do **laboratório** foi corrigido em `technical-reconciliation.ts`: agora consultas a projeções e pedidos `ALREADY_LINKED` precisam manter **concessionária e canal originais**, além de App/WABA/Phone/recipient. Antes da correção, os três testes de isolamento falhavam; depois, **105/105 testes PASS** com as 88 regressões anteriores. TypeScript estrito dos seis módulos PASS, sem CI remoto ou typecheck integral dos testes.

O identificador **interno de ocorrência** de callback deve ser criado/guardado pelo ingresso durável S0, não derivado de `statuses[].id` ou de `status+timestamp`. O `occurrence_ref` dos ensaios é só um exemplo gerado em memória; não prova persistência ou idempotência real. Ver `docs/integracoes/whatsapp-meta/wa03a-auditoria-integrada-e-ocorrencias-v0_1.md`. **Nenhum módulo de laboratório emite ACK real ou envia mensagens.**


## WA-03B — auditoria complementar e reparos em módulos anteriores

Revisados WA-01A/B/C/D e contratos residuais da WA-02C/D. Cinco falhas adversariais reproduzidas e corrigidas: posições `messages[0]`/`statuses[0]` ambíguas (agora `position.array_kind`), buffer HMAC mutável antes do parse (agora snapshot), recibo com `outcome` não textual aceito, projeção sem `intent_id` exato e falsa duplicata com `correlation_id` diferente. Nenhum destes reparos implementa autorização ou persistência operacional.

Testes locais **120/120 PASS**, TypeScript estrito dos oito módulos **PASS**. Somam 105 testes anteriores de integração/saída e 15 adversariais novos, `preaudit-gaps.test.ts` e `wa01-audit.test.ts`. Os quatro arquivos de testes unitários originais WA-01 não foram reexecutados nesta rodada e os testes Node não foram integralmente typechecked; sem CI remoto. Blobs reparados e testes novos conferidos no GitHub.

Relatório: `docs/integracoes/whatsapp-meta/wa03b-auditoria-pendencias-e-reparos-v0_1.md`. Para C07 real: `position.array_kind` por evento, mais `ingestion_batch_ref`/`occurrence_ref` e payload protegido conferidos pelo ingresso S0. Não conectar a uma operação Meta, Graph, webhook ou Supabase hospedado sem gates.


## WA-04A — Seleção de credenciais Meta por App/loja, totalmente offline

`credential-routing.ts` implementa somente o **contrato candidato de roteamento** entre `route_ref` confiável, App titular da concessionária, WABA, número emissor e canal S0. Distingue as referências de **verify token GET, App Secret POST HMAC e Graph access token**. Retorna apenas o nome do slot protegido; nunca lê ou devolve o valor do segredo, usa rede ou fornece autorização comercial. Vigência, revogação, rotação por revisão e duplicidades são negadas por padrão; `production_authorized:false` sempre.

**19/19 testes sintéticos PASS** em Node 22.16 e TypeScript estrito do módulo PASS, hashes conferidos com GitHub. O cadastro definitivo será feito pelo responsável e não foi acessado nesta etapa. Ver `docs/integracoes/whatsapp-meta/wa04a-roteamento-credenciais-meta-offline-v0_1.md`. DEC-WA-04/06 e contratos S0 continuam pendentes; não usar a POC da concessionária de demonstração como ambiente definitivo sem decisão específica.


## WA-04B — Simulação de GET/POST com HMAC por App e canal autenticado

`routed-webhook.ts` faz a **composição offline** dos módulos WA-04A, WA-01D e WA-01A: seleciona os nomes dos slots por **rota confiável**, recebe valor de segredo somente por uma porta privilegiada **fictícia**, valida GET ou HMAC do corpo bruto POST e associa cada evento a App/WABA/Phone/canal/loja configurados. Revalida revisão/vigência/slot após leituras assíncronas e recusa lotes que misturem canais de Apps independentes. Nenhum token sai na decisão e **`ack_allowed:false` sempre**.

A WA-04A também passou a rejeitar globalmente um `phone_number_id` ou `canal_id` reutilizado por Apps distintos e WABAs atribuídas a Apps diferentes. Essas verificações são de fixture, não prova do registro S0 em Supabase.

**Evidência local:** 28 cenários novos WA-04B + 19 WA-04A + 120 regressões = **167/167 testes PASS**, `tsc --strict` PASS para os módulos e 10 arquivos de testes selecionados, após pequenos reparos de tipagem em `cross-contract.test.ts` e `graph-template.test.ts`. Não houve CI remoto ou reexecução dos quatro arquivos de teste unitário WA-01 legados. Referência: `docs/integracoes/whatsapp-meta/wa04b-get-post-roteamento-hmac-v0_1.md`.

**Sem Supabase hospedado, env secrets reais, endpoint, Graph API, migrations, ACK durável, merge ou deploy.** O responsável avisará quando finalizar o cadastro de credenciais; não pedir valores no chat.


## WA-04C — Propostas de ciclo de vida de credenciais, sem token

`credential-lifecycle.ts` monta **propostas apenas em memória**, sem aplicação, para `REVOKE_APP`, `REVOKE_CHANNEL` e `STAGE_ROTATION`. A rotação proposta exige nomes novos/únicos de slots e deixa **inativo** o App no registro candidato, sem mecanismo de ativação. Ações não autentificadas ou controle operacional não são oferecidos por esta função. `production_authorized:false` permanece em todas as saídas.

**Dependência atualizada:** o token Meta definitivo necessita **verificação de outra pessoa**; testes reais e consulta/configuração de segredos estão **adiados**. Pode-se continuar com revisão e testes exclusivamente sintéticos. Executados localmente: **13/13 LIFE PASS** e TypeScript estrito PASS (somente WA-04C); hashes dos dois arquivos confirmados no GitHub. Documento: `docs/integracoes/whatsapp-meta/wa04c-ciclo-credenciais-sem-token-v0_1.md`.

O índice transversal `docs/MAPA_MENTAL.md` na branch S0 (`feat/s0-fundacao-prumo`) passa a registrar também a frente WA; atualizá-lo nos próximos incrementos significativos, sempre deixando explícitos [P]/[V local]/[R]/[D], sem substituir a fonte normativa dos PRs.


## Auditoria WA-04-AUD1 — cobertura conjunta e reparo após WA-04C

Auditoria retroativa executada em **11 módulos e 16 arquivos de testes** da frente WhatsApp/Meta, todos com hashes Git conferidos contra o código atualmente publicado. **235/235 testes sintéticos locais PASS** e TypeScript `--strict` dos 27 arquivos PASS, incluindo **45 testes WA-01 originais** agora reexecutados. Não houve CI remoto nem teste operacional.

**Achado reparado:** a WA-04C podia lançar exceção com `registry.apps` não-array ou registro não clonável; agora responde `REGISTRY_OR_APP_DENIED` sem aplicar qualquer mutação. Regressões permanentes em `wa04-audit.test.ts` (10 testes) cobrem ainda o bloqueio simulado GET/POST após revogação, staging de rotação e conservação do escopo por concessionária.

O **primeiro diagrama** do `docs/MAPA_MENTAL.md` na branch S0 foi ampliado apenas com cinco relações Meta relevantes (App da loja, HMAC, inbox/ACK, token pendente e saída via outbox). Evidências e limitações detalhadas: `docs/integracoes/whatsapp-meta/wa04aud1-auditoria-integrada-235-testes-v0_1.md`.

**Não significa homologação real:** não existe token liberado, autorização de envio, conexão com o Supabase hospedado, inbox durável comprovada, webhook operacional, merge ou deploy. DEC-WA-04 e DEC-WA-06 ainda pendentes.


## WA-04D — lifecycle versionado e regressão de revogação durante POST

`lifecycle-simulation.ts` implementa um **FakeVersionedMetaRegistry exclusivamente em memória** para exercitar transições de revogação/rotação da WA-04C, conferindo revisão, loja, `operation_ref` repetido/conflitante e estado inativo até verificação externa. Não é backend, mecanismo operacional de credenciais ou transação no Supabase.

**Defeito corrigido:** `routed-webhook.ts` podia conferir o encerramento de um POST com um snapshot do App anterior à revogação. Agora **reconsulta** a fonte de configuração e **revalida cada vínculo** do lote antes de liberar eventos técnicos; um teste adversarial falhou antes e passou após o reparo. Ainda existe janela de concorrência até um futuro commit transacional da S0; `ack_allowed:false` permanece.

**Testes locais 250/250 PASS** (235 anteriores + 15 LIFE-D) e TypeScript estrito PASS nos 12 módulos/17 suítes, sem CI remoto nem dados reais. Relatório: `docs/integracoes/whatsapp-meta/wa04d-ciclo-credenciais-concorrencia-v0_1.md`. Os tokens permanecem bloqueados por verificação externa.


## WA-05A — Transação fictícia de inbox com revalidação no commit

`transactional-ingress.ts` adiciona **somente fixtures em memória**: `FakeProtectedPayloads` e `FakeTransactionalInbox`. Conecta o POST assinado e mapeado pela WA-04B ao registro fake versionado da WA-04D, refazendo o vínculo vigente **no instante da inserção simulada**. Se houver revogação/rotação do App ou canal, payload ausente/divergente, lote contraditório ou falha de gravação fictícia, nenhum marcador parcial é inserido. `messages[0]` e `statuses[0]` mantêm ocorrências separadas, e callbacks iguais em lotes distintos não sofrem dedupe por `wamid`.

**268/268 testes sintéticos locais PASS** (250 anteriores + 18 WA-05A), TypeScript estrito PASS em 13 módulos/18 suítes, hashes dos 2 arquivos novos conferidos. **A fixture não possui cofre real, transação SQL, prova de commit, recibo COMMITTED ou ACK HTTP**: `ack_allowed:false` em todas as respostas. A S0 real deve realizar validação e persistência **atômicas**, com payload protegido e política DEC-WA-06, antes de qualquer ACK.

Ver `docs/integracoes/whatsapp-meta/wa05a-ingresso-transacional-simulado-v0_1.md`. Sem Meta/Graph reais, token, Supabase hospedado, migrações, merge ou deploy.


## WA-05B — Recuperação de ingresso e efeito interno, somente laboratório

`recovery-journal.ts` simula um registro técnico de batches/ocorrências **em memória**, falhas antes/depois da gravação, resposta de commit perdida, redelivery por `batch_ref`, consultas após reinício lógico de trabalhador, leases com fencing e prevenção de repetição de efeitos **somente internos ao próprio objeto fake**. Repetições de callbacks em batches distintos são preservadas; `wamid` nunca é usado como ID único de callback.

**294/294 testes locais PASS** (268 anteriores + 26 RECOV), TypeScript estrito PASS dos **14 módulos e 19 arquivos de teste**. Blobs Git do código e testes novos coincidem com os arquivos executados. O módulo **não** verifica HMAC, payload real, autorização S0 ou persistência; criar outra instância do journal **perde todos os dados**. Nenhum recibo `COMMITTED` ou ACK HTTP é emitido, e nenhuma operação externa se torna exactly-once. Documento: `docs/integracoes/whatsapp-meta/wa05b-recuperacao-ingressos-sem-token-v0_1.md`.

DEC-WA-04/06, token Meta e implementação de inbox transacional S0 continuam pendentes. Sem Graph API, Supabase hospedado, merge/deploy ou modificações na POC concessionária de demonstração.

**Complemento de auditoria WA-05B:** IDs `wamid` com padding e caracteres opacos são aceitos, controles recusados; fixture não clonável produz `LAB_INVALID` sem exceção. Total final **294/294 PASS**, 26 RECOV + 268 regressões, com hashes Git atualizados no relatório.

## WA-05-AUD1 — auditoria retroativa WA-05A/B e reparos

Revisão independente da fronteira fake `transactional-ingress.ts` (WA-05A) e do journal `recovery-journal.ts` (WA-05B). A WA-05A manteve seus cenários sem novo defeito reproduzido. **Cinco falhas/lacunas WA-05B foram demonstradas e corrigidas**: divergência entre metadados lidos e clonados, exceções em getters, ausência de escopo App/loja/canal em `claim` e `finish`, e aceitação de campos desconhecidos potencialmente sensíveis.

`TrustedWorkerScope` é agora obrigatório **em runtime** nas operações de worker da fixture; ele **não é autenticação**, somente validação simulada de contexto. Os 26 testes RECOV foram adaptados e o novo `recovery-audit.test.ts` acrescenta 12 cenários adversariais.

**306/306 testes locais PASS**, TypeScript estrito PASS sobre 14 módulos e 20 arquivos de testes. Hashes publicados conferidos; não há CI remoto, credenciais, transação real ou ACK. Documento: `docs/integracoes/whatsapp-meta/wa05aud1-auditoria-retroativa-ingresso-recuperacao-v0_1.md`.
