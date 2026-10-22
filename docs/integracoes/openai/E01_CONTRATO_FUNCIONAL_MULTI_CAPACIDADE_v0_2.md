# E01 — Contrato funcional S0 ↔ OpenAI, multicaptacidade | v0.2

> **Versão operacional posterior:** [E01_CONTRATO_FUNCIONAL_OPERACIONAL_v0_3.md](./E01_CONTRATO_FUNCIONAL_OPERACIONAL_v0_3.md) — candidata [P/R] de 22/10/2026, coerente com AL-IA. O presente arquivo permanece **histórico** para rastreabilidade; em divergências não aplicar sua redação anterior. A nova versão não equivale a aceite físico S0, testes ou implementação.


> **AVISO DE PRECEDÊNCIA — AUDITORIA DA FRENTE OPENAI, 22/10/2026.** Este documento anterior permanece preservado como **contrato candidato/histórico**; trechos conflitantes **NÃO são a direção funcional vigente**. Ler primeiro [AL-IA-00 — índice e precedência](./ALINHAMENTO_2026_10_22_00_INDICE_E_PRECEDENCIA_v0_1.md), [AL-IA-01 — jornada](./ALINHAMENTO_2026_10_22_01_JORNADA_F01_F02_F03_v0_1.md), [AL-IA-04 — deltas](./ALINHAMENTO_2026_10_22_04_RASTREABILIDADE_DELTAS_PENDENCIAS_v0_1.md), [AL-IA-07 — dependências entre frentes](./ALINHAMENTO_2026_10_22_07_DEPENDENCIAS_RELEVANTES_OUTRAS_FRENTES_v0_1.md) e [AL-IA-08 — auditoria documental](./ALINHAMENTO_2026_10_22_08_AUDITORIA_FECHAMENTO_DOCUMENTAL_FRENTE_OPENAI_v0_1.md). O texto abaixo documenta o estado de sua data original, **sem emendar código, criar autorização S0, nem corrigir documentação de outras frentes**.
>
> **Atenção especial:** operações, exemplos e parâmetros aqui são candidatos datados; as instruções atuais são quatro campos globais (F01 instruções+comportamento; F02 e F03 instruções distintas), sem versões por concessionária. F03 consulta histórico lógico integral até o corte; Consultor não corrige campos da ficha; transições permitidas podem resultar de F03 via S0, nunca `vendido`.


**Data:** 18/10/2026 | **Estado:** [P] contrato candidato detalhado para revisão com S0; requisitos novos informados pelo responsável em 18/10/2026, consolidação interfrentes [R]. **Sem endpoints, prompts ou código implantados**. Este documento não substitui as decisões normativas 13A/21/22/23/41; onde houver alteração de prática, registrar delta e solicitar validação aos donos.

## 0. Resultado de negócio e limites

A frente OpenAI possui funcionalidades técnicas distintas que compartilham segurança e chamada ao provedor, mas **não** compartilham autorização de ação:
- **F01 Vendedora:** sugerir mensagem durante posse IA do caso, operação conceitual C03.
- **F02 Planejadora de recontato:** sugerir somente versões preexistentes de templates autorizados, C05.
- **F03 Extratora pós-atendimento humano — NOVA DIREÇÃO FUNCIONAL informada pelo responsável [D-direção, R-contrato de integração]:** depois de o operador encerrar seu atendimento humano na plataforma, a OpenAI lê APENAS a conversa e as mídias transcritas autorizadas daquele caso, identifica dados que o cliente informou e devolve proposta estruturada para **preenchimento automático da ficha pelo backend S0**. A digitação rotineira pelo operador não é etapa do fluxo; o operador conversa, conclui atendimento e confere resultado quando apropriado. Não inventar fatos ausentes. Opera mesmo que IA Vendedora esteja permanentemente silenciada.
- **F04 Áudio de saída:** transformar texto de resposta comercial autorizado em áudio para envio futuro via adaptador Meta; não envia por conta própria.
- **F05 Áudio de entrada:** transcrever/interpretar áudio recebido, retornando conteúdo com provenance e incerteza para contextos autorizados; não determina sozinho estado ou campos.
- **F06 Avaliação de modelos:** testar qualidade/custo/latência por tarefa; modelo e versão escolhidos por governança humana [R].

