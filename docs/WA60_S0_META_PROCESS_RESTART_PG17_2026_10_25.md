# WA-60 — Persistência e idempotência forense entre processos Node independentes (PG17)

**25/10/2026. Apenas S0/Meta em banco descartável e listeners `127.0.0.1`. Não é serviço Meta de produção.**

## Hipótese

Reiniciar ou matar um processo HTTP não deve redefinir a identidade de um evento forense. O estado relevante de arquivamento é transacional e persistido no PostgreSQL; as operações de rede e as chaves do processo em memória são descartáveis. Se o processo morrer **antes do COMMIT**, o evento não fica arquivado; se morrer **após o COMMIT e antes da resposta**, uma retransmissão em novo processo deve encontrar o evento, classificá-lo como replay e não gerar segunda observação.

## Implementação

`supabase/tests/s0_wa_064_pg17_restart_worker.mjs`: executável isolado em **processo filho Node independente**; conecta como cliente sintético restrito ao banco `prumo_s0_test_ci`. Constrói novamente o gate de assinatura de bytes WA46, ticket WA45/44, ponte WA56 e receptor HTTP local WA57/59. O parent fornece somente chaves HMAC aleatórias sintéticas e uma senha efêmera para o laboratório. Sua emissão JSON `ready` contém PID/porta loopback, e logs privados do child registram somente referência de evento/resultado — nunca chaves. Modos `normal`, `precommit` e `postcommit` executam respectivamente uma escrita padrão, `SIGKILL` antes da query SQL e `SIGKILL` **após** o retorno da query SQL bem-sucedida, mas antes de resolver a resposta HTTP. Encerramento voluntário via `STOP`, sem listeners residuais.

`supabase/tests/s0_wa_065_http_process_restart_pg17.test.mjs`: 24 provas novas, executadas **após** as regressões históricas WA39–59 e selagem WA55. Verifica banco permitido, primeiro arquivamento e replay no mesmo PID, encerramento limpo e novo PID com **nova chave** do laboratório mantendo somente uma observação no ledger, evento distinto registrado em processo sucessor, queda `SIGKILL` pré-COMMIT sem inserção, reinício e primeira gravação, queda pós-COMMIT com resposta HTTP destruída e ledger persistido, reinício/replay, e **dois processos simultâneos de PIDs e chaves distintos** arquivando o mesmo evento via HTTP: uma observação original, um replay, nenhuma duplicação. Inclui HMAC incorreto, shadow inexistente e ausência de flags comerciais.

Não há migração nem alteração em tabelas/códigos de produção. A WA60 amplia somente testes e fixtures de laboratório. Regra de contagem: base WA39–59 **611**; WA60 **24**; total **635** apenas depois de CI `SUCCESS` no SHA exato e marcadores únicos conferidos.

## Limites e diretriz Prumo Growth

A prova cobre reinício de **processo**, não falha de máquina, recuperação de cluster, durabilidade contra perda do volume PostgreSQL, disponibilidade de rede ou autenticação IAM/M2M de verdade. Processo e listener não são publicados; HTTP 202 é confirmação de laboratório, não ACK real da Meta. Não habilita Graph, envio de mensagens, retry comercial, mudanças em S1, Supabase hospedado, PR merge ou `main`.

A Issue #3 audita **workflows S1** e **não autoriza** otimização ou alteração da S1. O teste WA60 foi acrescentado ao workflow próprio da S0, sem suprimir as provas anteriores. Futuras integrações exigem branch específica, validação e autorização prévias.

**Dependência da S1:** nenhuma para a WA60.

**Próxima candidata WA61:** reconciliação forense sob reinício associada a revogação de chave e mudanças de vínculo/estado entre tentativas, com testes adversariais sem autorizar mutações comerciais.
