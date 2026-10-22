# AL-IA-01 — Jornada de atendimento, papéis das IAs, histórico, ficha e estados

**Data de consolidação:** 22/10/2026  
**Fonte:** decisões expressas do responsável no alinhamento funcional de 21–22/10/2026, em continuidade aos contratos e debates anteriores.  
**Estado:** **[DN] decisão de negócio recente**, **[DA] decisão anterior ainda compatível**, **[P] proposta de desenho**, **[R] pendente de reconciliação interna**, **[V] dependência externa**.  
**Natureza:** DOCUMENTAÇÃO na frente OpenAI (PR #3). Não equivale a migração, API, teste, aceite cruzado S0, autorização Meta/Banco/LGPD, implantação nem modificação do PR #1/#2/#8/#12.

> **Precedência:** este registro documenta manifestações **mais recentes** do responsável. Em caso de colisão com docs anteriores (13A/21–23/24/40/41 ou OAI-05/07/08), a divergência precisa ser apontada e conciliada formalmente pelas frentes responsáveis, **não** corrigida de modo invisível no código. A distinção [DN] × [P] × [V] é obrigatória.

## 1. Vocabulário, escopo e invariantes

1. **[DN/DA]** Papéis de interface: **Diretor** (antigo responsável/administrador), **Gestor** e **Consultor** (antigo operador). Identificadores técnicos legados não são renomeados por este documento. A equipe humana pertence à operação Prumo, mesmo quando atua em concessionária específica.
2. **[DN/DA]** Isolamento **absoluto por concessionária**: o mesmo telefone/CPF em A e B representa contextos totalmente separados; nenhuma IA, humano, consulta, resumo, log, conhecimento privado, ficha, histórico ou indicação da própria existência do registro em B é exposta ao atendimento de A. O canal de saída próprio de uma concessionária não autoriza consulta de outra. Autorizações e garantias devem existir na S0, não somente em prompts.
3. **[DN/DA]** WhatsApp oficial Meta como canal principal. A janela de serviço de **24 horas conta da última mensagem recebida do cliente**; janela Meta fechada não é atendimento concluído; envio de template não reabre por si uma janela de mensagem livre. Fora da janela, a comunicação só ocorre por templates/aplicações permitidos e com verificações atualizadas.
4. **[DN/DA]** A F01 é a IA que conversa comercialmente com o cliente; a F02 planeja recontatos e templates já existentes; a F03 extrai informação e classifica desfechos **após conclusão expressa de atendimento humano**. F02 e F03 não são interlocutoras de clientes.
5. **[DA]** Não há IA Analista/Otimizadora autônoma aprovada, apesar de aparecer como visão histórica no consolidado de 10/10. O documento 06 v4.6 posterior a excluiu explicitamente. Melhoria da operação e análise administrativa ficam como possibilidades governadas por humanos e MCP, sem inferir agente que altera as próprias regras ou desenvolve código por conta própria.

## 2. F01 — Vendedora e atendimento por IA

**[DA/DN]** A F01 atende de forma natural e progressiva, conhece apenas a concessionária atual, consulta conhecimento autorizado, apresenta o LiberaCred sem promessas financeiras inventadas, trabalha dúvidas e objeções com respeito, identifica necessidades, solicita dados permitidos e atualiza informações cadastrais conforme a autorização técnica do backend. Sua orientação/estilo vêm de campos globais separados de instruções e comportamento (ver AL-IA-02).

- Linguagem WhatsApp curta, humana e adaptativa; não transformar a conversa em formulário rígido nem alegar aprovação do Banco sem comprovação. Pedido explícito do cliente por texto/áudio deve ser levado em conta; padrão reiterado pode informar preferência, áudio isolado não fixa preferência permanente. Voz, transcrição, mídia e templates dependem das respectivas homologações e canais.
- Ante dúvidas de teor jurídico/regulatório, dificuldades técnicas/linguísticas, pedido humano ou qualquer handoff válido, faz entrega apropriada e **interrompe suas mensagens naquele caso**. O fato de não existir consultor disponível não torna lícito revelar distribuição, escalas ou equipes à F01; S0 decide alocação/fila.
- **[DA]** Cliente que **já comprou naquela concessionária** e volta espontaneamente, qualquer que seja o assunto, vai diretamente para humano; não retorna à F01. Venda e histórico anteriores não são retroativamente alterados. Se compra foi em A e contato ocorre em B, B não pode saber da compra em A; a situação é analisada apenas pelo contexto conhecido em B. Manifestação do próprio cliente de compra anterior deve ser encaminhada a humano, sem tratar alegação como prova.
- **[DN/V]** Objetivo futuro, se formalmente viabilizado: quando a F01 concluir dados e condições necessários, **desencadear** remessa direta por operação autorizada da plataforma; caso não haja integração bancária direta homologada, entregar ficha pronta ao consultor para remessa humana real. F01 não é conexão bancária independente nem assume autorização por mera conclusão conversacional.

## 2A. Complementos auditados da entrada e do retorno [DA/R]

- **[DA] Entrada da carteira:** fase inicial admite leads elegíveis de listas/importações; o **telefone/WhatsApp apto** pode ser o único campo inicial. `aguardando primeiro disparo` não significa conversa iniciada. `primeiro disparo enviado` depende do **envio real** do primeiro template sem resposta; a conversa atendida pela F01 começa quando o cliente **manifesta-se/responde**, ou por entrada receptiva, e passa a `em atendimento pela IA` quando pertinente. A lista-mestre de campos e as condições oficiais de elegibilidade/opt-in continuam pendentes.
- **[DA] Novos lotes importados:** cada remessa é lote independente; **não substituir os dados conversacionais mais confiáveis por campos auxiliares reapresentados**. Mesmo contato ativo não inicia duas conversas/cadências paralelas. Identificador comercial vigente no acervo anterior é **telefone dentro da concessionária**; a nova hipótese de vários telefones por cliente requer conciliação específica de identidade [R] (AL-IA-04).
- **[D Meta/DEC-WA-05] Canal e titularidade (correção interfrentes 22/10):** **cada concessionária é titular da própria conta Meta, App, WABA, número WhatsApp de atendimento e catálogo de templates**; a Prumo é prestadora/integradora delegada, não proprietária presumida dos números. O canal de atendimento não é o número pessoal do Consultor, e o mesmo número emissor não serve simultaneamente a lojas distintas. Propriedade real, permissões e credenciais dependem de conferência externa [V]. **A premissa antiga 'número da Prumo dedicado à loja' está SUPERADA quanto à titularidade**, embora a exclusividade por loja continue. Referência: PR #2 DEC-WA-05 e índice WDC-02/03.
- **[DA] Horários:** atendimento receptivo automatizado pode ser contínuo quando permitido; humano atua em **horário comercial**. Não havia restrição comercial interna universal fixada para fins de semana, madrugada ou feriados, mas horários, bom senso, manifestação do cliente e regras legais/Meta prevalecem.
- **[DA] Cliente explicitamente informa compra anterior e quer nova contratação:** F01 escala ao humano da **concessionária corrente**, mesmo que ela não possua prova de compra em seu próprio histórico; não inferir que o Banco autoriza vários contratos nem consultar outra loja.

## 3. F02 — Planejadora de recontatos

**[DA]** F02 organiza e ajusta planos de recontato dentro de critérios internos/externos, selecionando **apenas templates previamente cadastrados/aprovados, com versão**. Não redige livremente um template novo para disparo, não autoriza a si própria exceções, não envia por conta própria e não altera o resultado Meta. S0 planeja/executa/cancela sob revalidação; Meta é responsável pelo transporte.

- Primeiro template de abordagem inicial é mecanismo separado da cadeia da F02. Para pessoas nunca responsivas, o doc 08B previa provisoriamente duas tentativas de recontato + template final separado; para conversas já engajadas, normalmente duas a cinco tentativas planejadas por engajamento. **Faixas provisórias, não limites bancários/Meta homologados.**
- Plano inclui ordem, template/versão, horários, motivos, execução, cancelamento e falhas; novas respostas devem cancelar envios incompatíveis. Pedido de retorno futuro é contexto relevante.
- Template final é fixo, versionado e separado das tentativas. A regra documental anterior prefere **envio do template final cerca de 24h após a última tentativa**, quando elegível; **são outras 24h após o envio efetivo do template final, sem resposta**, para encerrar a cadeia e registrar `perdido` por inatividade. São **dois intervalos diferentes**. Isso não é a janela Meta nem o botão de conclusão humana. Falha/não envio do template final **não autoriza** fingir que se iniciou a segunda contagem.
- **[DA] Falhas da cadeia:** uma tentativa falha **não cancela automaticamente** a seguinte; **duas falhas comprovadas consecutivas cancelam as tentativas posteriores**. Erro/timeout ou status Meta incerto não conta cegamente como falha comprovada. Resposta do cliente, recusa explícita, handoff definitivo para humano, `cadastro enviado ao banco` ou `perdido` cancelam/bloqueiam recontatos incompatíveis. Se cliente voltar a responder, planos futuros daquele ciclo são cancelados; silêncio posterior pode gerar **novo plano/contagem**, quando elegível. Pedido de retorno em data futura pode informar o plano sem criar novo status.
- **[DA/P] Recuperação de falha operacional geral:** proposta anterior é tentar recuperação controlada uma vez e, persistindo, encaminhar a humano com alerta técnico; **não confundir** essa rotina com duas falhas consecutivas de envio de templates nem com incidente sistêmico crítico da F03.
- **[DN]** Se após atendimento humano concluído a F03 identificar falta de informações essenciais, prefere-se nova tarefa ao **consultor original**, e não iniciar automaticamente uma nova campanha F02; quando consultor indisponível, notifica-se seu Gestor responsável.

## 4. Consultor, conclusão humana e F03

**[DN] O consultor conversa; não edita a ficha.** Não haverá interface nem permissão de modificação manual de campos cadastrais pelo Consultor. Ele pode visualizar a ficha preenchida e as lacunas (**visão integral provável, interface ainda sujeita a definição**), dialogar com o cliente, esclarecer ambiguidade e pressionar **Concluir/Encerrar atendimento**. As operações de remessa humana real e marcação manual de venda/negativa definitiva, nas condições do Banco e com evidência, são atos distintos de edição cadastral, e não foram revogados.

**[DN] Gatilho estrito:** somente o comando explícito de conclusão do atendimento humano aciona a F03. Expiração de 24 horas do WhatsApp, ausência de mensagem, leitura ou mera entrega do caso NÃO acionam a F03. Mesmo após fechamento da janela Meta, um caso ainda não concluído permanece visível ao Consultor nas condições de atribuição/permissão; o Consultor pode eventualmente operar templates permitidos. Não se presume autoencerramento.

**[DN] Repetição:** um cliente pode retornar e conversar novamente com o mesmo consultor ou outro autorizado, e ocorrer **novo encerramento humano**; cada encerramento válido gera nova execução F03. Essa repetição não significa automaticamente novo ciclo comercial, nova venda, nova ficha ou perda do histórico.

**[DN] Corte imutável e histórico integral lógico:**
- A F03 tem direito lógico ao **histórico completo disponível desse cliente dentro daquela mesma concessionária**, desde o primeiro contato feito na plataforma, inclusive anos antes: mensagens de F01, clientes e diferentes consultores, handoffs, templates, autores, datas, mídias e eventos contextuais autorizados.
- O conjunto analisável termina **inclusive na última mensagem existente no instante daquele encerramento**. Nunca inclui mensagem posterior ao seu `cutoff`. Uma nova mensagem pode participar de uma execução FUTURA após outro encerramento, sem modificar retroativamente o anterior.
- Contexto histórico não significa transcrever indiscriminadamente todos os bytes para um único prompt: recuperação em partes, indexação, resumos com acesso à fonte e processamento multimodal são estratégias técnicas **[P]** que precisam preservar completude lógica, autoria, ordem, correções e privacidade.
- Declarações antigas e recentes não são automaticamente equivalentes. Datas, intenção, tipo de dado, falas do cliente e confirmações pelo Consultor são evidência. A interpretação semântica é essencial; informação mais recente não prevalece sem análise de significado.
- Áudio, vídeo, foto, imagem, documento e outros anexos do histórico devem estar **logicamente disponíveis à F03 conforme acesso autorizado**, com data/proveniência. A F03 escolhe o que precisa consultar. Integração multimodal, obtenção/transcrição/guarda e segurança ainda **[R/V]**, não funcionalidades já entregues. **Conflito explícito a conciliar:** os docs 06/08B antigos orientam **não reter mídia bruta no banco operacional por padrão**, apenas transcrições/extrações/metadados permitidos; a decisão nova exige que a F03 possa examinar conteúdo multimodal quando necessário. Não inventar retenção eterna nem apagar a necessidade de acesso. Definir fonte de mídia/transcrição, prazo e tratamento legal antes de fixar arquitetura física.

**[DN] Ficha única evolutiva por concessionária:**
- Os dados do cliente naquela concessionária permanecem numa **ficha cadastral contínua**, atualizada pelas IAs e ações autorizadas, em vez de criar outra ficha inteira para cada oportunidade/negociação. Ex.: renda R$3.000 registrada em um encerramento, nova conversa esclarece R$3.500; o novo encerramento reanalisa e atualiza valor atual, preservando fonte histórica.
- Não importar conversas antigas ao início da plataforma. F01 inicia captação e a F03 trabalha no histórico originado na plataforma. Após anos, informações antigas poderão exigir ponderação temporal.
- Novos atendimentos, negociações, resultados e documentos enviados ao Banco podem manter **eventos/snapshots históricos próprios** para preservar a realidade daquele instante. Isso é diferente de duplicar a ficha viva do cliente.
- Cadastro enviado anteriormente ao Banco **não impede** F03 de atualizar silenciosamente dados após nova conclusão humana. Não exige notificação rotineira só pela existência de remessa anterior. Atualização cadastral não falsifica o conteúdo da remessa passada.
- A F03 extrai **todos os campos permitidos e identificáveis do catálogo**, inclusive opcionais, com fonte e interpretação válida. Não inventa dados. A S0 é responsável por validar tipos, versões, autorização, proveniência e executar alterações permitidas.

**[DN] Dúvidas e falhas:**
- Se houver contradição genuinamente não resolvida, F03 sinaliza campo e pergunta ao Consultor; o próprio diálogo e sua compreensão são fontes para resolver. Exceção esperada rara. Falta de campo essencial retorna ao humano; falta só de opcional não bloqueia remessa.
- Consultor original preferido; se indisponível, a F03 envia pendência ao **Gestor daquele Consultor**, com identificação do atendimento e dos campos faltantes. Gestor decide se resolve pessoalmente quando autorizado ou redistribui. A S0 assegura endereçamento/permissões; a IA não distribui arbitrariamente.
- Falha recorrente da F03 é **incidente crítico de software**: diagnosticar e reparar causa com urgência pelos responsáveis técnicos; não criar preenchimento manual rotineiro como substituto. Eventual administração excepcional por Diretor/MCP é outro fluxo, não concessão ao Consultor. Não suspender a operação inteira ou autocorrigir código silenciosamente.
- Execuções concorrentes exigem garantia de que uma análise antiga não sobrescreva uma correção mais recente. `cutoff` histórico imutável e elegibilidade/versão para **aplicação** são coisas diferentes, cuja reconciliação pertence à S0.

## 5. Estados comerciais e autoridade de alteração

**[DA] Oito estados canônicos (não criar nono):**
1. `aguardando primeiro disparo`
2. `primeiro disparo enviado`
3. `em atendimento pela IA`
4. `em atendimento pelo operador` (exibição futura: consultor)
5. `cadastro enviado ao operador` (exibição futura: consultor)
6. `cadastro enviado ao banco`
7. `vendido`
8. `perdido`

**[DN]** A F03, após encerramento humano, **pode propor e desencadear alteração automática de status comercial**, dentro do contexto/configuração operacional aprovada e das regras S0, inclusive identificar **desistência/perda** e registrar razão. Essa decisão **substitui a orientação anterior** OAI-05/OAI-07/PR #8 de bloquear universalmente mudança automática para `perdido` em conclusão humana. O catálogo final de motivos e transições ainda [R]. Nenhum campo de instrução da F03 concede poderes além de S0.

**[DA/DN]** `vendido` é a exceção explícita: SOMENTE Consultor humano devidamente autorizado, com confirmação/evidência real exigida do Banco, marca manualmente. F01/F02/F03 não podem marcar venda. `cadastro enviado ao banco` exige **remessa real comprovada**, não interpretação, ficha completa ou promessa de envio. `cadastro enviado ao operador` exige entrega real da ficha à fila/destinatário correto. Marcas de banco não decorrem só de conversação.

**[DA] Negativa bancária ≠ desistência:** negativa definitiva comprovada do Banco, conforme documento 21, exige lançamento humano autorizado com prova e transita para `perdido`. Pedido bancário de correção/complemento não é negativa. **[DN]** Desistência/sem interesse explicitada pelo cliente pode ser tratada automaticamente pela F03 segundo regras aprovadas; não inventar prova de negativa do Banco.

**[DN/V] Remessa instituição financeira — dois caminhos ainda condicionados:**
- Preferido: **envio direto pela plataforma**, quando houver autorização e integração homologadas; F01 ou F03 podem disparar o processo após verificações S0. Serviço bancário da plataforma é comum às duas IAs, não duas integrações autônomas.
- Contingência: **entrega ao humano** para remessa oficial/comprovada caso envio direto não seja possível.
- O próprio responsável decidiu **não investigar/fixar a integração bancária nesta etapa**; viabilidade, contrato, provas e capacidades continuam [V/R]. Não simular status de enviado por expectativa de integração.

## 6. Casos de retorno, equipe e tempo

**[DA/DN]** Após `vendido`, retorno espontâneo na mesma concessionária é **sempre humano**, para qualquer assunto. A ficha atual continua atualizável em encerramentos humanos posteriores, preservados os eventos de venda histórica. Não reativar F01 pela nova oportunidade. Casos/ciclos históricos não devem ser apagados/reescritos para simular continuidade.

**[DA]** Após `cadastro enviado ao banco`, retorno espontâneo ou reaparecimento do cliente em nova lista na mesma concessionária vai **diretamente a atendimento humano**, sem reativar F01 nem rebaixar retroativamente o ciclo bancário anterior; um banco já recebeu/remessa comprovada não é sinônimo de venda. **[DA]** Após `perdido`, um contato novo/elegível pode iniciar **novo ciclo comercial** vinculado ao histórico da mesma concessionária, respeitando opt-out e demais guardas, sem restaurar automaticamente mensagem/atendimento apagado legalmente.

**[DN] Continuidade com o mesmo Consultor e janela Meta:** durante a janela de atendimento contada desde a última mensagem do cliente, a preferência expressa é que o cliente consiga **voltar a falar com o mesmo Consultor que estava conduzindo o caso**, se ele ainda for o responsável autorizado. O fechamento da janela Meta, sozinho, **não retira a conversa da carteira do Consultor e não dispara F03**. Mesmo sem poder enviar mensagem livre fora da janela, ele mantém a possibilidade de utilizar templates oficialmente elegíveis se o caso **não foi efetivamente concluído por ele**. **[R]** Quando o Consultor já clicou em Concluir e a janela Meta expirou, prazo de reserva/reatribuição da carteira e procedimentos de retorno ainda dependem das regras operacionais S0/S1; não inventar uma liberação automática da atribuição por 24h.

**[DN]** A janela Meta de 24h é independente do botão humano; disponibilização/atribuição do atendimento não deve ser encerrada só pelo relógio da Meta. **Não presumir** como norma mais recente uma disponibilidade fixa de 24h após o clique humano: o responsável esclareceu que a referência relevante é a última mensagem recebida do cliente e que só o clique humano conclui o atendimento. Reabertura, posse do caso e transferências são separadas do relógio da Meta e dependem de regras S0/S1.

**[DA]** Gestor supervisiona conversas D2 das concessionárias autorizadas e gerencia equipe/fila com escopo, sem adquirir automaticamente documentos bancários D3/D4 em leitura comum nem titularidade de todos os casos. Consultor mantém acesso somente ao atribuído; gestor designado pode atuar como consultor nesse caso. Nenhum acesso cruzado entre concessionárias.

## 6A. Identificação de cliente com novo número [DN/R]

O responsável deseja que a **IA conduza uma, duas, três ou quantas verificações contextualmente necessárias** para avaliar se o novo número pertence à mesma pessoa **naquela concessionária**, sem simplesmente confiar numa alegação. Quando o número anterior não for mais válido, a intenção é **substituí-lo no cadastro vivo**; quando ambos ainda forem úteis, **vincular múltiplos números à mesma ficha**, sem ficha duplicada. A intenção é funcional [DN], mas o método de prova de identidade, risco de número reciclado/compartilhado e aplicação segura pela S0 continuam [R]. **Não tratar a decisão anterior de telefone como identificador comercial único como se a transição para múltiplos números já estivesse modelada ou homologada.**

## 7. Dependências técnicas e cenários críticos [P/R]

Os seguintes itens são **critérios de futura especificação/teste, não testes executados**: (a) mesmo telefone A/B, histórico e embeddings sem vazamento; (b) fechamento no último evento e mensagem logo após, com duas execuções independentes; (c) retorno após `vendido` sem F01; (d) renda antiga x correção nova inclusive concorrência; (e) ficha já enviada ao Banco seguida de nova atualização cadastral sem adulterar snapshot bancário; (f) mídia multimodal autorizada e indisponível com fallback explícito; (g) campo essencial/optativo e consulta ao gestor; (h) desistência explícita x negativa bancária; (i) remessa não comprovada sem `cadastro enviado ao banco`; (j) falha crítica F03 sem edição manual pelo consultor; (k) janela Meta expirada sem disparo F03; (l) confirmação manual de `vendido`.

**Referências anteriores:** pacote Drive 17/10 docs 06, 08B, 08C, 13A, 21, 22, 23, 41; consolidado auditado 10/10; OAI-05, OAI-07, OAI-08, E01 v0.2; frente S0 PRs #1/#8/#12. Ver índice AL-IA-00 e matriz AL-IA-04.
