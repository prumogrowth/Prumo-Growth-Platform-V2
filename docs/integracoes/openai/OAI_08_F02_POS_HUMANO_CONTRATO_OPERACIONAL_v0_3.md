# OAI-08 v0.3 — Planejamento F02 e nova cadeia pós-humana (candidata)

**Data:** 22/10/2026. **Estado:** decisões de produto [DN/DA]; contrato F02, limites e C09 [P/R]; condições Meta/LGPD [V]. Sem agendamento persistido, envio ou integração executada.

## 1. Precedência e papéis

Esta versão é o contrato operacional de trabalho para o assunto de `OAI_08_CONTRATO_PLANEJADORA_POS_HUMANA_CF_OP_02_v0_1.md` (histórico). Fontes: AL-IA-01 `3–4/6, AL-IA-04 DEL-09/10/21/24/25 e AL-IA-07 XFR-02/03/04/05/11; CF-OP-02 issue #6 ainda em revisão. OAI-01/OAI-05/OAI-07/E01 v0.3 prevalecem em suas fronteiras.

**F02 é planejamento interno, não interlocutora:** recebe somente **instruções globais próprias**, sem campo administrativo de comportamento e sem instruções por concessionária. Não gera texto livre de template, não registra envio, não decide opt-in, não envia mensagens e não altera comercial diretamente. S0 valida/agenda/cancela; Meta executa/prova transporte.

## 2. F02 antes e depois do atendimento humano

- **Abordagem inicial**: mecanismo próprio separado da cadeia de F02. Sem resposta ao primeiro template, não declarar atendimento IA iniciado. O contexto e elegibilidade da lista inicial continuam com S0/Meta.
- **Durante caso sob IA, sem handoff**: S0 pode pedir plano elegível conforme estágio; resposta/inbound cancela incompatíveis, e F01 só fala se a S0 continuar autorizando posse IA.
- **Após handoff**: plano de IA antigo incompatível permanece cancelado. F01 nunca volta a falar naquele caso. Conclusão humana **não aciona automaticamente** F02; F03 analisa após clique e devolve lacunas/desfecho principalmente à via Consultor/Gestor.
- **Novo plano pós-humano**: pode existir apenas se S0 fizer pedido separado/autorizado (pedido humano ou outro motivo elegível após avaliação F03), com **nova identidade/finalidade**, sob responsável humano e sem ressuscitar cadeia cancelada. Pedido manual de **um único template** segue S0→Meta, não exige F02.
- Novo contato após `vendido`/`cadastro enviado ao banco` fica sob humano; a existência de venda passada **não** autoriza cadeias F02, proposta de nova contratação nem reabertura de F01. A S0 precisa considerar caso atual, não somente status antigo.

## 3. Templates, limites e revalidação

F02 recebe **somente opções previamente aprovadas, ativas, da WABA/concessionária correta e elegíveis à finalidade interna solicitada**, versão congelada e condições de uso. Categoria Meta (`MARKETING`/`UTILITY`) e **finalidade interna** não são sinônimos; um template pode ter múltiplas finalidades, cada qual com elegibilidade separada. Parâmetros ``slot→fonte` são versionados e preenchidos **exclusivamente no momento do disparo pela S0**, sem valores inventados pela F02.

As referências históricas são **provisórias**: para não responsivos inicialmente, até duas tentativas regulares e template final separado; para já atendidos/engajados e silenciosos, normalmente **duas a cinco** tentativas regulares e template final **separado**. Não assumir teto irrestrito nem definir número final sem aceite normativo. Ordem, horários, intervalo, motivo, política de contato e opt-out são revalidados pela S0.

Se template é pausado/invalidado pela Meta, **S0 pode** pedir replanejamento de alternativas aprovadas. Falha ordinária de envio **não** chama F02. Cada loja possui opt-out próprio; novo inbound espontâneo **não** restaura opt-in de modo automático.

## 4. Três marcos temporais e falhas definitivas

1. **Janela Meta**: até 24 horas da última mensagem *recebida do cliente*. Template outbound não abre sozinho janela de texto livre.
2. **Conclusão humana**: somente ato explícito do Consultor; dispara F03 e não ocorre automaticamente por vencimento Meta.
3. **C09, silêncio após template final**: template final planejado separadamente, com referência histórica de ~24h após última tentativa regular quando ainda elegível. **Somente envio efetivo `sent` comprovado** inicia a contagem seguinte de +24h de silêncio para possível `perdido` pré-banco elegível, conforme matriz C09 **a ratificar pela S0**. `queued`, `API_ACCEPTED` ou `unknown` não bastam. Nunca aplicar C09 por silêncio a `cadastro enviado ao banco` ou `vendido`; `cadastro enviado ao operador` continua dependente de estado/fase homologados.

**Duas falhas DEFINITIVAS consecutivas**, correlacionadas à mesma cadeia, cancelam tentativas remanescentes e produzem **`perdido` com motivo TÉCNICO via motor S0**, conforme interface Meta/S0; um envio `sent` comprovado entre elas zera contador. Timeout/aceite HTTP/incerteza não são falha definitiva e não autorizam perda. Esta transição **não** é decisão livre da F02.

## 5. Requisição/resposta conceituais [P/R]

**Entrada S0 → F02**: operação `recontact_plan`; request/contract version; concessionária/WABA/caso/ciclo autorizados; solicitante e finalidade; roteamento `human` ou `seller_ai` **determinado pela S0**; catálogo filtrado de `template_ref` + versão + finalidade; escopo de dados/consentimento e janelas; limites; compromissos de retorno com fonte e grau de certeza; versão do caso/plano e política.

**Resposta F02 → S0**: `proposed_attempts[]` (ordem, template e versão dentre elegíveis, horário candidato, motivo e fonte), `final_template_candidate` separado, riscos/ambiguidade ou recusa. **Nunca** fornece texto editado, valores de variáveis aprovadas, confirmação de envio, status comercial, atribuição ou relógio C09 já realizado.

Toda intenção planejada deve ser revalidada na execução quanto a versão, opt-out, janela, finalidade, status atual, concorrência com template individual, destinatário, vínculo App/WABA e prova do provedor. S0/Meta decidem o que de fato ocorreu.

## 6. Gate de aceitação [R]

Exige conciliação com C05/C08/C09 na issue #6, prova real de `sent` Meta, matriz de estado/fase pré-banco, concorrência de template único e cadeia, cancelamento por inbound/handoff, impossibilidade de reativar venda/IA, catálogo de finalidades e testes sintéticos. **Nenhum teste ou envio realizado por esta versão documental.**
