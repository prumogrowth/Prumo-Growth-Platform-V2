# S1-002 — alinhamento da issue #10: pausa só de novos leads e transferências seguras (20/10/2026)

**Prioridade de produto sobre o hardening I32 da testemunha I31.** Trabalho somente em `feat/s1-002-equipe-prumo`, PR #5 Draft, sem merge, deploy ou Supabase hospedado. Fonte: [issue #10](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/10), atualização de negócio de 20/10/2026.

## Decisões recebidas [D] e mudança necessária

1. **Conta x disponibilidade x concessão:** a conta permanece `equipe_prumo_s1.estado='ativo'` durante pausa de novos leads; nenhum grant A/B/C é revogado. Só os responsáveis criam/removem/bloqueiam contas. Gestor age apenas na própria equipe. Pausar/retomar só exige botão e confirmação; nenhum motivo, justificativa ou data de retorno.
2. **Redistribuição:** apenas casos cuja inexistência de atendimento humano iniciado foi **comprovada pelo S0**, para operador disponível da **mesma equipe** com concessão válida para a concessionária do caso. Se não houver substituto, **não remover a atribuição**. Casos iniciados permanecem com o titular até eventual decisão manual por caso do gestor.
3. **Transferência manual excepcional:** integrante da mesma equipe pode receber um caso sem grant de loja, desde que **acesso revogável somente àquele caso**, sem acesso geral a mensagens, leads, documentos, casos ou outros ciclos da loja. Requer autorização de S0/RLS e teste de acessos correlatos; não falsificar um grant de concessionária.
4. **Indicador de mensagens:** S0 é dono das projeções e da prova de leitura/resposta. UI apresenta **contador de não lidas**, ou, após leitura sem resposta, **bolinha de outra cor e sem número**. Leitura pelo gestor não deve mudar a leitura do operador. S1 não deve inserir estados artificiais de leitura.
5. **Concorrência:** versionar estado de disponibilidade, autoria e transição, manter uma única atribuição ativa e preservar história. Botões confirmam sucesso somente após ACK efetivamente aplicado no núcleo, e não após uma requisição simplesmente aceita.

## Auditoria dos contratos antigos

- **I11/migration 048:** `s1_pausar_operador_da_equipe` muda conta para `suspenso`, causa redistribuição de **todos** os casos via trigger I2 e impede leitura por RLS. A nova decisão **supersede** esse comportamento. Seus 14 testes anteriores continuam úteis como evidência histórica, não como critério atual.
- **I12/migrations 049–050:** `s1_mover_atendimento_da_equipe` exige grants ativos no destino e equipe comum. O normal segue seguro; a exceção sem grant exige um **novo** contrato acoplado ao S0 e não pode remover guarda geral nem usar identidade definida pelo browser.
- **I18–I31:** os gateways HTTP/HMAC antigos ainda fazem `pausar/reativar` no contrato legado com motivo obrigatório. Não tratá-los como API correta para a nova UX. Deve haver novo caminho com versão, ator de sessão GoTrue, respostas categóricas e assinatura validada; os testes históricos desses gateways não são evidência de cumprimento da issue #10.

## Fase 1 implementada em fixture PG17 isolada (NÃO migration operacional)

Arquivos:
- `supabase/tests/s1_053_issue10_disponibilidade_local_only.sql`: `s1_disponibilidade_leads_10` isolado da conta; controle `s1_definir_disponibilidade_leads_10(gestor,operador,pausar,versao_esperada)`, com chefia e estado de conta validados após locks de linhas, CAS, replay idempotente e trilha append-only sem motivo; trigger de bloqueio de **novas atribuições ao operador pausado**, mantendo titulares anteriores; desabilita as funções antigas perigosas de pausa/retomada apenas no ambiente que aplica a fixture. Tabelas privadas com RLS, função apenas `postgres` local de teste, sem EXECUTE para `anon/authenticated/service_role`.
- `supabase/tests/s1_053_issue10_disponibilidade_aceite.sql`: provas sintéticas de conta ativa, grants intactos, mesmo titular, recusa da nova atribuição, versão obsoleta, equipe cruzada, legados bloqueados, retomada sem recuperar/alterar antigos, RPC privada e ausência de concessão geral indevida.
- `.github/workflows/s1-002-issue10-intake-local.yml`: roda as regressões antigas **antes** da fixture, e depois executa os testes novos, somente PostgreSQL 17 descartável.

