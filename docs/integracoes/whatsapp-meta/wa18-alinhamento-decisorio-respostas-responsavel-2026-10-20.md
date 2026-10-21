# WA-18 — Registro de alinhamento de decisões WhatsApp/Meta (20/10/2026)
> **Atualização de precedência — WA-18B possui precedência sobre itens revistos neste documento:** o responsável posteriormente confirmou que a edição de templates pode ser permitida quando a Meta a autorizar; o **mapeamento da versão aprovada** é que fica congelado. Confirmou também **duas falhas comprovadas consecutivas → cancelar restante da cadência e marcar `perdido` por erro sistêmico**, sem chamar a Planejadora por falha comum; a Planejadora pode reorganizar somente modelos disponíveis e aprovados quando a Meta invalidar algum deles. Ver [WA-18B](./wa18b-alinhamento-fechamento-optout-variaveis-falhas-cadencia-2026-10-20.md). O opt-out já possui tabela S0 sintética, mas não homologação real.


**Tipo:** decisões verbais expressas do responsável, verificações externas pontuais e perguntas residuais. **Estado:** registro para auditoria/reconciliação, não uma migration, regra de produção ou autorização externa. **PR #2 Draft**, sem merge/deploy/Graph real. A frente MCP é independente: aqui somente contratos de domínio WhatsApp/Meta.

## A. Decisões expressas do responsável nesta sessão [DECISÃO INTERNA]

### D-WA18-01 — [SUPERADA EM 20/10, VER WA-18B] Template aprovado permanece imutável na Liberacred

> **Esta seção abaixo registra uma posição anterior do responsável, REVISTA logo depois.** A decisão atual é: edição de conteúdo Meta pode ocorrer onde API/estado permitirem, com controle de revisão e novo status/aprovação conforme aplicável; imutáveis são os snapshots históricos e o vínculo de posições com campos da **versão já aprovada**. Não implementar a vedação absoluta abaixo. Ver [fonte canônica](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md) e [WA-18B](./wa18b-alinhamento-fechamento-optout-variaveis-falhas-cadencia-2026-10-20.md).


- Depois que a **Meta aprovou** um template, a plataforma não permitirá modificar seu conteúdo nem seus componentes submetidos (BODY, HEADER, mídia, FOOTER, botões, URLs) na mesma identidade/versão.
- Poderá ser tornado **indisponível** para novos envios no catálogo local, mantendo histórico, snapshot e links dos envios anteriores. Exclusão física na Meta é uma operação técnica **distinta**, não implicada por desativação local, a definir sob confirmação.
- Para alterar texto ou componentes, gerar **novo rascunho/identidade e novo ciclo de aprovação**, preservando versões anteriores.
- **Não concluir que Meta proíbe toda edição:** a Meta possui endpoint `POST /{template-id}` para editar templates; a imutabilidade é decisão deliberada **da Liberacred**, mais restritiva do que a API permite. Referência oficial: https://www.postman.com/meta/whatsapp-business-platform/request/bpcsm6i/edit-template .
- **PENDÊNCIA:** esclarecer se é permitido alterar após aprovação somente o **mapeamento interno de fontes de variáveis** sem alterar conteúdo submetido; a solicitação anterior do responsável previa essa operação. Mesmo sem alterar `{{1}}`, trocar `cliente.nome` por outra fonte pode modificar sentido/risco.

### D-WA18-02 — Administração por MCP com identidade individual e dupla confirmação
- **Todos os responsáveis autorizados** terão conta/vínculo MCP **individual**, de onde podem pedir a IA administrativa para consultar, criar, corrigir, excluir/desativar dados permitidos, anexar mídias e criar/submeter templates. Podem redigir eles mesmos ou delegar geração do texto à IA.
- **A IA não recebe DDL, schema, automodificação estrutural nem superusuário**. O servidor MCP, identidade/delegação, transporte e ferramentas executáveis pertencem a **outra frente**; a frente WhatsApp fornece contratos e operações internas verificáveis.
- **Toda escrita/exclusão:** operação preparada com alvos/antes/depois e **segunda confirmação explícita pelo MESMO responsável autenticado**, revalidação e trilha administrativa append-only; consultas sujeitas a autorização sem confirmação adicional universal. Nenhuma operação é aceita porque um modelo declarou `sou admin`.
- Esta declaração **amplia a intenção funcional** em relação à decisão normativa anterior D41-03 que só autorizava escrita MCP para **importação de lote e remanejamento de casos** e explicitamente vedava alterar templates. Exige **emenda formal da matriz granular por operação**, no futuro ciclo de auditoria. Não inferir que a ampliação está tecnicamente implementada ou permite editar prova bancária/status financeiro/DDL irrestritos.
- Referências: `documentos/41_Decisao_Aprovada_Matriz_Permissoes_Gestor_Operador_MCP_v1_0.md` e `documentos/10_Identidade_e_Auditoria_Administrativa_v4_1.md`.

