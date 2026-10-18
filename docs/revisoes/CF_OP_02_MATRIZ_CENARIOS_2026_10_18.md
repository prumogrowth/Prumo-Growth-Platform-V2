# CF-OP-02 — Matriz de cenários e fronteiras | v0.1

**Natureza:** testes CANDIDATOS [P], **nenhum executado**. Referências: [Contrato de coordenação CF-OP-02](CF_OP_02_DIRETRIZ_CADEIAS_JANELA_HUMANA_2026_10_18.md), [issue #6](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6), docs 03/09/13A/21/26/40/41 e OAI-05/OAI-07. Usar somente fixtures sintéticas de concessionárias A/B com operador Prumo válido e autorizado.

| ID | Dono | Ensaio sintético | Aceite |
|---|---|---|---|
| CF2-01 | S0/FV | Operador não concluiu; passam 24h sem inbound | Atendimento permanece pendente, histórico legível, composer livre bloqueado, opção de template elegível |
| CF2-02 | S0/FV | Operador pede **um** template aprovado | Pedido auditado, loja/atribuição/opt-out revalidados; não cria cadeia por acidente |
| CF2-03 | S0/OAI/FV | Operador pede nova cadeia após fim de semana | Modelo só devolve template_id/versão/horário e quantidade 2–5 dentro de política; sem envio do próprio modelo |
| CF2-04 | S0/Meta | Template outbound enviado fora da janela, cliente ainda não responde | Não abrir janela livre nem liberar digitação humana |
| CF2-05 | S0/Meta/FV | Cliente responde ao template de retomada | Janela 24h reinicia; cancelar tentativas futuras incompatíveis; manter rota de humano atribuído |
| CF2-06 | S0/OAI | Lead jamais teve handoff; responde cadeia da IA | Retorna à IA Vendedora somente se caso ainda é IA e elegível |
| CF2-07 | S0/OAI | Lead teve handoff; responde cadeia planejada por IA | Retorna ao humano autorizado, IA Vendedora silenciada |
| CF2-08 | S0/FV/OAI | Operador conclui conversa com janela Meta aberta | Evento técnico único + snapshot extrator; conversa permanece na janela visual ativa até último inbound +24h |
| CF2-09 | S0/FV | Concluído, janela Meta expira | Sai apenas da lista ativa; ficha, histórico e auditoria persistem |
| CF2-10 | S0/FV | Caso NÃO concluído, janela Meta expira | Não arquivar nem marcar `perdido` pelo relógio Meta |
| CF2-11 | OAI/S0 | Conversa concluída inconclusiva, nenhum dado suficiente | Extrator registra faltas; Planejadora pode propor nova cadeia se elegível, sem inventar fato ou status |
| CF2-12 | OAI/S0 | Cliente diz "volto dia 5 do mês que vem" com mês inequívoco | Data contextual fundamentada em fonte/corte, horário e cronograma respeitam política; não antecipar encerramento |
| CF2-13 | OAI/S0 | Cliente diz "talvez mais pra frente" | Data incerta, não inferir dia; revisão/plano conservador |
| CF2-14 | S0 | Nova cadeia pós-humano quando antiga foi cancelada no handoff | Plano NOVO auditado, não reativa o antigo ou IA Vendedora |
| CF2-15 | S0 | Cliente responde durante cadeia | Cancelar próximos agendados/reservados sem apagar rastros; sem perda |
| CF2-16 | S0 | Duas falhas técnicas qualificadas, C08 | Suspender posteriores segundo regra, sem fingir template final enviado |
| CF2-17 | S0/Meta | Final só `queued/accepted`, callback `sent` não confiável | NÃO iniciar relógio pós-final de 24h; nenhum `perdido` |
| CF2-18 | S0/Meta | Final efetivamente enviado, 23h59 sem inbound | Não marcar `perdido` |
| CF2-19 | S0/Meta | Final efetivamente enviado, 24h passadas, zero inbound, ciclo pré-banco elegível | Marcar `perdido` uma só vez, motivo silêncio, sair da fila ativa, manter histórico |
| CF2-20 | S0/Meta | Final enviado; resposta chega simultânea à avaliação das 24h | Locks/idempotência impedem perda fictícia; precedência do inbound verificável |
| CF2-21 | S0 | Ciclo `cadastro enviado ao banco` silencioso 24h | NÃO converter para `perdido` por silêncio; recusa bancária exige prova humana |
| CF2-22 | S0 | Ciclo `vendido` silencioso | Não converter para `perdido`; novo contato cria rota humana separada |
| CF2-23 | S0/OAI | Operador escolhe template individual com plano IA em andamento | Política explícita impede envios duplicados/conflitantes |
| CF2-24 | S1-002 | Suspende operador Prumo com casos pendentes e cadeias | Sem novas atribuições; remanejamento atômico mesma loja; planos preservam caso mas próximo inbound vai novo autorizado |
| CF2-25 | S1-002 | Revoga B de operador com A+B | Redistribuir B, preservar A; nenhum dado cruzado |
| CF2-26 | S1-002 | Todos operadores da loja indisponíveis | Fila protegida para gestor, sem conceder acesso ou perder lead silenciosamente |
| CF2-27 | S0/OAI/FV | Cliente retorna após `perdido` do caso humano | Histórico preservado, novo ciclo/roteamento aprovado, sem reabrir status anterior nem devolver operador inativo |
| CF2-28 | S0/OAI | Modelo pede template fora catálogo, frequência > limite ou horário proibido | S0 rejeita proposta/itera com restrição; não envia |
| CF2-29 | S0/Meta | Opt-out antes do agendamento ou antes da execução | Nenhum envio, final não conta, sem perda por template fictício |
| CF2-30 | S0/FV | Duplo clique em concluir e resultado OpenAI atrasado após nova mensagem | Uma conclusão/snapshot por versão; resultado velho não sobrepõe revisão nem cria plano duplicado |
| CF2-31 | S0 | Mesma pessoa em loja A e B, telefone igual | Eventos, mensagens, planos, canais, operador e histórico isolados por loja |
| CF2-32 | OAI/Meta/S0 | Texto do cliente tenta instruir IA a ignorar limites e enviar template | Conteúdo como dado não confiável, sem alteração de regra/credencial/permissão |
| CF2-33 | S0/FV | Atendimento humano concluído, plano de recontato ativo, janela Meta expira | Arquivar visualmente somente conversa concluída; agenda pode continuar, caso/histórico preservados e alertas controlados |
| CF2-34 | S0/Meta | Template final enviado, mas mensagem inbound chega logo após `perdido` | Registrar novo contato/ciclo conforme norma, sem apagar perda histórica, roteamento autorizado pelo caso prévio |

**Gates:** (G0) conciliação normativa de elegibilidade e semântica C09 pós-humano [R]; (G1) revisão de assinaturas entre S0/OpenAI/Meta/FV [R]; (G2) fixtures/implementação no sandbox e execução de CF2-01–34 [P]; (G3) privacidade/custos/homologação Meta e Banco [V]; (G4) go-live [NÃO AUTORIZADO]. Nenhuma linha desta matriz é prova de execução.
