# WA-01A — Adaptador Meta inbound isolado (candidato)

> **ENTRADA ÚNICA DA DOCUMENTAÇÃO FUNCIONAL (21/10/2026):** [LEIA PRIMEIRO — frente WhatsApp/Meta](../../docs/integracoes/whatsapp-meta/README.md). Ali estão a especificação atual, as 20 regras identificadas, o mapa de conflitos entre fontes e a auditoria documental. O README técnico abaixo é um histórico de **módulos offline/candidatos**, não a especificação vigente de produto nem evidência de integração em produção.

> **Índice documental vigente (21/10/2026):** o histórico técnico abaixo deve ser interpretado junto à [fonte de decisões atuais WhatsApp/Meta](../../docs/integracoes/whatsapp-meta/00-decisoes-vigentes-precedencia-documental-2026-10-21.md). Este README descreve fases WA-01 em diante e não substitui a matriz de decisões posteriores sobre WABA por loja, finalidades de templates, duas falhas consecutivas, opt-out por concessionária e contratos futuros de MCP. A auditoria desta fase é **somente documental**, não comprovação de execução do código.


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

## WA-05C — Contrato Meta → S0, sem recibo confiável/ACK

`s0-handoff-contract.ts` reúne o POST Meta inspecionado **com credenciais fictícias** em um envelope mínimo candidato para a S0: batch/rota e revisão, App, referência do corpo protegido, `payload_sha256`, `scope_sha256`, contagem e posição/escopo por ocorrência. Não inclui corpo, PII do participante, token, segredo, `occurrence_ref` definitivo nem persistência. O `scope_sha256` vincula revisão/canal/loja/posição, mas **não é autenticação**.

`reviewS0ReceiptFixture` só confere estrutura, escopo e contagens, recusando campos inesperados, getter hostil e divergências. Mesmo `COMMITTED` aparentemente válido retorna **`STRUCTURE_MATCHES_BUT_UNVERIFIED`** com `ack_allowed:false` e `production_authorized:false`: não existe ponte para HTTP ACK nem para uma transação S0 real.

**330/330 testes sintéticos locais PASS** (24 S0C novos + 306 regressões), TypeScript estrito PASS em 15 módulos/21 suítes; hashes Git dos arquivos novos conferidos. [Documento WA-05C](../../docs/integracoes/whatsapp-meta/wa05c-contrato-handoff-meta-s0-v0_1.md). Token Meta e DEC-WA-04/06 continuam pendentes; sem Supabase hospedado, POC concessionária de demonstração, merge/deploy ou CI remoto.

## WA-05D — Gate interno S0 simulado, sem autorização real

Novo `s0-ingress-gateway.ts` cria o `FakePrivilegedS0Ingress`: entrada candidata WA-05C com HMAC **somente de fixture**, origem de serviço declarada por porta protegida **fictícia**, confirmação de bytes no `FakeProtectedPayloads`, digest do corpo/escopo recalculados e revalidação independente App/loja/canal/revisão no momento do **commit em memória**. Rejeita campos inesperados, escopos alterados, getters, falha de escrita, replay divergente e serviço revogado.

**352/352 testes sintéticos PASS** (22 GATE novos + 330 anteriores), TypeScript estrito PASS (16 módulos/22 testes). Hashes Git dos 2 arquivos conferidos; [relatório WA-05D](../../docs/integracoes/whatsapp-meta/wa05d-porta-interna-s0-simulada-v0_1.md).

A identidade de serviço dos `ports` **não é autenticada**, o `Map` **não é durável**, a fixture **não contém proteção real LGPD/SQL**, e `LAB_ACCEPTED` **nunca** autoriza HTTP 200 ou um recibo `COMMITTED`. Nenhum acesso Supabase/Meta/Graph real, CI remoto, merge/deploy ou alteração na POC concessionária de demonstração.

