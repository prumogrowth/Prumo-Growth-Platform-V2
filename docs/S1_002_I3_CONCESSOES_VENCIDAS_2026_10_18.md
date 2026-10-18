# S1-002/I3 — Varredura de permissões vencidas | 18/10/2026

**Front única:** S1-002 / PR #5. **Natureza:** código exclusivamente local sintético, não serviço agendado. Base: D-ORG-01, I1/I2, contratos CF-OP-02.

## Lacuna atendida
O trigger I2 cobre uma suspensão ou uma revogação por UPDATE/DELETE do vínculo. Porém `valido_ate` pode vencer por tempo sem nenhum UPDATE, deixando a atribuição antiga formalmente ativa, mesmo que RLS já negue a concessionária ao operador. Não podemos considerar que o relógio provoca um trigger SQL.

## Nova fronteira interna
Função privada `prumo_private.s1_reconciliar_elegibilidade_vencida(max_grupos)` só executável por `postgres` em banco descartável. Seleciona grupos (operador Prumo, loja) com atribuições ativas e sem pertencimento ativo à equipe OU sem concessão operacional válida naquela loja. Executa o remanejamento I2 existente sob as mesmas travas, prioriza operador autorizado da mesma loja, preserva A se apenas B venceu, cria fila protegida se ninguém elegível, registra histórico e encerra vínculos residuais de casos vendidos/perdidos sem alterar o status. Suporta lote limitado de 1 a 100 grupos e repetição sem novos efeitos.

**S1-002 decide quem pode ser operador e quem passa a ser responsável pelo caso; S0 permanece proprietário do status, mensagens e agendamento de recontatos.** Frontend reflete, OpenAI não atribui, Meta não determina acesso.

## Limite explícito
A função é invocação interna **sob demanda** no teste; não há scheduler, credencial de execução de worker, aprovação de administrador RH ou rotina de produção. Isso é um mecanismo de reconciliação, não monitoramento em tempo real. A entrada real na plataforma, intervalo de execução, custos, autoridade e alertas ainda precisam de especificação e autorização.

## Critérios propostos
S1X-01..07: fixture multiloja A/B/C, vencimento verdadeiro sem UPDATE, RLS negando B/C, lote 1 + 1 + repetição idempotente, preservação A, redistribuição B, fila C, acesso restrito e entrada inválida rejeitada. Execução e log são necessários antes de aprovar; sem GoTrue/REST pós-040 nem teste intersessões. NÃO altera main, Supabase hospedado, Meta, Banco, OpenAI, Frontend ou n8n.


**Evidência executada de I3:** [CI PostgreSQL 17 #39161092070 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39161092070), commit `2a800609acfc3aaf151c29dc0c89a45bfebde9c9`, job `117774376189`; logs auditados: **S1X-01..07 = 7/7 PASS**. O mesmo runner também exercitou S1R-01..09 e S1E-01..07 no seu escopo sintético. Não há cron nem execução automática do reparo pela passagem do tempo; função exige acionamento por executor interno confiável. Sem Auth/REST integrado nem teste intersessões. **NO-GO para produção.**
