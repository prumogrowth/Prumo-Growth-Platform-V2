# Auditoria retroativa S0-037A/B/C e MAPA_MENTAL — 18/10/2026

**Escopo:** revisão independente do trabalho comercial S0-037A, S0-037B e S0-037C ainda não auditado após seu aceite, do runner PostgreSQL 17 e do `docs/MAPA_MENTAL.md`. Base do PR #1 antes deste ensaio: `ef16defa8bda2fd78003de6dccf0a5bbd633cb0e`. PR #1 e #2 Draft, sem merge. Não houve leitura/escrita de mensagens de clientes, alteração de canais, migrations hospedadas ou deploy.

## Constatações

**AUD37-01 — cobertura negativa insuficiente em S0-037C.** O teste `OWNER37C-05` já comprova sessão inexistente/revogada, e `OWNER37C-03` nega loja B com gestor A, mas nenhum dos dois afirmava explicitamente que uma **prova HMAC válida para ator A e sessão pertencente a B** deveria ser rejeitada, nem que **gestor B com sessão válida** continua proibido de escrever na loja A. São lacunas de regressão, **não uma vulnerabilidade demonstrada**, porque o código verificado em `gateway_*_s0` exige `auth.sessions.id=p_sessao AND user_id=p_ator`, e o domínio exige vínculo de gestor ativo na loja.

**AUD37-02 — replay C07 com payload divergente não coberto no teste completo assinado.** A 037C já testa nonce repetido C08 e duas decisões C07, mas não tinha teste posterior de C07 `ALREADY_APPLIED` com novo nonce e **mesma** decisão completa, versus `CONFLICT_VERSION` para decisão divergente sobre a mesma pendência. O código de domínio 020 compara ator, decisão, justificativa e envio antes de autorizar o replay. Cobertura faltante, **não defeito de domínio demonstrado**.

**AUD37-03 — limite de evidência S0-037B.** Os `OWNER37B-01..05` funcionam somente com role e políticas transitórias de loja A, sem HMAC nem sessão; isso está explicitamente documentado. `OWNER37C-01..05` exercitam cadeia HMAC real do simulador, **mas sob as wrappers comerciais legadas `SECURITY DEFINER postgres`**. Os dois testes são complementares, não equivalem à homologação de uma role de domínio sem `postgres`. Não promover a matriz 037B como grants operacionais.

**AUD37-04 — mapa mental e PR #2.** O `MAPA_MENTAL.md` recebeu atualização posterior de acompanhamento WA-01–04C e deixou claro que evidências locais Node e credenciais propostas **não** são ambiente Meta real nem migração Supabase. Documentos PR #2 `wa04b-get-post-roteamento-hmac-v0_1.md`, `wa04c-ciclo-credenciais-sem-token-v0_1.md`, `wa03b-auditoria-pendencias-e-reparos-v0_1.md` conferem os números 167/167, 13/13 e 120/120 nas suítes declaradas, **sem CI remoto dessas suítes**. Nenhuma prova Meta `COMMITTED`, Graph operacional ou token definitivo liberado. DEC-WA-04 e 06 seguem pendentes; DEC-WA-05 trata somente titularidade por concessionária.

## Reparo de auditoria — estritamente sintético

Ampliar `supabase/tests/s0_037c_execucao_assinada_c07_c08.sql` **dentro do mesmo BEGIN/ROLLBACK** sem alterar migrations nem o runtime:
- **AUD37-01:** assinatura válida com ator A, sessão B → `SESSAO_INATIVA`; assinatura válida com ator B/sessão B e loja A → `FORBIDDEN_SCOPE`;
- **AUD37-02:** C07 `VINCULAR_SINTETICAMENTE` repetido pelo mesmo gestor, mesmo comentário/envio e novo nonce → `ALREADY_APPLIED`; mesma pendência com decisão divergente e novo nonce → `CONFLICT_VERSION`;
- **AUD37-03:** confrontar contagem de nonces e auditorias com os resultados, garantindo rollback integral das tentativas recusadas e ausência de evento/associação duplicados.

Nova prova de replay C07 idempotente gera **um registro a mais** de auditoria de gateway e **um nonce a mais**, sem segunda associação C07. Ajustar somente o contador final `OWNER37C-05` de 4 para 5; manter todos os critérios comerciais anteriores.

**Gate de aceite:** registrar SHA, CI PG17 e marcadores AUD37-01..03 em `tests/S0_ACEITE.md` e `docs/MAPA_MENTAL.md` **apenas após sucesso**. O workflow Auth/REST local pesado não deve ser executado só por alteração de fixture, pois nenhuma migration, função, política ou privilégio persistente foi modificado; referenciar separadamente a última baseline `#39122948236`.

## Proibições mantidas

Sem mudança de owner das wrappers comerciais, sem `BYPASSRLS`, sem nova role/conta persistente, sem RPC pública, sem Meta/Banco/OpenAI real, sem token, sem merge, sem hosted Supabase e sem produção. A S0-037D de redesenho de privilégios permanece **não iniciada** até o fechamento desta auditoria.

## Fechamento — resultado confirmado

**[PostgreSQL 17 #39128133133 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39128133133)**, commit de testes `2c2d81311b1bd275fb4364cd4fa422d1efb9e659`. Logs: AUD37-01..03, OWNER37C-01..05 e demais regressões PASS; 24 testes Python OK.

- AUD37-01: sessão de outro ator recusada por SESSAO_INATIVA; gestor de outra loja recusado por FORBIDDEN_SCOPE, mesmo com assinatura de teste válida.
- AUD37-02: replay idêntico de C07 com novo nonce retorna ALREADY_APPLIED; decisão divergente na versão encerrada retorna CONFLICT_VERSION.
- AUD37-03: cinco nonces aceitos e cinco registros de gateway, incluindo replay idempotente; tentativas negadas não geram registro nem segunda associação C07. OWNER37C-05 permanece PASS após ajuste da contagem de auditoria.

**Conclusão:** lacunas de cobertura supridas sem alterar migrations, funções comerciais ou proprietários. Não foi reproduzido desvio de autorização nesses cenários. A aprovação é apenas sintética: os proprietários comerciais postgres continuam pendentes de redesenho, assim como DEC-WA-04/06 e a integração Meta/C07 real. A execução Auth/REST local mais recente da baseline é [#39122948236](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122948236); não foi repetida porque não houve alteração do runtime. MAPA_MENTAL.md sincronizado com o marco de auditoria. 
