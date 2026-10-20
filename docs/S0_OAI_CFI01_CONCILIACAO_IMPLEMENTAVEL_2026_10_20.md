# CFI-01 — Conciliação técnica verificável S0 ↔ OpenAI ↔ FV/S1 | rodada de 20/10/2026

**Estado:** COMPARAÇÃO DE CONTRATOS FEITA; decisão/assinatura S0 e OpenAI **PENDENTE [R]**; substituição de permissões fictícias **BLOQUEADA até interface transacional aprovada**. Isto é proposta de integração para revisão dos proprietários, **não** nova norma, endpoint, DDL, API ou homologação.

**Referências verificadas em 20/10/2026:**
- S0 [PR #1](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/1), branch `feat/s0-fundacao-prumo`, HEAD observado `7ba1625d08a81c4cc2a360a86d8bbf291cc350c7`: `backend/identity_boundary.py` blob `e1b953d7506b65a74d4e39d75fad4cc326d5bdf9`; `docs/GATE_BACKEND_AUTH_S0_2026_10_17.md`, `docs/S0_037C_EXECUCAO_ASSINADA_COMERCIAL_2026_10_18.md`, `docs/CF_OP_02_CONTRATO_NUCLEO_RECONTATO_HUMANO_v0_1.md`, `docs/S0_043_PAUSA_SELETIVA_E_INDICADOR_CONVERSA_2026_10_20.md`.
- FV: `frontend/docs/05_CONTRATO_FV02_CONCLUSAO_EXTRAÇÃO_POS_HUMANA_v0_1.md` e `07_CONCILIACAO_INTERFRENTES_FV_S0_OAI_v0_1.md`, branch `feat/frontend-plataforma-visual`.
- OpenAI: OAI-05, OAI-07, OAI-08 e E01/E02 no [PR #3](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/3); protótipos F01/F02/F03 e roteadores no [PR #8](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/8).
- S1-002: atualização da [issue #10](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/10), sobre pausa/intake, redistribuição e exceção por caso; S1 ainda **não** fornece produção/atribuição física que autorize F03 por si só.
- Revisão solicitada nas [issues #4 CFI-01](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4) e [#6 CF-OP-02](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6). Ambas permaneciam abertas na consulta.

## 1. Estado real observado: reusar o que existe sem atribuir capacidades inexistentes

1. `backend/identity_boundary.py` já implementa, como **laboratório local**, verificação de identidade via GoTrue e verificação da sessão ativa na camada SQL. O módulo **não publica endpoint HTTP** e sua allowlist tem **somente** `cancelar_plano` e `conciliar_c07`. Não oferece `concluir_atendimento_humano`, consulta de grants/atribuição F03, `aplicar_extracao` ou `pedir_cadeia_pos_humana`.
2. Os testes S0 037C demonstram fluxo **HMAC + nonce + sessão e escopo** para operações C07/C08 sintéticas, não estendem automaticamente autorização a F03/F02. A cadeia tem limites próprios de owner/least privilege; **não** copiar `SECURITY DEFINER postgres` nem usar uma GUC/bool do browser como permissão.
3. O contrato S0 CF-OP-02 tem comandos **S0-A..F candidatos**, incluindo conclusão humana, novo plano e provas, mas declara **não ser API implantada nem assinatura ratificada**.
4. Não foi encontrada, nos módulos backend S0 listados e no contrato S0 consultado, implementação física **aprovada** do fechamento humano → snapshot → persistência automática, nem do comprovante de remessa para OAI-07. Isto não prova inexistência em outras branches; requer confirmação explícita do proprietário S0.
5. A regra S0-043 separa pausa de intake de suspensão da conta e exige **prova de contato humano já iniciado** para redistribuição seletiva. Um operador *pausado para novos leads* não equivale a um operador com sessão/grant revogado. A S1-002 ainda solicita ao S0 a fonte de prova e a autorização **excepcional por caso**; não tratá-las como implementadas.

**Consequência:** não é correto mapear `CurrentAuthority(... bools ...)`, `S0OutcomeAuthority`, `S0StageDecision` ou `S0PlanningAuthorization` dos gates offline como credenciais ou grants reais. Nenhum desses objetos autentica ou autoriza alguém.

## 2. Quatro fronteiras propostas, sem operação extra assumida

```text
FV (usuário autenticado)
  -- case_ref + expected_case_version + idempotency_key -->
S0 [verifica sessão + concessão + caso/atribuição + locks/versões]
  -- evento técnico durável + corte/snapshot autorizado + catálogo/política -->
OpenAI F03 (human_close_extract: campos + desfecho OAI-07 + fontes)
  -- proposta estruturada, sem permissão de escrita -->
S0 [valida proveniência/escopo/catálogo; rechecagem na MESMA transação;
    aplica apenas valores elegíveis; registra pendências e versão;
    verifica provas bancárias independentes de qualquer texto]
  -- se e somente se houver NOVA autorização de finalidade elegível -->
OpenAI F02 (recontact_plan: IDs/versões de templates e horários candidatos)
  -- proposta, sem execução -->
S0 [decide e registra eventual plano, revalida inbound/opt-out/concessão,
    S1 para titularidade, Meta para envio/recibos]
```

O fluxo não altera os oito estados comerciais por efeito de clique ou modelo; depois de qualquer handoff F01 continua silenciada. `ATENDIMENTO_HUMANO_CONCLUIDO` é evento técnico, não o fim do negócio. `WAITING_BANK` / `CONTINUE_TO_BANK_REVIEW` é **avaliação conversacional**, não comprovante de remessa, aprovação ou venda.

## 3. Tabela de reconciliação de campos: alternativas NÃO equivalentes

| Elemento | FV-02 / E01 | OAI-05 / OAI-07 | Proposta para decisão S0/OAI [R] |
|---|---|---|---|
| Pedido UI→S0 | `FV-02.request_human_conversation_completion` com `case_ref`, `expected_case_version`, `idempotency_key` | não é operação OpenAI | S0 definir comando, autenticação, resposta imediata e replay; **sem receber ator/grant/corte fornecidos pelo browser** |
| Evento domínio S0 | `trigger_ref` ou evento `atendimento_humano_concluido` | `closure_event_id` + `closed_at` | Escolher identificador físico, prova de autoria, estado técnico, cutoff e unicidade |
| Operação interna | `human_close_extract` | `human_close_extract` | Nome lógico convergente; **versão física [R]**, não mapear silenciosamente `s0-openai.v0.2-candidate` |
| Loja/caso/ciclo | `scope.{concessionaria_ref,caso_ref,conversa_ref,ciclo_ref}` | campos planos `concessionaria_id`, `caso_id` etc. | S0 definir identificadores **derivados de contexto autorizado**, não apenas eco do modelo |
| Conversa | `authorized_context_ref` + `context_version` | `snapshot_ref/hash`, `message_watermark`, `messages[]` | Definir watermark estável, proveniência, hashes, minimização e tratamento de mensagem em voo |
| Catálogo/ficha | `fields_policy_version`, `expected_case_version` | `allowed_fields_catalog_version`, `form_version_observed` | Distinguir catálogo, caso e ficha; catálogo D3/autoaplicação e normalização pertencem à S0 |
| Saída campos | `extraction.field_suggestions[] {field_key,value,evidence_refs}` | `fields_proposed[] {field_code,proposed_value,source_message_refs}` | Escolher **um** formato e rejeitar campos/fontes/desconhecidos; sem escrita do modelo |
| Lacunas/conflitos | `missing_field_keys[]`, `conflicts[]` | `missing_fields[]`, `conflicts[]`, `extraction_warnings[]` | Catálogo de motivo, nível da evidência e pendência essencial vs opcional sob S0 |
| Resultado/desfecho | `needs_human_clarification`, `outcome` | OAI-07 `conversational_assessment`, `next_step_proposal` | Retornar rótulo CONVERSACIONAL com fontes; S0 valida status e provas bancárias independentemente |
| Progresso UI | `ACCEPTED_FOR_PROCESSING` vs ficha atualizada | `PROPOSED/PARTIAL/NEEDS_REVIEW/FAILED` | Nunca confundir pedido aceito, retorno do modelo, S0 VALIDATED ou **APPLIED/COMMITTED** |
| F03→F02 | advisory sobre necessidade de acompanhamento | `followup_need_advisory` OAI-08 | Advisory não é comando; criar pedido C05 separado e idempotente **somente com permissão e finalidade S0** |

**Ainda sem conciliação física:** `f03_candidate_wire.py` rejeita blocos não vazios de lacunas, conflitos, avisos e advisory por ausência de schema ratificado; o protótipo de desfecho OAI-07 é outro módulo offline e **não foi acoplado a um contrato real de extração**. Não mudar o parser unilateralmente apenas para alcançar compatibilidade artificial.

## 4. Quem emite a prova de autorização real e como substituímos as fixtures

**Proposta de interface S0 read-only por operação**, sujeita a revisão: a S0 deve expor internamente **um caminho confiável e transacional** que (i) autentique sessão atual (reusar a cadeia GoTrue/HMAC admitida pelo S0, não token de modelo); (ii) resolva loja/caso/ciclo pelo domínio; (iii) valide papel/operador ativo, grant normal **ou exceção individual por caso especificamente ratificada na S1**; (iv) confira atribuição atual, versão/cutoff, fechamento e finalidade; (v) registre consulta/decisão e rejeição de acesso; (vi) devolva ao worker autorizado apenas informações mínimas e referências curtas, com validade **limitada ao processamento**, não uma permissão eterna para escrever.

A prova **não pode** ser uma flag `True` enviada pelo navegador, um campo de JSON do modelo, um registro assinado somente pelo próprio adaptador, um JWT não revalidado, nem um `owner_route` inferido da conversa.

**Aplica-se separadamente a cada efeito:** para persistir campos, S0 lê novamente os fatos sob locks/serialização e grava versão/auditoria atômicas; para registrar nova cadeia, revalida S1/C04/opt-out e regras de fase; antes de publicar para Meta, revalida destinatário, canal, template, versão e mensagem nova. O modelo nunca possui ferramenta SQL, grant administrativo, API Meta, credencial Banco ou `SERVICE_ROLE`.

**Marco B (substituição real) — NÃO INICIÁVEL ainda:** enquanto o S0 não publicar comando/evento/consulta confiável **aprovados**, nenhuma branch OpenAI poderá dizer que substituiu `CurrentAuthority`, `S0StageDecision`, `S0PlanningAuthorization` ou `bank_submission_proved` fictícios. Após a assinatura, implementar cliente server-side com **adapters S0 reais e testes de integração de negação/revogação/replay/escopo**, manter os objetos sintéticos somente como testes.

## 5. Decisões interfrentes necessárias, sem pergunta prematura ao responsável

| ID | Propriedade | Decisão/contrato para assinatura |
|---|---|---|
| R-S0-01 | S0 + FV | Comando único de conclusão humana, sem C10/C13, identidade, caso/versão, idempotência, resultado `ACCEPTED` distinto de `APPLIED` |
| R-S0-02 | S0 + S1 | Prova de atribuição e contato humano, conta ativa **vs** pausa intake, exceção por caso, revogação imediata/locks |
| R-S0-03 | S0 + OAI | Evento de conclusão + snapshot imutável, corte, hash, retries, nova mensagem e correção humana concorrente |
| R-S0-04 | S0 + OAI | Catálogo mestre por campo/versão/classe LGPD; autoriza aplicação automática, protege opcionais essenciais, autoria técnica |
| R-S0-05 | S0 + Banco | Fonte única de prova de remessa e retorno bancário, sem inferência da conversa; status comerciais permanecem sob ato autorizado |
| R-OAI-01 | S0 + OAI | Envelope/reply canônicos `human_close_extract` que conciliem E01/OAI-05/OAI-07, versão e erros |
| R-OAI-02 | S0 + OAI | Finalidade/consentimento, mídia/transcrição e limites reais de tratamento e chamadas, sem chave nem prompt no browser |
| R-F02-01 | S0 + Meta/OAI | Pedido NOVO pós-humano, elegibilidade por etapa, opt-out, catálogo/versionamento, limites e eventual C09 humana [R] |
| R-F02-02 | S0 + Meta/S1 | Status confiável sent/inbound, cancelamento por resposta/duas falhas qualificadas, janela Meta/relógio C09 separados |
| R-FV-01 | S0 + FV | UQ03/projeção e estados técnicos, campo/versionamento confirmados pós-commit, regra de erro/reprocessamento |

**Nota temporal:** o S0 evoluiu desde a conciliação FV de 18/10: o HEAD observado neste levantamento é 20/10 e contém regras novas de pausa seletiva S0-043. Antes de qualquer adapter real, revalidar HEAD e os contratos dos donos; não portar datas/nomes de migration por inferência.

## 6. Gates objetivos para cumprir a sequência solicitada

**A. Conciliação com a S0:** comparação e divergências concretas documentadas (**este artefato**), revisão/decisão formal S0 e OpenAI com versão de contrato publicada (**PENDENTE**). Até decisão formal, não declarar A concluído.

**B. Troca de permissões fictícias por reais:** exigirá S0 operar autenticação/escopo/atribuição/fechamento, prover snapshot e provar remessa via contratos reais, mais adapter server-side e teste real em sandbox seguro (**PENDENTE, DEPENDE DE A**). Se interfaces ainda não existirem, status é `BLOCKED_BY_S0_CONTRACT`, nunca `PASS`.

**C. Ponto de parada futuro:** **somente quando A e B estiverem finalizados e auditáveis**, parar evolução da frente, apresentar ao responsável lista deduplicada de dúvidas pendentes e, depois, iniciar auditoria geral de código/documentação/decisões. Não iniciar essa pausa nem a auditoria agora; 210 suítes históricas F03 continuam sendo outra pendência de verificação, sem atribuir a elas aprovação da integração.

**Sem merge, CI disparado por esta alteração, deploy, API paga, Supabase hospedado, dados pessoais reais, SQL comercial ou alteração de status.** PR #1, PR #2, PR #3, PR #5 e FV preservados.
