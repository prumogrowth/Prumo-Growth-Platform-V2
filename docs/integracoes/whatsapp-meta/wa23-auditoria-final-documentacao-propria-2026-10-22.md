# WA-23 — Auditoria editorial final da documentação PRÓPRIA da frente WhatsApp/Meta

**Corte:** 22/10/2026. **Branch:** `docs/whatsapp-meta-concessionária de demonstração-poc-20261017`, **PR #2 Draft**. **Escopo autorizado:** atualizar, organizar e auditar **somente arquivos da frente WhatsApp/Meta**, sem revisão executável de código, alteração em SQL, testes, webhook real, OpenAI, Meta Graph, MCP ou documentação/branches de terceiros. **Não é auditoria técnica nem declaração de homologação.**

## 1. Resultado e alcance real

**Parecer:** **APTA COMO REFERÊNCIA DOCUMENTAL DA PRÓPRIA FRENTE, com pendências técnicas e externas expressamente registradas**. Após esta auditoria, os documentos de consulta da nossa frente permitem identificar:

- **o que o responsável decidiu** (com data/fonte),
- **o que era uma decisão antiga substituída somente no tema correspondente**,
- **o que é proposta técnica ou contrato interfrentes a conciliar**,
- **o que depende de Meta/LGPD/Banco/contas/terceiros**,
- **o que tem apenas simulação/testes escritos e o que realmente foi validado**.

**Inventário conferido:** foram listados e percorridos os **62 documentos Markdown que existiam antes da criação deste relatório** em `docs/integracoes/whatsapp-meta/` no PR #2. Depois da inclusão desta WA-23, o diretório passa a **63 documentos Markdown** nesta versão. Também inspecionado `integrations/whatsapp-meta/README.md`, que pertence ao nosso módulo de integração e aponta para o índice de documentação.

**Verificação automatizada de referências:** em cinco lotes, os links Markdown locais dos 62 arquivos anteriores foram resolvidos em relação às pastas correspondentes e comparados aos caminhos versionados no PR #2. **Nenhum destino local ausente foi identificado pelo método de verificação aplicado.** Isto **não** verifica URLs externas, âncoras Markdown de seções, qualidade da fonte de cada afirmação nem o conteúdo linha a linha de todas as mensagens históricas. Os links dos documentos centrais foram também examinados na auditoria anterior.

**Organização:** 5 referências centrais anteriores (`README`, `00`, `01`, `02`, `WA-19`); 48 registros históricos de engenharia com banner de leitura controlada no início; 6 históricos de decisão/contrato com erratas de precedência próprias (`WA-07`, `WA-17A/B`, `WA-18/A/B/C`); 3 documentos recentes temáticos (`WA-20/21/22`). O total verificado **após adicionar este relatório é 63 arquivos Markdown** no diretório (62 anteriores + este). O índice técnico do código é um arquivo Markdown **fora desse diretório**.

## 2. Hierarquia de consulta para qualquer desenvolvimento futuro

