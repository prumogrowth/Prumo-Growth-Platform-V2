# M09 — Onboarding e isolamento de ativos por concessionária: laboratório

**31/10/2026. Estado:** checagens e fixtures de reconciliação de inventário implementadas na frente Meta, **sem ativação real**. [Issue #8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8) é a dependência canônica S0/S1 e recebeu parecer **STATUS: EM_ANALISE** da S0; não é contrato ratificado.

## Premissas de negócio e fontes

- **WDC-02/03:** concessionária possui os seus próprios recursos Meta Business, App, WABA/número e catálogo privado. A Prumo é integradora **por delegação**, não titular desses recursos. A comprovação da propriedade efetiva, permissões, webhooks, identidade e concessões **precisa acontecer nas fontes reais** da Meta e da S0.
- **WA-04A** [`credential-routing.ts`](../../../../integrations/whatsapp-meta/credential-routing.ts): registry tipada sintética com `app_ref`, `route_ref`, `concessionaria_id`, `revision`, validade, `waba_id`, `phone_number_id`, `canal_id` e **nomes de slots**; GET, HMAC POST e Graph utilizam slots distintos. Nenhuma credencial é retornada.
- **WA-04C** [`credential-lifecycle.ts`](../../../../integrations/whatsapp-meta/credential-lifecycle.ts): propostas sintéticas de revogação de App/canal ou rotação, sem escrita nem reativação externa.
- A S0 comentou na [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8) que a matriz PG17 histórica tem grants por canal, rota, revisão e revogação em laboratório; ainda **não identificou/ratificou fonte canônica operacional, mutadores autorizados nem serviço M2M**.
- **Dependências já existentes:** não duplicar a [#2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) (recibo/ACK físico) nem a [#10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10) (consentimento/recheck no envio).

## Implementação Meta neste ciclo

**Código candidato:** [`wa09-asset-onboarding-audit.ts`](../../../../integrations/whatsapp-meta/wa09-asset-onboarding-audit.ts).
**Testes adversariais:** [`wa09-asset-onboarding-audit.test.ts`](../../../../integrations/whatsapp-meta/wa09-asset-onboarding-audit.test.ts).

O verificador puro confronta **três peças diferentes**, cada qual só usada como *fixture*:

1. `registry: TrustedMetaRegistry`, com canais/slots/revisão e validade já definidos no candidato WA-04A;
2. manifesto `wa09-s0-asset-expectation.fixture.v0.1`, contendo a expectativa sintética S0 por App/loja: `business_owner_ref`, `delegated_partner_ref`, `route_ref`, `revision`, WABAs, catálogos e **s0_bindings** (`canal_id` + `waba_id` + `phone_number_id`);
3. manifesto `wa09-meta-assets.fixture.v0.1`, representando alegações simuladas de origem externa sobre a titularidade dos ativos e delegação, com pares WABA/número e catálogo **sem canal_id autoritativo**; a Meta real não pode criar um grant S0 só porque um identificador foi fornecido.

A comparação impede: um negócio ser declarado de outra concessionária; WABA/telefone/catálogo compartilhados entre lojas; uma mesma conta empresarial Meta indicada como proprietária de lojas distintas; App/rota/revisão divergentes; ausência de parceiro delegado; `canal_id` S0 inexistente/trocado; número não listado, canal revogado, registry desatualizada ou vencida; membros extras/faltantes e campos estranhos como `access_token`. Compara conjuntos de números sem depender da ordem, exige chaves próprias e recusa getters/proxies defeituosos.

O retorno positivo se chama explicitamente `LAB_INVENTORY_MATCHED_UNVERIFIED`, **nunca `ONBOARDED`**. Mesmo nesse resultado, permanecem `false`: `provider_ownership_verified`, `delegation_verified`, `s0_principal_verified`, `onboarding_approved`, `production_authorized`, `send_authorized`, `ack_allowed`, `s0_write_authorized`. Retorna apenas contagens, sem número, business owner, slot ou segredo.

**Escopo importante:** a igualdade entre três fixtures inventadas não prova identidade, autorização, autenticidade do Business Manager, validade de templates no provedor, HMAC real, concessão de S0 ou compliance. O código não chama rede/Graph nem autentica M2M.

## Critérios externos restantes para M09

- [ ] **S0/S1** na Issue #8: definir fonte confiável persistida de App/route/WABA/phone/channel/tenant, grant técnico, readback/revisão, mutação/revogação, autenticação e menor privilégio; atualizar contrato a partir da v0.x proposta.
- [ ] **Meta Business/Infra/Proprietário:** comprovar titularidade empresarial e de App/WABA/número por concessionária, acesso delegado real da Prumo, inscrições de webhook e estado das contas; sem presumir que um nome no cadastro é prova.
- [ ] **Meta + S0:** conferir fonte de catálogos privados por loja, estado e aprovação de templates e política de alterações/revogação. Avanço em M13/M16 requer contratos próprios de template.
- [ ] **S0 + Infra:** assegurar revogação instantânea ou regra temporal definida, fonte de tempo confiável, revisão atômica durante uso e registro audível, sem revelar credenciais.
- [ ] **Integração:** E2E em ambiente autorizado com dados de teste reais do fornecedor, revalidação de versão e auditoria dos fluxos de falha. Sem autorização para criar contas nem despachar.

**Decisão:** continuar apenas laboratório M09; nenhuma aprovação real do onboarding, nenhum principal S0, merge, deploy, Graph ou envio WhatsApp foi autorizado. M09 principal permanece `[ ]`.
