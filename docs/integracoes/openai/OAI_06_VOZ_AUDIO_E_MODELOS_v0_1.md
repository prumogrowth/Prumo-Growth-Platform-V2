# OAI-06 — Voz, áudio e seleção de modelos OpenAI | contrato v0.1

**Data:** 18/10/2026 | **Estado:** [D de finalidade] necessidade funcional apresentada pelo responsável: IA Vendedora poderá responder com mensagens de áudio quando adequado; [P] fluxos técnicos, catálogo e avaliação; [R] regras de quando usar voz, linguagem/identidade, modelo por tarefa, critério de qualidade, suporte real do canal; [V] políticas Meta/Banco/LGPD, mídia, condições contratuais. NÃO IMPLEMENTADO.

## 1. Três capacidades diferentes, sem confundi-las

| Capability proposta | Entrada autorizada | Saída / finalidade | Dono do resultado |
|---|---|---|---|
| `speech_transcribe` | Mídia de áudio WhatsApp acessada pela frente Meta/S0 de modo autorizado; referência + arquivo temporário preparado no runtime controlado | Transcrição com referência à mensagem-fonte, indicação de idioma/qualidade/trecho incerto; origem para IA Vendedora ou OAI-05, nunca evidência bancária isolada | OpenAI normaliza; S0 decide armazenamento e validade |
| `sales_reply` com preferência `output_mode=audio` | Contexto textual/transcrição de mesma loja/ciclo ainda SOB IA, instruções comerciais autorizadas | Proposta de texto exato a ser falado, sujeito às guardas S0 | OpenAI retorna proposta; S0 valida |
| `speech_synthesize` | Texto final de resposta **já aprovado pela S0**, voz/estilo/idioma autorizados | Audio bytes ou referência técnica temporária, duração e metadados de formato; não publica WhatsApp | OpenAI gera áudio; S0 aprova publicação; Meta adapta/enviará mídia conforme seu contrato |

**Não confundir:** `human_close_extract` de OAI-05 é pós-atendimento humano, não gera resposta ao cliente nem áudio. A IA Vendedora não reabre caso após handoff. Mensagem de áudio enviada pela IA precisa passar pelo mesmo bloqueio final de handoff/versionamento que texto.

## 2. Caminho candidato WhatsApp assíncrono [P]

1. Meta/PR #2 autentica, obtém a mensagem e resolve autorização/correlação canal/loja; armazenamento temporário de mídia e conversão técnica são pontos a decidir entre Meta, S0 e adaptador, sem transferir titularidade.
2. S0 confirma ciclo IA ativo e autoriza `speech_transcribe` com escopo mínimo; resultado pode ser adicionado à mensagem com ligação ao `message_id` se autorizado.
3. IA Vendedora `sales_reply` produz texto comercial aprovado pelo S0 (inclusive termos/condições de Banco/Meta). Se autorizado para aquele tipo de resposta, solicitação `speech_synthesize` converte **esse mesmo texto** em voz.
4. S0 vincula referência temporária ao item de outbox, revalida handoff e versão imediatamente antes de autorizar envio e entrega a Meta/PR #2; o módulo Meta negocia mídia/formato/Graph e reporta recibos técnicos.
5. Falha TTS: não assumir fallback automático para texto nem envio duplicado; a política de fallback depende de regras de experiência/permissão [R]. Não gerar áudio antes da aprovação do texto para reduzir riscos e consumo.

**Essa é arquitetura text → TTS de mensagens gravadas e assíncronas, NÃO ligação telefônica, streaming bidirecional ou sessão de voz em tempo real.** O Realtime API é hipótese de pesquisa futura apenas se houver requisito de fala síncrona, interrupções ou telefone; não há justificativa atual para seu custo e arquitetura. O n8n continua alternativa de orquestração em aberto, não requisito de voz.

## 3. Fronteiras de permissão

- OpenAI: transcrever ou sintetizar mídia recebida em escopo mínimo, com modelo/voz configurados, formatos/erros e métricas sanitizados; não envia mídia diretamente ao WhatsApp nem atualiza tabela de mensagens/cadastros.
- S0: elegibilidade, bloqueio IA após handoff, autorização de transcrição e síntese, texto final, correlação entre áudio/texto/fonte, auditoria, privacidade, status da outbox.
- Meta: webhooks, origem autêntica, download de mídia, limites de formatos/tamanhos do Graph, upload/transporte e callbacks; **o PR #2 preserva integralmente essa responsabilidade**.
- Operador: continua humano em casos recebidos; extrator pós-humano usa transcrição existente/permitida como fonte, mas não tem autorização para emitir voz.
- Responsável: política de voz, identidade declarada de assistente virtual, consentimento quando aplicável, limites de duração, custo e testes [R/V].

