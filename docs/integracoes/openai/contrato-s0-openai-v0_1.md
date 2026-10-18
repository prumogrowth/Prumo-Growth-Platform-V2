# OAI-01 — Contrato candidato S0 ↔ OpenAI | v0.1

**Data:** 18/10/2026 | **Estado:** [P] proposta para revisão cruzada, [R] escolhas e autorizações pendentes, [V] condições externas a validar.
**Aplicação:** terceira frente independente, sem modificar escopo, backlog, código, PRs ou ritmo das frentes S0 e WhatsApp/Meta.
**Natureza:** desenho de interfaces, NÃO endpoint criado, schema aprovado, API conectada, prova de autenticação, autorização de dados reais ou liberação comercial.

## 1. Escopo e donos — cláusula de não interferência

| Responsabilidade | Dono preservado | Limite da frente OpenAI |
|---|---|---|
| Domínio comercial, autenticação de atores, autorização loja/caso, RLS/GRANT, cadastros, oito estados, handoff, C03/C05/C08/C10/C12 e auditoria de domínio | **S0 / PR #1** | Consumir contrato autorizado, nunca modificar regras, estados, SQL, tabelas, workers ou autorizações por decisão própria |
| Persistência de mensagens, contexto comercial confiável, versions, inbox/outbox e decisão final de publicar uma mensagem | **S0 / PR #1** | Receber somente contexto filtrado/autorizado e devolver proposta tipada; não criar segundo banco, fila nem fonte de verdade |
| Webhook, HMAC Meta, números/canais por concessionária, Graph, templates como transporte, recibos, callbacks e reconciliação externa | **Meta / PR #2**, conforme fronteira acordada com S0 | Não enviar ao WhatsApp diretamente, não tocar em credenciais Meta ou em seus módulos |
| Criação de projeto de API OpenAI, emissão/revogação de credencial, armazenamento MANUAL da chave pelo responsável e decisão sobre gastos | **Responsável humano** | Especificar procedimento e evidências NÃO sensíveis; nunca inserir a chave no GitHub, em logs ou na conversa |
| Adaptador de provedor OpenAI, tratamento do protocolo da API, normalização de retorno e erros, política técnica de timeout e rastreabilidade sem PII | **Frente OpenAI [P]** | Especificar porta independente de transporte; implementar em branch própria apenas quando autorizado, com testes sintéticos, sem decidir n8n versus ligação direta antecipadamente |
| Configuração do comportamento IA Vendedora e IA Planejadora | **Governança humana com execução/validação S0 [D/P]** | Podem existir propostas de prompts/versionamento, mas não mudança autônoma de parâmetros; sem IA Analista |
| ChatGPT/MCP administrativo e confirmações de escrita | **Fluxo independente vigente** | Não absorver por esta frente a autorização/escrita MCP |

**Regra de conflito:** se a frente S0 ou Meta já estiver desenvolvendo uma funcionalidade ou contrato que tangencie OpenAI, não apropriar nem reatribuir o trabalho. Formalizar somente a dependência e solicitar revisão cruzada sem interromper a execução original.

## 2. Capacidades vigentes [D] e escopo de implementação [P]

- **IA Vendedora:** atendimento comercial C03, linguagem adequada, coleta progressiva, respostas breves e encaminhamento a humano quando cabível; proibição de inventar aprovação bancária, taxas, ofertas ou resultados.
- **IA Planejadora de Recontatos:** propõe escolhas de quantidade/horário/intervalo e **versões de templates já aprovados**, sem gerar novos textos de template; backend S0 efetua elegibilidade, versão, programação e cancelamento.
- **Handoff definitivo:** após transição para atendimento humano ou cadastro enviado ao operador, IA Vendedora não retoma naquele caso. Revalidar antes da chamada e novamente antes de qualquer publicação. Falhas técnicas não suspendem globalmente handoffs nem reparam software automaticamente.
- **IA Analista autônoma: fora do escopo [D].** Não adicionar testes, capacidade latente, módulo opcional ou treino autônomo de regras para isso.
- **MCP:** não é caminho para contornar as regras acima; escritas exigem autenticação, escopo e segunda confirmação inequívoca do responsável.

## 3. Contrato candidato de entrada S0 → adaptador OpenAI [P]

A S0 seria responsável por gerar envelope privado com, no mínimo:

