# S0/032 — ciclo de vida transacional da inbox sintética

**Marco candidato — somente PostgreSQL 17 efêmero, sem Meta, Banco, credenciais operacionais, worker real ou API pública.** Incremento aditivo à S0-031, sob DEC-WA-01/02/03. DEC-WA-05 aprovada quanto à titularidade Meta por concessionária; DEC-WA-04/06 permanecem pendentes. Não há alteração de canais reais.

## Fundamentos e mudança intencional

A migração 029 podia reacquirir automaticamente uma tarefa `LEASED` cujo lease expirou. Isso não distingue trabalho sem efeito de resultado externo incerto. **Na S0-032, um lease vencido não é renovado nem reexecutado automaticamente.** Precisa de conciliação versionada e explícita. O teste de concorrência da S0-030 foi atualizado para preservar sua cobertura, exigindo agora declaração de ausência de efeito **apenas de fixture**.

## Implementação técnica

`supabase/migrations/202610180032_s0_ciclo_tarefas_ingresso.sql`:

- Adiciona `proxima_tentativa_em`, `motivo_terminal_s0` e `concluido_em` à tarefa existente. Não cria uma segunda fila comercial. `RETRY_PENDING` exige timestamp, e os outros estados não podem carregá-lo.
- Cria `historico_tarefas_ingresso_s0`, com FK composta para a tarefa dentro da mesma loja, versão anterior/posterior contínua, autoria de fixture e ação controlada. UPDATE/DELETE da auditoria são negados por trigger, incluindo tentativa de alteração acidental do owner.
- Atualiza `reservar_ingresso_s0` mantendo sua assinatura: `READY` ou `RETRY_PENDING` com janela de retry alcançada e menos de **três** tentativas. Bloqueio por linha `FOR UPDATE SKIP LOCKED`. Não rearma `LEASED` expirado automaticamente. Registra cada reserva e versão.
- `registrar_resultado_ingresso_s0`: verifica `concessionaria_id`, `canal_id`, UUID do worker, versão, estado `LEASED` e prazo do lease. Grava transição e auditoria na mesma transação. Resultados: `APLICADO_SINTETICO` → `APPLIED`; `FALHA_RETRY_SEGURA` → `RETRY_PENDING` com atraso, até a terceira tentativa, quando → `DEAD_LETTER`; `FALHA_DEFINITIVA` → `DEAD_LETTER`; `RESULTADO_INCERTO` → `QUARANTINED`. Repetição comprovada da mesma ação/worker/versão é idempotente. **Não chama C02/C07, não prova efeito comercial, não transmite mensagem nem produz ACK HTTP.**
- `reconciliar_lease_expirado_s0`: exige expiração, versão vigente e revisor **fictício**; opções de quarentena, falha definitiva ou atestado explícito `SEM_EFEITO_FIXTURE` que permite novo ciclo `RETRY_PENDING`. A declaração de fixture **não é** uma política de reconciliação real ou autorização de identidade de pessoa.
- Funções são `SECURITY INVOKER`, restritas a `current_user='postgres'` nos testes SQL descartáveis; nenhuma autorização `anon`, `authenticated`, `service_role`, `prumo_s0_gateway` ou `prumo_s0_signer`. A limitação do proprietário de alto privilégio persiste e está fora deste gate.

## Ensaios e regressões

`supabase/tests/s0_wa_032_lifecycle.sql` cobre:
- WA32-01: conclusão versionada, worker não titular, versão obsoleta, replay da conclusão, histórico imutável;
- WA32-02: três tentativas com backoff de fixture, respeito ao agendamento e DLQ sem replay cego;
- WA32-03: resultado incerto em quarentena sem auto-retry;
- WA32-04: lease expirado não reaquisição, finisher vencido rejeitado, conciliação escopada/versionada;
- WA32-05: conciliação explícita **sem efeito apenas na fixture**, seguida de tentativa segura;
- WA32-06: isolamento de lojas, falha definitiva e ACL privada.

`scripts/test_s0_wa_032_lifecycle_concurrency.sh` verifica duas sessões competindo para concluir a mesma tarefa: somente a titular da reserva registra o resultado, com trilha única e reconciliação obsoleta rejeitada.

A regressão `scripts/test_s0_wa_030_concurrency.sh` foi **adaptada, não eliminada**, para passar pela reconciliação explícita antes de renovar um lease vencido. `scripts/run-s0-local.sh` executa o conjunto completo em banco local cujo nome começa com `prumo_s0_test_`, com recusa de URL remota.

**Resultado de aceite:** deve ser registrado em `tests/S0_ACEITE.md` somente depois de CI realmente confirmado. Não inferir resultado de commit, documento ou execução pendente.

## Riscos/gates ainda abertos

- O marcador `APLICADO_SINTETICO` **não executa** C02/C07 e não comprova conclusão comercial; um worker operacional exigirá transação única com efeito e auditoria, privilégio mínimo e proteção contra execução duplicada.
- Lease em `LEASED` vencido permanece aguardando conciliação. Não existe job automatizado de monitoramento, painel, auditoria externa, recuperação de payload, DLQ operacional ou retomada de envios Meta.
- O número máximo 3 e os atrasos sintéticos de 15/60 s **não são política operacional aprovada**. DEC-WA-06 deve definir limites, retenção, escalonamento, quarentena/ACK e restore.
- O Supabase Auth/REST local gerenciado não foi declarado compatível com 028–032 até testes próprios. Redução dos privilégios `SECURITY DEFINER postgres` comerciais permanece pendente.
- DEC-WA-05: um aplicativo Meta distinto e propriedade por concessionária, mas registro autêntico e permissões precisam ser confirmados antes de uso real.
- PR #1/#2 seguem Draft sem merge. **NO-GO** para Supabase hospedado, número comercial, Graph API, OpenAI/Banco, custo e produção.

## Retorno à frente WhatsApp/Meta

A fronteira S0 mantém ausência de recibo `COMMITTED` e de autorização de ACK HTTP 200. Correlacionar WA-01A/B/C/D apenas documentalmente, até haver armazenamento protegido/recuperável, HMAC por App, vínculo vigente WABA/emissor→loja, dedupe sem falso conflito e decisão DEC-WA-06. A gestão de resultado incerto deve permanecer sob conciliação; nunca automatizar reenvio quando o efeito externo não é conhecido.