**Auditoria WA-05D concluída:** GATE-21 demonstrou que status/instante do provedor não estavam cobertos por `scope_sha256`; digest da WA-05C e conferência da WA-05D corrigidos. GATE-22 verifica colisão de batch contra payload-ref diferente. **352/352 PASS** e TypeScript estrito PASS; ainda não há identidade de serviço operacional nem ACK.

## WA-05D-AUD1 — Auditoria de origem interna e atestação fictícia

**Falha adversarial reproduzida:** `scope_sha256` não era uma assinatura. O digest podia ser recalculado depois de adulterar `provider_kind`, mantendo o HMAC Meta anterior e fazendo o simulador S0 retornar `LAB_ACCEPTED`. Agora `FakePrivilegedS0Ingress.admit` **exige `FakeInternalServiceProof` HMAC**, com chave interna de fixture **distinta do App Secret e do token Graph**, vinculada a serviço, envelope completo e validade. Confere prova e rotação também após `beforeCommit`.

**358/358 testes locais PASS** (352 anteriores + 6 GATE-23..28), TypeScript estrito PASS em 16 módulos e 22 testes. Blobs auditados: gateway `9f54c91c0c59dec24660b4711df61603305b7f59` e testes `1f44fe6eed8ef199b8077bcfcb90a7e266be451c`. Relatório: `docs/integracoes/whatsapp-meta/wa05d-aud1-atestacao-interna-offline-v0_1.md`.

A chave simulada e o principal injetado **não são autenticação de produção**; ainda faltam cofre/ACL de serviço, nonce e prevenção durável de replay, transação ACID, payload íntegro protegido e recibo/ACK aprovado. Token Meta depende de validação por terceiro. Sem deploy, merge ou serviços reais.

## WA-06B — serialização canônica da prova interna candidata (somente bytes, 18/10/2026)

A [WA-06A](../../docs/integracoes/whatsapp-meta/wa06a-contrato-identidade-servico-replay-s0-v0_1.md) foi desdobrada em **código puro de contrato**, `internal-proof-wire-v1.ts`, com `canonicalizeInternalProofV1`. Produz bytes determinísticos e versionados com domínio e campos prefixados por comprimento para `service_ref`, finalidade/audiência, `request_ref`, `nonce_ref`, versão de chave, lote, rota, payload e todas as posições/status. Não assina, não verifica credenciais, não consome nonce, não autentica S0 e nunca autoriza ACK. **Não** integra o emissor `FakeInternalServiceProof` WA-05D ao serviço real.

`internal-proof-wire-v1.test.ts`: **WIRE-01..15: 15/15 PASS local** em Node 22.16 e TypeScript `--strict` PASS apenas dos arquivos novos, usando declaração local temporária da interface de tipo WA-05C. Blobs Git iguais aos ensaiados: código `1dc5fddd1893d69151043a1a5ea70fcc03a0c34f`, testes `773f1ccc950497ea787d04ab26b789d2403aef54`. A suíte antiga de 358 testes **não foi reexecutada** no incremento WA-06B, e não houve CI remoto. Ver [relatório WA-06B](../../docs/integracoes/whatsapp-meta/wa06b-serializacao-canonica-prova-interna-v0_1.md).

**Gates:** revisão cruzada de formato/interoperabilidade e fonte real da identidade S0; nonce e ACL transacionais, recibo de commit, DEC-WA-04/06, token de terceiro e toda autorização operacional. PR Draft; sem merge, migração, POC concessionária de demonstração, Supabase hospedado, Graph, envio ou plano pago.

## WA-06C — referência independente Python / TypeScript (18/10/2026)

A frente verificou em **duas linguagens** o formato de bytes candidato WA-06B: `wa06c_reference.py` produz cinco vetores independentes de consistência, enquanto `wa06c-crossruntime.test.ts` executa **o encoder TypeScript publicado** contra esses cinco valores e três negativas. Evidência local: **Python 2/2 métodos unittest PASS** (inclui cinco subtestes), **Node 8/8 PASS**, `tsc --strict` dos dois arquivos TS selecionados PASS com espelho temporário do tipo WA-05C. Blobs testados iguais aos publicados: Python `03c14661d98bb701167cd4524aaa0eca29acf11a`, Node `b30b1b72fdb0cd7d484580d0f464d9e3a9a75064`; encoder original `1dc5fddd1893d69151043a1a5ea70fcc03a0c34f`. [Relatório WA-06C](../../docs/integracoes/whatsapp-meta/wa06c-verificacao-independente-python-typescript-v0_1.md).

