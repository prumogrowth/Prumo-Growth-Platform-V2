# E03 — Projeto API, credencial e gates para laboratório | v0.1

> **Sequência atualizada por autorização humana de 22/10/2026:** E04 **offline** foi expressamente liberada e [o laboratório inicial foi publicado](./e04_offline_lab/README.md). Este novo aceite **não inicia E03-A..H**, que continuam adiadas até decisão manual de projeto API/billing/segredos **antes de E05**, nem autoriza qualquer consumo real.

> **Complemento documental de 22/10/2026:** [E03-PRE v0.2 — retenção, custos, caching, orçamento e preparação SEM chave](./E03_PRONTIDAO_PRE_OPERACIONAL_SEM_CREDENCIAIS_v0_2.md). **E03-A..H continuam ADIADAS**, sem projeto, billing, key ou secret criados nesta frente. Alerta mensal de orçamento do projeto API é flexível; não tomar notificação como corte financeiro garantido. Sem teste ou consumo.

**Data:** 18/10/2026; **decisão de sequenciamento em 19/10/2026 [D-tempo]** | **Estado:** checklist [P] preservado, execução manual E03 **deliberadamente adiada** até estrutura/testes offline autorizados estarem preparados para ensaios E05; [R] runtime/ação humana; [V] projeto/conta. **E03 NÃO CONCLUÍDO.** Nenhuma credencial, conta, cobrança, secret, API call ou ambiente foram criados/modificados por esta frente.

## Objetivo e distinção de ambientes

Preparar acesso da Prumo Growth à **API OpenAI**, exclusivamente para futuros testes controlados com dados fictícios. O projeto técnico Supabase **Prumo Growth - Platform** já foi identificado com ref **projeto-supabase-omitido**. Isso NÃO demonstra projeto OpenAI criado, nem cobrança habilitada. O GitHub PR #3 não deve receber credenciais. A emissão e cadastro da chave OpenAI permanecem ações **MANUAIS pelo responsável**, conforme OAI-02.

## E03 — Lista de tarefas e aceites

**Orientação operacional vigente [D-tempo]:** não iniciar agora nenhum item E03-A a E03-H nem pedir ao responsável chave, conta, faturamento ou cartão. A sequência é: consolidar contratos/estrutura → obter liberação própria de implementação e concluir testes OFFLINE conforme E04 → **só então** fazer checklist manual E03 antes de E05 (chamada real), com nova autorização expressa e sem compartilhar segredo. A documentação E03 fica disponível como preparação, não como exigência imediata.

| Etapa | Nosso trabalho | Evidência segura (sem credenciais) | Estado |
|---|---|---|---|
| E03-A | O responsável abre https://platform.openai.com, confere organização correta e acesso | Organização/projeto validados, sem segredos | PENDENTE |
| E03-B | Criar ou selecionar projeto dedicado da **API** à Prumo Growth, distinto do projeto Supabase | Nome/ID NÃO secreto confirmado | PENDENTE |
| E03-C | Conferir Billing/Usage da API (separado da assinatura ChatGPT), créditos, modelo de cobrança e quem é dono financeiro | “Billing revisto: sim/não”; nenhum cartão, nota ou chave no chat | PENDENTE |
| E03-D | Conferir Limits, modelos disponíveis, rate limits, spending controls, alertas e destinatários | Configurações não sensíveis e comportamento do controle de gastos confirmados | PENDENTE |
| E03-E | Escolher service account dedicada ao projeto (se permissões permitirem) ou chave de projeto com privilégios mínimos | Tipo, restrições e responsável anotados SEM valor da chave | PENDENTE |
| E03-F | Responsável cria e salva **manualmente** a chave OpenAI em cofre seguro; verificar permissões | Apenas “credencial criada e guardada: sim/não” | PENDENTE |
| E03-G | Decidir onde a chave será registrada no runtime aprovado; só então o responsável a insere manualmente | Confirmação de presença do secret SEM valor ou pedaços | [R] topologia ainda não decidida |
| E03-H | Registrar política de rotação e revogação de segredo, quem pode agir em incidentes | Processo e dono aprovados | PENDENTE |

