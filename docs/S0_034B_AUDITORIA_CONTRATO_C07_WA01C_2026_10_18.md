# S0-034B — auditoria do contrato C07 e WA-01C (18/10/2026)

**Estado:** avaliação contratual com regressões sintéticas. **Nenhuma nova migration nesta etapa**, nenhuma ligação automática entre `inbox_eventos_s0` e o núcleo C07, nenhum serviço Meta, credencial, HTTP ACK, envio ou deploy. O PR #1 preserva 001–034; PR #2 continua Draft. Base revisada: PR #1 HEAD `b890e501de1ee9968143a9f6d5467724e2575310`, PR #2 HEAD `58f6ac63e3a311bba261a081bb305109fc731b6c` no início deste incremento.

## 1. Fonte de verdade e precedência

- `202610170019_c07_callbacks_sinteticos.sql`: contrato privado `registrar_callback_c07_sintetico(canal,correlacao,evento,status,instante)`; `evento_externo_ficticio` é **ID único artificial da ocorrência de teste** por canal e loja, enquanto `correlacao_externa_ficticia` identifica o envio ligado à mensagem; observações fora de ordem não mudam os oito estados comerciais.
- `202610170020_c07_reconciliacao_falhas_sintetica.sql`: pendências e auditoria de reconciliação; gestor escopado, decisão versionada sem reenvio.
- `202610170021_c07_bloqueio_retry_incertos.sql` e `202610170022_c07_auditoria_replay_eligibilidade.sql`: falhas/incertezas bloqueiam novos planos/reservas automáticos; o replay do plano não deve afirmar elegibilidade vigente.
- `202610180029_s0_inbox_outbox_sinteticos.sql` e `202610180030_s0_replay_multicanal_fixture.sql`: inbox técnica ainda restrita ao laboratório, **não** é adaptador C07 operacional e **não** autoriza ACK Meta. O lote da 030 representa status por `st:<message-id>:<status>:<timestamp>`.
- PR #2 `docs/integracoes/whatsapp-meta/wa01c-ids-eventos-meta-e-correlacao-v0_1.md` e `integrations/whatsapp-meta/technical-keys.ts`: WA-01C **candidato [P]**, `safe_to_auto_dedupe:false`. Segundo o documento da frente Meta, `messages[].id` é ID da mensagem inbound, mas `statuses[].id` é ID da **mensagem de saída**, não da observação de status. `status+timestamp` é pista, não prova de evento único.
- DEC-WA-01/02/03 aprovadas como direção e DEC-WA-05 aprovada quanto à titularidade App/WABA/emissor **por concessionária**. DEC-WA-04/06 ainda pendentes.

## 2. Resultado da comparação — riscos e invariantes

| Item | Resultado no S0 atual | Gate para futura integração |
| --- | --- | --- |
| Correlação de envio | `correlacao_externa_ficticia` por loja, consulta também `canal_id`; callback não encontrado vira `PENDENTE_RECONCILIACAO` | Exigir identidade autenticada de App/WABA/emissor→canal, com vigência e revogação |
| Identidade de evento C07 | `evento_externo_ficticio` obrigatório e único por loja+canal, passado **pelo caller de teste**, não fornecido pela Meta | **Não copiar `statuses[].id` para `evento_externo_ficticio`**; falta política de occurrence-ID, payload guardado e dedupe aprovado |
| Status com mesmo segundo | 019 armazena ambos **se** cada ocorrência tiver um token interno distinto; 030 colapsa status/timestamp na chave técnica e gera conflito quando fixture difere | A chave WA-01C é *hint* não autoritativo; guardar observações sem perder ocorrência legítima e sem reprocessar efeito |
| Fora de ordem | `fora_de_ordem` baseado em timestamp e flags técnicas monotônicas por OR; nunca altera ciclo | Definir semântica ordenada Meta e conflitos de status; relógio/precisão não comprovam ordem civil |
| Falha/incerto/contradição | Triagem e bloqueio de retry automático existentes no C07 sintético | Preservar separação HTTP Graph ACEITO ≠ entregue/lido; decisão de reenvio incerto exige conciliação |
| Autorização | `current_user='postgres'` só no ensaio; select de gestor escopado e escrita de API revogada | Privilégio mínimo, autenticação e segregação Meta HMAC vs gateway interno continuam pendentes |
| Efeito comercial | C07 não muda oito estados, não dispara mensagem | `status` Meta nunca autoriza marcar `vendido` |
| Transação e ACK | A 030 aceita lote de fixture, sem corpo Meta real recuperável | Exigir persistência íntegra, guarda durável e resultado `COMMITTED` verificado antes de HTTP 200 |
| Cliente 8↔9 | Não pertence ao contrato de identificador de callback | Não usar normalização de telefone como chave de envio ou como ID C07 |

