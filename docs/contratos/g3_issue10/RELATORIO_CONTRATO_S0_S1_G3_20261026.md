# Issue #10 — catálogo físico e contrato de retomada S1/G3

26/10/2026, São Paulo. **Entrega auxiliar para revisão do Codex principal.** Branch exclusiva `aux/s1-g3-issue10-catalogo-20261026`, criada da S0 `060b472`. Não integra PRs nem altera S0 principal, S1, outras frentes, banco hospedado ou produto.

**Conclusão:** a dependência de levantamento recebe uma resposta rastreável. Existem contatos, ciclos, casos, atribuições e mensagens sintéticas em SQL; existe leitura contextual candidata na S1 e controle restrito CFI-01 em outro PR. **Não foi identificado serviço implementado de mídia/anexos, Storage de aplicação, download ou URL assinada nas fontes auditadas. Não há catálogo produtivo D3/D4 nem matriz ratificada por campo. G3 continua parcial.** A I75D pode confrontar estes objetos com I75B/I75C e tratar os bloqueios abaixo sem refazer I61–I74.

## 1. Proveniência e significado de “existe”

| Frente | Ref consultado por Git/connector | Estágio observado |
|---|---|---|
| `main` | `dace737ab7afb7ae3f5a3a6f5cb522e6def8b43a` | Somente README inicial; não é aplicação integrada |
| S0 fundação | `75095fe9b6050c704df37c663bb92595bc6513b6` | Migrations/contratos sintéticos |
| S0 atual / PR #4 | `060b472b03e9e7b89f5b3d7e19b72b98836f106d` | Base desta auxiliar; núcleo em laboratório |
| S1 / I75C | `e868b5dbd98b107f4ebd3f9f7087e24ec8518dbe` | I74 certificada na frente; I75B estático e I75C catálogo; I75D aguarda retorno |
| CFI-01 / PR #9 | `ff623482fca0eb1857a64b51959e3716bc0216d7` | Draft; executor de código `1b4f284`, recibo/nonce/auditoria restritos em fixtures |
| UI / PR #11 | `ddec1b80444bfde871d43a02d0ee94b9ed7cde11` | Draft; envelope/validação candidatos; sem transporte/lookup/SQL novos |
| Meta / PR #8 | `cb7fc3e2eacdaad9b8d47ffca1284759ca3357a3` | Draft; webhook/observação HTTP offline; sem Graph/ACK durável/Storage |
| Composição Meta / PR #7 | `450dcd645f35d4c8bf93e974e75d3b09467965a7` | Draft; patches e composição de laboratório; não M2M operacional |
| F03 / PR #1 | `a7ba0136ae7c7907cc5b7f9ad0ee6b6ae499125e` | Draft; histórico, fichas e mídia sintéticos isolados; não importados pela S0 atual |
| Frontend | `e44a14dbc89e8c443bed08ea06c20a1f16f4ac12` | Projeções/fixtures visuais; não barreira de acesso ao banco |
| S2 | `ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c` | Adaptadores/propostas sintéticas; sem autoridade SQL |

Checkpoints recuperados: [S0 atual][s0-checkpoint], [CFI-01 restrito][p9-report], [S1 I74 e gates][s1-checkpoint], [S1 I75A][i75a], [I75B][i75b], [I75C][i75c]. Os resultados históricos de CI citados nesses documentos são **evidências declaradas pela frente**, não execuções refeitas nesta tarefa. A enumeração e os testes novos estão em `evidence/execution.json`.

Estágios deste contrato:

- **Implementado em fonte/laboratório:** DDL/runtime existente no SHA indicado, podendo ser materializado em PG17 descartável. Não significa implantado/homologado.
- **Experimental:** fixture/porta local executável, separada das migrations canônicas e de outros PRs.
- **Proposto:** requisito ou contrato ainda sem aprovação/implementação operacional.
- **Ausente no recorte:** nenhum componente correspondente identificado nas fontes fixadas. Não é afirmação sobre o catálogo de um projeto hospedado, que não foi consultado.

