# OAI-07 — Desfecho após atendimento humano, roteamento, avisos e preferência de canal | v0.1

**Data:** 18/10/2026 | **Origem:** esclarecimentos funcionais expressos por um responsável do projeto na presente conversa.
**Classificação:** [D-NEGÓCIO] intenção funcional explicada; [P] interfaces, eventos, tipos e fluxo candidato; [R] reconciliação com S0/Meta e atos comerciais normativos; [V] requisitos oficiais de remessa, tratamento de dados, Banco/Meta/LGPD. **NÃO é código implantado nem autorização para alterar estados comerciais.**
**Precedência:** docs 13A/21–23/41 (decisões normativas) > interfaces propostas 24/26/40 e OAI-01/05/06. Se a orientação nova divergir de uma decisão aprovada, declarar a tensão e não revogá-la silenciosamente.

## 1. Novas orientações funcionais informadas [D-NEGÓCIO]

1. **Fim do atendimento humano:** em QUALQUER handoff válido — solicitação explícita do cliente, assunto jurídico, dificuldade técnica/linguística, atendimento especializado ou falta de dados — o operador conduz a conversa e aciona um botão de **encerrar atendimento** ao terminar. O evento técnico de fechamento, de propriedade S0/UI, dispara análise silenciosa pela OpenAI. A IA Vendedora NÃO recomeça a conversar.
2. **Análise do desfecho:** nessa ocasião, o modelo deve identificar, COM evidência da conversa, se houve avanço de intenção comercial, conclusão sem avanço, desistência, venda apenas alegada ou resultado incerto, e a razão identificável. O objetivo funcional é dispensar a seleção manual rotineira “ganho/perdido/fechado” pelo operador **na interface do atendimento**. Porém, o modelo NÃO tem autoridade para converter hipóteses de conversa em venda bancária confirmada ou recusa definitiva; as duas operações continuam humanas por normas 13A/21/41 até decisão formal que as substitua.
3. **Extração extensiva:** preencher por processo S0 TODO campo do catálogo cujo valor tenha sido identificado de modo explícito, consistente, autorizado e verificável, mesmo se o campo NÃO for necessário à remessa; não limitar extração apenas aos campos exigidos pelo banco. Nenhum campo é inventado. A lista de campos e suas regras ainda não existe como catálogo final aprovado [R/V].
4. **Obrigatoriedade é distinta de disponibilidade:** S0 fornece versão do catálogo distinguindo `required_for_bank_submission` vs. `optional` e `auto_apply_allowed`. **Ausência de dados essenciais exigidos pelo Banco:** retornar ou manter o caso com humano para complemento, acompanhando aviso curto com nomes/códigos dos campos faltantes. **Ausência apenas de opcionais:** não devolver ao humano por esse motivo; seguir fluxo autorizado. Dados proibidos não são coletados via canal inadequado.
5. **Rota pós-análise:** se a conversa aponta continuidade e dados essenciais estão válidos, encaminhar para **remessa direta ao banco SOMENTE quando autorização, integração e prova de envio estiverem homologadas** [V/R]; até lá, remeter o caso ao operador responsável para a remessa humana comprovada, como estabelecido em 06/13A/21. A OpenAI jamais transmite ao Banco por conta própria.
6. **Resumo de motivo em todos os encaminhamentos IA → humano:** enviar aviso OPERACIONAL curto, contextual e acionável, com motivo adequado (`HUMAN_REQUESTED`, `LEGAL_OR_REGULATORY_TOPIC`, `REQUIRED_FIELDS_MISSING`, `UNRESOLVED_DATA_CONFLICT`, `PROVIDER_OR_QUALITY_ISSUE`, `BANK_SUBMISSION_REQUIRES_HUMAN`, `OTHER_REVIEW`). O operador vê resumo antes ou junto da atribuição. Mensagem é interna, **não enviada ao cliente**, sem copiar documentos D3/D4 ou incluir aconselhamento jurídico.
7. **Voz e preferência contextual:** a IA considera pedido explícito de texto/áudio, padrão RECENTE e REITERADO de mensagens de cliente, tipo de conteúdo e finalidade. Uma mensagem de voz isolada NÃO prova preferência persistente. Não fixar regra rígida “x áudios ⇒ sempre áudio”. Mesmo em conversa majoritariamente escrita, áudio ocasional pode ser proposto quando adequado, mas permanece sujeito a autorização, inteligibilidade e regras comerciais. Após pedido explícito `use_text` ou `use_audio`, respeitar preferência dentro das capacidades e das limitações técnicas/políticas. Nada de áudio da IA após handoff.
8. **Modelos por tarefa:** comparar precisão de extração/desfecho, geração comercial, STT e TTS; não escolher um único modelo antecipadamente. n8n permanece alternativa não decidida.
9. **Custo:** não há teto global de gasto previamente definido. Utilizar testes sintéticos offline antes de qualquer consumo; para cada lote real, apresentar previamente escopo, modelos, número aproximado de chamadas, estimativa em moeda e risco de ultrapassagem. **Gasto somente após autorização expressa daquele lote**; não interpretar ausência de limite fixo como orçamento ilimitado.

