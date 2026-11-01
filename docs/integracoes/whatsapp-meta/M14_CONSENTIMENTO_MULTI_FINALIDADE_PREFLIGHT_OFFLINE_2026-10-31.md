# M14 — Elegibilidade, consentimento por finalidade e opt-out (offline)

**Data:** 31/10/2026. **Frente:** WhatsApp/Meta. **Estado:** M14-A/B/C em laboratório offline, sem integração nem autoridade. O marco principal M14 e M14-D permanecem abertos.

## Base preexistente

- `template-purpose-eligibility.ts` / WA-25 já seleciona templates/grants por ator, fluxo e campanha, mas não autentica consentimento real.
- `s0-template-purpose-bridge.ts` / WA-26 já revalida, em portas falsas, estado agregado `consent_state`, `opted_out`, autorização de caso, audiência e campanha em fases `PLAN`, `RESERVE` e `PRE_DISPATCH`. Uma decisão positiva nesse laboratório continua `send_authorized=false`; não implementa interface S0 real.
- M13 auditada seleciona forma e versão de template por manifesto sintético, sem autenticar `APPROVED`, source of truth ou sincronização. M14 não substitui nem conecta automaticamente M13 ou WA-26.

## Lacuna e implementação M14-A

O booleano `opted_out` e `consent_state` unitário da WA-26 não representam um **ledger de finalidades múltiplas**, nem permitem validar, separadamente, `template_purpose_ref` versus `consent_purpose_ref`, supressão por concessionária, concessão por campanha e revisões independentes.

Criado `integrations/whatsapp-meta/wa14-purpose-consent-preflight.ts` com:
- `inspectWa14ConsentOffline(request,ledger)` e `recheckWa14ConsentOffline(initialRequest,initialLedger,freshRequest,freshLedger)`.
- Contratos exclusivos de fixture `wa14-request.lab.v0.1` e `wa14-s0-ledger.lab.v0.1`. **Host e S0 são alegações injetadas, não respostas autenticadas.**
- Escopo obrigatório exato: `selection_ref`, `concessionaria_id`, `waba_ref`, `lead_ref`, `case_ref`, `case_version` e `authorization_revision`. Uma loja, WABA, lead, caso ou versão diferentes não herdam permissões.
- Um consentimento explícito por `consent_purpose_ref` com estado `GRANTED`, `DENIED`, `UNKNOWN` ou `REVOKED` e janela de validade. Consentimento de outra finalidade **não** supre a requerida.
- Supressão `active` por finalidade ou `consent_purpose_ref=null` para supressão geral **dentro da loja/lead já escopados**; estado INACTIVE não é opt-out. Dupla definição e campos contraditórios são negados.
- Grant de template/versão/finalidade de template/**finalidade distinta de consentimento**/ator/fluxo/campanha, explicitamente `ACTIVE`, com revisão. Campaign null exige `NOT_APPLICABLE`; campanha presente exige `ELIGIBLE`, além de grant específico.
- Revisões separadas `policy_revision`, `consent_revision`, `suppression_revision`, `grant_revision` e freshness limitado por `max_age_ms<=300000` **apenas para ensaio**. Os itens têm revisão não superior à versão sintética da respectiva fonte.
- Validadores de descritores own-data, arrays densos e limites de tamanho; getters, símbolos, proxies anômalos, duplicatas e campos inesperados negados. Saída não contém identificadores do lead/caso nem qualquer texto/telefone/segredo.
- No recheck, só o instante pode avançar; mudança de identidade, finalidade, versão de autorização, revisão de política/consentimento/grant/supressão ou revogação nega a continuidade da candidatura.

**Não há origem de prova de consentimento, evento de opt-out, identidade M2M, RLS, retenção, transação, gravação ou deduplicação.** Os nomes `LAB_POLICY_COHERENT_UNVERIFIED` e `LAB_RECHECKED_UNVERIFIED` significam apenas consistência estrutural. `consent_verified`, `s0_source_authenticated`, `principal_verified`, `tenant_binding_verified`, `send_authorized`, `production_authorized`, `graph_dispatch_authorized`, `automatic_retry_authorized`, `ack_allowed` e demais flags de autoridade são `false`.