### D-WA18-03 — WABA, número, catálogo e identidade por concessionária
- **Uma WABA separada para cada concessionária**, e **um número de WhatsApp dedicado a essa concessionária**. Não haverá WABA única central da Prumo.
- A Prumo operará tecnicamente a **API** conforme autorização; WhatsApp exibirá principalmente foto/logo e nome da concessionária, enquanto a IA conhece e respeita a identidade da loja representada.
- **Templates pertencem ao catálogo específico da concessionária/WABA**, sem compartilhamento entre lojas, inclusive quando contêm o nome da concessionária.
- **[RETIFICAÇÃO DE PRECEDÊNCIA — DEC-WA-05 de 17/10]** A titularidade **não estava aberta no conjunto do projeto**: concessionária proprietária da conta empresarial Meta, Meta App, WABA e número; a Prumo opera como integradora delegada. Permanece PENDENTE verificar no painel Meta a configuração de propriedade/acessos, registro, webhooks e credenciais antes do onboarding real. Não alterar mappings técnicos S0-042 ainda; auditar escopo App/WABA/phone por loja.
- Referências com potencial de conflito: `documentos/09_Estrutura_Mensagens_Templates_v4_6.md` e `documentos/34_Roteiro_Homologacoes_Meta_Banco_LGPD_Decisoes_Agrupadas_v0_1.md`, que tratavam números sob titularidade/controle da gestora.

### D-WA18-04 — Opt-out isolado por concessionária
- Se cliente pedir para não receber mais mensagens **na concessionária A**, o pedido bloqueia proatividade no **escopo A**; a concessionária B mantém seu histórico/decisões isolados, sem herdar o opt-out de A e sem consultar cadastro ou conversa de A.
- **A loja B precisa continuar com consentimento e finalidade próprios válidos**; não herdar opt-in de A e não tratar isolamento como dispensa da política Meta/LGPD.
- O pedido de cessar contato, quando identificado com certeza, deve ser **efetivamente respeitado pela execução** antes de novo disparo. A IA pode classificar a intenção em contexto, mas uma vez validado o opt-out o motor não pode decidir ignorá-lo. Não converter opt-out automaticamente em desinteresse/venda/perda comercial.
- Essa decisão escolhe a orientação **escopo A apenas** da antiga DEC-17 (caderno 35), mas exige parecer Meta/LGPD para ativação real. Registrar como decisão funcional nova, não como homologação externa.

### D-WA18-05 — Falha persistente e silêncio podem produzir perda comercial
- Após **falhas comprovadas e repetidas** de envio de templates, o lead pode terminar `perdido`, **com motivo técnico específico** (ex.: falha sistêmica, falha definitiva de envio), em vez de considerar automaticamente que recusou a oferta.
- Se não houver resposta, a regra de ausência de retorno pode marcar `perdido` quando a **cadência/finalização efetivamente enviada e janela de resposta** cumprirem os requisitos já aprovados.
- O eventual recontato de leads perdidos por erro será **nova campanha/lote deliberadamente importado por responsáveis/gestores**, com checagem renovada de elegibilidade e histórico; não autorrecontatar nem apagar perda anterior.
- **Nunca confundir:** `API_ACCEPTED`, falta de callback, timeout ou COMMIT perdido **não são evidência de falha definitiva nem de entrega**. A WA-16 e a recuperação Meta/S0 continuam bloqueando repetição cega. Antes da decisão `perdido` técnico, devem existir critérios verificáveis e separação entre resultados definitivos e incertos.
- **PENDÊNCIAS objetivas:** quantas falhas consecutivas qualificadas encerram a cadência, qual janela/estratégia de conciliação para resultado incerto, e qual marco exato do silêncio (sem começar 24 h de um envio que não ocorreu).
- Conflitos a reconciliar durante auditoria: recomendações DEC-13/14/15 do `documentos/35_Caderno_Decisoes_Agrupadas_Recomendacoes_Impactos_v0_1.md`. **A nova decisão muda a saída comercial após exaustão de falhas**, não reclassifica qualquer timeout como falha.

