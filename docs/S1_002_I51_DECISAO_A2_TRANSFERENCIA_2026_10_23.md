# S1-002 / I51 — decisão A2: nunca transferir para Consultor pausado

**Decisão [D] do responsável em 23/10/2026.** Substitui exclusivamente a antiga pendência A2 da matriz/contrato S1 de 22/10 e a etiqueta "bloqueio conservador" da I35. Não muda a autoridade S0 sobre o caso nem autoriza merge, deploy ou migrations operacionais.

## Regra de negócio inequívoca

- **É proibido transferir ou atribuir qualquer lead ou atendimento NOVO a um Consultor enquanto o intake estiver pausado.** Abrange atribuição automática, transferência manual comum (com concessão de loja), transferência manual excepcional (sem concessão de loja, somente por caso), encaminhamento de fila compartilhada e tentativas de bypass pelo backend. Gestor não pode forçar envio ao destino pausado.
- A autorização deve ser verificada **no commit da movimentação**, sob locks e versão do estado de intake/cheﬁa/caso, não somente em tela ou antes da operação. Recusar, sem conceder entitlement por caso, sem duplicar titular, sem mudar histórico nem mover o item da fila.
- **Pausar novos recebimentos não significa bloquear conta ou atendimento antigo.** O Consultor conserva os casos de que ainda é titular e pode ler/responder conforme suas autorizações anteriores. Redistribuição automática desses casos já existentes continua com o contrato próprio de prova de ausência de primeiro contato humano e elegibilidade da mesma equipe; sem prova, conserva-se titular.
- Ao retomar intake, o Consultor passa a ser elegível para futuras atribuições; não recebe retroativamente leads transferidos durante a pausa.

## Cobertura de implementação S1 existente

O fixture `s1_053_issue10_disponibilidade_local_only.sql` já instalava `s1_10_guard_novos_leads` antes de INSERT/UPDATE de titular, interrompendo nova atribuição a destino pausado com `NOVOS_LEADS_PAUSADOS`. O fixture `s1_055_issue10_excecao_caso_local_only.sql` já negava a via excepcional com `DESTINO_COM_INTAKE_PAUSADO`, **mas descrevia erroneamente o bloqueio como conservador enquanto A2 estava aberta**. I51 formaliza a decisão, atualiza o comentário e acrescenta regressão expressa dos dois caminhos na stack PG17 descartável. Não se presume integração produtiva pela presença desses controles de laboratório.

`supabase/tests/s1_075_a2_transferencia_pausado_local_only.sql` testa seis critérios com dados fictícios: (1) exceção por caso para pausado negada com erro específico, (2) manual comum com concessão da loja para pausado negado pelo guard, (3) negações deixam titular e histórico intactos, (4) pausa não cancela leitura/resposta no caso anteriormente atribuído, (5) retomada habilita transferência comum futura, (6) retomada habilita transferência excepcional com escopo estritamente por caso e titular único. Toda fixture usa BEGIN/ROLLBACK e executa os modelos legados da S1 sob PostgreSQL descartável; nenhum contrato é alterado na S0.

## Integração faltante — necessário antes do fechamento S1-002

**S1:** consolidar acesso de Diretor/Gestor/Consultor, estado de intake versionado, proibição de selecionar destino pausado na UI e revalidação da autorização na operação de movimentação. A concessão de loja, o vínculo gerencial e entitlement excepcional NÃO anulam a proibição de pausa.

**S0:** produtor e consumidor de atribuição devem revalidar consulta de disponibilidade sob transação/lock, antes de inserir atribuição; mesma regra em fila manual, transferência direta, retomada da distribuição e fluxos de exceção; preservar eventos e auditorias idempotentes. Reconciliar ordem de locks S1→S0 e provar concorrência pausa-vs-transferência com contas GoTrue reais em ambiente integrado, não apenas fixtures.

**A2 deixa de integrar pendências de decisão.** Continuam pendentes especificações físicas do primeiro contato humano, DELIVERED/indicadores, mensagens/histórico D2-D4, F03, integração S0 e eventuais dependências externas. A proibição de transferir para pausado **não** decide automaticamente que todo caso já atribuído será transferido.

## Evidências

Registrar commit testado, resultados do CI e limites depois da execução.
