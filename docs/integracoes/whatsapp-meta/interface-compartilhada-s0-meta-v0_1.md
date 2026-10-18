# Interface compartilhada S0 ↔ Meta/Supabase | desenho v0.1

**Estado:** desenho de contrato [P] para revisão cruzada. **As diretrizes DEC-WA-01/02/03 estão APROVADAS [D]** pelo responsável; nomes de API, payloads internos, modelo físico, auth, fila e implementação permanecem **PROPOSTOS**, até confirmação pela frente principal.  
**Documento vinculante de contexto:** [Conciliação PR #1 ↔ PR #2](conciliacao-pr1-pr2-s0-whatsapp-v0_1.md), [contrato geral](contrato-webhook-meta-supabase-v0_1.md), [modelo ingresso/identidade/idempotência](modelo-tecnico-ingresso-identidade-idempotencia-v0_1.md).  
**Objetivo:** fronteira única, testável e com responsabilidades claras entre duas frentes; **não definir um segundo backend nem enviar mensagens reais**.

## 1. Donos das interfaces e cadeia principal

| Componente | Quem implementará após gates | Responsabilidade |
| --- | --- | --- |
| `concessionarias`, `canais_loja`, `leads_loja`, `conversas`, `mensagens`, casos/estados | Frente principal | Identidade comercial, FK composta por loja, RLS/GRANT, direitos, autorizações, máquinas de estados |
| Cadastro e vigência do vínculo `Meta app/WABA/phone_number_id → canal_id + concessionaria_id` | Principal (schema) + Meta (especificação/validação) | Identificar a loja **somente a partir do canal cadastrado e autenticado**; conservar exclusividade global do emissor |
| Webhook público Meta GET/POST | Frente WhatsApp | GET challenge, POST HMAC do corpo bruto, limites, parsing, classificação; nunca aceitar tenant do texto |
| Inbox técnico e fila/outbox transacionais | Frente principal | Persistir antes do ACK, claims/lease, dedupe, retries, DLQ, autorização do worker |
| Resolvedor BR + alias 8↔9 | Frente principal | Identidade única **por concessionária** sob critérios seguros; colisão → pendência; histórico/proveniência |
| C02/C07: aplicar entrada/callback no núcleo | Frente principal | Mensagens, vínculos, estados técnicos, efeitos idempotentes, respeitar handoff |
| Adaptador/worker de envio Meta | Frente WhatsApp | Consumir somente comando autorizado, Graph API, tokens por canal, IDs/status/erros, envio incerto |
| C03 IA / C06 templates / C12 humano | Frente principal | Regras comerciais e distintas pré-condições de autorização; convergem na outbox, não numa mesma função de negócio |
| Testes contratados e compatibilidade | Ambas | Geração de fixtures, CI sintético, gates de seguranca multiloja e homologação sandbox |

**Fronteira de execução:** a função `whatsapp-webhook-sandbox` hospedada no projeto `projeto-supabase-omitido` permanece **POC de teste, intacta**. `main` não possui a nova integração. Nada aqui é implantação.

## 2. Protocolo inbound proposto [P]

### 2.1 Entrada do adaptador

1. Confirmar origem com HMAC-SHA256 do corpo bruto Meta. GET challenge e POST devem obedecer a seus contratos próprios; Supabase `verify_jwt=false` apenas para a função pública de webhook, autenticada por assinatura da Meta no POST.
2. Desmembrar todas as entradas `entry[]`, `changes[]`, `messages[]` e `statuses[]`. Um único HTTP POST pode ter **vários itens lógicos**.
3. Resolver referência do aplicativo autenticado, WABA e `phone_number_id` em **canal vigente** na base principal; o mapeamento usa `public.canais_loja` S0, não uma nova tabela concorrente.
4. Entregar envelope mínimo de cada item ao serviço de persistência interno, autenticado com credencial de serviço específica e menor privilégio; segredo HMAC Meta **não** é o segredo do gateway comercial S0.
5. Confirmar `200` ao webhook **somente após** persistência transacional durável de todos os itens aceitos ou decisão técnica explícita de quarentena/descarte. Erro de commit não pode ser ocultado por `200`; não aguardar chamada Graph API, IA ou template.

### 2.2 Envelope técnico de transferência (sintético; não é API já publicada)

```json
{
  "contract_version": "meta-s0.v0.1-proposed",
  "source": "meta_whatsapp",
  "event_kind": "inbound_message",
  "ingestion_id": "fixture_ingress_0001",
  "provider_app_ref": "fixture_app",
  "waba_id": "fixture_waba",
  "phone_number_id": "fixture_sender",
  "canal_id": "uuid-canal-sintetico",
  "concessionaria_id": "uuid-loja-sintetica",
  "provider_message_id": "wamid.FIXTURE",
  "provider_timestamp": "2026-10-17T00:00:00Z",
  "payload_ref": "vault-or-private-storage-ref",
  "sender_identifier_ref": "protected-sender-ref",
  "correlation_id": "corr_fixture",
  "transport_signature_validated": true
}
```

Os placeholders não são valores de produção. `concessionaria_id` não pode ser inferido de um valor escolhido pelo remetente: vem do **vínculo de canal autenticado**. Campos de status usam `event_kind=status_callback` e `provider_message_id` do envio, sem exigir `callback_event_id` que a Meta não forneça. Versões incompatíveis devem ser rejeitadas de modo observável e seguro.

### 2.3 Resposta da persistência interna (proposta)

| Resultado | Significado e ACK ao webhook |
| --- | --- |
| `ACCEPTED_DURABLE` | Evento novo e sua tarefa persistidos na **mesma transação** → webhook 200 |
| `ALREADY_ACCEPTED` | Chave de ingressão já persistida com conteúdo compatível → webhook 200, nenhum efeito novo |
| `QUARANTINED_DURABLE` | Assinatura válida, mas campo/canal ambiguamente resolvido; item salvo em quarentena técnica restrita → política de ACK conforme causa e aceite durável |
| `RETRYABLE_STORAGE_FAILURE` | Não houve commit/aceite durável → webhook 5xx, nunca sucesso fictício |
| `UNTRUSTED_OR_MALFORMED` | Assinatura inválida/formato inválido → 401/403/4xx; política exata de replay e tratamento a homologar |

**Semântica obrigatória:** um HTTP POST agregado só pode retornar `200` se **todos os itens relevantes** tiverem recebido destino durável/decisão final segura. Nada de ACK parcial que perca itens silenciosamente.

## 3. Contrato de identidade 8↔9 — DEC-WA-01 [D/P]

### 3.1 Resolução central no núcleo

Entrada conceitual (não endpoint já criado):

```json
{
  "concessionaria_id": "uuid-loja-sintetica",
  "canal_id": "uuid-canal-sintetico",
  "raw_identifier_ref": "protected-id-ref",
  "source": "meta_authenticated_inbound",
  "provider_wa_id_ref": "optional-protected-ref",
  "provider_message_id": "wamid.FIXTURE"
}
```

Retorno conceitual:

- `MATCH_EXACT` + `lead_id`: identificador já associado sem conflito.
- `MATCH_CANONICAL_VARIANT` + `lead_id`: representação BR móvel elegível 8↔9 de mesma chave canônica, associação única e evidência técnica confiável; registrar novo alias/origem, **sem gerar segundo lead**.
- `NEW_SCOPED_CONTACT` + `lead_id`: nenhum candidato prévio, identidade comercial provisória/adequada conforme política da frente principal.
- `IDENTITY_CONFLICT` / `NEEDS_REVIEW`: vários candidatos, número fixo ambíguo, compartilhado/reciclado ou origem pouco confiável; preservar evento e impedir fusão/envio não autorizado.

**Exemplo ilustrativo aprovado pelo responsável:** `5581900000000` e `558100000000` são, sob critérios de elegibilidade definidos, representações do **mesmo número lógico** na mesma concessionária. Fazer lookup por ambas; armazenar forma original e formato Meta observado. A chave de comparação considera a inserção de `9` imediatamente após DDI/DDD em celular BR, **não remove qualquer dígito `9` em posição arbitrária**. Essa comparação não prova titularidade civil.

**Invariantes:**

- Identidade de lead é escopada por `concessionaria_id`; duas lojas podem ter históricos distintos com o mesmo número. `canais_loja.identificador_emissor` continua exclusivo globalmente, por ser **número da empresa**, diferente do número do cliente.
- O resolvedor é transacional: duas mensagens/threads concorrentes representando 8↔9 devem apontar ao **mesmo lead** nos casos comprovados; em conflito, não anexar a lead errado.
- Histórico de `eventos_identidade` e eventual projeção de aliases são aprovados como direção; **DDL e semântica de evidência/rotatividade** continuam para revisão da frente principal.
- Identificador original pode ser usado para auditoria autorizada, mas **não** é chave de envio automática; saída usa destino verificado/autorizado Meta no canal.
- Se o replay traz o **mesmo** `provider_message_id` com variante diferente mas equivalente e demais campos consistentes, responder `ALREADY_APPLIED` ao C02, nunca `CONFLICT_IDEMPOTENCY_KEY` só pela formatação. Conflito real de conteúdo/escopo não deve ser suprimido.

## 4. Contrato de entrega C02/C07 ao núcleo [P]

**C02 inbound:** depois de aceitar duravelmente, worker chama interface privada aprovada pelo backend com `concessionaria_id`, `canal_id`, `provider_message_id`, referência protegida de origem, texto/mídia protegidos e correlação. O backend resolve identidade e registra **uma `mensagens` por mensagem externa**, mantendo `conversas`, ciclos e handoff. O C02 sintético S0 existente **não é interface para payload Meta**; terá evolução controlada sem enfraquecer suas verificações.

**C07 callbacks:** os status Meta são associados ao envio por `provider_message_id` e escopo do canal, registrando estado, timestamp e observação; `statuses[].id` não é assumido ID único do evento. Callback repetido não altera ciclo, callback fora de ordem não rebaixa progressão técnica artificialmente. Callback não correlacionado entra em pendência de conciliação.

**Outcomes internos candidatos:** `APPLIED`, `ALREADY_APPLIED`, `ACCEPTED_FOR_PROCESSING`, `PENDING_EXTERNAL`, `UNCERTAIN_EXTERNAL`, `REJECTED` + `reason_code`. Nunca mapear `delivered/read` para `vendido`; status técnicos não ampliam os **oito estados comerciais**.

**Compatibilização S0:** `public.mensagens` exige hoje para saídas `caso_id` e `enviada_por`; a frente principal deverá propor migração compatível com autoria `humano|ia|sistema|template`, sem emprestar identidade do operador à IA, e sem alterar migrations antigas.

## 5. Contrato de intenção de saída e adaptador Meta [P]

**A outbox técnica pode ser compartilhada; os casos de uso são distintos:**

| Origem | Contrato de domínio | Gate antes de publicar para envio |
| --- | --- | --- |
| Resposta gerada pela IA | **C03** | IA está autorizada no caso/versão, não houve handoff, conteúdo permitido |
| Template e recontato | **C06** | Opt-in/opt-out, janela/template, plano elegível, trava e versão do estado |
| Mensagem humana | **C12** | Operador atualmente atribuído e autorizado no mesmo caso/loja |

Entrada proposta para o adaptador Meta, **após** reserva e autorização do backend:

```json
{
  "contract_version": "meta-s0.v0.1-proposed",
  "intent_id": "uuid-intencao-sintetica",
  "concessionaria_id": "uuid-loja-sintetica",
  "canal_id": "uuid-canal-sintetico",
  "sender_phone_number_ref": "fixture_sender",
  "recipient_verified_ref": "protected-recipient-ref",
  "message_kind": "template",
  "authorized_business_action": "C06",
  "authorized_state_version": 42,
  "idempotency_key": "fixture-outbound-001",
  "correlation_id": "fixture-corr"
}
```

O payload real deverá referenciar template/versionamento ou conteúdo protegido, não dados sensíveis em logs/CI. Antes da chamada Graph API, **revalidar no backend** bloqueios de opt-out, canal, atribuição, versão da autorização, sessão/template e takeover humano. Reserva técnica válida **não** substitui autorização de negócio atual. A decisão sobre onde fica a revalidação atômica pertence à frente principal.

Saída do adaptador: `api_accepted`, `provider_message_id` (se fornecido), `http_status`, `meta_error_code`/subcode mínimo, `attempt_id`, `send_state`, `correlation_id`; sem número real ou token em log. HTTP 200 Graph = aceite, **não entrega**.

**Falha com possível aceite da Meta:** estado `UNCERTAIN_EXTERNAL` e reconciliação; **não** reenviar cegamente. Chave idempotente no banco evita efeitos internos duplicados, mas não promete exactly-once de chamada externa.

## 6. Persistência, fila e transação [P]

1. Uma operação interna com permissão mínima recebe **lote de envelopes** e assegura, em transação Postgres, dedupe técnico + inbox + intenção de trabalho.
2. O webhook retorna ACK após commit. Se fila Supabase Queues/pgmq não puder integrar atomicamente no desenho final, usar tabela outbox + relé transacional, evitando janela de perda entre persistência e publish.
3. Worker processa com lease e limite de concorrência e revalida `concessionaria_id` / `canal_id`; mensagens e eventos de status preservam ordem de ocorrência/recebimento e estado de retry.
4. Falhas técnicas recebem backoff, limites, `DEAD_LETTER`, replay autorizado/auditado. Falhas de fonte de verdade/identidade `IDENTITY_CONFLICT` não são retentadas indefinidamente como se fossem indisponibilidade de rede.
5. RLS + GRANT + validação do backend exigidas, inclusive para rotinas de serviço; não confiar só em `service_role` ou autorização embutida em dados do provedor.

**Transação crucial:** inserir `inbox_evento` e a tarefa `outbox_processamento` **na mesma transação**, ou implementar equivalente com garantia durável. Não misturar com a tabela sintética `eventos_callback_sinteticos` nem inferir que `pendencias_inbound_simulado` seja DLQ de produção.

## 7. Erros e observabilidade de fronteira [P]

| Condição | Tratamento e dono |
| --- | --- |
| Meta POST com HMAC ausente/incorreto | Adaptador rejeita; sem efeito comercial |
| App/WABA/sender não vinculados | Adaptador + persistência técnica segura; sem atribuição a concessionária aleatória |
| Banco indisponível/commit falhou | ACK de erro transitório; reentrega/reconciliação segundo política Meta |
| Meta repetiu mensagem externa | `ALREADY_APPLIED`; sem segunda mensagem/resposta |
| Mesmo ID externo mas conteúdo realmente incompatível | `CONFLICT_IDEMPOTENCY_KEY`/quarentena; investigação |
| Chave 8↔9 única, elegível e verificada | Mesmo lead, alias e trilha; sem fusão destrutiva |
| Identidade ambígua | `IDENTITY_CONFLICT`, pendência humana, sem IA disparada |
| Status sem envio correspondente | `PENDING_RECONCILIATION`, sem status comercial inventado |
| Graph timeout após possível aceite | `UNCERTAIN_EXTERNAL`, sem segundo envio automático |
| IA perdeu autorização durante fila | Não enviar; backend cancela intent/audita |

Métricas sem PII: ACK latency (p50/p95/p99), eventos aceitos/duplicados/pendentes, tempo na fila, falhas por categoria, identidade conflito, tempo Graph, incertezas e operações por canal. Logs não podem conter tokens Meta, query de verificação GET, telefone bruto, mensagens ou dados financeiros.

## 8. Testes de contrato cruzados — critério mínimo para evolução [P]

| Caso | Dono dos fixtures/testes | Resultado obrigatório |
| --- | --- | --- |
| IN-01 Meta HMAC válido/inválido, corpo bruto alterado | WhatsApp | Inválido não entra; válido passa ao inbox |
| IN-02 POST com 2 inbound + 2 status | WhatsApp + Principal | 4 unidades duráveis; ACK após commit |
| IN-03 Desconhecido/revogado, número emissor compartilhado erroneamente | Ambas | Sem leak entre lojas; quarentena e auditoria |
| ID-01 Mesmo lead `5581900000000` → `558100000000`, e ordem inversa | Principal | Um lead por loja, aliases auditáveis |
| ID-02 Mesmo número em lojas A/B | Principal | Dois leads/históricos independentes |
| ID-03 Colisão/reciclagem/fixo | Principal | Sem fusão ou resposta automática errada |
| IDEM-01 Mesmo `wamid` 3x, inclusive com telefone variante | Ambas | Um `mensagens`, `ALREADY_APPLIED` |
| IDEM-02 Duas mensagens distintas de mesmo texto | Principal | Duas mensagens legítimas |
| CB-01 Status Meta repetido, atrasado, sem ID de evento | Ambas | Dedup conservador, sem perda de informação |
| CB-02 Callback antes de gravar envio | Principal | Pendência + reconciliação futura |
| OUT-01 IA/humano/template perdendo autorização entre criação e envio | Principal + Meta | Adaptador nunca envia sem autorização vigente |
| OUT-02 Graph timeout incerto | Meta + Principal | Sem retry cego; conciliação |
| SEC-01 Client anon/authenticated tenta escrever inbox/outbox/aliases | Principal | Bloqueado; serviço possui privilégio mínimo |
| SEC-02 Eventos simultâneos mesmo canal/diferentes lojas | Ambas | Sem acesso cruzado |
| OP-01 Falha de banco depois do parser antes de commit | Ambas | Sem `200` falso |
| OP-02 Recuperação de worker morto/lease expirada | Principal | Trabalho retomado sem efeito duplicado |

Os testes devem ser **sintéticos** em PostgreSQL descartável; smoke test sandbox Meta apenas em janela aprovada, sem números comerciais.

## 9. Gate por fase — o que foi e não foi aprovado

| Elemento | Situação |
| --- | --- |
| Supabase como adaptador principal em vez de n8n | **Decidido** |
| DEC-WA-01: resolvedor central de identidade e aliases | **APROVADO [D]** |
| DEC-WA-02: reutilizar e evoluir esquema S0 existente | **APROVADO [D]** |
| DEC-WA-03: inbox/outbox transacionais e execução assíncrona | **APROVADO [D]** |
| Esquemas JSON exatos, RPCs, constraints, migrations, workers | **PROPOSTOS [P]** |
| DEC-WA-04: ambiente Supabase definitivo e titularidade operacional | **PENDENTE [R]** |
| DEC-WA-05: posse/mandato Meta de números da gestora por loja | **PENDENTE [R/V]** |
| DEC-WA-06: segredo/retencão/continuidade/monitoramento/homologações | **PENDENTE [R/V]** |
| Plano Supabase atual Free | **Mantido**, até necessidade comprovada; avisar antes de custo |
| Execução em Supabase, migrations, webhook de produção ou merge | **NÃO AUTORIZADA** por este documento |

**Próxima entrega coordenada sugerida:** a frente principal valida/corrige este contrato quanto a autoria, tipos de evento, permissões e DDL; a frente WhatsApp implementará o adaptador somente depois da revisão, no ambiente explicitamente autorizado. Manter PRs Draft enquanto não houver decisão de merge.

## 10. Referências

- PR #1: `feat/s0-fundacao-prumo`, migrations `202610170001_s0_foundation.sql`, `202610170003_s0_domain.sql`, `202610170009_s0_c02_inbound_synthetic.sql`, `202610170019_c07_callbacks_sinteticos.sql`.
- PR #2: `docs/whatsapp-meta-concessionária de demonstração-poc-20261017`, [Conciliação](conciliacao-pr1-pr2-s0-whatsapp-v0_1.md), [Modelo técnico](modelo-tecnico-ingresso-identidade-idempotencia-v0_1.md), [Contrato webhook](contrato-webhook-meta-supabase-v0_1.md).
- POC `whatsapp-webhook-sandbox`: **ambiente sandbox isolado**, status funcional testado anteriormente, nunca substituir sem autorização.
