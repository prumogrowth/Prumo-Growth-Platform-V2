# OAI-04 — Avaliação de transporte OpenAI: direto ou n8n | v0.1

**Data:** 18/10/2026. **Estado:** [R] seleção de arquitetura NÃO decidida; [P] desenho de comparação; [V] suporte documental oficial confirmado, SEM teste de integração real da Prumo.

## 1. Decisão em aberto, sem extrapolar a frente WhatsApp

A arquitetura vigente do projeto tem Supabase/PostgreSQL como núcleo comercial e fronteira de confiança (docs 04, 11, 42, 43). O n8n **não é dependência obrigatória do S0** e sua contratação foi postergada até evidência de necessidade (docs 42/43). A frente Meta documentou direção de integração direta Meta → Supabase, mas isso não prova adequação da rota direta OpenAI.

**Não há teste, prova de autenticação, Edge Function OpenAI, workflow n8n da Prumo, credencial operacional, chamada HTTP real nem métrica comparativa desta frente.** Portanto, nenhuma rota foi validada como desenho final da integração OpenAI.

O contrato OAI-01 é **independente do transporte**: o núcleo S0 autoriza escopo e ações; a frente OpenAI normaliza pedidos/resultados do provedor; a frente Meta permanece responsável por transporte WhatsApp. A camada de transporte é substituível sem alterar estados, regras, guarda comercial, idempotência ou responsabilidades originais.

## 2. Alternativas candidatas

| Aspecto | A — Direto (candidato) | B — n8n (candidato) |
|---|---|---|
| Caminho lógico | S0 autenticado → adaptador servidor/Edge Function → API OpenAI → resultado ao S0 | S0 autenticado → porta autenticada n8n → nó/OpenAI API → resultado ao S0 |
| Viabilidade documental | Supabase Edge Functions documenta chamadas a APIs externas e workloads LLM; OpenAI documenta POST /v1/responses com Bearer key | n8n disponibiliza nó OpenAI com suporte a Responses API e credentials API key |
| Secret | Responsável salva manualmente chave no secret do runtime escolhido, por exemplo Edge Function Secrets do Supabase Prumo | Responsável deve autorizar e configurar manualmente credencial no secret/credential store n8n (ou outro cofre aprovado); o secret Supabase sozinho não basta |
| Dependências | Runtime servidor, autenticação, política de timeout/retry e observabilidade; sem orquestrador adicional | Instância n8n, credenciais, isolamento, manutenção, versionamento de workflows, logs e possível custo operacional adicional |
| Domínio comercial | Continua S0; nunca alterar estado, enviar WhatsApp ou acessar outro tenant por chamada de modelo | Continua S0; n8n nunca vira fonte de verdade, não grava estado comercial sem autorização S0 |
| Meta | Integração Meta continua sob PR #2 | Integração Meta continua sob PR #2 |
| Evidência atual | **Viabilidade pela documentação, nenhum teste Prumo** | **Viabilidade pela documentação, nenhum teste Prumo** |

**Nota:** não há Firebase nesta arquitetura documentada. O runtime candidato é Supabase/backend, não Firebase. Não introduzir uma nova plataforma para resolver apenas essa escolha.

## 3. Critérios objetivos — a medir antes de selecionar [P/R]

Em laboratório exclusivamente sintético, usar **exatamente os mesmos contratos, prompts, tamanhos de payload e cenários de falha**. Registrar diferenças com evidência por commit/versão, sem dados de clientes:

1. **Segurança:** credencial protegida, autenticação S0 → adaptador, escopo loja/caso, segregação de contexto, exposição de payload em logs, isolamento de administração e capacidade de revogar acesso.
2. **Integridade:** revalidação do estado/handoff após resposta, proteção contra stale version, tratamento de resultados duplicados, efeito zero para comandos de modelo não autorizados.
3. **Confiabilidade:** comportamento em indisponibilidade, timeout, 401/429, cota, latência externa, retomada e duplicidades; nenhum envio Meta como efeito da tentativa ao provedor.
4. **Observabilidade:** request/correlation IDs sanitizados, latência por trecho, métricas técnicas, custos estimados e trilha da decisão S0.
5. **Complexidade:** esforço de desenvolvimento, manutenção, versionamento, CI, políticas de acesso, upgrades e recuperação do próprio orquestrador.
6. **Custos:** número de componentes pagos, armazenamento/logs, execução n8n, chamadas OpenAI, overhead de cada rota; valores e limites reais precisam ser levantados na data da decisão.
7. **Compatibilidade:** chamadas e respostas estruturadas/validadas com versão, runtime, modalidade desejada e testes suportados sem alterar os outros PRs.

**Thresholds:** ainda NÃO definidos; estabelecer antes do benchmark para evitar decisão retrospectiva baseada em impressão. Não alegar que direto é mais rápido/barato/seguro sem medir, nem assumir que n8n resolve sozinho fila, retries, privacidade ou idempotência.

## 4. Sequência segura de validação [P]

- **V0 — Documental [V documental]:** confirmar suporte de fornecedor em fontes oficiais e produzir hipóteses. Este marco NÃO valida a integração.
- **V1 — Contrato offline [R]:** montar fixtures sem rede simulando porta direta e porta n8n; validar as mesmas 15+ propriedades contratuais. Nenhum consumo OpenAI.
- **V2 — Laboratório direto [R]:** somente após chave manual, escopo autorizado, custo aprovado e ambiente correto verificado; chamar Responses API com dados sintéticos e registrar métricas, erros e gastos.
- **V3 — Laboratório n8n [R]:** somente se V1/V2 ou requisitos de automação justificarem; aprovação de custo/infraestrutura e credencial n8n separadas. Se n8n não for necessário, explicar em parecer técnico por que não houve V3.
- **V4 — Escolha expressa [R]:** comparar evidências; responsável aprova A/B ou mantém pendente. Sem alterar PR #1/#2, sem merge/deploy por consequência automática.

A primeira chamada real à OpenAI não autoriza ativação comercial, uso de dados pessoais, envio Meta ou planejamento automático de recontatos.

## 5. Referências

**Internas:** pacote auditado em 17/10/2026 — docs 04, 11, 42, 43; PR #1 (núcleo S0) e PR #2 (Meta), ambos mantidos independentes.
**Externas (consulta documental em 18/10/2026):**
- OpenAI Responses API: https://developers.openai.com/api/reference/resources/responses/methods/create
- Supabase Edge Functions, integração LLMs: https://supabase.com/docs/guides/functions
- Supabase Edge Function Secrets: https://supabase.com/docs/guides/functions/secrets
- n8n OpenAI node: https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-langchain.openai
- n8n OpenAI credentials: https://docs.n8n.io/integrations/builtin/credentials/openai

**Veredito:** GO apenas para especificação e testes offline futuros quando autorizados; NO-GO para declarar qualquer topologia escolhida sem critérios/provas.
