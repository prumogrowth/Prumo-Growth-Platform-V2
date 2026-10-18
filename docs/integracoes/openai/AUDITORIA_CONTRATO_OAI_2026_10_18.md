# Auditoria contratual OAI v0.1 — terceira frente OpenAI

**Data:** 18/10/2026. **Escopo:** documentos da branch feat/s2-openai-adapter-sintetico e descrição do PR #3; análise documental, não teste de código/infraestrutura.
**Precedência:** decisões normativas do pacote auditado de 17/10/2026 e contratos ainda Draft dos PRs #1/#2. [D] decisão, [P] proposta, [R] pendência, [V] validação.
**Princípio de preservação:** a auditoria muda SOMENTE a branch OpenAI e o texto do seu PR; nenhuma revisão/apropriação de backlog/código S0 ou Meta.

## 1. Achados e correções

| ID | Relevância | Achado da v0.1 anterior | Tratamento na branch OpenAI | Situação |
|---|---|---|---|---|
| AUD-OAI-01 | ALTA | A seção de conexão dava impressão de rota direta / Edge Functions como arquitetura implícita, sem avaliação comparativa do n8n | Contrato passa a permitir rota direta OU n8n e institui OAI-04 com critérios, gates e métricas | CORRIGIDO DOCUMENTALMENTE; decisão [R] |
| AUD-OAI-02 | ALTA | Restrições de ferramentas e acesso estavam descritas de modo universal, em vez de definir alvo e autorização por sessão/conta executora | Removidas proibições globais; operações dependem da verificação de projeto correto, permissões e autorização | CORRIGIDO no conteúdo vigente |
| AUD-OAI-03 | MÉDIA/ALTA | O armazenamento no Supabase fora apresentado como suficiente independentemente da topologia | Provisionamento agora é condicionado ao runtime escolhido; se n8n, requer cofre/credencial e governança próprios | CORRIGIDO DOCUMENTALMENTE; destino [R] |
| AUD-OAI-04 | MÉDIA | Não existia ensaio comparável das duas rotas | Inclusão de testes A/B de autenticação, latência, falha, custo, segurança, operação e handoff | ESPECIFICADO [P], não executado |
| AUD-OAI-05 | MÉDIA | Suporte documental de fornecedor poderia ser confundido com integração já comprovada | Viabilidade oficial expressa como hipótese técnica, sem credencial/chamada/benchmark | ESCLARECIDO |
| AUD-OAI-06 | BAIXA | Havia risco de confundir o backend contratado com outra plataforma | Terminologia padronizada: núcleo S0/Supabase; nenhuma dependência Firebase criada | ESCLARECIDO |
| AUD-OAI-07 | PENDÊNCIA | Ainda não há revisão de execução concorrente, log/retention efetiva, TLS/egresso, autenticador interno, orçamento e tratamento real de dados | Gates R/V e teste em laboratório sintético antes de consumo, sem presunção de prontidão | ABERTO [R/V] |

## 2. Integridade das responsabilidades

**S0 / PR #1:** permanece dono do domínio e fonte de verdade (dados, identidade, autorização, RLS, oito estados, contexto permitido, handoff, planos e intents). Qualquer adaptação física, na ocasião própria, é revisada e implementada pela S0, sem apropriação pela OAI.

**Meta / PR #2:** permanece dona de protocolo Meta, credenciais Meta, Graph, status de entrega, transporte/recibo e requisitos de integração com S0. Nenhum adaptador OpenAI envia mensagens diretamente ao WhatsApp.

**OpenAI / PR #3:** documenta acesso ao serviço, normalização de pedidos e resultados, avaliação das alternativas de transporte, falhas técnicas e evidências. A escolha entre chamada direta e n8n está **ABERTA**, e o n8n não será contratado por presunção.

**Responsável:** mantém o controle da emissão e cadastramento MANUAL da chave OpenAI e das decisões sobre custos, liberação e operação. Outros trabalhos autorizados no projeto correto podem ser executados por usuários com suas permissões legítimas; esta documentação não impede o desenvolvimento das demais frentes.

## 3. Limites preservados

1. IA Vendedora e Planejadora sob normas vigentes; IA Analista autônoma EXCLUÍDA.
2. Oito estados comerciais; nenhuma alteração por saída do modelo ou por status técnico Meta.
3. Isolamento de contexto por concessionária, mesmo telefone em múltiplas lojas.
4. Handoff humano definitivo naquele caso, inclusive quando resposta OpenAI chega atrasada.
5. n8n, quando escolhido, pode orquestrar, **nunca** substituir a fonte de verdade S0.
6. Chave não fica em GitHub/frontend/logs/chat e não será exposta ao modelo.
7. PR #3 continua Draft; sem produção, Supabase remoto alterado, integração OpenAI real ou merge autorizados nesta auditoria.

## 4. Veredito e próximos gates

**GO DOCUMENTAL CONDICIONAL:** estrutura contratual revista e coerente com preservar as outras frentes. Pode seguir com plano de testes offline e preparação administrativa de credencial quando o responsável desejar.

**NO-GO:** afirmar topologia OpenAI pronta, contratar n8n, ativar API paga sem aprovação, migrar S0, implantar serviço, processar clientes reais ou alterar atividades de PR #1/#2.

**Pendências:** [R] topologia e thresholds de comparação; [R] modelo, custos, projeto OpenAI e local final de segredo; [V] 15 cenários e testes comparativos; [R/V] revisão cruzada de porta com S0, privacidade, gastos, autenticação e retenção. **Não houve teste OpenAI, nem inspeção de runtime nem execução Supabase nesta auditoria.**

**Controle de progresso:** nenhum ponto novo concedido ao planejamento por este ato; os critérios de evidência pertencem ao documento 19 e evoluções válidas.

## 5. Fontes

Documentos locais do pacote auditado: 04, 06, 11, 13A, 19, 26, 33, 38, 42, 43; documentos do PR #1 e PR #2 lidos em 18/10/2026.
OpenAI Responses API: https://developers.openai.com/api/reference/resources/responses/methods/create
Supabase Edge Functions: https://supabase.com/docs/guides/functions
n8n OpenAI node: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-langchain.openai