| Tipo de consulta | Documento vigente da nossa frente | Função e limite |
|---|---|---|
| Onde começar | [README — LEIA PRIMEIRO](./README.md) | Mapa da biblioteca, precedência e navegação |
| O que é regra de produto | [01 — especificação funcional consolidada](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) | Regras comportamentais, papéis, fluxos, evidências e exceções; atualização **em 22/10**, nome físico do arquivo histórico mantido para estabilidade dos links |
| Quais decisões têm origem | [00 — matriz WDC-01..22](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md) | **22 decisões**, fontes e semântica [D/E/S/P/V/T]; atualização **em 22/10** sem renomear path histórico |
| Qual trecho de qual documento foi revisto | [02 — mapa de conflitos e superações](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md) | Não revoga documentos inteiros; separa mudança de negócio de migração física |
| Como ocorreu a auditoria original | [WA-19 — auditoria e 13 achados documentais](./wa19-auditoria-documental-reconciliacao-2026-10-21.md) | Evidência do corte de 21/10, preservada como histórico e não falsamente reescrita |
| Pesquisa sobre assinatura | [WA-20 — nome visível](./wa20-identificacao-visivel-atendente-assinatura-mensagem-2026-10-21.md) | Pesquisa técnica e exemplo preliminar; **formato anterior SUPERADO por WA-21** |
| Nome/cargo e assinatura APROVADOS | [WA-21 — Diretor/Gestor/Consultor](./wa21-papeis-diretor-gestor-consultor-assinatura-2026-10-21.md) | `Consultor Nome:\nMensagem`, `Gestor Nome:\nMensagem`, `Diretor Nome:\nMensagem` nos textos humanos livres |
| O que outras frentes têm que repercute no canal | [WA-22 — revisão S0/S1/OpenAI/Frontend/CF-OP/CFI-01](./wa22-revisao-cruzada-outras-frentes-contratos-2026-10-22.md) | **12 achados XWA-01..12**, origem em branches Draft, limites e dependências; não transplanta implementação |
| O que realmente foi validado no fim WA-16/17 | [WA-16/17 — evidências e pausa](./wa16-wa17-fechamento-validacao-e-pausa-2026-10-20.md) | 42 checks V8 independentes versus 44 testes Node escritos/nativos não comprovados e 11 verificações PG17 não executadas no ciclo reportado |
| Contrato/código candidato Meta | [README técnico](../../../integrations/whatsapp-meta/README.md) | Status offline/candidato; não substituir decisões vigentes por exemplos antigos de módulo |

**Regra de precedência:** decisão expressa posterior prevalece **somente** no ponto que modificou. Um contrato externo posterior é dependência rastreada, mas não significa que a nossa frente possa implementar regras fora de sua alçada ou afirmar que o outro PR já entregou API homologada.

## 3. Matriz de cobertura dos assuntos essenciais

| Domínio / obrigação | Referência vigente, decisão | Resultado documental | Implementação / ressalva |
|---|---|---|---|
| **Identidade do sistema** | WDC-01, doc 17 original, WA-22 XWA-01 | **CLARO:** a **plataforma de atendimento ainda não tem nome comercial**, Prumo é gestora, **LiberaCred é produto da instituição financeira** | Dois documentos de engenharia de 17/10 com “plataforma Liberacred” receberam errata explícita SEM apagar o trecho original; não renomear IDs |
| **Propriedade WhatsApp/Meta** | DEC-WA-05, WDC-02/03 | **CLARO:** uma conta empresarial/App/WABA/número e catálogo por concessionária; Prumo acesso delegado | [V] prova de configuração/permissão efetiva na Meta antes de produção |
| **Separação de dados e canais** | WDC-04, WDC-14/15, WA-22 | **CLARO:** por loja e sem vazamento entre concessionárias; supressão A não se propaga a B | S0 somente sintético; escopo operacional/finalidade/consentimento [P/V] |
| **Registros de mensagens e transportes** | WDC-04/19/20, contrato WA-05/06/07 | **CLARO:** `mensagens`, `envios_template`, `catalogo_templates` separados, IDs/versões e provas; `HTTP 2xx ≠ sent` | CI atual de WA-16/17 não comprovada; callbacks reais não homologados |
| **Funções de IA** | Seção 4 de 01, WDC-05/11/12, WA-22 XWA-04/05/07 | **CLARO:** F01 conversa, F02 planeja aprovados, F03 analisa após **conclusão humana explícita**, IA administrativa Diretor/MCP e IA separada de melhoria têm fronteiras distintas | PR OpenAI e ponte F03 continuam contratos independentes; não reproduzir autorização via prompt |
| **Templates, finalidades e campanha** | WDC-07..12, WA-17B/18B/18C, WA-22 XWA-10 | **CLARO:** Meta category ≠ finalidades internas (múltiplas e com grants); F02 só catálogo filtrado; mídia/edição conforme Meta; campanha precisa oferta verdadeira vigente | Fonte física de ofertas/campanhas [R/P]; não construir banco de marketing unilateralmente |
| **Slots e variáveis** | WDC-09, seção 8 de 01 | **CLARO:** fonte posicional congelada por versão aprovada; somente plataforma preenche com campos elegíveis | WA-17A inicial permite remapeamento: **divergência T de código/documentação legada identificada**, para auditoria técnica |
| **Cadências e falhas** | WDC-11..13, WA-18C | **CLARO:** F02 ajusta modelos aprovados ao invalidar Meta; erro comum não chama F02; duas falhas definitivas consecutivas → `perdido` técnico; `sent` intermediário zera | Ordenação, evento incerto, repetição e concorrência ainda [P/T] |
| **Os três marcos/relógios** | WDC-20, WA-22 XWA-04/08, CF-OP | **CLARO:** janela livre último inbound +24h; fechamento humano explícito; C09 último template efetivamente enviado +24h e elegibilidade | Matriz C09 pós-humana [R]; `accepted` não inicia prazo |
| **Atendimento e equipe humana** | WA-21, WA-22 XWA-02/03/09 | **CLARO:** Diretor, Gestor, Consultor, assinatura `Cargo Nome:\nMensagem` automática e autenticada, sem ser campo nativo Meta; pausa intake não perde casos; leitura UI ≠ `read` Meta | Prova de mensagem humana real e atribuição [R/T]; prefixo visível não é recibo |
| **Histórico e mídias F03** | WA-22 XWA-05/12, AL-IA-01 e CFI-01 fonte | **CLARO COMO REQUISITO:** mesmo cliente+concessionária através de conversas, eventos/autores/mídias disponíveis até `cutoff` imutável | Retenção/LGPD, referência, fonte de transcrição, schema físico e autorização de F03 [R/V/T] |
| **Dados bancários e status** | WDC-18/20, WA-22 XWA-06/07 | **CLARO:** Meta não decide venda, negativa nem remessa; F03 pode propor desistência com gate S0; `vendido` só humano autorizado com prova | Conflito D41-04 x AL-IA-01 sobre edição humana da ficha pertence a coordenação S0/S1/OpenAI/UX [R] |
| **Diretor / MCP / auditoria** | WDC-05/06/22, WA-21/22 XWA-11 | **CLARO:** identidade individual, prévia e segunda confirmação de mutação, nenhuma alteração de software; auditoria própria protegida do MCP não editável por tools | Servidor MCP pertence à outra frente, ACL granular e logs físicos [R/T] |
| **Custos, eficácia e aprovação Meta** | WDC-08/17/18 | **CLARO:** painel de saúde/eficácia desejado; nenhum teto monetário de disparo automático; marketing/utility Meta tratados distintamente | Política Meta, tarifação, LGPD e uso financeiro [V] |