## M14-B: teste adversarial

`integrations/whatsapp-meta/wa14-purpose-consent-preflight.test.ts` contém **50 testes M14-01..50**, cobrindo separação de consentimentos, consentimento revogado/desconhecido/vencido/futuro, supressão por loja e finalidade, grant e template/versão/ator/campanha cruzados, case/audience, tenant/WABA/lead errados, revision stale/future, duplicatas, getters/arrays esparsos, falso campo de autorização, revogação e troca de revisão entre leituras, ausência de idempotência/dispatch.

**Evidência funcional:** SHA `a0d2dff540d800aa78e858855d161703ec8f794a`, [CI 41263817371](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41263817371): 1.497/1.497 Meta offline, incluindo 50 M14; scanner ACK estático lexical aprovado. As 18 verificações físicas PG17 de S0 ingress são ensaio **independente, não autenticam o ledger M14**. Reportar separadamente somente após confirmação final de ambos os jobs.

## M14-C: limitação, integração e contrato pendente

1. O consumidor S0 deverá obter e autenticar a fonte canônica de consentimento/opt-out **por concessionária e finalidade**, com eventos e versões monotônicas, comprovação de origem, revogação e privacidade. Não derivar consentimento do nome da categoria Meta (MARKETING/UTILITY) nem do template `APPROVED`.
2. A S0 deverá manter mapping vigente de template_purpose para consent_purpose **explicitamente autorizado**, grants por finalidade/ator/campanha e principal/loja/caso, e dizer se uma supressão é geral na concessionária ou escopada a finalidade. Sem fonte ratificada, dois objetos `GRANTED` não constituem consentimento legítimo.
3. A rechecagem `PRE_DISPATCH` em transação S0 deve revalidar última versão do lead/caso, escopo, opt-out, janela/purpose/campanha, template e autorização do principal, com readback/reserva de tentativa e tratamento de concorrência/ABA. Timeout ou resultado incerto nunca liberam Graph ou retry automático.
4. Principal responsável: S0/S1/Infra/Proprietário, [Issue canônica #10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10). Dependências de registry/grants [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8) e pedidos F02 [#7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7). **Não abrir Issue duplicada**.

**Conclusão:** conjunto M14-A/B/C offline sob evidência de testes; M14-D e marco principal `[ ]` aguardam contrato, fonte e integração S0 real. Nenhum merge, deploy, Graph, envio, SQL, HTTP ACK, credencial, alteração comercial ou autorização de produção.


## Adendo — auditoria corretiva M14, 31/10/2026

A [auditoria M14](AUDITORIA_M14_CONSENTIMENTO_PREFLIGHT_2026-10-31.md) identificou e corrigiu uma falha de consistência: a primeira versão podia retornar `LAB_RECHECKED_UNVERIFIED` quando outra finalidade, grant ou supressão havia sido modificada **sem alterar as revisões globais**. O recheck agora compara uma representação canônica de todos os registros do ledger, ordenados para não interpretar permutação de listas como mudança. O horário `observed_at_ms` pode avançar, mas ainda é validado por limites de freshness. Revogações explícitas seguem devolvendo `CONSENT_DENIED`, `SUPPRESSED`, `GRANT_DENIED` ou `CASE_OR_AUDIENCE_DENIED`.

Há **66 testes M14** (50 anteriores + 16 AUD-M14-51..66). [CI 41266701159](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41266701159), SHA funcional `640e73f591946970a8a169685c8771a237c2472d`: **1.513/1.513 Meta offline**, 18/18 PG17 históricos em outra frente de ingresso, dois jobs `success` e scanner ACK estático aprovado. Os números de 50/1.497 acima são históricos da primeira implementação.

Este endurecimento **não prova completude da fonte**, não elimina alterações ABA, não oferece lock, transação, autenticação de consentimento, verificação de opt-out real ou autorização `PRE_DISPATCH`; M14-D continua pendente de S0/Infra na Issue #10.
