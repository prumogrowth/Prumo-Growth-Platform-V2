# Prumo Growth E04 — conciliação independente da cadeia C04/C08 legada pós-humano

**Data de referência:** 25/10/2026, America/Recife (GitHub Actions em UTC já no dia 26). **Frente:** `feat/oai-s0-f03-history-port-20261023`, PR #1 Draft. **Código certificado:** `26cb7d73beb10a08e0f7dc9c3a5c287d183db67f`.

## Escopo entregue

Foi introduzida uma **porta independente de conciliação SOMENTE PARA REVISÃO TÉCNICA de cadeia C04 legada cancelada**, separada da minuta de planejamento pós-humano que continua recusando qualquer plano anterior.

- `backend/s0_f02_posthuman_legacy_reconciliation_local.py`: `S0F02LegacyReconciliationReview` requer obrigatoriamente a implementação física `S0F02LegacyObservedOriginBridge` da S0. A primeira etapa encadeia identidade S0/S1 e intenção sintética do gestor, conteúdo histórico F03/fechamento com HMAC/versões, testemunho C08 do cancelamento LOCAL e prova observada por gatilhos C04/C08 da criação do plano e tentativa anterior ao caso humano.
- Somente depois de todo o encadeamento retornar `LOCAL_OBSERVED_ORIGIN_REVIEW_ONLY`, a porta abre uma **nova transação PG17 read-only, repeatable read**, revalida o mesmo tenant, lead, caso e encerramento, exige intenção registrada e testemunho C08 vinculado, plano original ainda cancelado, nenhum plano não cancelado, nenhum opt-out e ausência de minuta nova na tabela privada.
- Estado positivo `LOCAL_LEGACY_EVIDENCE_REVIEW_ONLY` contém **somente o nome do estado**, sem dados de cliente, autoridade, horário comercial, token ou comando de envio. Trata-se de **parecer forense de evidência sintética local**, não autorização comercial, consentimento real, comprovante da Meta, agendamento, nem aprovação humana operacional de plano.
- Estados distintos impedem avanço em caso de origem posterior ao handoff, origem ausente, evento alterado, reserva antes externa sem prova de cancelamento, S0/caso/sessão divergentes ou falha física. A implementação da S0 que verifica origem observada foi ajustada para **propagar explicitamente** `RESERVED_PREVIOUSLY_EXTERNAL_UNKNOWN` para `RESERVED_EXTERNAL_UNKNOWN`, sem promover a cancelamento seguro.
- O arquivo `scripts/run-s0-f03-pg17-local.sh` passou a incluir somente a suíte Python da própria frente; **nenhum arquivo `.github/workflows` de outra frente foi editado**, nem código do agendador C04, nem Supabase hospedado.

## Teste de integração físico realmente atravessando a cadeia

- O `setUp` da bateria F03 agora cria, **somente para #322–328**, um plano C04 e tentativa programada no banco antes da inserção do caso humano. O ledger S0 observa os eventos de verdade em ordem SQL: plano → tentativa → caso humano. A linha sintética guarda os timestamps compatíveis e o ledger confirma o instante observado; assim não se trata apenas de plano pós-humano com `criado_em` retroativo.
- Após o encerramento F03 físico, a função C08 original cancela a cadeia no PostgreSQL e gera os eventos. A intenção sintética separada do gestor é registrada por meio da porta S0/F02. O testemunho C08, a verificação de origem e a nova porta de reconciliação passam por todo o caminho.
- **Teste #322:** resultado `LOCAL_LEGACY_EVIDENCE_REVIEW_ONLY`, com uma testemunha local e **zero minutas novas**, nenhuma tentativa pendente de envio. O plano legado continua existindo apenas como cancelado.
- **#323:** repetição da revisão sem duplicar ou agendar. **#324:** a minuta pós-humana comum segue bloqueada para a mesma cadeia, apesar do parecer local. **#325:** tentativa previamente `reservado` retorna `EXTERNAL_DISPATCH_UNKNOWN`. **#326:** adulteração posterior no evento de cancelamento bloqueia. **#327:** opt-out posterior bloqueia. **#328:** flag JS `sendNow` não se converte em autorização.
- Atestação positiva S0 por si só não valida política Meta/consentimento real, armazenamento inalterável contra superusuário, nenhum dado do provedor externo, nem permissão para liberar template.

## Certificação

**[GitHub Actions #40257851993 — SUCCESS](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40257851993)** no SHA exato `26cb7d73beb10a08e0f7dc9c3a5c287d183db67f`.

- **84/84 S0 Python**; **514/514 Python F02/F03**, dos quais **328 cenários físicos PG17** acumulados.
- **598/598 Python** em duas suítes, **269/269 Node** da S2 fixada, total **867 verificações distintas**. NÃO são 867 jornadas reais fim a fim ou homologação dos 70 gabaritos E02 originais.
- Novos nesta execução: **7 testes PG17 #322–328** e **6 testes unitários Python** para contratos e estados. Todos aprovados no mesmo SHA; nenhum teste preexistente foi removido para melhorar números.

## Pendências e governança

- Esta camada demonstra evidência física **somente no laboratório**. Ainda faltam autorização/assinatura humana S0/S1 em runtime real, trilha operacional de política e consentimento, template Meta real, cancelamento externo autenticado para reservas, janela comercial/frequência/horários homologados, executor isolado e idempotência de envio antes de construir o fluxo operacional.
- Não adaptar a minuta comum para aceitar simplesmente um boolean `legacyCanceled`. O caminho reconciliado permanece **apartado, sem escrita de plano**. Um contrato novo de proposta para esse caminho exigirá confirmação independente de autorização e regras S0 adicionais, sem herdar execução do C04 pré-humano.
- **Issue #3** da S1 é só auditoria inicial, não autoriza otimizações ou mudanças de workflow. As frentes permanecem em branches independentes; futura integração ocorrerá em branch própria, com validação e autorização antes da `main`.
- PR #1 continua Draft, sem merge, deploy, acesso a hosted Supabase, Meta/OpenAI API ou clientes reais.
