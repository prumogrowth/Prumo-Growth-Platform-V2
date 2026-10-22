# OAI-07 v0.3 — Desfechos, estados, avisos e roteamento (candidata)

**Data:** 22/10/2026. **Natureza:** [DN/DA] decisões de produto; [P/R] assinatura/roteamento físico sujeitos à S0/S1/FV; [V] Banco, Meta e LGPD. Sem endpoint, modelo, status físico ou envio homologados.

## 1. Precedência

Esta é a referência operacional atual da frente OpenAI para assuntos de `OAI_07_DESFECHO_ENCAMINHAMENTO_PREFERENCIA_CANAL_v0_1.md`, cuja redação divergente permanece histórica. Ler AL-IA-01 ``4–6, AL-IA-04 DEL-01/03/05/07/09/10/17/20 e AL-IA-07. Complementa OAI-01/OAI-05/OAI-08/E01 v0.3. **Não converter decisão funcional em permissão SQL da S0.**

## 2. A conclusão humana é evento técnico, não resultado comercial

A F03 só inicia depois de `Concluir/Encerrar atendimento` acionado **expressamente pelo Consultor autenticado** e aceito pela S0. Janela de 24h da Meta após último inbound é independente e **não** conclui o humano; cada fechamento válido tem cutoff próprio. O Consultor não edita ficha, mesmo quando F03 sinaliza dúvida.

A F03 pode interpretar e propor com **fontes daquele cliente na mesma loja até cutoff**:
- negociação com interesse confirmado / cadastro pronto para remessa;
- desistência inequívoca do cliente com motivo;
- dúvida, contraproposta, compromisso de retorno com data/ambiguidade;
- necessidade real de complemento de dados essenciais;
- desfecho inconclusivo, contestação ou conflito de evidências.

F03 não classifica fato inexistente, nem equipara relato de aprovação à prova bancária. Interpretação é **proposta conversacional**, não status persistido. Mantenha resultado técnico, avaliação conversacional, proposta de transição e comprovação de fato externo em **campos/sequências conceituais distintos**; schema final [R].

## 3. Oito estados comerciais, guardados pela S0

Estados vigentes (sem acrescentar nono): `aguardando primeiro disparo`, `primeiro disparo enviado`, `em atendimento pela IA`, `em atendimento pelo operador` (nome de exibição futuro Consultor), `cadastro enviado ao operador`, `cadastro enviado ao banco`, `vendido`, `perdido`.

A F03 **pode propor/desencadear** mudança comercial, inclusive `perdido` por desistência **explicitamente demonstrada**, e S0 decide **se, quando e como executar** com transição, status atual, motivo e versão autorizados. Não criar catálogo de motivos ou lista de transições por inferência: permanecem [R] S0. **Não reproduzir o veto antigo e universal a `perdido` em F03.**

**Exceções que não se flexibilizam:**
1. `vendido`: exclusivo ato **manual do Consultor humano autorizado**, com evidência real do Banco de venda/pagamento efetivado. Nenhuma saída F01/F02/F03 registra venda.
2. `cadastro enviado ao banco`: exige **remessa efetiva comprovada**, não intenção/encaminhamento/fiche pronta. A via direta pela plataforma depende de autorização bancária **adiada**, alternativa atual é remessa humana oficial quando aplicável.
3. `cadastro enviado ao operador`: exige entrega real da ficha a destinatário/fila apropriada e transição S0 aceita, não mero desfecho positivo.
4. **Negativa bancária definitiva**: ato humano autorizado com prova do Banco, distinto da desistência do cliente e da perda por silêncio ou falha Meta. Pedido de complemento/correção do Banco não é negativa.
5. **Perda técnica por duas falhas definitivas consecutivas de template**, com `sent` verdadeiro reiniciando contador, decorre de motor determinístico S0/Meta, não de avaliação arbitrária da F02/F03.

## 4. Ação após a avaliação F03

- Campo **essencial** ausente ou contradição legítima não resolvida: S0 devolve pendência **preferencialmente ao Consultor original**; somente se **indisponível para aquele caso**, ao seu Gestor que decide resolver quando autorizado ou remanejar. `intake_paused`, sozinho, **não comprova indisponibilidade**. F03 não escolhe titular nem lê equipe irrestrita; S0/S1 valida grants e atribuição atual.
- Campo **apenas opcional** ausente: não criar revisão humana por esse motivo e não impedir avanço que dependa só dos essenciais.
- Desfecho inconclusivo por si não significa ordem para F02. A pendência segue prioritariamente à via humana; recontato pós-humano só mediante pedido **independente/autorizado da S0**, conforme OAI-08 v0.3.
- Falha crítica da F03: incidente técnico com diagnóstico/reparo dos responsáveis, jamais fallback rotineiro de edição cadastral pelo Consultor. Logs da falha não expõem dados privados/segredos.
- Quando retorno espontâneo ocorre após `vendido` ou `cadastro enviado ao banco` na **mesma concessionária**, segue humano; F01 permanece bloqueada nesse contexto. Um **novo caso humano** pode ter nova conclusão/F03 sem reescrever venda/remessa passada.
- Ficha viva única continua atualizável via S0 mesmo após remessa/venda histórica, sem notificações rotineiras apenas pela existência dessa atualização.

## 5. Handoff e preferência de comunicação

Todo handoff **originado pela IA** precisa ter motivo operacional curto e compreensível ao humano; S0 determina fila/notificação e fallback quando geração falha. Motivo não deve revelar roster, credenciais ou dados de outra concessionária. A F01 cessa fala definitivamente no caso após handoff.

A F01 pode modular texto/áudio pelo pedido explícito e padrão **reiterado**, sem transformar um único áudio em preferência permanente. Transcrição e TTS exigem política de mídia, custo e autorização; Meta transporta. Mensagens de texto livre humanas têm identificação inserida pelo backend conforme regra Meta, **não** por simulação de F01. Confirmação final por e-mail não foi homologada como exigência.

## 6. Campos lógicos e testes para conciliação [P/R]

Resposta lógica proposta F03: `conversational_assessment` com resultado, razão, referências e incerteza; `commercial_transition_advisory` separado, com status/motivo/fonte e elegibilidade **a ser calculada pela S0**; `missing_fields`, `conflicts`, `followup_need_advisory` somente consultivos; `handoff_reason` para handoff feito pela F01, quando pedido. **Não são nomes canônicos aprovados.**

Cenários novos a inserir na E02: desistência clara versus negativa bancária, ficha pronta versus remessa real, `vendido` humano, campos opcionais, retorno pós-venda/remessa, retorno ao Consultor original após pausa só de novos leads, atualização de ficha após remessa, falha F03 e aviso operacional sem vazamento.

**Ratificação necessária:** S0 para transições/motivos e evidências; S1/FV para devolução de pendência e leitura sem edição; Meta para mídias/assinatura; Banco somente quando for autorizada investigação futura. **Sem teste executado nesta revisão.**