| Campo candidato | Origem e exigência |
|---|---|
| contract_version | Valor candidato 's0-openai.v0.1-proposed'; rejeitar versões incompatíveis |
| request_id / correlation_id | IDs opacos gerados no backend, não telefone/CPF |
| operation_kind | 'sales_reply' ou 'recontact_plan'; não aceitar ação administrativa/MCP por essa porta |
| concessionaria_id, canal_id, conversa_id, ciclo_id | Referências internas autorizadas, escopo único por concessionária |
| state_version e handoff_guard | Snapshot versionado do estado; revalidar na S0 ao aplicar resultado; snapshot não concede autorização permanente |
| authorized_context_ref / context_version | Referência a contexto MÍNIMO da mesma concessionária, fornecido pelo backend; não autoriza buscar outros clientes |
| knowledge_policy_version / prompt_policy_version | Versões de conhecimento e instruções aprovadas pelo gestor responsável da configuração |
| provider_policy_ref | Política técnica escolhida por humanos para modelo, limites de tokens, timeout e orçamento |
| request_deadline | Limite de tempo definido pela execução que usa o contrato |

**Cuidado:** este envelope NÃO é API existente. Os campos, nomes e formato físico aguardam conciliação S0 [R]. Não incluir chave secreta nem credentials Meta, JWT de usuário, SQL, prompt administrativo, CPF/telefone completos ou histórico de outra loja.

A fronteira de autenticação entre backend e adaptador continua por definir [R]; a identificação de loja e permissões não será aceita de mensagem do modelo ou de parâmetro externo não verificado.

## 4. Contrato candidato de saída OpenAI → S0 [P]

O adaptador retorna **proposta sem efeito colateral**, com contract_version, request_id, provider_trace_ref sanitizado, operation_kind, model_ref/version, prompt_policy_version, context_version, completion_kind e usage_metrics não sensíveis:

- sales_reply: 'proposed_text' minimizado **ou** 'request_human_review' com reason_code. Não publica no WhatsApp; S0 valida estado, segurança, políticas e cria intenção C03 autorizada na outbox que já pertence ao núcleo.
- recontact_plan: opções estruturadas de template_id + template_version + janela/intervalo sugeridos **somente entre candidatos previamente elegíveis fornecidos pela S0**. Não cria template, não agenda/enfileira diretamente, não abre novo status comercial.
- error: código seguro e categoria (AUTH_PROVIDER, RATE_LIMIT, QUOTA_OR_BILLING, TIMEOUT_UNKNOWN, TEMPORARY_PROVIDER_FAILURE, INVALID_PROVIDER_RESPONSE, POLICY_DENIED), sem expor token, payload sensível ou texto bruto.
- usage_metrics: contagens retornadas pelo provedor, quando disponíveis, para observabilidade e controle de custos; nunca inferir cobrança a partir do texto.
- Não há opção 'mark_sold', 'bank_approved', 'set_lost', 'handoff_override', 'send_graph', 'db_mutation' ou alteração arbitrária de parâmetros.

O backend S0, como única autoridade do ciclo, deverá revalidar versão, caso, loja, handoff, elegibilidade e permissão da ação antes de persistir. Resposta tardia/desatualizada deve ser descartada com motivo e evidência técnica segura.

## 5. Conectividade OpenAI e transporte [P/V/R]

- **API preferida para avaliação:** Responses API, conforme documentação oficial vigente; seleção definitiva de endpoint/modelo, SDK, formato de saída, retenção, recursos e configurações NÃO aprovada [R].
- **Topologia ainda não escolhida [R]:** A) backend autorizado/Edge Function Supabase → HTTPS → OpenAI; B) backend autorizado → n8n → OpenAI, com retorno ao núcleo. Não existe prova de integração desta frente nem decisão de contratar n8n. Em qualquer rota, a entrada do adaptador permanece estritamente server-to-server, autenticada e com autorizações aplicadas pelo núcleo.
- **Credential placement depende do caminho [R]:** referência lógica 'OPENAI_API_KEY' [P]; o responsável realizará o cadastramento MANUAL da chave no destino aprovado. Se for Edge Functions, secret do projeto Supabase correto; se for n8n, será preciso definir e aprovar armazenamento próprio de credencial n8n ou outro mecanismo seguro, sem supor que um segredo Supabase seja automaticamente acessível ao n8n. Nunca gravar a chave no repositório/chat/frontend.
- A existência de suporte oficial Supabase → OpenAI e n8n → OpenAI prova viabilidade documental, **não** prova integração real, idempotência, latência, observabilidade ou adequação à Prumo. Comparar caminhos segundo `avaliacao-transporte-openai-direto-ou-n8n-v0_1.md`.
- A frente OpenAI pode redigir exemplo de adaptador e mocks futuramente. Não implantar função nem chamar serviço real antes de autorização explícita, decisão de gasto e conformidade externa.
- Segregar credenciais e recursos de OpenAI dos segredos HMAC internos S0 e App Secret/Graph Token Meta. No caminho n8n, limitar histórico/payload de execuções, administração da instância, exposição dos segredos e permissões de workflows; nas duas rotas, somente S0 efetiva comandos comerciais.
- Projeto de API OpenAI, chave, modelo habilitado, billing, limites e autorização de tratamento de dados devem ser verificados por responsável [R/V]. A assinatura ChatGPT não equivale ao faturamento da API.

