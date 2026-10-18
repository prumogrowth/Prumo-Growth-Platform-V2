# Modelo técnico de ingresso, identidade telefônica e idempotência — WhatsApp/Meta ↔ Supabase | v0.1

**Projeto:** Plataforma de atendimento comercial para LiberaCred  
**Frente:** WhatsApp/Meta, integrando-se ao backend principal  
**Classificação:** **ESPECIFICAÇÃO TÉCNICA CANDIDATA [P] — não executada, sem migrations e sem modificação do webhook de teste**  
**Data:** 17/10/2026 — proposta elaborada após a POC bidirecional da concessionária de demonstração.  
**Decisões ratificadas nesta frente [D]:** Supabase diretamente como adaptador WhatsApp inicial, sem n8n no caminho crítico; suporte a telefones brasileiros com **8 ou 9 dígitos locais após DDD**; Free por enquanto, com pedido prévio de aprovação de eventual upgrade.  
**Escopo:** recebimento autenticado, escopo da loja, inbox/identidade, dedupe, handoff para contratos do backend, status e outbox para envio. **Não** introduz IA, status comercial, normas bancárias nem titularidade civil.

> **Nota de precedência:** as fontes canônicas existentes prevalecem sobre nomes candidatos deste texto: documento 25 (E01–E32), doc 26 (C02/C06/C07 e outcomes), doc 28 (segurança/confiabilidade), doc 30 (projeto físico M000–M014), docs 11/13/13A/40/41 (negócio/acesso) e o [contrato v0.1](contrato-webhook-meta-supabase-v0_1.md). `[D]` regra aprovada; `[I]` consequência necessária; `[P]` proposta; `[R]` decisão interna pendente; `[V]` validação Meta/LGPD/infra/negócio. Todos os novos campos, índices e transações citados abaixo são [P].

