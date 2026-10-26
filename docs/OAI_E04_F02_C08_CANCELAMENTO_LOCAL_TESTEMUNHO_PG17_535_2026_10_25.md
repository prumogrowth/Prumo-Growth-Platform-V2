# E04 — F02/S0: testemunho do cancelamento LOCAL da cadeia de recontato C08

**Data de referência local:** 25/10/2026. **Escopo:** branch própria `feat/oai-s0-f03-history-port-20261023`, PR #1 Draft, PostgreSQL 17 descartável no CI. Não é implantação, aprovação de envio, garantia de contato real nem integração com Supabase hospedado.

## Contexto e contrato

A função C08 já existente, `prumo_private.cancelar_recontatos_sinteticos`, serializa pelo lead, atualiza planos/ tentativas sintéticos e escreve eventos de cancelamento de tentativas; responde `transmissao_externa=DESABILITADA`. Não demonstra que a Meta ou outro provedor externo interrompeu ou sequer recebeu alguma entrega. O agendador C04 pré-humano continua bloqueando ciclos que tiveram caso humano.

**Implementação desta rodada, somente na S0:**

- `backend/s0_f02_legacy_cancellation_witness_local.py`: nova verificação física condicionada à intenção pós-humana imutável previamente registrada na S0 e à porta S0/F03/F02 de pré-validação. Verifica sessão do gestor, vínculo ativo S1, caso, loja, canal, encerramento e hash da intenção. Bloqueia lead, reconsulta elegibilidade sintética/opt-out e cruza planos locais, tentativas e eventos físicos da mesma pessoa/loja. Nenhuma origem da IA fornece prova de cancelamento.
- Atestação exige **pelo menos um plano anterior visível e uma tentativa física**; plano `ativo`, tentativa não cancelada, evento de cancelamento ausente, motivo inválido ou versão de plano inconsistente não recebem comprovante.
- Uma tentativa previamente `reservado` produz `RESERVED_PREVIOUSLY_EXTERNAL_UNKNOWN`, mesmo depois de cancelada localmente, porque uma reserva pode corresponder a processamento externo não comprovado. Esse gate tem prioridade sobre a promoção a atestado.
- Quando todos os elementos físicos são coerentes, gera hash SHA-256 de representação canônica (planos, tentativas e eventos ordenados) e assinatura HMAC com contexto de concessionária, encerramento humano, gestor, sessão e versão da chave, sem exportar identificadores/segredo para a F02. No replay, compara todo o snapshot vivo com o testemunho anterior; qualquer divergência obriga revisão.
- `supabase/tests/s0_f02_legacy_cancel_witness_local_only.sql`: registro privado, imutável, de finalidade única `C08_LOCAL_CANCELED_AUDIT_ONLY`, exclusivo por concessionária+fechamento, associado à intenção prévia e gestor/sessão S0. Acesso dos papéis comuns é revogado; fixture executada apenas como administrador do PostgreSQL descartável. Isso **não** é a migração a ser aplicada no Supabase real.
- Um comprovante positivo `LOCAL_CHAIN_ATTESTED_AUDIT_ONLY` **não** cria planos, não insere envios, não altera status comercial, não muda consentimento, não habilita `agendar_recontatos_sinteticos`, não interage com Meta e não constitui autorização de disparo.

## Certificação efetiva

**GitHub Actions #40248896748 — SUCCESS:** https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40248896748

**Commit de código certificado:** `78736c4541e8bd06071ba1710e2e87747488d906`.

- Testes físicos novos #277–290: **14/14 PASS** no PostgreSQL 17 descartável, cobrindo cancelamento C08 real local, replay exato, nenhuma cadeia, cadeia ativa, ausência de tentativa/evento, mudança posterior de evento, tentativa previamente reservada, opt-out subsequente, suspensão do gestor S1, hash de intenção fraudado, dupla execução paralela, imutabilidade do comprovante e isolamento de leitura.
- Mais **sete novos unitários Python**, incluindo input/assinatura, ausência de cadeia, estado ativo, ausência de evento e retorno mínimo.
- Total Python: **84/84 S0 + 451/451 F02/F03 = 535/535**; entre os F02/F03, **290 testes físicos PG17** acumulados. S2/Node fixada: **269/269**. Total de **804 verificações em suítes distintas**, não 804 jornadas independentes de ponta a ponta, nem homologação dos 70 oráculos SYN E02.
- Durante a construção, as primeiras execuções do novo CI foram substituídas por commits corretivos antes da certificação. O estado certificado corresponde exatamente ao SHA de código e à execução acima.

## Limitações materiais e próximas dependências

- A fixture histórica semeia planos, tentativas e cancelamento local em cenários sintéticos; **não prova ainda a ordem temporal real** de criação de cada plano em relação ao início/encerramento do atendimento humano. O próximo gate deverá amarrar também os carimbos temporais ao handoff e impedir uma cadeia fabricada posteriormente.
- O hash/HMAC atesta consistência das linhas consultadas em certo instante, mas não prova por si só origem autenticada de mensagens externas, imutabilidade nativa dos eventos C04 pré-existentes ou cancelamento remoto. Logs de transporte, se vierem a existir, exigirão validação independente, inclusive para `reservado`.
- Sessões/identidades de testes provêm de fixture local. Mesmo o retorno positivo não equivale à autenticação GoTrue/S1 de produção.
- O novo planejamento pós-humano continua **não implementado**. Exigirá contrato próprio S0/S1 com autorização explícita separada, provas de cancelamento da cadeia anterior, opt-out e consentimento reais, janela temporal, catálogo Meta/template, limite de tentativas, idempotência, estados de envio e rechecagem antes de qualquer entrega. Não contornar a proibição do agendador C04 pré-humano.
- Estratégia de governança mantida: cada frente trabalha na própria branch, futura integração em branch específica com aprovação antes de `main`; não alterar workflows de outras frentes sem coordenação. A [Issue #3](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/issues/3) é **somente auditoria** e permanece sem aplicação. **Nenhum workflow da S1 foi editado**, nenhuma migração de Supabase hospedado, dado real, Meta/OpenAI API, merge ou deploy ocorreu.
