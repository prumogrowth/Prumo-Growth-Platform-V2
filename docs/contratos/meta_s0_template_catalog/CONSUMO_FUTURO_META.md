# Handoff objetivo para Meta e Codex principal

**META-S0-TEMPLATE-CATALOG-05 / 0.1-candidate. Não ratificado.**

## O que aproveitar agora

1. Manter graph-template.ts e graph-template-interactive.ts inalterados. A interface nova emite suas formas atuais; o literal offline.v1 de quick replies não é renomeado unilateralmente.
2. Usar contract.ts e os testes fictícios para discutir a entrada completa: escopo de cinco campos, binding/catalog/template/content/mapping revisions, provider ID, componentes Meta e política S0 de payloads.
3. Consultar source-manifest.json e a evidência no SHA executável. São 13 fontes originais sem alteração; testes novos não duplicam WA39–68, reserva, M2M ou lock.

## O que falta antes do consumo operacional

- **T1/T2/T3:** serviço S0 autenticado deve resolver binding e catálogo existente, comprovar status+manifesto atual por identidade Meta exata e atribuir revisões locais persistidas. Hoje esse serviço não está implementado; readProductionTemplateCatalog retorna SOURCE_NOT_IMPLEMENTED.
- **T4:** catálogo administrativo deve fornecer os payloads opacos versionados. A Meta aprova estrutura/labels, não a semântica desses payloads internos. Não usar texto do usuário ou payload dinâmico até contrato separado.
- **T5/T6:** invalidar ao pausar/rejeitar/alterar fonte e revalidar junto aos controles ratificados de reserva/dispatch S0/S1. Clock/TTL e watermarks persistidos precisam de contrato e prova física.

Não substituir a fonte ausente por catalogo_templates_sinteticos.aprovado_simulacao, strings APPROVED de JSON, hash F02, recibo de criação, preview MCP ou fixtures deste PR. Não usar identidade GoTrue humana no lugar da autenticação técnica a definir. O PR #18 continua PENDING_EVIDENCE para template/política; esta candidata não o ratifica.

## Sequência futura, sob responsabilidade S0

1. Backend resolve escopo por identidade e binding vivo, sem aceitar a concessionária/phone escolhidos pelo cliente como prova.
2. Catálogo entrega um único snapshot completo atual ou nega. Sem fallback de língua, revisão antiga, base TEXT sem os botões ou componente desconhecido descartado.
3. Verificar versão do contrato, status, recibo de fonte, integridade, revisões e idade. Snapshot é interno; o handle WeakMap de teste não atravessa processos e não é bearer.
4. Projeção TEXT e manifesto QUICK_REPLY devem vir desse mesmo snapshot. Validar os parâmetros usando os builders existentes, com intenção e valores obtidos pelo backend autorizado.
5. Manter o descriptor inerte. Finalidade/grants, consentimento, opt-out, janela, direitos S0/S1 e reserva/begin de tentativa são decisões independentes; template aprovado não permite pular nenhum deles.
6. Frente Meta poderá consumir a interface **depois da ratificação e implementação do adapter real**, sem importar a fonte fixture para runtime operacional.

## Uso exclusivamente no laboratório atual

~~~ts
const result = await fixtureReader.read(query);
if (result.decision !== 'LAB_CATALOG_VALIDATED') {
  // Interromper a preparação; motivo sanitizado disponível.
} else {
  const candidate = await fixtureReader.prepare(result, syntheticIntent, 'v24.0');
  // LAB_INERT_DESCRIPTOR continua sem envio/autorização; não realizar POST.
}
~~~

query pede nome/idioma e revisões esperadas. O host fictício fornece escopo separado, registro de fontes de variáveis, fonte de catálogo e maxAgeMs. Os exemplos em fixtures.ts são inventados; nenhuma conta, template ou aprovação Meta foi consultada.

## Avaliação do Codex principal

- Conferir diff aditivo contra PR #15, preservando as outras branches.
- Examinar as negativas, principalmente manifesto parcial, pausa após emissão, regressão de geração e policy revision reusada com payload divergente.
- Ratificar ou devolver T1–T6 com dono/fonte concreta. Não chamar o sucesso do CI de homologação Meta ou persistência distribuída.
- Manter DISPATCH-01/02, ACK-03, LOCK-04 e C1–C7 nos respectivos contratos. Nenhuma migration/endpoint deve ser gerada automaticamente a partir desse protótipo.

**Esta entrega não executa integração final, merge ou deploy.**
