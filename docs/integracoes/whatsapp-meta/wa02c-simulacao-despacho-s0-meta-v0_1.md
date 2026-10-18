# WA-02C — Simulação fechada de despacho S0 → Meta | 18/10/2026

**Situação:** incremento de engenharia sintética isolada no PR #2, **sem envio real, Supabase, tokens, `fetch`, segredo, Graph API, fila ou deploy**. Continua valendo a distinção entre implementação de código candidata [P] e aprovação operacional [D/R/V]. Não substitui o webhook sandbox `whatsapp-webhook-sandbox`.

## 1. Contratos reaproveitados

- `graph-outbound.ts` WA-02A: `prepareGraphTextRequest()` para C03 e C12, e `classifyGraphSendResult()` para `API_ACCEPTED`, `PROVIDER_REJECTED`, `UNCERTAIN_EXTERNAL`.
- `graph-template.ts` WA-02B: `prepareGraphTemplateRequest(intent, trustedSnapshot, trustedScope, apiVersion)` para C06 (texto posicional com manifesto completo e escopo consistente).
- `docs/integracoes/whatsapp-meta/interface-compartilhada-s0-meta-v0_1.md`: contrato candidato de autorização, reserva, resultado e tratamento de envio incerto.
- Correções auditadas de 18/10 em `wa02-reparos-pos-auditoria-2026-10-18.md`: 408/425 incertos, `wamid` opaco, escopo/catálogo C06.

## 2. Código introduzido

`integrations/whatsapp-meta/offline-dispatch.ts` define **somente um harness local em memória**:

- `FakeS0Outbox`: armazena fichas fictícias de autorização atual. `upsertCurrent` permite simular revogação, alteração de versão, canal, destinatário, App/WABA, template ou bloqueio **antes da execução**; `reserve` impede que uma mesma intenção passe duas vezes; `record` registra somente resultado técnico sintético.
- `ScriptedFakeGraph`: devolve observações pré-carregadas `http_response` ou `transport_error`. Não chama rede; contabiliza somente quantidade e tipo de requisições observadas, **não retém texto/destinatário**.
- `simulateOfflineDispatch(command, fakeS0, fakeGraph, apiVersion)`: reconsulta a ficha fictícia atual e exige igualdade de intenção, tentativa, correlação, ação, versão, escopo completo e destinatário. Prepara texto C03/C12 ou template C06 pelo módulo específico. Somente então reserva a intenção e consome **uma** observação falsa; classifica o resultado e tenta registrá-lo no fake backend. Duplicata não chama novamente o transporte.
- A falha de conexão, 408, 425, 429, 5xx ou 2xx malformado permanece `UNCERTAIN_EXTERNAL`/sem retry. Falha do registro sintético após observação devolve `RECORD_UNCERTAIN`, mantém a reserva e exige conciliação manual; não executa segundo envio.
- `OfflineDispatchResult` expõe apenas códigos e metadados técnicos sem conteúdo, telefone ou tokens. A existência de `allowed_now=true` **é um dado de fixture**, não evidência de opt-in, permissão, identidade civil, registro do App ou autorização bancária.

**Atenção:** `FakeS0Outbox` não é persistente, não é RLS, não cria transação, não fornece lock distribuído, não suporta recovery real, nem elimina race entre validação de estado e chamada externa. `ScriptedFakeGraph` não é conector de produção; o código não fornece um transporte real injetável. Somente tests podem afirmar que o harness foi executado.

## 3. Testes locais executados e verificação de integridade

Node.js `v22.16.0`:

```bash
node --experimental-strip-types --test \
  integrations/whatsapp-meta/graph-outbound.test.ts \
  integrations/whatsapp-meta/graph-template.test.ts \
  integrations/whatsapp-meta/offline-dispatch.test.ts
```

**64/64 PASS** (17 WA-OUT, 24 WA-TPL, **23 SIM**). `SIM-01..23` cobrem C03/C12/C06, revogação/escopo/versão, template pausado e manifesto inválido, reserva antirrepetição, timeout/4xx/5xx, erro de gravação, ausência de script, dados sensíveis e ausência de recibo de banco.

Compilação dos três módulos em TypeScript `v5.8.3`, `tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck` → **PASS**. Os testes foram **executados**, mas não integralmente typechecked nesta sessão por falta de `@types/node`; não foi acionado CI remoto.

SHA Git confirmado de arquivos publicados versus arquivos executados:
- `offline-dispatch.ts`: `5ca93690bef2afafb82e69a7a44ea332ba72bf46`.
- `offline-dispatch.test.ts`: `503ac1f11eba38720585a393a09cc1060e3d7ae5`.
- `graph-outbound.ts`: `7870a499007ae2ff8c6a5558086554916b092aa7`.
- `graph-template.ts`: `bcb0a1422f3526624cfbfac43bfb9ad79c496518`.

## 4. Dependências para uma etapa posterior (não resolvidas por WA-02C)

A frente principal continua responsável por autorização real C03/C06/C12, verificação de opt-out e elegibilidade, atribuição/handoff, versão de estado vigente, vínculo App/WABA/emissor com vigência, destino confirmado, reserva **transacional e durável** de tentativa, catálogo Meta atualizado e registro/reconciliação de envio incerto. O planejamento de segredos, observabilidade e continuidade é DEC-WA-06; o ambiente definitivo é DEC-WA-04; DEC-WA-05 aprovou **titularidade dos ativos por concessionária**, não onboarding nem autorização de números.

**Próximo incremento candidato:** contrato/testes sintéticos de conciliação de callbacks técnicos com `wamid` e estado incerto, sem mexer em C07 comercial; ou auditoria de portabilidades da simulação. **NO-GO** para real Graph API, port HTTP, Supabase hospedado, migrations, tokens operacionais, webhook da concessionária de demonstração, numbers comerciais, merge ou deploy. Os PRs seguem Draft.