O índice `evidence/source-inventory.json.gz` registra 11 snapshots completos, árvore, caminhos, blobs Git, SHA-256, declarações lexicais e menções/consumidores por linha. Menção em comentário/teste não é implementação. Catálogos `*-catalog.json.gz` são metadados reais do PG17 inicializado nesta tarefa: owners, tipos, colunas, FKs/checks, RLS, policies, ACLs efetivas por coluna/role e funções privadas. `columns.csv` facilita a comparação. Nenhuma linha de cliente/segredo foi exportada.

## 2. Objetos físicos de histórico e identidade

As 11 relações I75B/I75C estão abaixo. Schema `public`, owner SQL `postgres` nos perfis materializados. S0 é responsável pelo domínio; S1 possui os candidatos de autorização. **Não há owner humano/tenancy implícito no owner SQL.** Colunas completas, incluindo alterações posteriores, estão no CSV e nos catálogos; as colunas abaixo explicam finalidade/isolamento.

| Objeto | Colunas/chaves relevantes presentes na S0 atual | Fonte e estágio |
|---|---|---|
| `leads_loja` | `id`, `concessionaria_id`, `telefone_cliente_normalizado`, `criado_em`; UNIQUE loja+telefone e loja+id | [001][s0-001], implementado sintético; telefone sem mascaramento no banco |
| `ciclos_comerciais` | `id`, loja, `lead_id`, `status_comercial`, `aberto_em`, `ultima_transicao_em`, `versao_registro`; FK loja+lead; oito status | [001][s0-001]/005, implementado; status “cadastro enviado ao banco” não é arquivo/prova bancária |
| `casos_humanos` | `id`, loja, `lead_id`, `ciclo_id`, `origem`, `criado_em`, `motivo_simulado`; consistência loja+ciclo+lead | [003][s0-003]/005/009, implementado; versão física de ciclo não é versão de caso |
| `atribuicoes_humanas` | `id`, loja, `caso_id`, `operador_id`, `atribuida_em`, `encerrada_em`; uma atribuição ativa por caso | [003][s0-003]; escrita limitada à atribuição corrente |
| `conversas` | `id`, loja, `lead_id`, `canal_id`, `caso_id` anulável, `origem`, `criada_em` | [003][s0-003]/005; caso+contato coerentes; S1 I59 reforça FK, sem novos grants |
| `mensagens` | `id`, loja, `conversa_id`, `canal_id`, `caso_id` anulável, `direcao`, `origem`, `conteudo_sintetico`, `id_externo`, `enviada_por`, `criada_em`, `roteamento_simulado` | [003][s0-003]/009/034; não contém bucket, path de anexo, MIME ou URL assinada |
| `itens_lote` | `id`, loja, `lote_id`, `ordinal_linha`, `lead_id` anulável para rejeitados, `resultado`, `motivo_rejeicao`, data | 003/006/031; linha pode estar sem contato; não liberar bruto por mera presença no lote |
| `reencontros_lote` | loja, lote, lead, `motivo`, data | 003; administrativo relacionado ao contato, não concessão de acesso |
| `eventos_status_comercial` | loja, `ciclo_id`, `versao_ciclo_apos`, status anterior/posterior, `tipo_origem`, data, `mensagem_simulada_id` | 003/009; histórico sintético, não prova Banco/Meta |
| `lotes_importacao` | loja, `chave_importacao`, `origem`, data, `payload_fingerprint` | 003/006; cabeçalho compartilhado entre contatos/equipes |
| `canais_loja` | loja, `identificador_emissor` globalmente único, `modo='simulado'`, data | 003/010; canal não é telefone do cliente |

Objetos associados existentes, também enumerados no catálogo:

