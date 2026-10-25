# E04 interfrentes — F02 pós-humano x S0/C04 física: incompatibilidade certificada

Data: 25/10/2026. Escopo: laboratório E04, branch feat/oai-s0-f03-history-port-20261023, PR #1 Draft. PostgreSQL 17 descartável no GitHub Actions; nenhuma alteração ao Supabase hospedado, cliente real, Meta, OpenAI API, cobrança, merge ou deploy.

## Contratos efetivamente confrontados

1. Código REAL e FIXADO da branch S2 (`ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c`): `plan-lifecycle.mjs` exporta `reconcileF02Plan` que, perante um plano sintético de rota humana e pós-humano validado, emite `READY_FOR_S0_RECHECK`, nunca autorização de disparo. A journey F01→humano→F03→F02 está coberta por testes nativos Node.
2. Código S0 já existente: migrações físicas locais `202610170012_s0_recontatos_sinteticos.sql`, `202610170016_c04_elegibilidade_optout_sintetico.sql`, `202610170017_c04_estado_replay_plano.sql`. C04 tri-state `verificar_contato_sintetico` reconhece somente evidência de elegibilidade FICTÍCIA e opt-out; a função vigente `agendar_recontatos_sinteticos` **rejeita ciclo com qualquer caso humano**, incompatível com um novo plano pós-humano.
3. Adicionado `backend/s0_f02_posthuman_compatibility_local.py`, porta somente de leitura vinculada à S0/F03: a evidência original deve passar pela prova de histórico F03 (HMAC, proposta, valores fictícios textuais, identidade, versões/CAS e corte). O código valida forma estrita do resultado JavaScript da F02, recupera na S0 lead/caso/ciclo/canal corretos, consulta diretamente `verificar_contato_sintetico` no banco físico, verifica opt-out, autorização fictícia e presença de plano legado ativo.
4. Resultado positivo do alinhamento de todos os requisitos fictícios é **`LEGACY_C04_HUMAN_CASE_INCOMPATIBLE`**, NÃO `READY`, NUNCA SEND. Um resultado JS isolado é sempre insuficiente. Qualquer opt-out, ausência de evidência, plano antigo não cancelado, desvio de tenant/canal, resposta Meta queued ou falsificação de flag `sendNow` também bloqueia.

## Prova física executada

GitHub Actions SUCCESS: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40196499065
Commit de código certificado: `bc949dd6b746db8827e3d6f2018246b440c6519b`.
- Testes S0 existentes: **84/84 PASS**.
- Testes F03 + porta F02/S0: **390/390 PASS**, incluindo **249 casos físicos F03 no PostgreSQL 17** e 8 testes unitários F02 adicionados.
- Código S2 em Node nativo: **269/269 PASS**. Total Python **474/474**; total conjunto 743 verificações de duas suítes distintas, NÃO 743 jornadas end-to-end de negócio.
- Testes físicos de integração F02/S0 241–249 passam: JS do S2 realmente avaliado; opt-out, ausência/revogação de evidência, canal fora do caso, plano IA legado ativo, Meta queued, saída JS com permissão inventada, autorização S0 inválida, proibição de agendamento e compatibilidade insuficiente de C04 após humano.
- O primeiro CI desta etapa falhou porque a bancada F03 ainda não montava as tabelas físicas C04. O runner `scripts/run-s0-f03-pg17-local.sh` passou a carregar as **três migrações C04 originais somente no banco PG17 descartável**; a execução integral seguinte passou. Nenhuma migração foi aplicada em banco remoto.

## Gate arquitetural pendente (não contornar)

É preciso definir um contrato físico S0/C04 **separado e explícito** de elegibilidade pós-humano. Não remover o bloqueio de casos humanos no agendador pré-humano existente nem simplesmente permitir `ownerRoute=human` vindo da IA. O novo caminho precisará de: solicitação S0 independente autenticada e autorizada por papel S1/gestor, prova de fechamento do caso e contexto da mesma pessoa/loja, cancelamento atestado da cadeia IA antiga, finalidade/consentimento compatíveis, opt-out final e rechecado, catálogo/versionamento/categoria dos templates, política de frequência e respostas Meta reais quando forem autorizadas, janela e relógio, idempotência/controle concorrente, trilha de auditoria, e nunca usar a pontuação F03 como decisão comercial.

A captura de identidade/sessão no teste F03 usa fixture de autoridade histórica; não é homologação de sessão real. Os 70 SYN E02 permanecem documentais e ainda exigem execução e aceite conforme seus gabaritos originais. Esta etapa é o mapeamento/prova física do ponto de incompatibilidade, **não a resolução operacional do recontato pós-humano**. Supabase hospedado somente na fase de integração geral futura decidida pelo responsável.
