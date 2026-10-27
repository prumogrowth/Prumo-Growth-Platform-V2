# F02/S0 — critérios de homologação conjunta e correção de cronologia UTC V1

**Emissão:** 27/10/2026. Frente isolada `feat/oai-s0-f03-history-port-20261023`, PR #1 Draft. Base S0 candidata: `exp/s0-f02-revisao-autoritativa-20261026` no `88af4aea3aeb2c403bab4c078fdc04d560f2cba0`, evidência de CI S0 `40414847271`. Código F02 anterior certificado `dcac0d17196daadce6e095cbbb2650f7c74fbbdd`, CI `40473502352`.

## Objetivo e entrega de código

A F02 já vincula o hash SHA-256 **não autenticado** do pedido às quatro evidências declaradas, proposta, template e versão, interpreta os 13 estados técnicos candidatos da S0 e bloqueia promoção a ações comerciais. Faltava uma leitura única, **testável por máquina**, da compatibilidade local versus aquilo que permanece sem homologação interfrentes.

Novo módulo `backend/f02_s0_joint_homologation_candidate.py`: `assess_joint_review_candidate(evidence, proposal, handoff, window, projection, previous=None)`. Ele reusa `classify_bound_s0_review_followup`, mantém toda a validação do contrato/continuidade e retorna somente `JointAssessment(status, followup, blockers)`, com exatamente os sete gates técnicos pendentes do manifesto `docs/contracts/OAI_E04_F02_S0_JOINT_GATES_V1.json`.

Nenhum campo de evidência fornecido pelo chamador, status `RECORDED`/`CURRENT`/`REPLAY`, revisão de hash, booleano ou resposta `UNAVAILABLE` elimina um desses gates. Não existe estado `APPROVED`, execução de IO, autorização de transporte, credencial, endpoint, aprovação, persistência ou agendamento.

Uma projeção local coerente é `CANDIDATE_CONSISTENT_NOT_HOMOLOGATED`; retorno S0 negativo exige `S0_RECHECK_NOT_HOMOLOGATED`; divergência de contrato, retomada ou origem de proposta exige `CONTRACT_RECHECK_NOT_HOMOLOGATED`. Em todos os casos, os sete bloqueios permanecem.

## Gates explícitos a validar com responsáveis

| ID | Frente/área | Critério de liberação futuro |
|---|---|---|
| G01 | S0 | Ratificar versão/protocolo, result e comandos |
| G02 | S0/Frontend/S1 | Canal autenticado, lookup D3 e binding CFI server-owned, inclusive reentrada |
| G03 | S0/F03/F02 | Prova de recibo F03, cutoff, C08 local e ledger de origem autenticados |
| G04 | S0/S1 | Autoridade de gestor independente do capturador, ato auditado com negação/revogação |
| G05 | S0/Meta/Privacidade | Disposição real de reserva/tentativa, opt-out, consentimento e template |
| G06 | S0/Produto/Privacidade | Política temporal, retenção, minimização e versões homologadas |
| G07 | S0/F01/F03/F02/S1 | Cenário físico integrado do encerramento humano à revisão, com corridas negativas |

Esses itens são **dependências de homologação**, não pedidos de implementar tudo agora na F02. O manifesto registra apenas `INTEGRATION_PENDING`; jamais deduz release a partir de testes locais. A F02 não modifica código/provas da S0, nem adapta sozinho seu registro PG17/GoTrue.

## Cronologia e horário de verão

Foi corrigido um detalhe real em `inspect_s0_review_projection`: comparação de `requested_at >= expires_at` em `datetime` com o **mesmo tzinfo ZoneInfo** pode comparar horários de parede nos minutos ambíguos da volta do horário de verão, ignorando a diferença de `fold`. Agora a ordem da janela é comparada em instantes UTC. Casos adversariais em `America/New_York` provam tanto a recusa de janela retrocedida quanto a aceitação de sequência UTC válida cuja hora de parede diminui.

**Não se presume horário de verão para a operação em Recife ou adoção de timezone estrangeiro**: estes são vetores adversariais de validação genérica de timestamps aware. A janela voluntária S0 de 72h do teste continua distinta dos 48h da fixture F02 e da janela sintética de proposta de contato; nenhum teto comercial é aprovado.

## Auditoria, limites e próximo trabalho

`backend/tests/test_f02_s0_joint_homologation_candidate.py`: 20 testes novos, cobrindo os 13 estados S0, sete gates não dispensáveis, perdas, terminal/reabertura, alterações de proposta, falsas permissões, trocas de fuso e sequência cronológica. O runner PG17 experimental passa a incluir a suíte. Matriz F02-A24 acrescentada como `LAB_VERIFIED`, **não** `INTEGRATION_PENDING` homologado. A certificação só vale quando GitHub Actions terminar com SUCCESS no commit atual.

A S0 ainda não publicou resultado autenticado no canal da F02; o registro é transacional no próprio laboratório, mas `projection` recebido no módulo F02 continua um dicionário alegado por chamador. Assinatura do canal/proveniência, ratificação real S1, C08 externo/Meta, opt-out, TTL produtiva, transportes e regras de retenção continuam de responsabilidade da S0 e frentes correspondentes.

**Sem merge, deploy, main, credenciais reais, Supabase hospedado, migração produtiva ou disparo Meta.**
