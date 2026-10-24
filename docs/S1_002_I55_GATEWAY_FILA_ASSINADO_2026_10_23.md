# S0 + S1-002 / I55 — API assinada de consulta e assunção da fila

**Estado em 24/10/2026:** I55 **validado em CI local descartável**: 11/11 testes unitários, 8/8 E2E I55, 8/8 E2E I53. Não homologado para produção, sem deploy, sem merge e sem uso de dados reais. Código verificado em `ad17444ea64e6bf539e8a579b7019188f999c425`.

**23/10/2026.** Continuidade do I54; S0 e S1 são implementadas pela mesma frente. Ambiente de teste **somente CI local descartável**, sem deploy, merge, WhatsApp, cliente real ou bancos externos.

## Integração

O I54 criou a fila na S0, mas ela ainda não dispunha de API autenticada. I55 acrescenta um gateway HTTP de loopback em `backend/s1_gateway_fila_canonical_local.py`, que valida Bearer de GoTrue e só aceita dois comandos, ambos POST:

- `/s1/fila`, corpo exatamente `{"loja_id":"<UUID>"}`: retorna no máximo 25 itens pendentes com **apenas** `concessionaria_id`, `lead_id`, `ciclo_id` e `versao`. Não retorna telefones, mensagens ou casos de outras equipes; Gestor deve estar ativo e possuir grant vigente para aquela concessionária.
- `/s1/assumir_fila`, corpo `{"loja_id":"<UUID>","ciclo_id":"<UUID>","versao_esperada":1}`: registra assunção **no comando S0 canônico**, com lock no lead, versão CAS, novo caso e atribuição em transação e trilha de auditoria. `CONFLICT` ou caso já criado respondem HTTP 409. Nunca delega um papel administrativo, destinatário ou ator a partir do corpo HTTP.

**Assinatura e autoridade:** domínios separados `FILA55L` e `FILA55C` com identidade ator/sessão verificada independentemente pelo assinador, loja/ciclo/versão assinados, HMAC conferido exclusivamente no custodiante I22 e nonce consumido pelo executor I21 (role NOLOGIN). A ponte PostgreSQL, owned por postgres, confere novamente `auth.sessions` viva, ator cadastrado, alçada de Gestor e delega a assunção ao `prumo_private.s0_fila_assumir` do I54. A sessão ou chave revogada impede nova operação; sem concessão da loja não há listagem nem assunção. Funções internas e tabela de fila permanecem fora de `authenticated` e do login SQL do gateway.

## Limites e validação

`supabase/tests/s1_079_fila_assinada_canonica_local_only.sql` instala o **protótipo de serviço assinado I55** dentro da stack Supabase CLI efêmera, após migrations S0/S1 053 e 054; não é migration pública em produção. A suíte `scripts/test_s1_002_i55_signed_queue_e2e.py` usa o gateway GoTrue/HMAC I37/I53 com oito cenários de aceitação: evento S0; projeção mínima; escopo multi-loja; schema HTTP estrito; claim/CAS e owner único; nonce; revogação de grant no mesmo JWT; impossibilidade de SELECT/RPC direto. `tests/test_s1_002_i55_queue_gateway.py` inspeciona assinaturas e entrada HTTP.

**Ainda não homologado:** implementação distribuída e HTTPS da borda, sessão persistente e KMS/isolamento de hosts, reconciliação de pendência quando outro produtor cria caso, comprovação de primeiro contato/delivery, UI, D2/D3/D4, F03, produção Meta/Banco e aprovação LGPD. Os resultados dos testes serão adicionados após validação no GitHub Actions. A2 segue fechada: Consultor pausado jamais recebe novo atendimento, inclusive manual.

## Evidências

**Histórico de bloqueio inicial do CI (23/10/2026; superado no repositório novo em 24/10/2026):**

