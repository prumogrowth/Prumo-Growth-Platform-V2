# ADR-001 — Transporte WhatsApp/Meta: Supabase direto versus n8n

**Data:** 17/10/2026 (revisão técnica após POC, logs em 18/10 UTC)  
**Status:** **DIREÇÃO SUPABASE DIRETO ESCOLHIDA PELO RESPONSÁVEL** (planejamento, sem implementação de produção). Avaliação de filas, SLA e detalhes técnicos ainda [P/R].  
**Contexto:** frente WhatsApp/Meta — concessionária de demonstração / plataforma de atendimento LiberaCred.  
**Escopo:** arquitetura de recepção/entrega de eventos Meta e comunicação com núcleo transacional; não define a arquitetura total de IA, campanha, CRM ou instituição financeira.

## 1. Pergunta arquitetural

É necessário colocar n8n no caminho crítico entre a Meta WhatsApp Cloud API e o Supabase, ou Edge Functions + Postgres + filas no Supabase atendem com latência, confiabilidade e custo aceitáveis?

**Diretriz escolhida pelo responsável para a fase inicial:** **Supabase direto como adaptador e gateway padrão da Meta**, preservando a possibilidade de n8n **fora do caminho crítico** para automações visuais, integrações heterogêneas, rotinas agendadas ou workflows operacionais quando houver benefício demonstrável. Não contratar nem instalar n8n por premissa de performance.

## 2. Evidência efetivamente medida versus hipótese

### Medido no piloto (não benchmark)

- Meta `messages` inbound → Supabase Edge Function com validação HMAC: evento real confirmado.
- Supabase → Meta Graph API de mensagens: `SANDBOX_AUTO_REPLY sent:true api_status:200` registrado, com confirmação de recebimento pelo operador.
- Números comerciais existentes não foram migrados nem utilizados como remetentes no teste.
- **Não** foram medidos p50/p95/p99, throughput, cold start, custo por evento, concorrência, falha sob carga, confiabilidade de fila nem operação ininterrupta.
- **Não** houve instalação, medição ou carga comparativa envolvendo n8n.

Portanto, a POC prova **viabilidade funcional**, não superioridade quantitativa de uma arquitetura sobre a outra.

### Documentação e condicionantes externos

- A própria Supabase apresenta Edge Functions como endpoints HTTP de baixa latência e receptores de webhooks; há limites de recursos, incluindo CPU de 2 s por request e memória de 256 MB no ambiente hospedado: https://supabase.com/docs/guides/functions e https://supabase.com/docs/guides/functions/limits
- Supabase Queues (baseadas em Postgres/pgmq) suportam fila durável e consumo por Edge Functions; sem garantir **exatamente um efeito de negócio** por si só. A deduplicação no domínio continua indispensável: https://supabase.com/docs/guides/queues e https://supabase.com/docs/guides/queues/consuming-messages-with-edge-functions
- n8n suporta modo fila, Redis e workers horizontais; **a documentação reconhece overhead/latência adicional de webhooks quando uma execução vai para worker**: https://docs.n8n.io/hosting/scaling/queue-mode/
- A performance de n8n depende do fluxo e dos recursos disponíveis. Benchmarks publicados pelo fornecedor **não são comparação direta** com a arquitetura Supabase do projeto: https://docs.n8n.io/hosting/scaling/performance-benchmarking/
- Custos e condições de licenciamento/hosting do n8n devem ser avaliados quando houver caso real; não assumimos SaaS white-label permitido irrestritamente. Referência do projeto: documento 43 (Playbook GitHub/Supabase/Custos n8n).

## 3. Comparação qualitativa (estimativas arquiteturais, não medições)

