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
6. **PLANO_EXECUCAO_E_CRITERIOS_DE_CONCLUSAO_v0_1.md** — roteiro fechado E00–E08, responsáveis, gates, evidências de conclusão e limite da entrega laboratorial [P].
7. **E01_CONTRATO_FUNCIONAL_MULTI_CAPACIDADE_v0_2.md** — contrato funcional [P] para IA Vendedora, Planejadora, preenchimento automático pós-atendimento humano F03 e entrada/saída de áudio F04/F05; revisão S0/Meta [R].
8. **E01_PLANO_DE_AVALIACAO_MODELOS_E_VOZ_v0_1.md** — shortlist e avaliação por tarefa, sem fixar modelo ou voz antes de benchmark.
7. **OAI_05_CONTRATO_EXTRAÇÃO_PÓS_ATENDIMENTO_HUMANO_v0_1.md** — cadastro extraído após conversa humana concluída, com fontes e validação S0; interface [P/R].
8. **OAI_06_VOZ_AUDIO_E_MODELOS_v0_1.md** — áudio recebido/enviado, STT/TTS, modelos por tarefa e critérios de comparação [P/R/V].

## Princípios de precedência

- A plataforma ainda NÃO tem marca comercial aprovada; LiberaCred é o produta instituição financeira.
- As normas vigentes são 00A, 13A, 21–23 e 41, com apoio dos docs 06/26/33/38/40. Propostas [P], pendências [R] e validações [V] não são decisões [D].
- Exatamente oito estados comerciais; nenhuma saída da OpenAI modifica estado automaticamente.
- IA Vendedora e IA Planejadora estão no escopo; há ainda extrator pós-atendimento humano SILENCIOSO (nova orientação funcional, interface P/R) e capacidade futura de áudio/voz; **IA Analista autônoma está EXCLUÍDA**; ChatGPT/MCP administrativo é fluxo independente sob normas próprias.
- Concessionárias não compartilham contexto de cliente, histórico ou resultado. Handoff humano encerra definitivamente a IA Vendedora do caso.
- Somente o núcleo decide elegibilidade, permissões, persistência, status, handoff e intenção de envio; somente a frente Meta responde por transporte/callbacks WhatsApp.

## Referências

Projeto: pacote documental auditado em 17/10/2026 (00A, 06, 13A, 26, 33, 38, 40, 41) e branches PR #1 / PR #2 consultadas em 18/10/2026.
OpenAI projetos/chaves: https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform
OpenAI segurança de chaves: https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety
Supabase secrets para funções autorizadas: https://supabase.com/docs/guides/functions/secrets

**Nova orientação F03 [D-direção/R-interface, 18/10/2026]:** ao encerrar o atendimento humano, uma rotina OpenAI separada da IA Vendedora extrai informações declaradas e propõe preenchimento automático dos campos elegíveis; S0 valida/persiste sem exigir digitação rotineira do operador. A falta de informação permanece pendente, sem preenchimento fictício. Nenhuma tela/SQL/ação Meta foi assumida pela frente OpenAI. Também entram no contrato TTS (áudio de saída), STT (áudio de entrada) e avaliação por tarefa/modelo, sujeitos a provas e autorizações próprias.

**Topologia OpenAI ↔ backend [R]:** chamada direta autenticada pelo runtime servidor/Edge Functions OU orquestração via n8n; nenhum caminho foi testado/selecionado para esta frente. O contrato de domínio deve ser independente da topologia. **Sem GO para operação real.** Mudanças em outra frente dependem da frente proprietária e de revisão cruzada.
