# S0 / CFI-01 — evento técnico de conclusão humana, incremento de laboratório

**20/10/2026 | Escopo local e NÃO homologado.** Esta frente OpenAI implementa os ajustes específicos na S0, conforme instrução do responsável; não existe equipe S0 separada aguardada. Branch `feat/s0-cfi01-f03-auth-preflight-20261020`, derivada de `feat/s0-fundacao-prumo`, isolada de PR #1 e PR #8. Nenhum merge, deploy, Supabase remoto, Meta, OpenAI real ou Banco.

## O que foi efetivamente implementado no S0

`backend/s0_human_closure_event_local.py` adiciona um **protótipo executável server-side** para registro de **evento técnico LOCAL** da conclusão de conversa humana. Ele **não** altera `ciclos_comerciais.status_comercial`, não preenche ficha, não declara remessa/venda/negativa, não chama IA e não autoriza recontatos.

Entrada pública lógica mínima: `case_ref`, `expected_cycle_version` e `idempotency_key`. Identidade do ator e sessão são verificadas pelo `IdentityProvider` herdado de `backend/identity_boundary.py` (GoTrue é implementação possível, mas **não foi exercitado nesta bateria**). A SQL parametrizada revalida a sessão em `auth.sessions`, o caso, a atribuição humana atual, a concessionária ativa, o vínculo de loja e versão/status do **ciclo** no mesmo cursor/transação local. Retorna sempre estados distintos: `DENIED`, `STALE`, `BLOCKED_S1`, `UNAVAILABLE`, `NO_CONVERSATION`, `ALREADY_CAPTURED`, `DUPLICATE_SNAPSHOT`, `CAPTURED_LOCAL_ONLY`.

A autorização S1 **não é um booleano vindo do navegador ou da IA**. A captura requer um adaptador `S1TransactionAuthority.check(cursor, principal, store, case, assignment)` que opere **no mesmo cursor transacional** e retorne o enum estrito `S1Proof.ALLOW`. Esse adaptador **não existe no backend real**; `s1=None` bloqueia antes de abrir o banco. Os testes injetam um S1 fake, **não provam concessão de produção**. Não confundir pausa de intake com suspensão/conta revogada.

A transação candidata utiliza `FOR UPDATE` sobre caso/ciclo/loja/atribuição e sobre conversas do caso. A captura lê `mensagens` por conversa/caso/loja (incluindo entradas cujo `caso_id` de mensagem pode não ter sido preenchido), ordena mensagens por `criada_em,id`, calcula um fingerprint SHA-256 **não assinado** do conteúdo sintético, guarda apenas hash, última mensagem, contagem e chaves de controle, sem copiar texto bruto ao registro nem à resposta. Novas entradas e edição/concorrência exigem **rechecagem física ainda não implementada**; as locks atuais são **hipótese de serialização**, não prova de corrida PostgreSQL.

**Registro privado de ensaio:** `supabase/tests/s0_cfi01_human_closure_table_local_only.sql`. A tabela `prumo_private.cfi01_human_closure_events_local` exige FK para caso/ator/atribuição, versão positiva, hash SHA-256 formatado, unicidade `(loja,caso,chave)` e `(loja,caso,atribuição,hash)`, com grants revogados a roles públicas. **Não é migration**, não entrou no `scripts/run-s0-local.sh`, só pode ser aplicada explicitamente a PostgreSQL descartável após baseline S0; nenhuma conexão ao banco ocorreu nesta rodada. Autorização de escrita do fixture continua sendo papel `postgres` local apenas e **não** deve virar serviço exposto.

## Evidência e limitações exatas

- `backend/tests/test_s0_human_closure_event_local.py`: **35/35 testes unitários PASS** com identidade/cursor PostgreSQL simulados: idempotência/replay, bloqueio S1, escopo, versão, status de banco/vendido, snapshot, hash, no-op e ordem de locks, DSN somente localhost.
- `backend/tests/test_s0_human_completion_preflight.py`: **33/33 PASS**, versão anterior da própria S0.
- **68/68 PASS** em **uma execução local** `unittest discover` + `compileall` PASS. O container usou um **stub de `backend/identity_boundary.py` só para os tipos de teste**; o arquivo publicado importa o módulo real, sem substituí-lo na branch. Não somar estes 68 com os 220 testes OpenAI para inventar uma regressão integrada.
- Blobs Git idênticos aos testados: módulo evento `740a576bdb51463e89b7e0ceb163acf34daff8ba`, testes `c114b573c7ea2c86a3a721a4c9e4183d6ba058e6`, fixture SQL `b810a3f97ec03aab4641bcbb753f56f867268abf`. Não houve prova em PostgreSQL/GoTrue reais, teste de concorrência nem CI nesta rodada.

## O que falta para a VERIFICAÇÃO REAL e a substituição de permissões fictícias

1. Executar fixture e contrato num PostgreSQL 17 **descartável** com migrations S0 aplicadas; verificar chaves, constraints, locks, corridas entre novo inbound/cancelamento/revogações e duas conexões concorrentes; revisar o uso de `FOR UPDATE` e integridade de FK. Ainda há necessidade de uma **fonte S1 confiável** implementada, com prova de conta/atribuição vigente e eventual exceção por caso — sem importar fixtures S1 como direito real.
2. Definir versão física de caso/conversa/ficha e contrato de fechamento/idempotência assinado S0/FV; hoje só existe `ciclos_comerciais.versao_registro`. A S0 precisa também bloquear duplicidade por outro canal/processo, não apenas pela chave fornecida.
3. Implementar `begin/recheck` autorizados, snapshot minimizado e assinatura canônica OAI-05/OAI-07. Um hash SHA-256 **sem assinatura não comprova autoria, imutabilidade ou remessa bancária**. Registros `CAPTURED_LOCAL_ONLY` são provas técnicas de laboratório, **não fechamento comercial**.
4. Especificar catálogo de ficha/campos e aplicação S0 atômica/idempotente com auditoria; promover somente valores permitidos e confirmar `APPLIED` após transação.
5. Testar autenticação real GoTrue/S1, isolamento por loja, falhas parciais, permissões de DB reduzidas e fronteira provider, e só depois decidir implantação/merge mediante autorização específica. Nenhum estado comercial/Meta/Banco decorre da IA.

**Ponto de pausa pactuado:** permanecer desenvolvendo os dois marcos S0↔OpenAI até conciliação contratual e verificação de permissão **real**, e **só então** pedir esclarecimentos e fazer auditoria geral da documentação, não nesta rodada.
