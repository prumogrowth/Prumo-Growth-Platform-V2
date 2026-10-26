# E04/F02 — auditoria de consolidação e matriz de aceitação funcional V1

**Corte auditado:** 26/10/2026 · HEAD inicial `e2258df83d9f8483c7e4b9db7a7bf56cefe9a6ff` · CI [#40298163935](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40298163935) **SUCCESS**. Repositório e branch experimental do PR #1 Draft. Nenhum merge, deploy, contato real ou Supabase hospedado autorizado.

**Matriz versionada verificável:** [`docs/contracts/OAI_E04_F02_ACCEPTANCE_MATRIX_V1.json`](contracts/OAI_E04_F02_ACCEPTANCE_MATRIX_V1.json). Contém 18 critérios com provas por **nome exato de teste**, classificação, fronteira de autoridade, pendências e checkpoints de branches relevantes. A contagem **7 LAB_VERIFIED / 8 LAB_PARTIAL / 3 INTEGRATION_PENDING** é um inventário de critérios, **não porcentagem de conclusão** nem cobertura global E02. `LAB_VERIFIED` significa *comportamento específico demonstrado no laboratório*, não aceite para produção.

## 1. Sobreposições auditadas — não remover garantias

| Contrato/módulo | Responsabilidade não intercambiável | Resultado |
|---|---|---|
| `s0_f02_posthuman_compatibility_local.py` e `s0_f02_posthuman_preview_local.py` | O primeiro limita formato/autoridade do resultado S2; o segundo consulta elegibilidade contextual/escopo para prévia sintética. | **Sem deduplicação segura comprovada**: diferentes fronteiras de confiança. |
| `s0_f02_posthuman_intent_local.py` | Intenção sintética de gestor, exclusivamente auditável, não aprovação comercial. | Manter separado da ratificação real S0/S1. |
| `s0_f02_legacy_cancellation_witness_local.py`, `s0_f02_legacy_observed_origin_local.py`, `s0_f02_posthuman_legacy_reconciliation_local.py` | Testemunho local C08, cronologia/origem observada e conciliação independente são **três provas diferentes**. | Não converter cancelamento local em confirmação Meta nem usar campos de horário isolados como prova. |
| `s0_f02_posthuman_draft_local.py` vs. `s0_f02_posthuman_legacy_reconciliation_local.py` | A minuta comum mantém bloqueio em cadeia legada até cancelada; a conciliação fornece somente classificação de revisão. | Divergência **intencional**: não abrir atalho para novo plano. |
| `f02_reconciled_human_authorization_handoff.py` vs. `f02_reconciled_review_lifecycle.py` | O primeiro produz hash SHA-256 de alegações tipadas; o segundo verifica prazo/replay/revogação em histórico **não confiável**. | São etapas complementares, sem assinatura, persistência, mutex ou autoridade. |
| `s0_f03_*_local.py` | Propostas experimentais de integridade, identidade, evidência e reserva; dependem do núcleo S0. | **Codex decide** equivalência, substituição e incorporação; não há limpeza unilateral. |

**Conclusão da auditoria:** não foi demonstrada duplicação que autorize exclusão de adaptador, retirada de gate ou redução de testes. A consolidação segura neste ciclo é **contratual e rastreável**, não fusão de módulos.

## 2. Leitura da matriz e critérios de aceite

- **LAB_VERIFIED:** teste sintético unitário/PG17 verifica o comportamento indicado; nunca prova origem de evidência, autorização de envio ou prontidão operacional.
- **LAB_PARTIAL:** existe teste específico, mas persiste dependência de fonte autoritativa, S1, Meta, concorrência ou integração.
- **INTEGRATION_PENDING:** sem prova adequada ponta a ponta, ratificação S0/S1 ou infraestrutura real; teste não inventado.
- **Condição de pronto experimental F02:** todos os critérios em escopo da branch com referências de teste válidas, regressões CI verdes, bloqueios não enfraquecidos, interfaces versionadas e pacote entregue à revisão Codex. Nenhum desses itens libera produção.
- **Condição de pronto para integração (futura):** Codex ratifica contrato S0/F03 e autorização humana; S1 ratifica papel/escopo; S2 tem handshake versionado; F01 fecha/handoff corretamente; opt-out, template Meta e cancelamento externo são rechecados; idempotência transacional, concorrência, revogação e auditabilidade são testadas na branch específica de integração; oráculos E02 originais são reexecutados. Exige autorização explícita.
- **Critério inequívoco de não pronto:** ausência de S0 recheck, comprovação externa da tentativa reservada, consentimento vigente, autorização humana assinada, ledger durável ou agendador isolado. `READY_FOR_S0_RECHECK_ONLY`, `HANDOFF_REVIEW_ONLY`, `LOCAL_LEGACY_EVIDENCE_REVIEW_ONLY` e `UNTRUSTED_EXACT_REPLAY_REVIEW_ONLY` **nunca** autorizam agendar, reservar nem enviar.

## 3. Interfaces a negociar com o Codex/S0

| Provedor | Insumo esperado pela F02 | Gate antes de incorporar |
|---|---|---|
| S0/F03 + F01 | Fechamento humano, sessão/principal, escopo `shop/lead/case/closure`, cutoff do histórico e recibo autenticado | Verificar prova na fonte S0 e ordem do handoff F01; nenhuma alegação arbitrária de `ClaimedS0Evidence` é suficiente. |
| S1 | Gestor ativo, vínculo e escopo, ato de ratificação | Revalidação S0/S1 no instante da decisão e antes de eventual envio. |
| S2 | Proposta com schema e versão fixados, sem flags de execução eficazes | Resultados JS não são autoridade; rejeitar versões/categorias alteradas pelo modelo. |
| C04/C08 + Meta | Ledger de plano/tentativa e eventos; resultado externo reservado/cancelado | C08 local não equivale a confirmação do provedor; revisar corrida entre cancelamento, reserva e entrega. |
| Serviço F02 futuro | Idempotência durável, revogação, expiração com relógio confiável, política aprovada, fila e logs | Ainda **não implementado**. Construir somente após coordenação e aprovação. |

**Branches externas observadas em 26/10/2026, sem incorporação:** `feat/s0-auditoria-nucleo-operacional-20261025` em `060b472b` introduziu ensaio do adaptador transacional GoTrue (`backend/s0_cfi01_communication_local.py`, `backend/s0_communication_contract.py`); `exp/s0-meta-integracao-auditoria-20261026` em `e3b3ff65` evoluiu laboratório Meta e isolamento de locks. Não há evidência, apenas por esse inventário, de que as propostas F02 sejam compatíveis com tais interfaces — **comparação/review pelo Codex é obrigatório**.

## 4. Cobertura e limitações

**Baseline comprovada antes deste ciclo:** 84/84 S0 Python; 561/561 F02/F03 Python, incluindo **330 cenários físicos PG17**; 269/269 S2 JS: **914 verificações de suítes distintas**. Elas não equivalem a 914 jornadas comerciais completas, aos 70 oráculos E02 originais homologados ou a teste de integração no Supabase hospedado.

A janela da solicitação de revisão (máximo **48h**) difere da janela sintética de horário de recontato (**24h–7d**); ambas são **fixtures experimentais**. `UntrustedTimeline`, revogações, registros e relógio são insumos do chamador. SHA-256 do handoff não autentica o emissor e nenhum retorno positivo comprova inexistência de opt-out tardio ou de revogação real.

**Arquivos deste ciclo**: nova matriz JSON, este relatório e teste de rastreabilidade dos contratos. O runner experimental da própria branch pode incluir o novo teste, sem editar workflows externos. Nenhuma migração, serviço S0 oficial, banco hospedado ou cliente real deve ser alterado.

**Próximo gate:** executar CI da própria branch, validar matriz contra nomes de teste/código e entregar os requisitos faltantes ao Codex; preparar depois cenários funcionais realmente ausentes, sem duplicar os 330 cenários físicos já existentes.
