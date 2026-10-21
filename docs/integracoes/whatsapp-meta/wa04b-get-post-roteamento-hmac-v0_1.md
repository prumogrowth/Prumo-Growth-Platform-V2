# WA-04B — Roteamento confiável GET/POST, HMAC por App e escopo de canal (offline)

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Data:** 18/10/2026. **Estado:** implementação candidata [P] e testes sintéticos na branch Draft do PR #2. **Sem** Supabase hospedado, leitura de segredos definitivos, tráfego Graph/Meta, mensagens reais, migration, troca do webhook concessionária de demonstração ou deploy.

## 1. Fronteira implementada

O módulo `integrations/whatsapp-meta/routed-webhook.ts` conecta as interfaces **já existentes** da WA-04A (`credential-routing.ts`), WA-01D (`verify-get.ts`) e WA-01A (`inbound.ts`) utilizando portas totalmente simuláveis:

- `currentRegistry()`: snapshot lógico do registro **confiável** do App/rota/concessionária/canais; sua futura origem, autorização e consistência transacional pertencem ao núcleo S0.
- `resolveSecret(slot)`: somente a referência interna do segredo é passada à porta privilegiada; o valor é recebido transitoriamente em memória para HMAC ou comparação GET. **O módulo de seleção WA-04A não recebe nem devolve valor de segredo** e as decisões WA-04B não retornam token/App Secret.
- `nowMs()`: relógio da aplicação protegida; não aceitar horário fornecido pela Meta ou por usuário público.
- `TrustedRoute` (`route_ref`, `expected_revision`): selecionado exclusivamente pelo host/endpoint confiável. **Não pode vir de body, query, header de cliente ou claims de tenant não autenticadas.**

`inspectRoutedMetaGet` seleciona `GET_VERIFY_TOKEN`, consulta a porta de segredo, verifica sua referência/revisão/vigência novamente após a consulta, executa o validador GET existente e revalida a rota. Retorna *somente* desafio validado ou código técnico sem valores sensíveis. Não é endpoint HTTP.

`inspectRoutedMetaPost` seleciona `POST_APP_SECRET` por rota confiável **antes de interpretar o payload**; captura o corpo limitado a **256 KiB** antes de qualquer `await`; autentica HMAC-SHA256 contra bytes idênticos aos interpretados pelo parser; revalida App/revisão/slot/vigência e vincula **cada evento** ao canal S0 configurado, exigindo WABA + `phone_number_id` exatos. Se **qualquer** item não pertence ao App/canal autorizado, **rejeita todo o lote**. Um POST assinado por um App pode conter múltiplas WABAs pertencentes a **esse mesmo App**, nunca misturar aplicativos independentes.

Toda saída POST, positiva ou negativa, marca `ack_allowed:false` e `production_authorized:false`. O sucesso **não** é ACK Meta; os eventos escopados incluem identificadores e podem conter dados pessoais em seus metadados: **não registrar payload, telefone ou retorno integral em logs/telemetria**. Ausentes: recibo S0 `COMMITTED`, enfileiramento/persistência, recuperação, política de quarentena DEC-WA-06, autenticação do resolver em produção e conexão HTTPS.

## 2. Endurecimento WA-04A realizado durante WA-04B

A validação do `TrustedMetaRegistry` agora exige unicidade **global entre Apps** de `phone_number_id` e `canal_id`. Uma WABA pode possuir múltiplos números na mesma App, mas não pode ser atribuída a dois Apps diferentes dentro do registro. Esses três conflitos passaram a invalidar o registro completo, em vez de apenas uma chave WABA + número duplicada.

**Não é o cadastro Meta definitivo:** a relação de uma WABA com múltiplos aplicativos, se houver no modelo real, deverá ser reavaliada antes da homologação, preservando a decisão DEC-WA-05 de titularidade isolada por concessionária.

## 3. Segurança de rotação e revogação

