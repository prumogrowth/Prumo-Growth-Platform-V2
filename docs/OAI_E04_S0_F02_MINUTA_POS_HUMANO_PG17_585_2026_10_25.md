# Prumo Growth E04 — minuta não executável de planejamento pós-humano S0/F02

**Checkpoint:** 25/10/2026 (America/Recife; Actions no dia 26 UTC). **Frente:** `feat/oai-s0-f03-history-port-20261023`, PR #1 Draft. **Código certificado:** `99d09c1f0c03ef20444d33cbb27067aeece29eb5`.

## Objetivo e limites

Construir um **contrato independente de proposta de plano pós-humano para revisão técnica**, sem aproveitar a função de agendamento C04 pré-humano, sem construir fila Meta, sem gravar envios e sem declarar um gestor autorizado operacionalmente. O produto nesta etapa é uma linha privada, sintética e imutável cujo estado constante é `REVIEW_ONLY_C04_BLOCKED`.

### Arquivos alterados na branch da própria frente

- `supabase/tests/s0_f02_posthuman_draft_local_only.sql`: tabela local de minuta com escopo de concessionária, fechamento humano, caso, lead, canal, template, gestor/sessão, tentativa S2, versão/categoria da política, horário **proposto**, hash do contexto e chave de idempotência. PK e exclusividades por fechamento e chave na mesma loja; RLS, revogação de acesso comum e imutabilidade por gatilho. **Somente** Pg17 descartável, não migração de produção.
- O gatilho de escrita exige intenção S0 previamente registrada, fechamento/caso/lead vinculados, gestor com sessão e equipe S1 ativa, template sintético aprovado e política imutável de finalidade `post_human`, elegibilidade sintética C04, ausência de opt-out, nenhum plano C04 anterior nas tabelas e nenhum evento histórico `PLAN` no livro local de origem. A minuta **não** entra em `public.planos_recontato_sinteticos` ou `public.envios_template_sinteticos`.
- `backend/s0_f02_posthuman_draft_local.py`: entrada tipada `PostHumanDraftRequest` construída na S0, verificação inicial física S0/F03/F02, consulta ao histórico real do encerramento e gestor S1, lock do lead, rechecagem de canal/versão/template/elegibilidade. Confere hash da intenção do gestor já gravada e bloqueia toda cadeia C04 anterior, inclusive cancelada ou apagada posteriormente quando o ledger local ainda a recorda. A mensagem JS da S2 não decide horário, consentimento, permissão ou envio.
- O controle temporal da fixture aceita uma única tentativa proposta entre **24 horas e sete dias** à frente do horário medido no PostgreSQL, sem depender do relógio do modelo. **Essa janela é apenas um guardrail de simulação**, não política comercial aprovada nem compromisso de horário.
- Replay idêntico retorna `DRAFT_REPLAY_REVIEW_ONLY`, tentativa conflitante retorna `CONFLICT_REVIEW_REQUIRED`; duas solicitações simultâneas são serializadas pelo lead. A assinatura/hash da intenção não equivale a homologação de consentimento, sessões de produção, Meta, LGPD nem comportamento financeiro. Nenhum campo de cliente é alterado.
- `backend/tests/test_s0_f02_posthuman_draft_local.py`: sete testes unitários de formato estrito, data com fuso, opção de envio falsificada, evidência inválida e retorno sem poderes adicionais.
- `backend/tests/test_s0_f03_pg17_integration.py`: **11 novos testes físicos #311–321**, com caminho positivo privado, nenhuma escrita nas tabelas de agendamento e envio, replay idempotente, mudança de horário/chave, janela fora do intervalo, plano antigo cancelado, opt-out posterior, flag de envio fraudada, imutabilidade/RLS, paralelismo e preservação da memória de um plano deletado no ledger de origem.
- `scripts/run-s0-f03-pg17-local.sh`: apenas adicionou fixture SQL e suíte Python próprios da frente. **Nenhum `.github/workflows/` foi alterado**.

## Certificação e métricas sem arredondamento

**GitHub Actions #40256034779 SUCCESS**: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40256034779

- **84/84 Python S0** da suíte anterior.
- **501/501 Python F02/F03**, incluindo **321 cenários físicos PG17 acumulados**.
- Total **585/585 Python** e **269/269 testes Node** da versão S2 fixada. São **854 asserções/testes de suítes separadas**, **não 854 jornadas de negócio completas** nem homologação dos 70 oráculos SYN E02.
- A execução imediatamente anterior [#40255757761](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40255757761) já havia passado com 584 Python e 269 Node. A execução final inclui a proteção extra e o teste #321, todos aprovados no SHA de código identificado acima.

## Limites que permanecem abertos

- A minuta funciona somente para **nenhuma cadeia C04 anterior identificada**. Caso exista plano ativo, cancelado ou vestígio `PLAN` no ledger, retorna `LEGACY_RECONCILIATION_REQUIRED`. O caminho com cancelamento anterior deverá usar o testemunho C08 e a origem observada na S0 em uma interface separada e sem promover automaticamente o cancelamento local a cancelamento Meta.
- O sistema de eventos de origem é um fixture com triggers PostgreSQL, **não WORM contra superusuário**, nem prova de inexistência histórica se registros foram suprimidos antes da sua instalação. O teste de plano apagado ilustra proteção dentro do laboratório, não promessa de imutabilidade externa.
- Ainda não há aprovação operacional humana independente da minuta, política de templates Meta real, consentimento real, janela/frequência comercial validada, controle de envio externo, confirmação de entrega, nem runtime completo S1/GoTrue. **Nenhum plano operacional ou mensagem foi criado ou enviado**.
- A função C04 original continua bloqueando ciclos humanizados. Não acessar Supabase hospedado ou cliente real até fase de integração geral autorizada; a integração ocorrerá em branch própria aprovada antes da `main`.
- Issue #3 é auditoria inicial de otimização da S1 e não autoriza mudanças; workflows e branches de outras frentes, PR Draft e `main` permanecem intocados.
