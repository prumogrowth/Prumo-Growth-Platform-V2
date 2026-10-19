# WA-10 — unicidade inversa tentativa S0 ↔ wamid na conciliação técnica

**Data:** 19/10/2026. **Situação:** implementação de desenvolvimento no PR #2 Draft. Sem API externa, credenciais, ambiente real, mensagens, merge ou deploy.

## Necessidade encontrada

O conciliador de status offline `FakeMetaStatusReconciler` já recusava a **mesma combinação App/WABA/emissor/wamid** reatribuída a outra intenção/tentativa. Porém faltava o sentido inverso: uma **mesma tentativa técnica S0** poderia ser vinculada silenciosamente a **dois wamids diferentes**, desde que ambos fossem novos. Se futuramente o transporte apresentasse observações conflitantes ou o mesmo envio parecesse gerar respostas divergentes, a simulação criaria duas associações para a mesma tentativa.

**Regra técnica modelada:** uma `attempt_id`, dentro da identidade de App/concessionária, pode apontar para **uma única tupla completa** de escopo, intenção, correlação, destinatário autorizado e `provider_message_id`. A repetição exata é idempotente; uma divergência retorna `CONFLICT`. Uma nova tentativa, com ID diferente, pode ter outro wamid; lojas/Apps distintos são isolados. A regra vale para *observações técnicas já aceitas*, e **não** autoriza reenvio, deduz comercial `sent`, cria ACK ou garante que a Meta nunca produza IDs incomuns. Antes de adotar como regra de produção, confirmar requisitos e comportamento real do provedor.

## Código entregue

- `integrations/whatsapp-meta/attempt-binding.ts`: `FakeAttemptBindingLedger` em memória, com índice inverso por `[app_ref,concessionaria_id,attempt_id]`. Retorna somente `NEW/SAME/CONFLICT/INVALID`; guarda a tupla completa sem expor PII em resultado. Valida string, formato e limite para todos os 10 campos; rejeita getters, propriedades extras, símbolos e entradas não estruturadas. Limite artificial de 100 vínculos no laboratório. Não tem banco, rede, token nem persistência.
- `integrations/whatsapp-meta/technical-reconciliation.ts`: `registerAcceptedSend` consulta o ledger **depois** do aceite Graph coerente, da busca por wamid já existente e de validar o escopo, mas **antes** de adicionar o envio técnico. Se a tentativa já tiver outra associação, retorna `CONFLICT` e não aumenta a contagem. O teste de idempotência por wamid existente permanece.
- `integrations/whatsapp-meta/attempt-binding.test.ts`: WA10-01..11; `technical-reconciliation.test.ts`: REC-36..39, para o novo caminho integrado. `run-offline-tests.sh --binding` executa a nova suíte isolada; `--focus` a inclui, e `--all` exige agora 27 suítes, incluindo `attempt-binding.test.ts`.

## Execução e auditoria nesta etapa

**WA10-01..11: 11/11 PASS**, realmente executados em **Node v22.16.0** com `--experimental-strip-types --test`. `tsc --strict --noEmit --skipLibCheck --target ES2022 --module NodeNext --moduleResolution NodeNext attempt-binding.ts`: **PASS**.

Auditoria durante implementação encontrou coerção implícita do `RegExp.test`, que aceita entrada numérica convertida em texto. Foi corrigido `typeof ... === 'string'` para **todos os 10 campos** e adicionado WA10-11. Verificados os hashes Git dos arquivos testados:
- Biblioteca `e50c98da1ba090ffc7bee6c68f515c4595a7da88`;
- Testes `1132bc1a509d4a42cdb2e703fb0047d7281e1a6b`.

**Executor Git SHA `65657cc248d1e99277dd86d115a6a9fac9d651d7`**: cópia idêntica (`git hash-object`), `bash -n` PASS, `--binding` **11/11 PASS**, `--all` em checkout parcial **exit 66**, corretamente rejeitando ausência das 27 suítes.

**LIMITAÇÃO IMPORTANTE:** `REC-36..39` foram adicionados e conferidos estaticamente, mas **não executados** juntamente com `technical-reconciliation.ts` nesta sessão: checkout privado completo indisponível no ambiente local. Não afirmar que REC-01..39, `--focus` ou `--all` passaram. O código novo da integração exige esse gate. PostgreSQL WA-06D (0/20 na evidência conhecida) e S0-040 (0/5) continuam pendentes; nenhum teste SQL desta alteração foi executado.

## Fronteiras

- A API da Meta e as credenciais reais permanecem **adiadas para integração final autorizada**, sem bloquear desenvolvimento.
- O fato de um evento ser `API_ACCEPTED` **não comprova `sent`**; não deve alimentar relógios comerciais, C09, opt-out, `vendido` ou `perdido` sem provas S0.
- A futura S0 deve preservar, em banco, um vínculo transacional e unicidade equivalente com **autenticação de serviço, escopo, revogações, idempotência e COMMIT comprovado**; este ledger fake **não** substitui a implementação.
- Mantidos separados Prumo (plataforma) e LiberaCred (produta instituição financeira). Sem alterações financeiras, produção, concessionária de demonstração, hosted, API Meta/Graph, OpenAI ou Banco.

**Próximo gate técnico:** checkout completo → executar `--focus` e `--all` → PG17 local descartável → integração real Meta↔S0 interna; nenhuma dessas etapas requer conectar API externa real.
