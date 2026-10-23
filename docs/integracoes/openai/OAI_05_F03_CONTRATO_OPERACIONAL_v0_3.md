# OAI-05 v0.3 — F03: extração pós-conclusão humana e histórico integral (candidata)

## E04/S0-F03 — HMAC persistido e 177 testes aprovados no PG17 (23/10/2026)

A frente OpenAI implementou diretamente na S0 compartilhada [prova HMAC persistente e vinculada ao manifesto F03](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/oai-s0-f03-history-port-20261023/backend/s0_f03_bound_content_seal_local.py), com locks transacionais na leitura do histórico, versão de chave explícita, idempotência e rechecagem de autorização. [GitHub Actions #40032787969](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40032787969) **SUCCESS — 177/177 testes**, 84 de S0 e 93 de F03, inclusive **23 físicos PG17.11 e 15 da barreira S0 de autorização**. [Relatório técnico detalhado no PR #16](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/oai-s0-f03-history-port-20261023/docs/S0_F03_HMAC_PERSISTIDO_PG17_177_TESTES_2026_10_23.md).

**Limite:** a prova HMAC refere-se ao texto sintético e vínculo de mensagens cobertas, não à integridade de mídia, à completude de histórico sob todos os escritores, à segurança/rotação de chave real, às versões independentes de ficha/caso/catálogo ou ao grant de conteúdo. **Nada de acesso OpenAI a texto real, escrita de ficha, deploy ou merge**; estados somente `REVIEW_ONLY`. Não há necessidade de instalar PostgreSQL ou providenciar credenciais nesta E04.

## E04/S0-F03 — Testes físicos realizados em GitHub Actions (23/10/2026)

**Impedimento anterior de PostgreSQL 17 RESOLVIDO** mediante autorização do responsável para usar GitHub Actions: [execução PG17 #40027116504](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40027116504) **150/150 PASS**; [execução PG17 #40027635632](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40027635632) **153/153 PASS** (84 S0, 24 leitor F03, 31 selo F03 e **14 testes físicos F03**). Logs confirmam PostgreSQL **17.11**, gatilhos, ACL e reprocessamento real no banco descartável.

A frente OpenAI implementou diretamente no [PR #16 S0 compartilhada](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/16) o [leitor HMAC-SHA256 de conteúdo histórico](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/oai-s0-f03-history-port-20261023/backend/s0_f03_content_integrity_local.py), que **detectou em PG17 mudança no texto de caso antigo sem alterar o hash de metadados**. [Relatório técnico](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/oai-s0-f03-history-port-20261023/docs/S0_F03_PG17_CI_HMAC_2026_10_23.md). **Limite importante:** HMAC ainda não vinculado ao manifesto persistente por transação nem provisionado com chave S0 real; não autoriza enviar o conteúdo à F03, aplicar ficha ou iniciar E05. A antiga afirmação “0/11 testes PG17 executados” descreve somente **o momento anterior a esses runs**.

## E04 — validação física S0/F03 preparada em PR #16 (23/10/2026)

A própria frente OpenAI adicionou na S0 compartilhada [executor manual PG17 protegido](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/oai-s0-f03-history-port-20261023/scripts/run-s0-f03-pg17-local.sh), [11 testes de integração descartável](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/oai-s0-f03-history-port-20261023/backend/tests/test_s0_f03_pg17_integration.py) e [documento de execução e limitações](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/oai-s0-f03-history-port-20261023/docs/S0_F03_PG17_EXECUTOR_E_LACUNA_CONTEUDO_2026_10_23.md), todos no [PR #16](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/16), preservando o PR #12.

**Evidência obtida nesta sessão:** sintaxe Python e Shell aprovada, três recusas comprovadas de conexão indevida (remoto, nome de banco e `PGHOST`), blobs GitHub iguais aos arquivos locais validados. **PostgreSQL 17/psql indisponíveis neste ambiente: 0/11 testes físicos executados**. O teste 11 registra uma lacuna relevante: mudança no texto de caso histórico **não altera o selo atual de IDs/metadados**, por isso o selo não autoriza conteúdo para F03. Os 70 SYN E02 seguem separados; E05/merge/deploy não autorizados.

> **Concretização da interface S0 pela OpenAI (23/10/2026):** [PR #16](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/16) contém agora pré-leitor de metadados multi-casos e **selo persistente local de pertencimento de mensagens**, com 31 testes unitários Python locais aprovados. O selamento **não certifica completude histórica física**, não fornece conteúdo de mídia/texto nem autoriza uso do modelo ou mutação de ficha; ver [relatório técnico S0](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/oai-s0-f03-history-port-20261023/docs/S0_F03_HISTORY_SEAL_APPEND_ONLY_2026_10_23.md). A frente OpenAI seguirá implementando a própria S0 até a integração ser segura, conforme [decisão de governança](./DECISAO_S0_COMPARTILHADA_EDICAO_POR_FRENTES_2026_10_23_v0_1.md).

> **Propriedade corrigida em 23/10/2026:** **F03 pertence integralmente à frente OpenAI**; S0 não possui frente exclusiva ativa. A frente OpenAI deve adaptar diretamente a S0 para fornecer histórico, versões e grants necessários, mediante PR isolado e regressões — [decisão de governança](./DECISAO_S0_COMPARTILHADA_EDICAO_POR_FRENTES_2026_10_23_v0_1.md). Primeiro incremento concreto em [PR #16](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/16), metadados multi-casos `REVIEW_ONLY_NOT_FROZEN` na S0. Não interpretar como histórico completo já homologado.

> **Manifesto histórico F03 [P/R]:** [CFI-01E — evidência multi-casos, cutoff e revalidação](./CFI_01_MANIFESTO_HISTORICO_F03_CANDIDATO_v0_1.md). Não confundir o recibo físico da S0 do PR #12 com payload multimodal/cliente/loja já autorizado.

> **Conciliação física pendente [R]:** ver [CFI-01 v0.3 — ponte F03 com S0/S1/FV/Meta](./CFI_01_CONCILIACAO_PONTE_F03_INTERFRENTES_v0_3.md) e [E02-REV v0.3](./E02_PACOTE_REVISAO_CRUZADA_E_GATES_v0_3.md). PR #12 S0 confirma metadados internos, **não** o histórico multimodal completo nem permissão de aplicação.

**Data:** 22/10/2026. **Estado:** decisões de produto [DN/DA]; modelo de envelope [P/R]; privacidade e Banco/Meta [V]. **Sem contrato físico ratificado, IA real, migração ou aplicação de cadastro.**

## 1. Precedência

Esta versão de trabalho **supera na intenção funcional** ``1–6` históricos de `OAI_05_CONTRATO_EXTRAÇÃO_PÓS_ATENDIMENTO_HUMANO_v0_1.md`, sem apagar decisões históricas. Fontes: AL-IA-01 ``4–5, AL-IA-02, AL-IA-04 DEL-01/02/03/04/05/06/07/08/19/27, AL-IA-07 XFR-10 e AL-IA-08; OAI-01/E01/OAI-07 v0.3. **Não atribuir aceite físico à S0.**

## 2. Gatilho, identidade e histórico

1. Apenas ato **expresso e autenticado do Consultor** em `Concluir/Encerrar atendimento` gera evento de conclusão humana elegível, produzido pela S0; janela Meta fechada, handoff, silêncio e fim de template não são gatilhos.
2. Cada conclusão válida é evento separado/imutável; mesmo cliente pode ter várias conclusões e várias execuções F03, inclusive após remessa ou venda histórica. Não cria automaticamente ficha ou ciclo novo.
3. Para aquela execução, o corte inclui **a última mensagem existente no instante da conclusão**; qualquer mensagem posterior fica fora daquele histórico de evidências, embora possa ser tratada em uma próxima execução.
4. A F03 obtém **acesso lógico ao histórico inteiro autorizado desse cliente naquela concessionária**, desde o primeiro atendimento na plataforma, cruzando seus casos/ciclos, diferentes consultores, F01, mensagens do cliente, templates, referências e tempos de mídias, handoffs e eventos relevantes. Prova de outra loja jamais entra, ainda que número/CPF coincida. A F03 não precisa receber todo o histórico de uma só vez em prompt; paginação/recuperação/resumo deve manter retorno verificável à fonte, ordem, autoria e contradições.
5. Áudio, imagem, foto, vídeo e documentos são elegíveis **quando disponíveis e legalmente autorizados**, sob contrato de acesso/transcrição/proveniência. Disponibilidade lógica não impõe armazenar mídia bruta indefinidamente nem presume consentimento/retenção; faltas precisam ser sinalizadas, não preenchidas por ficção.

## 3. Ficha, extração e crítica de evidência

- Há **uma ficha viva evolutiva por pessoa/concessionária**. Novas declarações podem atualizar valores antigos por autorização S0, preservando histórico e snapshots de remessas efetivamente realizadas. Nem lote novo nem negociação nova apaga declaração mais confiável sem avaliação temporal.
- F03 propõe **TODOS** os campos do catálogo autorizado encontrados explicitamente, incluindo opcionais. A S0 determina tipos, essencialidade, permissão de autoaplicação e validade. Não inventar campos, valores, evidência nem documentos bancários.
- Cada campo deve referenciar origem rastreável (mensagem/transcrição/mídia, autoria, data, pertencimento à loja, contexto e versão) e incerteza/conflitos. Evidências anteriores ao encerramento podem ser de **casos diferentes da mesma pessoa/loja**; proibição antiga de fonte fora do caso atual fica superada por esta decisão, **não** por permissão irrestrita.
- Declaração mais recente não prevalece automaticamente sobre antiga; interpretar se é correção, mera comparação, hipótese ou fala de terceiro. Contradição não resolvida → sinalizar; essencial faltante → pedir complemento humano; opcional faltante isolado → não bloquear.
- **Consultor não edita ficha**, nem excepcionalmente por C13 como método previsto neste contrato; ele conversa, consulta conforme UI autorizada e conclui. Falhas recorrentes de F03 são incidentes críticos técnicos. Correções administrativas de Diretor/MCP, se futuramente habilitadas, são outro fluxo autorizado, sem delegar a edição ao Consultor.
- A F03 não notifica o cliente e não reativa F01. Atualização cadastral depois de `cadastro enviado ao banco` ou `vendido` não altera a prova ou o conteúdo histórico da remessa/venda.

## 4. Envelope para ratificação S0↔OpenAI [P/R]

**Requisição candidata**: `contract_version`; `request_id`; `operation_kind=human_close_extract`; `concessionaria_ref`; `client_ref` (identidade *resolvida pela S0*, não suposta pelo número); `case_ref` e evento de conclusão `closure_event_ref`; `cutoff_ref`/`cutoff_at`; `history_scope_ref`/versão de seleção; `snapshot_hash` e watermark assinados/validados; `allowed_fields_catalog_version`; versão da ficha separada de versão do ciclo/caso; `policy_versions`; referências de mídia acessíveis e autorização. **Nomes são proposta**, não correspondência física automática com PR #12.

**Resposta candidata**: correlação de evento/corte/versão; `fields_proposed[]` (código, valor, confiança contextual, fontes completas), `missing_fields[]` (sem inventar obrigatoriedade), `conflicts[]`, `conversational_assessment`, `followup_need_advisory` apenas consultivo, avisos de evidência não disponível e estado de processamento/erro tipado. Proposta de transição comercial, quando aplicável, deve ser classificada **separadamente** do desfecho conversacional, com motivo/fonte; a S0 decide se é admissível. A saída da F03 **não** contém comando SQL/Graph/Banco, nem marca venda/remessa/negativa bancária.

## 5. Atualidade, concorrência e persistência

O recibo histórico de cutoff permanece válido como registro, mesmo havendo novo inbound depois. **Aplicar proposta antiga é outra decisão:** S0 confere na hora da gravação versão da ficha, caso/ciclo, identidade, autorização/atribuição e eventos mais recentes, em operação idempotente e auditada. Não sobrescrever fato novo nem promover conclusão histórica a permissão vigente. Se conflito ou falta de autorização, resultado `STALE/DENIED/REVIEW_REQUIRED` (códigos finais [R]), sem gravação. Reprocessamento com outra conclusão preserva isolamento entre execuções.

**Distinção física aberta:** `expected_cycle_version` do PR #12 indica versão comercial; não inferir `expected_case_version`, `form_version`, `assignment_version`, nem versão do catálogo a partir dele. Recibo S0 de hash/watermark **não contém** histórico integral, transcrição, documentos, catálogo nem autorização de transferência ao provedor.

## 6. Testes de aceite futuros (não executados nesta frente)

- Duas lojas com mesmo número/CPF e histórico: F03 da A jamais consulta B.
- Dois fechamentos, mensagem posterior ao primeiro, dados retificados: corte antigo preservado; persistência antiga impedida se obsoleta.
- Fonte válida em caso antigo da **mesma loja**, com autoria, datas e mídia autorizada; fora da loja recusada.
- Ficha após remessa: atualização viva sem mutação do snapshot bancário; `vendido` nunca automático.
- Desistência inequívoca gera proposta de `perdido` com evidência; negativa bancária formal exige operação humana separada.
- Dado opcional explicitamente informado não omitido; campo essencial ausente retorna à revisão, sem permitir edição pelo Consultor.
- Mídia indisponível/expirada e retenção incerta: diagnóstico honesto, sem fabricar transcrição.
- Corrida de versões, evento falso, autorização revogada, duplicação/retry e JSON malformado: negar ou revisar sem efeitos.

**Pendências para a issue #4:** esquema/identidade do cliente com múltiplos telefones, recorte histórico, multimodal/privacidade, catálogo, versões distintas, políticas de aplicação idempotente e ratificação S0↔OpenAI↔FV. **Banco direto permanece adiado.**