A extração pós-humano NÃO é IA Analista autônoma; não cria regras, não corrige software, não muda prompts nem gerencia automações. Não é retomar conversa automatizada. Não criar nono estado comercial nem botão/UI nesta branch.

### Compatibilização normativa obrigatória

- Doc 23 [D]: cadastro entregue pela IA como `cadastro enviado ao operador` deve ser completo segundo lista-mestre FUTURA; correção humana individual excepcional continua permitida; IA Vendedora não volta a falar; nenhuma suspensão/autorreparo automático. Novo F03 **não** afrouxa essa regra de handoff IA→humano.
- Docs 24/40 [P]: O3 continua espaço de visualização, conferência e correção pontual, com C13 para correção humana, sem exigir que operador digite rotineiramente campos obtidos da conversa. A UI, registro de conclusão e schema físico pertencem ao S0.
- Doc 26 [P]: C03 `campos_extraidos[]` ao longo do atendimento IA e C13 correção humana existem como CANDIDATOS, mas **não cobrem completamente** o gatilho fim do atendimento humano + extração + persistência automática. F03 requer contrato NOVO, sem reaproveitar C13 de modo a falsificar autoria humana.
- Doc 41 [D]: permissões de leitura/conferência do operador/gestor e escopo loja/caso seguem vigentes; output da OpenAI não concede acesso novo.
- Normas bancárias: remessa comprovada e desfecho do Banco continuam atos autorizados e evidenciados, sem status/venda/recusa inferidos pelo modelo.

### Governança dos nomes e referências de interface [P/R]

Os nomes técnicos `human_close_extract`, `speech_synthesize` e `speech_transcribe` são os **mesmos usados nos contratos específicos OAI-05 e OAI-06** já presentes nesta branch. Os termos descritivos “extração pós-humano” e “gerar áudio” não são novos valores de enum; renomear futuramente exige revisão cruzada. A versão ilustrativa `s0-openai.v0.1-proposed` permanece CANDIDATA, não endpoint já implantado. Este arquivo organiza as capacidades; **OAI-05 detalha o contrato de extração e OAI-06 detalha o contrato de voz**. Na eventual divergência de campo técnico entre dois exemplos, não inferir aprovação — registrar [R] e padronizar com S0/Meta antes de implementação.

## 1. Fronteiras de responsabilidade

| Responsável | Permanece dono de | Esta frente oferece |
|---|---|---|
| S0 / PR #1 | Autenticação, autorização por concessionária/atribuição, evento técnico de conclusão humana, versão do caso, mensagens, ficha, validação por campo, persistência, fila, status, handoff, regras banco, outbox e auditoria de domínio | Tipos e semântica de pedidos/respostas OAI, com validação exigida do lado S0; nunca alterações unilaterais no PR #1 |
| Meta / PR #2 | Inbound/outbound WhatsApp, webhook, mídia, formatos e upload/download, correlação/deduplicação e entrega | Texto proposto, ou referência a áudio gerado **sem enviar**, e resultado de transcrição quando autorizado; sem Graph API nesta branch |
| Responsável humano | Conta/chave OpenAI e inserção MANUAL de segredo; custo, decisões de modelos, critérios de liberação | Procedimento, testes, comparativos e evidências sanitizadas |
| OpenAI / PR #3 | Adaptador de protocolo de provedor, prompts versionados sob governo, extração proposta, TTS/STT, erros, métricas e testes sintéticos | Não cria/muda telas, SQL, RLS, workers S0, jobs Meta, rotinas n8n ou status comerciais |

## 2. Envelope mínimo, agnóstico à topologia [P]

