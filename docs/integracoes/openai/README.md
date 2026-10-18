# Frente OpenAI — Prumo Growth | índice inicial

**Data:** 18/10/2026. **Branch:** feat/s2-openai-adapter-sintetico. **Estado:** planejamento contratual [P], sem integração operacional. Branch derivada de main; não contém código das branches S0 ou Meta.
**Regra de convivência:** NÃO transferir, cancelar, bloquear, reescrever ou assumir demandas dos PRs #1 (S0) e #2 (WhatsApp/Meta). Se uma dessas frentes já implementa algo relacionado a IA, a titularidade permanece com ela até decisão expressa posterior.

## Objetivo particular desta frente

Preparar o acesso da plataforma técnica Prumo à API da OpenAI: entendimento de projetos e credenciais, contrato de chamada/retorno do provedor, configuração de segredo via ação MANUAL do responsável, limites, evidências e integração futura com o núcleo S0.

**Fora desta etapa:** gerar ou divulgar chave por automação, escrever segredos no GitHub, consumir API paga, ativar IA real, implantar Edge Functions, modificar esquema, efetuar merges ou mudanças nas outras duas frentes. Qualquer operação futura no Supabase exige verificar o projeto exclusivo da Prumo, permissões da conta executora e autorização da mudança; não inferir indisponibilidade geral de ferramentas a partir de uma sessão de trabalho.

## Documentos nesta branch

1. **contrato-s0-openai-v0_1.md** — porta e fronteiras entre S0, OpenAI e Meta; v0.1 candidata, atualizada com as operações novas.
2. **OAI_05_CONTRATO_EXTRAÇÃO_PÓS_ATENDIMENTO_HUMANO_v0_1.md** — contrato específico `human_close_extract`, campos com evidência e persistência automática sob validação S0 [P/R].
3. **OAI_06_VOZ_AUDIO_E_MODELOS_v0_1.md** — contrato específico `speech_transcribe` / `speech_synthesize`, texto aprovado, voz e limites Meta [P/R/V].
4. **E01_CONTRATO_FUNCIONAL_MULTI_CAPACIDADE_v0_2.md** — visão integrada de F01–F05, segurança e autoria, com exemplos e semântica harmonizados com OAI-05/06.
5. **E01_PLANO_DE_AVALIACAO_MODELOS_E_VOZ_v0_1.md** — plano de benchmark dos modelos de texto, extração, transcrição e TTS sem escolha antecipada [P].
6. **provisionamento-credenciais-manual-v0_1.md** — emissão e armazenamento MANUAL da chave pelo responsável, destino seguro conforme runtime.
7. **matriz-dependencias-e-testes-v0_1.md** — titularidade preservada e cenários de teste.
8. **avaliacao-transporte-openai-direto-ou-n8n-v0_1.md** — conexão direta versus n8n ainda em aberto [R].
9. **AUDITORIA_CONTRATO_OAI_2026_10_18.md** — auditoria da fase de abertura e seus gates.
10. **MAPA_CAPACIDADES_E_PENDENCIAS_OPENAI_v0_1.md** — inventário que preserva também mídia visual/documentos como pesquisa futura sujeita a autorizações, governança de conhecimento, modelos e dependências, sem ampliar o escopo sem decisão.
11. **E02_POLITICAS_SEGURANCA_CRITERIOS_ACEITE_v0_1.md** — E02: segurança, privacidade, autoaplicação de campos com fonte, limites e gates propostos [P/R/V].
12. **E02_MATRIZ_CASOS_SINTETICOS_E_METRICAS_v0_1.md** — E02: 32 cenários de teste a implementar em E04, métricas, bloqueios críticos e comparação futura [P].
13. **OAI_07_DESFECHO_ENCAMINHAMENTO_PREFERENCIA_CANAL_v0_1.md** — esclarecimentos [D-NEGÓCIO] do responsável em 18/10 sobre fechamento humano, motivo/desfecho da conversa, todos os campos disponíveis, essenciais × opcionais, roteamento e avisos IA → humano, voz adaptativa e orçamento por lote; limites bancários [R/V].
14. **PLANO_EXECUCAO_E_CRITERIOS_DE_CONCLUSAO_v0_1.md** — roteiro fechado E00–E08: E00 concluído; E01 e E02 documentados em revisão, E03–E08 pendentes. Nenhum teste E02 executado.

