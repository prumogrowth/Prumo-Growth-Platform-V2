# Conciliação entre PR #1 (núcleo S0) e PR #2 (WhatsApp/Meta) | v0.1

**Status:** parecer técnico cruzado registrado como **proposta de alinhamento**, não migração, homologação ou aprovação automática de decisões pendentes.  
**Contexto:** parecer recebido da frente principal e conferência de leitura de migrations/documentos da branch `feat/s0-fundacao-prumo`, em 17/10/2026.  
**Fontes de implementação examinadas:** `supabase/migrations/202610170001_s0_foundation.sql`, `202610170003_s0_domain.sql`, `202610170009_s0_c02_inbound_synthetic.sql`, `202610170011_s0_c02_ambiguous_inbox.sql`, `202610170019_c07_callbacks_sinteticos.sql`, `docs/DECISAO_POSTERIOR_EXCLUSIVIDADE_NUMEROS_2026_10_17.md`, `docs/C02_RECEBIMENTO_SIMULADO_S0.md`. Os demais arquivos do PR #1 podem evoluir independentemente; revalidar branch/HEAD na implementação.

**Decisões preexistentes que NÃO estão em discussão neste PR:** usar Supabase diretamente no caminho crítico inicial; telefone comercial escopado por concessionária; número de atendimento dedicado e não compartilhado entre concessionárias; reconhecimento seguro das variantes móveis brasileiras 8↔9; estados comerciais da norma 13A; autorização/hand-off do backend; plano Free enquanto adequado, com apresentação prévia de necessidade de pagamento.

## 1. Resultado executivo

**Compatibilidade conceitual:** SIM. **Compatibilidade do esquema físico atual para integrar Meta em produção:** NÃO AINDA. O PR #1 tem um núcleo **sintético**; o PR #2 descreve contratos e a prova de conceito **Meta sandbox**. Nenhum PR integra atualmente o outro de ponta a ponta.

**Resolução arquitetural proposta:** não implantar estrutura paralela de domínio. Reutilizar `concessionarias`, `canais_loja`, `leads_loja`, `conversas`, `mensagens`, `casos_humanos` e `atribuicoes_humanas`. Adicionar os recursos técnicos ausentes por migrações futuramente aprovadas pela frente principal, sem modificar migrations históricas do S0 e sem alterar o piloto Meta.

## 2. Reconciliação física — o que realmente existe versus o que foi desenhado

| Conceito | S0 vigente em branch PR #1 | Adaptação coordenada proposta [P] | Responsável primário |
| --- | --- | --- | --- |
| Loja/tenant | `public.concessionarias` | Continua a origem de `concessionaria_id` confiável | Principal |
| Número emissor/canal | `public.canais_loja`: `identificador_emissor UNIQUE` global, `modo='simulado'` | **Evoluir a mesma tabela**, preservando ID/FKs/exclusividade. Propor vínculo Meta por `app_ref, waba_id, phone_number_id`, vigência e estado de autorização; modos reais dependem de nova migration e gate | Principal (persistência) + WhatsApp (mapeamento Meta) |
| Lead/telefone | `public.leads_loja`: `UNIQUE(concessionaria_id, telefone_cliente_normalizado)` | Preservar escopo. Resolver alias 8↔9 **antes** de criar lead; adicionar registro auditável de aliases e conflitos; revisar implicações de número compartilhado/reciclado | Principal |
| Identidade E04 | `eventos_identidade` previsto, não identificado como tabela S0 nessas migrations | Implementação/projeção de prova da associação; não duplicar tabela por outro nome sem revisão | Principal |
| Conversa | `public.conversas` | Reutilizar `(concessionaria_id, lead_id, canal_id, caso_id)`; preservar casos humanos e histórico | Principal |
| Mensagens | `public.mensagens`; `origem='simulado'`, `conteudo_sintetico NOT NULL`, autoria de saída via ator e caso | Evolução de conteúdo protegido, origem/autor (`humano|ia|sistema|template`), correlação externa e permissões; manter teste sintético intacto até migração | Principal |
| Pendência inbound | `public.pendencias_inbound_simulado` | Reaproveitar **conceito** de quarentena para identidade ambígua, sem assumir que essa tabela sintética já atende evento real | Principal |
| Evento de integração E29 | Desenhado nos docs 25/30, ainda não parte das migrations S0 examinadas | Inbox técnico durável com idemporência independente de identidade telefônica | Principal |
| Callback C07 | `eventos_callback_sinteticos` depende de `evento_externo_ficticio` | Criar adaptador/projeção Meta conforme IDs reais; não declarar `statuses[].id` ID único do callback | Principal (estado) + WhatsApp (parser) |
| Fila/outbox | Não há infraestrutura de ingresso/saída **real da Meta** nos arquivos auditados | Uma transação de inbox + intenção de processamento durável; outbox única para efeitos autorizados | Principal |
| Adaptador Graph API | POC no Supabase externo ao código S0 | Implementar versão nova e versionada, sem copiar resposta síncrona da POC para produção | WhatsApp |

