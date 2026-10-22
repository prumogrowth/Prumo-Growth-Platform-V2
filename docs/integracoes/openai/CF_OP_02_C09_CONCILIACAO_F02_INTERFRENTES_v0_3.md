# CF-OP-02/C09 v0.3 — Conciliação da F02 com S0, S1 e Meta

**Referência:** 22/10/2026. **Estado:** [DN/DA] decisões de produto AL-IA-01 e AL-IA-07; [P/R] contrato de gatilho/estado/template; [V] dados Meta, políticas externas. **Proposta documental somente**, sem alterar [issue #6](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6), outros PRs, backend ou envios. Precedência OAI-08 v0.3 e AL-IA sobre OAI-08 v0.1/CF-OP-02 de 18–20/10 onde houver divergência.

## 1. Pontos já coerentes e correções necessárias

| Tema | Diretriz de produto vigente | Diferença no histórico a harmonizar |
|---|---|---|
| F02 após F03 | F03 **não gera automaticamente** novo plano, ainda quando aponta lacunas ou inconclusão. Pedido novo/individual autorizado da S0 pode solicitar F02 pós-humano. | Issue #6 (20/10) foi redigida para planejamento após análise de conclusão e pode ser lida como automatismo; preservar histórico, mas não executar assim. |
| F03 sem resposta conclusiva | Primeiro via **Consultor original** ou, se indisponível para aquele caso, o **seu Gestor**. A F03 não escolhe equipe. | Alternativa histórica de encaminhar diretamente para planejadora em inconclusão deve ser reavaliada. |
| Conclusão humana | Somente clique expresso do Consultor dispara F03; não cancela histórico nem reativa F01. | Janela Meta/UI e ausência de mensagens não substituem conclusão. |
| Janela Meta | 24h desde última **mensagem recebida do cliente**; template outbound não abre por si janela livre. | Não calcular desde template ou mensagem humana enviada. |
| Pós-template final | +24h só desde prova confiável **`sent`** do template final, para eventual perda por silêncio em caso/fase pré-banco elegível. | `API_ACCEPTED`, `queued` e `unknown` não satisfazem. A matriz de status C09 pós-humano continua aberta. |
| Duas falhas definitivas | Se consecutivas na mesma cadência, efeito de cancelamento e eventual `perdido` técnico pertence ao **motor determinístico S0**; um `sent` entre falhas zera contador. | Não inferir `perdido` pela sugestão da F02 ou somar falhas sem classificação Meta. |
| Templates | Catálogo filtrado por **finalidade interna + loja + versão + aprovação**; categoria Meta é dimensão diferente. Variáveis são resolvidas por S0 **no envio**. | Histórico com catálogo amplo ou slots pré-resolvidos no planejamento não é fonte de autoridade. |
| Handoff | Cancela cadeia de IA incompatível; **F01 silenciada no caso**; nova cadeia humana autorizada usa ID/finalidade novos. | Não restaurar cadeia original por reaproveitar ID ou concluir humano. |
| Pós-banco/venda | Retorno espontâneo segue humano, com histórico e status protegidos; não reabrir F01/C09 por silêncio. | Não confundir ficha viva atualizável com elegibilidade de nova prospecção. |
| Opt-out | Por concessionária, revalidado antes de envio, sem reopt-in automático por inbound. | F02 não deve ser sistema de consentimento. |

## 2. Interfaces lógicas candidatas [P/R]

**Entrada S0→F02**, quando **requisitada separadamente**: `planning_request_ref` única e idempotente; `purpose_internal` (não equivale a categoria Meta); `store_ref` e App/WABA/linha autorizados; `case_ref`/ciclo e rota `human` ou `seller_ai` **imposta pela S0**; versões de catálogo/política/estado; opt-out/limites já pré-filtrados; `eligible_template_refs[]` com versões, finalidade e slots *por fonte*; janelas e compromissos do cliente com evidência; `attempt_min/max` e teto de custos aprovados; vínculo a encerramento F03 apenas quando juridicamente e funcionalmente pertinente. **Não são nomes de campos físicos homologados.**

**Resposta F02→S0**: `proposed_attempts[]` com ordem, `template_ref` + versão dentre permitidos, horário candidato, finalidade e justificativa/fonte; `final_template_candidate` explicitamente **separado**, ambiguidade/erros/pedidos de revisão. Não retorna template criado, variável final, `sent` confirmado, status comercial ou decisão de atribuição. Uma sugestão de compromisso datado pelo cliente não equivale a opt-in ou autorização de contatar.

**S0 antes de cada disparo:** revalida canal por loja, versão/status do template, finalidade, consentimento/opt-out, janela, horário, limite/cadência, caso atual, atribuição, corrida com inbound/handoff, custos e reserva idempotente; **resolve slots no disparo**; envia via Meta e concilia evidências. Após falha ordinária, não chama F02 arbitrariamente; só replanejar mediante pedido novo da S0 se template antigo ficou inelegível.

## 3. Máquinas temporais não intercambiáveis

| Relógio | Origem verificável | Critério objetivo | Efeito possível |
|---|---|---|---|
| **W24-META** | Timestamp do último inbound **do cliente** | T+24h; inbound novo altera marco, outbound não | Permissão de texto livre no canal; **não** conclusão humana/F03 |
| **H-CLOSE** | Evento de conclusão humana autenticado S0 | Clique expresso válido; múltiplos eventos possíveis | F03 interna silenciosa, cutoff imutável de cada fecho |
| **C09-FINAL** | Comprovante confiável `sent` do **template final** correlacionado | +24h sem resposta, opt-out/caso/estado/fase elegíveis e sem corrida | S0 **pode** decidir `perdido` por silêncio segundo matriz ratificada [R], não ato de F02 |

**Contraprovas mandatórias:** `API_ACCEPTED` sem `sent` não abre C09; cliente manda inbound posterior ⇒ não cumprir condição de silêncio; `cadastro enviado ao banco`/`vendido` ⇒ não usar C09 de silêncio; `em atendimento pelo operador` e `cadastro enviado ao operador` requerem semântica/fase/aceite S0 próprios, não assumir que são elegíveis ou proibidos sem matriz.

**Falha técnica de transporte** é quarto assunto **distinto** dos três relógios: eventos com classificação definitiva do provedor e prova de correlação da mesma cadência, contador reiniciado em `sent`. S0/Meta, não OpenAI, controlam cancelamento e transição correspondente. A quantidade do esforço regular permanece **parametrizada**: faixa histórica de não respondentes iniciais até 2 e pós-atendimento geralmente 2–5, ambos com template final separado e confirmação de limites [R]; nenhuma autorização de envio ilimitado.

## 4. Dependência de equipe e UI

- Atendimento humano concluído pode permanecer disponível ao Consultor durante janela Meta, sem apagar histórico; UI pode retirar conversa da lista ativa **somente quando** critérios de conclusão e janela expirarem, sem encerrar atendimento não concluído.
- Se pessoa retorna enquanto caso pertence a humano, mantém o **profissional atual autorizado** ou redistribuição S0/S1 válida. `intake_paused` de novos leads não significa incapaz de responder casos antigos.
- Suspensão/revogação real deve seguir redistribuição/capacidade e ACL S0/S1 da loja, nunca escala inventada pela F02. Se o original está indisponível para a **pendência F03**, o seu Gestor é caminho de escalonamento segundo decisão posterior AL-IA-01.
- Identificação do texto livre enviado por humano pertence ao backend/Meta com autoria comprovada, não a texto gerado por F02; leitura interna UI não se prova por webhook `read` Meta.

## 5. Decisões abertas por proprietário

| ID | O que precisa ser fechado | Owner | Evidência exigida |
|---|---|---|---|
| F02C-R01 | Nome/evento físico do pedido F02, idempotência e vínculo a encerramento humano | S0 + OpenAI | Versão contratual, entrada/saída e teste de cadeia separada |
| F02C-R02 | Lista de finalidades internas × categoria Meta × templates/versões × concessionária | S0 + Meta + Prumo | Catálogo/ACL compartilhável e regras de mudança |
| F02C-R03 | Matriz exata de estados **e fases** C09, especialmente caso humano e `cadastro enviado ao operador` | S0 + S1/Meta | Matriz aprovada com negativos pós-banco |
| F02C-R04 | Prova de `sent`, eventos definitivos/incertos, contador e duplicação de webhook | Meta + S0 | Recibos e teste idempotente com ordem fora de sequência |
| F02C-R05 | Escopo pós-humano, limites e horários; individual versus cadeia, concorrência e cancelamento | S0 + S1 + OpenAI | Testes com handoff, inbound e template individual |
| F02C-R06 | Redistribuição e relação entre `intake_paused`, suspensão, atribuição e roteamento gestor | S0 + S1 + FV | Contrato de disponibilidade por caso e revogação |
| F02C-R07 | C04 opt-out e elegibilidade LGPD/Meta, limite de gasto/retenção | S0 + Meta + privacidade | Política aprovada e prova de transporte, não texto do modelo |

Todos **ABERTOS [R/V]** neste pacote; documento da OpenAI não possui mandato para ratificá-los sozinho.

## 6. Provas e cruzamentos E02

- **SYN-17/19/20, 47/48/49:** handoff, não F02 automática, plano novo pós-humano e template individual.
- **SYN-50/51/52:** teste C09 com `API_ACCEPTED` negativo, `sent` verdadeiro e inelegibilidade pós-banco.
- **SYN-53/54/55/56:** duas falhas definitivas consecutivas, reinício por `sent`, template pausado e renderização tardia de slots.
- **SYN-39/40/41:** fluxo humano e elegibilidade por caso.
- **CF2-T01..20** (issue #6), **OAI8-01..10**, **OAI-T** legados: sobreposições candidatas, sem duplicar contagem.

**Gate de saída:** ratificação expressa S0/Meta/OpenAI dos registros F02C-R01..R07 + casos negativos documentados com versão e owner. A OpenAI pode preparar testes e esquemas candidatos, mas **não** executar Meta, classificar prova de canal como fato bancário, decidir estado comercial ou liberar E04/E05 por conta própria.
