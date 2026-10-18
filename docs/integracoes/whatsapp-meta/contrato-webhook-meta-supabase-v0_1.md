# Contrato de integração — WhatsApp Cloud API ↔ Supabase | v0.1

**Projeto:** plataforma de atendimento para LiberaCred — frente WhatsApp/Meta  
**Data:** 17/10/2026 (planejamento a partir da POC); **estado:** ESPECIFICAÇÃO PROPOSTA, não implementada nem homologada para produção.  
**Diretriz aprovada pelo responsável nesta frente:** usar **Supabase diretamente**, sem n8n no caminho crítico inicial, sujeito a reavaliação por necessidade real e métricas. **Plano atual relatado:** Supabase Free. Nenhuma contratação aprovada agora.  
**Alcance:** ingressar eventos autenticados da Meta, entregar fatos ao núcleo transacional, permitir comandos de saída autorizados e tratar identificadores telefônicos brasileiros com oito OU nove dígitos locais. **Não cria políticas legais nem estados comerciais.**

> **Precedência:** respeitar os docs canônicos 11, 13/13A, 25, 26, 28, 29, 30, 33, 34, 40, 41 e 43 do pacote auditado de 17/10/2026. `[D]` decisão de negócio aprovada, `[P]` especificação proposta, `[R]` decisão interna pendente e `[V]` validação de fornecedor/jurídica externa. Campos, filas, rotas e chaves deste documento são **[P]**, não migrações nem APIs já criadas. A POC permanece isolada do núcleo ainda em desenvolvimento.

## 1. Regras inegociáveis [D] e fronteiras [P]

1. **Uma identidade comercial por concessionária.** O telefone identifica comercialmente o lead apenas **dentro da loja**; o mesmo número pode ter atendimentos distintos em lojas A e B. CPF não é chave global. Telefone reciclado ou compartilhado exige revisão humana, não fusão automática (docs 11, 25, 26 e 33).
2. **Canal dedicado e escopado.** Identidade externa `waba_id` + `phone_number_id` deve resolver **um canal_id e uma loja_id** por cadastro de vínculos com vigência. Não aceitar `loja_id` fornecido por texto/IA/cliente como autoridade. Os números definitivos serão da gestora, dedicados à loja conforme decisão [D]; a POC em app/concessionária não decide propriedade/mandato [R/V].
3. **Fonte de verdade.** `MENSAGENS` = uma linha por mensagem individual; `ENVIOS_TEMPLATE` e eventos técnicos para templates; `CICLO_COMERCIAL` e eventos comerciais para oito status exclusivos; `CASO_HUMANO` para handoff. Metadados da Meta `sent/delivered/read/failed` **não** são status comerciais (docs 25/26).
4. **Sem automação bancária implícita.** A IA não envia cadastro ao banco nem registra venda/recusa definitiva. Regras bancárias e opt-in/opt-out exigem aprovações [V]. Entrada espontânea não equivale a opt-in para campanha.
5. **Handoff permanente no caso.** Mensagens recebidas após atendimento humano, cadastro enviado ao banco ou vendido seguem rota humana apropriada e preservam histórico (docs 21/22/26).
6. **Isolamento e menor privilégio.** Secret só no servidor, HMAC da Meta no webhook, permissões por loja, RLS **e** GRANTs **e** verificações backend; nenhuma credencial/PII em logs, código versionado ou respostas de erro. Direitos da decisão 41 prevalecem sobre propostas conflitantes de gestão anteriores.
7. **Não tocar produção na fase de contrato.** Nenhum número comercial será migrado, inscrito, substituído ou usado para disparo sem autorização explícita, plano de rollout e rollback.

## 2. Topologia de referência [P]

