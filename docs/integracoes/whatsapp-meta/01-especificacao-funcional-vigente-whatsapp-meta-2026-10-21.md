# WhatsApp/Meta — Especificação funcional vigente da frente

**Atualização:** 22/10/2026 · **Condição:** decisões de produto até 22/10 mais regras históricas compatíveis e interfaces recentes dos PRs independentes · **Escopo:** WhatsApp/Meta e contratos documentais com S0, S1, OpenAI, MCP futuro e interface dos Consultores. **Esta é a referência FUNCIONAL de consulta; não substitui validações externas nem afirma que tudo está implementado.**

**Leitura obrigatória:** [índice das decisões com IDs WDC-01..22](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md) e [mapa de conflitos e fontes históricas](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Para registros anteriores, vale a regra explícita de precedência: **última decisão expressa do responsável somente sobre o tópico revisto**; as demais normas históricas permanecem. D = decisão aprovada; H = histórico ainda válido; P = proposta de desenho; V = validação externa; T = situação técnica a comprovar.

## 1. Identidade do produto e escopo da operação [D/H]

- **A plataforma de atendimento comercial ainda NÃO tem nome comercial escolhido.** É desenvolvida/operada pela gestora **Prumo** e utilizada no atendimento às concessionárias para promover/comercializar **LiberaCred, que é o produto de crédito da instituição financeira**. Até nova decisão de marca, em textos e interfaces usar **plataforma**; não chamar o software de LiberaCred nem batizá-lo de Prumo por inferência. Fonte já aprovada: `documentos/17_Identidade_e_Nome_da_Plataforma_v0_1.md`, reafirmada em 22/10; integração entre PRs descrita na [WA-22](./wa22-revisao-cruzada-outras-frentes-contratos-2026-10-22.md).
- **Cada concessionária terá sua conta empresarial Meta, Meta App próprio, WABA separada, número WhatsApp dedicado e catálogo de templates específico**, conforme a DEC-WA-05 expressamente aprovada em 17/10 e reiterada em 20/10. Sem WABA central única da Prumo. Um mesmo cliente pode aparecer em concessionárias A e B, com históricos e direitos independentes; impedir consulta e referência cruzadas.
- O nome e a foto do WhatsApp exibidos ao cliente correspondem à **concessionária**, e a IA conhece e representa a identidade daquela loja. Ela não precisa repetir uma autodescrição artificial a cada mensagem.
- **Decisão de negócio já tomada [D]:** esses ativos Meta são das concessionárias e a Prumo age como integradora **mediante acesso delegado** (DEC-WA-05). **Validação externa ainda necessária [V]:** confirmar em cada conta Meta os titulares efetivos, IDs, habilitação, sistema de permissão, webhook, inscrição WABA e acesso delegado. Não confundir falta de verificação documental real com falta de definição da titularidade desejada.

### 1A. Nomenclatura aprovada dos papéis (WA-21)

**Diretor** substitui o cargo antes chamado responsável, **Gestor** mantém o nome, e **Consultor** substitui o cargo anteriormente chamado operador. Isso altera nomenclaturas visíveis, não permissões técnicas automaticamente. Textos antigos e identificadores físicos continuam preservados até migração coordenada; o substantivo genérico “responsável” não é necessariamente um cargo. [Decisão WA-21](./wa21-papeis-diretor-gestor-consultor-assinatura-2026-10-21.md).

## 2. Registros estruturais separados e dados rastreáveis [D/H]

1. **`mensagens`**: UMA linha por mensagem enviada ou recebida, com loja, conversa/ciclo, direção, tipo, remetente, timestamp, ID Meta quando houver, corpo permitido e metadados JSONB apenas complementares. Não salvar todo chat como um array de JSON nem colunas de mensagens numeradas.
2. **`envios_template`**: UMA linha por tentativa/etapa programada, mesmo cancelada ou falha, com plano/ordem, template e **versão exata**, canal, chave de idempotência, eventos de solicitação/aceite/enviado/entregue/lido/falhou/incerto/cancelado, horário e correlação com a mensagem. Estado atual e **histórico de eventos append-only** separados.
3. **`catalogo_templates`**: templates, componentes, categoria oficial da Meta, finalidades internas, WABA/loja, status Meta, versão/snapshot do conteúdo, vínculos de variáveis e políticas de uso. O contrato lógico é obrigatório; o SQL definitivo será conciliado com S0.

Uma aceitação HTTP/API nunca prova que a mensagem foi realmente enviada, entregue ou lida; callbacks válidos precisam de assinatura, correlação e deduplicação. O banco/S0 controla transições comerciais e possui o estado persistido; o adaptador Meta controla evidências de transporte. Nunca apagar histórico por replanejamento, cancelamento, opt-out ou edição de template.

## 3. Máquina comercial distinta do transporte [H]

Os **oito** status comerciais são, com nomes literais documentados no pacote histórico: `aguardando primeiro disparo`, `primeiro disparo enviado`, `em atendimento pela IA`, `em atendimento pelo operador`, `cadastro enviado ao operador`, `cadastro enviado ao banco`, `vendido`, `perdido`.

Esses status **não são** estados de envio, estados de template, fila humana ou aprovação bancária. A IA não inventa venda, negativa definitiva, remessa bancária, entrega ou leitura. O atendimento humano e os comprovantes da instituição financeira têm contratos próprios, conservados mesmo após mudanças na frente Meta.

## 4. Papéis distintos das IAs e responsabilidade da plataforma [D/H/R]

- **IA de atendimento/vendedora:** conversa e interpreta respostas no contexto daquele lead/loja, respeitando handoff humano, finalidade, opt-out e política Meta.
- **IA Planejadora/Orquestradora:** elabora/revisa a **cadência** (templates aprovados permitidos, ordem, quantidade e horários), inclusive após a Meta rejeitar/pausar/inutilizar um template. Não cria novo template por conta própria, não acessa o MCP administrativo ao faltar opção, não faz POST Graph e não decide autorização final de envio.
- **IA administrativa delegada pelo Diretor autenticado via MCP futuro:** pode criar/editar rascunhos de templates, escrever texto exatamente instruído ou propor texto, anexar mídia, escolher botões, solicitar revisão e demais ações administrativas expressamente autorizadas, sujeitas a confirmação/auditoria. O **servidor MCP real é desenvolvido por OUTRA frente**.
- A **IA separada que melhora o atendimento** possui seus próprios parâmetros e só modifica os parâmetros AUTORIZADOS da IA de atendimento, não se altera autonomamente; não se confunde com Planejadora nem IA administrativa.
- **F03 — extração e classificação pós-atendimento humano (frente OpenAI):** não conversa com o cliente e é acionada exclusivamente pela conclusão humana explícita autorizada na S0. Recupera contexto permitido do mesmo cliente/concessionária até o corte do fechamento, propõe campos/desfechos sem autorizar por si remessa, venda ou disparo; histórico multimodal e portão físico seguem [R/V/T]. Ver [WA-22](./wa22-revisao-cruzada-outras-frentes-contratos-2026-10-22.md).
- **Plataforma/S0 e serviço Meta:** resolvem as variáveis com fonte confiável, revalidam elegibilidade/permissões, registram eventos e só transmitem intenções autorizadas. A IA escolhe a proposta; **a plataforma decide tecnicamente o que é permitido e executa**.

## 5. Meta category versus FINALIDADES do template [D]

**Categoria oficial Meta:** `MARKETING` / `UTILITY` e outros formatos/categorias que a API Meta efetivamente suportar. Tem validade, revisão e políticas do provedor; utility não deve ser presumido gratuito.

**FINALIDADE de template:** dimensão INTERNA e configurável da concessionária, não categoria Meta. Exemplos iniciais, **não enum fechado**: abertura de conversa, recontato, atendimento por consultor, atendimento por IA, campanha determinada, informativo. **Um mesmo template pode ter MÚLTIPLAS finalidades.**

**Permissão independente por finalidade e contexto:** a associação do template com uma finalidade não concede automaticamente acesso a Consultores, Planejadora, outros fluxos ou campanhas. Precisam de concessões expressas e escopadas, considerando identidade/consumidor, loja, WABA, finalidade, situação e público autorizado.

A **finalidade do contato/consentimento/opt-out** é uma TERCEIRA dimensão distinta: não reutilizar seu significado nem sua coluna para indicar finalidades do template.

## 6. Uso de campanha e prevenção de promessa falsa [D/P]

- Um template Meta aprovado **não prova** que uma oferta/desconto/condição de crédito vale para qualquer lead. Templates de campanha só podem ser candidatos se houver campanha vigente, público/lead elegível e condições verificadas por dados confiáveis.
- **Antes de chamar a IA** Planejadora, a plataforma filtra o catálogo segundo loja/WABA, status atual, versão, idioma, finalidades, papéis, campanha e elegibilidade real. A Planejadora não recebe todo o catálogo.
- **Antes da reserva e imediatamente antes do envio**, repetir os mesmos gates; contexto/consentimento/status/campanha podem mudar. Se nenhum template for elegível, não improvisar texto, não usar modelo de campanha fora do público e registrar ausência de opção.
- A entidade concreta de campanhas e seus campos são **P**: reusar o cadastro de campanhas já existente ou aprovado pela frente comercial, se houver; não duplicar estrutura nem tratar criatividade da IA como prova de oferta.

## 7. Autoria, multimídia e edição de templates [D/V]

- Suportar rascunhos com BODY texto e exemplos; HEADER texto, imagem, vídeo ou documento, FOOTER, botões de URL estática ou dinâmica com **rótulo visível distinto do link**, telefone, resposta rápida; recursos Meta adicionais só após contratos técnicos próprios. Nem toda combinação é válida em toda versão de API.
- A IA administrativa pode redigir conteúdo ou obedecer literalmente ao Diretor autorizado; registro distingue autoria humana, assistência e geração por IA, **sem** mudar permissões.
- **Diretor autenticado com permissão vigente** pode solicitar submissão e consulta de status por fluxo administrativo autorizado, mas **2xx/ID da Meta não equivale a APPROVED**. Somente status Meta verificável indica aprovação, e aprovação não equivale a autorização de disparo.
- **Edição de template que já foi aprovado não é proibida pela plataforma por princípio:** oferecer quando API/estado Meta permitir, preservando identificação, ciclo de revisão, exigência de confirmação administrativa e snapshots de versões anteriores. Se a edição exigir reaprovação, bloquear o uso da revisão até Meta confirmar.
- Desativar LOCALMENTE o template para novos envios é diferente de pedir exclusão pela Meta. Em ambos, histórico/snapshot não são apagados e alterações administrativas têm autoria/auditoria.

## 8. Variáveis: fonte congelada por versão; plataforma preenche [D]

- Exemplo de rascunho: `Olá {{1}}, temos informações sobre {{2}}`; fontes fixadas **antes da aprovação daquela versão**: `body.1 -> lead.nome`, `body.2 -> lead.modelo_interesse`. Se a versão for aprovada, **NÃO trocar as fontes desses slots nessa versão**.
- A lista completa de colunas comerciais da tabela de leads **ainda não foi decidida**. Cada nova coluna de negócio pode se tornar **candidata** a fonte de variável, desde que política por campo/finalidade a autorize. Um nome de coluna existente não concede automaticamente divulgação de CPF, dados bancários, segredo, IDs técnicos nem metadados sensíveis.
- Ao enviar, o backend lê os **dados da mesma concessionária** e resolve `{{n}}` com tipos, fontes e validações autorizadas. Não confiar em parâmetros de IA ou campos SQL arbitrários; não inventar valores ausentes. Falta de dado seguro bloqueia envio e gera evidência de motivo.
- Slots de BODY, HEADER e URL dinâmica de botão também obedecem ao vínculo imutável da versão e verificação de links/domínios seguros. É permitido evoluir **versão seguinte** por fluxo autorizado, nunca reescrever os envios anteriores.

## 9. Planejamento e substituição de templates [D]

Se Meta **pausar, rejeitar, desabilitar ou invalidar** template de um fluxo, a plataforma:
1. Retira aquele template dos candidatos e impede novos disparos com ele.
2. Registra evento com loja/WABA, identificadores/versionamento, motivo/código Meta disponível e cadências afetadas.
3. Aciona a **IA Planejadora**, fornecendo contexto mínimo do problema, posição do template e **apenas alternativas previamente aprovadas, permitidas e pertinentes**.
4. Permite à Planejadora retirar/substituir, reordenar, mudar quantidade ou horários segundo seus gates; persiste um plano revisado e cancela tentativas obsoletas de forma auditável.
5. Se não houver alternativa, encurta/remove aquela etapa ou informa a ausência de opção; **não solicita criação emergencial** a uma IA administrativa nem espera template novo.

Uma **falha cotidiana de envio de mensagem** não é indisponibilidade de template. Não aciona a Planejadora e não abre um ciclo de autoria MCP.

## 10. Duas falhas CONSECUTIVAS de envio [D/H]

O contador é **por cadência/fluxo do lead**, não pelo tempo cronológico entre os agendamentos. Só uma **falha definitiva, comprovada e correlacionada a tentativa distinta** incrementa a contagem.

| Sequência de resultados comprovados | Contador após cada etapa | Efeito |
|---|---|---|
| FAIL, SENT | 1, 0 | Seguir; silêncio do cliente não muda o reset |
| FAIL, SENT, FAIL | 1, 0, 1 | A última falha é primeira de nova sequência |
| FAIL, FAIL | 1, 2 | Cancelar todos envios restantes e registrar `perdido` técnico |
| SENT, FAIL, FAIL | 0, 1, 2 | Encerrar após segundo erro seguido |
| FAIL, INCERTO | 1, CONCILIAÇÃO | Não presumir sent nem falha |

**SENT** exige evidência técnica confiável e correlacionada, e **NÃO exige resposta do cliente**; chegada de confirmação posterior deve ser conciliada idempotentemente. `API_ACCEPTED`, reserva, timeout, ausência de callback e COMMIT incerto não bastam para resetar nem incrementar o contador; não reenviar às cegas.

Na segunda falha consecutiva qualificada, o backend cancela todo o restante do plano e marca o ciclo/lead `perdido` com **motivo técnico**, não por recusa expressa. Eventual recontato posterior depende de nova iniciativa/importação autorizada por Diretor ou outro ator expressamente competente, com revalidação de elegibilidade.

Se o envio comprovado do template FINAL ocorreu, a regra C09 de silêncio pós-envio de **24h** pertence a outro fluxo; agendamento/aceite/incerteza **não inicia** ficticiamente esse relógio. Handoff humano bloqueia cadências incompatíveis.

## 11. Opt-out por concessionária; consentimento independente [D/H/V]

- Pedido claro à **loja A** de parar mensagens proativas **bloqueia A**, inclusive considerando mudança futura de canal da própria A; **não marca opt-out da B**, que é um domínio comercial distinto.
- Loja B **não herda opt-in de A**, devendo ter sua própria autorização válida. O processamento de consentimento e retenção [V] depende de análise Meta/LGPD.
- A IA pode interpretar contexto de botões/respostas para tratamento comercial, mas **opt-out inequívoco validado exige bloqueio na plataforma**; não se pode ignorá-lo porque a IA preferiu continuar. Opt-out não equivale automaticamente ao status comercial `perdido`.
- **Há protótipo sintético S0-016:** `supressoes_contato_sinteticas` registra loja+lead+canal+finalidade, evento de origem e instante, cancela envios pendentes do escopo. S0-018 impede que inbound espontâneo implique reopt-in; função sintética não autoriza Meta real. Não criar outra estrutura concorrente sem auditar S0.
- A abrangência legal exata entre **finalidades de comunicação** e canal ainda exige política executável [P/V]; o objetivo aprovado de produto é não propagar A para B.

## 12. Consultores, Gestores, botões e atendimento humano [D/H]

- Botões são componentes da mensagem; a IA de atendimento interpreta o resultado no contexto. Um clique em “Não tenho interesse” não marca automaticamente `perdido`; pode suscitar clarificação, encaminhamento humano ou desfecho de acordo com regras.
- Um pedido de “Parar mensagens” válido é exceção: supressão automática de proatividade da loja sem depender de conclusão comercial da IA.
- Consultor autenticado e atribuído ao caso pode solicitar envio de template **individualmente** dentro de suas concessões/caso/loja e janela Meta, sem ganhar privilégio de gerenciar todo catálogo. Handoff ao humano interrompe automação de IA para aquele caso e roteia inbound subsequente ao responsável humano conforme contrato S0.
- O envio de template **não abre** a janela de mensagem livre de 24h; somente inbound do cliente pode alterar a janela prevista.

### 12A. Identificação visível do Consultor, Gestor ou Diretor no WhatsApp [D/P/V]

> **ATUALIZAÇÃO WA-21 — FORMATOS DECIDIDOS:** não usar “Mariana — Atendimento” e não classificar mais o formato de assinatura como indefinido. Em **cada mensagem textual livre enviada por humano**, a plataforma acrescentará automaticamente cargo e nome reais antes do conteúdo: `Consultor Fulano:\nMensagem`, `Gestor Ciclano:\nMensagem` ou `Diretor Beltrano:\nMensagem`. A nomenclatura substitui antigo operador por **consultor**, antigo responsável-cargo por **diretor** e preserva gestor. A autoria é autenticada pelo S0, e o prefixo é texto do `text.body`, não identidade Meta nativa. **Para templates** só conteúdo ou slots aprovados pela Meta; não concatenar prefixos arbitrários. Identificadores físicos/status anteriores só mudam após revisão de compatibilidade. [WA-21](./wa21-papeis-diretor-gestor-consultor-assinatura-2026-10-21.md).



A decisão de produto determina que cada mensagem textual livre **enviada por Consultor, Gestor ou Diretor** terá automaticamente seu **cargo e nome** antes do conteúdo no WhatsApp do cliente, de forma automática. Na Cloud API Meta, o envio sai do `Phone-Number-ID` da concessionária e o corpo está em `text.body`; **não foi identificado atributo oficial que renderize o agente humano como remetente visual separado da mensagem**. A identificação em uma plataforma de atendimento pode ser apenas visual na UI própria, ou parte literal do texto enviado ao WhatsApp quando o backend acrescentar uma assinatura de texto.

**Contrato de autoria:** obter conta/autorização/atribuição de caso a partir do S0, não do nome escrito por IA ou cliente. Conservar `actor_tipo`/referência ao autor humano real e snapshots de cargo/nome no histórico e registrar o texto **exato** efetivamente enviado. Prévia deve corresponder ao resultado, respeitando janela WhatsApp, escopo da loja, idempotência e limite de mensagem. **Não atribuir nome humano a mensagens da IA.**

**Templates aprovados:** o nome do autor só pode ser inserido por **slot/variável aprovado** ou conteúdo previamente aprovado; não anexar prefixo livre ao payload de um template e não usar mensagem livre fora de janela. A plataforma preenche qualquer variável autorizada. O cargo/nome/dois-pontos para texto livre HUMANO já foram decididos; somente exceções para mídias/legendas e apresentação de IA ainda estão pendentes. **A funcionalidade ainda não foi implementada.** Referência: [WA-20](./wa20-identificacao-visivel-atendente-assinatura-mensagem-2026-10-21.md).

## 13. Administração MCP e auditoria de autoria [D/H/P]

> **Nomenclatura atual:** o antigo papel superior denominado responsável é agora **Diretor**, e o antigo operador é **Consultor**. Na administração por MCP, aplicar a matriz de acesso por perfil sem conceder poderes novos automaticamente; preservar a segunda confirmação e a identidade individual. Ver [WA-21](./wa21-papeis-diretor-gestor-consultor-assinatura-2026-10-21.md).


- Cada **Diretor autorizado** possui autenticação e vínculo individual, sem conta compartilhada como prova de autoria. O Diretor pode instruir sua IA administrativa conectada ao MCP: ler dados autorizados, preparar rascunhos, texto, mídia, finalidades, editar/excluir/desativar o que sua matriz expressamente permite e solicitar submissão à Meta.
- **Consultas** exigem autenticação/autorização; **TODA escrita ou exclusão** exige prévia da operação EXATA, **segunda confirmação do MESMO Diretor autenticado**, revalidação de escopo/versão, execução limitada e auditoria administrativa imutável. Nem a IA nem o MCP podem conceder a si próprios autoridade, alterar estrutura SQL/DDL, provas bancárias ou registros de auditoria.
- **A frente MCP** implementará protocolo/servidor/tools executáveis e identidade delegada; **a frente Meta** documentará e implementará posteriormente apenas os contratos e serviços internos de domínio. O arquivo de 12 ferramentas WA-17B é **especificação, NÃO servidor instalado**.
- Documento histórico 41 D41-03 limitava inicialmente as escritas MCP a importações/remanejamentos. A intenção nova **revoga esse teto funcional restrito** para operações administrativas de templates, mas não cria por si uma ACL executável pronta nem libera ações bancárias/estruturais; emenda granular global ainda pendente.

## 14. Segurança de integração e fronteiras de execução [H/T]

- Conferir escopo App/WABA/número/loja, HMAC do webhook, idempotência, correlação de mensagem e tentativa, resposta a duplicação/replay, autenticidade de status Meta e provas internas S0.
- ACK do webhook só após ingresso durável do lote relevante; COMMIT cujo resultado é incerto deve ser recuperado em sessão confiável, sem recriar envio externo.
- Credenciais e tokens não saem para IA, frontend ou outra loja. Serviços reais Graph/Supabase estão fora da autorização de execução desta fase; não apresentar simuladores como adaptadores homologados.
- IA e adaptador não movimentam status `vendido` nem fazem remessa à instituição financeira por dedução de conversa.

## 15. Mídias, dados pessoais, preços e eficácia [D/V/P]

- IA pode orientar cliente sobre dados necessários após transparência/aceite válido; **recebimento espontâneo** de documento/imagem não autoriza automaticamente OCR, armazenamento integral, solicitação de identificadores completos, compartilhamento com banco ou exposição à IA. Política Meta/LGPD/Banco [V] será analisada antes de produção.
- Desejado: painel de **saúde de templates**, monitoramento de pausas/rejeições/qualidade e eficácia por versão, componente e finalidade. Métricas de `sent`, `delivered`, `read`, resposta e venda têm denominadores e evidências separados; correlação temporal não é prova de causalidade.
- Não implementar **limite/bloqueio automático por gasto**; análise financeira fica para a Prumo. Caso haja informação tarifária oficial nos eventos/relatórios, registrar metadados autorizados sem inferir preço exato de cada POST. MARKETING e UTILITY não devem receber gratuidade presumida.

## 16. Matriz daquilo que está definido versus aquilo que está pronto [D/T]

| Parte | Decidido em produto | Estado de implementação comprovado |
|---|---|---|
| Estruturas lógicas de mensagens/envios/catálogo | Sim, pacote 09 | SQL produtivo completo ainda não homologado |
| Opt-out por loja e respeito a supressão | Sim | Implementação **sintética** S0-016/018, escopo técnico mais estreito |
| Planner só entre templates aprovados por finalidade | Sim | Filtragem de finalidades **ainda não implementada** |
| MCP individual e administração de templates | Sim como intenção/regras | Só **contratos de ferramentas**, MCP real com outra frente |
| Meta revisão/edição/mídias e versões | Sim condicionado à Meta | WA-17A/B **offline**, Graph real ausente |
| Variáveis por campo permitido congeladas por versão | Sim | Contrato inicial WA-17 permite remapeamento após APPROVED: requer reparo técnico |
| Duas falhas consecutivas e reset por sent | Sim | S0-C07 diagnóstico; regra comercial/contador ainda NÃO homologados |
| Testes WA-16/17 | Cenários definidos | 44 testes Node escritos, 42 verificações V8 independentes; execução Node atual/PG17 WA16 **não confirmada** |

## 16A. Contratos interfrentes confirmados na revisão de 22/10 [D/R/T]

A [WA-22 — revisão cruzada das outras frentes](./wa22-revisao-cruzada-outras-frentes-contratos-2026-10-22.md) é o registro de origem/precedência. Ao especificar esta integração, observar:

1. **Prova de humano:** consultor/gestor/diretor escrever ou clicar enviar não confirma contato. Receber evidência `human_message_sent` autenticada/correlacionada ao caso e ao autor; assinatura textual `Consultor Nome:` NÃO substitui a prova técnica. Chamadas atendidas via Meta permanecem [V].
2. **Pausa de novos leads:** `intake_paused` NÃO deve bloquear resposta do profissional em caso que conserva; S0/S1 decide titularidade, concessão e fila. F01 não deve ter acesso à equipe/escala/disponibilidade.
3. **F03 pós-humana:** somente comando explícito de conclusão humana pela S0 aciona F03, **não** expiração de 24h Meta. O transporte Meta fornece eventos/mensagens necessários a histórico temporal, mas não gera o ato de fechamento.
4. **Histórico e mídias:** disponibilizar IDs, timestamp, autores, eventos e referências a mídias legalmente retidas do cliente **na mesma concessionária ao longo de conversas e ciclos**, sob `cutoff` imutável, sem misturar mensagem futura. Acesso multimodal e retenção precisam de política Meta/LGPD/Banco; não inventar guarda eterna.
5. **Três marcos:** janela de livre resposta Meta a partir do último inbound, conclusão expressa do Consultor e janela C09 24h após `sent` do template final em caso elegível são relógios/atos independentes. Template individual versus cadeia F02 e C09 pós-humano ainda têm matriz [R].
6. **Indicador de leitura da UI:** `COUNT/DOT/NONE` para inbound não lido/lido sem resposta/respondido pertence à **atribuição humana no S0/S1**; leitura supervisora de Gestor não marca leitura do Consultor. `read` callback da Meta indica outra coisa (leitura pelo destinatário), não equivale ao painel.
7. **Dados cadastrais e motivos:** OpenAI AL-IA-01 de 22/10 registra que o Consultor **não edita ficha manualmente** e que a F03 pode propor perda por desistência após conclusão humana, sob guardas S0, **nunca venda**. Isso altera ou conflita com D41-04 quanto a correções humanas; coordenação deve resolver antes de qualquer UI/payload de edição. Nossa frente não decide status comercial.
8. **Elegibilidade promocional:** catálogos de conhecimentos/condições comerciais controlados por concessionária podem servir de fontes, mas **a fonte autorizada da oferta** precisa ser definida. O pacote 17/10 não previa banco central de campanhas/marketing na S0; não criar tabela só por existir finalidade CAMPANHA nos templates.
9. **MCP Diretor:** exige autenticação/delegação, prévia e segunda confirmação para mutações, e a **base de auditoria protegida do próprio MCP não pode ser editada/excluída por suas ferramentas**. Servidor e seus controles são de outra frente; registrar somente operações de domínio WhatsApp autorizadas.

**Status:** são contratos/decisões documentais; PRs #1/#3/#5/#7/#8/#12 e frontend continuam independentes. Este guia NÃO significa implementação real dessas mudanças nem validação de Meta/Banco/LGPD. Casos pendentes e links exatos na WA-22.

## 17. Como proceder se houver conflito ou nova decisão

1. Consultar [00 — matriz WDC](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md) para ID, origem e precedência.
2. Aplicar a regra vigente desta especificação **somente ao tema que a nova decisão modificou**.
3. Ler [02 — conflito por documento/trecho](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md), sem tratar fontes de 17/10 como se tivessem sido apagadas.
4. Se faltar decisão: classificar **P ou V** e deixar explícito; não inferir comportamento, permissão, legislação ou alteração de banco.
5. Se a implementação divergir: abrir defeito para auditoria TÉCNICA, não alterar a decisão silenciosamente.
6. Nova decisão exige data, autor, ID, texto revogado, regra atual e efeito sobre contrato/teste. A edição deste guia não substitui aprovação do responsável nem parecer Meta/LGPD/Banco.

**Fontes históricas principais:** pacote 17/10 documentos 04, 06, 09, 10, 11, 13/13A, 25, 26, 28–31, 33–37, 40–41; revisão WA-07/17/18A–C; issue #11. **Sem merge, deploy, Graph real, MCP real ou alteração SQL como consequência desta consolidação.**