## 2. Fluxo proposto após clique em “encerrar” [P]

```
OPERADOR_FECHA_ATENDIMENTO (evento técnico S0 autorizado; não é status comercial)
  -> S0 fixa snapshot/versão/loja/caso e contexto mínimo
  -> OpenAI human_close_extract + avaliação do desfecho conversacional
  -> S0 valida TODAS as sugestões de campo elegíveis, fontes, conflitos e versão
  -> S0 persiste automaticamente campos permitidos; os demais permanecem pendentes
  -> S0 decide próximo passo mediante regras homologadas:
     a) pendência de campo ESSENCIAL ou conflito essencial -> fila humana + motivo/itens pendentes
     b) não há pendência ESSENCIAL e intenção de remessa é válida:
        b1) transmissão direta AUTORIZADA e comprovável -> processo de remessa S0/banco com comprovante
        b2) sem autorização de envio direto -> fila humana de remessa + motivo curto
     c) desfecho conversacional sem continuidade / desistência / perda sugerida:
        proposta de encerramento operacional para S0, SEM converter automaticamente em "perdido"
        até existir norma específica para os casos sem negativa bancária
     d) venda alegada/indicada na conversa:
        registrar hipótese com fonte; NÃO marcar "vendido" sem confirmação oficial do banco e ato humano
     e) caso ambíguo/resultado inconclusivo -> revisão humana justificada
```

O evento `atendimento_humano_concluido` é distinto do fim do ciclo comercial. Reabertura de ATENDIMENTO HUMANO para complemento é fila/tarefa técnica, não retorno da IA Vendedora e não altera retroativamente `cadastro enviado ao banco`/ `vendido`. O contrato físico e nomenclatura serão revistos com S0 [R].

## 3. Contrato candidato de resposta composta `human_close_extract` [P]

Preservar `contract_version`, `request_id`, `closure_event_id`, `snapshot_hash`, `expected_form_version`, versão do catálogo, fontes e outome do OAI-05.

Adicionar bloco descritivo (campos [P], não JSON Schema homologado):

```json
{
  "conversational_assessment": {
    "conversation_outcome": "CONTINUE_TO_BANK_REVIEW",
    "reason_code": "CLIENT_CONFIRMED_INTENT",
    "reason_summary_short": "Cliente confirmou interesse; cadastro exige validação.",
    "evidence_message_refs": ["msg_demo_004"],
    "certainty": "explicit"
  },
  "extracted_fields": [
    {"field_code":"CAMPO_FICTICIO_01","value":"VALOR_FICTICIO","source_message_refs":["msg_demo_003"]}
  ],
  "field_gaps": [
    {"field_code":"CAMPO_EXEMPLO_PENDENTE","is_required_for_bank":true,"reason_code":"NOT_STATED"}
  ],
  "handoff_advisory": {
    "needed": true,
    "reason_code": "REQUIRED_FIELDS_MISSING",
    "short_message": "Falta o CAMPO_EXEMPLO_PENDENTE para preparar a remessa."
  },
  "next_step_proposal": "RETURN_TO_HUMAN_FOR_REQUIRED_DATA"
}
```

