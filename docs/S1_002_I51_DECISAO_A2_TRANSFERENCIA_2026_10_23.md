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

**Evidência verificada em 23/10/2026:**

- [PG17 completo — GitHub Actions #39982946724](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39982946724), job `120514688377`, **SUCCESS** sobre o commit `dc2175a3c62f59fe738741d3005ac0df8ac656a6`. Logs inspecionados: `PASS I51-01`, `02`, `03`, `04`, `05`, `06` — **6/6** com SQL transacional e rollback. O teste comprova recusa de transferência excepcional e comum para destino pausado, preservação do caso original e retorno à elegibilidade só após retomada.
- O runner `scripts/run-s1-002-i12-local.sh` passa a executar `s1_075_a2_transferencia_pausado_local_only.sql` junto com os contratos e regressões antigas. Nenhuma migration S0 alterada; não se trata de integração real de serviço nem de teste GoTrue/Meta.
- Contrato 01, matriz 02 e índice 00 atualizados para marcar **S1-D14/A2 como [D] FECHADA**, explicitando diferença entre bloqueio de **novas atribuições** e permanência de autorização em casos já atribuídos.

**Pendente [R/T] técnico:** os serviços do núcleo S0 devem consumir estado de intake do destino com prova de versão/lock em todos os comandos de atribuição, antes do commit, inclusive concorrência de pausa e transferência. Os testes PG17 de fixture não homologam o backend produtivo, a fila S0 real, o WhatsApp nem a operação da plataforma.
