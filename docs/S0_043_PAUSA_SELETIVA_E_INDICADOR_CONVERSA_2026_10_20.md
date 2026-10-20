# S0-043 — Pausa de novos leads com redistribuição seletiva (candidato offline)

Data: 20/10/2026. **Decisão direta do responsável [D]**. Fronte proprietária S0 autorizada a realizar ajustes pontuais; frente S1-002 permanece independente e é responsável por implementação transacional de equipe, atribuições e grants. **Sem deployment/merge, acesso ao Supabase hospedado, migração RLS ou alteração de endpoints.**

## Separações obrigatórias

| Dimensão | Regra de produto | Efeito |
|---|---|---|
| Conta | Só responsável adiciona, remove e bloqueia operador/gestor | Suspensão/revogação independente de distribuição |
| Recebimento de novos leads | Gestor pode pausar/retomar operador da própria equipe, com confirmação simples, sem motivo/data | Impede novas atribuições em todas as lojas concedidas |
| Casos SEM contato humano confirmado | Redistribuir automaticamente somente para operador disponível da **mesma equipe** com grant válido da **loja do caso** | Sem substituto: permanecer com o operador pausado, sob atenção do gestor |
| Casos COM contato humano confirmado | Permanecem na titularidade original durante pausa | Transferência manual individual por decisão do gestor |
| Transferência manual SEM grant de loja | Decisão do responsável admite exceção dentro da equipe | Exige autorização **estrita por caso**, não concessão geral, que S1/S0 ainda precisam formalizar e garantir em RLS |
| Retomada | Gestor confirma pelo botão | Novos leads podem voltar; casos anteriormente redistribuídos não retornam por inferência |

**Contato humano iniciado:** critério de prova candidato é o primeiro evento humano efetivamente persistido no S0; atribuição, leitura, abertura do diálogo ou interações apenas da IA não servem. Estado desconhecido ou sem prova deve **permanecer sem transferência automática**.

**Mensagens:** interface operacional deve apresentar **um único indicador**: número de mensagens recebidas não lidas; após leitura confirmada sem resposta, a mesma bolinha perde o número e muda de cor; resposta humana confirmada remove a pendência. Cor final é design. Gestor ler conversa não deve marcar como lida pelo operador. Métricas por tempo/sla não têm prioridade na lista operacional.

## Mudança desta frente S0: componente de política puro, aditivo

`backend/operator_distribution_policy.py` e `backend/tests/test_operator_distribution_policy.py`.

- Recebem exclusivamente **snapshots fictícios** de caso, primeiro contato humano comprovado, chefia, versão, concessionária e possíveis destinatários, sem consultar banco.
- `propose_selective_pause_case` devolve uma **proposta, nunca uma operação**: `RETAIN_STARTED`, `RETAIN_CONTACT_UNVERIFIED`, `RETAIN_NO_SAME_TEAM_RECIPIENT`, `PROPOSE_SAME_TEAM_REASSIGNMENT` ou `DENIED_OR_UNVERIFIED`.
- Nenhum caso perde titular quando não existe elegível. Receptor proposto precisa compartilhar o gestor, estar com conta ativa, disponível para intake e possuir grant da concessionária de origem. Ordenação determinística é apenas de ensaio, não algoritmo final de distribuição nem distribuição equitativa.
- `classify_manual_transfer_target` retorna `S1_STANDARD_AUTH_REQUIRED` ou `S1_CASE_SCOPED_EXCEPTION_REQUIRED`, **sem autorizar transferência**. Falta de grant de loja não pode ser convertida em grant geral pelo S0 nem pelo browser.
- Funções são sem efeito colateral; não alteram conta, status comerciais, caso, logs, Meta, remessa ou RLS; não aceitam informações médicas, prazo ou justificativa.

## Integração pendente com S1 — atenção

O I11 atual da S1 suspende `equipe_prumo_s1.estado` e redistribui **TODOS** os casos ativos. I12 exige grant de loja nas transferências manuais, inclusive entre membros da equipe. Ambos precisam mudar **sob propriedade da frente S1**, não mediante alterações furtivas nas migrations anteriores. A [issue #10](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/10) contém as divergências anteriores; o responsável enviará mensagem detalhada com as regras novas. Nenhuma interface é exposta na S0 enquanto essa autorização e transação não estiverem disponíveis.

Contrato de integração a pactuar: prova de contato humano persistido; status de intake próprio; critérios de elegibilidade; autorização por caso/expiração; versão de atribuição; serialização transacional e idempotência; auditoria técnica sem motivo pessoal; projeção de não lidas e lidas sem resposta separada do ato de gestor visualizar.

## Gate técnico

Validação local limita-se a testes unitários do módulo puro com cenários sintéticos. Provas PostgreSQL, GoTrue/PostgREST, concorrência, RLS, autorização real, canal Meta, integração bancária e possíveis efeitos colaterais da migration S1 são **pendentes**. Não considerar o fluxo operacional liberado com o módulo candidato isolado.

**Não alterar:** migrations antigas S0/S1, triggers, Auth, gateway, tabelas e índices existentes, comandos financeiros, provedores, usuários reais ou dados hospedados. O progresso 19F e homologação FV permanecem inalterados.
