# FV-02 — Concluir conversa humana → extração → ficha | contrato UI ↔ S0 v0.1

**Data:** 18/10/2026. **Natureza:** orientação funcional de negócio aprovada pelo responsável em 18/10; assinatura e estados de integração **candidatos [P]** até S0 conciliar [R] com OpenAI OAI-05/E01. Nenhum endpoint/API implementado nem chamada externa executada.

## 1. Nova regra de fluxo [D-direção]

**O operador da Prumo NÃO preencherá normalmente campos como nome, e-mail e demais dados de cliente na plataforma.** Sua ação principal é conversar no atendimento humano e, no momento correto, clicar **Concluir atendimento** (rótulo provisório [P]). Isso solicita ao S0 finalizar a etapa de conversa e iniciar o processamento de extração pela OpenAI. A proposta estruturada retornada pela OpenAI será validada e, apenas quando elegível e autorizada, **persistida automaticamente pelo backend S0** em versão auditada da ficha. O operador vê o resultado e eventuais pendências; não precisa transcrever manualmente a conversa.

A extração é um serviço de retaguarda, **não a IA Vendedora conversando novamente**. Nenhuma mensagem automática, remessa bancária ou transição comercial decorre desse clique.

## 2. Sequência e autoridade

1. **Frontend**: operador designado pressiona 'Concluir atendimento'; evita disparos acidentais repetidos enquanto pedido está pendente. Mostra confirmação apenas do pedido, nunca do preenchimento.
2. **S0**: revalida ator da Prumo autenticado, concessão de loja, atribuição ativa do caso, versões e evento de conclusão; captura cutoff imutável de mensagens **daquele caso e loja**, correlaciona idempotency_key e registra evento técnico de conclusão.
3. **S0 → OpenAI**: aplica política de minimização, finalidade, catálogo autorizado de campos e versões; encaminha a chamada ao adaptador OAI-05/F03 da frente OpenAI, não ao navegador. Formato do adaptador pertence à frente OpenAI, não a FV-02.
4. **OpenAI → S0**: devolve campos sugeridos, fontes de mensagens, ausências, contradições e incertezas, SEM SQL, banco, evento comercial ou WhatsApp.
5. **S0**: valida os dados um a um (allowlist/catálogo, tipo, fonte, classe sensível, permissões, snapshot/hash, versão e atualização concorrente); grava automaticamente **somente campos elegíveis** com autoria técnica fiel, evento idempotente e nova versão; guarda pendências sem palpite.
6. **Frontend**: consulta status de processamento e UQ03 autorizada; apresenta progresso técnico, ficha versão atual, proveniência permitida e pendências. Após revogação de acesso, descarta dados de tela e recusa ações.
7. **Humano**: diante de pendência, conversa com cliente para esclarecimento ou, **excepcionalmente**, corrige caso específico segundo doc.23/C13/D41-04, política ainda a refinar; nunca restabelece a IA Vendedora.

## 3. Ação frontend → S0 [P; NÃO endpoint físico]

**Nome lógico provisório:** FV-02.request_human_conversation_completion (não criar C25/C10/C13 por analogia).

Pedido mínimo sugerido, campos de origem browser:
- case_ref: ID opaco do caso visível e atribuído;
- expected_case_version: versão visualizada pelo usuário;
- idempotency_key: identidade estável da tentativa de conclusão, para não duplicar com duplo clique/reenvio de rede;
- request_id/correlation_id: correlação operacional não pessoal, segundo convenção do S0.

**NÃO confiar em:** actor_ref, concessão de loja, status, 'closed_at', 'closed_by', message_watermark, hash de conversa, catálogo de campos, lista de permissões, evidência de LGPD ou resultados de IA providos pelo browser. Todos são derivados e verificados pelo backend; o caso é vinculado à concessionária e à atribuição no servidor.

**Retorno imediato proposto:** request_id, case_ref permitido, result = ACCEPTED_FOR_PROCESSING | ALREADY_APPLIED | erro, closure_event_ref e processing_ref quando confirmados por S0, current_case_version/as_of. Sucesso da solicitação **não é** prova de ficha preenchida, nem retorno OpenAI.