| Critério | Edge Functions + Postgres/Queue Supabase | n8n no caminho crítico |
| --- | --- | --- |
| Tempo de resposta do webhook | Menos componentes no percurso; **potencialmente** menos overhead | Depende de instalação/configuração; fila e workers podem introduzir overhead |
| Escala de webhook | Requer desenhar processamento desacoplado, fila, workers e monitoramento | Escala horizontal via workers/webhook processors, usando Redis + BD e infraestrutura |
| Confiabilidade | Suportável com persistência transacional, dedupe, outbox/queue e retries implementados | Bons recursos de workflows; não elimina necessidade de dedupe/estado transacional |
| Conectores SaaS | Integrações HTTP/SDK por código | Ampla biblioteca visual, vantagem se houver muitas integrações externas |
| Manutenção | Código versionado/testável, requer engenharia | Menos código para integrações simples, mas requer governança de fluxos/instância |
| Operação/custos | Consumo do Supabase + banco/fila; observar quotas e plano | Instância/plano n8n, Redis/BD/observabilidade; custo varia |
| Governança multitenant | Regras centralizáveis em serviços + RLS/ABAC | Regras devem permanecer no backend, fora dos nós de fluxo |
| IA conversacional | Pode chamar serviços de IA e núcleo por interfaces versionadas | Pode orquestrar IA, mas workflow não deve ser fonte de verdade comercial |

**Conclusão da comparação:** n8n **não é intrinsecamente mais rápido**; Supabase parece suficiente para o adaptador Meta. A escolha quantitativa final exige benchmark controlado.

## 4. Desenho recomendado para avaliação (ainda não executado)

```text
Meta Cloud API (webhook)
    |
    v
Supabase Edge Function: GET verificação / POST HMAC e limite de payload
    |
    +--> roteamento WABA + phone_number_id -> canal_id + loja_id
    +--> dedupe e persistência durável mínima do evento
    +--> resposta HTTP 200 rápida, APÓS persistir/aceitar com segurança
              |
              v
        Fila durável / outbox (Postgres / Supabase Queues)
              |
              v
    Worker(s) separados para validação de negócio, IA e roteamento humano
              |
              v
        Núcleo transacional de estados e permissões
              |
              v
         Outbox de envios WhatsApp
              |
              v
   Adaptador de saída Meta + IDs, retries e callbacks de status
```

**Se a persistência falhar, não reconhecer sucesso fictício.** Política de erro/retentativa de webhook Meta e tratamento de janela precisam ser validados; não fazer chamadas longas de IA ou aguardar envio Meta antes de reconhecer webhook. Usar `waitUntil` só para tarefas cuja perda seja aceitável ou já duravelmente registrada, jamais como única garantia de entrega.

### Contrato de fronteira proposto (rascunho; não é API em produção)

- **Origem e identidade:** `provider=meta_whatsapp`, `waba_id`, `phone_number_id`, `channel_id`, `loja_id` e referência de assinatura validada. Buscar `loja_id/canal_id` por cadastro confiável do backend; não aceitar tenant declarado pelo payload de forma autossuficiente.
- **Envelope interno versionado:** `contract_version`, `event_id`, `request_id`, `correlation_id`, `idempotency_key`, `occurred_at`, `recorded_at`, `event_type`, `payload_ref` protegido e origem autenticada. **Não usar telefone puro como FK global**. Alinhar a docs 25/26/28/40.
- **Recebimento:** comando conceitual C02 `receber_inbound`, chave candidate `provider + channel_id + external_message_id + inbound`. Mensagem duplicada não cria nova resposta.
- **Status:** comando conceitual C07 `callback_meta`, chave separada para status; diferenciar requisição aceita HTTP 200, ID retornado, enviado, entregue, lido e falhou sem afirmar entrega por aceite de API.
- **Envio:** comando conceitual C06 `executar_envio`, sempre com `idempotency_key`, elegibilidade de janela/template, opt-out, estado e alçada revalidados antes do envio; registrar `message_id` externo/status/erro sem marcar venda.
- **Handoff:** após passagem ao humano, a IA não responde ao caso; mensagem espontânea em `cadastro enviado ao banco` ou `vendido` segue as regras atuais da mesma loja, sem reativar IA nem apagar histórico (docs 11/21/22/26).
- **Segurança:** RLS + GRANT + ABAC; credenciais Meta por empresa/WABA no servidor e rotação; dados pessoais mínimos com retenção definida e controles LGPD. Não expor logs brutos, templates ou documentos sensíveis entre concessionárias.
- **Fonte de verdade:** transações de negócio, oito status comerciais e autorizações são responsabilidade do backend/Postgres, não do webhook nem do n8n. Docs 11/26/41/43.

