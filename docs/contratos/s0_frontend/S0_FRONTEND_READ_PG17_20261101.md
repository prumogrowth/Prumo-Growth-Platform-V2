# S0/S1 → Frontend — leitura do titular, atenção humana e ordenação (PG17 LAB)

**01/11/2026 · Issue [#14](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/14). Status: CANDIDATO_EM_REVISAO / LAB_ONLY.** Não significa API S0 hospedada, usuário autenticado, dado real, acesso gerencial ratificado ou aceite pela frente Frontend.

## Autoridade da regra e fontes imutáveis

A regra definida pelo proprietário na #14 é: **abrir uma conversa pelo Consultor titular (ou Gestor autoatribuído) conta imediatamente como leitura operacional**, inclusive se fechar no mesmo instante. **Gestor supervisor não marca leitura do titular**. Quando não há resposta humana efetivamente publicada, a conversa lida continua com pendência sem contador. Nova mensagem visível depois da leitura reabre as não lidas. Rascunho local e `API_ACCEPTED` técnico **não** provam resposta humana. Caso histórico sem ação mantém indicador de leitura/pendência e **não** oferece compositor fictício.

Fonte Frontend original pinada: `ca262179e180c635fb7f44aaa37e4c1214f9ba12`, módulo `frontend/visual/conversation-attention.mjs`, testes `conversation-attention.test.mjs` e `attention-integration.test.mjs`. A S0 **não editou essa árvore** nem declarou a fixture visual como autorização de operador. Fonte de ingresso técnico PG17 pinada `01ffdb093013664b73b18d23f92aac2202578210`. Base S0/F02: `5b619c7779fb8b6595c72da696a4aa7faec128d1`.

## Contrato candidato: `prumo.s0.frontend.attention/0.1-lab`

A porta `integration/s0s1_frontend_read/pg17_service.py` trabalha somente por instalador em PostgreSQL 17 descartável, no banco `s0_meta_ingress_lab`, e depende do schema `pg17_schema.sql`. Quatro tabelas sem privilégio runtime: `cases` (loja, titular, versões de atribuição/caso/inbox, ação/histórico); `events` (INBOUND visível, HUMAN_REPLY_PUBLISHED, API_ACCEPTED, LOCAL_DRAFT, sequência e timestamp com alegação de verificação); `read_cursors` por caso/titular; `open_attempts` com identificador único. Todas são **fixtures**, não fontes reais. Não há conteúdo de mensagem, telefone nem dados pessoais nessas tabelas.

**`open_case`** exige escopo de loja, ator/role injetado, caso ativo, titular compatível e três revisões `assignment_revision/case_revision/inbox_revision` exatas. Lock exclusivo por caso serializa abertura e novas mensagens **quando o produtor respeita o mesmo lock**. O primeiro `open_ref` registra a leitura até a última mensagem inbound **visível** na mesma transação; repetição exata não marca mensagens posteriores, colisão ou versão obsoleta nega. A resposta positiva **antes do COMMIT** é `LAB_READ_RECORDED_BEFORE_COMMIT` e **não pode ser exibida como confirmação operacional enquanto o commit não for reconhecido**. Supervisor retorna `SUPERVISORY_VIEW_NO_READ`, sem gravação de cursor e sem validar leitura cognitiva ou dwell time.

**`owner_queue`** calcula da própria trilha a projeção por caso do titular: `unread_inbound_count` (número de inbound visível após cursor), `operator_read_confirmed`, `human_reply_pending` como `COUNT` (há não lidas), `DOT` (lida sem resposta humana) ou `NONE`; `historical_read_only`, `composer_enabled`, `last_activity_at`, `last_activity_cutoff_seq` e `activity_time_state`. Somente `INBOUND` visível ou `HUMAN_REPLY_PUBLISHED` com sequência própria contam como atividade conversacional; ACK, rascunho e evento técnico não substituem recência nem resposta. Relógio da **última** atividade conversacional ausente ou sem marca `source_verified` resulta em `last_activity_at=null` e `UNKNOWN`, sem herdar horário antigo ou inventar `Hoje/Ontem`. Casos com horário conhecido são ordenados pelo instante UTC; desempate por `case_ref` e casos sem horário ao final por ordem estável **não cronológica**.

**`manager_summary`** reutiliza a mesma classificação de atenção, mas retorna **só contagens agregadas por loja**, sem `case_ref`, titular, corpo, anexos ou dados D3/D4. Role/escopo são fixtures injetadas; atribuição real de supervisor ainda exige serviço de identidade/ACL ratificado.

A CI usa o componente original `stageConversationAttention` com mapeamento `COUNT/DOT/NONE` → pendência booleana do contrato visual `ui-attention-proposal/0.1`; os arquivos visuais originais não foram alterados. O teste com evidência física gera uma projeção no PG17, executa `stageConversationAttention` e descarta o arquivo temporário após a etapa. **Compatibilidade de teste não é implantação do adaptador no Frontend.**

## Evidência reproduzível e contagem sem duplicação

[CI funcional em `71140f0f7e763e053c2accb856b58cf672a077f8`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41310529428): `completed/success`, **2 jobs aprovados**. Contagens distintas: **25/25 testes PG17 novos**, **8/8 testes de interoperabilidade**, **27/27 regressões Frontend originais** e **25/25 regressões F02 físicas S0**, total **85 casos diferentes**. Na etapa offline, o teste de interoperabilidade que depende do PG17 é `skipped` intencionalmente e passa na etapa física. Não somar os 7 testes offline reexecutados.

Casos cobertos: abertura imediata, supervisor, mensagem recebida após abertura, ausência de resposta humana apesar de draft ou API_ACCEPTED, resposta publicada, reply sem verificação recusada, histórico sem compositor, aggregate gerencial minimizado, ordenação UTC e timestamp ausente/sem prova, três versões e reassignment, colisão/replay de `open_ref`, várias lojas, inbound invisível, rollback, ACL runtime negada, dupla abertura concorrente e abertura contra novo inbound.

**Uma CI inicial falhou em um teste de expectativa**: a fonte com horário não verificado foi corretamente movida para fim da fila e o teste consultava a posição inicial. O teste foi corrigido para buscar `case_ref` estável. A CI do SHA final incluindo este documento exige uma nova execução e confirmação.

## Limites e aceites abertos

- **Não há autenticação S0 real:** `allowed_stores`, `actor_ref`, papel e `source_verified` são valores fictícios fornecidos pelo harness. Atividade/rótulo `VERIFIED_LAB_ONLY` não prova ocorrência real, e fonte de inbound não está ligada ao ingresso Meta #2.
- **Não há evento humano hospedado com origem comprovada:** `HUMAN_REPLY_PUBLISHED` da fixture não deve ser tratado como `sent` real, nem como decisão comercial; transporte outbound é domínio #9.
- **Sem interface de produção:** falta fonte S0 para operador/atribuição/mensagens, autorização de supervisor e corte causal com commit/readback, além do contrato de erro/retry para a UI. Dados e timestamps reais exigem origem S0 confiável. Supressão de conteúdo e isolamento D3/D4 ainda precisam auditoria de ACL com Frontend.
- **Aceite solicitado ao Frontend na #14:** revisar tipos, `COUNT/DOT/NONE`, leitura após commit, regra titular/supervisor, indicador histórico sem compositor, readback idempotente, versão/cutoff e ordenação de horários ausentes; responder **aceite técnico candidato ou incompatibilidades concretas**. Não inferir aceite por CI verde.
- Frentes Meta #8/#10 e OpenAI #7 permanecem com seus próprios gates, não destravados por este laboratório. Sem Graph, OpenAI real, mensagens, credenciais, merge, deploy ou banco hospedado.
