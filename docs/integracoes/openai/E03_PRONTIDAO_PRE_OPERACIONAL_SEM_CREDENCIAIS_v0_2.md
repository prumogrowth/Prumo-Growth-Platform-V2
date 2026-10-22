# E03-PRE v0.2 — Preparação sem conta/chave, retenção, orçamento e segurança da API

**Data:** 22/10/2026. **Tipo:** revisão documental de prontidão [P/R/V], **não execução operacional de E03-A..E03-H**. A orientação de 19/10 permanece: **não** abrir/criar projeto OpenAI, solicitar chave, fazer billing ou cadastrar secret antes do sequenciamento de E04 offline autorizado e do aceite específico para E05. Nenhum acesso à conta OpenAI da Prumo foi verificado nesta rodada. Não confundir conta ChatGPT, projeto Supabase e organização/projeto OpenAI API.

## 1. Registro do estado de E03-A..E03-H (não preencher como feito)

| Item da lista E03 v0.1 | Preparação de política possível agora | Evidência operacional necessária **depois**, por pessoa autorizada | Estado atual |
|---|---|---|---|
| A — organização | Definir verificação dupla de organização correta e papel de proprietário | Captura não sensível da organização e permissão | **ADIADO** |
| B — projeto API | Definir nome/isolamento do projeto API e governança | Projeto/ID efetivos confirmados na organização correta | **ADIADO** |
| C — billing | Preparar formulário de teto por rodada e dono financeiro | Billing e termos efetivos revisados sem expor cartão | **ADIADO** |
| D — limits/modelos | Definir comparação de modelos, rate limits, controle de gasto e alertas | Limites reais/roles/modelos habilitados registrados | **ADIADO** |
| E — service account/escopo | Estabelecer menor privilégio por tarefa e quem responde a incidente | Papel de acesso/chave de projeto efetivos, endpoint allowlist | **ADIADO** |
| F — emissão de chave | Plano para credencial única por runtime e rotação | Confirmação simples "secret presente"; NUNCA valor | **ADIADO** |
| G — instalação de secret | Decisão técnica de runtime aprovada **antes** de escolher cofre | Prova de secret instalado manualmente pelo responsável no runtime correto | **ADIADO [R]** |
| H — rotação/revogação | Definir responsáveis e teste de revogação sem segredo real em log | Procedimento formal e ensaio controlado | **ADIADO** |

**A revisão documental E03-PRE não altera o estado de nenhuma tarefa E03-A..H**. Abrir página de documentação pública ou consultar preço sem login tampouco equivale a criar projeto/chave.

## 2. Limites e gasto — atenção à distinção [V]

A documentação de gerenciamento de projetos da API explica que o **limite mensal de gastos do projeto é flexível**: ao ultrapassá-lo, as requisições podem continuar; alertas não constituem corte automático. Outra ajuda oficial descreve **limites rígidos** que podem bloquear tráfego conforme elegibilidade/configuração, mas que têm latência de aplicação e podem ser ultrapassados marginalmente. **Não assumir que ambos estão disponíveis com o mesmo efeito na conta real da Prumo.**

**Gate financeiro de cada futuro lote E05 [P]:**
- Aprovação humana identificada, data e finalidade **somente fictícia**; versão de modelo/endpoint; massa de casos e tamanho; quantidade **máxima de requests**; número de tentativas e política de retry.
- Estimativa por operação: texto entrada/saída, prefixo cacheado e custo de escrita/leitura, áudio/segundos/sessões, overhead e margem; **preços vivos capturados na data do orçamento**, sem números presumidos.
- Limite de segurança **interno à aplicação/runner**, independente do painel, com interrupção local ao atingir limite de requests e orçamento aprovado; inspeção de uso/custo real ao concluir.
- Erro 429, quota, timeout e respostas tardias não disparam repetição ilimitada; nenhum gatilho pode assumir autorização de custo.

