# AL-IA-05 — Memória de ideias anteriores, hipóteses históricas e limites de ativação

**Data:** 22/10/2026. **Função:** preservar o contexto dos alinhamentos mais antigos sobre IAs, atendimento, negócio e evolução **sem confundir projeto imaginado em 10/10 com decisões normativas posteriores**. Complementa AL-IA-01 a AL-IA-04.

## 1. Origem e direcionamento do projeto (histórico de 10/10)

O consolidado auditado de 10/10/2026 descreve uma **empresa independente de operação comercial para o LiberaCred**, com CNPJ distinto das concessionárias e da agência de marketing, buscando atender leads, conduzir negociações, melhorar conversão e, mediante autorização aplicável, cadastrar/concluir negócios para concessionárias Marca A. A visão não era apenas um chatbot, mas plataforma modular (atendimento, orquestração, dados, gestão de templates, humanos, relatórios e conciliação).

[TRECHO COMERCIAL INTERNO EXCLUÍDO DA VERSÃO PÚBLICA]

[TRECHO COMERCIAL INTERNO EXCLUÍDO DA VERSÃO PÚBLICA]

**Variantes estudadas:** (a) terceirização comercial operada pela Prumo com humanos + IA, preferida conceitualmente; (b) SaaS/white-label com finalização pela loja, alternativa histórica; (c) automação cadastral ampliada, somente se validada externamente. Nenhuma declaração informal substitui conformidade de Banco/Meta/LGPD.

## 2. A antiga proposta de múltiplas IAs

Em 10/10 discutiu-se:
- **IA Vendedora**, comunicando, qualificando, lidando com objeções e usando WhatsApp.
- **IA Analista/Otimizadora**, separada da Vendedora, examinando resultados, hipóteses, padrões e experimentos; teria capacidade de propor/mudar **parâmetros externos autorizados da Vendedora**, nunca os próprios pesos do modelo. Templates Meta seriam sugeridos e geridos por ações/permissão separadas.
- **IA Gestora**, para relatórios e conversação com administradores.
- **Motor determinístico** de tarefas, regras, cancelamento e recontatos, não necessariamente IA.
- Otimização de horários por histórico, preferências expressas e limites, sem IA adicional obrigatória.

**Precedência decisiva [HS]:** o documento **06_IA_Governanca_e_Aprendizado_v4_6.md** posterior **EXCLUIU explicitamente a IA Analista autônoma**. Não reinstalar por inferência ao reler o consolidado histórico. A ideia de análise/otimização permanece como **referência de possível estudo humano futuro**, não produto atualmente autorizado. A “IA Gestora” evoluiu na documentação para experiência **ChatGPT/MCP dos Diretores** administrada sob identidade, confirmação e regras próprias (AL-IA-03). O núcleo determinístico continua indispensável às autorizações.

A terceira capacidade da arquitetura atual é **F03 pós-atendimento humano**, que não é a antiga IA Analista de aperfeiçoamento. Ela extrai histórico/cadastro/desfecho e não reprograma modelos, código nem regras.

## 3. Ideias comerciais de atendimento ainda aproveitáveis

Essas orientações aparecem no consolidado/06/08B e são compatíveis com a direção recente, respeitando políticas e conhecimento aprovados:

- **WhatsApp natural**: mensagens breves, interativas, perguntas graduais, sem blocos excessivos nem promessa de aprovação/valor/taxa não comprovados.
- **Objeções**: se cliente mencionar concorrência, IA não deve necessariamente escalar de pronto; escuta, reconhece argumentos pertinentes, esclarece com dados autorizados e não inventa equiparação/desconto.
- **Histórico conversacional e ficha**: armazenar mensagens individuais com data, papel/autoria, vínculos e referências a templates; respeitar pedido expresso de opt-out ou canal. Histórico próprio de uma loja não vira contexto de outra loja.
- **Prospecção x atendimento receptivo**: origem do lead importa, mas importação não é consentimento Meta nem autorização para disparar mensagem; recontato exige templates elegíveis.
- **F01 silenciada no handoff**: depois que a posse da conversa passou ao humano, F01 não reinicia conversa naquele caso. Uma **nova conclusão humana** ativa F03, não F01.
- **Mensagens multimodais**: preferência texto/áudio não é inferida por um único áudio isolado; interpretação de áudio/imagem/documentos depende de autorização, qualidade e tratamento seguro.
- **Aprendizados comerciais**: métricas de resposta, conversão, primeira/segunda mensalidade, receita, custo, reclamações, opt-out etc. podem informar análises humanas futuras, mas correlações não estabelecem causalidade, e nenhuma IA Analista autônoma encontra-se autorizada hoje.

