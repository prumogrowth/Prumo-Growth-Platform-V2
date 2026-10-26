# Cloud API — contrato offline de observação HTTP e encaminhamento ao S0

**Prumo Growth / WhatsApp-Meta — 26/10/2026.**
**Estado:** proposta isolada, sem envio real, credenciais, HTTP público, Supabase hospedado, S0/S1 alterada ou ACK concedido.

## 1. Por que existe

A frente já possui `graph-outbound.ts` (preparo inerte de mensagem e classificação de `API_ACCEPTED/PROVIDER_REJECTED/UNCERTAIN_EXTERNAL`), `graph-template.ts` (template por catálogo confiado), `offline-dispatch.ts` (intenção sintética + claim simulado + observação roteirizada), WA30 (commit externo incerto) e `cloud-webhook-handoff.ts` (entrada Meta de eventos múltiplos assinados). Não se deve duplicar essas implementações.

A lacuna concreta para a futura homologação é a **fronteira entre um transporte HTTP real e o classificador Graph já testado**: headers/corpo recebidos têm limites, parsing UTF-8/JSON, status 429 e `Retry-After`; nenhuma dessas entradas deve conceder automaticamente reenvio, ACK de webhook ou mutação comercial. Esta etapa implementa só a normalização **pura** de uma observação roteirizada, não o cliente HTTP.

## 2. Implementação independente

- `integrations/whatsapp-meta/cloud-wire-observation.ts`: função pura `classifyCloudWireObservation(attemptId,correlationId,observation)`. Entrada com shape restrito `not_attempted`, `transport_error`, ou `http_response` contendo status, cabeçalhos e bytes. Não importa `fetch`, `http`, tokens, host URL, DNS, client Supabase, S0, banco ou qualquer segredo.
- Reutiliza **sem alterar** `classifyGraphSendResult` de `graph-outbound.ts`: `wamid` retornado na resposta Graph só comprova aceitação da API, **não entrega nem leitura**; ausência de `wamid` válido no 2xx é **`UNCERTAIN_EXTERNAL`**.
- Respostas JSON são decodificadas como UTF-8 fatal **somente** até 65.536 bytes; Content-Type JSON validado; cabeçalhos são lidos por descriptors de objeto de dados, sem chamar getters. Não armazena nem devolve body, token, erros textuais do provedor, número, destinatário ou endereço de request. O identificador `wamid` tecnicamente aceito só deve circular entre serviços confiáveis.
- Para status `408/425/429/5xx`, timeout ou 2xx malformado, classifica o efeito externo como **incerto**, exigindo conciliação sob autoridade da S0. O header `Retry-After` de **429/503** é apenas dica informativa numérica até 86.400 segundos; data HTTP/valores inválidos não são escalonados e não há agendamento automático. Não configura quotas Meta nem reconhece custo tarifário.
- Respostas de rejeição explícita 4xx (exceto 408/425/429) seguem o classificador anterior, mas nunca concedem nova tentativa automaticamente. Redirecionamentos e estados não contratados continuam incertos.
- Todos os resultados têm `retry_automatically=false`, `ack_allowed=false`, `send_authorized=false`, `s0_write_authorized=false`, `production_authorized=false`, `delivery_confirmed=false`, `case_transition_authorized=false`.

**Importante:** uma observação isolada não prova que o chamador tinha autorização para enviar; nem que uma tentativa foi reservada e gravada de forma durável. Um objeto JavaScript com valores sintéticos não é principal M2M. A classificação `NOT_ATTEMPTED` não autoriza iniciar envio. Também não decide retorno HTTP do futuro webhook.

## 3. Testes de contrato

`cloud-wire-observation.test.ts`: **20 testes novos** no Node 22 sem rede, relativos a resposta aceita, `wamid`, 429 e dica `Retry-After`, timeout, 408/425/5xx, 400, 401/403, redirecionamento, Content-Type inválido, UTF-8/JSON malformado, resposta acima do orçamento, headers duplicados/injetados/getters e supressão de segredos na saída.

