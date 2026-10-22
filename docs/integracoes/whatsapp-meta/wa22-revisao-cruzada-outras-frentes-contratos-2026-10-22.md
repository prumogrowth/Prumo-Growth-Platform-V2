# WA-22 — Revisão documental cruzada das outras frentes relevante ao WhatsApp/Meta

**Data:** 22/10/2026. **Natureza:** inspeção de contratos e decisões em branches **Draft** independentes, para beneficiar a frente WhatsApp/Meta. **Escopo:** documentação, pontos de interface e riscos; **NÃO** revisão exaustiva de código, homologação, SQL real, deploy, merge ou aceite da outra frente.

> **NOME DO PROJETO — DECISÃO PRESERVADA:** estamos desenvolvendo uma **plataforma de atendimento comercial, ainda SEM nome comercial próprio definido, operada pela Prumo**, destinada a apoiar concessionárias na comercialização do **LiberaCred, produto da instituição financeira**. **Não chamar o software/plataforma de “LiberaCred”** em documentação nova. Referência histórica **já aprovada**, `documentos/17_Identidade_e_Nome_da_Plataforma_v0_1.md` (pacote 17/10); confirmada diretamente pelo responsável em 22/10 e usada na frente OpenAI. Nomes de arquivo/branch antigos que contêm “Liberacred” são apenas legados; manter referências históricas intactas.

## 1. Fonte e método: branches separadas, data e autoridade