```json
{
  "contract_version": "s0-openai.v0.1-proposed",
  "request_id": "req-ficticio-001",
  "operation_kind": "human_close_extract",
  "scope": {
    "concessionaria_ref": "loja-ficticia-A",
    "caso_ref": "caso-ficticio-7",
    "conversa_ref": "conv-ficticia-2",
    "ciclo_ref": "ciclo-ficticio-3"
  },
  "expected_case_version": 14,
  "trigger_ref": "evt-fim-atendimento-ficticio",
  "authorized_context_ref": "ctx-ficticio-minimo-7",
  "context_version": 5,
  "fields_policy_version": "campos-sinteticos-v0",
  "prompt_policy_version": "prompt-f03-v0",
  "provider_policy_ref": "modelo-por-tarefa-pendente",
  "deadline_ref": "prazo-servidor"
}
```

**Contrato lógico, não payload de API pública implantada.** IDs são opacos e correlacionados pelo backend, não dados pessoais; `trigger_ref` obrigatório apenas para F03. O gateway verifica legitimidade do ator do domínio, loja, finalidade, versão, posse do caso e allowlist de campos. Jamais aceitar referências enviadas pelo cliente como prova de permissão. F04/F05 usam referências seguras para conteúdo/mídia, não blobs pessoais em logs.

## 3. F03 — Extração pós-atendimento humano: contrato candidato [P]

### Gatilho

1. **S0** registra evento técnico `atendimento_humano_concluido` para o caso atribuído, com ID opaco, autoria humana, horário, `expected_case_version`, `snapshot_mensagens_ref` e eventual `cadastro_versao_ref`; nomes finais [R].
2. Essa conclusão é **evento de workflow, não um nono status comercial**. `em atendimento pelo operador` e os marcos bancários seguem governados por regras próprias. A conclusão não presume remessa/venda e não reabre IA Vendedora.
3. **S0** autoriza F03 exclusivamente para as mensagens DAQUELE caso/loja até o corte do snapshot, com respeito a permissões, finalidade, opt-out/privacidade, mídia/transcrições permitidas e política da lista-mestre. A conversa íntegra só será enviada ao modelo se justificada e aprovada; preferir trechos mínimos com IDs de mensagens.
4. O adaptador chama provedor compatível com **Structured Outputs** e retorna proposta de campos, pendências e contradições, SEM acesso a tabela ou ferramenta de escrita S0.
5. **S0** valida cada valor contra allowlist, tipagem, fontes de conversa, regras de obrigatoriedade, versão, conflito com dados existentes, grau de incerteza, permissão e finalidade. **Aplica automaticamente os campos elegíveis** em nova versão auditada da ficha, sob autoria técnica `processo_openai_pos_humano` e ID de execução correlacionado — **não falsifica autoria como operador**.
6. Campos ausentes, incertos, conflitantes, protegidos ou sem evidência NÃO são inventados nem persistidos como declaração factual. Permanecem `pendente`/indisponíveis para esclarecimento pelo humano, segundo política S0 a definir [R].
7. Operador vê ficha preenchida e indicadores de pendências; pode corrigir pontualmente via C13, sem reabrir IA Vendedora. Sem confirmação humana obrigatória a cada campo **por padrão proposto**, mas dados sensíveis/inconsistentes podem requerer validação adicional por classe de campo [R/V].
8. Retries e reprocessamentos têm ID e versão idempotentes: execução duplicada não duplica versões; mensagens humanas novas exigem novo snapshot e nova autorização [R]. Erro do modelo nunca elimina valores existentes nem muda resultado comercial.

### Saída canônica [P]

```json
{
  "contract_version": "s0-openai.v0.1-proposed",
  "request_id": "req-ficticio-001",
  "operation_kind": "human_close_extract",
  "trigger_ref": "evt-fim-atendimento-ficticio",
  "context_version": 5,
  "fields_policy_version": "campos-sinteticos-v0",
  "extraction": {
    "field_suggestions": [
      {
        "field_key": "preferencia_moto_exemplo",
        "value": "modelo-ficticio",
        "evidence_refs": ["msg-ficticia-005"],
        "source_kind": "customer_statement",
        "certainty": "explicit"
      }
    ],
    "missing_field_keys": ["campo_sintetico_pendente"],
    "conflicts": [],
    "needs_human_clarification": true
  },
  "proposed_effect": "validate_then_apply_by_s0",
  "warnings": []
}
```