- `atores`, `vinculos_papel_escopo` e `concessionarias`: identidade Auth, concessão com `papel/valido_desde/valido_ate`, estado da loja. Papéis persistidos são `operador/gestor/responsavel`, com exibição Consultor/Gestor/Diretor; renomear exibição não concede direitos.
- `prumo_private.aliases_identidade_s0`, `eventos_identidade_s0`, `pendencias_identidade_s0`: alias/decisão de identidade **por loja**, com número/variante sintéticos. Uma variante numérica não é prova de identidade civil ou titularidade. Conflito vai para pendência; não unir arbitrariamente contatos. [028][aliases]
- `catalogo_templates_sinteticos` (`codigo/versao/aprovado_simulacao`), `planos_recontato_sinteticos` (loja/lead/ciclo/canal/finalidade/estado/versão), `envios_template_sinteticos`, eventos/callbacks/reconciliação: transporte e elegibilidade simulados; nenhum template Meta real homologado por essa flag.
- `evidencias_elegibilidade_sinteticas`, `supressoes_contato_sinteticas`: finalidade/opt-out sintéticos. Bloqueio de envio não equivale a exclusão de histórico nem a permissão documental.
- Inbox/outbox/tarefas privadas S0 (`inbox_eventos_s0`, `inbox_c02_fixture_s0`, `aplicacoes_c02_inbox_s0`, `tarefas_ingresso_s0`, `historico_tarefas_ingresso_s0`, `outbox_intencoes_s0`) e bindings `meta_apps_fixture_s0`, `meta_canais_fixture_s0`, `meta_vinculos_tentativa_fixture_s0`: recursos técnicos de laboratório, não acervo de mídia. O catálogo contém seus campos/ACLs exatos.

### Chave e segmentação do contrato

Histórico lógico: **`(concessionaria_id, leads_loja.id)`**; `conversas.lead_id` liga cada conversa e suas mensagens ao contato. `mensagens` não tem coluna `lead_id`: o vínculo exige JOIN por **loja+conversa**. `casos_humanos` e `ciclos_comerciais` também carregam loja+lead. A consulta contextual atravessa casos/ciclos/canais autorizados sem perder autoria/segmento e pode incluir conversa pré-caso (`caso_id IS NULL`).

O telefone é atributo/alias e chave de unicidade **dentro da loja**, não chave global do histórico. Canal usa `canal_id + concessionaria_id`; `id_externo` inbound é deduplicado por loja+canal+id externo. App/WABA/phone/revisão nos contratos Meta são outra identidade de transporte, não substituem lead ou atribuição.

Escrita exige **caso+atribuição corrente+ator+loja** e suas concessões; histórico antigo não transfere essa autoridade. Transferência fecha a atribuição anterior e cria contexto novo; não reescreve autoria nem torna o novo titular remetente de mensagem antiga. O pós-encerramento/arquivamento não é licença eterna: permanece dependente de titularidade/autorização vigente e da retenção a definir.

## 3. Leitura contextual, RLS, revogação e envio

| Perfil/camada real | Leitura | Escrita/envio | Limite observado |
|---|---|---|---|
| S0 002/004/008 | Consultor com grant vigente e atribuição lê caso/conversa correspondente; Gestor com grant de loja lê D2 amplamente na loja | `authenticated` tem INSERT só em colunas de mensagem sintética; RLS exige autoria própria, saída, caso e atribuição ativos | S0 não implementa supervisão por equipe nem histórico completo entre casos; SELECT de tabela não minimiza campos |
| S1 migrations até I61 | Acrescentam equipe ativa, chefia, guardas de atribuição/fila e ledger de exceção | I61 liga exceção a ator+loja+caso+UUID da atribuição, revogável; pausa de intake não é revogação do caso existente | **Criar a exceção não instala a candidata I63** |
| S1 I63 [fixture][i63] | Oito policies, união permissiva + barreira restritiva nas quatro tabelas de caso/atribuição/conversa/mensagem; Consultor titular atual acessa histórico do contato; Gestor depende da participação de sua equipe no caso | Policies são SELECT; não ampliam INSERT | Helpers são DEFINER `postgres`, schema de teste; não são solução produtiva de owner mínimo |
| S1 I64–I74 | Quarentena de cabeçalhos/indiretos, recorte por linha/coluna, views invoker, exportação limitada/assinada | Não criam acesso documental nem envio Meta | Fixtures candidatas; baseline canônica não as contém após rollback |
| PR #9 CFI-01 | Executor interno lê somente colunas necessárias para snapshot do caso | Login real só executa porta atômica; owner NOLOGIN sem BYPASSRLS; locks mínimos com UPDATE(id) e WITH CHECK false; nonce+recibo+auditoria atômicos | Não oferece leitura contextual pública, documentos, campo F03 ou envio; ponte mantém `VERIFIED_CONTRACT_PENDING` |
| PR #11 | Valida forma/correlação do envelope | Nenhum dispatch, transporte, novo SQL ou binding de recheck | D1–D4 do PR são decisões de protocolo pendentes; **não** classes de dados D2/D3/D4 |