**Esse JSON é demonstração integralmente fictícia.** O modelo pode SUGERIR `conversation_outcome` e `next_step_proposal`, mas S0 calcula/valida a decisão final segundo estágio do ciclo, remessa comprovada, campos, permissões e normas vigentes. `is_required_for_bank` não pode ser criado ou confiado ao modelo; deve ser conferido contra versão da allowlist mantida pelo S0. O indicador comercial `CONTINUE_TO_BANK_REVIEW` não significa venda comprovada ou aprovação de crédito.

Outcomes candidatos para conversa [P]: `CONTINUE_TO_BANK_REVIEW`, `NO_FURTHER_COMMERCIAL_INTEREST`, `CUSTOMER_WITHDREW`, `SALE_CLAIMED_UNVERIFIED`, `INCONCLUSIVE`. **Não são os oito status comerciais.** Qualquer proposta `SOLD` com ausência de prova do banco é mapeada a hipótese não comprovada; qualquer proposta `LOST` baseada somente na conversa fica sujeita a definição normativa de encerramento sem recusa bancária [R].

## 4. Contrato de aviso de handoff IA → humano [P]

Todo encaminhamento provocado pela IA Vendedora ou pós-processamento OpenAI deve oferecer `handoff_advisory` com:
- `case_ref`, `handoff_event_ref`, `reason_code` de catálogo, `short_message` em pt-BR (ideal 1–2 frases), `missing_required_field_codes[]` se houver, `source_ref[]` quando cabível, `policy_version`, `generated_by=ai|deterministic_fallback`.
- A atribuição/entrega da notificação e sua visualização no painel são **S0/UI**; não são endpoints implementados nesta branch.
- Exemplo solicitação do cliente: “Cliente pediu atendimento humano diretamente.”
- Exemplo questão jurídica: “Cliente trouxe questão jurídica; necessária análise humana.” **Sem emitir interpretação jurídica.**
- Exemplo dados essenciais: “Faltam os campos obrigatórios X e Y para preparar remessa.” Usar nomes legíveis fornecidos por S0, não criar requisitos bancários.
- Exemplo remessa humana: “Dados essenciais conferidos; envio ao banco depende de operador autorizado.”
- Aviso deve ser curto, não repetir CPF, extratos, áudio/transcrição privada nem conteúdo jurídico sensível. Não é resposta WhatsApp.

**Falha da OpenAI não deve bloquear handoff:** se geração de resumo falhar, S0 gera aviso determinístico com motivo técnico conhecido (p. ex., `OTHER_REVIEW`), registra incerteza e mantém encaminhamento humano. A exigência do aviso **não** concede autoridade ao modelo para atribuir operador, enviar mensagem ou alterar status.

## 5. Preferência de canal: contrato candidato `response_modality_advisory` [P]

S0 fornece `explicit_modality_request` se houver (`TEXT`, `AUDIO`, `NONE`) + métricas/eventos MINIMIZADOS do padrão recente (`recent_customer_text_count`, `recent_customer_audio_count`, `modality_recency_ref`) e política aprovada; não usar apenas o último formato recebido. A OpenAI sugere `TEXT` ou `AUDIO` com `reason_code` e `policy_version`, mas S0 decide e revalida elegibilidade, custo, canal Meta, comprimento, motivo comercial e handoff.

Regras mínimas:
- Pedido explícito prevalece sobre inferência de histórico quando permitido, respeitando acessibilidade e limitações; não insistir em áudio quando o cliente pediu texto.
- Padrão reiterado é INDÍCIO, não fato definitivo nem preferência global da pessoa; é escopado ao caso/loja.
- Um áudio isolado não altera permanentemente preferência.
- Uma mensagem de áudio eventual em conversa escrita é opção contextual permitida sob política futura; não usar “aproximação humana” para ocultar identidade automatizada ou criar promessa bancária.
- Transcrição incerta de valores críticos não autoriza preenchimento automático, e fala sintética deve corresponder ao texto validado.
- Após handoff humano, nenhuma saída automática de voz ou texto ao cliente.

