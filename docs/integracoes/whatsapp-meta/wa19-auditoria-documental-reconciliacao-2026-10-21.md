# WA-19 — Auditoria documental de decisões e contratos WhatsApp/Meta

**Data de referência:** 21/10/2026. **Responsabilidade:** frente WhatsApp/Meta; interface com S0 e outra frente MCP. **Escopo AUTORIZADO:** documentação, não auditoria funcional/estática de código, não execução de tests/CI/SQL e não integração real. **PR #2:** Draft, sem merge/deploy.

## 1. Metodologia e alcance real

1. Material entregue: consolidação de ideias auditada v0.2, datada 10/10, mais ZIP contendo **55 documentos de 17/10**. Validação de integridade de TODOS os 55 documentos: bytes e SHA-256 coincidiram com as 55 linhas do manifesto do pacote (55/55). O manifesto e os documentos preservam um snapshot histórico, não o estado de produto 21/10.
2. Foi efetuada **varredura temática de todos os 55 documentos** por arquitetura, WhatsApp, Meta/WABA, templates, IA Planejadora, MCP, opt-out, cadência/falhas e permissões; leitura contextual aprofundada dos itens de maior relevância: 00A, 04, 05, 06, 09, 10, 11, 13, 13A, 25, 26, 30, 31, 33, 34, 35, 41 e índice de progresso, dentre outros trechos relacionados. Não afirmar revisão editorial integral de cada parágrafo de todos os 55.
3. Inspecionados documentos atuais de referência do GitHub: WA-07, WA-16/17 status, WA-17A/B, WA-18, WA-18B, WA-18C e README Meta; comparadas as respostas expressas do responsável de 20–21/10.
4. Classificação: **D** decisão expressa do responsável; **E** norma histórica preservada; **S** parte superada; **P** proposta/implementação a decidir; **V** dependência externa; **T** status técnico, que exige prova. Separar lacuna documental de defeito de código e de risco jurídico.

**Artefato central resultante:** [00 — decisões vigentes e precedência](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md), com IDs WDC-01..WDC-20, fontes, glossário e pendências.

## 2. Resultados por criticidade — achados realmente confirmados

