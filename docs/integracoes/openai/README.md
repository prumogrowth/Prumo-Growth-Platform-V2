# Frente OpenAI — Prumo Growth | índice inicial

**Data:** 18/10/2026. **Branch:** feat/s2-openai-adapter-sintetico. **Estado:** planejamento contratual [P], sem integração operacional. Branch derivada de main; não contém código das branches S0 ou Meta.
**Regra de convivência:** NÃO transferir, cancelar, bloquear, reescrever ou assumir demandas dos PRs #1 (S0) e #2 (WhatsApp/Meta). Se uma dessas frentes já implementa algo relacionado a IA, a titularidade permanece com ela até decisão expressa posterior.

## Objetivo particular desta frente

Preparar o acesso da plataforma técnica Prumo à API da OpenAI: entendimento de projetos e credenciais, contrato de chamada/retorno do provedor, configuração de segredo via ação MANUAL do responsável, limites, evidências e integração futura com o núcleo S0.

**Fora desta etapa:** gerar chave por automação, copiar chave para este chat, escrever segredos no GitHub, consultar o plugin Supabase conectado (pertence a OUTRO projeto), consultar ou modificar qualquer instância Supabase, consumir API paga, ativar IA real, implantar Edge Functions, modificar esquema, efetuar merges ou mudanças nas outras duas frentes.

## Documentos nesta branch

1. **contrato-s0-openai-v0_1.md** — fronteira entre adaptador OpenAI, núcleo S0, regras comerciais e Meta; contrato C03/C05 conceitual.
2. **provisionamento-credenciais-manual-v0_1.md** — roteiro público de projeto/chave OpenAI e segredo Supabase que SOMENTE o responsável aplicará no projeto correto, quando decidir.
3. **matriz-dependencias-e-testes-v0_1.md** — donos, condicionantes e aceite incremental sem interromper outras frentes.

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
Supabase segredos em Edge Functions (instrução documental, **sem acesso a projeto**): https://supabase.com/docs/guides/functions/secrets

**Sem GO para operação real.** O texto aqui é um contrato candidato de interface; mudanças em outra frente dependem da frente proprietária e de revisão cruzada.
