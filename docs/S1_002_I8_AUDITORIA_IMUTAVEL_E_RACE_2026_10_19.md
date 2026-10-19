# S1-002/I8 — Integridade dos históricos e corridas de status | 19/10/2026

**Fronteira:** exclusivamente S1-002, branch Draft PR #5. Oito estados comerciais, ordem de negócio e C02/C04–C09 seguem sob S0. SQL apenas para PostgreSQL 17 descartável. Nenhum dado real, Meta, OpenAI, Supabase hospedado ou frontend.

## Por que este incremento

Na auditoria I2–I7, a frente provou remanejamento, fila protegida e atendimento humano pós-venda com dados fictícios. Porém as tabelas S1 de eventos de equipe, histórico de remanejamento e histórico de recuperação ainda permitiam UPDATE/DELETE/TRUNCATE por operação privilegiada. Isso é diferente de serem *append-only*: revogar ao usuário autenticado não impede uma rotina interna privilegiada de apagar registros por engano.

A migração 045 adiciona trigger proibitivo para UPDATE, DELETE e TRUNCATE nas **três trilhas**:
- `public.equipe_prumo_eventos_s1`;
- `prumo_private.s1_remanejamento_historico`;
- `prumo_private.s1_recuperacao_fila_historico`.

INSERT continua permitido aos fluxos internos existentes; as movimentações não passam a alterar status comerciais nem deixam de produzir auditoria. A fila **operacional** `s1_remanejamento_pendencias` permanece mutável, pois é consumida nas reatribuições. Nenhuma concessão pública é introduzida. Não se promete inviolabilidade contra DBA/superusuário capaz de desabilitar triggers, restaurar backups ou remover a função. Retenção/LGPD e evidência criptográfica, se exigidas, são questões [R/V].

## Verificações planejadas

S1H-01..08: INSERT normal de auditoria, suspensão cria histórico/fila, ativação recupera e cria histórico, tentativas de UPDATE/DELETE/TRUNCATE (inclusive `postgres` comum) rejeitadas nas três tabelas, entradas anteriores intactas, operador autenticado com leitura legítima do caso mas **sem** acesso direto a eventos RH. Não confundir simulação de role PostgreSQL com GoTrue, token JWT real ou Data API.

S1SC-01..04: duas conexões independentes, uma delas simulando uma atualização de status do S0 **via SQL de fixtures**, outra realizando suspensão S1, e um segundo par competindo com recuperação da fila. Testa snapshot comercial após esperar por commit e preserva retorno humano `retorno_pos_venda`; não finge testar API bancária ou função S0 inexistente. **Somente PG17 local**.

## Gates de produção ainda abertos

Autenticação efetiva Supabase GoTrue/REST, ator autorizado a suspender, equipe por turno/capacidade, fila visível com autorização de gestor, recuperação agendada, revisão jurídica da retenção de eventos, teste de conciliação com workers S0 e mudanças bancárias reais. Não fazer merge/deploy sem essas provas e aceite dos responsáveis.


## Resultado verificado do incremento I8 — 19/10/2026

[**GitHub Actions PostgreSQL 17 #39229666792 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39229666792), commit ensaiado `51025c6e578dc67031c23bf7233d9866da017440`, job `117984297521`: logs consultados e marcadores conferidos: **S1H-01..08 = 8/8 PASS**, **S1SC-01..04 = 4/4 PASS**; também passaram regressões S1E 7/7, S1R 9/9 em 3 passagens, S1X 7/7 em 2 passagens, S1C 5/5, S1D 5/5, S1Q 10/10 em 2 passagens, S1QC 4/4, S1B 10/10 em 2 passagens, AUD1 7/7 e AUD2 5/5. Ausência de erros SQL inesperados nos marcadores; corridas no script representam UPDATE comercial sintético e não API bancária real.

**Conclusão estrita:** proteção append-only aplicada e testada nas três trilhas S1, permitindo inserts legítimos; simultaneidade demonstrada somente nas duas ordenações construídas. **Não certifica isolamento contra superuser que desabilite triggers, tráfego distribuído, serviço GoTrue/REST de verdade, segredo de produção ou autorização de RH.** Status comercial do ciclo permanece S0. Sem merge, deploy, Supabase hospedado ou dados reais.