```text
Meta (GET challenge / POST messages)
    |
    v
Edge Function de entrada (pública; GET token verificação / POST HMAC SHA-256)
    |  filtra tipo, valida tamanho e app, correlaciona WABA/número a canal/loja
    v
RPC/Transação Postgres:
   registro técnico + chave idempotente + outbox/enfileiramento DURÁVEL
    |
    +--> HTTP 200 para Meta após aceite durável, sem aguardar IA ou Graph API
    |
    v
Worker consumidor de fila (Supabase Queues/pgmq ou outbox equivalente)
    |--> C02 mensagem inbound / C07 callback
    |--> núcleo transacional: estado/opt-out/handoff, IA e humano
    |--> outbox de envio para C06/C12/C03 conforme regras de negócio
    v
Worker de saída -> Meta Graph API
    |--> resultado técnico e external_message_id
    +--> novos callbacks Meta -> mesmo ingresso autenticado
```

**Observações:** `Supabase Queues` é uma opção concreta; verificar disponibilidade e configuração no projeto, transações e consumidores reais antes de escolher implementação. Se a chamada para fila e a persistência ocorrerem em requisições separadas, não afirmar atomicidade: usar uma RPC/transação ou outbox transacional + relé controlado. A entrega de fila não equivale a **efeito exatamente uma vez**: implementar dedupe e restrições na base. Recursos pesados de IA devem ficar fora do POST de entrada.

## 3. Contrato do endpoint público Meta [P/V]

### 3.1 GET — verificação da assinatura

**Rota existente na POC:** `/functions/v1/whatsapp-webhook-sandbox`. Em produção, URL e estrutura por app/tenant serão decididas, **sem reutilizar a POC automaticamente**.

- Aceitar somente `hub.mode=subscribe`, `hub.verify_token` correto e `hub.challenge` bem formado; devolver desafio como corpo com 200 ou recusar com 403.
- Token de verificação não é token de acesso à Graph API e não deve ser exibido em documentação. **Rotacionar** o token se aparecer em logs de URL e limitar retenção/acesso aos logs históricos; planejar revalidação sem afetar canais ativos.
- `verify_jwt=false` é intencional somente para a função pública da Meta; não dispensa validação do desafio GET nem assinatura HMAC no POST. Endpoints internos **não** ficam automaticamente públicos.

### 3.2 POST — mensagens, status e outros campos homologados

- Ler bytes brutos com limite de tamanho configurado; checar formato da assinatura `X-Hub-Signature-256: sha256=<hex>` e HMAC-SHA256 do **corpo bruto**, usando o segredo do app correto. Comparar em tempo constante. Rejeitar assinatura ausente/incorreta com 401/403 sem armazenar payload não autenticado.
- Não escolher secret arbitrariamente a partir de um `loja_id` enviado pelo cliente. Se houver múltiplos apps Meta, rotear por endpoint de app ou resolver conjunto limitado de chaves de maneira segura, com auditoria, **antes** do vínculo de loja.
- Depois da autenticação, validar `object`, `entry[]`, `changes[]`, `field=messages`, `value.metadata.phone_number_id`, referências `entry.id` (WABA) e limites da estrutura; suportar **múltiplas entradas e mudanças** no mesmo corpo sem descartar após a primeira.
- Resolver WABA + Phone Number ID em vínculo ativo e verificável `(app_ref, canal_id, loja_id, vigencia)`. Evento assinado de WABA desconhecida: registrar apenas diagnóstico mínimo em quarentena e não encaminhar a nenhum tenant; definir política de ACK/replay e retenção antes da implementação.
- Persistir a chave técnica e um envelope reduzido (ou referência a payload protegido sob retenção) com idempotência; reconhecer HTTP 200 **após commit durável** da aceitação. Para falha transitória de commit, devolver erro apropriado e permitir retry do provedor, sem fingir sucesso. Erro definitivo de estrutura deve ser tratado de modo que não cause loop infinito, com política de descarte/quarentena auditável.
- **Nunca** chamar LLM, verificar crédito, esperar envio da Meta, gerar template ou alterar estado bancário antes do ACK.
- Meta pode reenviar eventos e enviá-los fora de ordem. Não assumir `event.id` universal nem fechamento de janela por webhook (docs 13/26/28).