**Não** é autenticação de origem, HMAC real, nonce persistido, commit, recibo ou ACK: nenhuma porta operacional ou migration foi criada. WA-06D candidata requer **teste transacional PostgreSQL descartável** pela S0. A suíte histórica WA-05D-AUD1 358/358 e a WA-06B 15/15 não foram reexecutadas nesta etapa. DEC-WA-04/06 pendentes, plano Free; sem Graph/Meta/Supabase hospedado/POC concessionária de demonstração/merge/deploy.


## WA-07 / CF-OP-02 — janela e cadeia humana

O contrato candidato [WA-07](../../docs/integracoes/whatsapp-meta/wa07-contrato-janela-e-templates-cf-op-02-v0_1.md) separa **janela Meta 24h desde último inbound do cliente**, **conclusão humana** e **C09 24h após prova de envio real do template final**. Meta transporta eventos e templates preaprovados, não escolhe operador/agenda, não marca perdido, não fecha UI e não converte template outbound em janela livre sem resposta do cliente. Plano pós-humano, seleção de template individual e remanejamento Prumo são responsabilidades respectivamente S0/OpenAI, UI→S0 e S1-002. **Riscos de prova sent, categoria do produto, opt-out, cobrança e política externa [R/V]; não há integração real.** Referências: PR #7 e issue #6.

## WA-06-AUD1 — auditoria do contrato atualizado WA-07 (18/10/2026)

Após ler a [WA-07](../../docs/integracoes/whatsapp-meta/wa07-contrato-janela-e-templates-cf-op-02-v0_1.md) e CF-OP-02, foi auditada a WA-06A/B/C. Achado reproduzido: o encoder WA-06B **antes aceitava lote com duas concessionárias sob uma única Meta App** e mapeamentos contraditórios de `channel→(waba,sender)`. O [relatório WA-06-AUD1](../../docs/integracoes/whatsapp-meta/wa06-aud1-auditoria-contrato-atualizado-wa07-v0_1.md) registra os reparos em `internal-proof-wire-v1.ts`, com regressões em `internal-proof-wire-audit.test.ts`.

**Evidência local desta auditoria:** 7/7 testes AUD-01..07 PASS e TypeScript `--strict` PASS dos arquivos em escopo, com cópia local de auditoria e tipo WA-05C temporário; os cinco vetores de referência Python recalculados coincidiram; não houve CI nem execução das suítes antigas completas. Os blobs atuais publicados são encoder `f4ac80c5e8fe09f4d4ef0ae7673cd8e8f815feeb` e regressões `d78f994ade18d987f8e90645ab404e22efb9cc44`. **Os blobs históricos anteriores citados nas seções WA-06B/C não são mais o blob atual do encoder**: continuam como evidência temporal, não identificador da implementação corrigida.

**WA-07 permanece contrato [D-negócio/P-R-V], não execução:** janela livre Meta desde último inbound do cliente, template de saída não reabre janela, `sent` final confirmado é pré-requisito de sinal ao relógio C09 da S0, nenhuma mudança comercial Meta; não reinterpretar a autorização técnica de ingresso como permissão para C03/C06/C12. `received_at`, política de relógio e fonte confiável `sent` ainda pendentes. DEC-WA-04/06, nonce+ACL ACID, S0 e homologação real ainda bloqueiam ACK/produção. Sem envio, Graph, Supabase hospedado, POC, merge, deploy ou custos.

## WA-06D/A — ensaio PostgreSQL para ingresso (ainda sem execução)

