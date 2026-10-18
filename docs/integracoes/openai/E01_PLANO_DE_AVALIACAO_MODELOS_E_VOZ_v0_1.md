# E01 — Plano de avaliação de modelos e áudio OpenAI | v0.1

**Data:** 18/10/2026 | **Estado:** [P] shortlist metodológica, sem escolha vinculante de modelo, preço, voz ou arquitetura. Sem chamada de API, consumo ou resultados de benchmark. Complementa E01_CONTRATO_FUNCIONAL_MULTI_CAPACIDADE_v0_2.md.

## 1. Uma tarefa ≠ um modelo obrigatório

| Capacidade funcional | O que avaliar | Candidatos documentados em 18/10/2026 (não aprovados) | Saída/critério principal |
|---|---|---|---|
| F01 — IA Vendedora texto | Naturalidade em pt-BR, instruções comerciais, escopo, recusa de promessas, latência e custo | Modelos de texto Responses, p.ex. `gpt-6-luna` / `gpt-6.1-sol` / `gpt-6-astra` — confirmar acesso/preço na organização antes de testar | Proposta C03 e handoff sem inventar informações |
| F02 — Planejadora de recontatos | Seleção apenas de templates pré-aprovados, cumprimento dos limites e políticas sem escrita direta | Mesma família de modelos de texto sob teste; não presumir modelo único | Plano C05 validável por S0 |
| F03 — Extração após atendimento humano | Fidelidade, proveniência por mensagem, valores explícitos, faltantes/conflitos, Structured Outputs, custo por volume de histórico | Começar pelo candidato eficiente `gpt-6-luna`, comparar `gpt-6.1-sol` e escalar para `gpt-6-astra` se evidências mostrarem necessidade | Campos válidos, recusas de suposições e persistência somente pelo stub S0 |
| F04 — Gerar áudio de mensagem | Entonação pt-BR, pronúncia de Prumo/LiberaCred/Marca A, clareza, custo, latência, formato e divulgação de voz sintética | `gpt-4o-mini-tts` como candidato de TTS; avaliar suporte atual antes do laboratório | Áudio de conteúdo previamente autorizado, referência segura; não envio Meta |
| F05 — Transcrever áudio recebido | Acurácia de sotaques brasileiros, motocicletas/modelos, números sensíveis, ruído, pausas e incerteza | `gpt-4o-transcribe` e `gpt-4o-mini-transcribe`; comparar conforme custo e erro | Texto com fonte/caveats, sem afirmação de certeza indevida |
| Conversação falada contínua (futuro) | Se surgir exigência real de streaming, interrupção, turnos e chamadas de ferramentas | GPT-Live/Realtime como ARQUITETURA ALTERNATIVA futura, não pressuposta para áudios de WhatsApp | Decisão separada; só incluir se requisitos demonstrarem necessidade |

A shortlist é ponto de partida para ensaio — NÃO é aquisição, homologação nem promessa de acesso. Preferir testar uma configuração por tarefa com controle de versão de modelo/prompt, nunca usar o preço isolado para selecionar.

## 2. Formatos, métricas e método

- **Texto comercial:** conjunto sintético com conversa simples, objeção, informação desconhecida, solicitação fora de escopo, handoff enquanto modelo responde, variações de linguagem e opt-out. Avaliar aderência, segurança e naturalidade com rubrica auditável.
- **Extração F03:** dataset sintético rotulado, com anotações explícitas por mensagem; avaliar precisão por campo, omissão correta quando ausente, conflitos detectados, fonte certa, extrapolação indevida, respeito aos campos permitidos, custo e p50/p95 de latência. Dados críticos exigem limite de erro mais conservador, a aprovar antes de testar. Nunca inferir documento/CPF/renda.
- **Structured Outputs:** avaliar suporte a JSON Schema com versão, enum de operação, campos e `additionalProperties:false`; validação de forma **não** prova veracidade semântica. Testar recusa e conteúdo truncado.
- **TTS F04:** vozes e tons autorizados, audição humana em português brasileiro para números, nomes de motos e pausas; medir clareza/inteligibilidade e divergência entre texto aprovado e áudio ouvido. Verificar formato real aceito pela Meta antes de trânsito. Por padrão OpenAI TTS pode retornar MP3, Opus ou WAV; não supor que codec/contêiner específico passa no WhatsApp sem teste. Deve ser sinalizado ao usuário final quando voz for produzida por IA conforme políticas OpenAI.
- **STT F05:** pares sintéticos áudio/transcrição de referência, ruídos/acento, nomes próprios e números: comparar taxa de palavras erradas, troca de valores numéricos, cortes e conteúdo inventado; marcar incerteza e pedir confirmação humana para dados críticos.
- **Privacidade:** qualquer gravação de teste real com pessoas, ainda que a conversa seja simulada, depende de controle/consentimento aplicável; preferir voz sintética para primeiro benchmark. Antes de dados reais avaliar processamento por fornecedor e retenção [V/R].
- **Custos:** coletar tokens, segundos de áudio, tempo, armazenamento/reprocessamento e operações em cada abordagem, com preços do dia e volume projetado; orçamento teto depende de aprovação expressa. Não informar preços fictícios.