**Atenção de naming:** `loja_id` em contratos é **identidade lógica**; o físico S0 usa `concessionaria_id`. No PR #2, `canais_whatsapp` e `aliases_contato_canal` são **nomes candidatos**, não autorização para criar cadastro duplicado.

## 3. Decisões técnicas compartilhadas propostas

### DEC-WA-01 — Número canônico e conflito de identidade [P; confirmação conjunta]

**Regra de produto já decidida [D]:** representações elegíveis `55 + DDD + 9 + oito dígitos` e `55 + DDD + oito dígitos` são o mesmo número lógico para busca e identificação no escopo de cada loja, **sem duplicar leads quando há correspondência única e confiável**.

**Problema S0 demonstrado:** C02 `receber_mensagem_sintetica` busca/insere `p_telefone` literal, com `UNIQUE(concessionaria_id, telefone_cliente_normalizado)`. Assim, variantes podem virar dois leads. No replay de `id_externo` o código compara `v_tel_antigo` com `p_telefone`, causando `CONFLICT_IDEMPOTENCY_KEY` por diferença só do nono dígito.

**Mudança candidata:** centralizar no **núcleo** um resolvedor `(concessionaria_id, source_evidence, raw_digits) → matched_lead | provisional | conflict`; usar lookup exato + comparação 8↔9 restrita a celular BR confiável e correspondência única; salvar alias/forma recebida/origem/verificação/histórico; todos os aliases do mesmo contato comercial resolvem ao mesmo `lead_id`. Identidade técnica e civil não são equivalentes. Em dois candidatos, origem duvidosa, telefone fixo ou reciclado, **não fundir registros** e não responder como IA; preservar evento/abrir revisão humana.

**Revisão da restrição:** a UNIQUE atual de `leads_loja` pode permanecer como proteção por representação principal, mas **não basta** para impedir dois leads de alias diferente. Exigir controle transacional, chave/índice escopado de aliases, colisão e concorrência. Não fazer `UPDATE` destrutivo de todo telefone antigo nem `UNIQUE` global. A mesma numeração pode existir em lojas A e B com históricos distintos.

**Comportamento de mensagem repetida:** primeiro deduplicar pela **identidade externa da mensagem e canal**; depois validar coerência de conteúdo e identidade resolvida. Variação 8↔9 **não deve** causar conflito sozinha. Payload conflitante para o mesmo ID externo **pode** indicar problema real e exige quarentena.

### DEC-WA-02 — Modelo físico sem estruturas paralelas [P; confirmação conjunta]

- Evoluir `canais_loja` em migrations aditivas com vínculo temporal app/WABA/Phone Number ID, **preservando** `identificador_emissor UNIQUE` global e FKs compostas. `modo='simulado'` é check atual; não cadastrar números comerciais como se o canal real fosse simulado, nem desabilitar restrição sem revisão de domínio e segurança.
- Preservar as tabelas já criadas `conversas`, `mensagens`, `casos_humanos`, `atribuicoes_humanas`; introduzir autoria técnica distinta do ator humano. Saídas de IA/sistema/template **não ganham `enviada_por` de operador** e passam por autorização final do backend. O predicado atual `saida ⇒ caso_id AND enviada_por` deve evoluir em mudança compatível, sem reescrever migrations S0.
- Usar E04 para trilha de identidade e E29 para ingressão técnica; alias pode ser uma projeção/index auxiliar, não cadastro comercial alternativo. Não reutilizar `pendencias_inbound_simulado` como se fosse uma fila operacional real.
- O `id_externo` de `mensagens` é da mensagem; aliases de telefone não participam da sua unicidade. Registrar status e correlação da Graph API separadamente.

### DEC-WA-03 — Inbox/outbox, idempotência e C02/C06/C07 [P; confirmação conjunta]

```text
Webhook Meta (GET challenge; POST HMAC bytes brutos)
  → resolve app/WABA/número em canal_id + concessionaria_id confiáveis
  → uma transação grava item(ns) técnicos do inbox e trabalho durável
  → ACK HTTP 200 após commit (não espera Graph API nem IA)
  → worker escopado → núcleo aplica C02 inbound ou C07 callback
  → backend autoriza C03 resposta IA, C12 humana ou C06 templates
  → outbox única de intenção autorizada → adaptador Meta
  → retorno/status técnico + correlação/reconciliação
```

