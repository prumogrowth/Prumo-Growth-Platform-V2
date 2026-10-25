# E04 S0/F02 — intenção pós-humana auditável, idempotente e não executável

Data: 25/10/2026. Frente: S0/F02/F03, `feat/oai-s0-f03-history-port-20261023`, PR #1 **Draft**.

## Escopo efetivamente implementado

- `backend/s0_f02_posthuman_intent_local.py`: novo comando de **registro auditável de intenção consultiva**. Só aceita `EXPLICIT_REVIEW_SYNTHETIC_ONLY` em um pedido Python tipado, verificado pela identidade S0 injetada e pelo contrato existente de pré-validação F02→S0. A identidade do gestor vem da camada S0, nunca do JavaScript/modelo.
- Depois do pré-voo, uma transação física S0 em PostgreSQL 17 descartável recupera o lead do encerramento humano, adquire bloqueio do lead, revalida a sessão, equipe S1 ativa, papel gestor da concessionária, mesma mensagem/caso/canal, ciclo, evidência sintética de elegibilidade, inexistência de opt-out ou plano legado ativo, template aprovado, finalidade pós-humana, categoria e versão de política S0.
- A exclusividade de `(concessionaria_id, evento_fechamento_id)` e de `(concessionaria_id, chave_idempotencia)` impõe uma única intenção por encerramento. A repetição exata retorna `ALREADY_RECORDED_AUDIT_ONLY`; mudança no hash de evidência, identidade, contexto ou chave produz revisão de conflito. Solicitações concorrentes do mesmo lead são serializadas por bloqueio da linha do lead. Até mesmo repetição idempotente passa por verificação de opt-out/condição atual, evitando declarar elegibilidade após revogação.
- `supabase/tests/s0_f02_posthuman_intent_local_only.sql`: tabela privada imutável com estado constante `AUDIT_ONLY_C04_BLOCKED`, hash da proposta e hash fictício de evidência de gestor. Gatilho exige vínculos de concessionária, caso, sessão/S1/gestor, canal, política e ausência de plano ativo/opt-out. Há RLS e retirada de acessos comuns. Nenhum conteúdo de conversa nem mensagem enviada fica nesse recibo.
- **O registro NÃO cria plano, não dispara template, não altera ficha ou status comercial, não executa Meta/n8n, não implementa consentimento real nem autoriza marketing.** O agendador C04 existente continua negando ciclos com atendimento humano. A intenção sintética não é uma decisão de aprovação para o executor comercial.
- O SHA de evidência do gestor é um *fixture* tipado, não verificação do ato do gestor no mundo real; o `LocalIdentity` dos testes é sintético. Há dependências futuras de sessão GoTrue, papéis S1 efetivos, consentimento e política Meta reais, ratificação de planos/contratos e migração geral.

## Testes/execução

- GitHub Actions **SUCCESS**: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40200244727
- **Código certificado:** `7f5cd06b782cffccb36de2c0443c56a06d4c18a7`.
- **84/84 S0 Python + 430/430 F03/F02 Python = 514/514 Python**; os F03/F02 incluem **276 testes físicos PG17**, com 15 novos (262–276).
- **269/269 Node JS** nativos sobre checkout S2 fixado. São **783 verificações de suítes distintas no mesmo CI**, não 783 jornadas end-to-end nem homologação dos 70 oráculos E02 originais.
- Adicionados sete novos testes unitários para formato de decisão, hash, chave de idempotência e tipos; os 15 físicos verificam registro sem envio, replay único, conflitos, escopo gestor/S1, alteração de opt-out, plano antigo, versão de template, concorrência, imutabilidade/RLS e tentativa de gravação cruzada.
- O primeiro CI desta etapa falhou por colisão de nome `old` de alias SQL com variável reservada PL/pgSQL `OLD`. O apelido foi corrigido para `prior_plan`; a **repetição integral** certificou o resultado. O erro anterior não foi ocultado, e não houve redução de cobertura.

## Governança e próximo gate

- Orientação de 25/10: manter branches por frente e preparar futura integração em branch específica, supervisionada por validação e autorização antes da `main`. Não incorporar diretamente à main.
- A [Issue #3](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/issues/3) cuida apenas de auditoria inicial de duplicação do CI S1. **Não autoriza otimizações.** Nenhum workflow de outra frente foi alterado nesta etapa; o runner local F03 recebeu só a fixture e o teste da própria frente.
- Sem acesso a Supabase hospedado, clientes reais, Meta/OpenAI, implantação, merge, E05 nem envio.
- Próximo gate possível: especificar cancelamento verificável de cadeia IA anterior e aceite humano S0/S1 com recibos independentes; desenvolver novo contrato de planejamento pós-humano **separado** da função C04 pré-humana, com controles de opt-out, finalidade, catálogo de templates, limites/horários, concorrência e estados de transporte. Seguir offline; só na fase futura integrar numa branch própria.