**Atenção:** `preferencia_moto_exemplo` é CAMPO SINTÉTICO ilustrativo, não lista-mestre de cadastro aprovada; `modelo-ficticio` não é oferta real. `certainty` não substitui verificação de prova nem autorização. O backend aceita somente field_keys contempladas em catálogo de versão aprovada e não copia literalmente `warnings` para comandos executáveis.

### Casos-limite [P]

- Cliente não informou dado → `missing_field_keys`; nunca preencher com palpite ou informação de outra loja.
- Cliente informa dois valores contraditórios → `conflicts` com IDs de evidência, solicitar revisão; não selecionar arbitrariamente.
- Operador descreve hipótese ou sugere um valor, mas cliente não confirma → não apresentar como declaração confirmada do cliente.
- Declarações do operador sobre informação já validada podem ser fonte distinta, **somente se política específica permitir**; não converter anotação interna em consentimento/prova de cliente.
- Cliente fala por áudio → só usar transcrição permitida, com referência ao objeto/mensagem, confiabilidade e necessidade de confirmação quando crítico; não supor que transcrição é literalmente exata.
- Conversa da IA antes do handoff + conversa humana depois → incluir apenas trechos autorizados do mesmo caso; identificar quem disse o quê. Nunca retomar a IA Vendedora.
- Caso encerrado com ficha incompleta → pendência interna técnica/operacional, NÃO `cadastro enviado ao operador` nem `cadastro enviado ao banco` por esse motivo. Resolver com regra de S0, não novo status.
- Venda/recusa informada pelo cliente ou pelo modelo → NÃO criar `vendido` ou `perdido`; prova e comando humano continuam exigidos.
- Provedor atrasado e operador corrige manualmente antes do retorno → rejeitar resultado obsoleto; não sobrescrever a correção.

### Delimitação adicional: novo caso humano após `vendido` [D/P/R]

A decisão ATD-VENDIDO-RET-01 do doc.22 [D] determina que retorno espontâneo do cliente após `vendido` histórico abra/vincule **atendimento humano novo** e preserve a venda anterior. **F03 só deve processar o novo atendimento quando houver conclusão autenticada e snapshot próprio do novo caso; não usar automaticamente valores do ciclo vendido ou classificar atendimento de suporte como nova negociação.** `conversational_assessment` pode identificar falta de finalidade comercial, mas enum físico depende de aceite [R]. Um resultado F03 nunca cria novo ciclo bancário.

A existência de `vendido` histórico não autoriza F02 para prospecção de novo contrato. Uma cadeia eventual depende de novo objeto/finalidade e autorização S0 expressas, ainda [R/V]. Caso em fila protegida ou com operador revogado não devolve fala à IA Vendedora nem autoriza envio; S0/S1 são donos de atribuição e revalidação. Ver OAI-08 adendo e [E02 rastreabilidade](E02_RASTREABILIDADE_CF_OP_02_v0_1.md), PV-01..05 (textuais, não executados). Nenhum nono status ou interface física é proposto.

## 4. F01 e F02 — contratos existentes mantidos

- `sales_reply` (C03): entrada com case/cycle/knowledge/version/messages refs autorizados; saída texto proposto + campos extraídos com proveniência + possível motivo de handoff. O modelo não envia; S0 valida e cria intenção de envio C03 para a Meta. **Somente se IA Vendedora detém atendimento, jamais depois do handoff**.
- `recontact_plan` (C05): selecionar janelas/intervalos e somente IDs/versões de templates apresentados como ELEGÍVEIS pela S0, sem criar textos nem enviar. S0 decide agendamento e cancelamento.
- `human_close_extract` (NOVO F03): permitida após conclusão humana mesmo com flag `aiSuspended=true`, pois se trata de **processamento documental sem mensagens ao cliente**. Separar politicas técnicas `aiSellerCanSpeak` e `internalExtractionAuthorized`, ambas derivadas por S0, sem relaxar a primeira. Não dar ao modelo prerrogativa de reabrir sessão comercial.