**Revogação rastreável:** expirar/revogar grant de loja corta leituras na próxima avaliação; fechar a última atribuição elegível corta leitura contextual do Consultor; encerrar chefia corta supervisão candidata do Gestor. I61 considera exceção vigente, atribuição exata, equipe/chefia/loja habilitadas; mudança de titular invalida aquela atribuição. Não inventar grant geral para acomodar uma exceção. Diretor não possui leitura universal por rótulo de papel; o teste novo confirma isso para mensagens.

**Lacuna de sessão, confirmada sem extrapolar:** os predicados SELECT S0 e I63 testados dependem de `auth.uid()` e vínculos; não consultam `auth.sessions`. Mantido o mesmo GUC de identidade, DELETE de sessão sintética preservou a leitura. É uma prova negativa da hipótese “esta RLS corta leitura no logout”, **não teste com token GoTrue nem demonstração de ataque ao serviço hospedado**. O helper CFI-01 do #9 aceita sessão sintética viva e nega a apagada sob lock, mas esse controle pertence à operação CFI; não pode ser atribuído à leitura contextual ou a download inexistente. A I75D precisa verificar o caminho efetivo de cada leitura com sessão real.

**Supervisão não é titularidade:** no seed novo, Consultor atual vê 3 mensagens (caso atual, caso antigo, pré-caso) com I63. Gestor da equipe atual vê 2: caso atual e pré-caso; o caso antigo ligado à outra equipe fica negado. Na S0 sem candidata, o Gestor da loja vê 4 mensagens da loja, inclusive outro contato. Essa diferença deve permanecer explícita; a política candidata não foi promovida a regra nova. O requisito S1 vigente prevalece sobre descrições antigas “Gestor vê toda a loja”.

Não existe prova de envio externo nesta tarefa. INSERT sintético autorizado, intenção outbox, HTTP 2xx, API_ACCEPTED, delivered e autorização humana são eventos diferentes. #8 não concede ACK, retry, mutação comercial ou permissão documental. #7 não homologa M2M/ordem global de locks. Nenhum dos três PRs solicitados resolve essa lacuna por composição automática.

## 4. D2, D3, D4, fichas, atestados e documentos

| Classe | Existência física constatada | Consultor / Gestor / Diretor | Minimização, finalidade, retenção e arquivo |
|---|---|---|---|
| D2 conversacional/operacional | Identificadores, telefone, conteúdo sintético, direção/autoria/datas/status e relações acima | Consultor: contexto do contato autorizado, sem carteira alheia. Gestor: supervisão da própria equipe, sem envio sem assumir. Diretor: competências administrativas não significam leitura universal | **Lista produtiva mínima por campo não ratificada**. `conteudo_sintetico` é texto livre e não sanitiza informação sensível por nome; não usar SELECT amplo como contrato de UI/IA. Mascaramento produtivo não identificado |
| D2 administrativo | Linhas de importação, reencontros, eventos, cabeçalhos | Candidatos I67–I74 limitam linhas do Gestor autorizado; Consultor excepcional não recebe administração bruta | I68 propõe itens: loja/lote/ordinal/lead/resultado; reencontros: loja/lote/lead; eventos: loja/ciclo/versão/status posterior. Projeções agregam somente linhas autorizadas, excluindo emissor/cabeçalho bruto. Isso é recorte **experimental existente**, não nova lista aprovada |
| D3 cadastral/sensível | Não há schema produtivo de ficha classificado por campo. PR #1 tem `cfi01_f03_form_fields_local` com `campo_sintetico/valor_sintetico` e versões | Nenhuma lista de campos D3 produtiva para os três papéis foi encontrada. Supervisão/histórico não concede ficha bruta; proposta de modelo não concede escrita | Categoria/mascaramento/origem/finalidade por campo pendentes. Form fixture não prova identidade/renda, consentimento ou homologação Banco |
| D4 documental/bancário | Não identificados repositório de arquivos bancários, remessa/download ou prova bancária operacional; UI tem demonstração `bank-view.mjs` | Nenhum direito bruto inferido para qualquer cargo. Estar na conversa ou ter status comercial não torna documento legível | Retenção, expurgo, base/finalidade, arquivo e transferência precisam de decisões de Produto/LGPD/Banco e objetos físicos reais |