## 5. Experimento de decisão (futuro)

Comparar em ambientes isolados com mesmos eventos **sintéticos**, configuração de capacidade conhecida, mesma região e cargas progressivas:

- **A:** Edge Function Supabase → persistência → fila/worker → outbox.
- **B:** Edge Function de autenticação → n8n → operações equivalentes no Supabase (sem duplicar regras); e, se necessário, n8n webhook diretamente com verificação HMAC equivalente.
- Registrar p50/p95/p99 de **ACK Meta**, latência evento→persistência, processamento→resposta aceita, tempo até callback de entrega, throughput sustentável, duplicações/efeitos duplicados, retries, backlog, erros, custo e esforço operacional.
- Testar rajadas, falha de Redis/BD/worker/Meta, repetição de eventos, entrega fora de ordem, expiração de token, falha de IA e indisponibilidade de rede.
- Adotar SLA/limiares quantitativos **antes dos testes** por decisão da equipe; não inventar números nem declarar vencedor por benchmark externo de laboratório.
- Comparar custo total (incluindo manutenção), não somente preço da chamada API. A latência da Meta e dos serviços de IA também compõe o tempo percebido pelo cliente.

## 6. Portões de decisão e riscos remanescentes

1. **APROVAÇÃO ARQUITETURAL:** revisar com a frente de desenvolvimento, usando matriz 13/13A, interfaces 25/26/40 e segurança 28/33/41.
2. **NÃO PRODUÇÃO:** POC não autoriza números comerciais, campanha, dado cadastral financeiro real nem atendimento bancário.
[TRECHO COMERCIAL INTERNO EXCLUÍDO DA VERSÃO PÚBLICA]
4. **TENANCY DOS CANAIS:** histórico prevê números **dedicados da gestora por loja**, enquanto a POC usou app/conta de teste no contexto empresarial da concessionária. **Modelo de posse WABA/número/mandato da gestora e padrão de integração definitiva ainda precisa de decisão**, sem presumir que o piloto resolve.
5. **SEM DECISÃO DE COMPRA:** n8n permanece opcional e não contratado; reavaliar apenas por fluxo que demonstre ganho de tempo de desenvolvimento, integração ou operação.

**Referências internas:** pacote de documentação do projeto, especialmente `11_Arquitetura_Geral_Consolidada_v4_8.md`, `26_Contratos_Conceituais_Eventos_APIs_v0_1.md`, `28_Especificacao_Confiabilidade_Privacidade_Recuperacao_v0_1.md`, `34_Roteiro_Homologacoes_Meta_Banco_LGPD_Decisoes_Agrupadas_v0_1.md`, `40_Contratos_Interfaces_Campos_Operacionais_Rastreabilidade_v0_1.md`, `43_Playbook_Inicio_Tecnico_GitHub_Supabase_Custos_n8n_v0_1.md`. O pacote é fonte de planejamento, não prova de implementação.

## 7. Deliberação posterior e documento derivado

**Decisão expressa do responsável:** prosseguir com Supabase diretamente; Supabase Free durante desenvolvimento enquanto suficiente; comunicar ANTES de qualquer etapa que objetivamente exija plano pago. n8n não integra o caminho crítico inicial, podendo ser reconsiderado por comparação medida e ganhos reais.

**Novo requisito de identidade:** suportar telefones brasileiros com oito ou nove dígitos locais (após DDD), com variantes/aliases por loja e sem fusão automática sem evidência. Regras propostas no [Contrato de integração Meta ↔ Supabase v0.1](contrato-webhook-meta-supabase-v0_1.md). A especificação do contrato é proposta; não implementa componentes.