### 3.3 Campos Meta observáveis e verificação pendente

Campos usados na POC: `entry[].id` WABA, `changes[].field`, `value.metadata.phone_number_id`, `value.messages[]`, `value.statuses[]`. Os campos `messages[].id`, `messages[].from`, `contacts[].wa_id` e `statuses[].id/status/timestamp` entram como **campos candidatos para homologação por payloads de teste**; eventual ausência deve levar a quarentena ou fluxo de incerteza, não fabricação de identificador.

**Status HTTP**: 200 = evento autenticado **duravelmente aceito**, inclusive duplicata já persistida; 401/403 = assinatura inválida; 400/413 = payload impossível/limite inválido conforme tratamento definido; 5xx = falha transitória de aceitação, sujeita à política de retries. Tais códigos são desenho interno, não promessa de contrato oficial da Meta.

## 4. Envelope interno e contratos C02/C06/C07 [P]

**Proposta de envelope v1** em serviço privado/registro transacional; campos não são nome de endpoint publicado:

```json
{
  "contract_version": "1.0-proposed",
  "event_id": "evt_01_SYNTHETIC",
  "event_type": "whatsapp.message.inbound",
  "request_id": "req_SYNTHETIC",
  "correlation_id": "corr_SYNTHETIC",
  "causation_id": null,
  "provider": "meta_whatsapp",
  "provider_app_ref": "app_ref_sandbox",
  "waba_ref": "waba_sandbox",
  "phone_number_ref": "sender_sandbox",
  "loja_id": "loja_ficticia_A",
  "canal_id": "canal_ficticio_A",
  "external_message_id": "wamid.TESTONLY",
  "occurred_at": "2026-10-17T21:00:00-03:00",
  "recorded_at": "2026-10-18T00:00:01Z",
  "source_authenticated": true,
  "payload_ref": "protected_event_ref",
  "identity_resolution": "VERIFIED_PROVIDER",
  "schema_version": "1.0-proposed"
}
```

Todas as referências `SYNTHETIC`/fictícias são placeholders, não IDs reais.

| Contrato canônico do doc 26 | Evento/comando adaptado | Efeito permitido |
| --- | --- | --- |
| **C02 `receber_inbound`** | `whatsapp.message.inbound`; `channel_id`, `external_message_id`, `from_raw` protegido, `contact_ref`, `content_type`, `content_ref`, horário | Uma linha `MENSAGENS` + vínculo de conversa/lead da loja; respeitar handoff, cancelamentos e ciclos históricos |
| **C07 `callback_meta`** | `whatsapp.message.status`; `external_message_id`, `provider_status`, horário, referência de correlação | Evento de envio técnico, dedupe, tratamento de fora de ordem e falha; NUNCA tratar entregue/lido como vendido |
| **C06 `executar_envio`** | Comando interno da fila `whatsapp.send.requested` associado a `envio_id`, `canal_id`, template/versão, idempotency_key | Revalidar autorização/opt-out/handoff/janela, escrever tentativa, chamar Meta, registrar aceite/erro/ID externo |
| **C12 `mensagem_humana`** | Comando de operador autenticado, caso atribuído, texto permitido | Encaminhar à mesma outbox de envio respeitando direitos atuais |
| **C03 `resposta_ia`** | Proposta da IA, **não** publicação imediata | Backend valida contexto, versão e ausência de handoff; só depois publica envio pela outbox |

O núcleo conserva outcomes **APPLIED, ALREADY_APPLIED, ACCEPTED_FOR_PROCESSING, PENDING_EXTERNAL, UNCERTAIN_EXTERNAL, REJECTED**, com `reason_code` e correlação, conforme doc 26. A API Graph do fornecedor retorna seus próprios códigos; **não confundi-los** com outcomes internos.

