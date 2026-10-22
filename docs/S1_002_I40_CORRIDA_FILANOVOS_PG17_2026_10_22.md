# S1-002 / I40 — corrida multissessão de lead novo e fila sem titular

**22/10/2026 — escopo:** S1-002, validação em PostgreSQL 17 descartável. Contrato S1-D06–D09/D19. **Somente laboratório, sem migration homologada.**

## Implementação
- `supabase/tests/s1_059_proto_fila_novos_setup_local_only.sql`: extração das MESMAS funções e filas I39, reutilizadas pelo teste sequencial e pelas conexões concorrentes.
- `supabase/tests/s1_059_novos_leads_fila_cross_team_local_only.sql`: I39 mantém sua execução `BEGIN/ROLLBACK` com o módulo compartilhado.
- `supabase/tests/s1_060_fila_race_seed_local_only.sql`: dados fictícios em PG17, três casos S0 sem titular, dois Gestores com grant de mesma concessionária, terceiro sem grant, Consultor com intake pausado.
- `scripts/test_s1_002_queue_race.sh`: guarda anti-DB remoto (`localhost/127.0.0.1/::1`, DB `prumo_s0_test_*`), duas conexões `psql` simultâneas e terceira conexão para observar `pg_stat_activity.wait_event_type='Lock'`. Não aceita apenas execução sequencial.
- `scripts/run-s1-002-i12-local.sh`: roda I40 após regressão I39.

## Critérios da prova
1. Duas equipes/Gestores autorizados disputam o mesmo lead novo: primeiro commit cria titular, segunda transação bloqueia em lock de caso S0 e falha com `FILA_CAS_OBSOLETO`.
2. Redistribuição automática e assunção por Gestor disputam outro lead: mesma exclusão com caso S0 como lock, Consultor elegível titular ao fim; Gestor não substitui título já confirmado.
3. Gestor sem grant daquela concessionária não assume o lead remanescente.
4. Invariantes após ambos: dois casos com **um titular ativo cada**, terceiro segue `PENDENTE` sem titular, versões de fila corretas, conta ativa.

## Execução confirmada
[GitHub Actions PG17 #39856679877](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39856679877): job `120097068962`, teste I40 executado sobre SHA `a6ab69e981cd19ae7474a1ea0411b1fc2dfc1007`. Logs: `PASS I40-01`, `PASS I40-02`, `PASS I40-03/04`, `PASS I40`; ambos os competidores realmente bloquearam (`pg_stat_activity.wait_event_type='Lock'`) e o perdedor recebeu `FILA_CAS_OBSOLETO`. I38-GREEN01–04 e I39-01–08 permaneceram aprovados. Execução prova apenas o fixture PG17; nenhuma homologação S0/Meta/GoTrue de produto.

## Limites de homologação
A fila `s1_fila_novos_59` é uma **fixture de laboratório** criada em DB descartável; não define o modelo de domínio final, não é fila canônica S0, não aplica autenticação GoTrue ou integra Meta. `postgres` como executor da função não substitui identidade/capacidade autenticada. Concorrem sessões PostgreSQL reais, mas sem cliente REST e sem carga distribuída/stress/isolamento serializable. A validação garante comportamento apenas na implementação simulada e na corrida observada, não garante propriedades de produção de S0.

**Antes de integrar:** revisar/RLS I38, alinhar contrato com S0, tratar fila canônica, exceção de caso para Consultor sem grant, redistribuição de carteira com prova de início humano e corrida revogação/intake. Manter PR #5 em Draft; não alterar S0, bancos hospedados ou branches alheias.