| ID | Gravidade documental | Fontes e conflito evidenciado | Resolução aplicada na documentação | O que NÃO foi resolvido nesta auditoria |
|---|---|---|---|---|
| DOC-01 | ALTA | Documento 41 D41-03 autoriza somente importação de lote e remanejamento via MCP; decisões WA-17B/WA-18 passam a desejar gestão de templates, mídia, finalidades e outras escritas pelo responsável. | WDC-05/06 dão precedência **somente às novas intenções autorizadas pelo responsável**, preservando mesma identidade, prévia, segunda confirmação do MESMO ator, auditoria e proibição de DDL/elevação de privilégios. | Matriz física/individual por ferramenta e operação, a ser emendada pela frente MCP/global; NÃO declarar todo CRUD tecnicamente liberado |
| DOC-02 | ALTA | Pacote 04/09/25/30/33/34 cita número de titularidade/controle da gestora, e no 30 o escopo de template da loja é opcional; WA-18 decide WABA, número e catálogo de templates **separados por loja**. WA-07 ainda dizia que cada loja seria titular de App/WABA/número. | WDC-02/03 e nota em WA-07 reconhecem **isolamento obrigatório da WABA+telefone+catálogo por concessionária** e deixam **titularidade jurídica/Meta App** para formalização externa. | Emendar 04/09/25/30/34 na consolidação documental global; auditar adequação do schema S0/Meta sem editar migrations aqui |
| DOC-03 | ALTA | WA-18 D-WA18-01 inicialmente negava qualquer edição depois de APPROVED; responsável depois admitiu edição **quando Meta/API permitir**, mas congelou vínculo de fonte de variáveis em versão aprovada. WA-17A/B ainda possuem descrições de mapeamento editável posterior. | Marcação local da parte **SUPERADA** em WA-18, errata contextual WA-17A/B, WDC-08/09. Conteúdo editável segundo status/regras Meta com versionamento/snapshot; mapeamento da versão aprovada congelado. | Contratos/código WA-17A/B e validação exata por versão/status Meta, reservados à auditoria de implementação |
| DOC-04 | ALTA | Pacote 13 REC-10, 26 e 35 DEC-15 recomendavam cancelar duas falhas sem marcar automaticamente perdido; WA-18B/18C determinam duas FALHAS DEFINITIVAS consecutivas e saída PERDIDO técnica. WA-18B deixava aberto evento reset. | WDC-13 + notas WA-18B/18C: enviado confirmado entre falhas **zera contador mesmo sem resposta**, independentemente do intervalo; duas falhas consecutivas cancelam restantes e geram motivo técnico. | C07/S0 ainda só diagnóstico; nenhum teste de concorrência, callbacks tardios ou falha final foi executado |
| DOC-05 | ALTA | Pacote 33/34/35 DEC-17 mantinha alcance do opt-out entre números/lojas pendente; decisão WA-18 suprime A sem atingir B. Implementação S0-016 é somente sintética por loja+lead+canal+finalidade. | WDC-14/15 esclarecem negócio **loja A apenas** e distinguem supressão operacional da IA; não duplicar tabela já existente. | Alcance por finalidade/canal em troca de número, política Meta/LGPD, interface operacional real e testes |
| DOC-06 | ALTA | WA-17A era manual/BODY-only e dispensava redação por IA; WA-17B e responsável autorizam IA administrativa via MCP para redigir conteúdo e suportar multimídia/botões. | WDC-05/07, errata WA-17A e nota WA-17B. MCP servidor **fora desta frente**; módulos WA-17 legados têm limites documentados. | Servidor/identidade/tooling MCP, mídia verificada, catálogo persistente e Graph real não implementados |
| DOC-07 | ALTA | Classificação oficial MARKETING/UTILITY em WA-17 e 09/25/30, mas necessidade atual de contexto ABERTURA/RECONTATO/OPERADOR/CAMPANHA. Primeiras notas usavam o termo “categorias internas”; em 21/10 responsável escolheu “FINALIDADES”. | WDC-10/11, WA-18C reparada: **múltiplas finalidades por template, cada uma com permissão explícita e independente**; Meta category separada; campanha exige fonte de oferta/eligibilidade confiável. | Modelagem relacional N:N e concessões granulares, filtros efetivos, entidade de campanha/verdade comercial ainda sem implementação |
| DOC-08 | MÉDIA | Atribuição da IA Planejadora pouco diferenciada da IA administrativa no material mais antigo; risco de interpretar que Planner pode criar templates emergenciais. | WDC-11/12 e WA-17B/18B explicitam Planner somente nos templates APROVADOS disponíveis e escopados; erro comum não chama Planner, invalidade Meta chama para replanejar. | Backend efetivo deve filtrar opções e revalidar no envio; sem prova operacional |
| DOC-09 | MÉDIA | “Variável” poderia significar template preenchido por IA, ou coluna sem restrições. Fonte conceitual 09 e código inicial não registram decisão posterior sobre titular do preenchimento. | WDC-09: valor preenchido exclusivamente pela PLATAFORMA ao enviar; fontes derivadas de campos comerciais permitidos da tabela lead, cujo esquema definitivo está pendente. Não expor credenciais/IDs/provas por ser coluna. | Registro dinâmico seguro de fontes e política por campo/uso sem implementação |
| DOC-10 | MÉDIA | Termo “finalidade” já aparece em 33 e S0-016 como finalidade jurídica do contato; reutilizá-lo para categorizar templates sem qualificação cria ambiguidade. | Glossário do índice separa **finalidade de template**, **finalidade de contato/consentimento** e **categoria Meta**. | Nomes físicos e SQL futuros precisam preservar essa distinção |
| DOC-11 | MÉDIA | O documento base 0.2 é datado 10/10, diz nome/plataforma provisório, MVP ainda não implementado e WABA pendente; índice 19F do ZIP marca régua de planejamento em 69% datada 17/10. | Fonte canônica marca ambos como FOTOGRAFIAS históricas, não o estado atual de engenharia ou escolha do nome. | Não recalcular porcentagem de planejamento nem afirmar “69% implementado”; auditoria técnica separada |
| DOC-12 | MÉDIA | Risco de tratar pacote 09 “template aprovado” e callback como garantia de autorização de envio; riscos Meta/LGPD/Banco ainda [V], sobretudo contatos financeiros/documentos. | WDC-18/20 ressalvam gates separadas, confirmação real de envio, status e consentimento; nenhum documento novo é parecer externo. | Homologação Meta/LGPD/Banco, precificação, política de dados cadastrais/fotos, papel contratual continuam pendentes |
| DOC-13 | MÉDIA | WA-16/17 status de teste V8 parcial poderia ser recuperado como “CI 44/44 aprovado” e criar falsa prontidão. | WDC-19 referencia relatório específico: 44 casos nativos escritos, 42 checks V8 separados PASS; Node/PG17 atuais **não comprovados**. | Causa da ausência de workflows, execução nativa atual, 11 provas SQL da WA-16 e revisão de código — FORA DESTA AUDITORIA DOCUMENTAL |

## 3. Reparos efetivamente publicados no PR #2

| Tipo | Arquivo reparado | Conteúdo e fronteira |
|---|---|---|
| Novo índice | 00-decisoes-vigentes-precedencia-documental-2026-10-21.md | Fonte recuperável de 20 decisões WDC com marca de proveniência, precedência, glossário e pendências |
| Errata local | wa17-gestao-manual-templates-variaveis-e-aprovacao-meta-2026-10-20.md | Não aplicar como regra atual as restrições de autoria manual, BODY-only ou remapeamento após aprovação |
| Complemento | wa17b-mcp-templates-multimidia-ia-delegada-2026-10-20.md | Referência a finalidades, WABA por loja, valores preenchidos pelo backend, congelamento por versão e editabilidade conforme Meta |
| Marcação explícita | wa18-alinhamento-decisorio-respostas-responsavel-2026-10-20.md | Etiqueta **SUPERADA** na seção antiga “template imutável”, sem apagar a decisão histórica |
| Fechamento | wa18b-alinhamento-fechamento-optout-variaveis-falhas-cadencia-2026-10-20.md | Duas falhas realmente consecutivas e envio comprovado como reset; “categorias internas” renomeadas para finalidades |
| Correção de termos | wa18c-falhas-consecutivas-taxonomia-interna-templates-2026-10-20.md | Decisão de múltiplas finalidades, autorização independente e separação de finalidades de contato; correção de frase circular “finalidades vs finalidades internas” |
| Entrada de contrato | wa07-contrato-janela-e-templates-cf-op-02-v0_1.md | A afirmação histórica de propriedade App/WABA/número não antecipa conclusão jurídica; escopo operacional WABA por loja |
| Índice técnico | integrations/whatsapp-meta/README.md | Link de precedência para evitar interpretação da fase WA-01 como norma atual |
| Relatório | Este arquivo WA-19 | Auditoria de proveniência, achados e pendências; não equivale a auditoria de código |