**Idempotência candidata [P]:**
- Inbound: `provider + canal_id + external_message_id + inbound`, unique sob escopo da loja; replay retorna `ALREADY_APPLIED`.
- Status: `provider + canal_id + external_message_id + status + provider_event_ref` quando existir, ou fingerprint de status/timestamp/proveniência com política explícita de colisão; preservar repetição real em instantes distintos. Atualização de status técnico precisa ser monotônica **sem eliminar eventos fora de ordem**.
- Outbound: `envio_id + tentativa_autorizada + canal_id`, com reserva transacional e controle de versão. Timeout após transmissão possível = `UNCERTAIN_EXTERNAL` e reconciliação, **não reenvio cego**.
- Uma mensagem pode gerar vários eventos de status; status callback não é nova mensagem recebida.

## 5. Identidade telefônica BR: oito e nove dígitos [D + nova especificação P]

**Requisito confirmado pelo responsável:** aceitar **números brasileiros com oito OU nove dígitos de assinante após o DDD**. Não exigir nono dígito para conseguir receber, localizar histórico ou cadastrar um contato. É requisito de compatibilidade, **não autorização para mesclar pessoas ou testar envios em números diferentes**.

### 5.1 Entradas que o adaptador deve aceitar [P]

- DDI brasileiro `55`, DDD (dois dígitos) e número local **de oito ou nove dígitos**, quando formato plausível/validado para a categoria e origem. Aceitar representação humana opcional com `+`, espaços, parênteses e traços, mas **armazenar formato limpo separado do valor recebido**.
- Exemplos fictícios: `+55 (81) 9XXXX-XXXX` (nove dígitos locais), `+55 (81) XXXX-XXXX` (oito) e valores Meta apenas numéricos. Não confundir total de dígitos nacional/E.164 com total após DDD.
- Preservar `raw_input`/valor original **protegido** e identificar `source` (`importacao`, `meta_messages_from`, `meta_contacts_wa_id`, `operador`, `cadastro_previo`). Não reutilizar URL/telefone de contato em logs.
- Fazer limpeza/validação com biblioteca confiável e metadados atualizados para DDI/DDD/categoria; não considerar `regex` isolado prova de número ativo de WhatsApp.

### 5.2 Identificadores e aliases [P]

Manter separados:
1. `lead_id` e `loja_id` (identidade comercial por loja; docs 11 e 25).
2. `telefone_cliente_normalizado` (chave comercial lógica por loja, atualmente [D/I] nos documentos; representação física a decidir).
3. `identificadores_whatsapp`/aliases **propostos**, com `canal_id`, `source`, `raw_digits`, `country_code`, `ddd`, `subscriber_digits`, `provider_wa_id` opcional, `variant_8_or_9`, `verification_state`, `verification_evidence_ref`, `valid_from/to`.
4. `outbound_destination` autenticado/autorizado para aquela finalidade e canal. Não usar `phone_number_id` (número **da empresa**) como identificador do cliente.

**Algoritmo de resolução seguro [P]:**

a) Validar assinatura e canal/loja antes de qualquer consulta de identidade.  
b) Tentar identificador externo/alias **exatamente igual** e previamente associado à **mesma loja/canal**, com evidência e vigência.  
c) Quando `from` e `wa_id` divergirem ou aparecer uma variante com/sem `9`, gerar **candidato** de equivalência somente se DDI/DDD e padrão forem compatíveis. **Nunca** remover/adicionar o `9` indiscriminadamente nem compartilhar candidatos entre lojas.  
d) Vincular automaticamente os aliases **somente com prova suficiente e política aprovada** (por exemplo associação confirmada no mesmo evento autenticado do fornecedor e sem colisão, ou validação explícita por processo humano). O valor exato de prova [R/V]. `wa_id` e `from` são identificadores técnicos e não comprovam titularidade civil.  
e) Em colisão (números podem ser de pessoas distintas, aparelho compartilhado, reciclado), marcar `IDENTITY_CONFLICT`, conservar mensagens autenticadas em escopo correto e bloquear fusão/contato proativo até solução humana.  
f) Se não houver alias conhecido, criar identidade local provisória do contato recebido, com origem e referência; **não inventar telefone com nove dígitos** nem importar histórico de outra loja.  
g) Reprocessamento/reimportação só acrescenta evento de descoberta; não duplica lead confirmado nem sobrescreve cadastro declarado em conversa. A regra de unicidade final fica para migração aprovada do doc 30.

