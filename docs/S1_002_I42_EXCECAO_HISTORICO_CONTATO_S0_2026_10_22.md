# S1-002 / I42 — exceção por caso com histórico do mesmo contato

**22/10/2026. Escopo:** contrato vigente S1-D12, D13, D18 e D19. **Status:** política candidata [T] executada apenas em PG17 descartável. PR #5 permanece Draft.

## Incremento
`supabase/tests/s1_062_excecao_historico_contato_local_only.sql` executa `BEGIN`, aplica em laboratório as fixtures I53/I54/I55 e cria uma extensão I42 de RLS. Todos os objetos temporários, mudanças de funções/policies e dados sintéticos terminam em `ROLLBACK`. Integrado ao runner `scripts/run-s1-002-i12-local.sh`.

A extensão consulta o vínculo excepcional **ativo** do Consultor com uma atribuição S0 atual, a chefia ativa, a conta ativa, a concessionária e `auth.uid()`. O mesmo contato é identificado pela dupla `(concessionaria_id, lead_id)`. A regra libera **somente leitura contextual** de casos, conversas e mensagens antigos daquela loja, mesmo se o Consultor não tem grant geral. O envio continua autorizado **somente no caso de titularidade corrente**. Inclui vista mínima de ciclo/telefone com filtro por contato e bloqueia leitura irrestrita de coleções S0.

## Cenários de aceitação
- **RED:** a fixture I55 lê apenas o caso corrente, não o histórico.
- **I42-01/02:** após a candidata, o Consultor excepcional lê os dois casos do mesmo contato na loja A, mas não outro contato da loja A nem o mesmo telefone na loja B; não enxerga `leads_loja`, `ciclos_comerciais`, `concessionarias`, `canais_loja` brutos.
- **I42-03:** mensagem simulada no caso antigo negada; no caso corrente permitida.
- **I42-04/05:** revogação auditada corta, no mesmo estado confirmado, acesso ao caso atual, ao histórico e à escrita, mesmo que a atribuição física ainda esteja ativa (necessita continuidade gerencial).
- **I42-06:** nenhum grant de concessionária ao Consultor excepcional e eventos auditados; `ROLLBACK` integral.

## Gatilhos de integração S0
**Não promover a SQL candidata** antes de resolver a correção RLS interequipes I41, autorização por contato histórico de todo Consultor titular (com e sem exceção), leitura de mensagens F01 sem `caso_id`, dados de ciclo/lead/relatórios, privacidade D3/D4, troca/revogação de chefia e prova de auth GoTrue/PostgREST. O I55 sobrescreve guardas S0 apenas na fixture, o que não é autorização para a S1 editar essa frente em produção.

A exceção deve ser derivada de um **entitlement canônico S0 vinculado a uma atribuição**, não de um grant de loja nem da política de assinatura WhatsApp. Não resolver A2 por inferência: transferência manual a Consultor com intake pausado permanece [R].

## Evidência de teste confirmada
[GitHub Actions PG17 #39868254265 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39868254265), job `120135831929`, código testado no commit `5cc2eae1c60d933eca17835017f74648849cb2c4`. Logs observados: `I42-RED`, `PASS I42-01/02`, `PASS I42-03`, `PASS I42-04/05`, `PASS I42-06/ROLLBACK`. Regressões `I41-01..07` e concorrência multissessão `I40-01..04` continuaram aprovadas. A primeira execução `#39867958800` falhou por parêntese extra na policy de mensagens; corrigido no commit acima, sem ampliar privilégios. Essa evidência é **somente PG17 descartável**, não homologação S0/GoTrue/PostgREST.
