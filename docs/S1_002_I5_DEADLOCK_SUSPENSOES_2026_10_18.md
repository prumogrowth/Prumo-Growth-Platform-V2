# S1-002/I5 — Contenção em suspensões simultâneas | 18/10/2026

**Proprietário:** somente frente S1-002. [D-negócio] continuidade da redistribuição automática; [P] mitigação transacional em sandbox; [V] execução real, escala e autorização de RH. Projeto sem merge/deploy.

**Risco descoberto por revisão de locks:** duas transações podem suspender operadores O1/O2 ao mesmo tempo. Se cada uma segura a linha de equipe própria e tenta usar o outro como substituto, uma seleção bloqueante cria interbloqueio PostgreSQL. O contrato exige nunca transferir caso a operador sendo desativado.

**Correção candidata em migração 041:** SELECT do receptor dentro de `prumo_private.s1_remanejar_ator` usa `FOR SHARE OF e,v,l SKIP LOCKED`. A seleção ignora destinatário com linha de equipe ou concessão bloqueada e prefere outro operador Prumo ativo autorizado **da mesma concessionária**. Se não houver substituto livre, encerra a antiga atribuição na mesma transação, registra motivo em histórico e fila protegida; não marca `perdido`, `vendido` nem altera status comerciais. Quem estiver temporariamente bloqueado não é marcado inativo por inferência.

**Teste de duas conexões independentes:** `scripts/test_s1_002_simultaneous_suspensions.sh`; S1D-01..05 valida destino alternativo, nenhum deadlock, fila protegida quando todos os alternativos estão sendo suspensos, RLS e idempotência. Antes de conferir CI, todos permanecem [P]. Testes S1C-01..05 já passaram na [CI #39163239631](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39163239631).

**Limite:** nenhuma fila protegida é atendida automaticamente com a migração 041; exige desenho do fluxo de recuperação e capacidade/escala, além de Auth/REST/worker real. Nenhuma regra bancária, Meta ou OpenAI é alterada.


## Evidência integrada S1-002/I4–I5 — 18/10/2026

[**GitHub Actions PG17 #39164266141 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39164266141), commit `326b1713196e510c0f48760e6e368e0677a263ec`, job `117783812725`; logs verificados: **S1E-01..07 (7 PASS), S1R-01..09 (9 PASS em cada uma das duas execuções), S1X-01..07 (7 PASS em cada uma das duas execuções), S1C-01..05 (5 PASS), S1D-01..05 (5 PASS)**. Regressão S0 de base rodou antes da 038; a suíte I2/I3 foi **reexecutada após a migration 041** e passou. Nenhum deadlock/erro inesperado no log; a recusa `PROFISSIONAL_PRUMO_INELEGIVEL` nos testes negativos é esperada. Os testes anteriores #39163601666/#39163765511 falharam por consulta de coluna inexistente ou contagens não isoladas; foram corrigidos e retestados, não são evidência de código produtivo aprovado.

**Limites:** testes locais/sintéticos apenas. Não há GoTrue/REST real após 041, autorização RH confiável, regras de escala/turno, job que drena fila protegida, cron de validade, concorrência distribuída ou cargas reais. Migração 041 evita interbloqueio por candidato de equipe/concessão temporariamente bloqueado usando `SKIP LOCKED`; se não existe destinatário desbloqueado, o caso permanece protegido, sem perda de história. **Sem merge, Supabase hospedado ou alteração das demais frentes; percentual global não atualizado.**
