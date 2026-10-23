# WA-37 — Contrato de aceite interfrentes: provas mínimas para uma futura porta Meta → S0

**23/10/2026 · [PR #2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2) · Frente WhatsApp/Meta da plataforma operada pela Prumo.** O nome comercial da plataforma ainda não está definido; **LiberaCred é o produto da instituição financeira**, não a marca da aplicação. Esta é uma especificação **de proposta e revisão**, não uma decisão assinada por S0/S1/Infra, migration ou implementação de webhook Meta produtivo.

## 1. Estado do contrato e fronteira de confiança

A [WA-36](./wa36-matriz-ratificacao-interfrentes-e-privilegios-minimos-2026-10-23.md) mapeou 12 temas sem aceite externo. WA37 oferece para cada um **um critério mensurável, uma prova positiva exigida e uma prova negativa exigida**. Os códigos WA37-Pxx/Nxx são **identificadores de cenários a serem ratificados e executados por seus respectivos donos**; **não** são testes de aceitação do sistema de produção já realizados. São diferentes dos **27 testes Node de integridade/negação do pacote de revisão** implementados nesta WA37.

As fontes de contexto permanecem independentes e **Draft**: [S0 PR #1](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/1) (fundação), [S1 PR #5](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/5) (equipe/papéis), [S0 CFI01 PR #12](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/12) (conclusão humana autenticada). O CFI01 apresenta um fluxo humano específico, com GoTrue/HMAC, recibo e bloqueios. **Proibido extrapolar esse fluxo para um principal Meta de máquina ou para um serviço de envio.** Não existe comprovação de que o serviço Meta pode acessar legitimamente um caso S0. A escrita WA33/34 continua uma fixture PG17 sob superusuário, sem principal S0 validado.

### Contrato proposto da chamada interna (ainda não API)

A origem seria um **ingressor Meta controlado pelo backend**. O servidor seleciona App/segredo pela rota confiável, verifica HMAC-SHA256 dos **bytes originais**, identifica exclusivamente um callback de status e resolve um binding persistente na S0. Um envelope assinado **separadamente** para a S0 traria finalidade fixa `FORENSIC_APPEND_ONLY`, identidade de emissor e audiência de serviço, `app_ref`, concessionária, canal, WABA, número remetente, `wamid`, destinatário, caso, tentativa, revisão de binding, evento/tipo de status, hash do corpo, nonce, emissão e expiração. A S0, **não a IA/n8n/frontend**, validaria credencial e assinatura do emissor, tenant, revisão/consentimento, nonce e evento no **mesmo caminho transacional** com ordem de locks ratificada pela S1. O esquema exato, a forma do principal, assinatura, digest/event ID, HTTP e erro **não estão homologados**.

O resultado proposto da escrita é **técnico e mínimo**: `RECORDED`, `EXACT_REPLAY`, `CONFLICT_QUARANTINED`, `DENIED`, `STALE` ou `UNAVAILABLE`, **sem entregar identidade do consumidor em uma resposta pública**. Esses nomes são **propostas**, não enum de produção. Nenhum resultado é autorização Graph, reenvio, mudança comercial, prova de entrega ou incremento de falha definitiva. O papel humano **Diretor/Gestor/Consultor** não é credencial de serviço.

## 2. Matriz operacional de critérios para homologação — 12 decisões ainda pendentes

Cada par P/N define o que seria uma evidência aceitável **se S0/S1/Infra ratificarem o desenho e executarem a prova em sandbox apropriado**. Passes WA27–36 não substituem essas provas por analogia.

| Código WA36 / responsável proposto | Critério de aceite proposto | Prova positiva necessária | Prova negativa necessária |
|---|---|---|---|
| **WA36-M2M-IDENTITY** / S0+Infra | Principal máquina identificado, limitado à porta S0 e revogável, separado de GoTrue humano | **WA37-P01**: serviço autenticado, atributo de audiência e escopo auditáveis | **WA37-N01**: JWT humano/sem credencial/emissor falso sem gravação |
| **WA36-META-PROVENANCE** / Meta+S0 | Route/App Secret selecionadas em backend; assinatura sobre bytes recebidos antes de qualquer binding | **WA37-P02**: callback HMAC válido correlacionado à rota e ao hash bruto | **WA37-N02**: body adulterado, rota controlada por cliente e App errada rejeitados |
| **WA36-KEY-SEPARATION** / Meta+Infra | Chave Meta distinta da chave interna, guarda/rotação/expiração expressas | **WA37-P03**: rotacionar ambas mantendo isolamento e trilha de auditoria | **WA37-N03**: segredo vazado/revogado não permite criar prova de S0 |
| **WA36-SCOPE-BINDING** / S0+S1 | Binding persistente App/WABA/remetente/destinatário/concessionária/caso/tentativa/revisão | **WA37-P04**: correspondência exata no receptor S0 sob revisão atual | **WA37-N04**: cross-tenant, destinatário diferente, binding obsoleto bloqueados |
| **WA36-MACHINE-ROLE** / S0+S1 | Permissão técnica apenas `FORENSIC_APPEND_ONLY` e sem herança de papéis humanos | **WA37-P05**: permissão mínima autoriza somente operação forense prevista | **WA37-N05**: Diretor/Gestor/Consultor, IA ou webhook cliente não recebem a permissão |
| **WA36-NONCE-ATOMICITY** / S0 | Verificação da assinatura interna + nonce único + gravação atômica em fronteira confiável | **WA37-P06**: registro e nonce confirmados numa única transação | **WA37-N06**: replay concorrente, rollback, assinatura falsa ou expirada não duplicam |
| **WA36-LOCK-ORDER** / S0+S1 | Ordem de locks do serviço conciliada com atualizações/revogação S1; sem deadlock | **WA37-P07**: rechecagem de concessão/caso/tentativa em transação concorrente | **WA37-N07**: revogação e transferência concorrentes não criam estado comercial incorreto |
| **WA36-RLS-MIN-PRIVILEGE** / S0+S1 | RLS e grants reais por tenant, sem escrita direta pelo ingressor ou usuário | **WA37-P08**: operação com privilégio mínimo no sandbox S0 | **WA37-N08**: acesso a outra loja, tabela base, SECURITY DEFINER indevido e BYPASSRLS negados |
| **WA36-CALLBACK-DEDUPE** / Meta+S0 | Identidade e taxonomia de evento estáveis, com múltiplas observações por `wamid` | **WA37-P09**: ingestão idempotente para duplicatas definidas e ordem não determinística | **WA37-N09**: conflito, status tardio e colisão de hash sintético não causam supressão indevida |
| **WA36-ACK-RETRY** / Meta+S0+Infra | Política versionada de HTTP ACK e redelivery de inbound independente de Graph resend | **WA37-P10**: ACK ocorre no ponto de durabilidade ratificado | **WA37-N10**: falha/commit incerto não dispara POST Graph ou ACK prematuro |
| **WA36-RETENTION-LGPD** / S0+Jurídico | Prazo, finalidade, minimização, exclusão, logs e auditoria definidos formalmente | **WA37-P11**: registro mínimo, consulta auditada e expurgo testados | **WA37-N11**: token, corpo bruto, PII desnecessária e histórico de outra loja não vazam |
| **WA36-REVOCATION** / S0+S1+Meta | Evidência técnica tardia pode sobreviver à revogação **sem reabrir autorização** | **WA37-P12**: revogação e arquivo técnico no mesmo modelo concorrente | **WA37-N12**: opt-out anterior/durante/após callback não gera envio, retry ou transição |

**Significado de “positivo” e “negativo”:** uma prova P/N deve ser feita em ambiente autorizado pelo dono, com referência imutável à versão do contrato, cenário, artefato executado, resultado e limites. Documento de laboratório ou PR Draft é somente **fonte de hipótese**. O responsável titular precisará registrar aceite explícito; assinatura e autoridade não podem ser fabricadas pelo artefato da frente Meta.

## 3. Pacote executável desta frente (sem aprovações)

`integrations/whatsapp-meta/wa37-acceptance-handoff.ts` define os 12 pares de testes em `WA37_CHECKS`, exige que cada item seja rastreável exatamente ao `id` e ao responsável proposto da `WA36_REQUIREMENTS` e expõe `createWa37PendingReviewPacket()` e `evaluateWa37ReviewPacket(raw)`. A entrada é estrita:

- `contract: "wa37.crossfront.acceptance.offline.v1"`;
- `purpose: "HANDOFF_REVIEW_ONLY"`;
- `entries`: 12 registros exatos com `id`, `requested_owner`, `positive_probe`, `negative_probe`, `evidence_state` (`NOT_PROVIDED`, `LAB_FIXTURE_ONLY` ou `OTHER_FRONT_DRAFT`) e `ratification: "AWAITING_OWNER_DECISION"`.

A saída de um pacote estruturalmente válido é **`LAB_REVIEW_BLOCKED` com 12 decisões externas necessárias**, nunca `APPROVED`; a de um pacote inválido é `INVALID_REVIEW_PACKET`. Ambas impõem `service_authenticated=false`, `s0_write_authorized=false`, `production_authorized=false`, `ack_allowed=false`, `send_authorized=false`, `retry_external=false`, `case_transition_authorized=false` e `delivery_confirmed=false`. Nada retorna token, telefone, assinatura, ticket nem referência de cliente.

`wa37-acceptance-handoff.test.ts` fornece **27 testes Node**, incluindo as 12 obrigações e seus 24 IDs P/N, integridade de proprietário, falta/repetição de critério, finalidade alterada, falso GoTrue/role humano, alegação de aceite, campos extras, getters/proxies, símbolos ocultos e sincronização **com este documento Markdown**. **São testes do pacote de revisão e não as 24 provas P/N externas.**

O estado `LAB_FIXTURE_ONLY` não representa aceite; um pacote com todas as linhas preenchidas continua **bloqueado**. Não existe API para promover o resultado por conta própria.

## 4. Condições para eventual retomada de implementação real

Antes de sugerir migração ou implantação, receber dos donos do contrato:

1. Decisão documentada e versionada para os 12 itens, incluindo *owner* explícito e responsável pela segurança do principal de máquina;
2. Semântica S0 de binding durável, revisão, nonce, status, chamadas e condições de ACK; política de deduplicação para eventos Meta que não fornecem identificador único de callback;
3. Plano de testes S0/S1 reais, sem confiar no superusuário PG17, cobrindo isolamento, grants, RLS, concorrência/lock, reenvio indevido e retenção;
4. Prova de segurança em sandbox próprio e revisão de prontidão, incluindo segredos reais geridos por Infra, **sem incluir seus valores nos documentos**;
5. Decisão explícita de mudança de estado de PR, merge e deploy pelos responsáveis apropriados — **não decorrência automática** de passes dos testes.

**Estado final do contrato WA37:** somente solicitação de revisão; nenhuma ratificação/implantação foi solicitada automaticamente, nenhum teste externo P/N foi executado, não houve chamada Meta Graph/ACK, publicação de endpoint, segredos, dados de cliente, alteração de branches S0/S1/OpenAI/F02/F03/frontend ou merge de PR. A frente WhatsApp/Meta mantém PR #2 em **Draft**.
