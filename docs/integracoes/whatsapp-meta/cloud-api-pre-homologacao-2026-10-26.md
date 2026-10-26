# WhatsApp Cloud API — preparação independente para homologação

**26/10/2026 — Prumo Growth / Frente WhatsApp-Meta.** Código em branch independente `feat/meta-cloud-envelope-contract-20261026` com origem exclusiva `docs/whatsapp-meta-concessionária de demonstração-poc-20261017`. **Sem conexão Meta, S0, Supabase, n8n ou endpoint público.** A decisão S0/PR #7 autoriza análise e preparação independente, mas não concede identidade M2M, ACK, envio, merge ou deploy.

## 1. Fontes recuperadas do próprio projeto

- `docs/integracoes/whatsapp-meta/wa36-matriz-ratificacao-interfrentes-e-privilegios-minimos-2026-10-23.md`: **12 contratos WA36** ainda sem aceite externo; papel humano não autentica máquina.
- `docs/integracoes/whatsapp-meta/wa37-contrato-aceite-interfrentes-m2m-2026-10-23.md`: **WA37-P01..P12 / N01..N12** são critérios de homologação propostos, **não provas executadas** em produção.
- `docs/integracoes/whatsapp-meta/wa38-handoff-revisao-s0-s1-meta-infra-2026-10-23.md`: origem histórica e responsabilidades propostas.
- PR #7/S0, `docs/integracao/S0_META_DECISAO_INTEGRACAO_20261026.md`: reutilizar laboratório, corrigir guard e ACL apenas em composição, sem porta M2M operável; WA67 aceito apenas no laboratório, WA68/budget operacional pendente; `APPROVED` comercial não inferido.

**Atenção à proveniência:** os documentos WA36/37 mantêm URLs do repositório anterior, que são referências históricas e não destino de deploy. O repositório atual é `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`.

## 2. Verificação externa de documentação técnica Meta

**Documentação oficial Meta verificada em 26/10/2026:**

1. Meta, **WhatsApp Cloud API** (coleção Postman oficial): https://www.postman.com/meta/whatsapp-business-platform/collection/wlk6lh4/whatsapp-cloud-api — exige business portfolio, WABA, número de telefone, token de usuário/sistema, permissões `whatsapp_business_management` e `whatsapp_business_messaging`; para alguns recursos de business portfolio, `business_management`.
2. Meta, **Messages**: https://www.postman.com/meta/whatsapp-business-platform/folder/o48mro7/messages — `POST /{phone-number-id}/messages`, token com permissão `whatsapp_business_messaging`, resposta com ID de mensagem `wamid`; status posterior chega por webhook e **não decorre da resposta do Graph**.
3. Meta, **Webhooks**: https://www.postman.com/meta/whatsapp-business-platform/folder/lboq68h/webhooks — endpoint de notificações HTTPS, subscrição a WABA, eventos de mensagens/status; a coleção oficial contém `POST /{WABA-ID}/subscribed_apps`.
4. Meta, **Send Template Interactive**: https://www.postman.com/meta/whatsapp-business-platform/request/lwtlz1k/send-message-template-interactive — template previamente criado, `type=template`, componentes/botões do formato aprovado. Templates devem ser compatíveis com catálogo e escopo correntes; aprovação **não vem do payload recebido**.
5. Exemplo oficial histórico Meta SDK: https://whatsapp.github.io/WhatsApp-Nodejs-SDK/receivingMessages/ — GET de verificação por challenge/token, POST com assinatura `x-hub-signature-256` e resposta 200 após processamento. **SDK arquivado**: referência de semântica, **não base recomendada de dependência nova**.

**Regras a confirmar na homologação, não fixar agora:** revisão Graph API vigente, janela de atendimento de 24h e elegibilidade/opt-in por finalidade, categoria/preço de templates, throughput e rate limits por WABA/número/categoria, idempotência de envio, contrato de timeout/ACK e redelivery, escopo efetivo da permissão de app, regras de retenção/LGPD. Os limites quantitativos podem mudar; **nenhuma cota fixa é autorizada nesta proposta**. Erro de rede após POST Graph = resultado potencialmente **incerto**; não reemitir por impulso.

## 3. Inventário de código já existente — não reimplementar

