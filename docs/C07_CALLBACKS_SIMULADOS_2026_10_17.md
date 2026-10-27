# Prumo — C07 callbacks de status: núcleo somente simulado

**Data:** 17/10/2026. **Escopo:** simulação S0/S2, sem webhook real, sem autenticação Meta, sem transporte e sem evidência de envio efetivo.

## Fonte normativa e regras preservadas
- Documento **26** C06/C07/C08/C09: evento com canal, identificador externo, ID do evento, instante e proveniência; deduplicação; eventos tardios/fora de ordem; não correlacionáveis ficam pendentes. Aceite da API não prova envio.
- Documento **37** PB-06/PB-07/PB-08: falha e resultado incerto não iniciam relógio de 24 horas, não marcam perdido e não autorizam reenvio cego; duas falhas qualificadas dependem DEC-15 [R/V].
- Documento **38** S2-A4/A6/A7: programação/aceite não é envio, callback tardio não causa reenvio, aviso final não comprovado não gera perdido.
- Documento **09**: cada tentativa programada preserva histórico próprio, eventos de status não devem sobrescrever evidência anterior.
- Mesma pessoa pode ser cliente em A/B/C com histórico isolado, enquanto um emissor de atendimento Prumo pertence a uma loja exclusiva.

## Implementação da migration 019
- `envios_template_sinteticos` ganha `correlacao_externa_ficticia` e **indicadores técnicos separados** para aceite, envio, entrega, leitura, falha e incerteza **SIMULADOS**. Não usamos esses campos como prova externa.
- `prumo_private.vincular_referencia_c07_sintetica` liga um identificador fictício a uma tentativa previamente reservada, após conferir loja, canal, plano, lead e ordem de locks. Vincular não solicita nem envia mensagem.
- `prumo_private.registrar_callback_c07_sintetico` recebe canal, correlação fictícia, ID de evento, estado e instante. Valida canal ativo/simulado, deduplica por evento externo no canal, rejeita mesmo ID com payload divergente, preserva eventos tardios e flags independentes.
- `eventos_callback_sinteticos` guarda todos os eventos técnicos, indicação de fora de ordem, correlação opcional com envio e `PENDENTE_RECONCILIACAO` para correlações desconhecidas. **Nenhuma associação inventada**.
- Retorno de callback inclui `comprovacao_real=NENHUMA` e `transmissao_externa=DESABILITADA`. Nenhuma função altera status comercial, cancela decisão humana, reinicia reserva cancelada, programa retry ou cria envio.
- Gestão da loja só lê os próprios eventos via RLS; nenhuma escrita do navegador, operador ou funções expostas à Data API.

## Casos de teste executados
`supabase/tests/s0_c07_callbacks.sql`, dentro da suíte PostgreSQL 17:
- C07-01: referência associada a envio reservado de teste, sem transmissão.
- C07-02: duplicatas reconhecidas, payload divergente rejeitado, callback fora de ordem persistido, falha/incerteza registradas sem perda/venda/status inventados.
- C07-03: evento não correlacionado preservado como pendente; um canal B não se vincula à referência da loja A.
- C07-04: callback tardio após opt-out preservado, envio continua cancelado.
- C07-05: gestor vê apenas a loja própria; usuário autenticado não insere eventos.

**CI:** [PostgreSQL 17 #39076677999 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39076677999). Testes RLS são com papéis simulados; suíte Auth/REST completa não foi rodada após a migration 019 por controle consciente do orçamento de GitHub Actions.

## Pendências / bloqueios de produção
1. Entrada HTTP assinada/autenticada da Meta, identificadores, schemas e estados oficialmente verificados **[V]**.
2. Adaptador que cria correlação apenas após sinal real legítimo; prova externa e timestamp de envio efetivo não são os flags `_simulado`.
3. Reconciliação/autorização de eventos não correlacionados, divergências entre falha e envio, callbacks fora de ordem e idempotency retention/dead-letter, incluindo atribuição humana.
4. Classificação de falhas consecutivas, DEC-13–15 e decisão sobre retry; **nenhuma retransmissão cega**.
5. C09 final comprovado + 24 horas reais + ausência de resposta + elegibilidade vigente; não implementado.
6. RLS via GoTrue/REST real para a tabela 019 ainda requer execução opt-in antes de homologação; LGPD, backups/restore, Meta/Banco e outros gates permanecem.

**Gate: GO apenas para a próxima engenharia sintética/segura; NO-GO para qualquer Meta real, dados comerciais reais, merge ou deploy remoto.**

## Adendo — validação integrada posterior (17/10/2026)

Embora a seção original registre que Auth/REST ainda não havia sido executado naquele momento, o marco foi concluído depois: [GitHub Actions #39079580129 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39079580129), inclusive `AUTH-11` da tabela de callbacks e das novas tabelas de reconciliação. Testes locais efêmeros, sem implantação comercial Supabase ou envio Meta.