## 6. Falhas, privacidade e segurança [D/P/R]

1. **Deny by default:** nenhum contexto sem escopo e finalidade autorizados; isolar concessionárias mesmo se o telefone for igual; proteger anexos, texto de clientes e instruções de terceiros contra prompt injection e vazamento.
2. **Saída não executável:** texto do modelo não é instrução para SQL, CRM, Meta, Banco ou MCP. Nenhuma chamada de ferramenta que modifique domínio nesta v0.1.
3. **Timeout e retry:** registrar incerteza técnica da chamada OpenAI sem autorizar mensagens Meta duplicadas; idempotência da intenção comercial é responsabilidade S0. Política de novas tentativas/custos [R].
4. **Handoff:** revalidar trava do ciclo antes da entrada no adaptador e antes de publicar; resposta OpenAI já produzida não supera uma transferência humana posterior.
5. **Auditoria:** guardar IDs opacos, versão, decisão e métricas autorizadas; não registrar chaves, prompt bruto contendo PII, conteúdo integral ou segredos em logs. Retenção e papéis de controladoria/subprocessamento exigem validação [V/R].
6. **Limites comerciais:** IA não presume venda, recusa bancária, confirmação de envio, leitura WhatsApp, preço ou condição não validada. Recusa definitiva após remessa é decisão humana documentada (13A/21). Pós-venda e pós-remessa são tratados por humanos conforme normas.
7. **Sem autoconserto:** identificar erro não autoriza alterar regras/prompt/infraestrutura autonomamente nem suspender globalmente a operação.

## 7. Gates e aceite [P]

- G0 documental: aprovar divisão de responsabilidade e versão candidata por revisão S0/Meta sem interromper PRs #1/#2.
- G1 credencial humana: responsável decide organização/projeto OpenAI, cria chave apropriada, limita permissão/gasto e providencia seu armazenamento MANUAL no mecanismo secreto do caminho aprovado; se escolhido Supabase Edge Functions, usar Edge Function Secrets do projeto Prumo verificado. Comprovar SOMENTE metadados e presença do nome, nunca valor. **Não presumir que o segredo Supabase, sozinho, atende ao caminho n8n.**
- G2 técnica offline: fixtures sintéticas para request/response, incompatibilidade de versão, isolamento A/B, injeção, timeout, 401/429, JSON inválido, custo, stale version e handoff; sem custos. Preparar os mesmos cenários para A (direto) e B (n8n) sem reescrever regras S0/Meta.
- G3 laboratório isolado: primeira chamada real apenas com aprovação explícita de custos e dados 100% sintéticos, sem banco comercial nem Meta. Comparar, quando autorizado, sucesso, resposta tardia, latência, falhas, rastreabilidade, manutenção e custo de ambos os caminhos; não contratar n8n antes de demonstrar necessidade.
- G4 integração futura: revisão cruzada da autenticação S0, auditoria, contratos, consentimentos/transferência e operações; decisão explícita da topologia mediante evidências; autorização separada antes de implantação, dados pessoais ou produção.

**Situação ao criar v0.1:** apenas G0 proposto, NÃO aprovado; G1–G4 NÃO executados. Nenhum incremento no percentual de planejamento sem evidência conforme doc 19.

## Referências e prevalência

Normas do pacote auditado: 00A, 06, 13A, 21, 22, 23, 26, 33, 38, 40, 41. Estado do repositório: PR #1 e PR #2 Draft, consultados em 18/10/2026; interface S0/Meta v0.1 e WA-05C ainda propostas.
OpenAI API: https://developers.openai.com/api/reference/overview
Projetos/chaves: https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform
Segredos Supabase: https://supabase.com/docs/guides/functions/secrets
Edge Functions e chamadas a LLMs: https://supabase.com/docs/guides/functions
Responses API: https://developers.openai.com/api/reference/resources/responses/methods/create
Integração n8n OpenAI: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-langchain.openai