Fontes: [gestão de projeto API](https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform) e [troubleshooting usage/spend limits](https://help.openai.com/en/articles/6614457-troubleshooting-api-usage-and-spend-limits). **Sem gasto de API nesta etapa.**

## 3. Dados e retenção do fornecedor — pontos verificáveis [V/R]

Segundo a documentação de Data Controls consultada em 22/10:
- Dados da API **não são usados para treinar modelos por padrão**, sujeito às políticas/opt-ins da organização.
- Na **Responses API**, o armazenamento de estado da resposta depende de endpoint/configuração: há comportamento padrão de retenção de application state por até cerca de 30 dias conforme configurações; `store=false` é controle relevante para o desenho, **mas não promete, isoladamente, ausência de todos os logs de segurança, cache ou outros estados**.
- **Zero Data Retention (ZDR)**, quando **realmente habilitado e elegível**, modifica `store` e outras regras; serviços/funcionalidades podem **não** ser elegíveis ou reter application state por propósitos específicos. **Não presumir ZDR habilitado.**
- Saídas de áudio, arquivos, background mode e outras capacidades têm tratamentos de retenção próprios que precisam ser verificados **por endpoint e modalidade**.
- O cache de prompt pode armazenar estado técnico para permitir reuse e possui duração/cobrança conforme modelo e opções; **não substitui** ACL/retenção/estado atual da base ou da conversa.

**Decisões necessárias antes de E05:** mapear, por **F01/F02/F03/STT/TTS**, tipo de dado permitido, finalidade, minimização de PII/finanças, proveniência, política de armazenamento/retenção, acesso a mídia, redaction/logging, elegibilidade ZDR e termo da API. Para **dados reais** depois do laboratório, exige avaliação legal/segurança e autorização adicional; e a investigação de API Banco continua adiada. Manter `store=false` como **hipótese de controle a confirmar por endpoint e contrato**, não como autorização geral de tratamento.

Fonte: [OpenAI API — Data controls](https://developers.openai.com/api/docs/guides/your-data).

## 4. Prompt caching — opção e não premissa de economia [V/P/R]

Documentação atual distingue gerações de modelo: modelos recentes na Responses API podem usar `prompt_cache_options.ttl` com vidas mínimas e custos de escrita distintos; modelos anteriores usam `prompt_cache_retention` quando suportado. Exemplos de duração **não são SLA geral nem política de deleção de dados**. Logo:
- Não especificar um único parâmetro/cache fixo válido para qualquer modelo da shortlist antiga.
- Priorizar prefixos **globais estáveis** de instruções F01/F02/F03, sem embutir conteúdo privado de uma loja/cliente; cache de prefixo reutilizado **não é memória do cliente**.
- Sempre recuperar bases/fatos/estado/handoff e permissões **atuais** por S0; revalidar vigência mesmo com cache HIT.
- Não alegar redução de custo/latência até medições reais de calls/tokens e comparação com `cache OFF` e `cache ON`; custos de escrita/reuse e duração podem alterar a conclusão.
- Política de ZDR/retenção precisa ser avaliada para a configuração efetiva antes de ligar cache extendido.

Fonte: [OpenAI — Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching).

## 5. Artefatos para futuro gate — sem valores secretos

| Evidência candidata | Campos publicáveis sem segredo | Não publicar |
|---|---|---|
| Aprovação de execução | Quem autorizou, escopo, prazo, versão, valor máximo, lotes e rollback | Cartão, chave, resposta de autenticação, detalhes pessoais |
| Seleção de fornecedor/modelo | Modelo exato e endpoint **disponíveis no projeto**, data e motivo, capacidade/codec/custo e política | Chave e acessos, token, dados privados de cliente |
| Políticas de dados | Finalidade, classes permitidas, `store` e retenção após verificação, base legal e dono | PII bruta, mídia real, prompts com dados sensíveis |
| Limites financeiros | Estimativa/duração/requests, limites do runner, alertas de painel e reconciliação de custo | Credencial, billing pessoal |
| Segurança | Chave mantida manualmente no cofre correto, ACL do runtime, teste de revogação e log sanitizado | Valor/fragmento do secret, screenshot do secret |
| Incidente | Evento, classe, timestamp, responsável, revogação/teste sem payload | Transcrição real, chave, CPF real |

## 6. Barreiras operacionais não negociáveis

**E02-REV continua ABERTA:** S0/Meta/S1/FV/Prumo devem ratificar a porta F03, C09/F02, catálogo/identidade/mídia, conhecimento/skills/MCP e consentimentos. **E02-FIX** requer schema/fixtures reais e somente poderá ser executada em E04 após **liberação expressa de implementação**. **E03-A..H continuam ADIADAS** por decisão de 19/10; E05 requer **aprovação independente de acesso, orçamento, dados sintéticos e execução**.

**Referências internas:** `E03_PREPARACAO_CONTA_CREDENCIAL_GATES_v0_1.md`, `E01_PLANO_DE_AVALIACAO_MODELOS_E_VOZ_v0_1.md`, E01-KH, E01-INT v0.4, E02-QA e AL-IA. **Status: revisão documental de fornecedor pronta; nenhuma conta, chave, secret ou gasto confirmado/criado.**
