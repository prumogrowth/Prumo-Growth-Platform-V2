# S0 + S1-002 — Marco de integração da issue #10: evidência humana e redistribuição seletiva (20/10/2026)

**Status: implementação sintética isolada, CI de integração sujeito a conferência de logs.** PR #5 continua Draft em `feat/s1-002-equipe-prumo`; branch S0 base não modificada, sem merge, Supabase hospedado ou mensagens reais.

## Contexto

A decisão da issue #10 exige que pausa de distribuição **não** suspenda a conta, que casos sem substituto continuem com seu titular, que atendimento humano já iniciado nunca seja redistribuído automaticamente e que somente operadores disponíveis da **mesma equipe** com grant da loja possam receber redistribuição. S0 não tinha frente ativa; o responsável autorizou aperfeiçoamentos isolados desse contrato. Mudanças estão como fixtures PostgreSQL locais, sem migration operacional nem alteração da base S0.

## Acordo de prova S0 e fronteira de confiança

`supabase/tests/s1_054_issue10_s0_prova_redistribuicao_local_only.sql` modela uma tabela privada `s0_contato_humano_prova_10` vinculada à chave composta (concessionária, caso), **ID exato de atribuição atual**, estado `SEM_INICIO_CONFIRMADO` ou `INICIADO`, versão e referência a um evento sintético de origem. A trilha `s0_contato_humano_eventos_10` é append-only, com fonte única por concessionária.

`s0_registrar_contato_humano_fixture_10` é **apenas produtor simulado** e somente executor PostgreSQL local: trava o caso, verifica a atribuição atual e revalida o estado em transação. Não permite voltar de `INICIADO` para `SEM_INICIO_CONFIRMADO`; rejeita evidência sobre atribuição obsoleta; duplicação da mesma prova negativa é idempotente. A ordem de locks do caso/atribuição serve de contrato para um futuro produtor S0 real.

**Prova negativa de início não é inferida da ausência de evento:** sem registro explícito `SEM_INICIO_CONFIRMADO` válido para a atribuição exata, o caso permanece no titular. Este ensaio **não comprova** que o WhatsApp/Meta ou um operador enviaram uma mensagem humana real. Em produção, o S0 precisará produzir um marcador confiável de primeira resposta humana confirmada e snapshot de ausência de início, sob a mesma fronteira de commit/lock. A fixture não autentica canal de envio nem captura dado real.

## Redistribuição S1 com autoridade e conservação de titular

`s1_redistribuir_pausado_provas_10(gestor,operador,versao_de_pausa)` exige executor interno, gestor da equipe, conta ativa e `intake_paused=true` com revisão CAS atual; não altera concessões ou conta. Inspeciona atribuições da pessoa, **trava caso e atribuição**, verifica prova S0 para a atribuição corrente e somente tenta escolher destino se o estado for `SEM_INICIO_CONFIRMADO`.

Destino elegível deve simultaneamente pertencer à equipe do mesmo gestor, estar ativo e não pausado, possuir grant vigente de operador na concessionária original (que precisa estar ativa), não ser o titular anterior e ter menor carga. Ausência de substituto, prova inexistente, início humano ou caso terminal **não encerram a atribuição atual**. Quando existe destinatário, a transferência fecha a atribuição anterior, cria **uma** nova na mesma concessionária, passando pelo guarda existente I2 e grava evento append-only com as duas atribuições e versões S0/S1. Repetição não desloca outras atribuições nem cria dois titulares.

**Importante:** o comando de pausa `s1_definir_disponibilidade_leads_10` retorna `DEFERRED_S0_PROOF`; a reconciliação posterior é separada em sandbox. O front não pode anunciar redistribuição final antes de confirmação transacional. A integração ponta a ponta deve definir se o status do botão é “pausa aplicada / redistribuição pendente”, com eventual rechecagem.

## Cobertura experimental

`supabase/tests/s1_054_issue10_s0_seletiva_aceite.sql` repete os 11 gates anteriores da issue #10 e acrescenta doze novos: prova de não início e início, replay da prova; pausa sem redistribuição prematura; quatro situações de caso; destino na mesma equipe; ausência de substituto de loja preserva titular; iniciado e caso desconhecido preservados; reconciliador idempotente; estado humano iniciado irreversível; atribuição antiga recusada; chefe de outra equipe recusado; nenhuma RPC pública para registrar prova nem redistribuir; retomada invalida versão anterior. Os dados gerados são inteiramente sintéticos e toda prova de domínio faz ROLLBACK ao final.

