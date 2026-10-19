# OAI-01 — Contrato candidato S0 ↔ OpenAI | v0.1

**Data:** 18/10/2026 | **Estado:** [P] proposta para revisão cruzada, [R] escolhas e autorizações pendentes, [V] condições externas a validar.
**Aplicação:** terceira frente independente, sem modificar escopo, backlog, código, PRs ou ritmo das frentes S0 e WhatsApp/Meta.
**Natureza:** desenho de interfaces, NÃO endpoint criado, schema aprovado, API conectada, prova de autenticação, autorização de dados reais ou liberação comercial.

**Exceção expressa de 19/10/2026 [D-escopo]:** o responsável autorizou **ajustes específicos na S0 que estejam bloqueando OpenAI**, também outorgando direito equivalente à frente WhatsApp/Meta no seu domínio. Isso NÃO transfere propriedade global da S0, não autoriza alterar arbitrariamente RLS/status/banco, nem torna a assinatura candidata automaticamente aprovada. Para evitar colisão, as propostas CFI-01 e C09 da frente OpenAI foram isoladas em [PR #8 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/8), base S0, sem editar PR #1/#2 ou os contratos físicos Meta. A tabela abaixo continua como limite padrão, **ressalvada intervenção limitada e explicitamente autorizada em branch própria com revisão cruzada**.

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
- **Extrator de cadastro pós-atendimento humano [nova orientação funcional, interface P/R]:** analisa somente snapshot autorizado da conversa humana ENCERRADA para produzir campos propostos com fontes e lacunas; cadastro deve ser preenchido automaticamente pelo backend quando validável, sem digitação rotineira do operador. Não conversa com o cliente, não reabre IA Vendedora e não executa gravação direta. Documento OAI-05.
- **Voz/áudio [requisito funcional, desenho P/R/V]:** transcrever áudios autorizados do cliente e converter resposta textual aprovada em mensagem de áudio da IA, respeitando handoff e entrega exclusivamente pela fronteira Meta. Documento OAI-06.
- **Handoff definitivo:** após transição para atendimento humano ou cadastro enviado ao operador, IA Vendedora não retoma naquele caso. Revalidar antes da chamada e novamente antes de qualquer publicação. Falhas técnicas não suspendem globalmente handoffs nem reparam software automaticamente.
- **IA Analista autônoma: fora do escopo [D].** Não adicionar testes, capacidade latente, módulo opcional ou treino autônomo de regras para isso.
- **MCP:** não é caminho para contornar as regras acima; escritas exigem autenticação, escopo e segunda confirmação inequívoca do responsável.

## 3. Contrato candidato de entrada S0 → adaptador OpenAI [P]

A S0 seria responsável por gerar envelope privado com, no mínimo:

| Campo candidato | Origem e exigência |
|---|---|
| contract_version | Valor candidato 's0-openai.v0.1-proposed'; rejeitar versões incompatíveis |
| request_id / correlation_id | IDs opacos gerados no backend, não telefone/CPF |
| operation_kind | 'sales_reply', 'recontact_plan', 'human_close_extract', 'speech_transcribe' ou 'speech_synthesize' [P]; nunca ação administrativa/MCP, SQL ou comando bancário |
| concessionaria_id, canal_id, conversa_id, ciclo_id | Referências internas autorizadas, escopo único por concessionária |
| state_version e handoff_guard | Snapshot versionado do estado; revalidar na S0 ao aplicar resultado; snapshot não concede autorização permanente. Para 'human_close_extract', handoff humano É pré-condição, mas resposta da IA Vendedora continua proibida; o extrator não envia mensagens |
| authorized_context_ref / context_version | Referência a contexto MÍNIMO da mesma concessionária, fornecido pelo backend; não autoriza buscar outros clientes. Para extração, S0 fornece fechamento, snapshot/hash/watermark, ficha e catálogo versionados; para voz, mídia/texto aprovado por referência autorizada |
| knowledge_policy_version / prompt_policy_version | Versões de conhecimento e instruções aprovadas pelo gestor responsável da configuração |
| provider_policy_ref | Política técnica escolhida por humanos para modelo, limites de tokens, timeout e orçamento |
| request_deadline | Limite de tempo definido pela execução que usa o contrato |

**Cuidado:** este envelope NÃO é API existente. Os campos, nomes e formato físico aguardam conciliação S0 [R]. Não incluir chave secreta nem credentials Meta, JWT de usuário, SQL, prompt administrativo, CPF/telefone completos ou histórico de outra loja.

A fronteira de autenticação entre backend e adaptador continua por definir [R]; a identificação de loja e permissões não será aceita de mensagem do modelo ou de parâmetro externo não verificado.

## 4. Contrato candidato de saída OpenAI → S0 [P]

O adaptador retorna **proposta sem efeito colateral**, com contract_version, request_id, provider_trace_ref sanitizado, operation_kind, model_ref/version, prompt_policy_version, context_version, completion_kind e usage_metrics não sensíveis:

- sales_reply: 'proposed_text' minimizado **ou** 'request_human_review' com reason_code. Não publica no WhatsApp; S0 valida estado, segurança, políticas e cria intenção C03 autorizada na outbox que já pertence ao núcleo.
- recontact_plan: opções estruturadas de template_id + template_version + janela/intervalo sugeridos **somente entre candidatos previamente elegíveis fornecidos pela S0**. Não cria template, não agenda/enfileira diretamente, não abre novo status comercial.
- human_close_extract (OAI-05): proposta estruturada de campos declarados após encerramento humano, cada um com field_code do catálogo autorizado, fonte em mensagens/transcrições, sinalização de ausências/contradições e versão do snapshot. S0 valida e aplica AUTOMATICAMENTE apenas campos elegíveis e fundamentados em nova versão auditada, sem fazer operador digitar rotineiramente; poder excepcional de corrigir continua. Não autoriza transição comercial, retomada IA Vendedora nem remessa ao banco.
- speech_transcribe (OAI-06): texto/transcrição propostos a partir de áudio temporário autorizado, com fonte, metadados seguros e indicadores de incerteza; não afirma conteúdo incompreensível.
- speech_synthesize (OAI-06): áudio temporário ou referência segura derivada do TEXTO EXATO já aprovado pela S0. Não envia WhatsApp; S0 entrega intenção à frente Meta apenas após revalidar permissão, handoff e outbox.
- error: código seguro e categoria (AUTH_PROVIDER, RATE_LIMIT, QUOTA_OR_BILLING, TIMEOUT_UNKNOWN, TEMPORARY_PROVIDER_FAILURE, INVALID_PROVIDER_RESPONSE, POLICY_DENIED), sem expor token, payload sensível ou texto bruto.
- usage_metrics: contagens retornadas pelo provedor, quando disponíveis, para observabilidade e controle de custos; nunca inferir cobrança a partir do texto.
- Não há opção 'mark_sold', 'bank_approved', 'set_lost', 'handoff_override', 'send_graph', 'db_mutation' ou alteração arbitrária de parâmetros.

O backend S0, como única autoridade do ciclo, deverá revalidar versão, caso, loja, handoff, elegibilidade e permissão da ação antes de persistir. **Guardas SEPARADAS CF-OP-02:** `sales_reply` e `speech_synthesize` COMO FALA DA IA VENDEDORA exigem posse IA vigente e são bloqueados definitivamente após handoff; `human_close_extract` é tarefa INTERNA silenciosa permitida após fechamento humano autenticado; `recontact_plan` também é tarefa INTERNA silenciosa e pode ser pedida pelo S0 para caso humano elegível (novo plano pós-humano), mas NUNCA reativa plano antigo nem fala com cliente. S0 decide plano, templates, destinatário, status e eventual envio Meta. Resposta tardia/desatualizada deve ser descartada com motivo e evidência técnica segura.

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

## 6A. Adendo CF-OP-02 / OAI-08, em revisão [P/R]

A F03 agora pode **sugerir necessidade de recontato pós-humano** e compromisso futuro com evidência (OAI-08), sem acionar F02 automaticamente. S0 valida eventual pedido `recontact_plan`; F02 devolve somente templates/versões autorizados, limite de tentativas e final separado, nunca agenda persistida nem texto novo. Pedido de template único pelo operador segue S0→Meta, sem F02. A resposta a uma cadeia após handoff volta ao operador Prumo ATUAL autorizado, não à IA Vendedora. Handoff cancela plano anterior incompatível; plano pós-humano tem novo propósito e ID.

**C09:** somente o S0 poderá futuramente marcar `perdido` por silêncio +24h depois de template final comprovadamente ENVIADO, em ciclo pré-banco elegível após matriz de estados homologada [R]. Janela Meta +24h desde último inbound e clique de conclusão humana são eventos distintos; nenhum desses dois relógios dispara `perdido`. Em `cadastro enviado ao banco`/ `vendido` não se aplica silêncio C09. O catálogo de campos, modelo, autenticação física e `cadastro enviado ao operador` ainda [R/V].

**Assinatura F03:** as nomenclaturas divergentes E01/OAI-05 são mapeadas no [CFI-01](CFI_01_PROPOSTA_CONCILIACAO_ENVELOPE_F03_v0_1.md). O mapeamento é candidato até aceite S0/OpenAI na issue #4. Nenhum endpoint ou estado comercial é aprovado.

## 7. Gates e aceite [P]

- G0 documental: aprovar divisão de responsabilidade e versão candidata por revisão S0/Meta sem interromper PRs #1/#2.
- G1 credencial humana: responsável decide organização/projeto OpenAI, cria chave apropriada, limita permissão/gasto e providencia seu armazenamento MANUAL no mecanismo secreto do caminho aprovado; se escolhido Supabase Edge Functions, usar Edge Function Secrets do projeto Prumo verificado. Comprovar SOMENTE metadados e presença do nome, nunca valor. **Não presumir que o segredo Supabase, sozinho, atende ao caminho n8n.**
- G2 técnica offline: fixtures sintéticas para request/response, incompatibilidade de versão, isolamento A/B, injeção, timeout, 401/429, JSON inválido, custo, stale version e handoff; sem custos. Acrescentar extração automática pós-humano com fontes, lacunas, versões e regressão de guardas distintas, mais STT/TTS e validação de texto/áudio. Preparar os mesmos cenários para A (direto) e B (n8n) sem reescrever regras S0/Meta.
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
