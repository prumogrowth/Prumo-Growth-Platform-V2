# CF-OP-02/F02 — Frequência de templates Meta, rejeição 131049 e proteção C09 v0.1

**Data:** 22/10/2026. **Situação:** pesquisa de fornecedor [V] e proposta técnica [P/R]. Não é decisão ratificada por S0/Meta, não autoriza envio ou mudança de status. Motivação: hipótese levantada pelo responsável de “2 templates por dia sem resposta”.

## 1. O que verificamos, e o que NÃO verificamos

- **Meta limita templates de MARKETING por destinatário**, conforme engajamento/receptividade; o bloqueio pode surgir como código **131049**, indicando não entrega para preservar o ecossistema. **Não foi possível confirmar uma quantidade universal e fixa de dois templates por 24h**, válida para todos os destinatários. Alguns provedores descrevem a combinação de uma conversa de marketing iniciada mais uma mensagem adicional na janela, mas isso **não equivale a uma quota universal diária**.
- A categoria **MARKETING** é distinta de **UTILITY** e **AUTHENTICATION**. Não aplicar indiscriminadamente o limite adaptativo de marketing a todas as categorias; as outras continuam sujeitas a suas próprias políticas. **Não reclassificar** um template promocional como utilitário para contornar limites. Finalidade interna de recontato e categoria Meta são dimensões separadas.
- **Janela livre de atendimento de 24h** começa no último inbound do cliente, não num outbound. O limite adaptativo por destinatário é diferente do alcance/limites do WABA/portfólio, qualidade ou pacing de templates; seu saldo real não é visível ao planejador.
- **131049 não comprova desinteresse, desistência, negativa bancária ou duas falhas técnicas qualificadas.** Proposta conservadora: suspensão/revisão, sem retry imediato automático, sem considerar sent, sem iniciar C09 +24h e **sem transformar sozinho em perdido técnico**. A classificação definitiva e precedência da S0 continuam [R].
- A Prumo/S0 podem futuramente aprovar **cota local adicional por contato, loja, categoria e janela móvel**, com valor versionado configurável. O exemplo **2 mensagens por 24h** usado nos testes é **somente uma política local fictícia**, não uma constante da Meta nem promessa de entrega.

**Fontes externas consultadas (22/10):**
- Política Meta oficial (atualizada em 23/09/2026): https://whatsappbusiness.com/pt-br/policy/
- Clickatell sobre frequência por usuário e erro 131049: https://www.clickatell.com/help-center/whatsapp/message-templates/what-are-per-user-marketing-template-limits/
- Vonage, limite por usuário e 131049: https://api.support.vonage.com/hc/en-us/articles/17270698783516-WhatsApp-Per-User-Marketing-Template-Messaging-Limits
- Infobip, descrição de dois por interação (não global): https://www.infobip.com/whatsapp-business/promotional-messages
- Referência oficial Meta Cloud API: https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-message-templates/ — acesso automatizado retornou HTTP 429; confirmar interpretação com o dono Meta.

## 2. Contrato funcional proposto com F02

| Etapa | Comportamento defensivo |
|---|---|
| **Antes de pedir F02** | S0 filtra templates aprovados/ativos, finalidade interna, categoria Meta real, loja/WABA, opt-in/opt-out, permissões e política local versionada. |
| **F02 planeja** | Propõe somente templates/cadência elegíveis; não conhece a quota adaptativa Meta e **não garante envio**. |
| **Antes de cada disparo** | S0 revalida regras e contador interno, inclusive reservas pendentes, categoria, qualidade/limites, status da cadeia, concorrência e opt-out. |
| **API_ACCEPTED, queued, unknown** | Não são comprovante sent; nenhuma contagem C09. Pendências podem reservar capacidade interna de modo conservador. |
| **Sent final comprovado** | Somente então a S0 pode iniciar avaliação do relógio C09 +24h, condicionado a status e fase comercial ratificados. |
| **Erro 131049 verificado** | Quarentena para decisão S0/Meta, sem retry imediato automático, perda comercial ou C09. Não tratar a resposta como desistência da pessoa. |
| **Duas falhas definitivas** | Continuam na regra determinística do motor S0, **com classe de falha qualificada a ratificar**. A proposta desta frente não conta 131049 como perda técnica. |
| **Novo inbound / cliente humanizado** | Janela Meta própria; recontato pós-humano exige pedido separado S0. F01 nunca retoma caso humanizado. |

## 3. Implementação offline E04 já realizada

- Módulo: [template-frequency.mjs](./e04_offline_lab/template-frequency.mjs), incluindo avaliação local versionada de marketing por contato/loja e classificação conservadora 131049.
- Testes: [template-frequency.test.mjs](./e04_offline_lab/tests/template-frequency.test.mjs), **33 casos**; nenhum usa Meta API.
- Compatibilidade: [transport-evidence.mjs](./e04_offline_lab/transport-evidence.mjs) e [testes de recibo](./e04_offline_lab/tests/transport-evidence.test.mjs), com **5 casos novos**, total **33**. Falhas com 131049 ou código não homologado nunca geram automaticamente candidato de perda.
- **Node.js 22.16.0: 66/66 testes PASS, zero FAIL**, apenas estas duas suítes, arquivos testados comparados pelos SHAs de blob com GitHub. Os 50 testes anteriores F01/F02/F03 têm outra evidência (V8); os 70 SYN originais continuam documentação, sem homologação conjunta.

**O que NÃO se provou:** assinatura real de webhooks, elegibilidade de envio, quotas da Meta, categoria efetiva, contabilidade por múltiplos telefones, timers C09, operação real de F02/S0, nenhum deploy. LOCAL_ELIGIBLE_META_UNCONFIRMED significa apenas que a política local fictícia não bloqueou a tentativa, **não** autorização Meta.

## 4. Questões objetivas para donos S0/Meta/Prumo

- **FREQ-R01 Meta:** documentação oficial, âmbito/geografia/categoria, 131049 e exceções, prova de erro e comportamento em conversa de marketing aberta.
- **FREQ-R02 Prumo/S0:** haverá cota local adicional? Quais valores por loja/contato/categoria, janela rolante, quem administra, versão e reservas pendentes?
- **FREQ-R03 S0/Meta:** classificação normativa de 131049 versus definitive_failed; precedência com regra das 2 falhas, políticas de hold/retry, C09 +24h desde sent final.
- **FREQ-R04 S0/S1/OpenAI:** bloqueio de marketing afeta F02 como pausa, replanejamento ou revisão humana? Como impedir cadeia cancelada e volta de F01?
- **FREQ-R05 Meta/privacidade:** destinatário/número versus pessoa identificada, múltiplos números e agregação entre lojas sem vazamento ou fusão presumida.

**Estado:** E04 offline prossegue autorizada; E05, conta/chave/API pagas, dados reais, Meta real, deploy, merge e mudanças nas outras frentes não foram autorizados.
