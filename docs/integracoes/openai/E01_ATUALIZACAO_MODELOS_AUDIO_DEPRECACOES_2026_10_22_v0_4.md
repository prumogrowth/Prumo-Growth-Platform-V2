# E01-AUDIO v0.4 — Revisão da shortlist de modelos, descontinuações e ensaio de voz

**Data de verificação externa:** 22/10/2026. **Classe:** [V] fatos na documentação pública da OpenAI, revalidáveis; [DN] separação F01/F02/F03 e STT/TTS auxiliares; [P/R] desenho de pipeline e seleção. **Não** há escolha aprovada de modelo, chamada à API, avaliação de preço/desempenho, criação de projeto/secret, gasto ou implementação. Esta revisão atualiza a leitura do plano histórico `E01_PLANO_DE_AVALIACAO_MODELOS_E_VOZ_v0_1.md`, sem eliminar sua trilha.

## 1. Achados oficiais que mudam a preparação

| Tema | Estado informado na documentação consultada em 22/10 | Implicação para nossa frente |
|---|---|---|
| F04 — TTS | `gpt-4o-mini-tts`, `tts-1` e `tts-1-hd` estão marcados como **deprecated**, com desligamento anunciado para **06/01/2027**. O guia direciona migração para **`gpt-realtime-2.1-mini` na Realtime API**; avisa que este modelo **não** é suportado em `/v1/audio/speech`. | **Não** fixar `gpt-4o-mini-tts` como escolha arquitetural de longo prazo nem supor troca direta de `model` no endpoint antigo. Reavaliar custo, protocolo, geração assíncrona, formatos e controle de aprovação S0 antes de decidir. |
| F05 — STT | Guia de transcrição de arquivo recomenda **`gpt-transcribe`** para fala gravada. `whisper-1`, `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, `gpt-4o-transcribe-diarize` e `/v1/audio/translations` constam como **deprecated** com desligamento anunciado para **26/02/2027**. | Priorizar **avaliação documental de `gpt-transcribe`** para áudio de WhatsApp gravado; candidatos antigos podem servir apenas como referência histórica, não dependência de nova arquitetura. |
| Modelos de texto | Catálogo vivo e orientações de Structured Outputs são atualizáveis; suporte, disponibilidade por projeto e API são próprios da data de verificação. | F01/F02/F03 precisam de decisão **por tarefa**, com snapshot do ID de modelo no projeto na hora do teste e schema ratificado; nomes históricos da shortlist não são contratação nem prova de acesso. |
| Voz divulgada ao cliente | Guia de TTS exige divulgação clara de que a voz é produzida por IA, não voz humana. | Especificar experiência de aviso pelo canal/Prumo/Meta e revisão jurídica antes de áudio em produção. |

**Fontes oficiais consultadas:** [transcrição de áudio gravado](https://developers.openai.com/api/docs/guides/speech-to-text), [síntese de fala e aviso de descontinuação](https://developers.openai.com/api/docs/guides/text-to-speech), [catálogo de modelos](https://developers.openai.com/api/docs/models), [saídas estruturadas](https://developers.openai.com/api/docs/guides/structured-outputs).

**Regra de atualidade:** datas e modelos podem sofrer novas alterações. Revalidar o aviso oficial e o endpoint **imediatamente antes de E04/E05**, com captura da versão/documentação e comentário de revisão. Este documento não pretende garantir que modelos novos estejam disponíveis na organização/conta da Prumo.

## 2. Decisão arquitetural ainda aberta para áudio assíncrono [P/R]

Fluxo obrigatório do negócio continua **Meta recebe mídia → S0 autentica e autoriza → F05 transcreve fonte permitida → S0 valida origem → F01 ou humano elegível**, e na saída **F01 propõe texto → S0 aprova publicação → F04 gera áudio técnico → S0 revalida handoff/estado → Meta transporta**. A rota Realtime indicada pela documentação é um **meio técnico possível**, não permissão para conversar ao vivo, nem razão para integrar voz ao F01 como um agente conversacional sempre ativo.

**Comparar no desenho técnico antes de escolher:**
1. Capacidade de gerar **um único arquivo/trecho aprovado**, fora de conversação contínua, com **isolamento por requisição** e encerramento de sessão; investigar formato de mídia entregue e conversão permitida pela Meta.
2. Segurança da fronteira de texto: somente texto F01 **previamente aprovado** vira voz; a síntese não cria preço, promessa, dado do Banco ou contato extra.
3. Custos (áudio/tokens/sessões), latência, retries, idempotência, falha/timeout e recepção de mídia; tratar recurso de sessão como dado técnico sujeito a retenção.
4. Comprovação de **integridade** por inspeção humana de português brasileiro, valores numéricos e nomes comerciais fictícios; áudio divergente bloqueado.
5. Não abrir conversação Realtime bidirecional com cliente por conveniência. Arquitetura deve satisfazer WhatsApp assíncrono e Meta/S0 aprovados.

**O que não foi decidido:** TTS definitivo, modelo de texto, STT definitivo, pipeline Realtime, n8n, codec/contêiner final, voz ou preço; não especificar endpoint funcional sem aprovação da frente.

## 3. Plano comparativo por capacidade [P/R]

| Capacidade | Hipótese de estudo | Matriz mínima antes da contratação |
|---|---|---|
| F01 texto | Comparar candidatos disponíveis no projeto com instruções globais + comportamento global F01; **nunca prompt local**. | Naturalidade pt-BR, escopo tenant, conteúdo bancário aprovado, handoff irrevogável, texto e preferência de áudio |
| F02 planejadora | A mesma família de modelos **não** implica mesmo preço/competência. | Só template+versão+finalidade filtrados da loja, limites, nenhum slot preenchido ou envio, pedido S0 separado pós-humano |
| F03 extratora | Contexto histórico completo autorizável, mas **não** cabe obrigatoriamente num único prompt; pode haver recuperação em etapas. | Proveniência multi-casos da mesma loja, optional e essential, conflitos temporais, cutoff, resultado em schema, recheck S0 |
| F04 áudio | **Evitar dependência nova no endpoint TTS depreciado**; estudar o fluxo de áudio atualmente suportado na documentação da data de execução. | Texto autorizado → áudio auditável → S0 recheck → Meta; sinalização de IA e tipos/codec permitidos |
| F05 transcrição | Investigar `gpt-transcribe` como ponto de partida para mensagens gravadas. | Sotaque/números/ruído e incerteza, direitos sobre mídia/retenção, proveniência, custo e latência; sem preencher ficha automaticamente |

## 4. Regressão E02 que precisa de nova revisão

- **SYN-21/22/23:** áudio recebido claro/incerto/indisponível; a transcrição com `gpt-transcribe` é **hipótese**, não valor real.
- **SYN-24/25/26:** geração de ativo técnico, mudança de permissão durante síntese e integridade comercial. As expectativas funcionais **não mudam**; varia o mecanismo técnico do provedor.
- **M-05/M-06/M-08/M-09** do plano antigo: atualizar modelo/endpoint antes do benchmark; medir token/sessão/formato com autorização.
- **AUD-DEP-01 [P]:** cenário documental de descontinuação do endpoint antigo não deve causar fallback silencioso nem áudio falso como enviado.
- **AUD-DEP-02 [P]:** quando nova rota de áudio exige sessão Realtime, o backend não pode conceder fala ao F01 após handoff, nem manter sessão capaz de atingir outro tenant.
- **AUD-DEP-03 [P]:** mídia original sem direito de uso ou já indisponível não pode ser reconstruída por STT.

**AUD-DEP-01..03 são verificações futuras adicionais, não membros de SYN-01..70, nem testes executados.** Não usar contagem para inflar a cobertura validada. O dono Meta/S0 deve ratificar a mídia/codec/transporte; OpenAI não edita branch Meta.

## 5. Gate de decisão

A escolha por F04/F05 fica **PENDENTE [R/V]** até: documentação oficial revalidada; permissão e disponibilidade do modelo no projeto API real da Prumo; contrato de mídia e privacidade aprovado; envelope tipado S0 aprovado; custo/teto por rodada aceito; métricas e rubrica por tarefa congeladas; **autorização expressa E04/E05 no seu estágio**.

**Status final:** revisão documental de fornecedor realizada, mudança na shortlist sinalizada; 70 SYN continuam documentais, **0 executados**. Não criar chave, billing, chamada paga, sessão Realtime, deploy ou runtime n8n por este texto.