**Seleção do destinatário para saída [P]:**
- Priorizar destino que esteja **verificado e autorizado** para o canal/caso, após avaliação de opt-in/out e janela/template; considerar `wa_id` do fornecedor quando aplicável e a identidade de envio bem-sucedida confirmada.
- Se uma variante não funcionar, registrar código/meta correlation. **Não tentar enviar cegamente às duas variantes** e não solicitar confirmação de contato através de mensagens sem elegibilidade. Para `131030` (sandbox) conferir lista autorizada; para `190`, credencial/permissões.
- O teste 17/10 demonstrou que `from` recebido e destinatário autorizado podem exigir representação diferente; **não comprovou regra universal de equivalência** com/sem nono dígito.

### 5.3 Casos mínimos de teste [P, não executados]

| Caso | Resultado esperado |
| --- | --- |
| Contato de oito dígitos local válido em A | Registrável/resolvível em A, sem exigência automática de `9` |
| Contato de nove dígitos local válido em A | Registrável/resolvível em A |
| Mesma pessoa comprovada com aliases de oito/nove em A | Histórico único em A, aliases e fontes preservados |
| Variante semelhante sem prova suficiente | Sem fusão; conflito/provisório e validação humana |
| Mesmo número (qualquer formato) em lojas A e B | Dois históricos isolados; sem consultas cruzadas |
| Telefone reciclado ou compartilhado | Não atribuir titularidade automaticamente; fluxo de conflito |
| Callback `from` de oito dígitos, destino Meta verificado de nove | Responder só ao destino **autorizado**, sem segunda tentativa automática |
| Importação com `+`, espaços, `55`, ou sem DDI explícito | Normalizar apenas contexto conhecido; origem ambígua → revisão sem envio |
| Evento duplicado com aliases variantes | Uma mensagem/efeito no escopo após prova de associação; sem duplicação |
| Mudança de número/canal com vigência histórica | Callbacks antigos continuam na loja/canal antigos, sem fuga de tenant |

## 6. Segurança, LGPD e isolamento [P/V]

- Dados pessoais persistidos apenas com finalidade/retencão aprovadas; usar referências protegidas e redigir informações sensíveis em logs e métricas. Criptografia/segredos para tokens Meta por app/WABA conforme mandato futuro; evitar uma variável de ambiente por cada cliente quando atingir limite de secrets do projeto.
- Proibir acesso direto de `anon`/browser às tabelas de webhooks, outbox, aliases ou logs internos. Serviços internos autenticados e escopados; verificar `GRANTs`, RLS, autorização contextual no backend e testes multiloja (doc 41).
- Contratos de IA recebem dados permitidos somente da própria loja e caso, sem credenciais, documentos brutos, nome civil presumido ou consultas por CPF cruzando lojas.
- Mensagem do cliente após opt-out pode ser roteada conforme doc 33; **não** reabre permissão genérica de marketing. Opt-out entre diferentes números da gestora permanece [R/V].
- Segurança das URLs do callback, tokens de verificação e histórico dos logs deve ser revisada antes de qualquer homologação.
- Políticas Meta para conteúdo financeiro, contratação, templates, automação, consentimento, opt-out e relação com instituição financeira continuam [V] (doc 34).

## 7. Recuperação, observabilidade e tratamento de falhas [P]

**Estados operacionais:** `RECEIVED_AUTHENTICATED`, `PERSISTED`, `QUEUED`, `PROCESSING`, `APPLIED`, `REJECTED`, `RETRY_PENDING`, `DEAD_LETTER`, `UNCERTAIN_EXTERNAL`. São status TÉCNICOS candidatos, jamais novo status comercial.

