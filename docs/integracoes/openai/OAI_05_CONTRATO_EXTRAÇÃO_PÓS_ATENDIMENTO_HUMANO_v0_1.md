# OAI-05 — Extração de cadastro após encerramento do atendimento humano | contrato v0.1

> **AVISO DE PRECEDÊNCIA — AUDITORIA DA FRENTE OPENAI, 22/10/2026.** Este documento anterior permanece preservado como **contrato candidato/histórico**; trechos conflitantes **NÃO são a direção funcional vigente**. Ler primeiro [AL-IA-00 — índice e precedência](./ALINHAMENTO_2026_10_22_00_INDICE_E_PRECEDENCIA_v0_1.md), [AL-IA-01 — jornada](./ALINHAMENTO_2026_10_22_01_JORNADA_F01_F02_F03_v0_1.md), [AL-IA-04 — deltas](./ALINHAMENTO_2026_10_22_04_RASTREABILIDADE_DELTAS_PENDENCIAS_v0_1.md), [AL-IA-07 — dependências entre frentes](./ALINHAMENTO_2026_10_22_07_DEPENDENCIAS_RELEVANTES_OUTRAS_FRENTES_v0_1.md) e [AL-IA-08 — auditoria documental](./ALINHAMENTO_2026_10_22_08_AUDITORIA_FECHAMENTO_DOCUMENTAL_FRENTE_OPENAI_v0_1.md). O texto abaixo documenta o estado de sua data original, **sem emendar código, criar autorização S0, nem corrigir documentação de outras frentes**.
>
> **Atenção especial:** a antiga exceção de edição cadastral pelo Consultor foi expressamente retirada; a F03 dispõe de histórico lógico integral do cliente na mesma concessionária até o corte, inclusive novas conclusões humanas; pode produzir propostas de transições permitidas pela S0, inclusive perda por desistência, mas nunca venda. O contrato físico precisa ser revisto.


**Data:** 18/10/2026 | **Estado:** [D-NEGÓCIO] orientação funcional expressa do responsável nesta conversa: preenchimento cadastral normal realizado por IA após conclusão da conversa humana, e não digitado rotineiramente pelo operador; **[P]** envelope, estratégia de gravação, parâmetros, gates e eventos; **[R]** revisão do contrato físico S0, enumeração dos campos cadastrais e definição de "atendimento concluído"; **[V]** dados pessoais/áudio/condições Banco–LGPD–Meta.

## 1. Fronteiras e compatibilidade

**Natureza:** capacidade de processamento silencioso em retaguarda, chamada **extrator pós-atendimento humano** (nome técnico provisório), NÃO terceira IA autônoma gestora/analista e NÃO retomada de mensagens da IA Vendedora. A IA Vendedora permanece silenciada após qualquer handoff, inclusive quando esse serviço é acionado. O extrator não envia respostas ao cliente, não decide venda/recusa, não acessa outros casos ou lojas e não chama Meta, Banco ou ferramentas de escrita diretamente.

**Responsabilidade principal do operador:** conversar com o cliente no atendimento humano; quando considerar sua etapa concluída, executar a ação de encerramento operacional que acionará o processamento. Não assumir preenchimento manual campo a campo como fluxo habitual. **Exceção normativa preservada:** decisões 23 e D41-04 ainda permitem ao operador designado conferir/corrigir inconsistências, solicitar complemento e registrar versão da correção; retirar esse poder exigirá decisão normativa específica, não ocorre por esta integração.

