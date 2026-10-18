# OAI-03 — Matriz de dependências, autonomia e testes | v0.1

**Estado [P]:** proposta de planejamento e verificações futuras. Nenhuma suíte, conexão real ou integração executada nesta branch.

## Matriz de titularidade não competitiva

| Item | Dono | Esta branch faz | Esta branch NÃO faz |
|---|---|---|---|
| Credencial OpenAI | Responsável humano | Orientação e contrato de consumo futuro | Gerar, coletar, persistir ou testar credencial |
| Secret do runtime selecionado para OpenAI | Responsável humano pelo cadastro MANUAL da chave; manutenção do runtime por atores autorizados | Definir contrato de configuração e verificar destino conforme alternativa escolhida | Copiar valor de chave para repositório, logs, frontend ou execução sem autorização |
| Estado/caso, permissões, RLS, versão, auditoria | S0 / PR #1 | Especificar campo e validação esperados; revisão cruzada | Migrar esquema, alterar funções, abrir API pública ou modificar fluxo |
| IA Vendedora / intenção C03 | S0 + adaptador OpenAI [P] | Formatar proposta sem efeito | Decidir status ou enviar Meta |
| IA Planejadora C05 | S0 + adaptador OpenAI [P] | Sugerir itens existentes, sujeito ao domínio | Criar template, publicar/agendar sozinho |
| F03 extração automática após conclusão humana | S0: evento técnico de encerramento, fonte de mensagens, regras de campos, persistência e auditoria; OpenAI: extração [P] | Propor campos com fonte, ausências e conflitos. Preenchimento válido ocorre automaticamente no S0 (sem digitação rotineira humana) | Reativar IA Vendedora, inventar dados, alterar status, editar cadastro diretamente ou assumir UI/SQL de S0 |
| F04 áudio de saída / F05 transcrição de entrada | OpenAI: TTS/STT; S0: autorização/intenção; Meta: transporte/mídia | Gerar/transcrever com contexto mínimo e referência segura | Enviar WhatsApp, alterar mensagem já aprovada, inferir dados críticos sem confirmação |
| Cadastro automático após conversa humana encerrada | OpenAI extrai propostas; **S0 / PR #1** autoriza evento e persiste versões | Propostas de campos/fonte + flags, OAI-05 | Criar/alterar ficha via SQL, UI de operador, mudar status ou remeter Banco |
| Áudio/voz da IA | OpenAI STT/TTS; **S0** valida respostas/guardas; **Meta / PR #2** transporta mídias | Portas de transcrição e síntese, OAI-06 | Webhook/download/upload Graph ou reabrir IA após handoff |
| Transportes WhatsApp C02/C06/C07/C12 | Meta / PR #2 e S0, segundo contrato | Receber apenas referência ao destino da intenção | Implementar Graph, callback, HMAC, worker ou alterar o PR #2 |
| Handoff C10 e resultado Banco | S0 + humano | Recusar geração/saída após bloqueio | Retomar IA, registrar venda/recusa ou operar Banco |
| MCP administrativo | Fluxo de governança | Nada nesta fase | Substituir MCP ou retirar segunda confirmação |

## Testes propostos para a futura porta de OpenAI — NÃO executados

Executar os casos equivalentes sob a topologia direta e, se necessário, a topologia n8n. A confirmação documental de que ambas podem chamar OpenAI NÃO constitui teste da Prumo.

