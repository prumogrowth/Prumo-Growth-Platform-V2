# WA-06-AUD1 — auditoria pós-contrato WA-07 dos incrementos WA-06A/B/C

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Data:** 18/10/2026. **Estado:** auditoria local concluída quanto ao escopo indicado, **com reparo de código**; o contrato de negócio WA-07 permanece [D-negócio/P-R-V] e a integração real [R]. **Não é homologação de serviço, Meta, Supabase ou produção.**

## 1. Fontes e precedência lidas

- `wa07-contrato-janela-e-templates-cf-op-02-v0_1.md` — **atualização contratual da frente WhatsApp/Meta**, alinhada ao documento transversal [CF-OP-02 v0.2](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/cf-op-02-cadeias-contextuais-20261018/docs/revisoes/CF_OP_02_DIRETRIZ_CADEIAS_JANELA_HUMANA_2026_10_18.md) no PR #7 Draft e [issue #6](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6). A direção de negócio está confirmada; nomes de eventos, prova externa de envio, endpoints, catálogos/consentimento, semântica de cancelamento e dados físicos continuam [P/R/V].
- `interface-compartilhada-s0-meta-v0_1.md`; WA-05C/05D-AUD1; WA-06A, WA-06B e WA-06C; `internal-proof-wire-v1.ts`, seu teste WIRE-01..15, `wa06c_reference.py` e `wa06c-crossruntime.test.ts`.
- DEC-WA-01/02/03/05 e D-ORG-01 mantidas. DEC-WA-04/06 pendentes. A frente S1-002/I1 no PR #5 regula **profissionais humanos da Prumo**; ela **não** define propriedade de App Meta ou identidade de serviço.

## 2. Auditoria de coerência com WA-07

| Verificação | Julgamento | Conduta |
| --- | --- | --- |
| Loja proprietária de App/WABA/número; S0 decide identidade e permissões | **Achado funcional WA6-AUD-01 reparado localmente** | Encoder de WA-06B agora recusa misturar `concessionaria_id` diferentes sob a mesma `app_ref` em um lote |
| Um emissor/canal não pode ser reinterpretado dentro do mesmo lote | **Achado funcional WA6-AUD-02 reparado localmente** | Encoder rejeita mapa conflitante `channel→(WABA,phone)` ou `(WABA,phone)→channel` |
| Mensagem inbound atualiza janela Meta e cancelamento do plano | **Sem regressão; integração não realizada** | WA-06B/C apenas cobrem bytes de ingresso; WA-07 exige novo evento/correlação S0, `provider_timestamp` **mais** `received_at` de confiança e política de relógio [R] |
| Janela Meta = última mensagem do cliente +24h, não template outbound | **Direção preservada, teste WA7-01..03 não executado** | Não inferir nova janela a partir de `sent`, `delivered` ou resposta Graph; S0 computa prazo |
| Template manual, cadeia pós-humana e opt-out | **Não implementados** | S0 autoriza por caso/colaborador e C04; Meta transporta, não escolhe plano/modelo, não empresta autorização do inbound para envio |
| Prova real `sent` do template final e C09 +24h | **Gate externo em aberto** | Nunca tratar HTTP accepted/queued, callback não autenticado ou `UNCERTAIN_EXTERNAL` como envio comprovado; perda C09 só S0 em ciclo elegível pré-banco |
| Callback `statuses[].id` e replays | **Vetores preservados** | Ocorrências repetidas em posições distintas continuam representáveis; SHA-256 de formato não prova origem, nonce, dedupe, armazenamento ou ACK |
| Identidade interna/nonce, persistência protegida, escopos e recibo | **Não atendidos por WA-06** | WA-06A é [P], SVC-01..12 não executados; autenticação real e teste transacional PostgreSQL/S0 ainda necessários |

**Cuidado de interface [R]:** WA-06A propõe `issued_at/expires_at`, enquanto WA-06B utiliza `issued_at_ms/expires_at_ms` em números inteiros. WA-06B **não promoveu** esses nomes a contrato definitivo; S0 deverá fechar nomes, unidade, epoch, política de relógio e regra de interoperabilidade antes de DDL/RPC. `received_at` de captura, confiabilidade do `provider_timestamp` Meta e tempo de negócio não são intercambiáveis por inferência.

## 3. Falhas comprovadas e correção

### WA6-AUD-01 — lote de duas lojas sob a mesma App aceito pelo encoder anterior