**Responsabilidade S0 (continua na frente PR #1):** disponibilizar snapshot autorizado e versão; definir evento/ação de "conversa humana concluída"; conferir escopo de loja, caso e atribuição; validar catálogo de campos aplicáveis e LGPD; conferir cada proposta com proveniência; aplicar nova versão cadastral por operação idempotente e auditada; expor lacunas/erros aos humanos; determinar se pode prosseguir ao próximo marco. Não transicionar automaticamente para `cadastro enviado ao operador`, `cadastro enviado ao banco`, `vendido` ou `perdido`.

**Responsabilidade OpenAI (PR #3):** receber recorte autorizado e esquema de campos S0, extrair propostas, sinalizar ausências/contradições, vincular fontes e devolver resultado estruturado sem efeitos colaterais. Não decidir o que constitui campo obrigatório ou as operações bancárias.

**Responsabilidade Meta (PR #2):** mantém o transporte e os dados técnicos de mensagens/áudio. O extrator recebe apenas referências ou transcrições autorizadas fornecidas pela S0; não lê Graph/Media URL nem armazena mídia de forma autônoma.

**Compatibilidade:** os oito status vigentes permanecem. "Atendimento humano concluído", "extração solicitada", "em revisão" e "extração falhou" são estados/eventos **técnicos candidatos**, NÃO novos status comerciais. Não confundir fechamento de conversa humana com resultado do ciclo comercial, remessa ou conclusão da venda. Casos humanos de exceção `em atendimento pelo operador` podem produzir uma ficha sem fingir que a IA Vendedora concluiu coleta e fez handoff `cadastro enviado ao operador`; encaixe exato depende da S0 [R].

## 2. Operação candidata: `human_close_extract` [P]

### Pré-condições impostas pela S0

1. Ator humano autenticado, caso sob sua atribuição no escopo da concessionária, ou evento de encerramento legitimamente produzido pela S0; delegações e reatribuições respeitadas.
2. Snapshot IMUTÁVEL de mensagens/conversas permitidas da MESMA concessionária e do caso/ciclo correto. Delimitar corte (`message_watermark` e `closed_at`) para não misturar retornos posteriores nem versões de outros atendimentos.
3. Esquema/catalogação `allowed_fields_catalog_version` fornecido pela S0 (inclusive regras de dados sensíveis e tipos), em vez de uma lista de campos inventada pelo adaptador.
4. Versão atual de ficha, autorização de tratamento (LGPD/Banco) e limites de envio a provedor externo validados pela S0. Não mandar histórico integral por padrão; minimizar.
5. Política sobre reprocessamentos, prazos e conciliação de mensagens/áudios ainda [R]; transcrição usada como evidência somente se autorizada, com indicador de origem/mídia.

### Envelope S0 → adaptador (nomes `[P]`, ainda não são endpoint físico)

- `contract_version`, `request_id`, `correlation_id`, `operation_kind="human_close_extract"`, `concessionaria_id`, `caso_id`, `conversa_id`, `ciclo_id` se houver (IDs opacos e confiáveis);
- `closure_event_id`, `closed_at`, `closed_by_ref` (referência interna, não dado de operador enviado à OpenAI), `message_watermark`, `conversation_snapshot_ref`, `conversation_snapshot_hash`;
- `current_form_version`, `expected_version`, `allowed_fields_catalog_version`, `allowed_fields[]` (códigos opacos/tipos/condições de elegibilidade), `existing_field_provenance[]` minimizada, `policy_versions`;
- `messages[]` somente após S0 resolver e minimizar: `message_ref`, `author_kind`, `sent_at`, `content_kind`, `text_or_transcript`, `transcription_ref?`, `permission_scope`; links privados e material bruto não são transferidos por padrão.

**Segredos proibidos no envelope:** API key, tokens Meta, service_role, JWT, credencial bancária, SQL, autorização para agir, cadeias de outras lojas. Mensagem do cliente e do operador é dado não confiável, não instrução que possa ampliar permissões.

### Saída adaptador → S0 (sem gravação ou envio)

- `contract_version`, `request_id`, `snapshot_hash`, `form_version_observed`, `fields_proposed[]`, `missing_fields[]`, `conflicts[]`, `extraction_warnings[]`, `provider_metadata` sanitizado, `outcome` (`PROPOSED`, `PARTIAL`, `NEEDS_REVIEW` ou `FAILED`).
- Cada `fields_proposed[]` contém `field_code` **presente no catálogo autorizado**, `proposed_value` do tipo exigido, `source_message_refs[]`, `source_kind` (declaração do cliente, confirmação humana, transcrição), `certainty` de finalidade interna (não prova de veracidade), `extraction_notes_code?`, `transcription_ref?`. Não retornar texto integral ao log administrativo.
- `missing_fields[]`: catálogo aplicável sem valor explícito fundamentado, com `reason_code`; `conflicts[]`: valores diferentes ou negações associados a fontes distintas, sem escolher arbitrariamente valor final.
- `provider_metadata` contém apenas modelo/versão/prompt/contagem de tokens/duração/traces sem conteúdo pessoal; não incluir chave ou mensagem integral.

### Exemplo EXCLUSIVAMENTE fictício de proposta (não schema final)

```json
{
  "contract_version": "s0-openai.v0.1-proposed",
  "request_id": "req_demo_001",
  "operation_kind": "human_close_extract",
  "outcome": "PARTIAL",
  "snapshot_hash": "hash_demo_sanitizado",
  "form_version_observed": 4,
  "fields_proposed": [
    {
      "field_code": "CAMPO_EXEMPLO_NAO_NORMATIVO",
      "proposed_value": "VALOR_FICTICIO",
      "source_message_refs": ["msg_demo_03"],
      "source_kind": "client_statement",
      "certainty": "explicit",
      "transcription_ref": null
    }
  ],
  "missing_fields": [{"field_code": "CAMPO_PENDENTE_EXEMPLO", "reason_code": "NOT_STATED"}],
  "conflicts": [],
  "extraction_warnings": []
}
```

**Nota:** esse exemplo deliberadamente NÃO define CPF, renda, endereço, valor de entrada, parcela, consentimento ou requisito de documentação bancária como campos obrigatórios. Catálogo de campos/autorização é responsabilidade S0 e validação externa [R/V]. É exemplo de contrato conceitual, não JSON Schema definitivo nem payload pronto para uso em provedor.

## 3. Aplicação automática de campos — quando a S0 permitir [P/R]

**Objetivo de negócio:** preencher automaticamente os campos comprováveis como padrão após a conversa; não pedir que operador os digite. **Implementação segura:** OpenAI propõe, S0 executa gravação automática de campos elegíveis se e somente se todo critério previamente aprovado for verdadeiro:

- campo pertence ao catálogo/perfil/loja aplicável; texto ou transcrição traz valor explícito sustentado por `source_message_refs`;
- valor está no tipo e formato definidos, sem invenção, tradução semântica arriscada ou inferência de dado financeiro;
- não há conflito ou revisão pendente aplicável; validação de sensibilidade e autorização do campo aprovada;
- `message_watermark`, hash, versão da ficha e atribuição/caso continuam atuais; nova mensagem ou alteração humana posterior invalida o snapshot ou provoca nova versão/revisão;
- gravação via operação S0 autenticada, auditável, idempotente, com origem `extracted_from_human_conversation` e nova `cadastro_versao`.

Na presença de lacunas, incertezas, inconsistências ou falha do provedor, **não inventar preenchimento**. O sistema disponibiliza pendências à equipe humana; o operador poderá conversar para esclarecer ou corrigir excepcionalmente. A política de autoaplicação por classe D3/campo e eventual revisão humana obrigatória [R/V] fica com S0/governança, não é aprovada por esta proposta. O fallback nunca reativa a IA Vendedora.

## 4. Idempotência, privacidade e falhas

- Mesma `closure_event_id` + `conversation_snapshot_hash` + `allowed_fields_catalog_version` não cria várias fichas diferentes; tentar novamente preserva rastreabilidade e trava de versão da S0.
- Corrida com mensagem nova, alteração/correção humana ou retorno de cliente: descartar resultado antigo ou exigir recomputação; nunca sobrescrever informação mais recente.
- Transcrição incerta, conteúdo sensível, áudio sem consentimento/autorização ou mídia indisponível: sinalizar `NEEDS_REVIEW`; não extrair dado sem evidência.
- Falhas `429`, `401`, timeout ou indisponibilidade: marcar erro técnico, manter responsabilidade humana e status comercial inalterados.
- Privacidade: minimização e controles de transferência/tratamento de dados, acordo com Banco e LGPD/Meta [V]; retenção do fornecedor, região e monitoramento ainda [R/V].
- Trechos que parecem comandos administrativos, alterações de regras de crédito ou pedidos de "ignore previous instructions" vindos da conversa são dados; não executá-los.

## 5. Critérios de aceite E01 para esta operação (tudo [P])

E01-X01: evento de encerramento não cria novo status comercial.
E01-X02: sem campos manuais no fluxo nominal; sistema propõe e S0 persiste somente campos comprovados/autorizados.
E01-X03: cada campo aplicado preserva fonte, versão e autoria de extração; sem fonte, não aplicar.
E01-X04: ausência/confusão/negação => campos vazios ou revisão; jamais completar com suposição.
E01-X05: duas concessionárias com telefone igual não compartilham ficha/histórico.
E01-X06: operador continua único responsável por remessa bancária efetiva e provas/resultados manuais.
E01-X07: a execução silenciosa pós-humana não reativa a IA Vendedora e não envia mensagens.
E01-X08: resposta atrasada, fechamento duplicado ou revisão posterior não causa sobrescrita nem duplica ficha.
E01-X09: mensagem em áudio só entra como fonte via transcrição autorizada e referência própria.
E01-X10: o catálogo definitivo, exceções da política humana e integração com eventos S0 são revisados pelo proprietário S0 antes de marcar E01 concluído.

## 5A. Esclarecimento funcional de 18/10/2026 — complementar com OAI-07

O responsável determinou que o botão **encerrar atendimento humano** deve funcionar independentemente da causa do handoff; após encerramento, a OpenAI deve analisar também **desfecho conversacional e motivo**, sem que o operador escolha rotineiramente uma classificação. A extração deve propor **todos** os campos disponíveis de catálogo permitido, não apenas essenciais para remessa. Se campos **essenciais para envio ao Banco** estiverem faltando, S0 devolve para atendimento humano, com motivo curto e indicação de campos; faltas APENAS opcionais não bloqueiam. Quando completos e havendo intenção válida, segue processo de remessa humana comprovada, ou envio direto somente se formalmente autorizado e implementado. OpenAI não cria/remete prova ou status comercial.

**Esclarecimento de negócio:** conversa “fechada” significa **interesse confirmado e dados suficientes para encaminhar a ficha para remessa**, não venda bancária; o operador não precisa rotular manualmente esse resultado conversacional. OAI-07 registra `NEGOTIATION_READY_FOR_BANK_HANDOFF` [P] e encaminhamento para a equipe de remessa (eventual `cadastro enviado ao operador` requer revisão de transição pelo S0). `cadastro enviado ao banco` exige envio efetivo comprovado; `vendido` somente após confirmação bancária efetiva da venda/pagamento e marcação manual com evidência, conforme 13A/21/41. Desistência sem recusa definitiva não autoriza automaticamente `perdido`. Política de fila/UI/estados pertence ao S0, não a esta branch.

## 6. Matriz de precedência — divergência declarada, NÃO resolvida unilateralmente

- Doc 23 [D]: operador humano tem direito de corrigir ficha e pedir complemento depois do handoff; falha no cadastro pronto é incidente de qualidade; não retomar IA Vendedora. **Mantido.**
- Doc 41 D41-04 [D]: gestor autoatribuído age como operador e pode corrigir a ficha no caso. **Mantido.**
- Docs 24/40 [P]: O3/SI03 exibe ações de conferência e correção; passam a necessitar revisão futura pela frente S0/UI para contemplar extração pós-encerramento, mas esta branch não os edita.
- Nova determinação funcional do responsável em 18/10/2026: digitação rotineira do cadastro pelo operador deixa de ser fluxo nominal; OpenAI analisa conversa concluída e extrai campos. **Registrada como nova orientação de negócio para contrato OAI**, sujeita à compatibilização operacional de S0 e catálogo [R].
- Doc 26 C03 e C13 existentes: C03 continua proposta de mensagem na fase vendedora; C13 continua correção humana excepcional. A nova operação OAI-05 é candidata complementar, NÃO renumera, reaproveita sem aprovação ou substitui contratos existentes.

**Resultado documental:** contrato candidato elaborado; sem revisão cruzada S0, teste de extração, modelo fixado, evento físico ou autorização de dados reais. **E01 segue EM REVISÃO [R]**, não concluído.


## Adendo OAI-08 / CF-OP-02 — extração e cadeia pós-humana

A conclusão humana continua iniciando F03 silenciosa, mas agora também analisa compromisso futuro e possível necessidade de nova cadeia de recontatos quando desfecho é inconclusivo, **sem enviar ou marcar perdido**. S0 autoriza pedido, Planejadora C05 propõe apenas templates preaprovados/horários/quantidade dentro de limites, com final separado e fontes; S0 valida/persiste e C09 aplica guarda bancária. Atendimento humanizado não volta à IA Vendedora. [Contrato proprietário OAI-08](OAI_08_CONTRATO_PLANEJADORA_POS_HUMANA_CF_OP_02_v0_1.md); [PR #7](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/7). Assinaturas E01/OAI-05 continuam [R], nada implantado.