| Componente | Reutilização | Não resolvido |
|---|---|---|
| `inbound.ts` | HMAC-SHA256 sobre bytes brutos, UTF-8 fatal, GET/POST separados, lotes de mensagens/status, limite de bytes/eventos | Não confirma durabilidade nem ACK, scope da rota confiável vem do host |
| `verify-get.ts`, `routed-webhook.ts`, `credential-routing.ts` | GET challenge e seleção de App Secret por registry confiável, sem pedir tokens ao evento | Infra/Meta: configuração, rotação, custódia, endpoint HTTPS público |
| `graph-outbound.ts` | Preparação inerte de texto + classificação `API_ACCEPTED/PROVIDER_REJECTED/UNCERTAIN_EXTERNAL`, sem retry automático | S0: elegibilidade/opt-in/consentimento/versão da intenção antes do envio; Infra: token |
| `graph-template.ts`, `template-catalog-control.ts` | Preparação inerte de templates de texto com catálogo confiado, aprovação/revisão e parâmetros | Meta/S0: catálogo real, mídia/botões, cadência e políticas comerciais |
| WA30–35 e WA39–68 | Evidências técnicas offline: commit incerto, retries indevidos, status, HMAC, locks/forense | Não são serviço real; PR #7 faz composição isolada, não integrar SQL aqui |
| WA36/37 | Matriz de titulares, 12 critérios P/N e pacote de revisão fail-closed | Ratificação formal pelos titulares |

## 4. Implementação independente nova — componente reaproveitável

`integrations/whatsapp-meta/cloud-webhook-handoff.ts` é um **adaptador puro** de handoff **após HMAC**:

- Reutiliza `inspectMetaWebhook` (não cria outro parser nem outra chave); copia uma vez os bytes antes do `await`.
- Confere **todos os eventos de um lote** com um escopo `waba_id/phone_number_id/revision` selecionado pelo backend de forma independente do corpo. Um único item fora de escopo nega o lote inteiro.
- Preserva posição e ordem dos itens de `messages[]` e `statuses[]` para conciliação; não remove callbacks repetidos silenciosamente.
- Rejeita status fora de `sent/delivered/read/failed`, sem presumir entrega/caso; mensagens inbound seguem apenas como observação técnica.
- Retorna SHA-256 dos **bytes exatos** e `candidate_key` técnico sintético, **não identificador único Meta** e **não `event_ref` S0 aprovado**; mudanças na ordem dos campos alteram body hash mas não mudam o candidate key.
- **Sempre** `ack_allowed=false`, `send_authorized=false`, `retry_external=false`, `s0_write_authorized=false`, `production_authorized=false`, `delivery_confirmed=false`, `case_transition_authorized=false`. O resultado `AUTHENTICATED_NOT_DURABLE` não é resposta HTTP pública.

`cloud-webhook-handoff.test.ts`: 12 verificações novas focadas; `.github/workflows/meta-cloud-envelope-contract.yml`: CI isolado Node22, sem rede, sem PG17 ou acesso a segredos. Também executa regressões existentes selecionadas de HMAC, routing, Graph e WA36/37, sem repetir WA39–68.

**Limitação deliberada:** a nova camada não assegura armazenamento atômico ou decisão final de ACK. O S0/Codex deverá definir a autenticação do ingressor, bind de tenant e revisão, writer transacional, confirmação de durabilidade, retenção de PII e pontos de falha, antes de operar uma entrada Meta real. NÃO passar o objeto de observação diretamente à S0 sem contrato/ACL.

## 5. Dependências a encaminhar aos titulares

| ID WA36/37 | Titular originalmente proposto | Decisão pendente |
|---|---|---|
| M2M-IDENTITY P01/N01, MACHINE-ROLE P05/N05, NONCE-ATOMICITY P06/N06, RLS P08/N08 | Codex/S0 + Infra/S1 | Credencial de máquina distinta de GoTrue humano; audiência/finalidade/grants por loja, nonce + append atômicos |
| META-PROVENANCE P02/N02, KEY-SEPARATION P03/N03 | Meta + Infra + S0 | Rota/App credenciada, guarda e rotação de App Secret/token/chave interna |
| SCOPE-BINDING P04/N04, LOCK-ORDER P07/N07, REVOCATION P12/N12 | Codex/S0 + S1/Meta | Binding durável com revisão; cancelamento/opt-out/transferência e ordem global de travas |
| CALLBACK-DEDUPE P09/N09 | Meta + Codex/S0 | Escopo de ID de callback, política para corpo variante, lote, eventos tardios, retenção |
| ACK-RETRY P10/N10 | Meta + Codex/S0 + Infra | ACK HTTP somente após ponto de durabilidade contratado; redelivery não equivale a reenviar POST Graph |
| RETENTION-LGPD P11/N11 | Codex/S0 + Jurídico/LGPD | Minimização, logs, acesso e expurgo; PII do novo candidato fica só em memória no laboratório |

## 6. Condições de saída

Código e CI offline aprovados **não** constituem liberação de produção. Somente após aceites formais pode-se implementar um adaptador de serviço real com API Graph versionada, HTTP 200 de webhook, timeout/reatentativa, autenticação M2M e integração ao S0. Mantenha a PR nova como **Draft**, sem merge, deploy, migrações, segredo real ou conexão Meta/Supabase. Não modificar a branch S0 nem a PR #7.