Critérios/heurísticas de contagem, duração e fallback, inclusive se o cliente muda de ideia, seguem [R], sem números inventados.

## 6. Critérios de regressão derivados [P]; SEM testes executados

- NC-01: todo handoff solicitado à IA contém reason_code e aviso interno, inclusive pedido do cliente e questão jurídica, sem vazar D3/D4.
- NC-02: falha do modelo não bloqueia handoff; fallback determinístico.
- NC-03: operador conclui, 15 de 20 campos fictícios explicitamente disponíveis, dos quais só 7 são essenciais: S0 stub preenche TODOS os 15 elegíveis (sem afirmar números como requisitos reais), e só remete lista exigida pelo banco segundo catálogo.
- NC-04: opcional ausente não retorna ao humano se essenciais foram conferidos; essencial ausente -> retorno humano com nome do campo.
- NC-05: legal/risco/revisão humana -> notificação curta correta, sem aconselhamento jurídico inventado.
- NC-06: pedido explícito “mande texto” prevalece contra várias mensagens de áudio anteriores.
- NC-07: áudio único não cria preferência permanente, e áudio contextual eventual não marca o cliente como “prefere áudio”.
- NC-08: após handoff, `speech_synthesize` não produz resposta ao cliente; `human_close_extract` interno ainda permitido se houver fechamento válido.
- NC-09: conversa diz “está vendido”, sem confirmação Banco -> nenhuma transição `vendido`.
- NC-10: recusa definitiva do banco não é inferida por OpenAI, continua evento humano comprovado.
- NC-11: eventual caminho direto ao Banco sem autorização/evidência -> bloqueado; usar envio humano.
- NC-12: conversa indica desistência, sem negativa bancária: retorno conversacional registrado, **nenhuma mudança automática para `perdido`** enquanto regra de encerramento sem recusa está [R].
- NC-13: teste em lote remoto não executa sem aprovação de estimativa específica, e não ocorre gasto ilimitado por ausência de teto global.
- NC-14: decisão de voz ou desfecho não muda, sem permissão, dados de outras lojas; prazo/versões e ids auditáveis.

## 7. Pontos pendentes sem bloquear trabalho offline

[R] Definir lista-mestre real dos campos, quais são essenciais para o banco e quais são captáveis/permissíveis; separar “preencher ficha interna” e “enviar dados ao banco”.
[R] Definir com S0 o ciclo de “encerrar → analisar → pedir complemento → novo atendimento humano → reencerrar” sem novo status comercial.
[R] Confirmar se “venda” mencionada pelo responsável quer dizer **venda comprovada pelo Banco** ou **aceite/negociação encerrada no WhatsApp**, para evitar enquadramento incorreto.
[R] Deliberar de forma EXPLÍCITA eventual automação de `perdido` quando o cliente desiste sem recusa definitiva, pois a norma 21 cobre apenas negativa definitiva do Banco e não autoriza conclusão genérica automática.
[R/V] Habilitação de envio direto ao Banco, confirmação bancária, provas e interfaces/contratos.
[R] Critérios de escolha de canal/modalidade e política de identidade de voz; apoio da frente Meta para formato e canal.
[R] Modelo, runtime direto × n8n, orçamento por lote e metadados de observabilidade, conforme E02 e OAI-04.
[V] Privacidade, tratamento e transferência de dados reais, LGPD/Meta/Banco.

**Regra de não interferência:** esta branch só documenta as interfaces e o comportamento de modelos. S0 e Meta permanecem livres para desenvolver seu backlog; nenhuma transferência, pausa, merge ou alteração de código e infraestrutura é efetuada por este documento.

**Status:** direção de negócio registrada; contratos candidatos [P] e revisão S0/Meta [R] não concluídos. Nenhum teste, credencial, consumo ou alteração Supabase realizado.
