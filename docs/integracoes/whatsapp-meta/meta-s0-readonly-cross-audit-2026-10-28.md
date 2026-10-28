# AUDITORIA READ-ONLY — S0 × Meta Cloud: contratos, lote, recibo e referência de contexto

**Data de execução:** 28/10/2026. **Alcance:** leitura cruzada do GitHub; testes exclusivamente sintéticos sobre código da frente Meta; nenhuma escrita de S0/S1, nenhuma autorização operacional.

**Base Meta:** PR #43 (`feat/meta-cloud-quoted-context-20261028`), SHA `b14c60d0ef2a2af5e5f67f3e97992aba6bab2494`.

**Fontes S0 consultadas SEM modificações:**

| Fonte | Branch / commit lido | Natureza |
|---|---|---|
| [S0/META-01 a 04, PR #14](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/14) | `aux/meta-s0-contracts-20261026` / `31bb84fa524f4ecfdf02360988471d7f989506d7` | Quatro contratos auxiliares candidatos; C1–C7 sem ratificação |
| [S0/CATALOG-05, PR #19](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/19) | `aux/meta-s0-template-catalog-05-20261026` / `d453a22f7160c4e9ff146d21aebe0c2679c9840a` | Catálogo candidato T1–T6; fonte produtiva não implementada |
| [S0 F02, PR #18](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/18) | `88af4aea3aeb2c403bab4c078fdc04d560f2cba0` | Revisões humanas, evidência pendente; não ratifica Meta |
| [S0/S1 I85, PR #42](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/42) | `840b2db7299d024c03ced2e5120b241a23046a0e` | Bootstrap laboratorial de Diretor, não identidade M2M/Meta |
| [Fixture histórica S0 WA-05C](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/b14c60d0ef2a2af5e5f67f3e97992aba6bab2494/integrations/whatsapp-meta/s0-handoff-contract.ts) | PR #43 base | Handoff técnico candidato, multicanais, sem commit nem ACK |
| [Compositor Meta vigente](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/b14c60d0ef2a2af5e5f67f3e97992aba6bab2494/integrations/whatsapp-meta/cloud-composed-observation-handoff.ts) | PR #43 base | Verificador HMAC de uma rota WABA/phone por chamada, sem S0 |

As fontes são **branches/PRs Draft, não uma integração executada**. Os caminhos atuais da S0 não foram editados, mesclados, reconstruídos ou reexecutados. A revisão diz respeito à **compatibilidade candidata**, não homologa os contratos de produção.

## Achados confirmados e classificação

### A1 — Diferença de granularidade de escopo do lote (CONFIRMADA; decisão conjunta S0/Meta pendente)

A fixture `prepareS0HandoffFixture()` resolve cada ocorrência contra o registro de canais da mesma App e **admite duas WABAs distintas** no mesmo POST, preservando os dois `canal_id`. Já `inspectSignedMetaComposedWebhook()` usa `trustedRoute: {waba_id,phone_number_id,revision}` singular e rejeita integralmente a segunda WABA.

**Prova reproduzível:** `BOUNDARY-03` no teste `meta-s0-readonly-cross-audit.test.ts` verifica, com **o mesmo corpo sintético, mesma assinatura e mesma App confiável**, S0 fixture `ok=true, event_count=2` e Meta compositor `decision=DENIED`. `BOUNDARY-04/05` confirmam que cross-App ou WABA/número fora do registry devem ser rejeitados em ambos.

**Não é prova de falha de segurança da S0.** A divergência é de perfil de ingresso: multicanais por App versus escopo de um canal. Ambos são conservadores dentro das respectivas fronteiras. Nunca dividir silenciosamente um POST físico, responder ACK parcial ou descartar itens não correspondentes.

**Decisão a ratificar:** S0/Meta devem estabelecer se um endpoint/POST pode conter várias WABAs da mesma App; se permitido, definir validação integral contra registry autoritativo e **commit/recibo atômico do POST completo**, mantendo a identidade por WABA/phone/canal em cada item. Se não permitido, definir rejeição integral por contrato e roteamento compatível, sem dedução por conteúdo. A implementação do adapter operacional pertence à fase autorizada, não a este PR.

### A2 — Referência `context.id` não consta do handoff mínimo S0 (VERIFICADO; decisão de política, não bug)

O compositor Meta PR #43 extrai `quoted_reference.quoted_provider_message_id` e `quoted_sender_identifier_untrusted` de um evento assinado, mas **não** associa a uma conversa ou tentativa. A fixture S0 `S0HandoffOccurrence` deliberadamente preserva apenas posição, escopo técnico, IDs e status/tipo; exclui participante, texto e referência de citação.

**Prova:** `BOUNDARY-06` verifica que a citação aparece exclusivamente na observação Meta, não no DTO mínimo S0, e que texto/produto/identidade do contexto não vazam. S0 ACK-03 já propõe armazenamento protegido do corpo bruto por lote, não promoção indiscriminada desse conteúdo ao recibo.

**Ação futura sugerida à S0, apenas se a funcionalidade exigir:** definir finalidades, retenção, controle de acesso e autorização para resolver `context.id` contra mensagem anterior. Pode optar por não expor a referência no DTO mínimo, mantendo processamento separado no domínio S0. Sem decisão, **não correlacionar por telefone/ID bruto nem inventar vínculo ao caso**.

### A3 — Prova de persistência, autoridade e ACK (BLOQUEIO PREEXISTENTE CONFIRMADO)

- A fixture `reviewS0ReceiptFixture()` considera um recibo textual `COMMITTED` como **STRUCTURE_MATCHES_BUT_UNVERIFIED**, nunca autorizando HTTP 200.
- O PR #14 prevê `META-S0-ACK-03`: autenticação Meta HMAC **mais** autenticação M2M independente, lote durável com recibo verificável, nonce/replay e política HTTP ainda pendente. O `CandidateLab` é modelo single-process/fixture; não é gateway operacional de produção.
- O hash `raw_sha256` da Meta pode corresponder a `payload_sha256` da fixture S0, mas SHA de bytes **não prova** commit nem existência de cópia protegida.

**Provas:** `BOUNDARY-02` verifica hash do mesmo corpo nas duas leituras; `BOUNDARY-07/08` verificam recusa de autoridade até diante de recibo forjado/com contagem parcial. `BOUNDARY-14` verifica ausência de prova M2M em ambas.

**Necessidade de alteração pela S0 agora?** Não. A pendência já está expressamente documentada nas decisões C3/C4 do PR #14. É um bloqueio para ativação real, não defeito novo demonstrado.

### A4 — Revisão/identidade/consentimento/catálogo (GATES PREEXISTENTES; sem erro novo confirmado)

- Compositor Meta aceita estrutura HMAC/escopo de um par WABA/phone; **não** contém registry S0 revogável, tenant, autorização por caso/atribuição ou fonte confiada de consentimento. `BOUNDARY-13` demonstra que uma rota revogada na fixture S0 é negada, enquanto a HMAC válida permanece uma observação técnica Meta; isso é correto e intencional.
- S0 PR #14 define que a S0 decide finalidade, destinatário, opt-out, janela, concessões, binding/revisões e gates. PR #19 declara `readProductionTemplateCatalog()` como **SOURCE_NOT_IMPLEMENTED**, sem aprovação de template Meta real. `app/route` e `revision` no ledger não são substituídos por um telefone do corpo assinado.
- A S0 candidata utiliza alguns domínios de revisão decimal int64 como **string**, enquanto leitores históricos Meta usam `revision:number` seguro. A conversão/mapeamento entre revisões distintas não pode ser feita por coerção nem inferência. O PR #14 já registra este limite.

**Destino das pendências:** fontes autoritativas/ratificação S0 (C1–C7, T1–T6) e contrato de transporte Meta/Infra. Nenhum teste aqui prova que o sistema comercial já tenha integrado esses gates.

## Certificação de testes

Nova suíte `integrations/whatsapp-meta/meta-s0-readonly-cross-audit.test.ts`: **14 testes sintéticos** (mesmo corpo e assinatura, multicanais, cross-App, phone mismatch, SHA bruto, contexto, recibo alegado, HMAC incorreto, sibling malformado, duplicatas, status não confundido com inbound, revogação, separação M2M).

Workflow `.github/workflows/meta-s0-readonly-compat-offline.yml`:
- 14 testes de auditoria cruzada novos;
- 24 testes **preexistentes, inalterados** de `s0-handoff-contract.test.ts`;
- 248 regressões focadas **preexistentes, inalteradas** dos leitores e compositor Meta;
- **Total esperado: 286/286**, sem rede e sem CI global S0/PG. A aprovação exige CI SUCCESS no **SHA final exato**.

## Encaminhamento mínimo à S0 — sem interromper a frente

**Ação nova a decidir, caso se prepare a integração operacional:** A1 — qual unidade de escopo do callback Meta é admitida (App multicanais ou uma WABA/phone por POST), com política de commit/ACK integral e roteamento autoritativo. Não houve proposta de SQL ou migração nem tentativa de corrigir essa escolha unilateralmente.

**Decisão opcional condicionada ao produto:** A2 — tratamento privado de referências citadas `context.id`, se a S0 precisar consultá-las. Não obrigatória para manter o transporte técnico sem correlação.

**Bloqueios anteriores já documentados e não reabertos:** A3/A4 — ratificação de contratos, M2M produtivo, recibo/ACK e fonte de catálogo/cadastro/escopo/revisões. Nenhum defeito novo foi confirmado no código da S0 consultado; trata-se de pendências conhecidas e diferença de interface.

**Regra de governança:** esta branch só contém testes, workflow e documentação da frente Meta. Nenhuma escrita nas branches, arquivos, PRs, issues, migrations, credenciais ou bancos pertencentes à S0/S1. Nenhum HTTP ACK, Graph API, envio, download, automação, rede de produção, deploy ou merge.
