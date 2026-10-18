# Auditoria corretiva S0-034A — integridade da aplicação C02, quarentena e canal

**Status:** incremento aditivo *sintético e privado* para resolver A33-01, A33-02 e A33-03 detectados na auditoria após S0-033. Não reescrever 001–033. DEC-WA-01/02/03 [D] e DEC-WA-05 [D] (titularidade Meta por concessionária) preservadas. DEC-WA-04/06 permanecem pendentes. Nenhum canal real, webhook, token, API pública ou migração no Supabase hospedado.

## A33-01 — tarefa C02 `APPLIED` somente com prova

- A migration `202610180034_s0_integridade_c02_e_pendencias.sql` atualiza `registrar_resultado_ingresso_s0` para exigir, quando o `inbox_id` possui `inbox_c02_fixture_s0`, uma linha `aplicacoes_c02_inbox_s0` do **mesmo inbox, concessionária, canal, worker e versão** antes de aceitar `APLICADO_SINTETICO`. Sem linha, `23514 C02_PROOF_REQUIRED`, sem mudança.
- Trigger de banco `tarefa_c02_applied_exige_prova_s0` bloqueia também `UPDATE` direto para `APPLIED` de tarefa C02 sem a mesma prova (mesmo executor fictício `postgres`). Isso não pretende restringir um superusuário malicioso, mas torna o invariante verificável por SQL.
- `aplicar_inbox_c02_s0` grava a prova **antes** de chamar o resultado S0-032, dentro **da mesma transação** em que C02 criou/reencontrou `mensagens`. Se inserção, trigger, resultado, auditoria ou commit falhar, todos os efeitos são revertidos. A assinatura da função e retorno `APPLIED_ATOMIC` continuam idênticos, assim como o replay por worker/versão.
- As simulações legadas da S0-032 sem `inbox_c02_fixture_s0` continuam podendo declarar `APLICADO_SINTETICO`. **Nunca interpretar esse estado legado como prova de C02**.

## A33-02 — pendência de identidade não pode desaparecer na exceção

- Na S0-033 uma identidade ambígua causava exceção dentro da transação, revertendo até a pendência gravada pelo resolvedor. A S0-034A substitui esse caminho: se `receber_mensagem_identidade_s0` retorna `NEEDS_REVIEW` ou `IDENTITY_CONFLICT`, a pendência, o estado técnico `QUARANTINED`, `motivo_terminal_s0` e ação na auditoria são persistidos **juntos**, no mesmo commit. O resultado é `QUARANTINED_IDENTITY`, com motivo específico, sem mensagem C02 nem prova `APPLIED`.
- `registrar_resultado_ingresso_s0` aceita os novos motivos técnicos, mas exige `pendencias_identidade_s0` com **o mesmo telefone, texto, ID externo, canal e loja** antes de autorizar essa quarentena. Não aceitar escolha arbitrária de causa por worker fictício.
- Não cria novo estado comercial, não autoriza IA ou atendimento humano operacional e não implementa política de quarentena/ACK real da DEC-WA-06.
- A regressão WA33-04 foi alinhada ao novo resultado seguro, preservando o teste histórico das situações ambíguas.

## A33-03 — mesma loja não significa mesmo canal

- Adiciona `UNIQUE(concessionaria_id,canal_id,id)` em `prumo_private.inbox_eventos_s0` e `public.mensagens`, permitindo FKs completas com o **canal**.
- `inbox_c02_fixture_s0` e `aplicacoes_c02_inbox_s0` ganham FKs `(concessionaria_id,canal_id,inbox_id)` para o mesmo evento. A aplicação ganha FK `(concessionaria_id,canal_id,mensagem_id)` à mensagem original.
- Trigger `aplicacao_c02_prova_sem_desvio_s0` valida que a mensagem comprovada é `entrada`, tem o mesmo `id_externo` e conteúdo fictício da fixture do inbox. Não confundir apenas mesmo canal com prova de mesmo evento.
- Regras antigas que permitem um número cliente em lojas A/B/C e uma exclusividade global do **emissor** permanecem intactas.

## Novas provas de teste

`supabase/tests/s0_wa_034_integridade.sql`:
- WA34-01: função genérica e UPDATE direto recusam APPLIED sem prova; aplicação real S0-033 sintética persiste uma vez com replay idempotente;
- WA34-02: canal distinto da **mesma loja** não pode assumir evento ou mensagem de outro canal; conteúdo/ID de mensagem diferente são rejeitados;
- WA34-03: NEEDS_REVIEW mantém pendência e motivo técnico com QUARANTINED e sem mensagem; replay após quarentena negado;
- WA34-04: colisão entre dois leads gera IDENTITY_CONFLICT (não se reduz a erro externo);
- WA34-05: sem pendência concreta não se pode inventar revisão; ACL pública continua fechada.
- Regressão WA33-01..05, WA33-CONC-01, WA32 etc e 24 testes Python permanecem no `scripts/run-s0-local.sh`. A aceitação exige logs do CI PostgreSQL 17 para o **commit exato** do código; o workflow Auth/REST gerenciado permanece reservado a gate próprio.

## Segurança/limites deliberados

Esta correção não instala worker, não cria role de serviço, não aplica C07, não faz ACK HTTP, não armazena mensagem Meta real protegida, não usa cliente real e não autoriza operação da instituição financeira/Graph. `p_mobile_confirmado` permanece flag **exclusivamente fictícia**. A titularidade da DEC-WA-05 é **por concessionária**, mas a parte operacional de Apps/WABAs/mandatos não está homologada. `SECURITY INVOKER` e o atual guarda `current_user='postgres'` restringem o protótipo, **não resolvem a redução de privilégios das wrappers comerciais SECURITY DEFINER**. Propriedade `postgres` do ambiente descartável não é modelo IAM para produção.

**GO:** continuar desenvolvimento sintético após confirmação das regressões. **NO-GO:** Supabase hospedado, API pública, Meta real, C07 operacional, disparos comerciais, produção e merge dos PRs.
