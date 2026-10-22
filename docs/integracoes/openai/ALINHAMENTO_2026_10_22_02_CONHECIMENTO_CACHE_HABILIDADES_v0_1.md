# AL-IA-02 — Conhecimento semântico, bases, instruções globais, cache e habilidades

**Data:** 22/10/2026 | **Escopo:** decisões de produto [DN] e propostas de estrutura [P], discutidas com o responsável em 21–22/10. Não é especificação física, API instalada nem decisão final de provedor/embeddings/cache.  
**Etiquetas:** [DN] decisão nova, [DA] regra anterior compatível, [P] proposta não aprovada fisicamente, [R] refinamento interno, [V] dependência externa. Ler com AL-IA-01, AL-IA-03, AL-IA-04 e índice AL-IA-00.

## 1. Objetivo e fontes de autoridade

**[DN]** A LiberaCred precisa oferecer às IAs conhecimento recuperável de modo controlado, econômico e coerente com suas responsabilidades, preservando a segregação integral entre concessionárias. **Não é obrigatório usar prompt caching**, não foi escolhido modelo de embeddings, vector store, banco de dados nem SDK. A escolha futura deve considerar **qualidade, latência, custo, atualização, auditabilidade e isolamento**.

**[DN]** A capacidade da API OpenAI de pesquisar a web foi entendida, mas o responsável **não quer pesquisa aberta na internet como padrão da F01/F02/F03**. Informação para financiar, cadastrar, ofertar ou decidir status deve vir do ambiente controlado, fontes aprovadas e S0. Qualquer pesquisa externa futura depende de função/fonte/finalidade autorizada, não de liberdade genérica do modelo.

**[DN/DA]** O conhecimento recuperado fornece **fatos e contexto**, não permissão de banco, evidência de remessa, autorização para alterar status, acesso a dados de outra loja, nem status de template na Meta. O núcleo S0 determina as autorizações técnicas e regras estruturais.

## 2. Unidade de conhecimento proposta pelo responsável

Duas partes propostas originalmente:

1. **Gatilho semântico [DN — orientação de desenho]:** frase **declarativa** que resume com precisão o escopo do conhecimento, focaliza entidades-chave, não imita a fala do cliente. Serve de índice/pista para recuperação por proximidade vetorial ou mecanismo equivalente.
2. **Fato canônico [DN — orientação de desenho]:** texto factual direto e suficiente para uma intenção, sem saudação nem conversação, incluindo valores exatos, condições, exceções e regras de negócio verificadas.

O responsável aceitou **metadados de controle** como terceira dimensão. Exemplos recomendados **[P]**: identificador/versão, fonte, data de aprovação e vigência, domínio, loja proprietária ou caráter institucional, autorização por IA, idioma, status e vínculos de evidência. Sinônimos, categorias, busca textual + vetorial e múltiplos gatilhos podem ser avaliados [P] para não depender de uma frase única.

**Não confundir:** “fato canônico” é canônico **no universo da fonte comercial aprovada**, mas não suplanta regra normativa S0, informação bancária posterior ou dado atual de um cliente.

## 3. Separação lógica de tipos de informação

As seguintes **camadas lógicas** foram aceitas como orientação de planejamento; **não** exigem cinco bancos físicos:

| Camada | Conteúdo | Autoridade / acesso |
|---|---|---|
| Estrutural | Fluxos técnicos obrigatórios, RLS, políticas de acesso, limites, validação de status, evidências | S0/backend/segurança; **não** recuperável como autorização editável por IA |
| Institucional compartilhável | Informações oficiais LiberaCred/Prumo e temas comuns apropriados | Conteúdo aprovado e versionado pela Prumo; sem transpor dados privados de concessionárias |
| Específica de concessionária | Informações da loja, campanhas, condições aprovadas, anexos e conhecimentos extras | **Isolamento absoluto por concessionária** na busca, exibição e geração |
| Funcional por IA | Instruções/configurações e conhecimentos elegíveis à tarefa F01/F02/F03 | Respeita função da IA; não concede privilégio |
| Histórico e ficha do cliente | Conversa, mídias, autores, carimbos de tempo, cadastro, eventos e provas daquela loja | Fonte transacional/autorizada; **não tratar declarações do cliente como fatos institucionais** |

**[DN]** Um mesmo conhecimento institucional pode ser usado por várias IAs quando relevante, mas **F01, F02 e F03 não precisam consultar o mesmo conjunto**. A F01 se beneficia fortemente de FAQ, produto e informação comercial; F02 precisa principalmente de contexto de recontato, templates e preferências; F03 precisa antes de tudo de histórico real e do catálogo/contrato de campos S0. F03 pode consultar conteúdo semântico adicional quando útil à interpretação, nunca para inventar permissão.

**[DN]** O histórico de cliente é conhecimento contextual para a IA, mas não é a base de conhecimento empresarial e não precisa caber integralmente em prompt fixo. A F03 conserva acesso lógico a todo histórico autorizado da mesma loja até cada corte, e eventual recuperação/resumo deve poder reexaminar a evidência, não mascarar contradições.