> **Revisão de compatibilidade S0 (PR #1):** o documento físico do planejamento usa `canais_whatsapp`, porém a implementação S0 **já criada** utiliza `public.canais_loja` com `identificador_emissor UNIQUE` global e `modo='simulado'`. **Não criar outra tabela de domínio.** Evoluir a existente em migração aditiva da frente principal e preservar FKs. `receber_mensagem_sintetica` hoje compara telefone literal e rejeita replays do mesmo ID externo caso mude o formato; o resolvedor central e a chave de mensagem devem ser separados. `mensagens` atualmente restringe saída a `caso_id` e `enviada_por`; a autoria IA/sistema/template necessita evolução controlada. `eventos_callback_sinteticos` requer ID fictício de evento, que não é garantido pela Meta. Detalhes e matriz de responsáveis: [Conciliação PR #1 ↔ PR #2](conciliacao-pr1-pr2-s0-whatsapp-v0_1.md). Nenhuma implementação realizada.

## 1. Fronteira ambiental — não misturar POC com núcleo definitivo

**Infraestrutura efetivamente existente da POC:** Supabase `projeto-supabase-omitido`, função `whatsapp-webhook-sandbox`, WABA e Phone Number ID **de teste**, comando de resposta fixa `TESTE PRUMO`. Esta função **não** possui inbox transacional, filas nem dedupe implementados; resposta do sandbox não é homologação.

**Documento 30, item 1 e M000:** prevê projeto/instância **NOVA e EXCLUSIVA** para a futura plataforma, não reutilização automática do Supabase já conectado a outro esforço. Mesmo com o nome atual “Prumo Growth - Platform”, o piloto **não autoriza** executar o schema comercial ali. Antes de qualquer migration, confirmar proprietário, finalidade, ambiente, isolamento, plano, backups, credenciais e aprovação expressa da outra frente. A escolha do **provedor Supabase [D]** não é escolha automática do **mesmo project_id [R]**.

## 2. Correspondência com o domínio já proposto (sem reinvenção de entidades)

| Documento 25 / 30 | Nome físico candidato do doc 30 | Papel no adaptador | Condição |
| --- | --- | --- | --- |
| E01 CONCESSIONARIA | `concessionarias` | Tenant, fonte do escopo | [P] já previsto |
| E02 CANAL_WHATSAPP | `canais_whatsapp` | Roteamento por WABA/Phone Number ID com vigência | [P] já previsto |
| E03 LEAD_LOJA | `leads_loja` | Identidade comercial somente dentro da concessionária | [D/P] |
| E04 EVENTO_IDENTIDADE | `eventos_identidade` | Conflitos, verificação, vínculo de variantes | [P] já previsto |
| E10 CONVERSA | `conversas` | Vínculo lead/canal/caso e histórico | [P] já previsto |
| E11 MENSAGENS | `mensagens` | **Uma linha por mensagem**, nunca por webhook/status | Estrutura lógica [D] |
| E27/E28 | `envios_template` / `eventos_envio_template` | Solicitação/versionamento/template/status | Estruturas [D/P] |
| E29 EVENTO_INTEGRACAO | `eventos_integracao` | Inbox e correlação de evento externo | [P] já previsto |
| Auxiliares M006-T | Outbox/fila técnica, chaves de idempotência | Efeitos e retries duráveis | [P], não criadas |
| Complemento deste documento | `aliases_contato_canal` **ou** projeção derivada de `eventos_identidade` | Variantes exatas, proveniência e confirmação por loja | **[P/R]**, não duplicar conceito sem decisão da frente de dados |

**Mapeamento de nomes:** `loja_id` é a identidade lógica usada no contrato; `concessionaria_id` é o nome físico do doc 30. São **o mesmo escopo**, não duas colunas independentes sem necessidade. Preservar `lead_id`, `conversa_id`, `canal_id`, `mensagem_id` dentro desse escopo.

## 3. Roteamento seguro do webhook — ordem obrigatória [P]

1. **GET:** somente challenge válido, token de verificação seguro e resposta literal do desafio. Controlar logs que possam registrar a query string; token de verificação não é token da Graph API.
2. **POST:** ler bytes brutos com limite; verificar assinatura `X-Hub-Signature-256` por HMAC-SHA256 e comparação sem temporização dependente da entrada; rejeitar assinatura inválida sem tratar payload.
3. Conferir `object`, lotes `entry[]` e `changes[]`, `field=messages`, estrutura e limites. Um POST pode conter várias mensagens e status, inclusive conjuntos mistos. **Não criar um único registro para o POST inteiro se houver múltiplos eventos lógicos.**
4. Resolver `meta_app_ref + waba_id + phone_number_id` para **um único canal válido e sua concessionaria_id**, considerando histórico de vigência. Não escolher tenant pelo texto, número do cliente ou claim não autenticado.
5. Se canal inexistente, desativado, ambíguo ou sem prova de posse/autorização: **nenhuma escrita de domínio comercial**; registrar somente diagnóstico/quarentena com acesso técnico restrito e retenção aprovada [R/V]. Em callback antigo, buscar mapeamento **histórico** antes de atribuir à loja atual.
6. Aceitar cada item com chave e envelope técnico próprios e persistir em **transação** com tarefa durável (inbox + outbox/enfileiramento atômico). Só então emitir HTTP 200 do webhook. Duplicata conhecida também retorna 200, sem segundo efeito. Se falhar antes do commit durável, usar erro de aceite/retry conforme política Meta homologada [V]; não responder 200 fictício.
7. Entregar itens persistidos a worker(s); Edge Function de entrada **não espera** chamadas da IA nem da Graph API.
8. Worker adquire **lease** exclusiva com vencimento recuperável, executa C02 ou C07 e marca outcome/efeito numa transação idempotente. Falha pode reprocessar sem multiplicar fatos comerciais.

**Princípio de segurança:** uma assinatura válida comprova origem da chamada no contexto da credencial Meta usada, **não** prova titularidade civil do telefone, consentimento comercial ou elegibilidade bancária.

## 4. Registro de ingresso (E29) e chaves de deduplicação [P/V]

### 4.1 Campos técnicos candidatos em `eventos_integracao`

`id uuid`, `concessionaria_id uuid`, `canal_id uuid`, `provedor`, `app_ref`, `waba_ref`, `meta_phone_number_id`, `tipo_logico`, `identificador_externo`, `event_dedupe_key`, `payload_ref_protegida`, `payload_digest`, `correlation_id`, `request_id`, `recebido_em`, `ocorrido_em`, `estado_processamento`, `tentativas`, `proxima_tentativa_em`, `lease_owner`, `lease_ate`, `processado_em`, `erro_codigo_minimo`, `mensagem_id?`, `envio_id?`. Não é lista de campos aprovados para migration.

- `concessionaria_id` + `canal_id` devem ser obtidos de vínculo servidor confiável; FK composta para impedir atravessamento de lojas.
- `payload_ref_protegida` aponta a conteúdo mínimo sob criptografia/autorização e prazo legal, **não** a dump público em logs ou prompt.
- `payload_digest` é checksum técnico (e.g. SHA-256 do corpo/elemento normalizado) para integridade e análise, **não é identificador de pessoa e sozinho não decide idempotência semântica**.
- Se ID da Meta não existir, não inventar `wamid`; registrar exceção técnica/quarentena e definir tratamento por tipo de evento.
- Não assumir garantias de unicidade globais de IDs da Meta sem homologar no provedor [V].

### 4.2 Duas camadas de idempotência

**Camada A: dedupe de evento de integração.** Exige um ID lógico estável, escopado e validado. Candidatos:

| Classe | Chave candidata | Tratamento |
| --- | --- | --- |
| Mensagem inbound | `meta + canal_id + inbound + message.id` | Se `message.id` existente e confiável [V], unicidade estável; rejeitar repetição sem repetir C02 |
| Callback status | `meta + canal_id + status + message.id + timestamp + discriminador` | `statuses[].id` refere-se à mensagem; **não supor ID único de evento de status**. Discriminador adicional sujeito à validação [V] |
| Evento sem ID suficiente | `ingestion_id + ordinal` (somente transporte) | **Não** garante dedupe semântico entre reentregas. Manter em quarentena ou aplicar regra conservadora por tipo, sem efeito externo repetido |

**Camada B: dedupe de efeito de negócio.** Independente de transporte e de quantas vezes o worker tentar:
- `mensagens`: unique parcial `(concessionaria_id, canal_id, meta_message_id)` **apenas** se o domínio e a semântica do ID forem confirmados [V]. `mensagem_id` interno continua UUID.
- `outbox`: unique `(concessionaria_id, intent_id/idempotency_key)` sob escopo e semântica aprovados; todo efeito de envio, cancelamento, transição ou handoff depende de uma intenção idempotente.
- `eventos_envio_template`/status: registrar evento técnico sem criar outra mensagem inbound e preservar fora de ordem; materialização do estado técnico sem “voltar” artificialmente a um estado anterior.
- Mesmo texto repetido em duas mensagens **com IDs distintos** = duas mensagens legítimas. Jamais deduplicar pelo telefone/texto/minuto.

**Concorrência:** index unique + transação `INSERT ... ON CONFLICT` com leitura do registro existente, worker claim por `FOR UPDATE SKIP LOCKED` ou mecanismo equivalente e idempotência do efeito no backend. Índice sozinho impede segunda linha mas **não** garante que chamada externa seja feita uma vez em cenário de timeout; saída incerta exige conciliação.

### 4.3 ACK, commits e retomada

- A persistência do inbox e da tarefa a processar precisa estar na **mesma transação** no Postgres. Se Supabase Queues/pgmq não puder participar dessa transação pelo caminho escolhido, usar **outbox transacional + relay** em vez de gravar inbox num request e publicar fila em outro sem garantia.
- O ACK HTTP 200 ao fornecedor declara **recepção técnica durável**, não C02 concluído, não resposta da IA e não entrega ao WhatsApp.
- Falhas recuperáveis ficam `RETRY_PENDING` com backoff/jitter/limite de tentativas; excedidas, `DEAD_LETTER`, diagnóstico sem PII e replay controlado.
- Claims de worker expiram e podem ser readquiridos, mas o efeito de C02/C07/C06 preserva chave de idempotência no banco.
- Não reprocessar contra a loja atual se o canal foi transferido; vincular ao snapshot e vigência autenticados.
- Métricas: `ack_duration`, `inbox_backlog`, `oldest_unprocessed_age`, `worker_retries`, `dedupe_hits`, `identity_conflicts`, `graph_send_attempts`, `uncertain_sends` (sem payload/telefone).

## 5. Identificação BR com oito OU nove dígitos locais [D/P]

### 5.1 Formatos aceitos e limites

- Número brasileiro com DDI `55`, DDD de **dois dígitos** e número de assinante de **oito ou nove dígitos**; pode ser fornecido ao humano com `+`, espaços, `()`, traço. Interpretar ausência de DDI **somente** quando a origem/país for explicitamente conhecido; do contrário, classificar `NEEDS_REVIEW`.
- `numero_original` protegido e `digits_exatos` mantêm informação de proveniência; `country_code`, `ddd`, `local_digits`, `local_length` e `source_type` vêm de validação. Preferir lib de parsing de números com metadados atualizados; validação de formato não comprova WhatsApp ativo.
- **Oito dígitos locais não significam automaticamente um celular antigo**: pode ser número fixo ou outro contexto. Compatibilidade não autoriza tentar contato sem elegibilidade. **Não inventar o 9** nem eliminar o 9 de qualquer 9 dígitos.
- Não registrar `digits_exatos`/original em observabilidade não autorizada. Criptografia/consulta indexada segura definida em revisão de dados/privacidade [R/V].

### 5.2 Modelo de aliases de contato — extensão mínima candidata

**Estratégia compatível com E03/E04:** `leads_loja` continua identidade comercial por concessionária; `eventos_identidade` guarda prova/decisão; **uma projeção/tabela técnica pequena** de aliases (nome candidato `aliases_contato_canal`) guarda:

`id`, `concessionaria_id`, `canal_id? (quando identificação depender do provedor)`, `lead_id? (somente se confirmado)`, `provider`, `source_type`, `digits_exatos_protegidos`, `lookup_fingerprint_escopado`, `wa_id_protegido?`, `length_8_or_9`, `verification_state`, `verification_evidence_ref`, `valid_from`, `valid_to`, `created_at`, `reviewed_by?`.

Estados candidatos: `OBSERVED_EXACT`, `CANDIDATE_VARIANT`, `LINK_CONFIRMED`, `IDENTITY_CONFLICT`, `REVOKED`. Todos são **técnicos**, não status comerciais.

**Únicos propostos sob revisão [R]:**
- Uma associação `(concessionaria_id, provider, canal_scope, lookup_fingerprint, vigencia_ativa)` não pode apontar simultaneamente para dois `lead_id` confirmados; se houver colisão, marcar conflito em vez de anexar.
- `lookup_fingerprint_escopado` não deve ser SHA-256 simples do número, vulnerável à enumeração. Adotar HMAC com segredo rotacionável e escopo da loja para lookup, armazenando o número protegido à parte e mantendo estratégia de rotação/reindexação [P/R].
- Contato/número compartilhado pode exigir **múltiplos casos humanos** e proibição de fusão apesar de chave exata; a política comercial de unicidade ativa do doc 30 não prova uma única pessoa [R].
- Não adicionar UNIQUE global por telefone, CPF, alias ou `wa_id` atravessando lojas.

### 5.3 Resolvedor de identidade — função pura candidata

```text
resolveContact(concessionariaId, canalId, rawFrom, optionalProviderWaId):
  requireTrustedChannelScope()
  parsed = parseBrazilianNumber(rawFrom, trustedCountryContext)
  if invalid/ambiguous: return NEEDS_REVIEW
  exact = findVerifiedOrObservedExactAlias(concessionariaId, canalId, parsed.exact)
  if exact has collision/shared/recycled flags: return IDENTITY_CONFLICT
  if exact is current and unambiguous: return MATCH_EXACT(leadId)
  candidateKey = comparableBrazilMobile8or9Key(parsed) // somente BR + DDD, variante 9 elegível
  candidates = findAliasesByScopedCandidateKey(concessionariaId, canalId, candidateKey)
  if candidates have multiple distinct leads or conflict flags: return IDENTITY_CONFLICT
  if candidates resolve to exactly one lead and trustedOriginEvidence(rawFrom, optionalProviderWaId)
      and candidate is an eligible 8<->9 representation:
      linkObservedVariantWithAuditTrail(parsed.exact, leadId)
      return MATCH_CANONICAL_VARIANT(leadId)
  if no match: return CREATE_SCOPED_PROVISIONAL_OR_CONFIRMED_BY_POLICY(parsed.exact)
  return NEEDS_REVIEW
```

**Regra aprovada [D]:** variantes brasileiras elegíveis `55 + DDD + 9 + oito dígitos` e `55 + DDD + oito dígitos` devem localizar **automaticamente o mesmo contato lógico na mesma loja** quando houver correspondência única, origem de canal confiável e ausência de conflito. `from` e `wa_id` autenticados podem contribuir para evidência técnica, **não comprovam titularidade civil**. Em colisão, número fixo, compartilhado/reciclado ou formato importado não confiável, bloquear fusão e pedir revisão; não alterar ciclo bancário por transformação de telefone.

**Exemplos inteiramente fictícios** (representação ilustrativa, não números contatáveis):
- `+55 (81) 9XXXX-XXXX` e `+55 (81) XXXX-XXXX`: suportados como formatos candidatos distintos.
- Quando ambos os formatos forem variantes válidas com **correspondência única e origem confiável na mesma loja**, apontam automaticamente ao mesmo `lead_id`, preservando aliases e histórico. Em caso de colisão ou falta de evidência técnica, manter em revisão.
- O mesmo número exato na loja A e B = dois `lead_id`, histórico e casos separados.


### 5.4 Chave de comparação e política de normalização — decisão complementar [D/P]

**Exemplo sintético dado pelo responsável:** `5581900000000` ↔ `558100000000`, entendidos como mesmo número de contato para o caso de variante móvel brasileira. O `9` é o primeiro dígito local, **logo após DDI 55 e DDD 81**. Não são números a enviar no piloto.

- **[D]** A plataforma **não pode duplicar o contato** quando duas variantes válidas correspondem inequivocamente ao mesmo identificador WhatsApp no contexto de uma loja. Pesquisa, inbound, reimportação e resposta devem chegar ao mesmo `lead_id`/histórico.
- **[P]** Manter `numero_original` (protegido), `alias_exato`, `chave_comparacao_mobile_8_9` (HMAC escopado), `identificador_meta_verificado`, `formato_meta_operacional` e `origem/evidencia/vigencia`. A chave de comparação é `DDI + DDD + oito dígitos finais` **apenas quando** a forma de nove dígitos tiver `9` nessa posição e for compatível com celular. Uma forma de oito dígitos também deve passar critérios de canal/origem para participar da correspondência.
- **[D/P]** Sem colisões e com origem técnica confiável (por exemplo webhook HMAC válido no canal conhecido + histórico Meta associado), ligação automática de aliases ao mesmo `lead_id`; não exigir confirmação humana em todos esses casos comuns. Se não há contato, criar um registro local, com chave candidata, permitindo resolução posterior sem duplicação.
- **[D]** Preferir no envio o formato efetivamente verificado/aceito pela Meta para aquele contato/canal; **não converter destrutivamente** o cadastro humano e não enviar simultaneamente a 8/9 como tentativa.
- **[R/V]** A fórmula numérica **não** pode confirmar sozinha titularidade civil: se duas pessoas/leads possuem a mesma chave, há fixo, número reciclado, canal equivocado ou proveniência não confiável, produzir `IDENTITY_CONFLICT` / `NEEDS_REVIEW`, mantendo a operação segura. Priorizar o identificador técnico confirmado do provedor, não assumir que a Meta sempre adota o mesmo comprimento.
- **Idempotência:** normalização de alias não altera `external_message_id`. Mensagens diferentes conservam IDs próprios; webhooks repetidos mantêm único efeito mesmo que a variante de telefone recebida mude.

**Testes adicionais obrigatórios:** busca por ambas as variantes retorna mesmo lead quando seguras; primeiro 8→9 e 9→8; evento real autenticado duplicado sob formatos alternados; número fixo de oito dígitos não vira celular automaticamente; colisão entre dois leads não une históricos; mesmo telefone em lojas diferentes mantém isolamento; envio apenas para destino autorizado pela Meta.

### 5.5 Seleção de destino de saída

1. Pedido de envio deve trazer `concessionaria_id`, `canal_id`, `lead_id`, finalidade, `recipient_reference`, e decisão de elegibilidade de backend com versão.
2. Revalidar opt-out, janela/template, contexto de resposta, atribuição humana, estado de ciclo e credencial do canal imediatamente antes de enviar.
3. Usar **destino aprovado/observado pelo provedor com evidência e escopo**, preservando representação exata usada no envio com sucesso e evento de confirmação. Falta de vínculo confiável = `REJECTED_IDENTITY_UNCERTAIN`/roteamento humano.
4. Um `131030` (destinatário não autorizado **sandbox**) não justifica testar variante indiscriminadamente. Um `190` exige tratar token/permissões; nenhum erro pode provocar envio para outra loja/contato.
5. **Nunca disparar simultaneamente à versão de oito e à de nove dígitos para “descobrir qual funciona”.** Não pressupor que `from` do webhook seja o destino de saída autorizado em todos os formatos.

## 6. Máquinas de estados técnicos e side effects [P]

**Ingressão:** `RECEIVED_AUTHENTICATED → PERSISTED → READY → LEASED → APPLIED` ou `RETRY_PENDING / DEAD_LETTER / QUARANTINED`. **Não** equivale aos oito estados comerciais.

**C02**: após inbox, resolver lead e conversa dentro da loja; inserir uma `mensagens` por `meta_message_id` confiável; reimportação/conflito exige rota humana, não fusão. Em uma transação, gravar mensagem + efeito interno que dispara processamento; aplicar política de handoff/cancelamento. Duplicate = `ALREADY_APPLIED`.

**C07**: status Meta correlacionado ao `envio_id`/mensagem técnica correta dentro do canal. Registrar histórico técnico sem rebaixamento por fora de ordem. Status sem correlação = `QUARANTINED` e reconciliação; não gerar nova mensagem/comercial.

**C06/C12/C03**: intenção de saída gerada pelo backend e persistida antes da chamada Graph API, com `idempotency_key`, lease e validação de permissões da operação. Sucesso HTTP 200 representa **aceite API**, não entregue, lido, enviado ou venda. Registrar `provider_message_id`/timestamps de callback quando fornecidos. Timeout depois de possível envio = `UNCERTAIN_EXTERNAL`, sem reenvio automático até reconciliação.

**Handoff e banco:** o adaptador não reabre IA após um caso humano; retorno espontâneo após `cadastro enviado ao banco`/`vendido` cria ocorrência humana conforme docs 21/22/26, preservando ciclo/status. IA não remete cadastro à instituição financeira nem classifica venda/recusa.

## 7. Restrições/índices candidatos — não executar SQL [P/V]

- FK composta para todas as relações do domínio: `(concessionaria_id, canal_id)` → `canais_whatsapp(concessionaria_id,id)`, `(concessionaria_id, lead_id)` → `leads_loja(...)`, `(concessionaria_id, conversa_id)` → `conversas(...)`. Ao vincular `mensagens` a conversa e lead, verificar também igualdade entre lead da conversa e da mensagem.
- Inbox: unique de `(provider, canal_id, tipo_logico, identifier_semantics, external_id)` **somente após** validar domínio do provedor; eventos sem external_id entram em trilha especial sem falsa unicidade.
- Mensagens: unique parcial proposto pelo doc 30 para `(concessionaria_id, canal_id, meta_message_id)`, com `meta_message_id IS NOT NULL`. Não aplicar o mesmo índice sobre callbacks de status.
- Intenção outbound: unique por `(concessionaria_id, intent_id/idempotency_key)`, FK escopada, tentativa de envio imutável e chave de correlação de status. `LEAD` pode existir sem envio.
- Aliases: unique ativo escopado **somente para vínculo confirmado**, com política para transferência/reciclagem/contato compartilhado; não tornar `CANDIDATE_VARIANT` automaticamente único nem anexar a lead.
- Índice operacional em `eventos_integracao(estado_processamento, proxima_tentativa_em, recebido_em)` e por `(concessionaria_id, canal_id, recebido_em)` com RLS/GRANT. Quarentena de canal sem tenant exige repositório técnico com acesso segregado do domínio comercial.
- Modelagem de fila/outbox auxilia a M006-T do doc 30; número final de tabelas [R]. Evitar DDL por `service_role` na operação de webhook. Scripts somente após M000 e autorização de ambiente.

## 8. Matriz de testes obrigatórios antes de migrations / produção [P]

| ID | Teste sintético | Aceite obrigatório |
| --- | --- | --- |
| ING-01 | POST Meta HMAC válido; 2 mensagens no mesmo POST | Dois envelopes individuais, ACK após transação, sem perda |
| ING-02 | HMAC inválido/body alterado | 401/403, nenhuma escrita comercial |
| ING-03 | Canal WABA/Phone Number ID não mapeado ou ambíguo | Nenhum roteamento a loja, quarentena segura |
| ING-04 | Callback tardio após alteração de vínculo do canal | Usa vínculo histórico confirmado; se ambíguo, não atribui |
| IDEM-01 | Mesma mensagem/ID recebida 3x + workers concorrentes | Uma `mensagens` e um efeito; tentativas auditáveis |
| IDEM-02 | Duas mensagens diferentes com texto idêntico | Duas linhas legítimas |
| IDEM-03 | Status idêntico repetido e fora de ordem | Sem mensagem inbound adicional, sem rebaixamento fictício |
| IDEM-04 | Falha de commit antes de ACK | Sem 200 falso, recuperação conforme política Meta |
| IDEM-05 | Worker morre após reservar lease | Lease expira e retry não duplica efeito |
| IDEM-06 | Meta timeout após possível envio outbound | `UNCERTAIN_EXTERNAL`, sem segundo envio automático |
| IDBR-01 | `55+DDD+8` e `55+DDD+9` isolados | Ambos aceitos no cadastro técnico quando plausíveis |
| IDBR-02 | Duas variantes elegíveis recebidas por webhook autenticado, único lead da loja e nenhum conflito | Reconhece automaticamente o mesmo lead, adiciona alias e não envia para ambas |
| IDBR-03 | Primeiro entra `5581900000000`, depois `558100000000` na mesma loja em origem confiável; teste de ordem reversa | Ambos resolvem ao mesmo lead e histórico com trilha de vínculo, sem contato adicional |
| IDBR-04 | Mesmo número exato em lojas A e B | Leads e históricos independentes |
| IDBR-05 | Alias colide com outro lead/telefone reciclado | `IDENTITY_CONFLICT`, sem acesso misturado |
| IDBR-06 | Formato ambíguo sem DDI/contexto | `NEEDS_REVIEW`, sem envio |
| AUTH-01 | API/browser tenta consultar inbox de outra loja | Negar mesmo conhecendo ID/telefone |
| AUTH-02 | Gestor supervisiona conversa D2 da própria loja sem atribuição | Leitura permitida conforme doc 41; escrita não permitida sem atribuição |
| AUTH-03 | Operador não atribuído tenta responder | Negar e auditar; gestor autoatribuído pode responder somente após atribuição válida |
| FLOW-01 | Handoff humano/ciclo vendido recebe novo inbound | Humano, histórico intacto, IA não retomada |
| FLOW-02 | Callback `delivered`/read após envio | Apenas status técnico; não marcar vendido |
| FLOW-03 | 2 tenants concorrem com phone_number_id distinto | Nenhuma chave, segredo, dado ou fila cruza lojas |
| FLOW-04 | Falha/quarentena e replay após recuperação | Idempotência, rastreabilidade e correlação verificáveis |
| FREE-01 | Ambiente Free pausado, backup ausente ou limite alcançado | Sinalizar bloqueio de prontidão para uso real e submeter avaliação de plano; não mascarar SLA |

**Critério geral:** testes com dados **inteiramente sintéticos** em projeto dedicado e descartável, sem chamadas reais a clientes/Banco, sem modificar WABAs comerciais. Atualizar matriz 29 mediante coordenação, não alterar suas evidências históricas.

## 9. Plano de implementação em incrementos, com gate humano

**ETAPA A — design/revisão somente (esta entrega):** validar fronteira do doc 30, nomes, tabela/projeção de aliases, semântica de IDs Meta e contratos C02/C07/C06. **Não** executar migration.

**ETAPA B — migrations propostas em projeto exclusivo autorizado:** sequência `M000 → M002/M006` do doc 30, com `M006-T` para inbox/outbox/aliases se aprovado, FKs compostas/índices parciais, RLS/GRANT, rollback e teste de restauração. Revisão humana de migração antes de aplicar. Não utilizar project_id da POC por inferência.

**ETAPA C — ingestão isolada:** nova função/versão em sandbox separado; HMAC, persistência e ACK rápido; teste de eventos sintéticos múltiplos e reenvio. Não substituir `whatsapp-webhook-sandbox` sem plano de mudança.

**ETAPA D — resolvedor BR + C02/C07:** normalização e resolução automática de variantes brasileiras elegíveis 8↔9 no escopo da mesma loja, com alias auditável e fallback conservador para colisões, dedupe/outbox e testes de concorrência; sem IA e sem encaminhar mensagens reais a clientes.

**ETAPA E — saída autorizada C06/C12/C03:** outbox com provas de opt-out, janela/template, handoff e estados `UNCERTAIN_EXTERNAL` e reconciliação; homologação específica Meta/Banco/LGPD antes de produção.

**ETAPA F — teste operacional/benchmark:** p50/p95/p99 de ACK/commit/processamento, throughput, uso de recursos, backlog e custos; avaliar Supabase Free versus Pro previamente a qualquer exigência de backups/continuidade/limite. n8n permanece opção fora do caminho crítico.

**Condições para avisar sobre plano pago:** no início de trabalho que exija backup automático/recuperação operacional, SLA/indisponibilidade incompatível com Free, armazenamento/invocações limitantes ou recurso exclusivo pago, apresentar impacto, custo atualizado, alternativa Free e pedir aprovação. **Nenhuma contratação, migration ou atualização de schema foi efetuada neste trabalho.**

## 10. Decisões e provas pendentes (sem disfarçar como implementação)

- **[D]** Reconhecer automaticamente variantes elegíveis 8↔9 como mesmo número lógico no escopo da loja quando origem confiável e correspondência única; **[R]** parametrizar evidências e critérios técnicos de colisão, telefone fixo/compartilhado/reciclado e concorrência de leads.
- **[V]** Escopo e estabilidade dos IDs Meta, forma exata de status/callback e política de replay; revisar com payloads sintéticos ou sandbox autorizado.
- **[R]** Físico de aliases (projeção E04 versus tabela separada), índice/criptografia HMAC e gestão de segredo de lookup.
- **[R]** Forma de vincular conversas/casos humanos a inbound provisório antes da confirmação de identidade, preservando mensagens sem inventar titularidade.
- **[R]** Aceite/rejeição e retenção de eventos sem canal válido, APP multi-WABA, rotação de credenciais e HMAC, administração de testes e runbooks.
- **[R]** Ambiente Supabase **novo e exclusivo**, região, autorização de criação, controle de migrations e backups; preço/necessidade de upgrade apenas quando for exigido.
- **[V]** Políticas WhatsApp para serviços financeiros, templates/opt-in/out, tratamento de dados, consentimento e autorizaçãa instituição financeira.
- **[D]** A operação comercial mantém oito status; documento 41 prevalece para permissões de gestor/operador/MCP; responsabilidade por correção estrutural e autorizações é humana.

## 11. Critérios de revisão pela outra frente e histórico

**Obrigatório antes do merge/execução:** confirmar mapeamento `loja_id ↔ concessionaria_id` e objetos do doc 30; revisitar chave comercial E03 e semântica de alias/lead provisório; aprovar abordagem transacional inbox/outbox e escopo WABA; revisar IAM/RLS/GRANTs e conformidade; garantir não haver duas fontes de verdade para mensagens/ciclos/status.

**Referências internas:** docs `11_Arquitetura_Geral_Consolidada_v4_8.md`, `25_Modelo_Dados_Plataforma_v0_1.md`, `26_Contratos_Conceituais_Eventos_APIs_v0_1.md`, `28_Especificacao_Confiabilidade_Privacidade_Recuperacao_v0_1.md`, `30_Projeto_Fisico_Banco_e_Plano_Migracoes_v0_1.md`, `41_Decisao_Aprovada_Matriz_Permissoes_Gestor_Operador_MCP_v1_0.md`, [POC concessionária de demonstração](poc-meta-sandbox-documentacao-publica-2026-10-17.md), [contrato v0.1](contrato-webhook-meta-supabase-v0_1.md), [ADR Supabase/n8n](adr-001-transporte-webhook-supabase-vs-n8n.md).

**Controle de mudanças:** documento novo em branch de documentação. Sem alterações de código operacional, sem conexão do núcleo ao banco, sem criação de tabelas, sem solicitação de plano pago. Toda regra descrita como [P] só será implementação após revisão/aceite da frente proprietária do backend.