## 4. Contratos candidatos de voz [P]

### Transcrição

**Entrada:** `request_id`, `operation_kind=speech_transcribe`, `message_ref`, `conversation_ref`, `concessionaria_id`, `audio_ref` efêmera validada, `media_mime`, `max_duration_policy`, `language_hint?`, `provider_policy_ref`, `privacy_policy_version`, `expected_version`.
**Saída:** `transcript_text` (se autorizado), `source_message_ref`, `segments[]?`, `model_ref`, `language_detected?`, `uncertainty_flags[]`, `status` e duração/uso técnico. Não inventar transcrição quando áudio indecifrável; não inferir cadastro de ruído.

### Síntese

**Entrada:** `request_id`, `operation_kind=speech_synthesize`, `approved_text_ref`, `approved_text_hash`, `voice_policy_version`, `voice_id` permitida, `language`, `output_format`, `max_duration`, `max_cost_policy`, `expected_version`, `case_guard` da S0.
**Saída:** `audio_artifact_ref` efêmera/segura, `audio_sha256`, `duration_ms?`, `format`, `model_ref`, `provider_trace_ref` sanitizado, `status`, `usage_metrics?`.
A resposta pode conter mídia apenas no runtime restrito; logs e GitHub guardam **somente referências e hash**, nunca arquivo bruto ou transcrição real sem autorização. Somente outbox autorizada da S0, via Meta, pode publicar.

**Segurança:** não clonar voz real de pessoa sem direitos/permissão e aprovação específicos; evitar confusão sobre ser humano; texto e áudio devem corresponder e ser auditáveis; evitar instruções de mídia que façam o modelo criar taxa, condição de crédito ou promessa. Limites/vozes efetivos exigem verificação do provedor e da Meta na ocasião dos testes.

## 5. Mapa de opções OpenAI documentadas em 18/10/2026 [V documentação ≠ decisão]

| Tarefa | Candidatos iniciais / tecnologia | O que falta validar no projeto |
|---|---|---|
| Conversa comercial `sales_reply` | Responses API, candidatos `gpt-6-luna`, `gpt-6.1-sol` e escalonamento pontual mais robusto se necessário | Evals comerciais, segurança, aderência ao prompt, custo por atendimento e latência; nenhum modelo fixado |
| Pós-atendimento `human_close_extract` | Responses API + **Structured Outputs JSON Schema**; comparar `gpt-6-luna` versus `gpt-6.1-sol` com casos sintéticos e documentos normativos | Precisão por campo, falsos preenchimentos (metrica crítica), proveniência, contradições, custo, versões e qualidade do português brasileiro |
| Recontatos `recontact_plan` | Mesma API com opções de catálogo pré-aprovado e validadores S0 | Nunca criar templates ou executar envio por conta própria; comparar com baseline determinístico |
| Áudio recebido (mensagem WhatsApp) | File transcription API, modelo inicial documentado `gpt-transcribe` | Qualidade em português BR, ruído, nomes, valores numéricos, sotaques, duração, MIME e LGPD |
| Áudio de saída de mensagens | Text-to-speech API, candidato documentado `gpt-4o-mini-tts` | Voz e pronúncia pt-BR, naturalidade, duração, tamanho/codec do WhatsApp, transparência de voz de IA, custo |
| Voz bidirecional síncrona | Realtime API, somente hipótese futura [R] | Não é necessária para mensagem de voz assíncrona; justificar requisitos antes de investigar |

Os modelos acima são **candidatos de pesquisa**, não selecionados nem garantidos para a organização/limite da conta. Atualizar catálogo/preços/limites antes da execução, pois mudam. Modelos de texto atuais NÃO são assumidos como geradores diretos de áudio; STT/TTS são tarefas distintas.

## 6. Plano de avaliação por tarefa [P]

