# AL-IA-00 — Índice mestre do alinhamento funcional de IA e conhecimento

**Projeto:** LiberaCred / Prumo Growth  
**Data:** 22/10/2026  
**Local no GitHub:** branch `feat/s2-openai-adapter-sintetico`, **PR #3 Draft, frente OpenAI**.  
**Estado:** **registro documental da manifestação do responsável**, **NÃO** implementação, merge, aceite de outra frente ou autorização externa.

## Propósito

Preservar integralmente em nossa **frente OpenAI** o alinhamento recente da LiberaCred sobre **atendimento F01/F02/F03, jornada humana, histórico, status comerciais, ficha, bases de conhecimento, contextos, instruções, comportamento, cache, habilidades e MCP de Diretores**, junto com a distinção de decisões históricas e pendências.

O registro é **aditivo**: não apaga arquivos antigos da frente OpenAI nem os 55 documentos da cópia de Drive 17/10; não altera S0/S1/Meta, não muda código nem testa integrações. O problema de possível documentação divergente no Google Drive/projeto/GitHub pertence a **frente documental distinta**. A presença deste pacote no PR #3 não confirma que todo o conteúdo dos 55 originais esteja aqui.

## Navegação recomendada

| Arquivo | Conteúdo |
|---|---|
| [AL-IA-01 — Jornada F01/F02/F03](./ALINHAMENTO_2026_10_22_01_JORNADA_F01_F02_F03_v0_1.md) | Atendimento comercial, handoff, conclusão humana, cutoff, F03 multimodal, ficha contínua, status, retorno pós-venda, F02, Banco |
| [AL-IA-02 — Conhecimento/cache/habilidades](./ALINHAMENTO_2026_10_22_02_CONHECIMENTO_CACHE_HABILIDADES_v0_1.md) | Gatilho semântico, fato canônico, metadados, bases por concessionária, pausa/contexto/vigência, quatro campos globais, caching opcional, catálogo de habilidades |
| [AL-IA-03 — MCP de Diretores](./ALINHAMENTO_2026_10_22_03_MCP_DIRETOR_GUIAS_AUDITORIA_v0_1.md) | Ações administrativas, dupla confirmação, proibição de alterar software, base de auditoria do MCP imutável pelo próprio MCP, guias semânticos tipo skills |
| [AL-IA-04 — Rastreabilidade](./ALINHAMENTO_2026_10_22_04_RASTREABILIDADE_DELTAS_PENDENCIAS_v0_1.md) | Deltas entre documentação antiga/novo alinhamento, conflitos, responsáveis, pendências técnicas, validações externas e propostas de testes |
[TRECHO COMERCIAL INTERNO EXCLUÍDO DA VERSÃO PÚBLICA]
| [AL-IA-06 — Auditoria de fidelidade e completude](./ALINHAMENTO_2026_10_22_06_AUDITORIA_FIDELIDADE_E_COMPLETUDE_v0_1.md) | Checklist de decisões, achados, reparos já publicados e divergências ainda não conciliadas |

**Ordem de leitura:** 00 → 01 → 02 → 03 → 04 → 05 → **06 (auditoria)**. Para esclarecer precedência, usar primeiro as etiquetas de status abaixo e conferir documento-fonte.

## Regras de interpretação e precedência

- **[DN] — Diretriz nova expressa (21–22/10/2026):** posição de produto declarada nesta conversa; pode **conflitar** com contrato normativo anterior e **exige conciliação**, não altera automaticamente direitos da S0.
- **[DA] — Decisão anterior compatível:** existente no acervo 17/10 ou contratos posteriores e não contradita pelo responsável.
- **[HS] — Histórico / superado:** ideia anterior que deixou de ser direção atual por decisão posterior, ou possibilidade nunca aprovada. Ex.: **IA Analista autônoma do consolidado 10/10**, excluída pelo doc 06 v4.6.
- **[P] — Proposta:** desenho físico, algoritmo, tabela, API, guia operacional ou teste sugerido, ainda sem aceite específico.
- **[R] — Refinamento interno pendente:** catalogação, versionamento, permissão, contrato interfrentes, organização de UI, mecanismos de segurança.
- **[V] — Validação externa pendente:** instituição financeira, Meta/WhatsApp, proteção de dados, fornecimento/transferência a IA e evidências oficiais.

**Precedência de conteúdo:** manifestação recente **expressa** sobre a função pretendida > descrições anteriores conflitantes como indicação de produto; **mas** decisões normativas aprovadas anteriores, contratos S0 e regras jurídicas **não são silenciosamente revogados ou implementados** pela frente OpenAI. Documentar choque e pedir emenda à frente titular. Ideias hipotéticas do assistente não viram regra sem anuência do responsável.

