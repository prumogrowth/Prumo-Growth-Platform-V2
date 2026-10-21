# WA-15C — primeira prova integrada TypeScript Meta → PostgreSQL S0-042

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Data:** 20/10/2026. **Status:** gate de laboratório executado e aprovado. PR #2 e PR #1 continuam **Draft**, sem merge, deploy, Meta Graph, banco financiador, tokens ou dados reais.

## Evidência definitiva

[GitHub Actions — run 39401664926](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39401664926), `conclusion=success`, código Meta executado do merge-test ref `b1b90e29e81c1759334d435d2a91477be8cdb7ac` (PR #2 atualizado ao commit `96c16ef24e6d1a263cd2657c4ca567c0a55916bc`) e checkout **independente, sem merge** S0 `2958c24f3ea0a2d3de751b52ea0f443d1f8b49c8`.

- Job `WA-15C contratos Meta TS + S0 PG17`, ID `118557590343`: **success**.
- Job `WA-06D PG17 descartavel`, ID `118557590356`: **success**, 14/14 WA06D-A + 6/6 WA06D-B.
- Job `meta-offline`, ID `118557589804`: **success**, **479/479** TypeScript Node 22, zero falhas.
- S0 rodou `scripts/run-s0-local.sh` completo em PostgreSQL 17, com banco descartável `prumo_s0_test_ci` antes do gate cruzado.
- Os dois checkouts PR Draft usaram `actions/checkout` em subdiretórios distintos `meta/` e `s0/` e `persist-credentials:false`; **nenhuma branch foi integrada**.

## O que foi testado de ponta a ponta dentro do laboratório

`wa15c-produce-s0-commands.ts` importa de verdade `prepareWa15FixtureCommand` (WA-15B) e gera **oito comandos sintéticos parametrizados**: `register`, `replay`, `recover`, `wrong_sender`, `wrong_intent`, `attempt_conflict`, `wamid_conflict`, `absent`. Confere que nunca há `ack_allowed`, `retry_external` ou `production_authorized` verdadeiros.

A rotina passa esses argumentos como **um único valor JSON ao psql**, analisa-os em JSONB e usa um despachante de testes `pg_temp.wa15c_call`, que permite exclusivamente as **duas funções S0 privadas conhecidas**; jamais concatena SQL do JSON ou executa nome de função arbitrário.

São criadas e consumidas as mesmas tabelas reais S0-030/040/041/042 de laboratório, incluindo outbox `BLOQUEADA_GATES`. Os testes abrem três conexões PostgreSQL independentes: criação e COMMIT do cadastro, gravação/replays e COMMIT do ledger, consulta posterior numa **nova conexão**.

**Marcadores executados e verificados individualmente:**
- WA15C-01 — gravação por dados TS no escopo de loja e emissor resolvidos pelo cadastro autoritativo S0;
- WA15C-02 — replay idempotente sem segunda linha;
- WA15C-03 — recuperação exata antes do COMMIT;
- WA15C-04 — tentativa por emissor técnico de outra concessionária rejeitada;
- WA15C-05 — intenção S0 de outra concessionária rejeitada;
- WA15C-06 — uma tentativa não admite outro `wamid`;
- WA15C-07 — um `wamid` não admite outra tentativa;
- WA15C-08 — `LAB_ABSENT` permanece sem retry, ACK ou alteração de ledger;
- WA15C-09 — registro único confirmado por COMMIT;
- WA15C-10 — consulta exata durável em nova sessão;
- WA15C-11 — leitura histórica após cancelar a intenção;
- WA15C-12 — bloqueio de novo registro/replay após cancelamento.

**Resultado:** **12/12 marcadores WA15C PASS**, com preflight extra `WA15C-00` e gerador TS `WA15C-TS` PASS. Foram recuperados os logs completos do job e verificada a saída explícita `PASS WA15C: 12 cross-branch PostgreSQL checks, three real psql sessions`.

## Correção no CI da WA-06D

Uma execução anterior [39401512006](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39401512006) já passou na WA15C, mas o job WA06D teve erro transitório: `pg_isready` retornou enquanto o entrypoint da imagem PostgreSQL ainda finalizava a inicialização e o servidor inicial estava sendo desligado. **Não houve falha de lógica WA06D SQL nessa tentativa; ela nem iniciou.**

O workflow agora aguarda a linha do próprio contêiner `PostgreSQL init process complete; ready for start up` **e** o `pg_isready`. O [run definitivo 39401664926](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39401664926) confirmou **3/3 jobs success**, inclusive WA06D **20/20 PASS**.

## Limitações rigorosas

A WA15C comprova a ligação **entre códigos de duas branches e PostgreSQL de laboratório**, não um serviço real autenticado. Ainda faltam: principal de serviço/IAM com permissões específicas, HMAC Meta e webhook reais, semântica de ACK HTTP após confirmação durável, janela/templates e autorização de disparos, otimização/IA, política de reintento em falha real de rede, LGPD, e transições comerciais. `API_ACCEPTED` jamais deve ser tratado como entregue/vendido. O teste de nova sessão após COMMIT **não simula queda do servidor durante COMMIT**; isso é gate posterior distinto.

**Decisão:** WA15C lab PG17 = APROVADO; serviço Meta↔S0 de produção = NÃO IMPLEMENTADO/HOMOLOGADO. Não conectar Supabase hospedado, Graph, bancos nem executar merge/deploy sem autorização separada.