**E03 termina** somente com evidência de E03-A a E03-H, sem chave exposta. **Primeira API call real é E05, não parte da comprovação do E03**; exige autorização específica de lote de consumo, dados 100% fictícios e controles de segurança. Não marcar E03 concluído somente por publicar esta lista.

## Orientações manuais

1. No painel OpenAI, selecionar organização e projeto de API corretos; criar projeto exclusivo da Prumo se ele não existir. Somente perfis autorizados podem criar projetos.
2. Nas configurações do projeto, conferir Members/Service accounts ou API Keys. A chave de conta de serviço é mostrada no ato da criação e não pode ser relida posteriormente; alterar permissões se vier com acesso amplo. Chaves do projeto podem ter permissões Restricted conforme os endpoints escolhidos.
3. Verificar em Limits e Billing/Usage tanto o escopo dos modelos quanto o consumo. **Atenção:** páginas da documentação sobre “budget” descrevem alertas que não param chamadas; documentação atual também descreve limites rígidos de gasto configuráveis em determinadas contas. Conferir o comportamento concreto da conta, não inferir que um alerta corta gastos. Limites rígidos também podem ter pequeno atraso na contabilização.
4. Guardar a chave fora de chat, issue, repositório, navegador público, logs, planilha e frontend. Se o executor vier a ser uma **Edge Function no Supabase Prumo**, destino candidato é **Edge Function Secrets**, com cadastro MANUAL do responsável; se for **n8n**, a credencial fica no gestor de credenciais do n8n; se runtime independente, no cofre apropriado. **NÃO escolher runtime por ter o Supabase conectado e NÃO instalar secret de antemão.**
5. Para prestação de contas, registrar somente projeto, status de billing, responsável, permissões gerais, data e presença do segredo; jamais pedir ou copiar API key.

## Orçamento por rodada, sem teto global arbitrário

O responsável declarou que aceita custo proporcional à utilidade, mas quer avaliar se a rodada será cara. Assim, cada lote futuro deve ser aprovado separadamente com finalidade, modelo/versão disponibilizado de fato no projeto, volume máximo de chamadas, tokens/segundos estimados, retries, preço vigente, custo total projetado, margem de variação e possibilidade de interromper. O módulo de execução deverá limitar quantidade de operações e consumo independentemente de alertas do painel. **Sem aceite expresso de um lote, nenhum gasto está autorizado.**

## Preparação paralela E04 — ainda sem implementar

Enquanto E03 aguarda a criação manual da chave, é possível revisar offline as **descrições de cenários** sintéticos propostas em E02 (32 SYN e 17 NC do OAI-07), ainda sem fixtures executáveis, além de elaborar o validador stub com campo de origem, tratamento de ausência, conflito, idempotência, versionamento e handoff. **Execução/implementação só após delimitação e aceite do gate E04/E02; esta publicação não configura testes executados.**

## Dependências inalteradas

S0 / PR #1 decide eventos de encerramento humano, campos essenciais para remessa, autorização/validação, fila e estado do domínio, inclusive transição para “cadastro enviado ao operador” após fechamento humano [R]. Meta / PR #2 mantém a titularidade do WhatsApp, áudio e envio. Banco/LGPD permanecem validações externas [V] para dados reais. Venda bancária somente com confirmação e marcação manual autorizada; saída de IA não marca vendido. n8n vs rota direta permanece [R]. Nenhum merge, chamada paga, migração, deploy ou modificação S0/Meta está autorizado pelo checklist.

## Fontes oficiais verificadas em 18/10/2026

- API Projects e service accounts: https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform
- Permissões de chaves: https://help.openai.com/en/articles/8867743-assign-api-key-permissions
- Erros/controles de gastos: https://help.openai.com/en/articles/6614457-troubleshooting-api-usage-and-spend-limits
- OpenAI Data Controls: https://developers.openai.com/api/docs/guides/your-data
- Supabase secrets (somente para runtime aprovado): https://supabase.com/docs/guides/functions/secrets

**Conclusão:** E03 preparado documentalmente, não concluído. Evidências operacionais dependem do responsável. Nenhuma mudança no índice global de progresso.
