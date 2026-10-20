# F03 OAI-07 → S0 → F02 CF-OP-02 — bloqueio de recontato comercial em etapa bancária (v0.1)

**20/10/2026 | Status:** projeto técnico **[P/R]**, simulação offline. Integração física, catálogo, consentimento, LGPD, regras banco/Meta e decisões normativas permanecem pendentes. Nenhum banco ou serviço externo foi consultado.

## Divisão operacional

- **F03** avalia o desfecho da conversa humana concluída: `NEGOTIATION_READY_FOR_BANK_HANDOFF`, `CONTINUE_TO_BANK_REVIEW`, `NEEDS_CLARIFICATION`, `CUSTOMER_WITHDREW`, `NO_FURTHER_COMMERCIAL_INTEREST`, `INCONCLUSIVE`. O fechamento humano é **evento técnico**, não venda, remessa bancária ou status comercial.
- **S0** decide se há comprovante real de remessa, elegibilidade, campos essenciais, operador com acesso, momento vigente e eventual autorização específica de planejamento. Um gerente mencionar informalmente que vai "amarrar" não comprova aprovação nem remessa.
- **F02** propõe apenas template/versão/horário de recontato para solicitação admissível da S0; nenhum modelo envia, cria template, agenda, aplica C09 ou cria prova do banco.

## Implementação adicional no PR #8 Draft

`backend/s0_openai_bridge/f03_outcome_plan_router.py` (Git blob **`ab6a8eb87f24aea290036ccb27e4e51aedad149b`**) compõe a avaliação F03 OAI-07 e a ponte F03→F02 existente usando um **`S0StageDecision` completamente FICTÍCIO**; esse campo e autorização de recontato para esclarecimento **não são** API real aprovada. `backend/tests/test_f03_outcome_plan_router.py` (blob **`654fb938c8561ae7816f6585f680c8f8b7803f63`**) oferece 43 casos sintéticos.

| Avaliação candidata F03 | Encaminhamento do roteador offline |
|---|---|
| `CONTINUE_TO_BANK_REVIEW` (com ou sem `bank_submission_proved` na S0 fictícia) | `COMMERCIAL_RECONTACT_BLOCKED`; sem agendamento comercial; a prova de banco e suas consequências são exclusivas da S0 |
| `NEGOTIATION_READY_FOR_BANK_HANDOFF` | `COMMERCIAL_RECONTACT_BLOCKED`; não confundir preparo/remessa com abandono |
| `CUSTOMER_WITHDREW` e `NO_FURTHER_COMMERCIAL_INTEREST` | `COMMERCIAL_RECONTACT_BLOCKED`; nunca transformar desfecho em `perdido` |
| `INCONCLUSIVE`, evidência insuficiente ou pendência essencial | `HUMAN_REVIEW`; campo essencial exige complemento humano |
| `NEEDS_CLARIFICATION` | `REVIEW_ONLY` apenas sob S0 fictícia que autoriza **expressamente este estágio**, sem banco/remessa, opt-out, desatualização, pendência essencial nem falha da ponte F03→F02; política final permanece **[R]** |
| Revogação de sessão, loja, finalidade, handoff ou rota humana | `DENIED` **antes** de revelar classe do desfecho e antes de `STALE` |
| Nova mensagem, formulário/catálogo mudado | `STALE`; não aplicar plano antigo |

Resultado `REVIEW_ONLY` carrega **somente IDs/versões de templates** e não implementa horário, envio, comando SQL, autorização transacional ou status comercial. Uma concessão S0 sintética **não comprova** elegibilidade real; as três verificações de escopo devem ser refeitas atomica e autoritativamente antes de qualquer efeito futuro.

## Evidência testada e pendências

No laboratório isolado criado a partir dos arquivos verificados do último pacote OAI-07: **179/179 PASS** em uma execução de `unittest discover` (44 F02 + 48 ponte F03/F02 + 44 desfecho F03 + 43 roteamento). `compileall` PASS. Houve falha inicial ao esquecer pendência essencial; foi corrigida antes do resultado final. Testes adversariais adicionais asseguram que rota/posse humana inválida seja negada mesmo no ramo bancário.

**Esses 179 testes não validam NLP real, recibos bancários reais, segurança transacional física, Meta ou as sete suítes históricas de 210 F03 (ainda sem regressão conjunta).** Nenhuma integração OpenAI paga, cliente real, SQL, merge ou deploy. Contratos OAI-05/OAI-07/CFI-01 (issue #4) e CF-OP-02 (issue #6) aguardam ratificação. Próximo passo: reconciliar a assinatura S0 de evento de encerramento, comprovante bancário, categoria de acompanhamento e regras por fase antes de substituir `S0StageDecision` fictício.