## Quadro sintético do que foi efetivamente alinhado

**F01:** única interlocutora IA com o cliente; tem instruções globais próprias **e comportamento global próprio**. Não existem instruções/comportamento por concessionária. Usa base institucional e conteúdo isolado da loja; oferece somente condições válidas. Handoff para humano cessa F01 naquele caso; retorno de cliente já `vendido` na própria loja é humano. Remessa direta futura somente se Banco autorizar/homologar.

**F02:** planejadora, **só instruções globais próprias**, sem campo “comportamento”. Usa templates preexistentes, calendário e contexto sob validação S0. Pendência pós-humana F03 vai prioritariamente ao Consultor/Gestor, não automaticamente à F02.

**F03:** extratora/classificadora silenciosa, **só instruções globais próprias**, sem campo “comportamento”. Executa exclusivamente após botão expresso do Consultor; cada evento imutável tem cutoff incluindo última mensagem naquele instante, sem futuras mensagens. Lê todo histórico **lógico** autorizado da mesma loja inclusive mídias e agentes anteriores; ficha do cliente é evolutiva, sem duplicação por negociação; pode propor mudanças automáticas de status pela S0, inclusive `perdido` com motivo, **nunca `vendido`**. Consultor não edita ficha; falha F03 é crítica. `cadastro enviado ao banco` depende de remessa real comprovada.

**Bases de conhecimento:** dois campos informacionais iniciais (gatilho semântico e fato canônico) + metadados aceitos; Prumo faz **todo** cadastro, inclusive de lojas. Bases adicionais exclusivamente vinculadas a uma loja, pausáveis/reativáveis; campo de contexto criado possivelmente na origem permanece visível na pausa sem forçar redação retroativa. Vigência de ofertas exige avaliação mesmo com base ativa. Pausa **automática opcional por data e hora**.

**Habilidades:** conhecimento associado, diretoria administra capacidades configuráveis pelo MCP; IA operacional não cria; integração executável nova requer desenvolvimento fora do MCP. Guias operacionais semânticos do **MCP** orientam o ChatGPT usado pelo Diretor e **não** são os quatro campos de instrução/comportamento das IAs internas.

**MCP Diretor:** operações amplas em **dados operacionais**, com confirmação expressa antes da mutação; **não** altera software/regras, nem pode escrever/editar/excluir a **base de auditoria protegida do próprio MCP** mesmo após confirmação; consulta autorizada a registros é possível. Exceções de retenção e mecanismos físicos dependem de especificação.

**instituição financeira:** integração/remessa direta é preferência **condicionada**, alternativa humana se não viável; responsável **não quer investigar/decidir Banco neste estágio**.

## Anteriores mais relevantes para conciliação

- Consolidado auditado de ideias de **10/10/2026** (cópia no projeto e Drive) — leitura **histórica**, não implementação nem autoridade mais recente universal.
- Pacote **55 arquivos de 17/10** (Drive/projeto): docs **06, 08B/08C, 09, 10, 13A, 21, 22, 23, 24, 25, 26, 40, 41** especialmente relevantes.
- GitHub frente OpenAI PR #3: `OAI_05_CONTRATO_EXTRAÇÃO_PÓS_ATENDIMENTO_HUMANO_v0_1.md`, `OAI_07_DESFECHO_ENCAMINHAMENTO_PREFERENCIA_CANAL_v0_1.md`, `OAI_08_CONTRATO_PLANEJADORA_POS_HUMANA_CF_OP_02_v0_1.md`, `E01_CONTRATO_FUNCIONAL_MULTI_CAPACIDADE_v0_2.md`.
- GitHub S0 PRs **#1, #8, #12** (em draft/concepção/testes locais) e Meta PR #2, cada um com sua titularidade. **Nenhum foi modificado nesta ação**.

## Fora do escopo deste registro

Não editar produção, Supabase, Meta, Banco, n8n, GitHub Secrets, OpenAI API real, configuração de memória de usuário, código ou branches alheias. Não instituir novos status, conceder permissões físicas ou declarar teste técnico/homologação concluída. Nenhuma mudança aqui converte hipótese comercial em regra contratual.

**Responsável pela conciliação física futura:** proprietários S0/S1/frontend/Meta/MCP/Banco, quando explicitamente acionados. A frente OpenAI conserva o registro de decisões [DN], propõe interfaces [P] e sinaliza incompatibilidades [R/V].
