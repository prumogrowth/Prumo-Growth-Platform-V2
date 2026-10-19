# S1-002/I12 — Movimentação manual de atendimento na equipe

**Status:** prova técnica em PostgreSQL 17 descartável, sem endpoint, sem GoTrue/REST real e sem merge.

**Regra [D]:** gestores administram OPERADORES supervisionados, independentemente das concessionárias. Somente os responsáveis concedem A/B/C a cada operador; o gestor não modifica essas concessões. O destino de uma movimentação precisa ser operador ativo, com autorização vigente para a concessionária do atendimento. **Hipótese prudente [P]:** o gestor só pode movimentar entre dois operadores da própria equipe; transferência entre equipes depende de contrato próprio.

Migration 049 adiciona função privada s1_mover_atendimento_da_equipe(solicitante,loja,caso,atribuicao_esperada,destino). A função confere alçada em origem e destino, trava registros de equipe em ordem e caso/ciclo, exige o ID exato da atribuição ativa para rejeitar replay, encerra atribuição antiga e cria a nova na MESMA loja. Cria histórico append-only de quem moveu, origem, destino, caso e IDs das atribuições. Ciclo vendido/perdido original sem novo caso humano é bloqueado; retorno humano pós-venda é permitido sem alterar vendido. Nenhum envio, status, grant ou composição da equipe é alterado.

O código aceita executor somente postgres no **sandbox**; não aceita chamada de authenticated/anon/service_role. Em produção será obrigatório extrair identidade validada da sessão pelo gateway e auditar autorização com requisitos do S0, incluindo caso já concluído. Testes S1M-01..12 verificam A/B sem grant para gestor, destino com/sem grant, pessoas de outras equipes, caso terminal versus retorno, repetição, isolamento por loja, trilha e negação da API. Testes concorrentes intersessões ainda pendentes.

**Limites:** não implementa agendamento, mutação RH real, controle de turnos, bulk manual, integração Meta, reabertura de caso, auth real nem alteração de S0.