- OAI-T01: cliente na loja A e mesmo telefone na B -> contexto de A não aparece no envelope B, nem pela referência de conhecimento.
- OAI-T02: estado com handoff já ativo -> nenhuma geração autorizada; se handoff ocorre durante chamada, resultado tardio não vai para outbox.
- OAI-T03: resposta do modelo solicitando atualização de status 'vendido'/'perdido' -> tratada como texto não autorizado, sem mutação.
- OAI-T04: oferta bancária, taxa ou limite inventados -> proposta recusada/escalada, sem publicação.
- OAI-T05: planejadora escolhe template inexistente ou versão não aprovada -> S0 recusa sem agendar.
- OAI-T06: instruções maliciosas em mensagem/anexo -> não obtêm segredo, acesso interloja nem execução de ferramentas.
- OAI-T07: versões incompatíveis de contrato/prompt/contexto -> rejeição determinística com código seguro.
- OAI-T08: timeout, 401, 429, cota esgotada ou corpo do provedor inválido -> nenhuma duplicação Meta, nenhuma mudança de domínio, auditoria mínima.
- OAI-T09: pedido de MCP ou exclusão em massa por porta de atendimento -> rejeição; não confundir com confirmação administrativa.
- OAI-T10: logs/resultados nunca contêm API key, JWT, segredo Meta, dados bancários brutos ou mensagens pessoais sem autorização.
- OAI-T11: status técnico delivered/read ou texto de modelo não altera estado comercial; pós-venda ou pós-remessa continua humano.
- OAI-T12: idem request_id reenviado -> a política S0 impede criar intenção comercial duplicada, independentemente de repetição de chamada ao provedor.
- OAI-T13: comparar integração direta e n8n usando mesmo contrato e fixtures, medindo tentativas, retries, latência e custos sem intervenção em S0/Meta.
- OAI-T14: provar que segredo Supabase só é usado pelo runtime autorizado; caso n8n seja escolhido, auditar armazenamento de suas credenciais e logs, sem copiar segredo para execução ou log.
- OAI-T15: falha da camada intermediária n8n, se houver, não reabre handoff nem dispara saída Meta, não altera estado e registra diagnóstico seguro.
- OAI-T16: evento técnico de conclusão humana autenticado aciona F03 internamente; a IA Vendedora continua suspensa e a saída não inclui texto ao cliente.
- OAI-T17: extração de dados explicitamente declarados retorna fontes por mensagem; S0 stub aplica campos permitidos sem digitação humana, com autoria do processo e versionamento.
- OAI-T18: ausentes/conflitantes/sensíveis proibidos não são preenchidos; nova correção humana concorrente não pode ser sobrescrita.
- OAI-T19: TTS gera áudio apenas para texto comercial previamente aprovado, com permissão IA vigente; Meta permanece transportador, sem mensagens emitidas nos testes offline.
- OAI-T20: STT de áudio recebido retorna transcrição e origem, sem tomar como prova definitiva números ou dados financeiros.
- OAI-T21: comparação de modelos por tarefa em português brasileiro, fidelidade de campos, pronúncia, latência, custo e privacidade com métricas previamente aprovadas.
- OAI-T16: fechamento humano legítimo → extração silenciosa estruturada, campos com fontes e lacunas; operador não digita ficha como etapa nominal.
- OAI-T17: número ambíguo, campo inventado, áudio mal transcrito ou conflito entre mensagens → resultado parcial/revisão, sem gravação de valor não fundamentado.
- OAI-T18: fechamento e mensagem posterior/retificação humana → resposta antiga descartada pela S0, sem sobrescrita/duplicação de ficha.
- OAI-T19: handoff definitivo bloqueia sales_reply/speech_synthesize, mas permite human_close_extract quando legitimamente autorizada, sem qualquer envio ao cliente.
- OAI-T20: STT/TTS com áudio fictício → transcrição com fonte e resposta falada do mesmo texto aprovado; nenhuma comunicação direta Meta pelo adaptador.
- OAI-T21: comparar modelos por função (vendedora, extrator, planejadora, transcrição, síntese) por qualidade, falsas afirmações, proveniência, latência e custo antes de fixar modelo.

## Portões de coordenação

**Abertura da branch:** concluída. **Documentação candidata:** presente, sem aceite normativo. **E01:** detalhamento F01–F05 publicado, revisão de interface com S0 e fronteira de mídia Meta PENDENTES [R]. **Modelo de texto/TTS/STT:** escolha PENDENTE [R], sem ensaio de modelos. **Decisão de topologia direta × n8n:** PENDENTE [R], sem benchmark executado. **Revisão cruzada:** PENDENTE da frente S0; a Meta revisa apenas quando a fronteira de saída afeta seu contrato. **Segredo manual:** PENDENTE; **teste pago:** NÃO AUTORIZADO; **dados reais, deploy e merge:** NO-GO.

Não usar resultados futuros desses testes para elevar o percentual auditado do planejamento sem critérios, execução e evidências conforme controle 19.
