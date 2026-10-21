# WA-18C — Falhas consecutivas e categorias internas de templates

**Data:** 20/10/2026. **Natureza:** decisão expressa do responsável + proposta conceitual. **Precedência:** complementa WA-18B e encerra a dúvida sobre o evento que zera o contador. Somente documentação, PR #2 Draft; não há código ou alteração de banco nesta rodada.

## 1. Decisão expressa: duas falhas consecutivas na mesma cadência

- A contagem é **por cadência/fluxo do lead**, não por intervalo de tempo entre as tentativas.
- **Falha definitiva tecnicamente comprovada** de um template → contador 1; a Planejadora não é acionada por esse erro comum. A cadência prossegue para a próxima tentativa planejada.
- **O template seguinte foi efetivamente enviado** → contador volta para **0**, mesmo que o cliente não responda. Uma falha subsequente volta a ser primeira falha. A falta de resposta segue a política distinta de silêncio/finalização.
- **Duas falhas definitivas comprovadas em tentativas consecutivas** → cancelar todos os envios futuros do plano e marcar o ciclo/lead como **perdido**, com motivo técnico de falha sistêmica de envio; preservar evidências e histórico.
- Os resultados devem ser apurados pela plataforma/S0 **sem envolver a IA Planejadora** na falha cotidiana.

| Sequência técnica confirmada | Contador | Ação |
|---|---|---|
| Falha, enviado | 1 → 0 | Continua; resposta do cliente não é requisito |
| Falha, enviado, falha | 1 → 0 → 1 | Continua; último erro é a primeira falha da nova série |
| Falha, falha | 1 → 2 | Cancela restantes e registra perdido técnico |
| Enviado, falha, falha | 0 → 1 → 2 | Cancela após a segunda falha seguida |
| Falha, incerto | 1 → pendente de conciliação | Não inventar sucesso nem falha |

**Distinção técnica para implementação:** “foi enviado” precisa de **evidência confiável e correlacionada de sent**. Apenas HTTP 2xx ou API_ACCEPTED não provam envio. Timeout/falta de callback/COMMIT incerto não somam falha nem zeram como sucesso sem conciliação; não permitem replay cego. Webhook duplicado ou fora de ordem não altera duas vezes contador. A implementação atual S0 C07 ainda é SOMENTE_DIAGNOSTICO e NAO_AVALIADAS_DEC_15; **não há contador final homologado**.

## 2. Decisão expressa: categorias e permissões internas de templates

O responsável quer que o catálogo da **concessionária/WABA específica** permita **criar e administrar categorias próprias**, de modo a determinar quais templates estarão disponíveis a qual sistema, IA, operador, campanha ou situação. Isso evita que a IA Planejadora escolha um template de promoção específica para um lead não elegível, criando promessa comercial falsa.

**Categoria oficial Meta é diferente de categoria de negócio da Liberacred.** MARKETING e UTILITY descrevem a classificação Meta (e regras/preços correspondentes); categorias internas definem contexto de uso/visibilidade/eligibilidade e NÃO substituem a aprovação Meta.

### Proposta de modelo multidimensional (ainda não homologada)

| Dimensão | Exemplos ilustrativos | Quem controla |
|---|---|---|
| Meta category | MARKETING, UTILITY, eventualmente AUTHENTICATION conforme API | Meta e gerenciamento aprovado |
| Categorias internas da concessionária | abertura, recontato, informativo, uso de operador, campanha | Responsáveis administrativos autorizados |
| Consumidor/escopo de uso | Planejadora, IA de atendimento, operador, campanha autorizada | Matriz de permissões contextual da plataforma |
| Elegibilidade comercial | campanha ativa, público elegível, oferta verdadeira/vigente, modelo de interesse, finalidade permitida | Fonte comercial autorizada, nunca alegação inventada pela IA |

**Exemplos de situações**, não enum fechado nem escolha final da cardinalidade:
- Um template de ABERTURA aprovado pode ficar disponível ao motor de contato inicial, mas não automaticamente à cadência de recontato.
- Um template de RECONTATO pode ser usado pela Planejadora quando a plataforma o disponibilizar naquele contexto.
- Um template de OPERADOR pode ser apresentado apenas a operador autorizado com caso elegível, sem liberar uso pela Planejadora.
- Um template de CAMPANHA X requer campanha vigente e vínculo comprovado do lead às condições anunciadas. Aprovação Meta **não comprova** direito à promoção.
- Mesmo em mesma categoria interna, templates de concessionárias diferentes não são compartilhados.

### Regra de acesso/seleção proposta (segura por padrão)

1. O backend seleciona, antes de chamar a IA Planejadora ou apresentar ao operador, um **conjunto filtrado** por concessionária, WABA, estado oficial da Meta, versão, idioma, status do catálogo, contexto de fluxo, permissões do consumidor, campanha e validade/eligibilidade.
2. A IA **não recebe acesso irrestrito ao catálogo**. Ela escolhe, substitui, remove, reordena ou varia a quantidade apenas dentro do conjunto autorizado; não cria ofertas e não contorna bloqueios por prompt.
3. O backend **revalida na reserva e no envio**, pois categoria, campanha, política, template e opt-out podem mudar após o planejamento. Não basta esconder templates no prompt.
4. Se nenhum template atender aos filtros, não improvisar mensagem promocional nem escolher categoria não autorizada; registrar falta de candidato permitido.
5. Responsáveis via futura IA administrativa/MCP poderão criar categorias e solicitar mudança de políticas com identidade individual, segunda confirmação e auditoria. **Esta frente não implementará o servidor MCP.**

**Recomendação de estrutura para auditoria (não é migration aprovada):** separar categoria interna da classificação Meta; prever categoria interna por concessionária, vínculos entre categoria e template/versão, regra de uso por consumidor e finalidade, vínculo opcional de campanha e snapshot de motivo/versão/permissão no planejamento e envio. Reutilizar entidades de campanha já existentes, se houver, evitando tabelas duplicadas. Políticas devem ficar versionadas/auditáveis, sem alterar retrospectivamente histórico de envios.

## 3. Questões pendentes (não transformá-las em decisão)

- Um template poderá pertencer a **mais de uma categoria interna**, ou uma categoria principal? Proposta: múltiplas etiquetas, **sem** combinar permissões para ampliar acesso acidentalmente.
- Uma mesma versão poderá ser permitida tanto em ABERTURA quanto em RECONTATO mediante concessões separadas, ou exigirá categoria única por contexto?
- Qual fonte do domínio comercial comprova que campanha/oferta é aplicável ao lead e ainda está vigente? Não usar decisão da IA como prova.
- A política para visibilidade de operadores deve respeitar escopo de loja e caso atribuído já previsto no S0, sem criar atalho alternativo.

Essas são questões de refinamento para a auditoria e não impedem registrar a decisão central.

## 4. Divergências e status a acompanhar

- WA-17A/B hoje modela apenas campo category=MARKETING/UTILITY da Meta; **a taxonomia interna contextual ainda NÃO foi implementada**.
- WA-18B deixava aberta a dúvida sobre qual evidência zerava falhas; WA-18C esclarece **enviado tecnicamente confirmado, sem necessidade de resposta**.
- O diagnóstico de falhas no S0 C07 ainda retorna ação SOMENTE_DIAGNOSTICO; nenhuma implementação real é presumida.
- WA-18B mantém decisões sobre edição Meta conforme permitido, congelamento do mapeamento de variáveis de versão aprovada e responsabilidade da plataforma por preenchimento no envio.
- Sem execução de Graph, PostgreSQL hospedado, nova migration, MCP ou deploy. PRs mantidos Draft.
