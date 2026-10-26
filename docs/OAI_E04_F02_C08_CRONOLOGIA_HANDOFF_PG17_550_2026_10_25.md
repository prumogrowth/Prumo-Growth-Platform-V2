# E04 — cronologia verificável da cadeia C04/C08 anterior ao atendimento humano

**Data:** 25/10/2026, fuso America/Recife. **Código certificado:** `49092b171bc203ec3d4d2dc902c255d499258b11`. Branch exclusiva S0/F02/F03, PR #1 Draft, sem merge ou deploy. **Ambiente:** GitHub Actions com PostgreSQL 17 descartável, Node S2 em SHA fixado.

## Lacuna resolvida nesta etapa

O comprovante local anterior verificava plano/tentativa/evento C08 cancelados, porém não amarrava quando a cadeia havia sido criada em relação ao encaminhamento ao humano. Isso permitia, no laboratório, apresentar um plano criado **depois** do início do caso como se fosse anterior ao handoff. O novo gate exige cronologia física S0, antes da assinatura de um atestado.

## Implementação realizada

- `backend/s0_f02_legacy_cancellation_witness_local.py`: a consulta local traz agora `planos_recontato_sinteticos.criado_em`, `envios_template_sinteticos.criado_em` e `agendado_em`, além dos estados e cancelamentos C08 já verificados.
- Busca, sempre do banco da S0, os marcos `casos_humanos.criado_em` (início do caso), `atribuicoes_humanas.atribuida_em` (atribuição formal ao operador, pelo identificador de atribuição da S0), e `cfi01_human_closure_events_local.registrado_em` (encerramento autenticado da sessão de testes). Não aceita marcos apresentados pelo JavaScript/modelo.
- Exige `caso.criado_em <= atribuicao.atribuida_em <= encerramento.registrado_em <= instante_atual`; plano antigo e tentativas devem ser anteriores ao início do caso e preservarem sua ordem de criação; `agendado_em` deve superar a criação da tentativa.
- Cancelamento local de planos, tentativas e seus eventos C08 deve ocorrer entre o início do caso humano e o instante atual, com coerência entre os carimbos de cancelamento do plano, tentativa e evento. São aceitas pequenas diferenças de registro do mesmo evento local dentro de janela delimitada (60 segundos); isso **não** equivale a precisão ou autenticidade de provedor externo.
- Novo estado `LEGACY_CHRONOLOGY_REVIEW_REQUIRED` impede a emissão do comprovante quando os marcos são incompatíveis, salvo quando a camada anterior da S0 já detectou adulteração e bloqueou por `S0_REVIEW_REQUIRED`. Essas recusas antecipadas não são erros a contornar.
- O resumo SHA-256 protegido pelo HMAC passa a incluir também os novos horários físicos de planos/tentativas e os três marcos do atendimento humano. Repetição de comprovante compara novamente os registros atuais com o snapshot anterior: modificações alteram a assinatura e exigem revisão.
- O fixture da bateria C08 anterior foi atualizado para situar **explicitamente** planos e tentativas sintéticos antes da criação do caso. Essa data retroativa é apenas uma configuração do teste, não valida qualquer possibilidade de falsificação de relógio em ambiente real.

## Certificação

- **GitHub Actions SUCCESS:** https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40250514389
- **Python S0:** 84/84 PASS.
- **Python F02/F03:** 466/466 PASS, incluindo **300 testes físicos PG17**.
- **Node da S2 fixada:** 269/269 PASS.
- **Total:** 550/550 Python + 269/269 JavaScript = 819 verificações em suítes distintas, **não** 819 jornadas ponta a ponta nem os 70 oráculos originais E02 homologados.
- **Novos testes:** 10 físicos #291–300 (cadeia e tentativa pós-handoff, cancelamento retroativo, tentativa anterior ao plano, agendamento cronologicamente inválido, caso/atribuição adulterados, alteração após o HMAC e data futura); 5 unitários de validador temporal e vinculação do snapshot.
- Primeira execução da rodada (#40250232292) apontou três expectativas específicas incorretas: as adulterações do caso ou da atribuição são bloqueadas **antes** pelo validador S0 existente (`S0_REVIEW_REQUIRED`), não chegam ao novo gate cronológico. Os testes foram corrigidos para reconhecer o bloqueio real já existente; a execução integral posterior #40250514389 obteve `SUCCESS`. Nenhum comportamento de segurança foi afrouxado.

## Limites e próximas dependências

1. O gate usa **carimbos internos sintéticos de banco**, cujo histórico de criação em tabelas C04 já existentes não é comprovadamente imutável. Hash e HMAC atestam o snapshot observado e detectam mudanças posteriores ao selo, mas não provam que as datas eram verdadeiras antes de a S0 observá-las. Precisamos de uma fonte transacional confiável de eventos de criação/cancelamento para uma etapa futura real.
2. Uma tentativa antes `reservado` continua recebendo `RESERVED_PREVIOUSLY_EXTERNAL_UNKNOWN` e **não** comprova que a Meta interrompeu o processamento. Nada foi enviado ou cancelado externamente por esta etapa.
3. Não houve mudança no agendador C04 pré-humano, nas migrações de produção ou em workflows de outras frentes. O certificado é local e não autoriza mensagens, criação de planos, alteração de ficha, gestão de dinheiro ou mudança comercial.
4. Ainda falta um contrato **novo e separado** de planejamento pós-humano com origem/autorização humana verificável, consentimento e opt-out reais, políticas de templates/Meta, idempotência, frequência/horário, estados de transporte e decisão do S0. Não usar o comprovante cronológico como autorização de execução.
5. Governança: frentes em branches independentes; integração futura em branch específica, revisão/autorização antes da `main`. Issue #3 é apenas auditoria não autorizativa de otimização da S1, sem alterações nesta rodada. Supabase hospedado, Meta, OpenAI API e dados reais intocados.
