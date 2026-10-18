# S0-033 — C02 sintético aplicado atomicamente a uma tarefa da inbox

**Status:** migração candidata sintética no PR #1, sem implantação hospedada. O C07 e a integração Meta real não fazem parte deste incremento. DEC-WA-01/02/03 aprovadas como diretrizes; DEC-WA-05 define titularidade Meta por concessionária. DEC-WA-04/06 e os demais gates permanecem abertos.

## Contrato e estratégia

A inbox S0-029/030 aceita eventos técnicos fictícios; a S0-032 gerencia versões, leases, resultados e auditoria. Nenhuma delas comprovava uma **aplicação comercial** ao concluir a tarefa. A migração `202610180033_s0_inbox_aplicacao_c02_atomica.sql` introduz um caminho exclusivamente privado e simulado que liga uma mensagem fictícia recuperável ao ingresso e usa a implementação C02 aprovada, sem copiá-la ou recriar o domínio.

- `prumo_private.inbox_c02_fixture_s0` guarda exclusivamente telefone, ID externo e texto **sintéticos** ligados ao `inbox_id` e concessionária. Não contém mensagem real da Meta, segredo, autorização de envio ou PII de cliente.
- `anexar_fixture_c02_s0` exige evento do tipo `inbound_message`, originado de `meta_apps_fixture_s0` via S0-030, escopo de loja/canal, marcador `payload_fixture_s0` e igualdade com `provider_message_id_s0` e a chave técnica `in:<ID>`. Só aceita antes da primeira reserva (`READY`, versão 1), com replay idêntico permitido e alteração conflitante rejeitada.
- `aplicar_inbox_c02_s0` exige lease vigente, worker correto e versão exata, sob `FOR UPDATE OF t`. Na **mesma transação** chama `receber_mensagem_identidade_s0` (que reutiliza C02 e suas regras de cancelamento de recontatos, estados e handoff), registra conclusão S0-032 e armazena vínculo escopado `inbox_id→mensagem_id` em `aplicacoes_c02_inbox_s0`. Falha em qualquer fase desfaz **inclusive a mensagem e o evento comercial**; não é permitido `APPLIED` sem prova de mensagem persistida.
- Replay idêntico do mesmo worker e mesma versão, após confirmação, retorna `ALREADY_APPLIED` com a mesma mensagem; worker diferente, versão obsoleta, scope errado ou lease vencido são rejeitados.
- Se o resolvedor 8↔9 retorna `IDENTITY_CONFLICT` ou `NEEDS_REVIEW`, a função **lança erro e desfaz as mudanças daquele intento**, mantendo a tarefa reservada. O operador sintético de testes pode registrar quarentena pela S0-032; isso não constitui encaminhamento humano operacional, e não cria prova falsa de C02.
- As tabelas são privadas com RLS ativada. Funções `SECURITY INVOKER` exigem `current_user='postgres'`, mantendo o mesmo limite de teste e revogando concessões a `anon`, `authenticated`, `service_role` e roles técnicos S0.

## Evidências e verificações propostas

`supabase/tests/s0_wa_033_aplicacao_c02.sql`:
- WA33-01: duas variantes 9↔8 no mesmo lead, duas lojas isoladas, replay idêntico e vedação a worker errado e mutação da fixture;
- WA33-02: falha simulada por trigger **após a execução de C02**, verificando rollback de mensagens, auditoria, tarefa e vínculo; remoção da falha e tentativa legítima;
- WA33-03: tentativa com lease vencido não produz mensagem;
- WA33-04: identidade ambígua não marca task como aplicada e exige caminho técnico explícito de quarentena;
- WA33-05: vínculo por escopo e ID externo, ACL privada.

`scripts/test_s0_wa_033_concurrency.sh`: duas sessões PostgreSQL disputando o mesmo evento e worker não titular; uma única aplicação e uma única conclusão. O runner protegido `scripts/run-s0-local.sh` exige banco PostgreSQL descartável local `prumo_s0_test_*` e inclui regressões 001–033.

**Aprovação de teste deve citar execução/commit específicos em `tests/S0_ACEITE.md`, após leitura dos logs.** Não pressupor resultado positivo sem evidência.

## Limites de segurança e próximos gates

- `APPLIED_ATOMIC` comprova só a transação PostgreSQL **sintética**; não comprova Meta HTTP, `commit_state=COMMITTED` de um ingressor real, autorização de aplicativo, conteúdo de mensagem original protegido, segredo HMAC ou operação de IA.
- A flag `mobile_confirmado_fixture` é declaração de teste, não evidência do proprietário do número; contatos fixos/reciclados e conflitos não podem ser fundidos automaticamente em produção.
- C07, suas callbacks de status sem ID de evento único, e os critérios WA-01C permanecem separados. Não transformar hash de correlação em dedupe final ou provocar envio externo.
- Essa implementação **não substitui** C01/C02 sintéticos legados, não resolve menor privilégio das funções `SECURITY DEFINER postgres` e não fornece serviço autenticado de worker.
- Migrações 028–033 ainda requerem teste Auth/REST local gerenciado antes de qualquer integração, sem usar o Supabase hospedado.
- DEC-WA-04 (ambiente) e DEC-WA-06 (segredos/retencão/quarentena/continuidade) seguem pendentes. DEC-WA-05 titularidade aprovada por concessionária, mas sem onboarding ou manipulação de canais.
- PR #1 e PR #2 em Draft, sem merge. **GO** apenas para engenharia sintética; **NO-GO** para deploy, Graph API, instituição financeira, OpenAI real, API pública ou produção.

## Retorno à frente WhatsApp/Meta

O próximo contrato conjunto precisa definir payload durável realmente recuperável, autenticação por aplicativo, vinculação com vigência App/WABA/emissor/loja, equivalência telefônica fundamentada e dedupe de callbacks C07. A prova atômica interna S0-033 não elimina exigências de ACK/retencão ainda pendentes.
