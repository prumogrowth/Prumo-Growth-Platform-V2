# Frente OpenAI — Prumo Growth | índice inicial

**Data:** 18/10/2026. **Branch:** feat/s2-openai-adapter-sintetico. **Estado:** planejamento contratual [P], sem integração operacional. Branch derivada de main; não contém código das branches S0 ou Meta.
**Regra de convivência:** NÃO transferir, cancelar, bloquear, reescrever ou assumir demandas dos PRs #1 (S0) e #2 (WhatsApp/Meta). Se uma dessas frentes já implementa algo relacionado a IA, a titularidade permanece com ela até decisão expressa posterior.

## Objetivo particular desta frente

Preparar o acesso da plataforma técnica Prumo à API da OpenAI: entendimento de projetos e credenciais, contrato de chamada/retorno do provedor, configuração de segredo via ação MANUAL do responsável, limites, evidências e integração futura com o núcleo S0.

**Fora desta etapa:** gerar ou divulgar chave por automação, escrever segredos no GitHub, consumir API paga, ativar IA real, implantar Edge Functions, modificar esquema, efetuar merges ou mudanças nas outras duas frentes. Qualquer operação futura no Supabase exige verificar o projeto exclusivo da Prumo, permissões da conta executora e autorização da mudança; não inferir indisponibilidade geral de ferramentas a partir de uma sessão de trabalho.

## Documentos nesta branch

1. **contrato-s0-openai-v0_1.md** — fronteira entre adaptador OpenAI, núcleo S0, regras comerciais e Meta; contrato C03/C05 conceitual.
2. **provisionamento-credenciais-manual-v0_1.md** — roteiro de emissão e armazenamento MANUAL da chave OpenAI pelo responsável, no destino técnico confirmado, sem impedir outras operações autorizadas no Supabase da Prumo.
3. **matriz-dependencias-e-testes-v0_1.md** — donos, condicionantes e aceite incremental sem interromper outras frentes.
4. **avaliacao-transporte-openai-direto-ou-n8n-v0_1.md** — decisão de topologia EM ABERTO [R], caminhos A/B, teste comparativo e critérios de escolha.
5. **AUDITORIA_CONTRATO_OAI_2026_10_18.md** — resultados da auditoria e pendências separadas de evidências executadas.

## Princípios de precedência

- A plataforma ainda NÃO tem marca comercial aprovada; LiberaCred é o produta instituição financeira.
- As normas vigentes são 00A, 13A, 21–23 e 41, com apoio dos docs 06/26/33/38/40. Propostas [P], pendências [R] e validações [V] não são decisões [D].
- Exatamente oito estados comerciais; nenhuma saída da OpenAI modifica estado automaticamente.
- IA Vendedora e IA Planejadora estão no escopo; **IA Analista autônoma está EXCLUÍDA**; ChatGPT/MCP administrativo é fluxo independente sob normas próprias.
- Concessionárias não compartilham contexto de cliente, histórico ou resultado. Handoff humano encerra definitivamente a IA Vendedora do caso.
- Somente o núcleo decide elegibilidade, permissões, persistência, status, handoff e intenção de envio; somente a frente Meta responde por transporte/callbacks WhatsApp.

## Referências

Projeto: pacote documental auditado em 17/10/2026 (00A, 06, 13A, 26, 33, 38, 40, 41) e branches PR #1 / PR #2 consultadas em 18/10/2026.
OpenAI projetos/chaves: https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform
OpenAI segurança de chaves: https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety
Supabase secrets para funções autorizadas: https://supabase.com/docs/guides/functions/secrets

**Topologia OpenAI ↔ backend [R]:** chamada direta autenticada pelo runtime servidor/Edge Functions OU orquestração via n8n; nenhum caminho foi testado/selecionado para esta frente. O contrato de domínio deve ser independente da topologia. **Sem GO para operação real.** Mudanças em outra frente dependem da frente proprietária e de revisão cruzada.
