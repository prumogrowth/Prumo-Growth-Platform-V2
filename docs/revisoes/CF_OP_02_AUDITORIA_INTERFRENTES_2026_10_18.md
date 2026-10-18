# Auditoria CF-OP-02 — comunicação e alinhamento entre frentes | 18/10/2026

**Escopo:** auditoria documental de GitHub para verificar se as regras do responsável sobre recontato contextual, janela Meta, conclusão humana, cadeia final + 24h, rota de respostas e redistribuição chegaram às frentes **e** se seus contratos já foram atualizados. Repositório privado `prumogrowth/Prumo-Growth---Platform`. **Não** é aceite de integração ou engenharia executável.

**Conclusão auditada:** COMUNICAÇÃO REGISTRADA EM 5 DESTINOS, DIRETRIZ TRANSVERSAL VERSIONADA, **CONTRATOS PROPRIETÁRIOS AINDA NÃO CONCILIADOS**, NENHUM DOS 34 TESTES CF2 EXECUTADO, nenhum merge/deploy. Comentário em PR/issue prova publicação, **não prova leitura, aceite ou implementação pelo proprietário da frente**.

## A. Provas de comunicação e estado dos artefatos inspecionados

| Frente | Evidência da comunicação | Contrato local e situação comprovada | Veredito |
| --- | --- | --- | --- |
| S0 / núcleo — PR #1, `6a9f3a09493c9eeb2a59d7a481f62cde5992ca3e` | [comentário #6253604891](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/1#issuecomment-6253604891) | `docs/RECONTATOS_C05_C08_SIMULACAO_2026_10_17.md` preserva C05/C08, mas não incorpora novo plano pós-humano e C09 humano; `docs/MAPA_MENTAL.md` não referencia CF-OP-02. S0 ainda deve reconciliar docs 26 e 40 como propostas canônicas | **Notificado; NÃO integrado** |
| Gestão Prumo S1-002 — PR #5, `64e55cbeba2854617f8ae5c0dbbc83252fc005cf` | [comentário #6253605995](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/5#issuecomment-6253605995) | `docs/S1_002_EQUIPE_PRUMO_PORTAO_INICIAL_2026_10_18.md`: suspensão já impede leitura autorizada, **mas mantém atribuições ativas**; redistribuição automática só como pendência, sem teste | **Notificado; bloqueador de implementação I2** |
| OpenAI — PR #3, `fac96b3a696aeefd4ac7c7bfb6fc301a67b2058b` no snapshot inicial | [comentário #6253605679](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/3#issuecomment-6253605679) | `OAI_05...` e `OAI_07...` descrevem extração/desfecho, mas ainda enviam resultado inconclusivo à revisão humana e **não especificam formalmente criação de cadeia pós-humana + solicitação manual à Planejadora, retorno ao humano, final +24h**. E01/OAI-05 assinaturas distintas [R] | **Notificado; CONTRATO PARCIAL** |
| Visual — branch `feat/frontend-plataforma-visual`, `f507364b56c9c26b9dd8425d7792498bc7980a0f` | [comentário #6253606287](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4#issuecomment-6253606287) | `frontend/docs/05_CONTRATO_FV02_CONCLUSAO_EXTRAÇÃO_POS_HUMANA_v0_1.md` cobre concluir→extração, mas **não integra** janela ativa que permanece aberta após concluir, template individual fora de janela, solicitar cadeia por IA, retorno ao humano, perda após template final, gestão de redistribuição | **Notificado; CONTRATO PARCIAL** |
| WhatsApp/Meta — PR #2, `e83080c1e00b4ac14c5072bdcfbedae1a19d3cc4` | [comentário #6253605274](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2#issuecomment-6253605274) | `integrations/whatsapp-meta/README.md` e contrato `wa06b-serializacao-canonica-prova-interna-v0_1.md` pertencem ao adaptador/ingresso e **não documentam integração executável completa** de janela 24h, templates pós-humano, comprovante real de `sent` e cancelamento; sem API Meta real | **Notificado; CONTRATO DE INTEGRAÇÃO PENDENTE** |

**Trilha central publicada:** [issue #6](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6) com [confirmação complementar #6253604489](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6#issuecomment-6253604489), [PR #7 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/7) com `CF_OP_02_DIRETRIZ...` e `CF_OP_02_MATRIZ...` (34 **testes candidatos**). [Issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4) permanece aberta. PRs #1/#2/#3/#5/#7 são Draft, não merged. A comunicação é verificável em cada destino, mas **não consta aceite formal de todas as frentes**.

## B. Conflitos materiais encontrados

### AUD-CF02-01 — Crítico: C09 exclui humano expressamente

**Fonte canônica:** pacote auditado 17/10, `documentos/26_Contratos_Conceituais_Eventos_APIs_v0_1.md`, **seção C09**: exige `ciclo ainda elegível e sob IA` para `perdido` por 24h após template final comprovadamente enviado. **Documento 03 ATD-01B** prevê 2 a 5 tentativas após contato, template final separado e +24h comprovadas sem resposta; não substitui expressamente a condição `sob IA` do C09. **Nova direção de 18/10** inclui cadeias pós-humanas e caso atribuído a operador.

**Tratamento:** não chamar a regra existente de já homologada para humanos; requer **emenda explícita do contrato C09** com critérios de elegibilidade por fase/ciclo e preservação de prova, autoria, status. Direção de negócio aprovada, estrutura técnica [R]. **Em particular, `cadastro enviado ao banco` só vira `perdido` por negativa definitiva comprovada e registrada humanamente (docs 13A/21); `vendido` histórico jamais muda por silêncio (doc 22).** Casos como `cadastro enviado ao operador`, intervenção humana pré-banco e remessa iniciada exigem matriz exata, não suposição.

### AUD-CF02-02 — Alto: C08/C10 cancela no handoff; plano pós-humano deve ser NOVO

Doc.26 C08 enumera handoff como motivo de cancelamento de pendentes; C10 cessa IA Vendedora e recontatos incompatíveis. O plano humano solicitado pelo operador ou a partir de conclusão ambígua precisa ter **origem/finalidade e versão próprias**, sem reativar o plano da IA cancelado no handoff. Backend decide concorrência entre template individual e cadeia automática, cancela futuras tentativas no inbound, impede duplicidade e não religa IA Vendedora.

### AUD-CF02-03 — Alto: três marcos distintos, UI e Meta não incorporados

1. Janela de 24h para mensagens livres contada da **última mensagem recebida do cliente**; template outbound isolado não a reabre.
2. Conclusão de atendimento humano dispara extração/análise, mas mantém conversa ativa até o fim da janela Meta, sem apagar histórico.
3. 24h após **prova efetiva** do template final, sem retorno e com ciclo elegível, dispararia C09 ampliado. Nunca contar do agendamento, aceite de API ou de janela Meta.

Atendimento humano não concluído mantém caso pendente mesmo com janela expirada; UI oferece **template individual aprovado** ou **solicitação de cadeia**. Pós-conclusão ambígua pode propor cadeia elegível. Front/Meta precisam contratos implementáveis para evidências e estados.

### AUD-CF02-04 — Alto: S1-002 não remaneja atribuições

Migration 038/7 testes validam portão de status da equipe; documento S1-002 reconhece duas atribuições ainda ativas após suspensão. A nova regra exige bloquear novos casos e **remanejar atomicamente** casos operacionais a operadores Prumo ativos autorizados na **mesma loja**, sem repassar papéis/concessões de outra loja ou recriar acesso ao reativar. Caso sem destinatário -> fila protegida e alerta gestor [P/R]. Testes de corrida e disponibilidade ainda não existem.

### AUD-CF02-05 — Médio/alto: OpenAI/FV não possuem assinatura final compartilhada

E01 x OAI-05 divergem em `trigger_ref/closure_event_id`, `field_suggestions/fields_proposed` e política de snapshot; issue CFI-01 #4 segue em revisão. Direção CF-OP-02 acrescenta agenda/proposta do C05, evidência da promessa de retorno e tipo de destino (humano/IA) **calculado pelo S0**, nunca model-determined. Contratos individuais precisam uma única versão canônica por fronteira antes de programar.

### AUD-CF02-06 — Gate Meta/LGPD ainda sem prova

Meta/WhatsApp não homologou categoria, consentimento, opt-out, custo, prova confiável de `sent`, horários ou eventos externos. `C04` exige elegibilidade comprovada; não ativar tentativas, prazo C09 nem contatos com dados reais. Sem orçamento/autorizações de APIs, nenhum envio externo.

## C. Critérios verificáveis para declarar frentes alinhadas — todos abertos no momento

- [ ] S0 aprova matriz de elegibilidade por status/caso, emenda C09 humano, C08/C10 e atribuição pós-resposta, documenta nomes/versão de operações.
- [ ] S1-002 especifica remanejamento atômico, tratamento sem elegível, suspensão/reactivação e validação de acesso pós-038 (não inferir 7/7 S1E como prova I2).
- [ ] OpenAI harmoniza OAI-05/OAI-07/E01 com C05 para compromisso, cadeia pós-humana e evidências; nenhum envio ou status pela IA.
- [ ] Frontend harmoniza FV-01/FV-02: janela Meta separada da conclusão, dois botões distintos, roteamento, status de execução e arquivo/histórico sem apagamento.
- [ ] Meta harmoniza contrato de evento last-inbound + envio final realmente comprovado + elegibilidade/cancelamento; prova de que template não reabre janela livre sozinho.
- [ ] Publicação de **aceite cruzado explícito** nos PRs/issues com links para as versões compatíveis, seguida de teste sintético; **34 cenários ainda não executados**.
- [ ] Checagem de políticas externas Banco/Meta/LGPD antes de produção, nenhum gasto/recurso hospedado sem aprovação.

## D. Veredito

**Comunicação: CONCLUÍDA e AUDITADA. Alinhamento de visão: PARCIAL, com diretriz comum. Alinhamento contratual: NÃO CONCLUÍDO. Integração: NÃO EXECUTADA.** Direção de negócio da nova extensão está documentada, mas as cláusulas candidatas não podem suplantar silenciosamente C09 ou regras bancárias. Este relatório é evidência de auditoria, não autorização de editar unilateralmente branches das outras frentes, merge, deploy ou progresso global.