- Exigir `request_id`, `correlation_id`, `canal_id`, `loja_id` e identificador opaco do evento no log. Sem corpo bruto, texto de conversa, telefone, token, hash reversível desnecessário ou informação financeira em logs.
- Indicadores a medir: volume ingressado, ACK p50/p95/p99, latência até commit, profundidade/idade da fila, tempo até resposta autorizada, retornos Meta por categoria de erro, tentativas, mensagens idempotentes, falhas permanentes, armazenamento, uso de Edge Functions e egress.
- Repetição do webhook = reprocessar somente se efeito ainda não ocorreu; status fora de ordem = registrar sem rebaixar interpretação técnica. Após falhas recorrentes, dead-letter com decisão humana e replay controlado.
- Se Graph API der timeout após possível aceite: `UNCERTAIN_EXTERNAL`, procurar status/correlação antes de qualquer retry; não afirmar entrega nem duplicar envio.
- Em indisponibilidade Supabase/Meta, seguir política operacional e contingência autorizada; não migrar automaticamente para WhatsApp comercial da concessionária.
- Mudanças de schema e código versionadas no GitHub com testes sintéticos, branches, PR, revisão, migrations e rollback/forward-fix (doc 43).

## 8. Plano Supabase Free e gatilhos de escalonamento [D relatada + P]

**Estado atual informado:** projeto Supabase no **Free**. **Decisão desta frente:** permanecer Free para ESPECIFICAÇÃO, testes sintéticos, desenvolvimento local e POC controlada, enquanto limites e requisitos permitirem. **Não contratar automaticamente nem afirmar que dados pessoais reais são apropriados ao Free.**

| Gatilho objetivo para informar o responsável ANTES de avançar | Ação proposta |
| --- | --- |
| Início de piloto com clientes/PII reais, com exigência de recuperação/continuidade | Avaliar backup/restore, políticas de retenção, controles LGPD e plano pago antes do uso |
| Serviço que não pode pausar após inatividade | Verificar migração para plano pago, pois Free pode pausar |
| Consumo aproximando limites de banco, storage, invocações/egress | Coletar métricas do Dashboard; propor upgrade/otimização antes de bloqueio |
| Teste ou requisito de concorrência/latência que excede capacidade real | Medir p95/p99, CPU, memória, filas e custo; propor otimização, upgrade ou worker externo |
| Necessidade de recurso só disponibilizado no pago (ex.: backups automáticos e PITR conforme plano) | Demonstrar requisito, opção, custo vigente e pedir aprovação do responsável |

**Referências públicas verificadas:** no Free a documentação Supabase mostra banco de 500 MB, storage de 1 GB e 500 mil invocações Edge Functions/mês, sujeitos a alterações; projeto Free pode pausar por baixa atividade. Edge Functions hospedadas têm até 2 s de CPU ativa por request e 256 MB de memória. **Revalidar métricas, quotas e preço no momento da decisão**, sem concluir que subir plano elimina limites arquiteturais.

- https://supabase.com/docs/guides/platform/billing-on-supabase
- https://supabase.com/docs/guides/platform/free-project-pausing
- https://supabase.com/docs/guides/functions/limits
- https://supabase.com/docs/guides/queues
- https://supabase.com/docs/guides/queues/consuming-messages-with-edge-functions
- https://supabase.com/pricing

**Comunicação:** sempre que alguma tarefa futura **nesta frente** exigir recurso pago, orçamento ou alteração de plano, interromper essa etapa e apresentar previamente motivo técnico, impacto, alternativa Free, plano recomendado e custo vigente para decisão explícita do responsável. Isso **não** configura monitoramento automático de uso fora das sessões de desenvolvimento.

## 9. Portões de aprovação e plano de testes de contrato [P/R/V]

**Pré-código:** revisar este documento junto às frentes de banco/IA e à matriz C02/C06/C07, decisões de canal/gestora, identidade com/sem nono dígito e significado da evidência de vinculação. Aprovar DDL lógico/segurança e responsabilidades pela reconciliação.