**PR #1 merece registro, não importação:** declarar “não existe nenhuma tabela de mídia/ficha em nenhuma frente” seria incorreto. Existem fixtures privadas reais, fora da S0 atual e fora do #9:

- `cfi01_f03_message_modalities_local`: `mensagem_id`, loja, `tipo` TEXT/AUDIO/IMAGE/VIDEO/DOCUMENT/UNKNOWN, `estado`, `anexo_sha256`, data. Modalidade e digest sintéticos; não guarda anexo.
- `cfi01_f03_media_attestations_local`: loja, fechamento, caso, mensagem, `proposito='F03_POST_HUMAN_REVIEW_SYNTHETIC'`, versão de chave, hashes de anexo/transcrição/prova HMAC, `valido_ate/atestado_em`. TTL do atestado **não é TTL de download**. O módulo retorna estado técnico, não bytes/transcrição ou autoridade F03. [Fonte SQL][f03-media], [leitor][f03-reader].
- `cfi01_f03_history_seals_local` e `cfi01_f03_content_proofs_local`: pertencimento/cutoff/fingerprints do histórico e recibo; hash não concede acesso nem comprova verdade semântica.
- `cfi01_f03_form_fields_local`, `catalog_entries_local`, `operational_field_contracts_local`, `lead_versions_local`, `case_versions_local`, `catalog_versions_local`, `reservations_local`, `form_application_local`, `form_application_items_local`: ficha/catálogo/versões/aplicação **sintéticos privados**, com guardas. Não afirmar que o PR apenas propõe dados em memória; há DDL e writers de bancada, porém nenhum catálogo D3/D4 produtivo homologado.
- Fixtures de identidade `cfi01_f03_identity_resolution_local`, `identity_human_reviews_local`, `identity_ratifications_local` também existem na fonte. São indexadas, mas não instaladas no perfil físico reduzido F03 deste pacote.

O perfil F03 materializa sete fixtures pertinentes, depois dos pré-requisitos CFI, para catalogar/sondar permissões; **não compõe esse PR com o #9**. Cada perfil usa seu próprio SHA, container e banco. O #9 possui somente recibo/chave/nonce/auditoria CFI e gate de equipe local; não possui essas tabelas F03 adicionais. Conteúdo privado continua negado ao cliente SQL `authenticated` no perfil instalado, sem declarar que isso testa D3/D4 reais.

## 5. Storage, URLs, retenção e revogação

| Capacidade | Resultado rastreado | Consequência para I75D |
|---|---|---|
| `storage.objects`, `storage.buckets` | Ausentes nos cinco catálogos materializados (quatro perfis + snapshot I63). Nenhum bucket de aplicação identificado nas fontes | Não afirmar inexistência no projeto hospedado; não houve consulta a ele. Schema genérico Supabase, se existir em outro stack, não prova acervo da aplicação |
| Upload/download de anexo, path/owner/MIME, ACL de objeto | Não identificados como caminho implementado de aplicação | Não criar endpoint/tabela para simular autorização concluída |
| Emissor/validador de URL assinada, TTL/cache, thumbnail, preview, replay | Não identificados para arquivos reais | Teste “URL antiga negada” **não executável neste recorte**, não PASS |
| Retenção de conversa/ficha/arquivo/auditoria e acesso após arquivamento | Política de negócio e expurgo operacional não ratificados | Registrar decisão por classe/propósito/titular antes de operar; não preencher prazo arbitrário |
| Nonces S0 | `expurgar_nonces_gateway_s0` impõe retenção técnica mínima de 10 minutos; chaves possuem validade/estado/auditoria | Essa janela técnica não é prazo LGPD, de conversa ou de arquivo |
| Atestado de mídia F03 | `valido_ate` e checagem de expiração/integridade da prova sintética | Não revoga bytes baixados nem URL, não implementa eliminação do documento |
| Perda de acesso/transferência | Concessão/atribuição/equipe/exceção governam futuras leituras quando efetivamente aplicadas | Exigir revalidação na rota real; conteúdo já entregue/exportado/cacheado não é recuperado pelo DELETE de um grant |