## 4. Reparos aplicados especificamente NESTA rodada editorial

1. **Matriz `00`:** data de atualização corrigida para 22/10; `WDC-01` deixa inequívoco que a plataforma ainda não tem nome próprio; `WDC-05/06/10` e pendências adotam **Diretor/Consultor** no lugar de rótulos antigos para o cargo; referência explícita à WA-22.
2. **Especificação `01`:** data de corte 22/10; antiga seção intitulada “três papéis de IA” corrigida para cobrir também F03 pós-humana; assinatura `Consultor/Gestor/Diretor Nome:` e papel de Diretor na gestão Meta/MCP; finalidade “atendimento por Consultor”; regra de envio individual humano; orientação de histórico/cutoff, C09, indicadores de leitura, campanhas, riscos de cadastro e auditoria MCP.
3. **Índice `README`:** atualização em 22/10; referência direta à WA-22 na ordem de leitura, cargos atuais, plataforma ≠ LiberaCred, catálogo de arquivos navegável. **63 documentos após a inclusão desta WA-23**.
4. **README técnico `integrations/whatsapp-meta/`:** corrigida menção ultrapassada a **20 decisões** para **22 WDC**, link para WA-22 e distinção de identidade do produto.
5. **Textos históricos `conciliacao-pr1-pr2-s0-whatsapp-v0_1.md` e `poc-meta-sandbox-documentacao-publica-2026-10-17.md`:** errata de leitura antes de “plataforma Liberacred”, com preservação do texto da época; não contamina a terminologia da especificação atual.
6. **WA-23:** este fechamento, com matriz de cobertura, status [D/R/P/V/T], trilha de verificação e fronteira de propriedade documental.