No ensaio, a configuração de App e segredo é consultada novamente **depois da resolução do segredo** e **depois da validação HMAC** (ou do desafio GET). Troca de revisão/slot, expiração, desativação e canal removido falham sem devolver escopo para processamento. A configuração real deve **sempre** incrementar a revisão em cada rotação/troca de binding, e o backend deve provar a origem confiável do registro. O exemplo não elimina todas as corridas de um sistema distribuído nem oferece transação contra a Meta.

**Segredos continuam sob responsabilidade do usuário no Supabase:** os testes usam apenas valores que começam por `ONLY_FAKE_` e slots `SLOT_*`; nenhuma senha/token real foi criada, lida ou migrada. Não assumir o projeto sandbox da POC concessionária de demonstração como ambiente definitivo. A verificação de presença/valor dos segredos será feita **somente após a notificação do usuário e um procedimento autorizado e controlado**; não é um pedido para compartilhar valores no chat.

## 4. Testes e resultados efetivamente executados

Ambiente local Node.js **v22.16.0** e TypeScript **5.8.3**. Comando Node `node --experimental-strip-types --test` executado sobre **10 arquivos de teste**: `routed-webhook.test.ts`, `credential-routing.test.ts`, `graph-outbound.test.ts`, `graph-template.test.ts`, `offline-dispatch.test.ts`, `technical-reconciliation.test.ts`, `scope-isolation.test.ts`, `cross-contract.test.ts`, `preaudit-gaps.test.ts` e `wa01-audit.test.ts`.

- **167/167 PASS**: 28 cenários WA-04B novos; 19 WA-04A; 120 regressões anteriores.
- TypeScript **`--noEmit --strict` PASS** dos módulos e de todos os **10 arquivos de teste** dessa rodada, habilitando os tipos Node locais disponíveis no `ts-node`. Dois defeitos anteriores **somente de tipagem** em testes (`cross-contract.test.ts`, `graph-template.test.ts`) foram corrigidos sem mudar o comportamento runtime.
- Arquivos legados específicos `inbound.test.ts`, `durable-receipt.test.ts`, `technical-keys.test.ts`, `verify-get.test.ts` **não foram incluídos nesta suíte**, embora seus módulos tenham integrado o teste WA-04B e os testes de contratos. Não anunciar todo o repositório como 100% testado.
- Hashes Git dos arquivos ensaiados, conferidos na branch PR #2:
  - `routed-webhook.ts` **`b20e7a2fd977858a412bf1e3160e8ecca1c5c99f`**
  - `routed-webhook.test.ts` **`bfb6781736596385591fe2e98960b8fed2c37b0f`**
  - `credential-routing.ts` (endurecido) **`b3dc24c897138dd04ad915ddc12179fbee4423e6`**
  - `cross-contract.test.ts` (tipagem) **`c77e1bb47effa9d9741866cfcdc701d23a8ee3a5`**
  - `graph-template.test.ts` (tipagem) **`5245c06fde641ed16588f5f11220bfe1ac8a3004`**
- Não houve GitHub Actions/CI remoto, banco real, Edge Function, Graph API, Meta callback real ou teste de restauração.

## 5. Gate e próximo desenvolvimento

**GO** para nova evolução sintética: desenhar contrato de rotação/revogação do resolver com privilégios mínimos e prova de origem, ou simular o handoff da requisição já assinada à inbox durável fake S0 (sem HTTP ACK). A frente principal precisa confirmar o registro autenticado `route_ref → App → WABA/Phone Number ID → canal_id + concessionaria_id`, revisões/expiração, política de secret slots, associação C07 por ocorrência e papel responsável pela persistência segura.

**NO-GO** para cadastrar/consultar segredos definitivos sem aviso, usar tokens Meta reais, habilitar `verify_jwt=false` em produção sem gateway seguro, receber webhooks operacionais, retornar HTTP 200, transmitir mensagens, executar migrations no projeto Supabase hospedado, mesclar PRs ou alterar concessionária de demonstração. DEC-WA-04 e DEC-WA-06 pendentes; DEC-WA-05 aprovou a **titularidade** do App/WABA/emissor por concessionária, não o onboarding de números.