Preparar corpus **100% fictício**, sem chat real do cliente:
- Vendedora: naturalidade e segurança, handoff, recusa de afirmações bancárias não sustentadas; medir taxa de erros comerciais e de bloqueios.
- Extrator: matriz de verdade por campo; medir precisão, recall para campos explícitos, **taxa de falsos positivos/valores inventados**, identificação de conflitos, citações corretas a mensagens, ausência de vazamentos entre lojas; aceitar somente modelo que passe gates ainda [R].
- STT: áudio consentido e sintetizado em pt-BR com ruído/sotaque, números e nomes fictícios; taxa de erro de transcrição e identificação de baixa qualidade.
- TTS: pronúncia, naturalidade, inteligibilidade, ritmo e tamanho do arquivo/latência para upload Meta; confirmar texto falado e configuração de voz.
- Execução: custo por caso resolvido, tokens, duração, retries, taxa de falha, tempo de resposta; limites e orçamento aprovados antes de chamadas pagas.
- Comparar rota direta versus n8n pelo documento OAI-04 **depois** da avaliação conceitual; escolha de modelo não depende de contratar n8n.

**Critérios quantitativos ainda [R]:** pesos de qualidade por tarefa, limites de falso preenchimento, latência, máximo custo e texto/voz padrão. Sem avaliação empírica, não declarar "melhor modelo" com base em marketing ou preço isolado.

## 7. Testes candidatos [P] — sem execução

- VOZ-T01: mensagem de voz curta pt-BR elegível → transcrição com fonte; resposta curta aprovada → áudio vinculado ao texto exato.
- VOZ-T02: caso muda para humano durante STT/TTS → nenhuma resposta de IA publicada e nenhum reativamento.
- VOZ-T03: mensagem de cliente com promessa de taxa/resultado inexistente → mensagem de voz não publicada.
- VOZ-T04: áudio não permitido, corrupto ou mídia expirou → falha segura, nenhum cadastro inventado.
- VOZ-T05: transcrição com numeral ambíguo → extrator exige revisão/ausência para campos relevantes.
- VOZ-T06: prova de sintonia texto aprovado ↔ áudio, sem informação comercial suplementar por improviso.
- VOZ-T07: duas lojas com mesmo cliente → mídia, contexto e resposta completamente segregados.
- VOZ-T08: artefato e logs não expõem credenciais, mídia bruta, áudio de cliente ou transcrição fora da política.
- VOZ-T09: formato/codec/duração/tamanho alvo Meta conforme contrato PR #2; a frente OpenAI não implementa Graph nem sua validação final.
- VOZ-T10: saída em áudio com confirmação de que é conteúdo automatizado segundo política aprovada [R/V].

## 7A. Preferência contextual de mídia [D-NEGÓCIO/P]

Em 18/10/2026 o responsável esclareceu que o assistente deve adaptar texto/áudio a pedidos expressos do cliente e ao padrão recente **reiterado**, sem thresholds artificiais antecipados. Uma mensagem de voz isolada NÃO prova preferência habitual. Áudio ocasional pode ser apropriado mesmo para quem escreve mais, sem forçar a interpretação de que o cliente passou a preferi-lo. O modelo propõe modalidade e motivo; S0 valida permissão de falar, eventual solicitação de texto, custo, adequação do conteúdo, handoff e canal. **Pedido explícito para usar texto tem precedência** sobre inferência de áudio. Toda mensagem de voz deve revelar identidade automatizada conforme política aprovada, não simular pessoa real. Depois de handoff humano, nenhum TTS de resposta da IA. Detalhes e casos NC-06/07/08 no OAI-07; heurísticas de frequência e fallback permanecem [R].

## 8. Fontes e precedência

Internas: documentos 06 (IA, áudio e pendências), 11 (arquitetura), 24 e 26 (conversa e handoff), 28 e 33 (privacidade), PR #1 e PR #2 (fronteiras).
Externas (documentação de fabricante consultada em 18/10/2026):
- Structured Outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- Modelo catálogo: https://developers.openai.com/api/docs/models
- Audio transcription: https://developers.openai.com/api/docs/guides/speech-to-text
- TTS: https://developers.openai.com/api/docs/guides/text-to-speech
- Realtime (não adotado): https://developers.openai.com/api/docs/guides/realtime

**Conclusão do E01 para mídia/modelos:** capacidades e interfaces especificadas como [P]; nenhuma chamada feita ou modelo escolhido. Testes de E02–E07 seguem pendentes.