## 4. Cadência anterior preservada com ressalvas

Conforme doc 08B v4.6, na jornada **F02**:
- Não iniciar por iniciativa própria a campanha de primeiro template; o envio inicial é outro mecanismo.
- Sem resposta inicial, proposta provisória de até duas tentativas de recontato e template final separado; com contato e silêncio, quantidade normalmente de 2 a 5, conforme engajamento; qualquer número e janela ainda sujeitos a políticas aprovadas.
- A F02 propõe sequência completa, intervalos, horário e templates previamente aprovados; a S0 confirma elegibilidade antes de cada envio e interrompe o que se torna indevido.
- O template final fixo é separado; a versão documental anterior priorizava envio aproximadamente 24 horas depois da última tentativa e **24 horas sem resposta após o envio real do template final** para classificação automática de `perdido` por inatividade.
- A janela WhatsApp Meta de 24 horas calcula-se desde a última inbound do cliente, não desde o encerramento humano, o template ou o agendamento de cadência.
- Falha comprovada, estado de mensagem desconhecido e cancelamento por nova resposta devem ser rastreados. API aceita envio ≠ entrega/lida; não inventar evidência.

**Nova regra pós-alinhamento:** uma pendência identificada pela F03 no atendimento humano concluído volta preferencialmente ao Consultor/Gestor, **não automaticamente à F02**. A F03 pode provocar `perdido` por desistência inequívoca sob S0 sem confundir com a perda por inatividade da F02.

## 4A. Regras operacionais mais antigas, compatíveis e que não devem desaparecer no resumo

**[DA] Entrada e prospecção (docs 08A Q01–Q05/Q19/Q30 e 08B Q49–Q51):** a fase inicial é baseada em listas de contatos aptos e legalmente elegíveis. O simples **telefone WhatsApp apto** pode ser entrada suficiente; nome e demais campos não são indispensáveis para incluir um lead. A origem/lista importada **não comprova por si consentimento ou início de conversa**. Um lead pode ficar em `aguardando primeiro disparo`, depois `primeiro disparo enviado` após envio comprovado, e somente se há resposta/manifestação começa o atendimento conversacional. Lotes novos são independentes e seus campos auxiliares **não substituem declarações cadastrais consolidadas na conversa existente**. A identificação comercial anterior por telefone **entra em tensão** com a nova diretriz de múltiplos números por cliente; AL-IA-01/04 registram a necessidade de conciliar.

**[DA] Reentradas (docs 08A Q26–Q29):** após `cadastro enviado ao banco` a pessoa retorna ao **humano**, não à F01, inclusive se aparecer em novo lote; após `vendido` retorna humano por qualquer assunto. Após `perdido`, pode haver novo ciclo e, quando cabível/autorizado, F01 pode atuar novamente com histórico daquela concessionária. Opt-out, exclusão legítima e mudança de titular do número impedem restabelecer um histórico eliminado ou vinculá-lo a pessoa errada. Separar evento de nova solicitação da criação física de outra ficha.

**[DA] Cadência e falhas (doc 08B Q52–Q59):** uma **primeira tentativa de recontato que falha** não elimina a próxima. **Duas falhas comprovadas consecutivas** cancelam a cadeia **e produzem `perdido` técnico via S0**, conforme decisão posterior WA-18C/WDC-13; um `sent` comprovado entre falhas zera o contador. Não tratar timeout, aceite HTTP ou estado Meta desconhecido como falha comprovada. Resposta do cliente, recusa expressa, handoff definitivo, `cadastro enviado ao banco` ou `perdido` cancelam/bloqueiam etapas futuras incompatíveis. Um novo silêncio após nova conversa pode gerar novo plano/contagem; pedido de retorno em data futura pode orientar esse plano. O **template final não conta** nas duas tentativas (sem resposta inicial) ou no intervalo provisório 2–5 (conversa já engajada); a preferência anterior era enviá-lo **aproximadamente 24h depois da última tentativa**, se aplicável, e então **esperar mais 24h após seu envio efetivo** antes de marcar `perdido` por inatividade. Não são as mesmas 24h da janela Meta.

**[DA] Horários (doc 08B Q55):** não foi fixada proibição comercial interna genérica de recontatar no domingo, feriado, madrugada ou fim de semana; F02 escolhe ocasião apropriada com contexto, cliente e restrições legais/Meta. A F01 em recepção automatizada pode operar continuamente, se autorizada; **atendimento humano** ocorre em horário comercial. Ausência de bloqueio interno universal não significa permissão para incomodar nem dispensa conformidade.

