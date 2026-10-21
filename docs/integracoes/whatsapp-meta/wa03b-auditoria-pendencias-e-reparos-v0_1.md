# WA-03B — Auditoria dos módulos anteriormente não auditados | 18/10/2026

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Estado:** revisão adversarial de WA-01A/B/C/D e regressão das WA-02A/B/C/D e WA-03A. Reparos publicados **exclusivamente** na branch Draft do PR #2. Nenhum merge, deploy, migration hospedada, webhook operacional, Graph API, número real ou custo pago.

## Objetivo e evidências examinadas

Auditar código efetivamente versionado em `integrations/whatsapp-meta/`: `inbound` (assinatura/parsing), `durable-receipt` (decisão abstrata de ACK), `technical-keys` (correlação não autoritativa), `verify-get` (challenge por App), `graph-outbound`, `graph-template`, `offline-dispatch` e `technical-reconciliation`. Consideradas as restrições da [interface S0 ↔ Meta](interface-compartilhada-s0-meta-v0_1.md) e a auditoria [WA-03A](wa03a-auditoria-integrada-e-ocorrencias-v0_1.md).

O contrato externo consultado usa `statuses[].id` como ID **da mensagem**, não ID exclusivo de evento. Referência oficial da Meta: [Coleção WhatsApp Cloud API / webhook payload](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api).

## Falhas realmente reproduzidas antes da correção

Foram criados testes adversariais, que apresentaram **cinco falhas antes dos reparos**:

1. **WA-01A — posição ambígua:** `messages[0]` e `statuses[0]` do mesmo `entry/change` geravam a mesma posição `entry_index/change_index/item_index`. Isso é **perigoso para a proposta de `occurrence_ref`**, caso a posição seja usada como parte da identidade interna.
2. **WA-01B — tipo de `outcome` permissivo:** `String(r.outcome)` aceitava um objeto dotado de `toString()` que representava `ACCEPTED_DURABLE`. Apesar de a porta futura exigir resposta de backend autenticado, essa validação estrutural não podia aceitar o objeto. A composição de contagens também ganhou limites por componente para não depender de soma potencialmente imprecisa.
3. **WA-02D — projeção sem intenção vinculada:** referência com `intent_id` diferente, mas igual escopo e `wamid`, conseguia consultar projeção técnica.
4. **WA-02D — duplicidade com correlação alterada:** o mesmo envio/tentativa podia ser marcado `ALREADY_LINKED` com `correlation_id` diferente.
5. **WA-01A — risco de alteração de buffer na fronteira HMAC:** o chamador podia modificar `Uint8Array` enquanto o processamento assíncrono da assinatura estava em andamento. O parser e o HMAC não garantiam consumir a mesma fotografia do buffer. O ensaio pré-reparo não obteve resultado válido sob essa mutação, mas revelou a falta de contrato de imutabilidade; o novo ensaio exige snapshot preservado e passou depois do reparo.

## Reparos efetivamente aplicados

- `inbound.ts`: `position.array_kind` obrigatório (`messages` ou `statuses`) nos eventos produzidos. Falhas de parse continuam sem exibir conteúdo. Captura **cópia** dos bytes brutos dentro do limite contratado antes da primeira operação assíncrona e usa-a tanto no `crypto.subtle.verify` quanto no `JSON.parse`. Erros de configuração seguem sem refletir segredos.
- `durable-receipt.ts`: `outcome` precisa ser **string primitiva**; contadores não podem exceder `total` antes da soma. **Isto não autentica o recibo nem comprova commit**.
- `technical-reconciliation.ts`: vínculo simulado agora conserva `correlation_id`; pedidos `ALREADY_LINKED` exigem coincidência de correlação, tentativa, intenção, destinatário e escopo. `projectionFor` exige também a intenção originalmente vinculada. Correções anteriores de loja/canal preservadas.
- Atualizadas as fixtures `inbound.test.ts`, `technical-keys.test.ts` e `technical-reconciliation.test.ts` para a nova posição com `array_kind`. O contrato de eventos é candidato [P], sem invocadores operacionais.
- Novos testes versionados: `preaudit-gaps.test.ts` (8) e `wa01-audit.test.ts` (7). Os ensaios WA-01C confirmam `safe_to_auto_dedupe=false`; GET rejeita app divergente, parâmetros duplicados ou challenge impróprio.

## Execução real e correspondência Git

No Node **v22.16.0**, a suíte `graph-outbound.test.ts`, `graph-template.test.ts`, `offline-dispatch.test.ts`, `technical-reconciliation.test.ts`, `scope-isolation.test.ts`, `cross-contract.test.ts`, `preaudit-gaps.test.ts` e `wa01-audit.test.ts` resultou em **120/120 PASS**: 105 regressões preexistentes e 15 testes adicionais.

`tsc --noEmit --strict` nos **oito módulos de implementação** (`inbound`, `durable-receipt`, `technical-keys`, `verify-get`, `graph-outbound`, `graph-template`, `offline-dispatch`, `technical-reconciliation`) → **PASS**.

Os hashes Git dos arquivos de implementação reparados foram comparados com os arquivos locais testados: `inbound.ts` **`dce2346f196c79c61a9dfd14347ff8d2f71f4bff`**, `durable-receipt.ts` **`80e91339fff186832c33c008377db15764841612`** e `technical-reconciliation.ts` **`d85ee320b71b1a38a6f00b6014febcde89ddbd80`**. Novos testes Git: `preaudit-gaps.test.ts` `71ebf9078afa2db7eb31c855db01be1c5288d66a`, `wa01-audit.test.ts` `e010b4a0eb9f040282612e23ed1dc96b429a69ae`.

**Limitação importante:** os 120 casos constituem a suíte combinada reexecutada, **não** totalizam todos os arquivos `*.test.ts` existentes: os arquivos legados individuais `inbound.test.ts`, `durable-receipt.test.ts`, `technical-keys.test.ts` e `verify-get.test.ts` tiveram código/fixtures revisados, mas **não foram executados nesta rodada**. Arquivos `*.test.ts` não passaram typecheck completo por indisponibilidade local de `@types/node`. **Nenhum CI Actions** foi acionado nesta auditoria. Não há evidência de testes reais com Meta, Supabase hospedado ou prova transacional de ACK.

## Limites e decisão

**GO para desenvolvimento adicional apenas sintético** e revisão conjunta dos novos contratos. **NO-GO para integração operacional.** Esta auditoria não implementa autorização S0, prova de commit, cofre de payload, worker privilegiado, retenção LGPD ou confiabilidade externa. `position.array_kind` e demais novas interfaces devem ser considerados em qualquer desenho futuro de ocorrência do C07; posição dentro do mesmo POST não substitui `ingestion_batch_ref` nem `occurrence_ref` gerados pelo serviço durável.

DEC-WA-04/06 continuam pendentes. DEC-WA-05 aprova **titularidade App/WABA/emissor por concessionária**, não onboarding ou envio. A POC concessionária de demonstração e os canais comerciais permanecem intocados.