## 5. F04 e F05 — porta de áudio [P]

### Saída de áudio `speech_synthesize` (F04)

S0 autoriza previamente **texto comercial exato** e o propósito do áudio. Entrada candidata: `request_id`, `case_ref`, `approved_text_ref`, `text_hash`, `voice_policy_version`, `locale=pt-BR`, `voice_ref` e `requested_media_profile` sob política aprovada. Adaptador solicita TTS ao provedor, recebe áudio e devolve `asset_ref` seguro, `text_hash`, `mime_type/codec`, `duration_ms` (se disponível) e métricas técnicas. **Não gera textos comerciais alternativos no estágio TTS**, nem envia WhatsApp, nem assume compatibilidade final com formato Meta.

S0 revalida possibilidade de responder, status/handoff e texto antes de criar intenção na outbox. **Depois do handoff humano, a IA Vendedora não pode gerar áudio como se ainda estivesse atendendo**. O transporte e a conversão de mídia para o formato final aceito pelo WhatsApp são responsabilidade/contrato da Meta; divisão exata do transcode [R]. Reter mídia temporária apenas sob política [R/V]; não gravar bruto no núcleo por padrão.

### Entrada de áudio `speech_transcribe` (F05)

Meta recebe/valida mensagem e disponibiliza referência segura à mídia, respeitando escopo por loja/caso. A frente OpenAI só transcreve quando S0 autorizar a finalidade. Retorno: `transcript_text` mínimo, `source_message_ref`, `language`, `transcription_model_ref`, `warnings`, `quality_flags` e estado técnico. Transcrição não prova identidade nem exatidão de CPF/número/valor. Validações de consentimento, retenção de mídia e restrições financeiras [R/V].

**Voz por WhatsApp não exige decidir Realtime de imediato.** Para mensagens assíncronas, primeiro avaliar pipeline texto → TTS para saída e áudio gravado → STT para entrada. Realtime/GPT-Live é candidato somente se houver requisito de conversa falada contínua [R]; não confundir formato WhatsApp com WebRTC.

## 6. Regras transversais de segurança, autoria e aplicação

1. **Autorização e tenancy:** S0 autentica e autoriza escopo; adaptador e provedor não decidem loja, concessão, perfil ou campos do cadastro.
2. **Separação de operações:** F01 pode propor fala; F03 nunca fala; F04 produz áudio sem enviar; F05 transcreve sem editar cadastro; F02 planeja sem executar.
3. **Sem tool calls de efeito comercial por default:** nenhuma instrução do texto do cliente/prompt injection permite SQL, Meta, Banco, MCP, tool de edição ou alterar parâmetros.
4. **Persistência por S0 com autoria técnica fiel:** somente S0 realiza atualização automática de campos autorizados após validação; trilha deve diferenciar `origem_cliente`, `origem_operador`, `origem_transcricao`, `extraido_pelo_modelo` e `persistido_pelo_backend`.
5. **Campos sensíveis:** lista-mestre ainda NÃO publicada [R]; CPF/documentos/dados financeiros e os canais permitidos dependem de Meta/Banco/LGPD [V]. Não inventar campos obrigatórios nem transmitir dados reais ao provedor até parecer/permissão.
6. **Falhas:** provedor indisponível ou versão obsoleta gera erro técnico/pendência interna e retentativa segura governada; não altera status, não reenvia áudio nem envia mensagem por conta própria.
7. **Custos e rastreabilidade:** medir por operação e modelo sem registrar segredos, conversa completa, mídia, extratos bancários ou dados pessoais em logs externos por padrão.
8. **n8n:** contrato é agnóstico (direto ou n8n [R]); nenhum orquestrador tem autoridade para contornar S0 nem hospeda credencial sem decisão de arquitetura e guarda manual do responsável.

## 7. Testes de aceite de E01 [P], ainda não executados

