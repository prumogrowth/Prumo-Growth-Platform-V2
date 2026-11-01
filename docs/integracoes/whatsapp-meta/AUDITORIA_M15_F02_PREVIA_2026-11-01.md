# Auditoria M15 — prévia F02, isolamento de snapshots e fronteira do fornecedor

**Data:** 01/11/2026. **Escopo:** somente WhatsApp/Meta, `wa15-f02-planner-preview.ts` e suíte própria. Conferidos WA-25/WA-26/M13/M14, a [Issue #7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7), a [Issue #10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10) e a [OFF-04 da frente OpenAI](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/1f8157838c11a7b59456a3b178a8ade21a17b42b/docs/integracoes/openai/OAI_OFF_04_PLANEJAMENTO_F02_CANDIDATO_v0_1.md), publicada em branch isolada com 678/678 testes offline segundo [Issue #7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7#issuecomment-6552774777). A publicação OFF-04 **não** significa integração/aceite S0, identidade confiável ou execução real.

## Parecer

**AUD-M15-01 — deriva entre snapshots durante a cadeia assíncrona (corrigida em laboratório).** A implementação anterior conciliava M13, lia o objeto-raiz M14 com cópia apenas superficial e depois chamava as portas `resolveSelection/readScopedPolicy/readScopedCatalog` da WA-26 com `await`. Posteriormente consultava **a referência original** do ledger na `inspectWa14ConsentOffline`. Uma porta falsa podia alterar consentimentos, supressões, grants ou versão/estado de templates durante a espera, fazendo uma resposta positiva misturar uma política antiga com um estado novo, inclusive sem incrementar revisões.

A implementação auditada:
- Faz cópia profunda **somente de dados próprios** e imutabiliza as fixtures de pedido, M13 host/catalog/provider e M14 ledger antes do primeiro `await`. Recusa getters, símbolos, ciclos, protótipos não suportados, arrays esparsos e abuso de profundidade/itens; não executa `toJSON` ou `toString` de objetos.
- Também captura cópias imutáveis de escopo, política e catálogo devolvidos em cada porta assíncrona WA-26, antes de repassá-los ao seu validador existente. Nem M13 nem M14 usam o ledger mutável do chamador ao validar candidatos.
- Antes de prosseguir e antes da saída positiva, recria e compara as fotografias das fontes originais usando igualdade estrutural profunda. Alterações detectadas — mesmo de finalidade não selecionada — recusam o lote inteiro com `INPUT_CHANGED_DURING_PREVIEW`. Se uma fonte passar a conter getter hostil/array esparso, é recusada sem executar código do getter. Negativas já estruturadas de política/escopo continuam sem dados pessoais.

**Limite explícito:** não é leitura transacional, RLS, revisão confiável, assinatura, cache autenticado, reserva ou garantias de independência. Mudança ABA durante duas comparações e alteração posterior à última verificação ainda são possíveis; a S0 deve oferecer snapshot verdadeiro com CAS/serialização e reserva/recheck no instante de despacho. Nenhuma saída passa a ser autorização.

**AUD-M15-02 — fronteira do fornecedor OpenAI/F02 não explicitada na prévia Meta (corrigida semanticamente).** A `wa15-f02-preview.lab.v0.1` divulga referências reais `template_ref` e `version_ref` para o host comparar candidatos, e nunca foi o payload autorizado diretamente ao fornecedor. O laboratório OpenAI `OAI_OFF_04_PLANEJAMENTO_F02_CANDIDATO_v0_1.md` separa uma entrada **privada** do host S0 da visão do modelo `prumo.openai.f02-plan-provider/0.1-candidate`, que usa **aliases opacos**, evitando revelar IDs de loja/pessoa/caso/requisição e IDs originais de templates. Portanto não existe compatibilidade automática.

A prévia M15 passa a declarar `intended_consumer:'LAB_S0_HOST_STAGING_ONLY'` e `openai_provider_payload_compatible:false`. **A M15 não cria aliases e não invoca OpenAI**; tal transformação e o mapeamento inverso pertencem à fronteira F02/S0, sob ratificação das frentes na #7. O rótulo não implementa barreira de rede nem elimina o dever do host de não entregar a prévia inteira a um modelo.

## Regressões

- **40 testes originais M15-01..40** preservados.
- **20 novos AUD-M15-41..60** testam alterações intermediárias de consentimentos e supressões por finalidade, revogação de grant, deriva de versão de catálogo ou conteúdo Meta, mudança de requisição, App/WABA e escopo/política WA-26 entre `await`, getter injetado e array esparso, múltiplos templates estáveis, não exposição de PII e exclusão explícita da forma provider OFF-04.
- **Resultado esperado:** 60 casos M15 próprios, **1.573 testes Meta offline** no total (base 1.553 + 20). Confirmar pela CI completa e associar SHA funcional exato abaixo antes de declarar homologação de testes. As 18 provas PG17 físicas históricas exercitam **ingresso S0↔Meta, não M15/F02**.

## Dependências pendentes

- [ ] S0/S1 e OpenAI/F02 ratificarem contrato de planejamento, projeção de aliases, mapping privado, janela, finalTemplate e continuidade de plano/cadeia/versão. A entrega Meta atual **não** é `ENTREGUE_PARA_ACEITE` de serviço interfrentes.
- [ ] S0/Infra/Proprietário ratificarem App/WABA/phone/grants, fonte de verdade de template/aprovação real e consentimentos por finalidade com trilha de opt-out, origem autenticada, isolamento de tenant e snapshot versionado [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8).
- [ ] `PRE_DISPATCH` real transacional, autorização/reserva/idempotência/readback e política de incerteza somente na [#10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10), **não** na F02.
- [ ] Auditoria de aceitação end-to-end após contratos. Regressões Meta e OpenAI são provas offline separadas; não somar ou usar como evidência de integração Meta↔S0↔OpenAI.

**Status:** M15-A/B/C corrigidos e auditados **somente offline**; M15-D e marco principal ainda `[ ]`. Todas as flags de autorização, aprovação real e envio permanecem falsas. Nenhum merge, deploy, Graph, API OpenAI, SQL, HTTP ACK, credencial ou envio foi executado.
