# S0-037E — injeção de falha na auditoria da execução assinada C08/C07

**Data:** 18/10/2026. **Estado:** prova sintética proposta, aceite condicionado ao CI. PR #1 continua Draft. Não há migration nova, nenhuma role persistente, nenhum emissor de token operacional, chave de produção, Graph, Banco ou Supabase hospedado.

## Hipótese, arquitetura vigente e limite

A S0-037D comprovou que uma capacidade protegida (ação, loja, alvo, versão e transação) pode restringir DML de laboratório mesmo quando uma GUC do cliente é falsificada, **mas não trouxe um emissor de capacidade autenticado nem substituiu as wrappers comerciais `SECURITY DEFINER postgres`**. S0-037C comprovou caminho assinado HMAC/nonce→sessão→gestor→C08/C07→auditoria, ainda com as duas wrappers comerciais legadas em `postgres`.

Um emissor operacional seguro exigirá solução para identidade de chamador, sessão revogada, HMAC, nonce, autorização comercial, owner comercial mínimo, logs protegidos e concorrência sem conceder DML ao gateway. **Não se pode supor que uma capability TEMP emitida por fixture `postgres` seja um novo mecanismo de segurança.**

O incremento S0-037E aumenta a evidência sobre a cadeia vigente antes de qualquer mudança arriscada: **uma indisponibilidade da auditoria privada depois das alterações de domínio deve fazer rollback de tudo, inclusive a reserva HMAC do nonce**. É uma prova de atomicidade e recuperação, não entrega de emissor novo.

## Ensaio implementado — arquivo de teste existente, sem migration

Em `supabase/tests/s0_037c_execucao_assinada_c07_c08.sql`, dentro de `BEGIN ... ROLLBACK` e com as mesmas fixtures HMAC exclusivamente fictícias, adicionamos:

- **AUTHATOM-01:** inserir uma trigger **só no banco descartável**, que lança `AUDITORIA_INDISPONIVEL_FIXTURE` ao tentar gravar `prumo_private.auditoria_gateway_s0`. Invocar cancelamento assinado C08 com envio fictício agendado e encerramento C07 de pendência recém-criada, ambos com gestor/sessão/prova HMAC válidos. As chamadas **devem falhar no estágio final da auditoria**.
- **AUTHATOM-02:** após as falhas, conferir plano/envio C08 e pendência C07 inalterados, ausência de eventos de cancelamento, ausência de auditoria comercial ou de gateway, e ambos os nonces não consumidos.
- **AUTHATOM-03:** remover a trigger de falha e **repetir exatamente os mesmos nonces/assinaturas**. As duas operações devem aplicar uma vez, com trilhas comerciais e registro de nonce/auditoria consistentes. Nenhum caso toca a loja B. O teste antigo de sessão revogada continua executado com contagem total atualizada.

Toda escrita e a própria trigger de teste desaparecem com o `ROLLBACK`, e o runner restringe a execução ao banco descartável `prumo_s0_test_*` em loopback. Nenhuma trigger é instalada em migration nem no Supabase hospedado.

## Evidência a registrar depois da execução

Preencher o SHA/CI final somente com logs confirmados `AUTHATOM-01/02/03`, `OWNER37C-01..05`, `AUD37-01..03`, `OWNER37D-01..04` e regressões do runner.

## Pendências e gates

- **Não existe ainda emissor confiável de capability para owner de domínio reduzido.** A validação assinada atual depende do `prumo_s0_signer` e das wrappers comerciais `SECURITY DEFINER postgres`; a S0-037D só possui emissor fictício privilegiado.
- Cenários de falha **entre** reserva de nonce, sessão e locks, auditoria e commit devem ser repetidos sob eventual desenho de novo owner — além de concorrência em conexões distintas e teste local GoTrue/PostgREST.
- Não usar assinatura de backend não verificada, `BYPASSRLS`, acesso direto do gateway a tabelas, `SET ROLE` de usuários como autenticação, GUC fornecida pelo chamador, ou um helper postgres oculto para declarar privilégio mínimo.
- Meta C07 real não segue deste teste: `statuses[].id` é ID de mensagem, não de ocorrência; WA-01C, DEC-WA-04/06, armazenamento protegido e ACK COMMITTED ainda carecem de gate. DEC-WA-05 mantém titularidade Meta por concessionária.
- PRs #1/#2 Draft, sem merge; sem credenciais reais, deploy ou migrações remotas.

## Fechamento do incremento — evidência verificada

**[CI PostgreSQL 17 #39130947663 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39130947663)**, SHA de código/fixture testado `59331c55975e2694a1e7d057d3ef16f3783c9331`. Logs consultados: **AUTHATOM-01/02 PASS** (falha de auditoria injetada nega C08/C07 e reverte plano/envio/pendência/eventos/nonces/auditoria), **AUTHATOM-03 PASS** (mesmo nonce e assinatura aceitos após retirada da falha, exatamente uma aplicação de cada operação), **OWNER37C-01..05 PASS**, **AUD37-01..03 PASS**, OWNER37D-01..04, demais regressões do runner e **24 testes Python OK**. Sem erros.

Não houve mudança em migration, funções comerciais, papel técnico real, HMAC real ou esquema hospedado. A trigger e as fixtures de laboratório são revertidas via `ROLLBACK`; após a queda, o retry usa **a mesma prova sintética**, não credenciais de Meta. As contagens da auditoria privada e do ledger de nonce foram aumentadas de cinco para sete somente dentro do teste transacional por conta das duas operações novas válidas.

**Parecer final restrito:** a cadeia assinada **existente**, ainda amparada em wrappers `SECURITY DEFINER postgres`, tem atomicidade de domínio/nonce/auditoria nos dois cenários adicionais injetados. **Não** foi implementado emissor de capacidade operacional de menor privilégio e **não** foi demonstrada transferência segura dos wrappers. A prova S0-037D de RLS continua separada. Último GoTrue/PostgREST local integrado do baseline [#39122948236 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122948236); não foi reexecutado, pois o incremento não altera runtime.

**GO** apenas para projetar e testar, em laboratório, um emissor confiável e a redução real de owner ou avançar a S1 visual com dados fictícios. **NO-GO** para publicação de grants, merge, Supabase hospedado, Meta, Banco ou produção.