## Princípios de precedência

- A plataforma ainda NÃO tem marca comercial aprovada; LiberaCred é o produta instituição financeira.
- As normas vigentes são 00A, 13A, 21–23 e 41, com apoio dos docs 06/26/33/38/40. Propostas [P], pendências [R] e validações [V] não são decisões [D].
- Exatamente oito estados comerciais; nenhuma saída da OpenAI modifica estado automaticamente.
- IA Vendedora e IA Planejadora estão no escopo; há ainda extrator pós-atendimento humano SILENCIOSO (nova orientação funcional, interface P/R) e capacidade futura de áudio/voz; **IA Analista autônoma está EXCLUÍDA**; ChatGPT/MCP administrativo é fluxo independente sob normas próprias.
- Concessionárias não compartilham contexto de cliente, histórico ou resultado. Handoff humano encerra definitivamente a IA Vendedora do caso.
- Somente o núcleo decide elegibilidade, permissões, persistência, status, handoff e intenção de envio; somente a frente Meta responde por transporte/callbacks WhatsApp.
- E02 reforça que JSON estruturado não prova veracidade: autoaplicação exige evidência explícita rastreável, campo permitido, versão atual e autorização S0. Dados reais e campos D3 permanecem dependentes de decisão e validação externa; requisitos de privacidade/retenção seguem sem homologação.

## Referências

Projeto: pacote documental auditado em 17/10/2026 (00A, 06, 13A, 26, 33, 38, 40, 41) e branches PR #1 / PR #2 consultadas em 18/10/2026.
OpenAI projetos/chaves: https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform
OpenAI segurança de chaves: https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety
Supabase secrets para funções autorizadas: https://supabase.com/docs/guides/functions/secrets

**Nova orientação F03 [D-direção/R-interface, 18/10/2026]:** ao encerrar o atendimento humano, uma rotina OpenAI separada da IA Vendedora extrai informações declaradas e propõe preenchimento automático dos campos elegíveis; S0 valida/persiste sem exigir digitação rotineira do operador. A falta de informação permanece pendente, sem preenchimento fictício. Nenhuma tela/SQL/ação Meta foi assumida pela frente OpenAI. Também entram no contrato TTS (áudio de saída), STT (áudio de entrada) e avaliação por tarefa/modelo, sujeitos a provas e autorizações próprias.

**Emenda OAI-07 [D-NEGÓCIO; implementação P/R]:** quando operador clicar encerrar, analisar evidências e desfecho conversacional, preencher automaticamente TODOS os campos elegíveis que foram explicitamente informados, voltar ao humano apenas se faltar dado realmente essencial ou houver outra necessidade legítima de revisão e exibir motivo curto para CADA handoff IA → humano; somente campos exigidos e legalmente autorizados seguem para remessa. A modalidade áudio/texto adapta-se ao padrão reiterado e pedido explícito, sem inferir preferência por um único áudio. Venda/recusa bancária oficiais permanecem atos humanos com prova conforme 13A/21/41; classificação IA é hipótese, não mudança de status. Não há teto global de gasto em testes: exigir autorização de estimativa por lote. Ver OAI-07.

**Esclarecimento de resultado comercial [D-NEGÓCIO, 18/10/2026]:** atendimento “fechado” significa interesse confirmado e dados preparados para remessa, NÃO `vendido`. A OpenAI poderá sugerir `NEGOTIATION_READY_FOR_BANK_HANDOFF` com fonte, e S0 encaminha para operador de remessa conforme regras. Status `cadastro enviado ao operador` após fechamento HUMANO requer validação da transição pela frente S0, e `cadastro enviado ao banco` exige envio real com prova. `vendido` continua condicionado à confirmação bancária efetiva de venda/pagamento e marcação humana com evidência. Ver OAI-07 atualizado.

**Topologia OpenAI ↔ backend [R]:** chamada direta autenticada pelo runtime servidor/Edge Functions OU orquestração via n8n; nenhum caminho foi testado/selecionado para esta frente. O contrato de domínio deve ser independente da topologia. **Sem GO para operação real.** Mudanças em outra frente dependem da frente proprietária e de revisão cruzada.