- E01-T01: distinção `sales_reply`, `recontact_plan`, `human_close_extract`, `speech_synthesize`, `speech_transcribe`; chamadas não podem ganhar privilégios cruzados.
- E01-T02: sem conclusão humana autêntica, F03 recusado; conclusão duplicada idempotente.
- E01-T03: F03 extrai campo de evidência explícita e S0 stub aplica versão com autoria do processo, sem digitação humana.
- E01-T04: campo ausente -> não preenchido; campo conflitante -> pendência, sem escolha inventada.
- E01-T05: fonte apenas anotação de operador sem política -> não vira declaração de cliente.
- E01-T06: mesmo contato loja A/B -> F03 não consulta nem persiste dados cruzados.
- E01-T07: `aiSuspended` bloqueia fala automática F01/F04, mas não F03 interno autorizado.
- E01-T08: correção humana concorrente ocorre antes do retorno F03 -> não sobrescrever versão.
- E01-T09: campos de lista-mestre não aprovados/sensíveis proibidos -> backend descarta, não tenta preencher.
- E01-T10: modelo informa venda/recusa -> nenhum novo status ou remessa; eventos continuam manuais com prova.
- E01-T11: áudios TTS exigem texto previamente validado; retorno com mime/codec inapropriado é retido/rejeitado antes da Meta.
- E01-T12: STT retorna texto e fonte, não valor probatório definitivo; áudios errados não criam dados no cadastro.
- E01-T13: prompts maliciosos e outputs não autorizados não obtêm tool write/MCP/cross-tenant ou segredo.
- E01-T14: timeout/retry/idempotência não geram versão duplicada, áudio duplicado nem mudança de status.
- E01-T15: custos e versões de modelo/provedor registrados com dados sintéticos; sem dados pessoais em logs.

## 8. Critério de fechamento de E01 e pendências

**E01 permanece EM REVISÃO [P/R]** até: (a) semântica de F03 e evidência do gatilho concluído aceitas pela frente S0, (b) nomes finais da porta e política de quem confirma dados críticos revisados, (c) contratos F04/F05 compatibilizados com Meta em nível de fronteira, (d) contrato/versionamento e esquema sintético aceitos, (e) decisões de dados/lista-mestre que forem bloqueantes explicitamente condicionadas. Não marcar E01 como concluído somente por publicação do presente arquivo.

**Fronteiras que esta branch NÃO implementa:** interface de operador, botão de concluir, tabela de cadastro, migrações SQL, RLS, remessa bancária, envio WhatsApp, Graph, gestão Meta e lógica comercial S0.

**Fontes internas:** docs 06, 11, 13A, 23, 24, 26, 33, 38, 40 e 41 do pacote documental auditado, contratos Draft do PR #1 e PR #2, OAI-05 e OAI-06 desta mesma branch.

**Fontes técnicas atuais:** https://developers.openai.com/api/docs/guides/structured-outputs ; https://developers.openai.com/api/docs/guides/audio ; https://developers.openai.com/api/docs/guides/text-to-speech ; https://developers.openai.com/api/docs/guides/voice-agents . Estas são bases de viabilidade, não teste nem seleção de modelo.


## Adendo CF-OP-02 — fronteira entre F02 e F03

**F03 / human_close_extract**: após conclusão humana, extrai ficha, avalia desfecho/compromisso e somente PROPÕE necessidade de recontato. **F02 / recontact_plan**: somente após pedido S0 válido, sugere a cadeia de templates pré-aprovados e agenda limitada, inclusive para caso humano pendente com janela expirada ou concluído inconclusivo; opção de um único template escolhido pelo operador é S0→Meta, NÃO chamada F02 obrigatória. Planejadora não fala com cliente, e resposta de caso humanizado vai ao operador autorizado atual. Ver [OAI-08](OAI_08_CONTRATO_PLANEJADORA_POS_HUMANA_CF_OP_02_v0_1.md). Contrato físico E01/OAI-05 ainda [R]; nenhum envio/status autorizado.