**[DA] Limites de discurso/qualificação (doc 08B Q60–Q70):** persona/frase de apresentação da F01 ainda **não foram definidas**; não fingir que é pessoa humana ou representante com alçada bancária. Coleta natural, sem ordem engessada; nome, moto, entrada e parcelas eram **exemplos**, não catálogo aprovado. Lead elegível de entrada é **minimamente qualificado**, não pronto para remessa. Condições fixas de valores e taxas continuam dependentes de informação oficial; concorrente por si não é motivo de handoff. Exigem atenção humana reclamação séria, questão jurídica, dados de terceiros, incerteza sem fonte oficial ou ato bancário sem autorização. **Confirmação final por e-mail era tendência cogitada, não decisão aprovada**, e não pode ser tomada como mecanismo obrigatório.

**[DA/R] Mídia (docs 06 e 08B Q67/Q69):** a arquitetura antiga preservava texto integral, transcrições/extrações e metadados autorizados, **não mídia bruta no banco operacional por padrão**. O alinhamento recente da F03 exige **disponibilidade lógica de áudio/vídeo/imagem/documento** quando necessário; essa tensão não está tecnicamente resolvida e deve ser conciliada sem perder nenhum objetivo.

**[HS → DN 22/10 — interpretação corrigida] WhatsApp dedicado (doc 08A Q20 e Meta DEC-WA-05):** a fonte histórica chamava o número de ‘da Prumo’, enquanto a DEC-WA-05 atribuiu estrutura BM/App/WABA/canal ao contexto da concessionária. **Esclarecimento expresso posterior:** a Prumo é quem, com autorização da concessionária, **providencia o número, coloca-o na estrutura Meta da concessionária, obtém o acesso autorizado à API e opera todos os atendimentos por esse canal**. A estrutura empresarial Meta da concessionária e o **controle operacional exercido pela Prumo** coexistem. Não usar as duas redações antigas isoladamente para deduzir propriedade jurídica irrestrita de qualquer lado; aquisição/portabilidade/contratos específicos dependem de documentação [R/V]. Número emissor permanece dedicado a uma loja, nunca ao telefone pessoal do Consultor. Este texto registra a **precisão mais recente**, preservando a origem histórica.

## 5. Estruturas de segurança anteriores que permanecem relevantes

- Separação por concessionária e identidade do canal emissor (número dedicado por loja), sem busca global do mesmo CPF/telefone para atendimento.
- Atos de Banco (remessa/resultado) necessitam evento/prova reais; `vendido` sempre ato humano comprovado, e negativa definitiva bancária em caso remetido também depende de humano + evidência.
- Catálogo de templates com versões e registro individual de envios, status, falhas, cancelamentos e correlação.
- Dados de cadastro e comunicações tratados segundo finalidade, bases legais, política de privacidade, consentimentos/opt-out e obrigações de segurança.
- Consulta empresarial/administrativa por IA externa não transforma a IA em administrador de infraestrutura; confirmação de escritas MCP, autoria e trilha protegida permanecem relevantes.

## 6. Ideias que **não** foram convertidas em capacidade homologada

As seguintes linhas devem constar como **histórico ou pendência**, nunca como mecanismo já existente:
- IA Analista autônoma alterando configurações automaticamente; pipeline automático de experiências e publicação de estratégia.
- Submissão automática de novos templates para aprovação Meta pelo antigo agente Analista.
- Modelo/API OpenAI específicos, caching obrigatório, RAG por índice específico, limites/custos efetivos, tratamento multimodal no provedor sem consentimento.
- Remessa direta à instituição financeira, consulta de pagamentos e cálculo efetivo de remuneração com regras externas ainda não aprovadas.
- Formulário/checkbox equiparado a contrato financeiro, aceite completo ou identidade comprovada.
- Alterar código, SQL, governança ou segurança pelo MCP dos Diretores.
- Conteúdo por concessionária que altere as **instruções globais** da F01/F02/F03; essa hipótese foi expressamente rejeitada em 22/10.

## 7. Critério para uso futuro deste anexo

Ao procurar uma ideia antiga, determinar: **foi decisão vigente na época? existe decisão posterior mais específica? exigia homologação de terceiros? tornou-se proposta revogada?** Nunca promover automaticamente descrição histórica [HS] a requisito [DN]. Os quatro documentos atuais de alinhamento detalhado são o registro recente; alterações de contrato físico só mediante conciliação com frentes proprietárias.

**Fontes diretas:** consolidado auditado de 10/10/2026 §§0–12, 16, 20; pacote Drive de 17/10 docs 05, 06, 08B, 08C, 10, 11, 13A, 21, 22, 23 e 41; materiais da frente OpenAI anteriores a 22/10.