**Consulta de progresso [R]:** anexar projeção técnica autorizada à UQ03 ou expor consulta específica mediante aprovação S0; esta branch NÃO numera UQ10 nem cria rota concreta. Expor processing_ref opaco, estado técnico mapeado, latest_form_version_ref se aplicado, pendências minimizadas, timestamp, request_id e reason_code seguro; nunca prompt, logs brutos nem histórico de loja diversa.

## 4. Estados de UX sugeridos [P], não estados comerciais

| Exibição | Condição mínima de backend | O que NÃO afirmar |
| --- | --- | --- |
| Pronto para concluir | Backend sinaliza ação elegível ao caso e ator | Que os campos já estão completos |
| Conclusão solicitada | S0 aceitou e registrou intenção/evento | Que a OpenAI concluiu ou escreveu na base |
| Extraindo dados | S0 informa processamento ativo | Que um campo sugerido já é válido |
| Ficha atualizada | S0 confirma nova versão persistida | Que houve remessa ao Banco |
| Parcial / Precisa de esclarecimento | S0 guardou lacunas/contradições e resultado permitido | Que todo campo obrigatório está preenchido |
| Erro técnico / Tentar novamente | S0 indica falha segura e política de retentativa | Que o fluxo comercial mudou ou a IA Vendedora voltou |
| Dados alterados durante a extração | S0 rejeitou snapshot/versão obsoleta | Que é seguro sobrescrever versões humanas posteriores |
| Sem permissão | S0 revogou acesso, concessão ou atribuição | Existência e detalhes de outro caso |

Os rótulos e outcomes técnicos finais são decisão da interface **com aprovação S0**, não taxonomia de estado de vendas. Propostas e pendências não contam como 'cadastro enviado ao banco'.

## 5. Compatibilidade com status e situações de origem

- Para atendimento que já chegou ao humano com ficha completa e status `cadastro enviado ao operador`, não usar a nova extração para fingir que houve nova coleta ou mudar status. Possível reextração só sob regra S0 [R].
- Para exceção humana ainda em `em atendimento pelo operador`, permitir extração após conclusão da conversa **sem supor** que o resultado autoriza transição direta para `cadastro enviado ao operador`; regra de encaixe e eventual marco comercial dependem de S0 [R].
- `cadastro enviado ao banco`, `vendido` e `perdido` continuam condicionados aos procedimentos e provas bancárias humanas; conclusão não os aciona.
- Retorno espontâneo pós-remessa/vendido cria atendimento humano separado e não altera ciclo histórico nem reativa a IA Vendedora.
- Mesmo telefone em duas concessionárias **não** permite cruzar snapshots, cadastros ou resultados.

## 6. Dados ausentes, conflito, áudio e privacidade

Dados que o cliente não declarou permanecem ausentes; declaração ambígua ou contraditória exige esclarecimento. O campo só pode ser aplicado com fonte demonstrável e política de classe aprovada. A lista-mestre de campos de cadastro **não está definida** [R]. Transcrição de áudio depende do processo e das autorizações sob S0/Meta/OpenAI [R/V]. Não carregar CPF, texto integral de conversa, mídia, segredo de provedor ou prova bancária em erros/telemetria de UX.

## 7. Idempotência, concorrência e falhas

- Mesmo caso/evento e snapshot: evitar duas gravações/versões por clique duplo e retries, S0 é autoridade de deduplicação.
- Mensagem nova ou correção manual excepcional posterior ao snapshot: resultado antigo NÃO substitui atualização recente; reprocessamento precisa de novo corte e autorização.
- Atribuição revogada: UI elimina ações imediatamente; S0 recusa comando mesmo se botão ficar renderizado por atraso.
- Falha de OpenAI/timeout/429: status técnico de falha ou pendência; manter a operação humana possível dentro das decisões, sem suspensão/autorreparo da plataforma e sem avanço do status.
- Cliente tenta instruir IA via conversa: conteúdo é dado, nunca comando ou credencial de permissão.

## 8. Critérios de aceite futuros [P, NÃO EXECUTADOS]