Foi publicado um [roteiro SQL autocontido](lab/wa06d_pg17_atomicity.sql), com 7 tabelas `TEMP`, função `pg_temp`, 11 casos candidatos e `ROLLBACK`, e o [relatório de escopo WA-06D/A](../../docs/integracoes/whatsapp-meta/wa06d-a-roteiro-postgresql-atomicidade-v0_1.md). Trata **apenas** atomicidade, replay e falhas de um ingresso **fictício**. Não é migration S0; não autentica serviço nem canal real e a resposta `IN_TX_ONLY` não permite ACK. A comparação com S0-029/032/033 orienta futura integração sem duplicar o esquema comercial.

**Situação:** artefato no PR #2, checagens editoriais/estáticas passaram, mas **0/11 SQL executados** porque o ambiente de auditoria não possui servidor nem cliente PostgreSQL. Exige execução posterior em PG17 local descartável, evidência de logs, revisão S0 e teste separado de concorrência, nonce/autorização real e recibo pós-commit. DEC-WA-04/06 abertas. Nada de Supabase hospedado, POC concessionária de demonstração, Graph, merge ou deploy.

## WA-06D/A2 — runner local protegido (18/10/2026)

O roteiro PostgreSQL WA-06D/A deve ser chamado apenas pelo `lab/run-wa06d-local.sh`, com banco descartável `wa06d_test_<sufixo>`, `127.0.0.1:5432`, removendo `PGHOSTADDR/PGSERVICE/PGSERVICEFILE/PGOPTIONS`. O guard não identifica um túnel externo: **nunca usar porta encaminhada a ambiente hospedado**. `lab/test_wa06d_runner.py` executou **5/5 testes Python locais PASS com binário `psql` falso**, `bash -n` PASS, incluindo injeção de `PGHOSTADDR` remoto; blobs coincidem com código testado. Detalhes no [adendo WA-06D/A2](../../docs/integracoes/whatsapp-meta/wa06d-a-roteiro-postgresql-atomicidade-v0_1.md). **Ainda 0/11 testes SQL executados**, nenhum serviço ou Meta comercial alterado.

## WA-06D/A3 — posição integral de evento Meta (18/10/2026)

Revisão pré-execução encontrou um defeito no roteiro PostgreSQL WA-06D/A: `UNIQUE(batch,kind,item_index)` colidia para ocorrências legítimas em `entry[]/changes[]` diferentes. Corrigido no SQL de laboratório para usar a **posição integral** `(batch,entry_index,change_index,kind,item_index)`, igual à semântica WA-05C/06B. A fixture de revogação agora restaura o canal antes dos testes seguintes. Acrescentados WA06D-12/13/14 para multientrada, posição realmente duplicada e dois canais da mesma App/loja. Relatório [WA-06D/A3](../../docs/integracoes/whatsapp-meta/wa06d-a-roteiro-postgresql-atomicidade-v0_1.md), código blob `e011969413332565bc4c3e1e37490f5ad99d5ac8`.

**11 checagens estáticas de conteúdo passaram; 0/14 testes PostgreSQL foram executados.** O runner offline anterior continua com 5/5 testes de proteção; isso NÃO comprova o SQL, identidade operacional, commit pós-transação nem HTTP ACK. Nenhum merge, deploy ou ambiente real alterado.

## WA-06D/B — cluster efêmero e prova pós-COMMIT (18/10/2026)

O ensaio WA-06D foi ampliado para um **runner que cria e destrói seu próprio PostgreSQL 17**, sem TCP, usando somente socket Unix privado e usuário não-root. `lab/run-wa06d-ephemeral.sh` chama o roteiro WA06D-A de 14 casos (`ROLLBACK`) e, **em conexões posteriores separadas**, os novos `lab/wa06d_pg17_postcommit_setup.sql` e `lab/wa06d_pg17_postcommit_verify.sql`: **6 novos gates candidatos** de leitura depois de COMMIT, digest, posições, colisão de request e reversão de subtransação. `lab/test_wa06d_ephemeral_runner.py` executou **5/5 testes Python com Postgres simulado PASS**, `bash -n` PASS; os 4 arquivos versionados coincidem byte a byte com os executados/inspecionados no laboratório local.