- Um POST pode incluir vários `entry/changes/messages/statuses`; separar unidades lógicas e idempotência.
- C02 sintético existente é prova de regras de negócio, **não interface externa** para a Meta; necessidade de service gateway autenticado e menor privilégio, com ACL/GRANT/RLS e auditoria.
- `C06` mantém o escopo de **execução de templates** previsto na S0; C03 (IA) e C12 (humano) têm autorizações próprias e convergem apenas para o **mecanismo de saída**. Evitar chamar toda saída WhatsApp de C06.
- Na Meta, `statuses[].id` é normalmente a identidade da **mensagem enviada**, não de cada callback. A chave sintética `evento_externo_ficticio` não pode ser copiada como exigência externa. Dedupe de status por envelope/atributos aprovados, preservando ordem de chegada e `timestamp` do fornecedor; incerteza de evento sem ID único deve ser tratada explicitamente.
- `200` da Graph API = **aceite de requisição**, não entregue, lido ou vendido; callback técnico não altera os oito status comerciais.
- Inbox/outbox podem garantir um efeito interno idempotente, **não garantem exatamente um envio externo** caso Meta tenha aceitado antes de timeout. Marcar `UNCERTAIN_EXTERNAL` e reconciliar, sem retry cego.
- Token HMAC Meta e verificador HMAC interno S0 **são credenciais distintas**, contextos distintos e não devem compartilhar chaves.

## 4. Responsabilidades e interface de equipe [P]

| Atividade | Titular recomendado | Interface obrigatória |
| --- | --- | --- |
| Entidades comerciais, identidades, aliases, permissões, migrations/segurança | **Frente principal** | Versão do contrato de resolução + políticas de conflitos + testes de loja |
| `canais_loja` (persistência e FKs) | **Principal** | WhatsApp especifica formato e ciclo de vida WABA/Phone Number ID |
| Adaptador de webhook, HMAC Meta, parsing e Graph API | **WhatsApp** | Envelope versionado + identificadores técnicos, sem decisões comerciais |
| Inbox/outbox/queue e procedimentos SQL | **Principal** | WhatsApp informa IDs/códigos de erros e requisitos de ACK/replay |
| Workers C02/C07 e fontes de verdade de mensagem/status | **Principal** | WhatsApp fornece eventos normalizados e correlação técnica |
| Worker de saída Meta | **WhatsApp** | Recebe intenção autorizada, destino validado, credencial de canal e idempotency key |
| IA, templates, handoff, estado comercial e alçadas humanas | **Principal** | Entrega de intents autorizados pela outbox, revalidação no envio |
| Testes integrados e autorização de rollout | **Ambas** | Dados sintéticos, ambiente isolado e aprovação explícita |

**Observação de implantação:** provedor **Supabase** está decidido; projeto Supabase definitivo **não** foi escolhido por essa decisão. POC no projeto `projeto-supabase-omitido` permanece isolada; o doc 30 prevê um projeto novo/exclusivo. Plano atual Free não impõe contratação nesta fase documental.

## 5. Matriz de incompatibilidades e provas antes de código

| Prioridade | Evidência do código S0 | Adequação exigida | Testes de aceite |
| --- | --- | --- | --- |
| **CRÍTICA** | `leads_loja` usa telefone literal, UNIQUE por loja | resolvedor 8↔9 transacional + alias | primeiro 8→9 e depois 9→8, concorrência, importação; **mesmo lead** |
| **ALTA** | C02 rejeita replay com diferença só no `p_telefone` | ID externo controla replay, alias resolvido em paralelo | mesmo `message.id` com formato alternado = `ALREADY_APPLIED`, sem segunda mensagem |
| **ALTA** | C07 pressupõe `evento_externo_ficticio` | callback Meta independente de ID único de evento | repetidos/fora de ordem/pending reconciliation |
| **ALTA** | `mensagens` saída exige `caso_id` e `enviada_por` | autoria explícita para humano/IA/sistema/template | cada tipo passa permissões próprias, nenhum impersonation |
| **ALTA** | `canais_loja.modo='simulado'` | evolução aditiva, posse/mandato e canal ativo validado | nenhum sender comercial entra por bypass |
| **ALTA** | webhook POC espera Graph antes de ACK, sem inbox | persistência durável + ACK rápido | falha de DB não retorna 200; falha Graph não apaga evento |
| **ALTA** | S0 e POC em ambientes independentes | contrato de interface e projeto definitivo autorizados | nenhum SQL de produção aplicado a POC por inferência |
| **ALTA** | verificador HMAC S0 e Meta têm objetivos distintos | segredos/validações separados, menor privilégio | chamada assinada pelo app ≠ permissão de alterar status comercial |