**Não modificados deliberadamente:** o ZIP de 55 fontes de 17/10, a consolidação v0.2 de 10/10, PRs #1 e #5, arquivos de código TS/SQL, workflows, Meta Graph ou banco hospedado. As fontes originais ainda poderão ser usadas como histórico, mas NÃO isoladamente para reger partes substituídas.

## 4. Reparo a ser feito na documentação global do projeto (fora da propriedade deste PR)

**Pacote para outras frentes / consolidação global, sem alterar a versão histórica:**

- 41 D41-03 (e 31/36): redigir **emenda normativa granular** cobrindo ferramentas administrativas de templates e finalidades via MCP com segundo aceite do mesmo responsável; conservar proibições de schema, poderes globais e auditoria. Definir matriz executável quando frente MCP trabalhar no serviço; não concluir permissão universal de banco.
- 04, 09, 25, 30 e 34: atualizar titularidade/escopo por concessionária de WABA+telefone+template; revisar especialmente campo escopo_catalogo com concessionaria_id opcional no 30. A real titularidade jurídica é [V], por isso evitar reescrever “pertence legalmente” sem prova.
- 13/26/29/35: substituir explicitamente afirmações de que duas falhas apenas cancelam sem perda por regra nova PERDIDO técnico após duas falhas comprovadas consecutivas; especificar reset após SENT e preservar bloqueio ao resultado INCERTO.
- 33/34/35: marcar DEC-17 como resolvida no **produto** para loja A apenas; condições Meta/LGPD ainda não [V].
- 06/09/25/30: diferenciar IA Planejadora de IA administrativa e categoria Meta de finalidades; catálogo de templates e versões SEM compartilhamento automático interlojas.
- 10/41: preservar identidade individual, auditoria obrigatória e dupla confirmação vinculada à mesma operação; textos anteriores não devem ser usados como autorização para ação MCP em produção sem matriz final.
- 00A/19F e consolidação de ideias 0.2: apor aviso de snapshot histórico ao reexportar; percentuais de planejamento não são porcentagem de desenvolvimento atual. Não alterar arquivos originais sem controle de versões e responsabilidade do projeto.

**Regra de governança:** este PR contém uma **emenda interpretativa da frente**, não substituição silenciosa de todo o corpus. A consolidação global deve incorporar estas mudanças com revisão cruzada, mantendo a origem/data do conteúdo original.

## 5. Critérios de aceitação da AUDITORIA DOCUMENTAL

- [x] Inventário íntegro dos 55 documentos recebidos, sem erros de hash ou tamanho.
- [x] Separação explícita entre decisão expressa, histórico, proposta, implementação e validação externa.
- [x] Documento único de consulta com precedência e rastreabilidade das decisões do responsável.
- [x] Resolução documental do conflito D41-03/MCP sem negar permissões ainda não implementadas.
- [x] Resolução documental de WABA/canal, templates por loja, opt-out A vs B e titularidade legal ainda pendente.
- [x] Resolução documental da regra FAIL/SENT/FAIL e FAIL/FAIL, distinguindo resultado INCERTO.
- [x] Finalidades múltiplas com concessão de uso contextual distintas da categoria Meta.
- [x] Evidência de que não foram alterados código/migrations nem declarada homologação técnica inexistente.
- [ ] Emendas normativas incorporadas em todos os 55 arquivos **originais** (deliberadamente fora do escopo desta intervenção; cabe consolidação global e governança documental).
- [ ] Auditoria técnica de implementação/CI e provas reais de Meta/PostgreSQL (próxima etapa, NÃO incluída).

## 6. Parecer de fechamento desta fase

**APTA PARA PASSAGEM À AUDITORIA TÉCNICA, COM RESSALVAS IDENTIFICADAS.** A documentação contemporânea da frente WhatsApp/Meta agora tem uma ordem clara de interpretação e reparos nos arquivos correntes de maior risco; permanecem documentos históricos intocados e obrigações de emenda global que deverão ser coordenadas com S0/MCP e donos das fontes originais.

O resultado não significa sistema homologado, interface MCP pronta, Meta validada nem PR apto a merge. Manter PRs Draft e nenhuma execução real até autorização e avaliação próprias.