**Critérios de aprovação:** previamente aprovados por responsável, a registrar em `MATRIZ_BENCHMARK_MODELOS_E_VOZ` ou instrumento análogo; não usar pontuações inventadas. As métricas não foram executadas e os thresholds finais permanecem [R].

## 3. Arquitetura de áudio mais simples para testar PRIMEIRO [P]

Para WhatsApp assíncrono, uma alternativa controlável é:
- Mensagem de voz recebida: **Meta** autentica/armazena/encaminha referência segura → **S0** autoriza conteúdo e finalidade → **OpenAI F05** transcreve → **S0** verifica origem e disponibiliza texto ao fluxo competente.
- Resposta de áudio gerada: **S0** valida proposta de texto F01, inclusive permissão de falar → **OpenAI F04** sintetiza áudio → **S0** revalida autorização e cria intenção → **Meta** prepara transporte/mídia e envia quando elegível.

Esse pipeline favorece auditabilidade do texto e mantém responsabilidade existente de Meta/S0, mas precisa ser testado. Não fica aprovado por esta especificação. Arquitetura Realtime/GPT-Live faria sentido para voz com turnos em tempo real; enviar/receber áudios assíncronos no WhatsApp não exige isso por definição.

## 4. Testes específicos de escolha

- M-01: mesmo caso sintético, 2–3 modelos de texto, instruções idênticas, rubrica e custo comparáveis.
- M-02: campo omitido vs inventado em 100% dos casos adversariais de referência; qualquer erro crítico reprova configuração até revisão, sem afirmar que risco é eliminável.
- M-03: mensagem contraditória, correção pelo cliente e nota especulativa do operador -> F03 gera fontes/motivos coerentes e S0 decide aplicação.
- M-04: resposta IA concluída depois de handoff -> texto e áudio cancelados.
- M-05: 2–3 vozes pt-BR com conteúdo fixo autorizado -> avaliação auditiva humana e compatibilidade técnica com mídia.
- M-06: STT com números e sotaques variados -> marcar incerteza e proteger ficha contra preenchimento indevido.
- M-07: comparação de custo e latência (p50/p95) sobre amostras equivalentes; sem inferir rendimento de um caso isolado.
- M-08: falha do TTS após texto aprovado -> não entregar texto como se fosse áudio enviado; S0 escolhe comportamento seguro.
- M-09: retenção/segredos/logs e revisão de permissões para cada endpoint.
- M-10: revisão humana da matriz e decisão por **tarefa**, com IDs/snapshots de modelos, não por preferência pessoal.

## 5. Fontes técnicas públicas verificadas em 18/10/2026

- Modelos de texto atuais: https://developers.openai.com/api/docs/models
- JSON estruturado: https://developers.openai.com/api/docs/guides/structured-outputs
- TTS: https://developers.openai.com/api/docs/guides/text-to-speech
- STT: https://developers.openai.com/api/docs/models/gpt-4o-transcribe
- Áudio em geral: https://developers.openai.com/api/docs/guides/audio
- Pipeline vs Realtime: https://developers.openai.com/api/docs/guides/voice-agents

**Estado:** shortlist e testes definidos documentalmente; nenhum modelo/voz aprovado, nenhuma avaliação experimental concluída. Escolha n8n × direto é independente e continua [R] (OAI-04).
