# F02 A29 — Evento histórico separado da inspeção
27/10/2026. Incremento de desenvolvimento F02, não nova auditoria da S0.

O histórico consultado pela F03 inclui mensagens anteriores ao encerramento; `observed_at` no envelope experimental F02 representa somente uma inspeção alegada pós-fechamento. O novo `source_event_at` é distinto e opcionalmente `null` (desconhecido). Quando declarado, deve ser datetime com fuso e não posterior à inspeção. Isso evita atribuir à mensagem original o horário do exame posterior.

O contrato permanece candidato `prumo.f02.s0.claimed_proof_binding/0.1-lab`. Todos os dados podem ser falsificados pelo chamador. Não autentica F03, C08, origem, intenção de gestor nem Meta. Não alteramos S0 nem decidimos cutoff, HMAC, versões ou direito de envio. O SHA do handoff não incorpora o evento original: sua coincidência é apenas identidade de pedido não confiável.

Incluídos oito testes 35–42 na suíte da F02. A matriz A29 ficará LAB_VERIFIED apenas após GitHub Actions SUCCESS no novo HEAD. Sem merge, deploy ou API real.
