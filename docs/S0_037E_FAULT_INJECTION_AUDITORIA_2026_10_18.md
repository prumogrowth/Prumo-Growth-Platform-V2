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

**Parecer provisório:** GO somente para ensaio e relatório sintético; NO-GO para mudança de owner e integração/produção.