## 4. Governança e criação de bases

**[DN] Somente a PRUMO administra e cadastra conteúdo**: global e das concessionárias. Concessionárias **não** criam/editam bases diretamente; podem encaminhar materiais à Prumo para que ela examine e cadastre, se permitido. Diretor da Prumo pode solicitar criação/alteração pelo MCP, dentro do controle previsto no AL-IA-03.

**[DN]** Existirá base/conjunto institucional compartilhável e conteúdo exclusivo de cada concessionária; será possível criar **bases adicionais dentro de uma mesma concessionária** para organização (por exemplo, campanhas ou ações especiais). Cada base extra permanece irremediavelmente vinculada à **concessionária proprietária**: jamais migra ou consulta dados de outra loja pela semelhança de nome ou campanha. A Prumo pode ativar, pausar e futuramente reativar uma base sem apagar seu histórico.

**[DN] Contexto da base:** campo descritivo semântico com a finalidade/escopo da base, potencialmente criado **no nascimento** da base pelo Diretor com orientação do MCP. **NÃO** exigir que esteja escrito no passado, nem que contenha relato de encerramento. Pode, por exemplo, informar “campanha X, iniciada em 01/07, prevista para encerrar em 20/07”. O texto original pode **não ser atualizado** após a pausa. A IA lê contexto + estado efetivo + datas estruturadas, sem presumir que a descrição foi reescrita.

**[DN] Base pausada:** fatos operacionais deixam de ser recuperados como **condições/ofertas vigentes**, mas o **contexto de identificação da base continua consultável**. Isso permite interpretar menções de clientes sobre campanhas passadas. Pausar **não apaga mensagens históricas nem os textos já enviados**. Contexto incompleto é deficiência de cadastro da base; a IA deve reconhecer incerteza, não fabricar validade ou condição.

**[DN] Vigência e pausa automática (nova decisão final):**
- A Prumo poderá configurar **opcionalmente data e hora de encerramento/pausa automática por base**. Não é campo obrigatório. Sem agendamento, a base pode permanecer ativa até operação manual/regras aplicáveis.
- Ao chegar a data/hora configuradas, a plataforma deve considerar a base **não utilizável como oferta ativa**, inclusive se algum job de atualização do rótulo “pausada” atrasar. Programação deve ser persistida e auditável; timezone e tolerâncias são detalhes de especificação [R].
- A data/hora de pausa da **base** não equivale às datas de vigência de cada **conhecimento/campanha**. Uma base ainda ativa pode conter uma condição já vencida. A F01 **deve interpretar datas/condições do conteúdo** e evitar ofertá-la como vigente; caso vigência seja incerta, pedir validação ou responder com cautela. Validade prevista ≠ encerramento confirmado, e não se presume prorrogação.
- Pausa futura pode ser reprogramada/retirada por operação autorizada; reativar não torna automaticamente vigente um conhecimento que já expirou. Critérios de aprovação/revisão de reativação [R].

**[P]** Campos auxiliares: nome, identificador, loja, versão, `contexto_semantico`, `estado`, `vigencia_inicio`, `pausar_em`, fuso, `pausada_em`, autoria, fonte, revisão, IAs autorizadas, referência à base substituta. Estes **não são nomes de coluna aprovados**. A camada semântica/guias internos do MCP devem auxiliar na redação do contexto e preenchimento dos campos, com checagens antes da confirmação.

## 5. Instruções e comportamento — decisão simplificada final

**[DN] NÃO existem instruções nem comportamentos por concessionária.** A hipótese discutida anteriormente de hierarquia “global + local” foi **expressamente retirada** pelo responsável. Diferenciação de lojas se faz pelo **conteúdo das bases** e dados autorizados, não por prompts distintos de missão/estilo da mesma IA.

Existem exatamente **quatro campos conceituais globais e separados**:
1. **Instruções globais F01** — finalidade, papel e orientações operacionais da vendedora.
2. **Comportamento global F01** — como a F01 fala com o cliente no WhatsApp, tom, clareza, tamanho e adaptabilidade.
3. **Instruções globais F02** — função e raciocínio de planejamento/recontatos.
4. **Instruções globais F03** — função e raciocínio de extração/interpretação/desfecho.

**[DN]** F02 e F03 NÃO possuem campo administrativo “comportamento”; elas não conversam diretamente com o cliente. Isso não elimina contrato técnico de saída estruturada, formato de erro, logging ou validação de suas respostas.

**[DN]** Esses quatro campos são **instruções para as IAs operacionais da plataforma**, NÃO instruções para o ChatGPT/agente externo que um Diretor utiliza para falar com o MCP. Os **guias operacionais semânticos do MCP** são outro domínio (AL-IA-03).

**[DN/DA]** A Prumo pode administrar as instruções e comportamento como **dados/configurações autorizados**, mas nenhuma instrução modifica S0, regras estruturais, isolamento, direitos de atores, provas bancárias, fluxos técnicos fixados nem código. Ex.: texto “F03 consulta loja B” não produzirá permissão de consulta. Alterações devem ser versionadas/auditadas e validadas nas próximas execuções [P].