Documentação Supabase consultada por MCP em 26/10: [downloads e signed URLs](https://supabase.com/docs/guides/storage/serving/downloads), [Smart CDN](https://supabase.com/docs/guides/storage/cdn/smart-cdn). Assinatura/expiração, Auth, cache e revogação precisam ser tratados separadamente; mudança de chave Auth não é prova de invalidação de URL Storage. Isso é referência técnica externa, **não arquitetura escolhida nem evidência de Storage instalado**. O changelog Markdown foi solicitado, mas o leitor web rejeitou seu content-type; não se implantou feature dependente dele.

## 6. Writers/readers e atalhos indiretos

| Caminho existente | Objetos/consumidores | Restrição/pendência |
|---|---|---|
| S0 C01/C02 e identidade | `importar_lote_sintetico`, `importar_lote_identidade_s0`, `receber_mensagem_sintetica`, `receber_mensagem_identidade_s0`, `aplicar_inbox_c02_s0`; SQL privado de laboratório escreve lead/ciclo/caso/conversa/mensagem/evento | Não são endpoints HTTP operacionais nem rotas de mídia; não confiar em `p_ator` isoladamente como autenticação |
| Cliente SQL/PostgREST modelado | Policies 002/004/008; SELECT D2 e INSERT de mensagem sintética | Data API efetivamente exposta/configurada no hospedado não foi verificada; grants e RLS são camadas distintas |
| CFI-01 #9 | `s0_cfi01_atomic_commands_local.py`, `s0_human_closure_event_local.py`, captura/recheck, recibo e auditoria privados | Consulta conteúdo para fingerprint interno do caso, não abre esse conteúdo à UI/F03; sessão/versão/atribuição rechecadas |
| F03 #1/S2 | `s0_f03_history_manifest_local.py`, seals/content proofs, validadores/catálogos e escritor sintético de campos; S2 recebe/propõe estruturas, sem autoridade de banco | Leitor de histórico usa loja+lead e cutoff do recibo; proposta/atestado não autoriza provedor, escrita produtiva ou documento |
| Meta #7/#8 | Inbox/outbox/bindings de teste; parser HMAC/lote; `cloud-webhook-handoff.ts`, `cloud-wire-observation.ts`, `graph-outbound.ts`, `graph-template.ts` | Transporte real, reserva antes de Graph, resultado incerto, M2M, ACK após durabilidade e locks globais permanecem contratos pendentes |
| S1 indiretos | Wrappers `prumo_s1_interface`, predicados I63, quarentena I64/I66, projeções I68, exports I69–I74 | I66 retira uso cliente do legado; I67 identifica `s1_gateway_local.py` como adaptador I19 aposentado. Não desquarentenar para fazer UI funcionar |
| Frontend | `s0-read-contract.mjs`, `registration-view.mjs`, `bank-view.mjs`; simulações de conversa/ficha/resumo bancário | O parser de leitura exige dados já minimizados; filtro visual não é RLS, assinatura de DTO não é concessão |
| Analytics/exports/SQL dinâmico externos | Nenhum serviço produtivo correspondente certificado por este levantamento | Inventário lexical só alcança fontes rastreadas; não prova inexistência de outros consumidores ou cópias de dados |

Os catálogos preservam ACL/configuração/owner de funções privadas para revisão de DEFINER e schemas. Os candidatos I68 usam `security_invoker=true`; a existência de uma view/função com nome de exportação não é licença de leitura irrestrita. Os testes originais I64–I74 permanecem a evidência da frente, sem serem recontados como testes novos desta auxiliar.

## 7. Provas executadas e limites

**PG 17.11, imagem fixada por digest, containers sem rede/portas/volumes, dados inteiramente sintéticos.** Quatro containers independentes, removidos ao terminar; nenhuma conexão hospedada. O runner transmite SQL de SHAs fixados por stdin, não edita/copia migrations para o checkout S1. Instala somente migrations da respectiva frente, mais as fixtures explicitadas no manifesto.

| Prova nova | Resultado físico |
|---|---|
| G3-01/02 — isolamento e histórico | S0: 1 mensagem autorizada; S1+I63: 3 do mesmo contato, incluindo caso antigo e pré-caso. Outro contato e mesmo telefone em outra loja negados |
| G3-03 — leitura versus escrita | INSERT sintético no caso atual passa como controle positivo; no caso antigo é negado, inclusive quando SELECT histórico passa |
| G3-04/09 — supervisão | Gestor não escreve sem atribuição; candidata respeita participação por equipe; após encerrar chefia, deixa de ler. S0 ampla por loja fica registrada como diferença |
| G3-05 — Diretor | `responsavel` sem outras alçadas não lê mensagens automaticamente |
| G3-06 — logout/SELECT | **Lacuna demonstrada:** apagar sessão sintética mantendo `auth.uid()` não bloqueia SELECT S0/I63. Não chamado de teste de logout GoTrue |
| G3-07/08 — revogação | Fim de grant ou da última atribuição corta próximas leituras do Consultor com a mesma identidade SQL |
| PRIVATE-01 | SELECT de recibo privado negado a authenticated; no perfil F03, ficha sintética/atestados existentes também negados |
| PRIVATE-02 | **Conexão com `session_user` real do login SQL restrito** não lê mensagens nem assume owner; não apenas SET ROLE de postgres |
| PRIVATE-03 | Helper CFI real do perfil aceita sessão sintética viva e recusa a apagada; não é captura/recheck com GoTrue |
| Higiene | ROLLBACK dos probes preserva catálogo S0/S1 byte a byte no mesmo banco e remove sementes; oito policies I63 não persistem; containers removidos |

O JSON registra os perfis e cada arquivo/ref aplicado. Logs possuem marcadores/asserts e identidades sintéticas, sem dados reais. Há **1.988 registros de coluna** no CSV somando perfis repetidos (não 1.988 colunas únicas de produto). Cinco catálogos contêm respectivamente 42/56/56/48/60 relações; isso não equivale a 262 tabelas implementadas ou a cobertura produtiva.

Não executados: Meta/Graph, GoTrue/PostgREST nesta auxiliar, download real/URL antiga, D3/D4 bancários, corrida de rede/logout/arquivo, browser, retenção produtiva ou consumidores externos. Não declarar I75A 8/8, G3 concluído ou integração final concluída.

Intercorrências de montagem, corrigidas sem afrouxar autorização: espera inicial podia observar servidor temporário do entrypoint Docker; passou a aguardar TCP loopback do servidor final. A expectativa inicial de supervisão contava um caso histórico da outra equipe; a asserção foi corrigida para a participação real (2). Um teste inicial tentava provar impossibilidade de SET ROLE após partir de `session_user=postgres`; foi substituído por conexão do login restrito, pois um superusuário mantém poderes de sessão. As execuções finais dos quatro perfis passaram com as verificações corrigidas. Falhas iniciais não são contadas como aprovação.

## 8. Contrato de retorno e instruções I75D

Esta entrega **não cria direito de acesso ou política comercial**. Consolida os fatos acima e os requisitos já vigentes da S1. `CONTRATO.json` expõe chaves, cenários e lacunas em forma legível por ferramenta; campos sem decisão permanecem nulos/pendentes.

1. Revisar esta auxiliar a partir da S0 `060b472`; conferir os SHAs em `source-inventory`, manifestos, logs e catálogo. Não importar automaticamente #8/#9/#11 ou as fixtures #1.
2. Confrontar as 11 relações I75B/I75C com `columns.csv`; usar `s1-catalog` como **migrations canônicas**, `s1-i63-candidate-catalog` como **candidata temporária**, nunca como estado implantado. Preservar as certificações I61–I74; não reescrever signer/exportador.
3. Para I75-G3-01/02/03/05/08, reaproveitar as provas/contratos S1 e testar a futura composição efetiva, com atores reais, a autorização do mesmo contato/loja, exceção I61, chefia e limites de escrita. Fechar recortes de colunas/texto livre antes de ligar UI/IA/exports.
4. Para I75-G3-04, o Codex principal/S0+S1 deve decidir e demonstrar onde cada leitura consulta sessão viva, grant, titularidade, exceção e equipe. Não transportar a garantia de sessão do CFI para SELECT histórico. Ordem global de locks e concorrência entre revogação e leitura ainda precisam de composição supervisionada.
5. Para I75-G3-06, Produto/LGPD+S0 precisam ratificar classes/campos mínimos por Consultor/Gestor/Diretor, finalidade/origem, mascaramento, consentimento quando aplicável, retenção/expurgo e pós-arquivo. **Nenhum prazo ou campo financeiro foi escolhido aqui.**
6. Para I75-G3-07 e documentos bancários, registrar **bloqueado por componente ausente**, sem endpoint fictício. Se houver futura implementação, inventariar primeiro objeto, identidade, armazenamento, leitor, ACL, revalidação, TTL/cache/preview/replay e tratamento após perda de acesso; só então executar negativos de URL antiga/duas lojas/arquivo bancário.
7. CFI/F03: #9 é execução técnica restrita; #11 continua candidato; `case_version`, `cycle_version`, atribuição, ficha, catálogo, cutoff e binding de recheck não são intercambiáveis. O retorno desta Issue não ratifica D1–D4 do #11 nem concede autoridade F03.

**Estado recomendado da Issue #10:** retorno entregue para revisão, Issue aberta até aceite do Codex principal. **Estado G3:** parcial/bloqueado em sessão da leitura operacional, classificação fina, mídia/documentos e retenção. A S1 pode retomar a análise I75D com essas respostas e avançar em outros gates independentemente. Integração, merge e deploy permanecem etapas posteriores não executadas.

[s0-checkpoint]: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/060b472b03e9e7b89f5b3d7e19b72b98836f106d/docs/auditoria/S0_ESTADO_NUCLEO_20261025.md
[p9-report]: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/ff623482fca0eb1857a64b51959e3716bc0216d7/docs/operacional/S0_CFI01_BACKEND_RESTRITO_20261026.md
[s1-checkpoint]: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/e868b5dbd98b107f4ebd3f9f7087e24ec8518dbe/docs/S1_002_CHECKPOINT_I74_E_GATES_2026_10_26.md
[i75a]: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/e868b5dbd98b107f4ebd3f9f7087e24ec8518dbe/docs/S1_002_I75A_GATE_G3_OBJETO_FINALIDADE_2026_10_26.md
[i75b]: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/e868b5dbd98b107f4ebd3f9f7087e24ec8518dbe/docs/S1_002_I75B_G3_INVENTARIO_EXECUTAVEL_2026_10_26.md
[i75c]: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/e868b5dbd98b107f4ebd3f9f7087e24ec8518dbe/docs/S1_002_I75C_CATALOGO_EFETIVO_G3_2026_10_26.md
[s0-001]: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/060b472b03e9e7b89f5b3d7e19b72b98836f106d/supabase/migrations/202610170001_s0_foundation.sql
[s0-003]: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/060b472b03e9e7b89f5b3d7e19b72b98836f106d/supabase/migrations/202610170003_s0_domain.sql
[aliases]: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/060b472b03e9e7b89f5b3d7e19b72b98836f106d/supabase/migrations/202610180028_s0_identidade_aliases_sinteticos.sql
[i63]: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/e868b5dbd98b107f4ebd3f9f7087e24ec8518dbe/supabase/tests/s1_087_rls_excecao_canonica_local_only.sql
[f03-media]: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/a7ba0136ae7c7907cc5b7f9ad0ee6b6ae499125e/supabase/tests/s0_f03_media_attestation_local_only.sql
[f03-reader]: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/a7ba0136ae7c7907cc5b7f9ad0ee6b6ae499125e/backend/s0_f03_media_attestation_local.py
