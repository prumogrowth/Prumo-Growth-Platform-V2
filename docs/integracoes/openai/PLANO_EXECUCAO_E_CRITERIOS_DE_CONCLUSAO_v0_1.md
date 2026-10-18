# Plano de execução e critérios de conclusão — Frente OpenAI | v0.1

**Data:** 18/10/2026 | **Estado:** [P] roteiro de trabalho proposto, com gates [R/V], ainda não aprovado como decisão normativa geral.
**Local:** PR #3, branch `feat/s2-openai-adapter-sintetico`. **Origem:** OAI-01 a OAI-04 e auditoria de 18/10/2026, decisões normativas do pacote do projeto, sem reatribuir trabalhos S0/Meta.

## Missão, início e fim

**Missão:** entregar, em laboratório controlado, uma porta OpenAI funcional, segura e testável por contratos, capaz de receber apenas contexto autorizado e devolver propostas tipadas sem efeitos comerciais; avaliar a necessidade real do n8n versus comunicação direta; preparar entrega técnica à S0 sem interferir nas demais frentes.

**Início real (estado em 18/10/2026):** branch OpenAI criada, PR #3 Draft, contratos OAI-01 a OAI-04 candidatos, auditoria documental publicada; projeto Supabase exclusivo da Prumo identificado pelo conector autorizado como `Prumo Growth - Platform`, ref `projeto-supabase-omitido`, ACTIVE_HEALTHY. A existência do projeto não demonstra esquema comercial implantado. Ainda NÃO há chave OpenAI confirmada, chamada real, banco modificado, endpoint ou integração da OpenAI testada.

**Fim da frente OpenAI de laboratório:** critérios de aceite de E00–E08 atendidos e rastreados; rota A/B decidida expressamente com evidências; projeto/chave/segredo de execução corretamente preparados sem divulgação; adaptação OpenAI executando chamada controlada real com dados exclusivamente sintéticos, sob autorização de custo; saídas estruturadas, erros, versões, isolamento e handoff testados; contrato revisto com S0 e pacote de entrega assinado/registrado. Sem deploy comercial, envio Meta, clientes reais, migração S0 ou merge automático. **Fechamento da frente de laboratório NÃO equivale à entrada em produção.**

O laboratório pode avançar com stub/mock de S0 enquanto PR #1 evolui. O acoplamento real ao S0 e a ativação comercial são etapas posteriores, com a participação da frente proprietária. Se a revisão externa da interface ou autorização do teste real não ocorrer, manter marcos bloqueados; não declarar 100%.

## Funções e governança

- **Responsável humano:** autoriza custos e chamada real; cria/gerencia organização/projeto OpenAI, credencial e segredo **manualmente**; aprova escolha arquitetural e liberação final. Não compartilha valor de chave com o assistente ou GitHub.
- **Frente OpenAI:** especifica contratos, adapta protocolo do provedor, implementa mocks e código isolado quando autorizado, escreve testes, coleta métricas não sensíveis e redige parecer arquitetural; não assume mutações SQL S0 ou transporte Meta.
- **S0 / PR #1:** continua dono de domínio, contextos confiáveis, identificação, autorizações, estados, C03/C05/C10, outbox, versionamento comercial e handoff. A equipe S0 revisará a porta de integração, sem interromper seu trabalho.
- **Meta / PR #2:** continua dona de WhatsApp, Graph, webhooks, templates como canal/transporte, correlação e callbacks; só entra na revisão se a interface interferir em sua fronteira.
- **Supabase:** qualquer conta com acesso legítimo ao projeto Prumo pode realizar solicitações autorizadas conforme permissões específicas; nenhuma restrição universal de plugin ou de sessão deve constar na documentação normativa. O registro da chave OpenAI, entretanto, permanece MANUAL por decisão do responsável. Conferir organização e project-ref antes de cada operação.

## O roteiro fechado OAI-E00 a OAI-E08