FV02-T01: operador não encontra edição rotineira de campos do cadastro; pode conversar e solicitar conclusão.
FV02-T02: pressionar 'Concluir' apenas registra pedido/conclusão técnica; não vende, não remete e não altera status comercial.
FV02-T03: navegador nunca chama API OpenAI diretamente e não contém chave.
FV02-T04: saída do modelo sem fonte, contraditória ou inválida não vira dado confirmado; S0 é validador/persistidor.
FV02-T05: versão de ficha aplicada exibida só após confirmação S0; PROCESSING/PARTIAL/FAILED têm feedback próprio.
FV02-T06: duplo clique e repetição do request são idempotentes no S0.
FV02-T07: resposta tardia não sobrepõe correção humana nem mensagem posterior.
FV02-T08: operador sem caso atribuído/gestor não autoatribuído/loja sem concessão não conclui nem vê dados.
FV02-T09: mesmo telefone em A e B não mistura fontes nem ficha.
FV02-T10: áudio sem transcrição autorizada fica pendente e não é presumido.
FV02-T11: gestor com autoatribuição válida usa poderes de operador no caso; sem ela só lê D2/visões autorizadas.
FV02-T12: correção excepcional C13 continua distinta do fluxo normal, sujeita à norma e revisão de UX [R].
FV02-T13: erro do provedor não religa IA Vendedora nem suspende toda a plataforma.
FV02-T14: caso do tipo exceção humana em `em atendimento pelo operador` não ganha status automático por extrair ficha.

## 9. Pendências de conciliação

**S0 [R]:** confirmar nome/semântica de evento e comando, estados técnicos, ponto exato de coleta/conclusão, esquema de campos, guarda idempotente, versões, projeção para UI e quem pode reabrir esclarecimento sem criar novo status. **OpenAI + S0 [R]:** OAI-05 e a versão atual E01 F03 já usam `human_close_extract` como nome candidato comum; **ainda divergem na estrutura de request/response** (`trigger_ref` versus `closure_event_id`, `extraction.field_suggestions` versus `fields_proposed`, etc.), sem assumir compatibilidade de payloads. **Produto [R]:** escopo de eventual exceção de correção humana, UI de confirmação do clique e obrigatoriedade de revisão humana para classes sensíveis. **Meta/Banco/LGPD [V]:** canal, mídia, tratamento e remessa reais.

**Veredito:** aprovado apenas como D-direção de negócio para **não digitação rotineira e gatilho de extração**; contrato técnico FV-02 ainda [P/R].

## Adendo FV-02/CFI-01 — mapeamento de fronteiras em 18/10/2026 [P/R]

**Nomes NÃO intercambiáveis:**
- `FV-02.request_human_conversation_completion`: nome **lógico candidato** apenas para o pedido do navegador ao S0, sujeito a evento/comando físico do S0. **Não** é a operação da OpenAI nem C13.
- `human_close_extract`: operação **candidata** exclusivamente da interface S0→adaptador OpenAI, hoje convergente como nome em OAI-05/E01 (sem schema físico unificado).
- `atendimento_humano_concluido`: evento de domínio **candidato** que S0 deverá conferir/registar, **não status comercial** nem resposta de provider.
- `Ficha atualizada`: feedback visual permitido apenas após confirmação e releitura, via projeção S0 autorizada, de nova versão persistida.

**Divergências OpenAI ainda [R]:** request E01 (`scope`, `trigger_ref`, `fields_policy_version`) versus OAI-05 (`concessionaria_id`, `closure_event_id`, `allowed_fields_catalog_version`); retorno E01 (`extraction.field_suggestions`, `evidence_refs`, `missing_field_keys`) versus OAI-05 (`fields_proposed`, `source_message_refs`, `missing_fields`). A UI não consome esses payloads. O grupo S0/OpenAI definirá versão única antes de codificação. Matriz em [CFI-01](07_CONCILIACAO_INTERFRENTES_FV_S0_OAI_v0_1.md); testes candidatos em [MAT-CFI-01](08_MATRIZ_ACEITE_CONTRATUAL_FV_S0_OAI_v0_1.md).

**Semântica ainda [R]:** concluir conversa humana NÃO é encerrar ciclo; política de mensagens em trânsito e corte, esclarecimento posterior, idempotência e reprocessamento só podem ser efetivados pelo backend. Os estados de frontend aqui descritos são [P] e não comprovam respostas reais. As 36 provas de conformidade ainda não foram executadas.
