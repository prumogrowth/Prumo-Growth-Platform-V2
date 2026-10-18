# WA-07 — Contrato Meta: janela 24h, templates humanos e prova do último envio | CF-OP-02 v0.1

Data: 18/10/2026. **[D-negócio] direção confirmada; [P/R] protocolo/eventos e sinais; [V] regras reais Meta/LGPD/Banco.** Proprietária: frente WhatsApp/Meta, subordinada às decisões DEC-WA-01/02/03/05, WA-01A/B/C, WA-05/06 e contrato S0 CF-OP-02. Não é homologação Graph API, template real ou webhook implantado. Issue #6/PR #7 coordenam.

## Propriedade exclusiva Meta

1. **Canal por concessionária.** DEC-WA-05: cada concessionária é titular de sua própria Meta App/WABA/número(s) e concede acesso à Prumo; não reutilizar credencial de loja A em B e não decidir concessão humana a partir da posse técnica do canal. Identidade de conversa e número são escopados à loja. Validar assinatura e vínculo app/WABA/canal, ACK só após aceite durável conforme DEC-WA-03, idempotência e correlação antes de entregar evento ao S0.
2. **Entrada inbound e janela.** Adaptador entrega evento do cliente com identidade técnica, canal/loja, ID externo, instante confiável, conteúdo ou referência autorizada e estado de deduplicação. **S0** atualiza estado de mensagens e computa janela de atendimento livre **24 horas desde última mensagem do cliente**; Meta não marca caso concluído, não apaga chat e não dispara mudança de status comercial por expiração. Se o usuário humano não marcou concluído, o caso continua pendente mesmo após vencer a janela.
3. **Template individual escolhido pelo operador.** Somente S0 valida identidade/concessão/caso, opção do operador e C04/opt-out/consentimento/finalidade, e gera intenção de envio contendo template Meta já aprovado com versão/categoria/canal. A frente Meta **não oferece botão** nem decide se operador pode agir. Transporta pedido autorizado, registra resultado real ou incerto e retorna evidência técnica. Fora da janela de 24h, **não** aceitar pedido de texto livre como substituto de template.
4. **Cadeia planejada por IA, executada por S0/Meta.** OpenAI escolhe PROPOSTA de templates preaprovados/horários/quantidade, sem acesso à API Meta. S0 aceita/persiste plano, cancelamentos e cada tentativa, revalida C04 e estado comercial imediatamente antes de pedir envio ao adaptador. Meta apenas transmite cada tentativa autorizada e devolve IDs, eventos reais e erros sanitizados. O handoff humano não transforma plano antigo cancelado em ativo; plano pós-humano é distinto.
5. **Template final e início de 24h pós-envio.** Último template de encerramento é tentativa própria. **Aceite HTTP, fila, reserva ou callback não confiável NÃO provam envio efetivo**. O adaptador expõe sinais técnicos autenticados/correlacionados e eventual prova oficial de sent com instante, para S0 decidir confiabilidade. **Só S0** inicia relógio C09 e pode marcar perdido após 24h sem inbound se ciclo pré-banco for elegível; não é responsabilidade Meta classificar desfecho, perda, venda ou recusa do Banco. Falha, status incerto, opt-out ou cancelamento não iniciam relógio fictício.
6. **Resposta do cliente.** Mensagem inbound cancela próximas tentativas incompatíveis **por S0/C08**; Meta não atribui operador nem reativa IA Vendedora. O roteamento S0 usa estado do caso e handoff permanente: se humano, continua com operador atual; caso nunca humanizado e ainda apto pode usar IA. Template outbound **não** cria por si janela de mensagens livres; aguardar inbound do cliente.
7. **Janela visual:** Meta não fecha/arquiva UI; fornece dados de evento, e S0 projeta elegibilidade. Se concluído e a janela expira, Frontend apenas deixa de exibir na lista ativa; se não concluído, permanece pendente e oferece template/cadeia pela interface S0.

## Interfaces candidatas [P/R], sem inventar endpoint

**Meta→S0 inbound_event**: event_ref, app_ref, waba_ref, channel_ref, concessionaria_ref confiável, external_message_id, direction=CUSTOMER_INBOUND, provider_timestamp, received_at, type, content_ref/payload autorizado, dedupe_ref, proof/authentication_ref.

**S0→Meta outbound_template_intent**: attempt_ref, case_ref opaco, channel_ref escopado, approved_template_id, template_version, approved_language/category/parameter_refs, plan_ref ou manual_once_ref, authorization_policy_version, idempotency_key. Meta não aceita actor_id/browser token como autorização suficiente; assinatura/prova entre serviços e privilégio mínimo [R].

**Meta→S0 transmission_status**: attempt_ref, external_message_id, provider_status (accepted/queued/sent/delivered/read/failed/uncertain, como **taxonomia candidata até verificar estados oficiais**), provider_event_at, receipt_at, authenticated_source_ref, correlation_confidence, event_version, duplicate/out_of_order flags. Não atribuir prova sent sem ligação verificável a emissor/loja/tentativa; WA-01C fingerprints não são dedupe autoritativa.

## Requisitos de integração e segurança

- App/WABA único por concessionária, mais segregação de segredos, rotacionamento e cobrança por proprietário; qualquer envio real exige configuração/permissões/avaliação de custo aprovadas.
- C04 governado pelo S0: prova opt-in/base legal ou outra elegibilidade legítima, opt-out, template/categoria aprovados, limites de horário/frequência, conta correta e política de produto financeiro. Meta verifica capacidades do canal sem decidir legalidade de contato.
- Callback duplicado ou fora de ordem não permite duplo envio, nova janela livre fictícia nem contagem de silêncio; em corrida inbound x execução, S0 revalida e cancela antes de mensagem obsoleta.
- Meta não retorna histórico integral de outra loja, dados bancários, segredo ou prova D4 ao browser/OpenAI. Áudio/transcrição segue autorizações separadas.

## Cenários de teste candidatos (ZERO executados neste contrato)

WA7-01 inbound muda janela Meta desde última mensagem do cliente; WA7-02 template outbound sem resposta não muda janela livre; WA7-03 mensagem livre fora da janela é recusada; WA7-04 operador pede único template S0 elegível; WA7-05 plano IA gerado mas S0 não autorizado não transmite; WA7-06 final queued/accepted/uncertain não inicia C09; WA7-07 prova sent real +24h alimenta **apenas sinal** para S0; WA7-08 inbound durante plano cancela tentativas posteriores; WA7-09 owner canal A não usa token/canal B; WA7-10 callback duplicado/fingerprint inválido não duplica; WA7-11 opt-out bloqueia envio; WA7-12 plano sob humano recebe resposta roteada ao humano via S0.

**Gate:** revisão/aceite dos donos S0/Meta/Frontend/OpenAI sobre assinaturas, eventos oficiais, prova de sent e requisitos externos [R/V]. Não chamar API Meta real, não alterar números ou Supabase hospedado, nem contabilizar testes como executados.
