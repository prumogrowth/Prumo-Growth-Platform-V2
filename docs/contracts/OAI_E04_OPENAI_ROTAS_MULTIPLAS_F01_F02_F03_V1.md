# Prumo E04 — jornadas múltiplas entre F01, F02 e F03 (candidato 0.1)

**Decisão de produto de 27/10/2026:** F01→F03→F02 é uma jornada válida, mas **não é linear nem obrigatória**. F01→F02→F01→F03→F02 e outras trajetórias condicionais também devem ser representáveis. F02 pode atuar **antes ou depois** da intervenção humana; o retorno à F01 antes do handoff exige rechecagem da S0. **Após humanização, uma mensagem não devolve automaticamente o caso à IA Vendedora.**

## Máquina de estados local implementada

Arquivo: `backend/f01_f02_f03_route_ledger_candidate.py`, função pura `classify_route_candidate(RouteScope, tuple[RouteEvent])`. Não substitui `journey.mjs`: aquele continua sendo uma **jornada única** com handoff humano, F03 e F02 pós-humano, e seus testes anteriores permanecem válidos. Este módulo acrescenta suporte estrutural a múltiplas voltas.

- `F01_OPEN` → F01; `S0_F02_PREHUMAN_REQUEST` → F02 pré-humano.
- `CUSTOMER_INBOUND` recebido enquanto F02 pré-humano cria **pendência**, não retorno automático. `S0_PREHUMAN_F02_RECONCILED` seguido de `S0_F01_RESUME_REQUEST` admite **nova visita candidata** a F01, ainda aguardando autenticação de cada um desses eventos pela S0.
- `S0_HUMAN_HANDOFF` transfere o candidato à fase humana. `S0_HUMAN_CLOSURE` gera novo encerramento distinto; só após isso `F03_PROPOSAL` é possível. **F03 só propõe** dados extraídos/estruturados, sem aplicar ficha ou status comercial.
- `S0_F02_POSTHUMAN_REQUEST` é pedido separado depois de F03, não efeito automático do encerramento ou da proposta. Novo inbound nessa fase só admite `S0_HUMAN_REOPEN_REQUEST`, não reativa F01. Uma segunda conclusão humana pode originar nova F03 e F02 com **outro** encerramento.
- `OPT_OUT` interrompe; `META_EXTERNAL_OUTCOME_UNCERTAIN` bloqueia continuação e exige avaliação externa, sem presumir cancelamento Meta.
- Escopo `route_id/shop_id/lead_id/case_id`, encerramento específico, sequência, tempo UTC, duplicatas, campos e fontes sintéticas são confrontados. Entrada máxima 64 eventos, nenhum texto de cliente, credencial ou PII nos retornos.

## Exemplos aceitos

`F01 → F02 → F01 → F03 → F02` com **eventos intermediários necessários**: contato do cliente, reconciliação do plano F02, solicitação S0 de retorno, handoff ao humano, conclusão humana, proposta F03 e pedido separado F02 pós-humano.

`F01 → [handoff humano] → F03 → F02` permanece válido.

`F01 → F02 → F01 → F02 → F01 → [handoff/fechamento humano] → F03 → F02` também é válido em laboratório.

O orquestrador não interpreta qualquer percurso como envio, reativação efetiva, agendamento, atendimento concluído ou permissão de leitura. **A ausência de uma etapa no log pode representar ausência de prova, não uma transição automaticamente autorizada.**

## Limites e decisão de autoridade

`RouteEvent.claimed_source = E04_SYNTHETIC_ROUTE_CLAIM_ONLY`, inclusive nos eventos com prefixo `S0_`. Isso é **nome de contrato necessário**, não assinatura, autenticação, prova ou decisão da S0. O resultado `ROUTE_SHAPE_RECHECK_ONLY` é somente compatibilidade local e mantém G01–G07, particularmente G03/G07, sem homologação. O contrato físico S0 sobre mudança de posse, novo ciclo, cancelamento anterior/Meta, sessão, histórico, autorizações e fonte real continua separado.

A integração futura das etapas poderá usar Supabase Edge Functions ↔ OpenAI API, conforme ADR aprovada, **sem inserir n8n obrigatório**. Este incremento não implanta Edge Functions, não chama OpenAI, não modifica S0/Meta, não cria plano, não reativa usuário, não envia WhatsApp, não faz merge e não processa dados reais.

**Testes:** `backend/tests/test_f01_f02_f03_route_ledger_candidate.py`; 30 verificações incluindo três trajetórias válidas, duas passagens humanas, negações por cross-tenant/caso/closure, retorno sem reconciliação, opt-out, Meta desconhecido e replay. Suite vinculada ao runner PG17 E04 apenas para regressão; todas as transições são simulações offline.