**NÃO são evidências executadas:** testes de alias, filas/worker, carga, reconciliação real Meta, permissões com números comerciais e produção. Requer CI em PostgreSQL descartável após implementação autorizada.

## 6. Decisões agrupadas para o responsável — sem aprovação por silêncio

| Grupo | Proposta | Estado |
| --- | --- | --- |
| **DEC-WA-01** Identidade | resolvedor no núcleo; aliases seguros + conflitos e histórico | **Recomendado [P]** |
| **DEC-WA-02** Modelo físico | evoluir tabelas S0 existentes, sem domínio paralelo | **Recomendado [P]** |
| **DEC-WA-03** Transações | inbox/outbox num único fluxo transacional, ACK durável, workers e reconciliação | **Recomendado [P]** |
| **DEC-WA-04** Ambiente | decidir instância/projeto dedicado e responsáveis antes de migration; não presumir POC | **Pendente [R]** |
| **DEC-WA-05** Posse Meta | titularidade/mandato dos números/contas/WABAs por loja e modelo onboarding | **Pendente [R/V]** |
| **DEC-WA-06** Operação | segredos, rotação, retenção, backups, SLA, fallback/quarentena, plano de segurança | **Pendente [R/V]** |

As decisões 01–03 são uma proposta tecnicamente consistente das frentes, **não autorização para executar DDL**. Os grupos 04–06 dependem de provas e aprovações próprias. Não contratar Supabase Pro por esse documento; só informar necessidade objetiva antes da etapa correspondente.

## 7. Ordem de implementação sugerida e gates

1. Revisão conjunta do presente documento com PR #1 e contrato WhatsApp v0.1, incluindo RLS e redução de privilégios comerciais `postgres` pendentes na S0.
2. Homologar interface e titularidade dos aliases: `concessionaria_id`/escopo, erro e estado de conflito, mapping Meta e contratos C02/C07/C03/C06/C12.
3. Obter aprovação agrupada 01–03; autorizar projeto Supabase/ambiente conforme 04; **não** executar migrations por dedução.
4. Desenvolver migrations candidatas **na branch proprietária do backend**, PostgreSQL descartável, invariantes, RLS/GRANT, constraints, índices e rollback.
5. Criar Edge Function/worker Meta **versionados** e separados da `whatsapp-webhook-sandbox` sandbox; testes HMAC, ACK, replay, bursts e canal desconhecido.
6. Validar C02/C07 contra eventos sintéticos e Meta sandbox, depois saída C03/C06/C12 e handoff, sempre com destino de teste autorizado.
7. Só após validação de Meta/Banco/LGPD/continuidade/mandato de emissor, negociar eventual operação comercial. A necessidade de upgrade Free→pago deve ser apresentada **antes** de dependência paga.

## 8. Referências e controle

**Parecer de origem:** “Parecer técnico — compatibilidade entre a plataforma LiberaCred e a frente WhatsApp/Meta”, recebido nesta conversa, com recomendações DEC-WA-01–06; não houve mudanças na outra frente durante a auditoria recebida.

**Código S0 (PR #1):** `supabase/migrations/202610170001_s0_foundation.sql` (telefone UNIQUE por loja), `202610170003_s0_domain.sql` (canais, mensagens e autoria), `202610170009_s0_c02_inbound_synthetic.sql` (lookup, replay), `202610170011_s0_c02_ambiguous_inbox.sql` (pendências), `202610170019_c07_callbacks_sinteticos.sql` (callback e unicidade sintética). **Somente leitura.**

**Frente WhatsApp (PR #2):** [Contrato Meta/Supabase](contrato-webhook-meta-supabase-v0_1.md); [Modelo de ingressão/identidade/idempotência](modelo-tecnico-ingresso-identidade-idempotencia-v0_1.md); [ADR Supabase direto](adr-001-transporte-webhook-supabase-vs-n8n.md); [POC concessionária de demonstração](poc-meta-sandbox-documentacao-publica-2026-10-17.md).

**Regras de proteção:** sem alterar migrations S0, sem merge ou alteração automática do PR #1, sem implantar novo webhook/SQL, sem usar números comerciais; sem confundir sinal de sandbox com prontidão para produção. Alteração atual é exclusivamente documental e solicita coordenação antes de engenharia.
