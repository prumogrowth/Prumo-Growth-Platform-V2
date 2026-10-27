# Entrega F02 → Coordenação Codex/S0 — decisão sobre homologação experimental

**27/10/2026 — encaminhamento documentado, não enviado automaticamente à S0.** Fonte GitHub `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`; branch isolada `feat/oai-s0-f03-history-port-20261023`, PR #1 **Draft**. Checkpoint F02 de entrada `84d76c1340f5ab831e10a6e9c3c76fa1ee01d72e`, [CI #40475244137](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40475244137) SUCCESS (1.056 testes em suítes distintas). Fonte S0 candidata `exp/s0-f02-revisao-autoritativa-20261026`, HEAD `88af4aea3aeb2c403bab4c078fdc04d560f2cba0`; código S0 `4a3d248d46fad5c195398324b3ee98ae6236365f`, [CI #40414847271](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40414847271) SUCCESS.

## O que já está materializado (não refazer)

A F02 já tem `prepare_handoff` para evidência alegada e hash SHA256, `evaluate_bound_review_lifecycle`, retomada `evaluate_review_recovery`, leitura estrita de schema `inspect_s0_review_projection`, classificador exaustivo de 13 estados `classify_s0_review_followup`, vínculo forte **apenas de coerência sintética** com `classify_bound_s0_review_followup` e `assess_joint_review_candidate` com sete gates incondicionais. A F02 permanece incapaz de autenticar `projection` de um chamador. O resultado `CANDIDATE_CONSISTENT_NOT_HOMOLOGATED` indica somente coerência formal de uma cópia não confiável.

A S0 já materializou **exclusivamente em PG17/GoTrue/CFI descartáveis** registro/leitura/retirada persistente `S0F02ReviewRegistryLocal`, transação recheck + auditoria, locks, prova de sessão original, idempotência `loja+ator+chave`, tombstones de retirada/expiração e resposta de `prumo.s0.f02.review.result/0.1-candidate`. O escopo permanece `CFI_CONTEXT_ONLY_F02_EVIDENCE_PENDING`, sem ratificação do gerente, comprovação das quatro testemunhas F02, opt-out/Meta ou agendamento. **Não interpretar a S0 como já liberando envio.**

## Artefatos entregues por esta frente

- `docs/contracts/OAI_E04_F02_S0_INTEGRATION_HANDOFF_V1.json`: pacote JSON de coordenação, com provenance, responsáveis, perguntas e prova esperada para **G01–G07**.
- `docs/contracts/upstream/OAI_S0_F02_REVIEW_RESULT_SCHEMA_0_1_PINNED.json`: cópia **byte a byte** do `result.schema.json` no blob S0 `61598ba702dc03f9f715673118c88f9359e64113`, exclusivamente como fixture de contrato pinado; **não é uma migração S0**, assinatura, endpoint ou contratação definitiva.
- `backend/tests/test_f02_s0_integration_handoff_contract.py`: regressões offline de compatibilidade do schema S0, pin Git blob, enum de estados, flags não operacionais, sete gates e pendências A16–A18; `scripts/run-s0-f03-pg17-local.sh` inclui a suíte.
- `docs/contracts/OAI_E04_F02_ACCEPTANCE_MATRIX_V1.json`: critério `F02-A25` apenas `LAB_VERIFIED`, sem promover A16–A18.

O pacote é **proposta para revisão de integração Codex/S0**, não aprovação de Produto, Segurança, S1, Meta ou Privacidade.

## Pedido de decisão e prova pela S0

Leia primeiro os contratos acima e os documentos S0 `docs/contratos/f02_s0_review/CONTRATO_CANDIDATO_0_1.md` e `ENCAMINHAMENTO_F02.md`; confira se há SHAs posteriores. Responda ao pacote `docs/contracts/OAI_E04_F02_S0_INTEGRATION_HANDOFF_V1.json` por gate, com **estado de contrato** (já atendido, parcialmente atendido, pendente), apontador para commit/teste/recibo físico, e decisão explícita de responsabilidade. Não trate testes de forma de envelope como testes de homologação de operação real.

**Pontos que exigem decisão coordenada:** ratificação da interface (G01); transporte e lookup autenticados após troca de sessão/processo (G02); mapeamento e comprovação F03/C08/origem/intenção com cutoff (G03); gestor S1 separado do capturador (G04); estado externo Meta, opt-out, template (G05); prazos/privacidade/retencão (G06); teste integrado da passagem humana à revisão (G07).

**Especial atenção à divergência:** o registro S0 não garante exclusividade por encerramento humano, mas por ator+loja+chave; a timeline F02 isolada contém suposições por encerramento e não deve ser transplantada para a S0. A janela técnica S0 é limite voluntário do pedido, **não** os 48h de `evaluate_review_lifecycle` nem os 24h–7d de proposta F02. Cancelamento C08 local **não** prova cancelamento Meta.

## Regras de governança

Sem modificar branch S0 nem os PRs alheios, main, políticas oficiais, workflows de outras frentes, migrações de produção ou Supabase hospedado; sem identidades reais, mensagens, chamadas Meta ou fluxos comerciais. A autorização de envio, agendamento, ratificação humana e deploy continuam não implementados e não autorizados.

**Certificação do novo commit F02:** exigir CI da própria branch em SUCCESS. O pacote e os testes são candidatos até isso ocorrer; não usar o CI anterior como prova deste acréscimo.