O workflow `.github/workflows/s1-002-issue10-intake-local.yml` executa regressões S0/S1 e I11/I12 **antes** das fixtures corretivas, depois executa os 11 testes iniciais e os 23 gates integrados sob PostgreSQL 17 descartável. A evidência final deve registrar run, SHA, marcadores e falhas/correções antes do aceite.

## Dependências abertas antes do marco da pausa para auditoria

- **Prova real do S0:** mensagem enviada por humano com autoria e confirmação de envio, registro de início imutável, controle de ordem de eventos entre Meta/canais e transação com remanejamento. Prova sintética é só teste de contrato.
- **Transferência manual excepcional sem grant da loja:** ainda exige RLS restrita por caso em todos os objetos, documentos, conversas e projeções S0; não há permissão excepcional ativa na fixture.
- **Indicadores de leitura/resposta:** contador de não lidas, bolinha após leitura sem resposta e visualização do gestor independente de leitura do operador pertencem às projeções S0; não foram implementados nesta etapa.
- **Nova API assinada de gerência:** gateway existente I18–I31 ainda possui assinaturas legadas de pausa global; sem autorização humana, assinatura HMAC versionada e endpoint adaptado não há operação real.
- **Transações/concorrência:** adicionar teste simultâneo de primeira resposta humana e redistribuição com múltiplas conexões e eventual bloqueio real do operador já iniciando atendimento, antes de declarar o problema encerrado.

**Marco proposto para uma pausa planejada de alinhamento:** concluir o pacote da issue #10 em sandbox — S0 evidência sintética, S1 seletiva, exceção manual segura por caso com regressões negativas, contrato dos indicadores e documentação de fronteiras — e então interromper incremento funcional antes de começar hardening I31/produção. Realizar nessa ordem as três ações pedidas: (1) perguntas de ambiguidade/decisão, (2) auditoria geral S1+interfaces S0, (3) limpeza, rastreabilidade e consolidação da documentação. Nenhum passo depende de tocar o banco hospedado.

**NO-GO produção, deploy e merge.** A qualidade do pacote não deve ser expressa como porcentagem global.

## Evidência CI verificada — prova seletiva + concorrência

**[GitHub Actions #39506166135 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39506166135)**, código testado SHA `400062d6eef9d1dd2a646f53f332075e96100889`, job `118915499582` concluído com sucesso. Logs inspecionados:

- **ISSUE10-01..23 = 23/23 marcadores únicos PASS**, incluindo 11 gates anteriores da separação conta/pausa e 12 novos gates de prova de início humano S0 e seleção transacional S1.
- **ISSUE10R-01..04 = 4/4 PASS**, sob **duas sessões PostgreSQL reais**. Cenário 1: prova positiva de resposta humana mantém lock de caso até commit; o reconciliador concorrente aguarda e preserva o titular. Cenário 2: a redistribuição adquire lock primeiro, move a atribuição e confirma; um evento humano tardio dirigido à **atribuição antiga** é recusado com conflito `ATRIBUICAO_NAO_ATUAL`. Nenhum cenário criou dois titulares.
- Todos os testes históricos S0/S1, incluindo I11/I12 com as premissas antigas, foram executados **antes** das fixtures corretivas no mesmo job, para detectar regressão técnica. Não se deve confundir a aprovação dos contratos históricos com aprovação da antiga regra de suspensão da conta.
- A tentativa anterior [#39506096877](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39506096877) não criou jobs porque o nome de uma etapa com dois-pontos não estava entre aspas no YAML. A correção gerou o CI verde acima. Não contar o workflow inválido como teste.

**Aceite restrito do pacote S0-prova/S1-seletiva:** simulador SQL local e isolamento transacional aprovados. **Ainda não há produtor de evidência Meta/GoTrue humano real nem transferência manual sem concessão geral à loja, API versionada de pausa, projeção de leitura ou autorização por caso.** A prova negativa de início é marcada pelo próprio fixture de teste, não por um canal real. A execução não é homologação operacional; branch S0 base, produção e Supabase hospedado continuam intactos.

**Marcação de revisão futura:** quando transferência por caso e indicadores de mensagens também estiverem cobertos por regressões locais e possuírem contratos explícitos, interromper novos incrementos para as três sessões ordenadas de alinhamento, auditoria geral S1/S0 e documentação consolidada.