| Frente efetivamente revisada | Fonte atual consultada | Natureza |
|---|---|---|
| **S0 fundação** — PR [#1](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/1), branch `feat/s0-fundacao-prumo` | `docs/S0_043_PAUSA_SELETIVA_E_INDICADOR_CONVERSA_2026_10_20.md`, `docs/S0_044_ALINHAMENTO_FILA_GESTORES_IA_2026_10_21.md`, `docs/S0_045_NOMENCLATURA_DIRETOR_GESTOR_CONSULTOR_2026_10_21.md` | Decisões recentes e candidatos de laboratório; **não** supor S0 produtiva/atualizada em todo aspecto |
| **S1 pessoas, concessões e fila** — PR [#5](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/5), `feat/s1-002-equipe-prumo` | `docs/S1_002_DECISAO_NOMENCLATURA_PAPEIS_2026_10_21.md`, I11/I10 com errata, `docs/S1_002_ISSUE10_INDICADOR_MENSAGENS_S0_2026_10_20.md` | Conceitos de papel, pausa, autoria/leitura e RLS; protótipos SQL não são API real |
| **OpenAI/IA** — PR [#3](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/3), `feat/s2-openai-adapter-sintetico` | `ALINHAMENTO_2026_10_22_00_INDICE_E_PRECEDENCIA_v0_1.md`, `01_JORNADA_F01_F02_F03`, `02_CONHECIMENTO_CACHE_HABILIDADES`, `03_MCP_DIRETOR_GUIAS_AUDITORIA`, `07_DEPENDENCIAS_RELEVANTES_OUTRAS_FRENTES` (prefixos completos nessa pasta) | **Nova documentação de 22/10**; algumas decisões de produto posteriores aos documentos WhatsApp/Meta de 21/10; dependências ainda não ratificadas fisicamente |
| **CF-OP-02** — PR [#7](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/7), `docs/cf-op-02-cadeias-contextuais-20261018` | `docs/revisoes/CF_OP_02_DIRETRIZ_CADEIAS_JANELA_HUMANA_2026_10_18.md`, matriz CF-OP-02 | Contrato interfrentes de cadência pós-humana e três marcos temporais separados |
| **S0↔OpenAI F03/C09** — PR [#8](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/8), `coord/s0-openai-cfi01-c09-20261019` | `docs/S0_CF_OP_02_MATRIZ_SEGURA_RECONTATO_SILENCIO_v0_1.md`, `docs/F03_OAI07_BLOQUEIO_RECONTATO_BANCARIO_CFOP02_v0_1.md` | Contrato de **gate conservador**/simulações, não habilitação real de C09, envio ou banco |
| **S0↔F03 fechamento autenticado** — PR [#12](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/12), `feat/s0-cfi01-f03-auth-preflight-20261020` | `docs/S0_CFI01_F03_SNAPSHOT_METADATA_RATIFICATION_GATE_2026_10_21.md`, `docs/S0_CFI01_S1_TRANSACAO_ORDEM_LOCKS_2026_10_21.md` | Evidência PG17/GoTrue efêmera de **recibo interno**, sem F03 real, histórico multimodal ou produção |
| **Interface visual** — branch `feat/frontend-plataforma-visual`, independente | `frontend/docs/00_COMECE_POR_AQUI_DECISOES_VIGENTES_2026_10_21.md`, `35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md`, `37_D_NOM_01_NOMENCLATURA_DIRETOR_GESTOR_CONSULTOR_2026_10_21.md` | Decisões de interface e dependências, não prova de frontend ligado à API Meta |
| **Fontes originais de projeto** | Pacote 17/10 de 55 arquivos, especialmente `documentos/04`, `06`, `09`, `10`, `13`, `17`, `24`, `26`, `33`, `35`, `41` | Base histórica; trechos corrigidos por decisões posteriores não prevalecem só por serem antigos |

**Classificação:** **[D]** decisão expressa rastreada e coerente; **[R]** reconciliação interfrentes/contrato ainda necessária; **[P]** proposta técnica e não autorização; **[V]** regra externa pendente; **[T]** efeito técnico comprovado apenas no limite da evidência. Regra de conflito: preservar fontes e registrar divergência; não afirmar que documento recente altera um schema de outra frente.

## 2. Achados úteis, com efeitos exatos na nossa frente

### XWA-01 [D] — Nome e identidade: software sem marca; produto bancário separado

**Fonte:** `documentos/17_Identidade_e_Nome_da_Plataforma_v0_1.md` de 16/10 e AL-IA-00/07 da OpenAI em 22/10. O antigo título de `documentos/09` ou o nome do pacote ZIP não denomina o produto de software. **Aplicar em todos os novos títulos e textos:** “plataforma”, “frente WhatsApp/Meta da plataforma” e, quando necessário, “integração para comercialização do produto LiberaCred (instituição financeira)”. Não trocar IDs físicos, nomes de GitHub, nem apagar menções legítimas ao produto.

### XWA-02 [D/R] — Prova de interação humana é mensagem realmente enviada

**Fontes:** S0-044 e FV-DOC-01 D-AL-04. Um Consultor apenas abrir o caso, ler, receber atribuição, escrever rascunho ou clicar “enviar” **não prova contato humano**. Precisa de evento efetivo e tecnicamente comprovado de mensagem do humano na plataforma. A frente Meta deve produzir **correlação confiável de autoria humana + resultado de envio**, separando `API_ACCEPTED` de confirmação de transmissão, com identidade S0. Eventual **chamada via WhatsApp** só contará se capacidade Meta real e **ligação atendida** forem verificadas [V/T]; chamada tentada não serve e não foi autorizada integração de chamadas agora. Não inventar registro manual de ligação externa.

**Impacto WA-21:** cabeçalho `Consultor Nome:\n...` identifica a pessoa dentro do texto visível, mas **não é prova autenticada de contato** por si só. Backend usa identidade, atribuição e recibo correlacionado; prefixo textual não concede autorização.

### XWA-03 [D/R] — Pausa de intake ≠ suspensão de login ou perda do caso

**Fontes:** S0-043/044, S1 I11 e FV-DOC-01 D-AL-01..07. Pausar recebimento de leads novos **não suspende automaticamente** responder aos casos mantidos. Quando um caso já atribuído sem interação humana for redistribuído por pausa, preferência por profissional da **mesma equipe** com grant à concessionária; sem substituto, preservar titularidade sob atenção do gestor. **Novo lead** pode ser distribuído entre equipes diferentes autorizadas à loja; sem elegível, fica em fila sem titular acessível apenas a gestores autorizados. Não confundir novo lead sem titular com caso previamente atribuído ao pausado.

**Impacto Meta:** diante de texto/template solicitado por Consultor, revalidar autorização **do caso e da sessão**, não bloquear por `intake_paused` isolado. Inbound continua sendo roteado pela titularidade persistida S0; a IA F01 não recebe roster, escala ou disponibilidade do Consultor. S0/S1 validam escopo e exceção por caso [T].

### XWA-04 [D/R] — F01, F02 e F03 fazem coisas diferentes; F03 só no fechamento humano explícito

**Fontes:** AL-IA-01 (22/10), CF-OP-02 (#7) e CFI-01 (#12). F01 conversa com o cliente até handoff; F02 planeja templates já aprovados; **F03 é uma IA de extração/classificação silenciosa** acionada **somente pelo botão de conclusão do atendimento humano do Consultor**. A janela Meta de 24h expirar, a chegada de um template, a ausência de resposta ou a leitura **NÃO** acionam F03 nem concluem o caso.

**Impacto Meta:** manter **eventos distintos** de `customer_inbound` (abre/renova janela Meta), `human_message_sent`, `human_case_closed` (proveniente de S0 e não do webhook Meta) e `final_template_sent` (prova de início do relógio C09). O transportador Meta não marca caso como encerrado por timeout ou expiração da janela.

### XWA-05 [D/R/V] — Histórico lógico F03 por cliente/concessionária e corte imutável

**Fonte:** AL-IA-01 §§4–5 (22/10), PR #12 `S0_CFI01_F03_SNAPSHOT_METADATA_RATIFICATION_GATE`. Em cada fechamento humano, F03 deve poder **recuperar logicamente** histórico disponível de mensagens, autores, templates, IDs, timestamps, contexto e mídia autorizada do **mesmo cliente na mesma concessionária**, inclusive atendimentos anteriores, **até a última mensagem existente no instante do fechamento**, sem incorporar mensagens posteriores. Novo fechamento futuro tem novo corte. Isso não significa mandar todos os bytes históricos a cada prompt.

**Impacto Meta:** não considerar `conversa_id` isolada como limite do histórico F03; preservar IDs/timestamps/correlação, versões de template e autoria, anexos/mídias referenciáveis sem perder a origem, respeitar corte e privacidade. `mensagens` continua uma linha por mensagem, mas permitir consulta temporal e de múltiplos casos dentro da mesma loja/cliente via porta autorizada S0. **Lacuna real:** material original 06/08B/09 preferia não reter mídia bruta; requisito de F03 multimodal precisa política de guarda, autorização, referência externa e retenção [R/V], **não significa guardar mídia integral indefinidamente**. O recibo hash/watermark do PR #12 ainda **não transporta mídia ou payload multimodal para F03**.

### XWA-06 [D/R] — F03 e ficha: Consultor não edita campos cadastrais manualmente

**Fonte:** AL-IA-01 §4 de 22/10. O Consultor pode visualizar campos permitidos e conversar; **não terá ação rotineira de editar manualmente a ficha**. F03 pode propor atualização de dados após comando de concluir, usando versão, proveniência e validação S0; falha F03 é incidente crítico, não permissão rotineira para digitação manual. Isto é **posterior e potencialmente conflitante** com D41-04 (documento 41) e textos históricos de S1/S0 que permitiam correções humanas excepcionais. Sem reescrever esses documentos, marcar como **reconciliação [R] com donos S0/S1/OpenAI/frontend**.

**Impacto Meta:** não tratar extração de mensagem ou mídia como edição autorizada de cadastro, não criar formulário manual de correção no contrato WA; preservar o histórico para F03 e sua prova temporal. Remessa bancária e marcação humana de venda/negativa definitiva são operações separadas de editar campos cadastrais; não foram automaticamente revogadas.

### XWA-07 [D/R] — F03 pode propor perda por desistência, mas não venda nem prova bancária

**Fonte:** AL-IA-01 §5 (22/10). F03 pode propor e **desencadear** transição S0 autorizada de status comercial, inclusive `perdido` por desistência/ausência de interesse com motivo; decisão posterior revê bloqueio universal anterior. **Não pode marcar `vendido`**, fabricar negativa do banco nem presumir `cadastro enviado ao banco` sem remessa efetiva. A decisão de duas falhas técnicas consecutivas da WA-18C é OUTRA origem de `perdido`, determinada pelo backend, não F03 ou Meta.

**Impacto Meta:** mensagens/botões fornecem evidência comunicacional correlacionada para S0/F03; **o adaptador não decide status**, e uma resposta como “Não quero” não causa estado comercial automático diretamente no webhook. A atribuição de motivo de perda requer pipeline de interpretação/autorização apropriado.

### XWA-08 [D/R] — Três marcos temporais distintos; interação humana não se encerra com janela Meta

**Fontes:** CF-OP-02 PR #7, matriz C09 PR #8, AL-IA-01 PR #3. **Janela de texto livre Meta = último inbound válido do cliente +24h**; **conclusão humana = comando explícito do Consultor**, não relógio; **perda por silêncio final = 24h após comprovado `sent` do template FINAL**, para ciclo comercial elegível. O template final costuma ser candidato a aproximadamente 24h depois da última tentativa regular, que é outro prazo de planejamento, não o prazo C09. Templates enviados não reabrem janela de mensagem livre.

**Impacto Meta:** contrato deve fornecer timestamps/provas distintos; não usar `accepted` como `sent`; nunca iniciar C09 se final falhou, ficou incerto, opt-out bloqueou ou cliente respondeu. **PR #8 é gate conservador que não retorna ALLOW para C09 pós-humano**; homologação de quais fases podem perder por silêncio continua [R]. Isso não pode ser sobrescrito por cálculo no worker Meta.

### XWA-09 [D/R] — Mensagens lidas: indicador único e acesso supervisor independente

**Fontes:** S1 issue #10, S0-043, FV-DOC-01 D-AL-09. Interface terá único indicador: `COUNT` de inbound não lido pelo titular; `DOT` quando inbound foi lido mas ainda não recebeu resposta humana posterior; `NONE` após resposta correlacionada. Visualização do **Gestor em supervisão** não marca mensagem como lida pelo Consultor. **Indicador de leitura INTERNA não equivale ao status `read` do WhatsApp/Meta** e não deve ser confundido com recibo de leitura de cliente.

**Impacto Meta:** fornecer eventos recebidos/outbound e sua autoria/ordem; não assumir que timestamp/UUID definem ordem total segura quando callbacks podem ser reordenados; S0/S1 definem idempotência, leitura por atribuição e ordem persistida. Esses indicadores são protótipos sandbox, não exigência de endpoint Meta.

### XWA-10 [D/P] — Catálogo de conhecimento/ofertas e finalidades sem fabricar elegibilidade

**Fontes:** AL-IA-02 (22/10), `documentos/04` (marketing/campanhas fora do banco núcleo), WA-18C/00-01 Meta. A frente IA terá bases controladas por concessionária, fatos canônicos, gatilhos semânticos, metadados de fonte, autorização e vigência; a pesquisa aberta na web **não será padrão** para F01/F02/F03. **Fonte de conhecimento ≠ autorização para prometer desconto** e nem prova de elegibilidade de campanha. A regra já aprovada de **FINALIDADES** e grants dos templates deve coexistir com a decisão histórica de NÃO criar automaticamente um subsistema completo de captação/UTM/campanhas dentro da S0.

**Impacto Meta:** a plataforma precisa de **referência verificável de oferta vigente e elegibilidade do lead** antes de dar template promocional à F02, mas a **localização física da fonte de verdade** (núcleo, integração externa da gestora ou entidade operacional já existente) é **[R/P]**. Não aprovar nova tabela `campanhas` apenas porque o catálogo suporta FINALIDADES e nem usar texto gerado por IA como prova da oferta.

### XWA-11 [D/R] — Diretor/MCP: auditoria protegida; não confundir escrita de dados com mutação do software

**Fontes:** AL-IA-03 de 22/10 e 41 histórico. **Diretor** poderá solicitar gestão ampla de dados operacionais, inclusive templates e dados administráveis, com prévia, segunda confirmação da MESMA pessoa, escopo/idempotência e auditoria. **Novidade expressa:** o MCP não pode alterar, apagar ou sobrescrever sua **própria base de auditoria protegida**, mesmo após confirmação administrativa. Não concede DDL, mudança de regras estruturais nem permissão de modificar segurança. Operações sensíveis (como exportação) exigem desenho específico [R].

**Impacto Meta:** operações de criar/editar/desativar template, mídias, finalidades e permissões do catálogo deverão registrar autor, mudança, snapshot e resultado Meta em trilha protegida. O **servidor MCP, transporte, identidade e sua auditoria interna são OUTRA frente**; o domínio Meta expõe interfaces auditáveis, não implementa a execução MCP.

### XWA-12 [D/R] — S0/S1 F03: lock/recheck para evitar resultado de conversa obsoleto

**Fontes:** PR #12 CFI-01 `S0_CFI01_F03_SNAPSHOT_METADATA_RATIFICATION_GATE` e `S0_CFI01_S1_TRANSACAO_ORDEM_LOCKS`. Há prova física **limitada a ambiente efêmero** de recibo interno de encerramento com identidade, atribuição, versão do ciclo, hash, watermark e rechecagem. **Não** há envelope completo com mensagem/mídia e conteúdo necessário à F03. O PR #12 encontrou risco de **deadlock** se travar caso antes da equipe S1; ordem correta de bloqueio precisa obedecer contrato S1→S0.

**Impacto Meta:** eventos de mensagem com IDs deduplicados e autoria/instante consistente são insumos necessários para snapshots, mas **nossa integração não determina locks S0/S1 nem os escreve pelo webhook**. Se entrar mensagem nova após o cutoff, preservar no histórico e exigir nova decisão S0 quanto a reexecução/recheck; não sobrescrever uma extração encerrada com dados posteriores.

## 3. O que JÁ estava alinhado em nossa frente e não deve ser reaberto

- WABA/App/número e catálogo por concessionária conforme DEC-WA-05 (modelos Meta juridicamente previstos pela loja), Prumo integrada por delegação; homologação real [V].
- Mensagens, envios e catálogo de templates **separados**; versão exata e histórico de eventos; nunca presumir `sent` de `API_ACCEPTED`.
- Opt-out pedido à loja A não bloqueia B; autorização específica por loja; suporte existente apenas sintético no S0.
- Duas falhas definitivas em tentativas consecutivas → `perdido` com motivo técnico; `sent` comprovado entre elas zera contador independentemente de resposta; erro cotidiano não chama F02.
- Finalidades internas MULTIPLAS com concessão independente, separadas da categoria Meta `MARKETING`/`UTILITY`; F02 só recebe templates ativos/aprovados/elegíveis da loja/WABA, sem criar novos.
- Slot de variável do template congelado por versão aprovada; **plataforma** preenche valores no envio; editar conteúdo Meta só se API/estado permitirem.
- Cargos oficiais **Diretor, Gestor, Consultor**; assinatura textual de autoria humana `Consultor Nome:\nMensagem`, `Gestor Nome:\nMensagem` ou `Diretor Nome:\nMensagem`, quando mensagem livre for elegível; **não** prefixar templates já aprovados arbitrariamente.
- Separação entre IA de atendimento F01, Planejadora F02, extração F03, IA administrativa/MCP e melhoria de atendimento; sem atribuir autorização de banco/comércio ao modelo.

## 4. Lacunas novas para posterior auditoria TÉCNICA — sem decisões arbitrárias agora

1. **Mensagem enviada por humano:** qual evidência Meta/S0 constitui prova de interação humana para alocação/redistribuição do caso; o prefixo textual não é prova. Cuidado com mensagens tardias e operadora pausada só para intake.
2. **Histórico lógico F03:** identidade cliente/loja cruzando conversas/ciclos, limite de corte (inclusive última mensagem) e eventos fora de ordem; acesso multimodal autenticado, retenção e anexos com LGPD/Meta.
3. **C09 pós-humano:** matriz de estados elegíveis ainda não ratificada; corrida entre template individual e cadeia F02; `sent` final correlacionado, janela e silêncio distintos.
4. **Permissões do Consultor na ficha:** AL-IA-01 proíbe edição manual, enquanto D41-04 e fontes históricas autorizavam correções excepcionais; precisa emenda interfrentes, não ação no payload WA.
5. **Campanhas/ofertas:** como comprovar elegibilidade e vigência de campanhas sem contrariar proibição histórica de marketing/UTM no núcleo.
6. **MCP auditoria:** prova de trilha própria imutável, segunda confirmação, isolamento de concessionária e manutenção de versão dos templates; nenhuma tool executável é disponibilizada por esta revisão.
7. **Autoria e apresentação:** assinatura humana automática WA-21 já foi decidida, mas payload livre só na janela, e mensagem template só com componentes/slots aprovados; exigir identidade real e snapshot.
8. **Terminologia:** revisar títulos novos e textos de UI para que a plataforma não seja chamada “LiberaCred”; não renomear GitHub/tabelas/ZIP por impulso.
9. **Outras frentes em Draft:** S0 PR #1, OpenAI #3, S1 #5, CF-OP #7, coordenação F03 #8/#12 e interface visual independentemente ainda não equivalem a uma integração homologada. Não atualizar PRs alheias automaticamente.

## 5. Critério editorial de precedência

- **Esta WA-22 é um MAPA DE DEPENDÊNCIAS**, não tentativa de reescrever a decisão técnica dos donos S0/S1/OpenAI/frontend.
- Nas decisões aqui atribuídas a AL-IA-01/02/03 de 22/10, registrar que são **posteriores** à fonte WA-19 de 21/10 e exigem harmonização entre contratos sem inferir consentimento de todos os donos.
- Para regras técnicas S0/Meta, preferir a decisão de produto com fonte + versão e bloqueio conservador até testes/ratificação, nunca aprovar novo evento SQL ou tipo Meta inventado.
- Onde uma fonte diz [DN] sobre produto, isso NÃO comprova que S0 tenha já incorporado a regra; onde há provas PG17 de laboratório, elas não validam Meta real ou OpenAI paga.

**Consulta:** [LEIA PRIMEIRO](./README.md) → [01 funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) → [00 WDC de decisões](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md) → [02 conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). A harmonização documental global está na [issue #13](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/13). **Nenhum merge, SQL de produção, Meta/Graph, OpenAI paga, MCP ou deploy neste registro.**
