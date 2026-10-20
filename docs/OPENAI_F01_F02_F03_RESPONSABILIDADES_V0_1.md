# LiberaCred — responsabilidades F01, F02 e F03 | v0.1

**Atualização:** 20/10/2026. **Escopo:** explicação funcional + inventário do laboratório; não ratifica contratos físicos, política comercial ou implementação de produção. **Referências:** OAI-01/E01/E02, OAI-05, OAI-08, CFI-01 (issue #4), CF-OP-02 (issue #6), PR #8 Draft.

## F01 — IA Vendedora: conversa e qualificação enquanto a IA é responsável

- **Objetivo:** conduzir atendimento comercial inicial permitido, responder dúvidas com conteúdo aprovado, coletar informações progressivamente e solicitar transferência a operador humano quando cabível.
- **Quando atua:** somente enquanto a S0 comprova posse IA válida para aquele caso/ciclo, contexto e permissões atuais.
- **Saída técnica proposta:** mensagem de atendimento para validação/publicação exclusiva da S0 e transporte exclusivo da frente Meta.
- **Proibições:** inventar aprovação, negativa bancária, taxa, oferta ou prazo; persistir por conta própria; enviar diretamente ao WhatsApp; reassumir o caso depois de handoff definitivo para humano.
- **Situação em código:** `f01_offline_gate.py` valida proposta `sales_reply` e a posse/versão/corte em **dados sintéticos**; `REVIEW_ONLY` não é licença de enviar nem teste de veracidade de conteúdo.

## F02 — IA Planejadora: sugerir recontatos e sequências de templates elegíveis

- **Objetivo:** a partir de solicitação **autorizada pela S0**, propor quantidade, ordem, janelas/horários e IDs/versões de templates já aprovados, justificando com fontes autorizadas.
- **Quando atua:** ciclo elegível da própria IA, solicitação de profissional autorizado ou eventual acompanhamento pós-humano **se** a categoria/regra for ratificada e a S0 emitir autorização própria.
- **Saída técnica proposta:** plano de tentativas com `template_id/template_version`, horário candidato e evidência; inclui template final separado quando a política do caso permitir.
- **Proibições:** inventar mensagem de template, agendar/salvar/enviar por conta própria, escolher a rota da resposta do cliente, contornar opt-out, disparar recontato pós-venda sem finalidade/permite explícitos ou alterar o status comercial (incluindo C09).
- **Situação em código:** `f02_offline_gate.py` valida cadeia candidata em **dados fictícios**; o número 2–5 e final separado foram codificados como **hipótese de laboratório**, não como contrato final. O relógio Meta e regras de falha/silêncio continuam S0/Meta [R/V].

## F03 — IA Extratora silenciosa pós-atendimento humano: preencher ficha com evidência

- **Objetivo:** após conclusão humana **registrada pela S0**, realizar **duas análises da mesma conversa autorizada**, preservando evidência e incerteza: (a) propor todos os campos elegíveis para a ficha; (b) **avaliar o desfecho conversacional** OAI-07 — interesse confirmado/pronto para remessa, menção a retorno do Banco, necessidade de complemento, desistência explícita ou inconclusão. O fechamento do operador não comprova negócio encerrado.
- **Quando atua:** mesmo depois que a IA Vendedora fica definitivamente silenciada; é processamento interno, não nova conversa.
- **Resultado de negócio pretendido:** **a S0**, após revalidar proveniência, catálogo, autorização e versões dentro da transação, aplica automaticamente os campos elegíveis na ficha sob **autoria técnica auditável**; o operador não deve redigitar rotineiramente os dados, mas pode conferir e corrigir exceções.
- **Proibições:** inventar dados, aplicar diretamente no banco, falsear autoria humana, mudar status bancário, declarar `vendido`/`perdido`, retomar F01, enviar mensagens ou transformar uma sugestão de recontato em autorização.
- **Situação em código:** validadores `f03_offline_gate.py`, `f03_assignment_recheck.py`, `f03_review_pipeline.py`, `f03_candidate_wire.py` e o NOVO `f03_outcome_offline_gate.py` trabalham em simulação, **sem integração entre todos os payloads físicos**; contratos transacionais de gravação/estágio bancário S0 ainda [R]. O novo gate faz somente triagem lógica de um rótulo/modelo e referências fictícias: **não interpreta língua natural com IA real**.

## A fronteira F03 → F02 é controlada pela S0

Após a conclusão humana, F03 pode identificar com fontes `FollowupNeed.YES/NO/UNCERTAIN`. **Isso não dispara automaticamente F02.** A ponte sintética `f03_f02_offline_bridge.py` só revisa uma proposta F02 quando recebe uma **solicitação S0 separada**, além de evento, snapshot, catálogo, finalidade, elegibilidade e permissões coerentes. Se houver opt-out, remessa, venda histórica, retorno de suporte ou perda de acesso, rejeita. Mesmo o retorno `REVIEW_ONLY` não agenda, não envia nem faz C09.

Exemplo conceitual: F01 conversa inicialmente e transfere ao operador; o operador conclui seu atendimento; F03 propõe preencher campos explicitamente informados; a S0 valida e pode aplicá-los; se houver acompanhamento permitido e solicitação autorizada, F02 propõe somente templates existentes para nova análise da S0. O eventual retorno do cliente após handoff é humano.

**Nota de terminologia:** F02 Planejadora de recontatos **não é** a IA separada de aperfeiçoamento/avaliação da IA de atendimento. Uma futura função de melhoria de parâmetros possui governança distinta e não deve editar seus próprios limites imutáveis.

## Evidência e pendências em 20/10/2026

- **Correção comprovada:** ponte F03→F02 passou a verificar revogação/opt-out/flags inválidas **antes** de retornar `STALE` por alteração simultânea de versão/inbound/fechamento. O comportamento anterior retornava indevidamente `STALE` quando a autorização havia sido revogada e o snapshot também mudado.
- **Regressão local atual:** **92/92 PASS** em uma única execução (44 da F02 + 48 da ponte, com quatro testes novos dessa prioridade). Sem API externa, dados de clientes, SQL ou efeito operacional. Hash do módulo corrigido: `c368fbc9884d69bf2d2b1dd2e938b6e6e3a5c9f9`; dos testes da ponte: `488d193b6bb853b042d3bb651bbf3f9b9a284aac`.
- **Regressão F03 separada:** as sete suítes históricas somam 210 testes e **continuam sem execução conjunta contra a versão atual**. Não somar séries de laboratórios diferentes como se fossem uma regressão única.
- **Próximo bloqueio:** S0/S1 e Meta devem ratificar contratos e prioridades transacionais, autorização real por loja/caso, política de campos/templates, opt-out, evento de conclusão e outbox. Ainda não há aprovação para merge, deploy, chamadas OpenAI pagas, dados reais ou escrita no Banco.

### F03 — exemplos de resultado conversacional OAI-07 [P/R] (20/10/2026)

| Evidência de conversa | Avaliação candidata F03 | Autoridade S0 e limite |
|---|---|---|
| Interesse confirmado, requisitos essenciais válidos, ainda sem remessa comprovada | `NEGOTIATION_READY_FOR_BANK_HANDOFF` | Orientar remessa **humana** ou fluxo homologado; **não** marcar `vendido` |
| "Estamos aguardando o retorno do banco", com envio bancário COMPROVADO em registro S0 | `CONTINUE_TO_BANK_REVIEW` | Apenas **aviso de espera/revisão**; resultado bancário e status não vêm do texto |
| A mesma frase, SEM comprovante S0 de envio | `CONTINUE_TO_BANK_REVIEW` **não comprova espera bancária** | Conferência humana de remessa; não criar evento `cadastro enviado ao banco` |
| Falta campo essencial/catalogado ou esclarecimento necessário | `NEEDS_CLARIFICATION` ou revisão por campo | S0 devolve ao humano para complemento; opcional ausente não bloqueia por si só |
| Cliente disse expressamente que desistiu | `CUSTOMER_WITHDREW` | Registrar avaliação; **não** converter automaticamente em `perdido` sem norma aprovada |
| Desfecho não claro ou evidência inadequada | `INCONCLUSIVE` | Requer revisão humana |

**Implementação sintética adicional:** `f03_outcome_offline_gate.py` recebe `OutcomeSnapshot`, `S0OutcomeAuthority` e `ModelOutcomeCandidate` **fictícios**. A fonte que rotula evidência por assunto é uma anotação de teste, não prova de que a IA classificou corretamente texto real. Exige loja/caso/fechamento/snapshot/versões/assinaturas coerentes; sessão ou grant revogado prevalece sobre resultado defasado; fontes sem fala de cliente autorizada retornam revisão. O resultado é somente `OutcomeReview` com **aviso candidato**, sem venda, perda, prova de banco, persistência, agendamento ou emissão Meta. O sinal `bank_submission_proved` é **fato fictício exclusivo da S0** e jamais inferido da resposta do modelo. A seleção final de status, remessa, retorno e F02 continua S0 e depende de normas ratificadas.

**Evidência offline deste incremento:** `backend/tests/test_f03_outcome_offline_gate.py`: **44/44 PASS** no laboratório sintético, sem API ou banco real. Blobs Git locais/remotos código `83352135ec8a0e809e9b6f5e721f7b1ba9d6e90c`, testes `364d25d5240f195fb188dd2ac5b3e1e912450434`. A regressão histórica conjunta **210 F03 continua não executada** na versão vigente; estes 44 casos não provam NLP, precisão bancária nem execução transacional.