- Commit de implementação `0560175332668d1c2c0cb6dfcc0388f7923b4dd5`, seguido de `4aa8cfa30e75b2f2ff04b854a1035a9c5bdab97c` (consulta da fila com `FOR SHARE` na equipe, concessão e loja, serializando revogação durante leitura; rejeição explícita de HMAC nula).
- [GoTrue/E2E #40039146985](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40039146985) e [PG17 #40039147068](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40039147068): **FAILURE sem qualquer etapa registrada nos jobs e logs do job indisponíveis (404 BlobNotFound)**. Reexecução via API solicitada, mas novamente não houve passos com evidência. Não se pode inferir falha ou êxito da implementação.
- Após correção pontual, [E2E #40039422379](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40039422379) e [PG17 #40039422319](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40039422319) também **FAILURE antes de qualquer etapa**. Isto caracteriza bloqueio de validação por infraestrutura/execução do Actions ou outra causa ainda não identificada, **não uma regressão de negócio comprovada**.
- Testes escritos e conectados ao workflow: `tests/test_s1_002_i55_queue_gateway.py` (11 unitários de esquema, assinatura e allowlist de saída) e `scripts/test_s1_002_i55_signed_queue_e2e.py` (8 cenários GoTrue reais locais). **Condição agora satisfeita:** conclusão SUCCESS e logs individuais verificados na execução #40082836279 abaixo.
- Na data daquele bloqueio, I54 permanecia a última camada **de fila** com validação positiva (8+2 testes PG17, 16/16 workflows na evidência I54). I55 é uma implementação adicional sujeita à execução e auditoria de segurança. Não houve merge, deploy ou acesso a Meta/Banco.

**Próxima atividade do mesmo responsável S0/S1:** recuperar a execução dos runners GitHub Actions e confirmar a ponte assinada no GoTrue efêmero; depois finalizar reconciliação de filas obsoletas, hardening de sessão/revogação e UI.

## I55.1 — defesa adicional na borda (24/10/2026)

A resposta do executor assinado agora passa também por uma **allowlist de saída** do gateway: a listagem só permite 25 itens e exatamente quatro campos UUID/versão por item; a assunção só permite o resultado e IDs/versionamento esperados. Uma futura mudança não auditada do `SECURITY DEFINER` não pode encaminhar telefones, mensagens ou campos extras automaticamente. Qualquer resposta divergente falha fechada em HTTP 503. Erros transitórios do PostgreSQL como `40001`/`40P01` não são tratados como proibição HTTP 403: exigem recuperação ou retry seguro. Foram adicionados testes unitários de contrato para saída e mapeamento de erros. **Agora validado no CI local da execução #40082836279.**

## Diagnóstico E2E no novo repositório (24/10/2026)

A primeira execução com Actions operante no espelho ([#40082201339](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40082201339)) aprovou os 11 testes unitários do I55 e chegou à S0 real (`PASS S1QUEUE-157`), mas a primeira consulta autenticada retornou HTTP 403. A causa identificada no fixture foi **a ausência de concessão de Gestor à loja**: o cenário histórico I37 vinculava o Gestor à equipe sem criar um `vinculos_papel_escopo` de papel `gestor` para a concessionária. A política I55 exige corretamente ambas as condições. O fixture E2E foi atualizado para conceder explicitamente esse escopo sintético ANTES da consulta, sem alterar a regra de segurança. A correção foi confirmada na execução #40082836279.

### Reforço do teste de revogação I55

O cenário E2E de revogação foi ajustado para criar uma **terceira pendência sintética ainda sem titular**. A negativa HTTP 403 agora deve ocorrer durante a checagem de concessão da própria assunção, e não por CAS de um caso já atribuído. O teste também verifica que não se cria caso e que a pendência continua disponível após restabelecer o grant. Validado na execução #40082836279.

## Evidências finais I55 — GitHub Actions, novo repositório (24/10/2026)

- [Execução #40082836279 — SUCESSO](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40082836279), commit de código `ad17444ea64e6bf539e8a579b7019188f999c425`. Jobs `http-policy-unit` (`120839735778`) e `e2e-gerencia-local` (`120839735859`): ambos **SUCCESS**.
- **I55 unitário:** 11/11 testes de `TestQueueV55` aprovados, incluindo validação da forma de saída, rejeição de campo sensível extra e distinção entre erros SQL transitórios e negações de acesso.
- **I55 E2E com GoTrue real local:** `PASS S1QUEUE-157` até `PASS S1QUEUE-164`, **8/8**. Cobertura explícita de evento S0, listagem mínima por concessão, Gestor de outra equipe negado, JSON estrito, assunção CAS, nonce anti-replay, revogação de grant em pendência nova e isolamento REST/SQL privado.
- **Regressão I53:** `PASS S1CANON-149` até `PASS S1CANON-156`, **8/8**, incluindo conta preservada na pausa, S0 bloqueando destino pausado e HMAC de domínio separado. Também `PASS S1INTAKE-147/148` para chave revogada e assinador indisponível.
- Execuções anteriores #40082201339 e #40082614227 demonstraram dois **problemas em fixtures E2E**, não exigiram enfraquecer o RBAC: primeiro faltava grant da loja; depois o teste de revogação usava caso já atribuído e recebia CAS 409. Corrigidos respectivamente em `fe0e770` e `ad17444`, com última execução verde.

**Limites ainda abertos:** esta é comprovação local com Supabase GoTrue/HMAC e banco descartável; não prova prontidão de infraestrutura de produção, frontend, paginação real além de 25 itens, reconciliação de fila com casos criados fora do fluxo, nem monitoramento operacional. Nenhuma alteração feita em hospedagem, Meta, Banco ou `main`.

### Resultado complementar I56 (24/10/2026)

A integração anterior I55 (8/8) foi ampliada com a prova S1QUEUE-165 de reconciliação de caso externo: **9/9 E2E GoTrue/HMAC e 11/11 unitários SUCCESS**, [run #40089738334](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40089738334), commit 640ba119. No PG17, [run #40089537969](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40089537969) validou I56 6/6 mais 2/2 corridas com locks reais e regressão I54. Ver [documento I56](S1_002_I56_RECONCILIACAO_FILA_2026_10_24.md). **Somente ambiente descartável; sem produção.**

### Regresso I57 (24/10/2026)

Aplicação do guard canônico de concessão do destinatário S0 (I57) na stack assinada efêmera: [GoTrue/HMAC #40125971536](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40125971536), 9/9 E2E da fila e 8/8 I53, com jobs SUCCESS. O [PG17 #40126423968](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40126423968) aprovou adicionalmente I57 5/5 e 2/2 corridas reais. Fonte [I57](S1_002_I57_GRANT_DESTINO_2026_10_24.md). Não comprova produção.

### Revalidação de autorização I58 — 24/10/2026

A projeção assinada I55 de LIST passou a utilizar o helper privado de autorização de Gestor I58; a assunção da S0 agora revalida o Gestor antes de retornar o CAS de uma fila já consumida. [PG17 #40132128199](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40132128199): **SUCCESS**, I58 6/6 + 2/2 corridas reais. [GoTrue/HMAC #40132414081](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40132414081): **SUCCESS**, I55+I56+I58 11/11 E2E + I53 8/8. [Contrato e evidências I58](S1_002_I58_AUTORIZACAO_GESTOR_FILA_2026_10_24.md). Somente laboratório descartável.