Workflow `.github/workflows/meta-cloud-envelope-contract.yml`: executa separadamente 12 provas de `cloud-webhook-handoff`, 20 provas novas desta etapa e as 129 regressões focadas anteriores (HMAC, roteamento, Graph, WA36/37). **Não repete WA39–WA68**.

## 4. Requisitos externos a solicitar ao Codex/S0

Os requisitos abaixo já estavam em WA36/37 e no parecer do PR #7. Agora se tornam **dependências concretas para o próximo estágio**, quando se pretender trocar a simulação por um cliente de transporte real.

| ID | Contrato necessário do S0/Codex | Critério objetivo |
|---|---|---|
| META-S0-DISPATCH-01 | **Porta de autorização e reserva de tentativa outbound.** S0, não o adaptador Meta, precisa revalidar tenant/canal/número/remetente/destinatário, finalidade, janela/opt-in, template e revisão da intenção; registrar claim durável e idempotente antes de permitir qualquer Graph POST | Uma tentativa não pode ser enviada duas vezes por concorrência/restart; escopo cruzado, versão obsoleta e opt-out rejeitados |
| META-S0-DISPATCH-02 | **Porta de observação e recuperação de resultado externo.** Associar ao claim a resposta `API_ACCEPTED`, `PROVIDER_REJECTED` ou `UNCERTAIN_EXTERNAL`, `wamid` válido se disponível, códigos sanitizados; resultado incerto permanece reservado e passa por conciliação humana/operacional autorizada, não reenvio cego | Queda depois do POST e antes do registro, 429/503, HTTP malformado e commit incerto não geram novo Graph POST automático |
| META-S0-ACK-03 | **Porta M2M autenticada de arquivamento durável de lote inbound/status**, com identidade do ingressor separada de GoTrue humano, revisão do registro técnico, nonce/idempotência e resultado explícito para todos os itens | Futuro ingressor só pode reconhecer o POST Meta conforme política ratificada **após confirmação durável do lote**; falha/resultado incerto não produz ACK prematuro |
| META-S0-LOCK-04 | Confirmar ordem global de locks e revogação entre S0, S1, outbox, chaves técnicas, tentativa e opt-out | Corridas com transferência/retirada de privilégio/cancelamento preservam isolamento e não reabrem envio |

**Não se está pedindo implementação agora no núcleo S0 sem alinhamento.** Solicita-se ao Codex decisão explícita sobre esses quatro contratos, seu responsável e testes positivos/negativos. Quando aprovados, a frente Meta poderá definir adaptador de rede com injeção de transporte autenticado e conciliação, sem inserir regras comerciais próprias no conector.

## 5. Outras dependências

- **Infra/Meta:** app/WABA/phone legítimos, token Graph com permissões apropriadas, vault de segredos, rotação, auditoria, webhook HTTPS, seleção de rota, taxa/limites efetivos e erros reais.
- **S0/S1/comercial:** janela de 24h, opt-in, template aprovado/catálogo atualizado, escalonamento humano, finalidade, cadência e opt-out por concessionária.
- **Jurídico/LGPD:** retenção/expurgo e acessos de conteúdo e identificadores pessoais; telemetria com campos sanitizados.
- **QA de homologação:** validar documentação oficial vigente, lotes, timeouts e permissões em sandbox autorizado, sem misturar `wamid`, candidato de evento forense e recibo de entrega.

## 6. Limite de responsabilidade

PR independente da branch `feat/meta-cloud-envelope-contract-20261026`, sem merge/deploy e sem mudanças em S0/S1/PR #7. Seu CI evidencia **comportamento de funções puras** e não certifica sistema operacional. Novas execuções devem focar lacunas reais, não repetir baterias históricas.

Fontes internas: `docs/integracoes/whatsapp-meta/wa36-matriz-ratificacao-interfrentes-e-privilegios-minimos-2026-10-23.md`, `wa37-contrato-aceite-interfrentes-m2m-2026-10-23.md`, `cloud-api-pre-homologacao-2026-10-26.md`; parecer PR #7 `docs/integracao/S0_META_DECISAO_INTEGRACAO_20261026.md`.
