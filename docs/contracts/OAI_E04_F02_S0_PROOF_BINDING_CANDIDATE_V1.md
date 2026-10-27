# F02 → S0/F03 — Validador de vínculo *declarado* das quatro evidências (E04, candidato 0.1)

**Checkpoint de entrada:** F02 `559b583d2d3e1f8b9c035d08bdb0ecd01de78861`, CI 40490546531 SUCCESS, PR #1 Draft. Auditoria S0 `aux/f02-s0-auditoria-integracao-20261027` `7c282df5f6e5942729f15187c199dffb5e872797` aponta G01–G06 parcialmente atendidos e G07 pendente; nenhuma liberação operacional.

## Código adicionado

`backend/f02_s0_proof_binding_candidate.py`: `inspect_claimed_proof_binding(evidence, proposal, window, packet)` verifica exclusivamente a **consistência do formato candidato** entre os quatro campos de `ClaimedS0Evidence` e suas referências **declaradas pelo chamador**. A função:

- Refaz `prepare_handoff`, confronta `handoff_sha256`, valida loja/lead/caso/encerramento no envelope e em **cada** uma das quatro referências.
- Exige os caminhos/métodos de produtor local previamente inventariados, rejeita campos extras ou ausentes, examina `source_ref`, revisão e versões alegadas de canonicalização/verificador.
- Compara cada hash declarado com o hash do pedido, sem alegar sua origem; exige observações e cortes temporalmente consistentes com o instante de encerramento declarado e a proposta.
- Retorna um único `ProofBindingResult(status)`, sem identificadores de origem, dados privados, credenciais ou ações. `CANDIDATE_CONSISTENT_NOT_ATTESTED` **não é validação de fonte**: todas as versões, timestamps, GUIDs, recibos e provas podem ser falsificados pelo chamador.

**O envelope `prumo.f02.s0.claimed_proof_binding/0.1-lab` é uma proposta de integração F02, NÃO um schema aceito pela S0.** Seus nomes de campos/versionamento são sintéticos e não definem a identidade/retorno efetivo de C08, F03 ou S1. Não modificar o `prumo.s0.f02.review.result/0.1-candidate` nem o núcleo de registro S0; não importar modelos de execução para conceder capacidades.

### Cuidados com cronologia

`closure_at` e `observed_at` são alegados. O ensaio exige `closure_at <= observed_at <= cutoff_at <= proposed_at`, comparando instantes UTC para evitar inconsistência de fuso. **Esta sequência é somente uma regra candidata de sanidade para a interpretação local de provas pós-encerramento**, não o contrato temporal canônico. Um produtor real pode ter timestamps e cutoffs diferentes: antes da integração a S0/F03 precisa definir esse mapeamento, sem reinterpretar silenciosamente o resultado como aprovação.

### Requisitos futuros por prova (não implementados)

O mapa `docs/contracts/OAI_E04_F02_S0_MAPA_QUATRO_PROVAS_V1.json` continua sendo a fonte de produtor/método e lacunas. A S0, F03 e domínios responsáveis devem especificar:

| Prova | Verificador físico a ratificar |
|---|---|
| F03 | Recibo final, conteúdo autorizado/minimizado, versões de caso/ficha/atribuição e catálogo, assinatura/canonicalização/cutoff |
| C08 local | Identificador de cadeia/plano/tentativa, HMAC e versão, releitura transacional, distinção expressa de disposição externa Meta |
| Origem | Ledger AFTER, ordenação física, criação original, consistência e completude da origem, rejeição de retrodatação |
| Intenção | Fonte de intenção sintética e, separadamente, futura ratificação do gestor legitimado S1, com revogação e expiração |

A S0 mantém as decisões G01–G07 e futura implementação de verificação de fontes; F02 não promove hash, `source_ref` nem revisão de candidato a autorização comercial.

`backend/tests/test_f02_s0_proof_binding_candidate.py`: 24 novos testes unitários offline, com escopos adversariais, trocas de digest/proposta, campos desconhecidos, falsos flags, ordenação temporal e ausência de capacidades. Runner PG17 de E04 inclui a suíte apenas para regressão; não transforma a implementação em integração física. A matriz passa para F02-A27 `LAB_VERIFIED` **após** CI SUCCESS no commit correspondente.

**Sem chamadas a Supabase hospedado, OpenAI real, Meta, banco, produção, migração, frontend, S0 oficial ou n8n.**

## Ajuste depois da auditoria F01/F02/F03 × S0 (27/10/2026)

O SHA do handoff F02 não inclui o prazo do pedido, mas o registro físico S0 exige um documento integral que inclui os dois instantes de `ReviewWindow`. O formato candidato da F02 agora exige `review_window.requested_at/expires_at` e confere igualdade UTC com o objeto `window` recebido independentemente. Isso reduz troca acidental do contexto temporal sem alegar autenticação, HMAC ou TTL de negócio. Ver `docs/OAI_E04_F01_F02_F03_S0_AUDITORIA_CONTRATOS_20261027.md`.

`observed_at` candidato é horário de **inspeção alegado**: não equivale a data de criação da mensagem F03 (possivelmente anterior ao fechamento). A ordenação antiga continua somente um pressuposto de laboratório; S0/F03 deverão definir a semântica canônica antes da integração real.

## A29 — Instante original e instante de inspeção

O envelope candidato agora inclui `proofs[field].source_event_at`: instante da ocorrência original declarado, com fuso, ou `null` quando desconhecido. O campo não substitui `observed_at` (inspeção de prova alegada). A verificação permite fonte histórica F03 anterior ao fechamento, mas nega evento futuro em relação à inspeção. Nenhum campo concede autoridade; a S0 ainda precisa revalidar a origem. Ver `docs/OAI_E04_F02_A29_EVENTO_HISTORICO_VS_INSPECAO_20261027.md`.