**Preservados sem alteração:** fonte do ZIP 17/10, documentação do Google Drive, outras branches e seus documentos, PRs #1/#3/#5/#7/#8/#12, migrations, testes, workflows, produção e contas externas. **Não** abrir automaticamente alteração em outra frente.

## 5. Pendências que não podem ser declaradas resolvidas por documentação

- **[R/T]** S0/S1: qual evidência técnica e transição constitui primeiro contato humano válido, especialmente com pausa/reatribuição, prova `sent` e assinatura visual separada.
- **[R/V/T]** F03: histórico lógico completo autorizado, mídia referenciável, retenção, cutoff e recheck; recibo CFI-01 de PR #12 ainda não é processamento multimodal.
- **[R]** D41-04 e AL-IA-01: conflito sobre correções humanas da ficha; frente Meta apenas fornece fonte original da mensagem, não interpreta ACL cadastral.
- **[R/P]** origem oficial de campanhas/ofertas e elegibilidade verificada antes da seleção de template promocional sem impor subsistema de UTM ao núcleo.
- **[R/T]** matriz C09 pós-atendimento humano, concorrência entre template individual e cadeia F02, ordenação definitiva de status `sent/failed/uncertain`.
- **[R/T]** persistência de finalidades N:N, grants, versões/snapshots Meta, bindings de variáveis e classificação de campos do lead.
- **[V]** Meta real, direitos de WABA/números/contas, políticas de template financeiro, instituição financeira, mídia, LGPD/consentimento e eventual precificação.
- **[T]** execução nativa WA-16/17 Node/PG17 no ciclo atual, integrações e segurança operacionais; **não** afirmar CI ou produção prontos.
- **[R/T]** MCP futuro: ACLs concretas por ferramenta/Concessionária/Diretor, auditoria protegida, identidade e confirmação; **não** implementar servidor nesta frente.

**Essas pendências são explícitas e localizáveis — não são informações omitidas nem autorizações por silêncio.** Fechar uma delas exigirá nova decisão/contrato e, quando aplicável, validação de Meta/Banco/LGPD, sem edição unilateral de outra branch.

## 6. Checklists de auditoria editorial e encerramento

- [x] Escopo estritamente da documentação **WhatsApp/Meta**, com efeitos para outras frentes registrados somente COMO dependências.
- [x] Inventário completo dos **62 Markdown anteriores** com navegação de todos no índice (exceto autolink do próprio README).
- [x] Links Markdown locais inspecionados por resolução de caminhos, nenhum quebrado pelo método aplicado nos 62 anteriores.
- [x] Precedência explícita entre documento de 17/10, WA-17/18, WA-20, WA-21 e WA-22, sem apagar histórico.
- [x] Marca indefinida da plataforma, Prumo gestora e LiberaCred produta instituição financeira inequívocos; duas erratas de terminologia histórica.
- [x] Cargos Diretor, Gestor, Consultor e assinatura visível por texto com fontes de autoridade, preservando IDs físicos legados.
- [x] Três funções F01/F02/F03 + administrativa/MCP + melhoria de atendimento diferenciadas.
- [x] 12 interfaces interfrentes WA-22 recuperáveis da especificação e índice, não confundidas com código implementado.
- [x] Estado de WABA/Meta, duas falhas, opt-out, finalidades, variables, templates, C09, mídia e autoria separado de prova operacional.
- [x] Evidências de laboratório/teste anteriores preservadas sem reclassificá-las como certificação de produção.
- [ ] Auditoria técnica/implementação SQL/TS/CI/Graph/OpenAI/Banco (OUTRA FASE).
- [ ] Conciliar decisões/contratos de outras frentes com seus próprios responsáveis (FORA DO ESCOPO DE EDIÇÃO DESTA FRENTE).

**Parecer final:** **documentação sob propriedade da frente WhatsApp/Meta organizada, rastreável e suficientemente inequívoca para orientar uma auditoria técnica ou implementação posterior**, com pendências e limites identificados. Uma auditoria documental não garante inexistência absoluta de todo conflito oculto ou atualização automática de futuras branches; exigir nova reconciliação se novas decisões surgirem. Manter PR #2 Draft até autorização específica, sem merge nem deploy.