Antes do reparo, um teste adversarial montou duas ocorrências com `app_ref=app_a`, `concessionaria_id=loja_a` e `concessionaria_id=loja_b`; o **código WA-06B anterior aceitou e serializou 736 bytes**. Isso contradiz a **consistência** de DEC-WA-05, mesmo que o verdadeiro autorizador S0 ainda precise consultar o registro confiável. Corrigido exigindo **uma única concessionária declarada por lote** no encoder candidato.

### WA6-AUD-02 — o mesmo canal/emissor poderia aparecer com associações incompatíveis

A validação antiga não bloqueava, no próprio lote, o mesmo emissor `(waba_id,phone_number_id)` apontar para `canal_id` diferentes, nem `canal_id` apontar para dois emissores. Corrigido exigindo relação 1:1 **dentro do lote**, conservando a possibilidade de **dois canais distintos na mesma App/loja**. S0 deve **ainda validar** que toda associação está vigente/autorizada no registro autoritativo com bloqueios transacionais; este parser de bytes não substitui essa prova.

**Arquivos do reparo:** `integrations/whatsapp-meta/internal-proof-wire-v1.ts` atualizado, sem alterar domínio, ordem, formato de bytes, versões, `ack_allowed:false` nem campos assinados; regressões permanentes em `internal-proof-wire-audit.test.ts`.

## 4. Evidência desta auditoria, e seus limites

No ambiente descartável de testes: Node.js 22.16.0 e TypeScript 5.8.3.
- **Antes do reparo:** reprodução positiva do lote cruzado `loja_a/loja_b` no encoder anterior (bug reproduzido).
- **Depois do reparo:** **7/7 testes locais PASS** — negativas cruzando lojas, mesmo emissor para canais distintos, mesmo canal para emissores distintos; positivas de dois canais distintos da mesma App/loja e callbacks repetidos; SHA-256 original e **cinco vetores WA-06C sem alterações**.
- `tsc --noEmit --strict` PASS para o encoder e regressões em escopo, com espelho **temporário** do tipo `S0HandoffCandidate` de WA-05C e `@types/node` local. Não foi compilada toda a branch.
- A referência Python independente foi recalculada nesta auditoria: **5/5 tamanhos e hashes coincidentes** com os valores versionados em WA-06C.
- O teste usado foi uma **cópia local de auditoria dos trechos executáveis** do encoder anterior, corrigida com o mesmo patch que foi publicado. O hash de GitHub do **arquivo remoto atualizado e do teste de regressão será conferido separadamente na leitura posterior**; a cópia local possui cabeçalho diferente, portanto não alegar igualdade de hashes byte a byte da cópia com o repositório.
- **Não reexecutados nesta auditoria:** 358 testes históricos WA-05D-AUD1, os 15 casos originais WA-06B como suíte completa, os 8 casos WA-06C originais como suíte completa, SVC-01..12 ou WA7-01..12. Nenhum CI remoto, PostgreSQL integrado, GoTrue/REST, Meta Graph, HMAC de serviço real ou deploy.

## 5. Próximos gates, sem pular dono

1. **S0 [R]:** revisar a validação de escopo e os vetores do WA-06B após reparo; autenticar identidade de serviço fora de JSON; validar autorização App→loja/canal vigente; consumir nonce e persistir bytes originais protegidos, batch, `occurrence_ref`, tarefas e recibo **na mesma transação PostgreSQL descartável**. Sem reaproveitar `trustedCaller()` como identidade real.
2. **Meta/S0/CF-OP-02 [R/V]:** fechar eventos `received_at` versus tempo de provedor, critérios de `sent` confiável, template humano/cadeia IA pós-humana, exclusão por opt-out, prova de envio final, clocks independentes e precedência bancária. WA7-01..12 são **casos propostos, ZERO executados**.
3. **Segurança/custos [R]:** DEC-WA-04 (projeto final), DEC-WA-06 (origem de serviço, chave/nonce/replay, continuidade, retenção, ACK/quarentena), validação de token por terceiro e custo/catálogo Meta.

**Restrições verificáveis:** PR #1/#2/#5/#7 continuam Draft salvo mudança posterior; nenhum merge, webhook `whatsapp-webhook-sandbox` da POC, ambiente Supabase hospedado `projeto-supabase-omitido`, número, conta, Meta real, envio, migration hosted ou plano pago foi modificado neste trabalho. A classificação de engenharia permanece **GO somente para revisão/testes sintéticos**, **NO-GO operacional**.