| Marco | Trabalho conjunto | Condição verificável para dar como concluído | Situação inicial |
|---|---|---|---|
| **E00 — Base e isolamento** | Validar branch, PR, contratos, projeto Supabase correto e donos S0/Meta. | Evidências de branch/PR; documentação e projeto corretos confirmados, sem alteração S0/Meta. | **Concluído (preparação documental)** |
| **E01 — Contrato da porta** | Congelar proposta v0.x de entrada/saída: sales_reply C03, recontact_plan C05 se pertinente, contexto mínimo, versionamento, handoff, nenhum side effect; revisar com responsável S0. | Contrato versionado com campos, exemplos, rejeições e registro de revisão cruzada; divergências resolvidas ou explícitas. | **Pendente** |
| **E02 — Segurança, aceite e arquitetura experimental** | Definir política de dados, secrets, autenticação interna, tratamento de saída, logging/retention, orçamento e critérios objetivos A/B definidos ANTES dos testes. | Checklist, casos adversariais, fixtures sintéticas, thresholds e plano de custos aprovados. | **Pendente** |
| **E03 — Conta OpenAI e credencial humana** | Confirmar organização/projeto OpenAI, billing/limites, credencial de escopo mínimo e destino de secret compatível com runtime. | Responsável confirma criação, permissões, limite/gasto e armazenamento MANUAL do segredo na infraestrutura correta, sem revelar valor; autorização de testes é gate à parte. | **Pendente** |
| **E04 — Adaptador sintético offline** | Escrever módulo isolado de chamada/normalização, respostas estruturadas, timeout/retry/erros e stubs para S0, sem acessar OpenAI, Supabase hospedado ou Meta. | Suíte local executada com evidências: incompatibilidade, injeção, interloja, atrasos, 401/429, cotas, handoff, versões e propostas inválidas. | **Pendente** |
| **E05 — Prova direta controlada** | Com autorização expressa de custo e ambiente, fazer primeiro teste real da API pelo runtime servidor/Edge Function aprovado com conteúdo 100% fictício; verificar autenticação, resultado, falhas, observabilidade e custo. | Evidência sanitizada da chamada real bem-sucedida e de cenários de falha; nenhum envio WhatsApp, dado real ou modificação comercial. | **Pendente** |
| **E06 — Decisão direta × n8n** | Comparar resultados da rota direta com requisitos e thresholds prévios. Se houver ganho/requisito não atendido, autorizar e testar n8n em laboratório; caso contrário justificar tecnicamente por que dispensá-lo. | Parecer comparativo, evidências, escolha expressa pelo responsável e estratégia de secrets/infra. Não atribuir aprovação à frente Meta. | **Pendente** |
| **E07 — Simulação de ponta a ponta contratual** | Simular S0 autorizado → porta escolhida → OpenAI → proposta → validador S0 stub, com handoff durante execução, isolamento por concessionária e sem saída Meta; alinhar contrato com S0. | Fluxo sintético reproduzível, logs sanitizados e testes de não mutação/não duplicidade; dono S0 reconhece fronteira ou registra bloqueio. | **Pendente** |
| **E08 — Auditoria e entrega da frente** | Consolidar documentação, código, resultados, custos, decisão A/B, riscos, pendências e instruções de operação/rotação; submeter PR #3 para revisão, sem merge automático. | Checklist E00–E07 com evidência, avaliação de segurança/privacidade e parecer final; pendências de integração/produção explicitamente repassadas aos responsáveis. | **Pendente** |

**Sequência padrão:** E00 → E01 → E02 → E03 → E04 → E05 → E06 → E07 → E08. O desenvolvimento offline E04 pode ocorrer antes de E03 para não depender da chave. A integração real com a S0 nunca é pré-requisito para continuar os testes locais. Não marcar E05 concluído sem uma chamada real autorizada e verificada.

## Gates de autorização

- **G-CUSTO:** consulta/preparação de billing e segredos não é autorização para chamadas pagas. E05/E06 n8n com consumo real exigem decisão expressa de valor/limite, responsável e ambiente.
- **G-SEGREDO:** o usuário faz pessoalmente emissão e registro da chave; nome sugerido `OPENAI_API_KEY`. Se runtime Edge Functions, secret Supabase Prumo; para n8n, cofre apropriado e autorização separados. Um secret Supabase não é automaticamente visível no runtime n8n ou num backend Python externo.
- **G-PRIVACIDADE:** E05 em diante somente conteúdo fictício; dados reais/produção dependem de gate próprio e outras frentes.
- **G-DEPENDÊNCIA:** PRs #1 e #2 não são modificados por E00–E08. Requisitos conflitantes viram pedido de revisão ao dono original, nunca alteração unilateral.
- **G-CONTRATO:** alteração de enum, RLS, SQL, status comercial, handoff ou transporte Meta não faz parte da execução OAI.
- **G-N8N:** n8n não é requisito assumido; é opção experimental/arquitetural com justificativa e aprovação explícita.

## Evidências e acompanhamento

Acompanhamento na descrição do PR #3 e neste roteiro: **PENDENTE → EM EXECUÇÃO → VALIDADO COM EVIDÊNCIA** ou **BLOQUEADO**, com data, responsável, link de commit/teste, critérios e decisão.
A preparação documental E00 está validada. Os outros oito marcos não estão concluídos. **Não converter automaticamente essa contagem em percentual de planejamento global**: o controle auditado do projeto pertence ao documento 19. Qualquer barra local OAI deve registrar pesos/critérios próprios previamente acordados, sem contaminar indicadores da plataforma.

## Riscos e decisões que ainda precisam de aprovação

[R] Escolha de runtime/linguagem do adaptador, política de autenticação S0 ↔ adaptador, modelos e formato de saída, contrato versionado final, thresholds A/B, orçamento e tratamento/retenção de dados. [V] Primeira chamada real, verificação de segredo e acesso em runtime, fluxos de falha, ensaios comparativos e revisão de segurança. Nenhum desses itens é considerado resolvido apenas por documentação do fornecedor.

**O marco E08 encerra a frente OpenAI de laboratório; operações comerciais reais requerem integração posterior e liberação global da plataforma.**