**Antes de enviar a números reais:** homologar app/WABAs/mandatos de uso; contrato de tratamento de dados e regras Meta/Banco; credenciais duráveis e segregadas; backups/restauração; logs sem PII; roteamento de tenant; kill switch por canal; testes de fim a fim em sandbox e pré-produção.

**Testes técnicos mínimos ainda não executados:** webhook GET correto/incorreto, POST assinatura boa/ruim, bursts e payloads múltiplos, destino oito/nove, alias confirmado/conflito, dois tenants com telefone coincidente, dedupe/replay, status fora de ordem, janela/template/opt-out, handoff, concorrência de envio humano/IA, timeout Meta com resposta incerta, renovação de credencial, falta de fila, cold start, backup/restore e replay de dead-letter.

**Critério de aceite para próxima implementação:** evidências versionadas em GitHub de testes automatizados com dados sintéticos, acesso por escopo, contrato compatível com C02/C06/C07 e retorno honesto de falha/incerteza. Sem simular aceite bancário ou comunicação com cliente real. Performance precisa ser medida, não presumida.

## 10. Inventário de perguntas e decisões a validar

| Tópico | Situação |
| --- | --- |
| Requisito suportar oito/nove dígitos locais BR | **Decisão do responsável nesta conversa [D]** |
| Supabase direto em lugar de n8n no fluxo crítico inicial | **Decisão de direção [D]; desenho físico [P]** |
| Equivalência automática de aliases sem nono dígito | **NÃO aprovada; exigência de evidência [R/V]** |
| Critério formal de confirmação dos aliases e resolver conflito | [R], precisa da frente de identidade/negócio |
| Posse definitiva WABA/app/número por loja, app e mandato | [R/V], conforme docs 11/34 |
| Política Meta financeira, templates, janela, opt-in/out, dados | [V], não resolvida na POC |
| Migração Supabase Free→Pro | **Ainda não necessária para este documento; revisão por gatilho** |
| Contrato de fila/RPC/DDL, regiões, SLA, thresholds | [P/R], dependem de implementação/benchmarks |
| Aderência a status comercial/casos humanos | [D] docs 11/13A/26, execução pendente |

## 11. Referências, rastreabilidade e histórico

**Fontes internas:** `11_Arquitetura_Geral_Consolidada_v4_8.md` (número da gestora e loja), `13_Matriz_Estados_Eventos_Responsabilidades_v0_6.md` e `13A_Emendas...` (estados e eventos), `25_Modelo_Dados_Plataforma_v0_1.md` (lead/canal/mensagens), `26_Contratos_Conceituais_Eventos_APIs_v0_1.md` (C02/C06/C07, envelope/outcomes), `28_Especificacao_Confiabilidade_Privacidade_Recuperacao_v0_1.md` (idempotência/falhas), `29_Matriz_Testes...` (cenários), `30_Projeto_Fisico_Banco...` (migrações/RLS), `33_Modelo_Ameacas_LGPD...` (identidade/consentimento), `34_Roteiro_Homologacoes...`, `40_Contratos_Interfaces...`, `41_Decisao_Aprovada...` (permissões), `43_Playbook_Inicio_Tecnico...` (GitHub/Free/n8n).

**POC fonte:** `poc-meta-sandbox-documentacao-publica-2026-10-17.md` e `adr-001-transporte-webhook-supabase-vs-n8n.md` nesta branch. Webhook atual POC somente recebeu e respondeu comando; **este contrato é planejamento para a integração principal**, não refatoração já implantada.

**Mudanças desta versão 0.1:** definida fronteira Meta/Supabase, funções conceituais C02/C06/C07 e riscos; suporte explícito 8/9 dígitos com aliases protegidos e sem fusão automática; critérios para sugerir Pro somente quando houver necessidade; referência explícita à decisão de usar Supabase diretamente.