## 6. Prompt caching, contexto e recuperação

**[DN]** Cache da OpenAI é **opcional** e será adotado apenas se eficiente. O responsável perguntou especificamente sobre **múltiplos atendimentos simultâneos da F01**: o compartilhamento de prefixos estáveis de instruções pode gerar acerto de cache entre chamadas, sem compartilhar o contexto privado dos atendimentos. **Cache não é memória do cliente, banco de mensagens, fonte da verdade, autorização de acesso nem garantia de isolamento.**

**[P] Modelo conceitual de montagem de chamada:**
1. S0 identifica IA, concessionária, caso e direitos.
2. Inclui instruções globais estáveis da IA e, apenas F01, comportamento global; a parte invariável pode favorecer cache.
3. Resolve estado atual das bases e vigências; recupera apenas conhecimento aprovado da concessionária/institucional autorizado.
4. Inclui contexto da conversa/ficha e evidências necessárias à tarefa, com cutoff da F03 quando aplicável.
5. Habilita apenas ferramentas/habilidades da IA e do estágio autorizados pela S0.
6. Valida a resposta/operações novamente na S0, fora do modelo.

Atendimentos A e B são separados por IDs, escopo, dados e controle de autorização. O cache de um prefixo geral **não é uma sala de conversa comum** e não coloca automaticamente mensagens de A em B. Se um bloco contém dados específicos de loja/cliente, o sistema não pode intencionalmente reutilizá-lo como conteúdo da outra loja. A decisão de usar `prompt_cache_key`, TTL de cache, limites, preços/modelos e estratégia de armazenamento requer avaliação atualizada [R] e testes, não é tomada aqui.

**[P]** Princípio de invalidação lógica: mudanças de instruções, pausa de base ou vencimento de campanha têm efeito a partir de novas chamadas elegíveis; prompts antigos em cache jamais prevalecem contra as verificações atuais. O sistema deve funcionar corretamente mesmo com cache ausente, expirado ou sem hit.

## 7. Habilidades extensíveis

**[DN]** Manter aberta a expansão futura das capacidades F01/F02/F03 por **habilidades** registradas. Nenhuma das três IAs pode criar ou instalar habilidades por iniciativa própria.

**[DN]** Uma habilidade deve possuir **conhecimento/descrição associado** para que a IA entenda sua finalidade, quando pode ser útil e como invocá-la, em vez de “adivinhar” a ferramenta. Pode incluir descrição semântica, requisitos, entradas/saídas, limites, exemplos e exceções **[P]**.

**[DN]** Diretores poderão administrar/criar **habilidades configuráveis pelo MCP**, quando a plataforma já oferecer as capacidades técnicas autorizadas correspondentes. **Nova integração executável** que dependa de criar código, ampliar permissões estruturais ou instalar infraestrutura não pode ser implantada pelo MCP operacional; pode ser **proposta/especificada** por ele e dependerá de frente técnica e autorização separadas. O responsável confirmou expressamente essa distinção.

**[P]** Catálogo possível: `id_habilidade`, escopo, IA(s) elegíveis, ativo/pausado, descrição semântica, guia/know-how vinculado, versão, ferramenta/ação permitida existente, esquema de argumentos, finalidade, gatilhos, custo/risco e confirmação exigida. Não são colunas aprovadas. Function Calling/MCP podem ser meios técnicos futuros, ainda sem topologia decidida.

## 8. Critérios de segurança e qualidade futuros [P/R]

- Pausar base entre duas mensagens da F01 e comprovar que a próxima resposta não a trata como ativa; manter contexto informativo da campanha.
- Base ainda ativa com oferta datada já vencida: não apresentar como vigente, com validação adicional de datas.
- Contexto em presente que declara término previsto passado: diferenciar fim previsto de fim confirmado; não inventar prorrogação.
- Pausa automática às HH:MM no fuso correto; reabertura/reversão autorizada; job atrasado não reativa elegibilidade.
- Duas concessionárias com bases extras de nomes idênticos sem vazamento no vetor, keyword, logging ou fallback.
- F01 e F02 recebendo instruções globais próprias; somente F01 possui comportamento; nenhuma instrução de loja aplicada.
- Múltiplas F01 simultâneas: cache eventual de prefixo geral sem referências de outra concessionária.
- Habilidade criada administrativamente sem código novo; tentativa de cadastrar ferramenta desconhecida resulta em “proposta pendente”, não execução.
- Recuperação de conteúdo com fonte, versão, permissão, vigência, precisão e tratamento explícito de lacunas.

**Fontes:** alinhamento funcional 21–22/10; consolidado histórico 10/10 seção 8 (histórico não normativo sobre IA Analista); pacote Drive 17/10 docs 06/08B/09/11/41; contratos OAI-05/06/07/08, E01 e mapa de capacidades. Ver matriz AL-IA-04.