**Limitação fundamental:** `0/20` testes SQL PostgreSQL executados, por falta de PostgreSQL local, e `0` verificações de serviço/Meta real. O novo ensaio só comprovará leitura após COMMIT **quando efetivamente executado**, não crash durability/COMMIT_UNKNOWN, identidades/revogação reais, payload protegido, HTTP ACK ou integração S0. [Relatório WA-06D/B](../../docs/integracoes/whatsapp-meta/wa06d-b-cluster-efemero-recuperacao-poscommit-v0_1.md). Nada de deploy, hosted, POC concessionária de demonstração, Graph, merge ou custos.


## WA-06D/AUD2 — auditoria de alinhamento e correções (18/10/2026)

[Relatório WA-06D-AUD2](../../docs/integracoes/whatsapp-meta/wa06d-aud2-auditoria-aderencia-execucao-v0_1.md). Achado: os B01–B06 **não testam a função de ingresso WA-06D/A** nem o caminho real S0-029/032/033; usam inserts de fixture separados. A prova B, se executada um dia, cobrirá apenas persistência sintética pós-COMMIT, **não integração/ACK**. Reparo: `run-wa06d-ephemeral.sh` sempre tenta desligar o PG mesmo quando a inicialização falhar; se continuar ativo, preserva cluster e falha (70). O marcador da fixture pós-COMMIT agora é `FIXTURE_COMMITTED_NOT_ACK`, com assertiva correspondente. **7/7 testes Python do runner com binários falsos PASS locais, `bash -n` PASS e root real rejeitado (77); 0/20 SQL PostgreSQL executados.** Blobs atuais: runner `3057062b31d1e7c63f8c26a9bac9c4508ce71890`, testes `1c8e49fbbb6d1fe88e5da9173fc0464c002c7af5`, setup `dc159fc4c00ee6f4708fa563d74f189ea5ce098c`, verify `ecb690e78647bf209cc17b32ed53cfc4ad152472`. Os hashes anteriores são históricos. **Próxima prioridade: não criar mais suítes sintéticas; executar PG17 descartável e buscar prova integrada S0.**

## Integração real adiada, contratos e testes antecipados (19/10/2026)

[Proposta de fases sem credenciais reais](../../docs/integracoes/whatsapp-meta/estrategia-apis-sem-credenciais-reais-v0_1.md): construir S0/Meta/IA/atendimento humano e interfaces **sem ativar Graph, OpenAI ou integrações bancárias reais**, mas definir contratos de eventos, segurança, erros, ACK e testes agora. **PostgreSQL local descartável e integração S0 não são dependências de API externa, portanto não devem esperar até o fim.** As seis fixtures de WA-06D/B não executam o caminho Meta→S0. Evidência atual: **0/20 testes SQL PG**; executar os já existentes antes de expandir fixtures. 

**Estado [P]:** proposta operacional, sem aprovação implícita de mudança de contrato, percentual ou custo; PR Draft e sem deploy/hosted.

## WA-08 — conciliação técnica rigorosa sem API externa (19/10/2026)

[Relatório de implementação e testes pendentes](../../docs/integracoes/whatsapp-meta/wa08-conciliacao-status-validacao-estrita-offline-v0_1.md). A rotina `technical-reconciliation.ts` passou a exigir `wamid` canônico, HTTP 2xx e estado Graph coerentes (`API_ACCEPTED`, sem erro Meta ou retry), números emissores com formato técnico esperado e posições de callback `statuses[]` com índices inteiros não negativos; a consulta de projeções também recusa IDs arbitrários. Preserva múltiplas ocorrências posicionais mesmo com mesmo wamid/status/tempo. `technical-reconciliation.test.ts` contém **REC-25..35 (11 novos casos)** incluindo saída real do classificador **offline** Graph (sem conexão). **0/11 executados nesta sessão**; teste TypeScript integral e PG17 permanecem gates distintos. Sem ACK, alteração comercial, reenvio automático, conexão Meta ou produção.

