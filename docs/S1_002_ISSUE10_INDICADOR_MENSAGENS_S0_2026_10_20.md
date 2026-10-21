# S0 + S1-002 / issue #10 — indicador único de mensagens (20/10/2026)

**Protótipo SQL exclusivo de sandbox**, não migration operacional, não endpoint UI, não integração Meta. Mantém branch `feat/s1-002-equipe-prumo`, PR #5 Draft; não altera Supabase hospedado nem S0 base.

## Contrato da decisão de produto

O frontend exibirá um único indicador com três saídas técnicas, correspondentes a **dois estados de alerta** e a nenhum alerta: `COUNT` com quantidade de mensagens de entrada não lidas, `DOT` (bolinha sem número, de cor a definir no frontend) quando não há entrada não lida mas existe mensagem lida sem resposta humana posterior, ou `NONE` quando não há nada pendente. `COUNT` tem precedência sobre `DOT`. A supervisão da conversa **nunca** altera o registro de leitura do operador.

## Fixture S0 I36

`supabase/tests/s1_056_issue10_indicadores_s0_local_only.sql` utiliza as tabelas S0 existentes e acrescenta três objetos privados, com RLS e sem acesso `anon/authenticated/service_role`:

- `s0_ordem_mensagem_56`: sequência interna por concessionária/conversa, gerada em trigger `AFTER INSERT` com lock da conversa; totalização independente dos timestamps e UUIDs. Ainda não representa ordem certificada por Meta.
- `s0_leituras_operador_56`: marca inbound individualmente como lido pelo **ID exato da atribuição corrente** e operador, com unicidade para retry idempotente. Registrar leitura de um ID de outra conversa é recusado. O marco de leitura não altera a mensagem fonte.
- `s0_visitas_supervisor_56`: trilha independente de visita/visualização pelo gestor da mesma equipe, sem escrita nos marcadores do operador.

As funções **postgres-only** `s0_marcar_leitura_operador_fixture_56`, `s0_visita_supervisor_fixture_56` e `s0_indicador_operador_fixture_56` simulam ações do frontend e retornam estados com escopo de loja, caso, conversa, operador e atribuição corrente. `DOT` exige que exista inbound lido para o qual ainda não há mensagem de saída humana do mesmo operador, na conversa/caso com ordinal posterior. Ao inserir saída sintética subsequente, o estado torna-se `NONE`; novo inbound reinicia `COUNT`.

O marcador é próprio da **atribuição**. Quando o caso troca de titular, a atribuição nova não herda explicitamente o registro de leituras do operador anterior: por hipótese de segurança, começa com todas as entradas anteriores do caso ainda não lidas. Esta opção deve ser confirmada na futura reunião de perguntas; não se trata de decisão de negócio já aprovada.

## Critérios de aceite

`supabase/tests/s1_056_issue10_indicadores_s0_aceite.sql` visa 18 gates: caso sem mensagens `NONE`, 2 entradas `COUNT(2)`, supervisor sem alterar leitura, leitura parcial `COUNT(1)`, todas lidas `DOT`, idempotência, resposta posterior `NONE`, nova entrada `COUNT`, supervisão posterior mantendo contagem, nova leitura `DOT`, rejeição de mensagens/casos alheios, gestor fora da chefia, mudança de titular, leitura reiniciada no novo operador, antigo titular bloqueado e RPC privada negada. O CI S1 da issue #10 roda regressões I11/I12 e 23 gates S0/S1 com 4 corridas e 20 gates RLS excepcional antes dos 18 novos.

## Limitações bloqueantes

A resposta humana é considerada por **inserção sintética no PostgreSQL**, não por confirmação de envio/entrega pela Meta. O indicador não foi testado com réplicas, múltiplos provedores, eventos tardios/out-of-order, status de entrega, histórico de conversa com `caso_id` nulo ou anexos. Não há interface visual, cores, notificações push, contadores em tempo real, JWT/GoTrue para registrar leitura nem RLS produtiva para projeção: são funções apenas de laboratório. Uma leitura que concorra com redistribuição precisa de teste de múltiplas sessões antes de deploy. A política de leitura após transferência é **hipótese**. Os estados `COUNT`, `DOT`, `NONE` não significam envio de WhatsApp.

**NO-GO produção/merge/deploy**, S0 hospedado intacto e sem porcentagem global do projeto.

## Evidência CI revisada — aprovado apenas em sandbox

**[GitHub Actions #39517258320 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39517258320)**, código ensaiado SHA `69fc6f51eacef79bfb15991a93110ad406da398a`, job `118952297289`, logs e marcadores confirmados: **MSG56-01..18 = 18/18 PASS**, **EX55-01..20 = 20/20 PASS**, **ISSUE10-01..23 = 23/23 PASS**, **ISSUE10R-01..04 = 4/4 PASS**. Todas as regressões S0/I11/I12 históricas foram executadas antes das fixtures issue10, com resultado global verde.

`MSG56` confirmou `NONE` sem entradas, `COUNT 2` e `COUNT 1` em leituras parciais, `DOT` sem número quando toda entrada foi lida mas não respondida, `NONE` após saída humana sintética posterior, nova entrada após a resposta retornando a `COUNT`, segunda leitura `DOT`, leitura de gestor isolada da leitura do operador, marcador idempotente, bloqueio de outra conversa/operador/equipe, projeção de novo titular independente e antigo titular bloqueado. A fixture `s1_056` não é endpoint e depende de confirmação de negócio sobre herança de marcadores.

**Histórico de falha corrigida:** [run #39517065926](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39517065926) falhou ao qualificar indevidamente a expressão SQL `COALESCE` como `pg_catalog.coalesce` no trigger de sequência; foi corrigido e executado novamente. O único aceite do indicador é o run verde #39517258320.

**NO-GO produção/merge/deploy:** ainda faltam frontend, verificação de entrega pelo provedor, saída humana em circuito real, JWT/GoTrue/RLS de leitura na UI, controle de eventos fora de ordem, logs duráveis e testes de concorrência envolvendo leituras.

## Ratificação visual — 20/10/2026

As duas situações de alerta (`COUNT` e `DOT`) são **semanticamente distintas**, mas **não há decisão obrigatória de cores diferentes**. A mesma cor ou cores diferentes são aceitáveis até definição visual posterior. A referência ao WhatsApp inspira o formato do aviso, **não** os significados, cores ou estados de leitura daquele aplicativo. O contrato SQL não deve persistir cor nem assumir regra de design; ele emite somente `state`, `unread_count` e o marcador de resposta pendente.