### D-WA18-06 — Planejadora reage à suspensão/rejeição, sem editar template aprovado
- A **IA Planejadora (API da OpenAI)** deve ser acionada se a Meta rejeitar, pausar, suspender ou retirar disponibilidade de template usado em uma cadência.
- O contexto entregue precisa conter escopo loja/WABA, identificadores e versão do template afetado, categoria/idioma, estado atual e motivo/código da Meta quando disponível, sequência e objetivos da cadência, templates **alternativos já aprovados** e as restrições de cada caso; limitar dados pessoais.
- A Planejadora pode avaliar e propor ou selecionar substituição apropriada, respeitando a política que vier a ser confirmada. **Não edita template aprovado**, não declara aprovação, não inventa substituto e não ganha poder administrativo MCP automaticamente.
- Se for necessário criar texto/novo template, o fluxo de **IA administrativa autorizada via MCP** gera rascunho novo, com responsável e segunda confirmação antes de submissão; a Planejadora não se transforma em autora/submissora administrativa por sugestão de substituição.
- **PENDÊNCIA:** confirmar se a Planejadora poderá substituir automaticamente um template **já aprovado** na cadência (dentro das mesmas finalidade/categoria/regras), ou deverá solicitar confirmação humana para substituir. Em todos os casos, bloquear emissões pelo template indisponível.

### D-WA18-07 — Resposta de botões é interpretada no contexto comercial
- Botões de template incluem escolhas de resposta, links e chamadas. Quando cliente responde um botão de decisão, a **IA de atendimento** interpreta a mensagem e o contexto do caso para decidir continuidade, encaminhamento ou desfecho comercial. Não converter automaticamente `Não tenho interesse` em `perdido` sem análise aplicável.
- **Exceção técnica/legal:** um pedido de `Parar mensagens` / opt-out explícito, uma vez validado, deve bloquear imediatamente novos envios proativos **naquela loja**, mesmo quando a IA interprete o motivo comercial separadamente. `STOP` não é o mesmo que `perdido`.

### D-WA18-08 — Indicadores e custos
- **Aprovar na pauta futura:** saúde operacional de templates por concessionária e eficácia por versão, componente, botões, horário e reação, com denominadores explícitos; dados de entregas, respostas e reclamações não devem ser inferidos de HTTP 2xx.
- **Não implementar limite/bloqueio automático de gasto** por concessionária no motor; a Prumo analisará o custo externamente e poderá ajustar a configuração da IA posteriormente.
- Capturar quando disponível metadados técnicos de tarifação (`pricing.billable/category` ou equivalente) e usar rate card/relatórios financeiros autorizados para custo estimado/efetivo **fora do fluxo de autorização de envio**. **Não presumir que POST de envio devolve valor exato cobrado.**
- Categorias de criação `MARKETING` e `UTILITY` devem ser suportadas; a Meta pode reclassificar e sua categoria é determinada pelo **conteúdo/finalidade real**, não pelo preço desejado. **Utility não é genericamente gratuito**. Fontes orientativas: documentação de preço em https://business.whatsapp.com/products/platform-pricing e endpoint de editar https://www.postman.com/meta/whatsapp-business-platform/request/bpcsm6i/edit-template .
- Meta e terceiros podem alterar preços; análise de viabilidade custo separada do envio em produção.

### D-WA18-09 — Cadastro e documentos recebidos
- A IA pode, depois de transparência e aceite apropriado, orientar o cliente sobre informações/documentos necessários para cadastro e futura remessa bancária autorizada; a mensagem do responsável manifesta preferência por **captura de dados, não solicitação indiscriminada de fotos**.
- Documentos e imagens enviados espontaneamente pelo cliente podem **chegar** por webhook, mas o recebimento **não autoriza automaticamente OCR, armazenamento integral, extração de número completo, compartilhamento com o banco ou uso de dados proibidos no canal**.
- A Política Empresarial WhatsApp proíbe **solicitar ou compartilhar números completos de documentos de identidade, contas financeiras e cartões**, entre outros identificadores. Antes de ativar, definir quais campos podem ser tratados, quais devem ir para **canal seguro distinto**, base legal LGPD, acesso, retenção e canal de envio autorizado ao banco.
- Continua pendente a homologação externa do enquadramento do LiberaCred frente às regras financeiras da Meta; apoio verbal bancário não substitui contrato/prova.
- Fonte oficial Meta: https://business.whatsapp.com/policy/preview?lang=pt_BR e `documentos/34_Roteiro_Homologacoes_Meta_Banco_LGPD_Decisoes_Agrupadas_v0_1.md`.

