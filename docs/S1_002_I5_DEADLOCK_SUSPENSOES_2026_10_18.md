# S1-002/I5 — Contenção em suspensões simultâneas | 18/10/2026

**Proprietário:** somente frente S1-002. [D-negócio] continuidade da redistribuição automática; [P] mitigação transacional em sandbox; [V] execução real, escala e autorização de RH. Projeto sem merge/deploy.

**Risco descoberto por revisão de locks:** duas transações podem suspender operadores O1/O2 ao mesmo tempo. Se cada uma segura a linha de equipe própria e tenta usar o outro como substituto, uma seleção bloqueante cria interbloqueio PostgreSQL. O contrato exige nunca transferir caso a operador sendo desativado.

**Correção candidata em migração 041:** SELECT do receptor dentro de `prumo_private.s1_remanejar_ator` usa `FOR SHARE OF e,v,l SKIP LOCKED`. A seleção ignora destinatário com linha de equipe ou concessão bloqueada e prefere outro operador Prumo ativo autorizado **da mesma concessionária**. Se não houver substituto livre, encerra a antiga atribuição na mesma transação, registra motivo em histórico e fila protegida; não marca `perdido`, `vendido` nem altera status comerciais. Quem estiver temporariamente bloqueado não é marcado inativo por inferência.

**Teste de duas conexões independentes:** `scripts/test_s1_002_simultaneous_suspensions.sh`; S1D-01..05 valida destino alternativo, nenhum deadlock, fila protegida quando todos os alternativos estão sendo suspensos, RLS e idempotência. Antes de conferir CI, todos permanecem [P]. Testes S1C-01..05 já passaram na [CI #39163239631](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39163239631).

**Limite:** nenhuma fila protegida é atendida automaticamente com a migração 041; exige desenho do fluxo de recuperação e capacidade/escala, além de Auth/REST/worker real. Nenhuma regra bancária, Meta ou OpenAI é alterada.