### Limite confirmado que bloqueia o adaptador

A 030 define `chave_evento` do status com ID da mensagem + tipo do status + instante do provedor. Se duas observações distintas tiverem os mesmos três campos, ela **não possui ID de ocorrência para diferenciá-las**. Com payload/fingerprint divergente, a própria função retorna `CONFLICT_IDEMPOTENCY_KEY`. Com payload idêntico, ela as considera replay da fixture. Ambas são escolhas **laboratoriais**; não podem ser promovidas a idempotência Meta sem aprovação de contrato e política de retenção. O sistema não deve transformar a pista SHA-256 da WA-01C em supressor automático de eventos.

### Outros cuidados

A reconciliação humana do C07 existente não é uma operação com Meta real, não autoriza envio ou altera `envios_template_sinteticos` como prova externa. A S0-034A garante atomicidade C02 apenas para tarefas com fixture C02 e não resolve callback C07. A outbox S0 continua bloqueada. Não adicionar RPC pública, worker ou função privilegiada com assinatura Meta nesta etapa.

## 3. Teste adicional independente (sem migration)

Novo `supabase/tests/s0_wa_034b_c07_contrato.sql`, executado no runner protegido, com os casos:

- `WA34B-CB-01`: um único ID da mensagem enviada recebe status diferentes e duas observações de mesmo status/timestamp com **IDs locais fictícios distintos**, que são preservados; repetição **do mesmo ID local** é idempotente, evento atrasado marcado, nenhuma mudança comercial.
- `WA34B-CB-02`: reutilizar deliberadamente o ID da mensagem como o ID da ocorrência provoca conflito ao observar outro status; é evidência negativa de que o API C07 de teste não pode consumir `statuses[].id` diretamente como `p_evento`.
- `WA34B-CB-03`: mensagem correlacionada na loja A/canal A1 não se correlaciona em A2 nem na loja B; resulta em pendência, nunca empréstimo de envio de outro escopo.
- `WA34B-CB-04`: caracterização negativa do protótipo 030 — um mesmo status/timestamp com marcador diferente gera conflito e não pode ser anunciado como dedupe segura da Meta.

Não editar C07 019–022, inbox 029/030, nem desligar nenhuma regressão antiga. O teste deve executar em `prumo_s0_test_*` no PostgreSQL local descartável. **Registre PASS apenas após confirmar CI e commit exatos em `tests/S0_ACEITE.md`.**

## 4. Retorno exigido da frente WhatsApp/Meta antes do C07 real

1. Confirmar o envelope autenticado e o identificador de *ocorrência de observação* gerado por **nosso ingresso**, distinto de `statuses[].id`, sem assumir que status+segundo é único.
2. Definir se/quando duas observações equivalentes podem compartilhar efeito de processamento sem descartar o registro/auditoria de ingressão; discriminar reentrega de ocorrência distinta quando possível, sem prometer `exactly-once` externo.
3. Definir conteúdo bruto e metadados indispensáveis ao reconhecimento de status e falha, histórico e proteção de payload sob DEC-WA-06, além do comportamento de múltiplos Apps/canais no mesmo POST.
4. Mapear com vigência e autorização App/WABA/phone_number_id→canal do núcleo e revogação; DEC-WA-05 determina propriedade por loja, não autorizou credenciais reais.
5. Estabelecer política para status contraditórios, entregas tardias, referências desconhecidas e HTTP 200/5xx após commit, sem liberar reenvio automático.

**Gate:** GO para auditoria e regressões sintéticas; **NO-GO para qualquer ligação inbound C07 à Meta, implantação hospedada, canal real ou produção**. Próximo incremento só após pactuar semântica de ocorrência e proteção durável, mantendo C07 comercial inalterado.