## B. Pontos sem mudança de decisão

- `mensagens` uma linha por mensagem, `envios_template` tentativa com eventos, `catalogo_templates` por versão exata; auditoria administrativa separada e append-only (`documentos/09_Estrutura_Mensagens_Templates_v4_6.md`, `documentos/10_Identidade_e_Auditoria_Administrativa_v4_1.md`).
- IA Vendedora/atendimento, IA Planejadora e IA administrativa/MCP têm **papéis distintos**. IA melhoradora de atendimento também é separada e só ajusta parâmetros autorizados, sem editar os próprios parâmetros.
- Não confundir recebimento Meta, aprovação de template, envio efetivo, entrega, leitura e venda. Handoff humano e regras bancárias permanecem intactos.
- Dados/regras de uma loja não interferem na outra, mas cada loja continua sujeita à sua própria elegibilidade e política externa.
- Não modificar agora migration S0-042, contrato de ledger, PRs #1/#5 ou ambiente real; esta rodada é **alinhamento**, não execução de nova funcionalidade.

## C. Perguntas residuais realmente necessárias (não presumir decisão)

1. **Após aprovação Meta, pode mudar apenas o mapeamento interno de uma variável `{{n}}` para outra fonte de dados autorizada, sem editar o template, com segunda confirmação e auditoria?** Exemplo trocar `operador.nome` por `operador.primeiro_nome`. Se não, também congelar `mapping_revision`; se sim, restringir a fontes semanticamente compatíveis e snapshot por envio.
2. **Falhas repetidas:** quantas **falhas definitivas comprovadas** e qual período caracterizam exaustão para passar a `perdido` técnico? O que fazer se resultado permanece `INCERTO` depois de conciliação? **Não inventar** quantidade, hora ou prazo.
3. **Alternativa a template indisponível:** Planejadora pode substituir diretamente na cadência por **outro template já APPROVED** da mesma concessionária, finalidade e categoria, ou o responsável deve confirmar essa substituição? Criar novo template sempre via MCP administrativo de responsável, independentemente dessa resposta.
4. **[RESPONDIDA por DEC-WA-05 de 17/10, identificada na auditoria]** A concessionária será proprietária da própria conta empresarial Meta, App, WABA e número; Prumo acessará por delegação. **Ainda conferir prova real de titularidade/onboarding**, não tratar como pergunta de negócio aberta.
5. **Botão explícito de opt-out:** validar execução de supressão automática no escopo da concessionária mesmo antes de a IA fechar eventual decisão comercial. Recomendação de conformidade: sim.

## D. Necessidades de auditoria documental futuras

- **Matriz MCP:** `documentos/41_Decisao_Aprovada_Matriz_Permissoes_Gestor_Operador_MCP_v1_0.md` D41-03 proíbe escrita em templates enquanto a decisão atual pede gestão ampla via MCP. Criar emenda de precedência com escopos por operação, dupla confirmação e bloqueio estrutural, sem apagar texto antigo.
- **WABA/número:** documentos 09/34 falam números gestora dedicados; substituir essa parte pela decisão DEC-WA-05 (17/10) de **conta/App/WABA/número pertencentes à concessionária**. Ainda verificar vínculos efetivos na Meta. Verificar se o esquema técnico `meta_apps_fixture_s0` / `meta_canais_fixture_s0` admite a relação.
- **DEC-13..18 (doc 35):** introduzir marcadores de evidência e desfechos `perdido` técnico; opt-out apenas por loja; esclarecimento de dois estados incertos; substituição de template sem alterações clandestinas.
- **WA-17A/B:** esclarecer conflito entre a implementação anterior que permitia editar `mapping_revision` pós-aprovação e a imutabilidade recém-afirmada. Sem modificar código até resposta.
- **Categorias/custos:** não presumir que utility seja gratuito nem equiparar relatório de cobrança ao webhook; custo não decide envio.
- **Atendimento/documentos:** alinhar importação/extrator de mídia ao parecer Meta/LGPD e regras de entrega bancária.

## E. Estado dos testes e próximos passos

- A WA-15C teve provas integradas de laboratório em CI anterior; WA-16 e WA-17 permanecem **sem CI nativo confirmado** na revisão congelada (44 testes Node e 11 cenários SQL preparados).
- Este registro **não afirma implementação/homologação** das novas decisões. Pausa para alinhamento e auditoria continua ativa. Nenhuma Graph API, Meta, Supabase hospedado, banco real, merge ou deploy acionado.