**Atenção:** o resultado do comando é `INTAKE_PAUSED` / `INTAKE_RESUMED` / `ALREADY_APPLIED`, com `version`, `operator_id` e `redistribution=DEFERRED_S0_PROOF`. Esta última categoria informa que a pausa foi aplicada para a distribuição futura, mas **não é prova de que a redistribuição dos casos não iniciados já foi executada**. Não anunciar “redistribuição concluída” à interface. Para o núcleo real, este retorno deve incluir uma versão de projeção S0 que permita distinguir `APPLIED`, `PENDING_VALIDATION`, `DENIED` e `CONFLICT`.

A `s1_excecoes_caso_preparacao_10` é apenas **estrutura privada de modelagem**: não concede SELECT nem RLS e não implementa a transferência excepcional. Isso evita criar um bypass de isolamento da loja antes de contrato conjunto com S0.

## Dependências formais da S0 e resolução esperada

**D-S0-01 — prova de início humano:** qual evento imutável do núcleo comprova primeira resposta humana efetivamente registrada, qual ID de caso/atribuição e timestamp, qual evidência de que *não houve* início, e como bloquear a criação de novo evento humano durante a operação de redistribuição? Sem verificação transacional com o S0, **nenhum caso é retirado do titular**, mesmo se parecer não iniciado.

**D-S0-02 — exceção por caso:** acordar objeto de autorização (concessionária, caso, atribuição, operador, emissor gestor, versão, janela, revogação) e propagação RLS/REST em **todas** as tabelas/visões/arquivos relevantes. Uma autorização para caso A **não** pode listar B nem o lead/ciclo/documentos alheios. Nunca criar grant geral A/B/C para contornar restrição. Ao revogar/remover titular, revogar também acesso por caso com trilha.

**D-S0-03 — operação concorrente:** travar caso, atribuição, marcador de início humano e gestor-equipe numa ordem comum. Permitir apenas um titular ativo; caso sem destino mantém titular antigo. Não fazer INSERT sem controlar a versão/antigo; retornar conflito para comando obsoleto.

**D-S0-04 — indicadores:** projeção `unread_count_for_operator` e `read_without_reply`, separadas do estado de supervisão `supervisor_last_seen`. Estabelecer ID de mensagem, leitura idempotente e evidências de resposta humana. S1 não inferirá `read` pela visualização do gestor.

**D-S1-05 — nova API assinada:** adaptar I18–I31 para chamada dedicada `intake`, sem parâmetro de motivo, com sessão real de gestor e número de versão esperado protegido na assinatura HMAC/nonce; retorno operacional não deve usar `PAUSED_GLOBAL`/ `ACTIVE_GLOBAL` legados.

## Próximos gates e segurança

Fixture I32 só representa **fase 1 de bloqueio seguro**, não satisfaz toda a issue #10. Antes da implementação ponta a ponta: confirmar D-S0-01..04, integrar S1/S0 de forma transacional e auditável, criar teste de redistribuição seletiva (caso iniciado, não iniciado provado, desconhecido, sem substituto, equipe alheia, loja sem grant, corrida de resposta humana), autorizar RLS por caso com testes negativos, validar GoTrue/HMAC do novo comando e certificar interface com confirmação de commit.

**NO-GO produção, merge, acesso Meta, dados reais e Supabase hospedado.** O hardening da testemunha I31 fica em backlog paralelo e não altera essas decisões de negócio.

## Evidência conferida — apenas o incremento isolado de segurança da pausa

**[GitHub Actions ISSUE10 #39458246432 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39458246432)**, SHA de código da fixture e testes 3431915129c64714b2181203c6607a5446483481, job 118750634658. Logs examinados: **11/11 identificadores ISSUE10-01..11 PASS**. Passaram os testes de conta ativa sem suspender login, concessões intactas, caso já atribuído permanece com titular, guarda contra novas atribuições, CAS e replay idempotente, outro gestor negado, legados que suspendiam conta recusados, retomada sem motivo/data, novo caso só após retomar, RPC proibida a authenticated e não elevação de concessões gerais.

**[Regressão PG17 #39458207272 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39458207272)**, código histórico em SHA 19f445434c6f64a84a3d5d4241c5eeb0f2dd0ee6; suite anterior I11/I12 S0/S1 passa **antes** de aplicar a fixture ISSUE10. As provas antigas da suspensão total continuam apenas históricas e contradizem o contrato de negócio vigente.

**Aceite parcial:** corretivo sintético de disponibilidade, autoria, CAS, guarda de inserção e desativação local dos comandos de suspensão. **NÃO constitui aceite** de redistribuição seletiva, evento de atendimento humano comprovado, exceção manual com RLS específica, projeção de mensagens do S0, nem nova API gerencial assinada GoTrue/HMAC. Nenhum usuário real afetado, nenhum deploy, merge ou Supabase hospedado.
