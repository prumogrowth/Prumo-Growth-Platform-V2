# WA-02D — conciliação técnica sintética de callbacks Meta | 18/10/2026

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Estado [P]: código de laboratório apenas.** PR #2 permanece Draft; não existe webhook novo, Worker C07, banco hospedado, inbox durável real, ACK HTTP, Graph API real, secrets ou envios. Esta entrega não autoriza mensagens nem modifica o C07 comercial do PR #1.

## 1. Contexto e contratos

A coleção oficial da Meta (WhatsApp Cloud API) utiliza `statuses[].id` como identificador da mensagem de saída, com eventos `sent`, `delivered`, `read`, `failed` e timestamps; **esse ID não identifica exclusivamente cada callback**. O contrato compartilhado v0.1 determina que callbacks tardios/repetidos e não correlacionados não podem gerar efeitos comerciais nem perdas silenciosas. Referências:

- [Meta — WhatsApp Cloud API, exemplos de callbacks](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api)
- [Interface compartilhada S0 ↔ Meta/Supabase](interface-compartilhada-s0-meta-v0_1.md)
- [Semântica dos IDs técnicos — WA-01C](wa01c-ids-eventos-meta-e-correlacao-v0_1.md)

## 2. Implementação isolada

`integrations/whatsapp-meta/technical-reconciliation.ts` exporta `FakeMetaStatusReconciler`. É uma fixture **em memória** com APIs de ensaio:

- `registerAcceptedSend(reference, outcome)`: somente simula vincular um envio cujo resultado técnico já seja `API_ACCEPTED` com `wamid`. O escopo exige `app_ref`, WABA, Phone Number ID, referência de concessionária/canal e destinatário confirmado. Mesmo `wamid` sob App/WABA/Phone distintos não causa mistura entre lojas. Registros incompatíveis com o mesmo identificador/escopo sinalizam `CONFLICT`, sem sobrescrever a intenção.
- `observeAuthenticatedFixture(callback, trustedAppRef)`: aceita o formato técnico de `MetaIngressEvent` WA-01A e **pressupõe** que o POST já foi autenticado via HMAC com segredo do App selecionado por roteamento confiável e já duravelmente aceito pelo serviço S0. A classe **não efetua essas verificações**, não emite ACK e não torna evento real confiável por ter sido chamada.
- Projeta somente a progressão **técnica** `NONE → SENT → DELIVERED → READ`. A chegada fora de ordem não reduz a projeção. `failed` é observação técnica separada (`failure_observed`), não "perdido" comercial e não desfaz `read`.
- Repetições idênticas de status + timestamp são **preservadas** como observações adicionais com `possible_repeat=true`, não descartadas pela suposição de ID universal de callback. A deduplicação operacional permanece no backend, após persistência e política.
- Callback anterior ao registro do envio ou sem correlação exata permanece `PENDING_RECONCILIATION` em memória. Jamais vinculamos destinatário com regras automáticas de números BR 8↔9. Mesmo ID em concessionárias distintas continua isolado. Status desconhecido não é automaticamente interpretado.
- Simulação limitada a **100 links**, **100 observações por mensagem** e **100 pendências**. Excesso resulta `CAPACITY_REACHED`, não descarte silencioso com falso sucesso. Esses limites são artificiais, **não quotas nem retenção de produção**.
- Os resultados retornam somente códigos, contagens e estados técnicos. Não expõem token, texto, telefone, tenant, corpo Meta, nem `commit_state` de banco. O armazenamento privado da própria fixture é **temporário e não protegido para dados reais**.

## 3. Evidências verificadas

Ambiente local Node.js **22.16.0**, TypeScript **5.8.3**:

- `node --experimental-strip-types --test integrations/whatsapp-meta/technical-reconciliation.test.ts` → **24/24 PASS** (REC-01..24).
- Regressão em conjunto com WA-02A, WA-02B e WA-02C → **88/88 PASS**, sendo 17 WA-OUT, 24 WA-TPL, 23 SIM e 24 REC.
- `tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck technical-reconciliation.ts` → **PASS**. Para typecheck local da importação `inbound.ts`, foi usado um **espelho somente de tipos** da interface exportada pelo PR #2, e os módulos `graph-outbound.ts` e `graph-template.ts` idênticos aos blobs Git do PR. Isso não constitui build completo da branch.
- Hashes Git locais comprovadamente iguais aos arquivos versionados:
  - `technical-reconciliation.ts`: `5eb563397c3fd9c53ad0bb313d16a8c874c48db9`
  - `technical-reconciliation.test.ts`: `98b1ca439eaadb744dda5e50f3c3a139bfe49948`
- **Não executado:** CI Github Actions, testagem com callbacks reais Meta, Auth/REST Supabase, schema, worker, persistência/recovery nem typecheck integral dos arquivos de teste Node.

## 4. Dependências e próximos limites

A S0 continua dona de C07 comercial, ligações confiáveis App/WABA/canal/loja (incluindo vigência e revogação), inbox durável, dedupe com conteúdo íntegro, callbacks sem `event.id`, transação, observabilidade, retenção, quarentena e autorização. Um callback autenticado sem envio conhecido precisa permanecer recuperável **em persistência do núcleo**, não em Map da fixture. Envio `UNCERTAIN_EXTERNAL` sem `wamid` não pode ser presumido entregue nem correlacionado por telefone.

**GO apenas para auditoria e evolução de testes sintéticos da interface. NO-GO** para consumir webhook real com esta classe, afirmar status persistido, liberar Graph, conectar Supabase remoto, migrar banco, substituir POC concessionária de demonstração, alterar números, mesclar PRs ou contratar recursos. DEC-WA-04 e DEC-WA-06 pendentes; DEC-WA-05 aprova titularidade por concessionária, não implantação.