## WA-09 — evidência técnica Graph/status validada offline (19/10/2026)

[Relatório de execução e limites](../../docs/integracoes/whatsapp-meta/wa09-evidencia-tecnica-status-validador-testado-offline-v0_1.md). Novo módulo puro `status-evidence.ts` com três validações de `wamid`, posição `statuses[]` sem getters e evidência Graph HTTP 2xx coerente; reutilizado pelo conciliador `technical-reconciliation.ts`. **8/8 testes WA09 executados e aprovados localmente em Node 22**, `tsc --strict` do helper PASS; Git blob SHA do fonte/teste **idênticos** aos arquivos executados: `4ce9bf8319a0dd2ba621643819dd5435833f3a77` / `97560d5d2b0c12b8178e8b37841c31d449c4f873`. **A suíte integrada REC-01..35 NÃO foi executada nesta sessão** e os testes WA-06D em PostgreSQL continuam bloqueados (0/20). Nenhuma API Meta, persistência S0, ACK, autenticação real, decisão comercial, produção ou merge.

## WA-09B/C — identificadores coerentes e executor offline (19/10/2026)

[Relatório WA-09 ampliado](../../docs/integracoes/whatsapp-meta/wa09-evidencia-tecnica-status-validador-testado-offline-v0_1.md). Corrigida a validação de `attempt_id`/`correlation_id` no predicado `isAcceptedGraphEvidence`, e aplicada uma verificação compartilhada de `phone_number_id` técnico ao vínculo Graph e ao callback em `technical-reconciliation.ts`. O formato não prova ausência de PII nem substitui autenticação Meta. **11/11 testes WA09 locais em Node 22 PASS, `tsc --strict` do helper PASS; blobs de fonte e teste no GitHub idênticos aos testados.**

Executor zero-install: `bash integrations/whatsapp-meta/run-offline-tests.sh --unit` (11 casos), `--focus` (inclui conciliador/Graph) ou `--all` (26 suítes atuais). **O `--all` recusa checkout incompleto (exit 66) em vez de declarar sucesso indevido**, e o runner limpa preloads Node herdados antes da execução. Snapshot local parcial: `--unit` 11/11 PASS, `--focus/--all` recusados corretamente. **REC-01..35 e a suíte completa não foram executadas**; PostgreSQL WA-06D e S0-040 também pendentes. Sem APIs reais, ACK, Graph, mensagens reais, Supabase hospedado, negócio comercial, CI pago, deploy ou merge.

## WA-10 — unicidade inversa da tentativa técnica (19/10/2026)

[Relatório de desenvolvimento, auditoria e execução](../../docs/integracoes/whatsapp-meta/wa10-vinculo-inverso-tentativa-wamid-offline-v0_1.md). `attempt-binding.ts` adiciona índice inverso **em memória** por App/loja/`attempt_id`, impedindo que uma tentativa já vinculada a um `wamid` seja silenciosamente vinculada a outro. `technical-reconciliation.ts` passou a exigir esse vínculo antes de registrar um envio técnico, sem tomar decisões comerciais nem autorizar retransmissão. A checagem de tipo foi endurecida após detectar coerção numérica por `RegExp.test`.

**Evidência executada:** WA10-01..11 **11/11 PASS em Node22**, `tsc --strict` do helper PASS; blobs dos dois arquivos Git iguais aos executados. Executor `run-offline-tests.sh --binding` também **11/11 PASS**, `bash -n` PASS; `--all` detecta checkout parcial e falha com exit 66. A suíte completa tem agora **27 arquivos `*.test.ts`** na frente Meta; `--focus` inclui WA10. **REC-36..39 escritos, ainda não executados**, assim como a regressão REC-01..39 e os testes PG17; não há validação Meta→S0 end-to-end, nem API externa conectada. PR continua Draft, sem merge/deploy.
