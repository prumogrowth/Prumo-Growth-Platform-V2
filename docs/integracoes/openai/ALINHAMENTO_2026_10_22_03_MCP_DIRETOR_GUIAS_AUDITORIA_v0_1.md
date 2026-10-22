# AL-IA-03 — MCP do Diretor, guias operacionais semânticos e proteção da própria auditoria

**Data:** 22/10/2026 | **Estado:** [DN] requisitos funcionais expressos recentemente, com interfaces/permissões físicas [P/R] e limites externos [V]. **Não** é implementação MCP nem alteração na frente S0.

## 1. Fronteira fundamental — administrar dados não é editar a plataforma

**[DN]** O **Diretor da Prumo** opera a plataforma por IA/ChatGPT conectado ao MCP, com ampla capacidade de lidar com **dados operacionais introduzidos/produzidos depois de a plataforma estar funcionando**. A intenção do responsável é que o Diretor possa **consultar, criar, modificar, exportar, baixar, importar, transferir e excluir esses dados**, inclusive em massa e até eliminar operacionalmente o conjunto de dados de determinada concessionária, **sujeito às confirmações**.

**[DN]** O MCP operacional **não** pode:
- Editar código-fonte, implantar software, alterar esquema/tabelas ou estrutura técnica.
- Mudar **regras estruturais**, fluxos obrigatórios, segurança, permissões base, guardas S0 ou lógica de autorização.
- Contornar salvaguardas, provas exigidas, LGPD, obrigações de retenção ou autorização externa por linguagem natural.
- Reescrever os **registros protegidos do próprio MCP** (seção 3).

**[DN]** Instruções globais F01/F02/F03, comportamento F01, conhecimentos e habilidades configuráveis são **configurações/dados administráveis quando a plataforma expuser recursos autorizados**. Essa possibilidade **não** significa poder alterar as regras fundamentais do software pela mesma via.

O usuário foi explícito: o MCP pode administrar a operação “depois de pronta”, mas **não construir/editar a própria plataforma**. O contrato anterior D41-03 limitava as escritas iniciais do MCP a importação de leads e remanejamento de casos; essa delimitação foi **superada como intenção de produto por decisão posterior [DN]** e exige revisão controlada pela frente responsável. Este arquivo NÃO concede automaticamente privilégios SQL que hoje não existem.

## 2. Fluxo de confirmação humana por operação

**[DN]** A IA conectada ao MCP **não executa uma mutação somente porque o Diretor escreveu “faça X”**. Para escrita, edição, exportação sensível ou exclusão (especificação de escopo técnico pendente [R]), o fluxo de desenho deve ser:

1. Autenticar **ator humano real** e conferir escopo/permissão para o recurso.
2. Interpretar a solicitação e **preparar prévia** clara: operação, concessionária(s), tipo de dado, alvos, escala, consequências e limites; alertar explicitamente irreversibilidade quando relevante.
3. Solicitar **segunda confirmação expressa** da mesma pessoa para a **operação específica**. Essa confirmação pode ocorrer na experiência conectada ao MCP, mas o backend deve vincular sua autenticidade/identidade ao ato, com prazo/versão/nonce ou mecanismo equivalente; texto interpretado isoladamente pelo modelo não é garantia suficiente.
4. Só após confirmação e **revalidação atômica** de permissões, versão e alvos, S0 executa o permitido, registra resultado por operação e evita duplicação/replay.
5. Responder sucesso **somente conforme resultado confirmado pela S0**, nunca antes.

**[DA/DN]** Consultas de leitura normais não exigem “segunda confirmação” genérica. Operações em massa devem explicitar seu raio de impacto. Uma confirmação de uma operação não autoriza outras. **Confirmação NÃO permite o que o MCP é estruturalmente incapaz de fazer**.

**Exemplo [DN]:** o Diretor pede excluir uma concessionária e todos os seus registros operacionais. O MCP não deleta imediatamente; prepara prévia exata e solicitação de confirmação, realiza somente exclusões permitidas após confirmação, mantém evidência no histórico protegido de operações. A política de retenção legal, backups e exclusões irreversíveis continua [R/V]; não prometer erradicação física de dados cuja retenção seja obrigatória.

## 3. Exceção absoluta: a base/registros do próprio MCP

**[DN]** O Diretor poderá **consultar/ver** registros de auditoria do MCP, mas o próprio MCP **NÃO poderá criá-los artificialmente, editá-los retroativamente, apagá-los nem reescrevê-los sob comando administrativo**, **mesmo com a confirmação explícita do Diretor**.

- Registros de quem solicitou, o que foi preparado/confirmado, quando, quais alvos foram atingidos, resultados, falhas, versões e justificativas devem nascer do mecanismo de auditoria da plataforma, **por acréscimo de eventos reais**.
- O bloqueio abrange **qualquer tipo de registro que no futuro seja classificado como parte da área/base protegida do MCP**, não apenas o histórico de edição.
- A plataforma poderá gravar **novos eventos legítimos** nessa área. Isso é diferente de autorizar um comando MCP a alterar eventos anteriores ou fabricar operações.
- Uma ordem de exclusão total de dados operacionais de determinada concessionária **não inclui** apagar a trilha protegida daquelas operações através do MCP.
- Proteção deve ser exercida em banco/credenciais/serviço, não apenas na mensagem “não faça isso” para o modelo.
- Retenção e eliminação estritamente legal/técnica sob processo independente, se cabíveis, **não constituem permissão de manipulação pelo MCP do Diretor** e ainda precisam de política própria [R/V].

Isso altera a formulação inicial ampla “tudo que entrar pode ser deletado”: **a exceção expressa posterior é a área protegida do próprio MCP**. Registrar essa ordem de precedência.

## 4. Camada semântica de guias operacionais — distinta das IAs da plataforma

**[DN]** O responsável quer uma **camada semântica do MCP** que ajude o ChatGPT/agente externo conectado a entender **como executar corretamente tarefas administrativas**, semelhante conceitualmente a “skills” do ChatGPT, mas **interna ao ecossistema LiberaCred**. Nome de trabalho [P]: **guias operacionais do MCP**.

Um guia poderá explicar:
- Qual é o resultado pretendido (“criar base semântica de campanha na concessionária X”).
- Etapas e cuidados para planejar e redigir um **bom contexto da base**, gatilho semântico, fato canônico, metadados, vigências, versões e fontes.
- Que campos são obrigatórios/opcionais e como conferir consistência sem criar informações inventadas.
- Quais ferramentas **já disponíveis** podem ser chamadas, qual prévia/confirmação gerar e como interpretar resultado.
- Quando registrar proposta para revisão humana/técnica em vez de executar.

**[DN]** Guias do MCP **não são** os quatro campos globais de instruções/comportamento das IAs F01/F02/F03; esses campos destinam-se somente às IAs **operacionais dentro da plataforma**. A IA que conversa com o Diretor está fora desse conjunto.

**[P]** Separar catálogo de guias (textos/procedimentos autorizados), catálogo de ferramentas MCP (operações executáveis) e validador S0 (autoridade). Texto de guia nunca cria endpoint, permissão SQL ou alteração em código.

## 5. MCP e habilidades das IAs operacionais

**[DN]** Diretor poderá, por MCP, cadastrar/gerenciar **habilidades configuráveis** com conhecimento vinculado para F01/F02/F03, desde que associadas a uma operação **já implementada e autorizada**. A capacidade deve ter descrição semântica e instrução funcional para o agente saber identificá-la e utilizá-la. F01/F02/F03 não cadastram suas próprias habilidades.

**[DN]** Uma nova capacidade que exija **escrever integração externa nova**, elevar privilégios, instalar código ou modificar a plataforma poderá ser **planejada/especificada** com auxílio do MCP, mas **não implementada/ativada** por esse MCP operacional. Desenvolvedores e frentes responsáveis tratam a mudança de software por processo distinto.

**[P]** A criação/edição de uma habilidade configurável deve usar prévia, escopo, ferramenta preexistente, modelos elegíveis, condições, conhecimento associado, riscos, versão e confirmação. Nenhum texto de conhecimento ou habilidade substitui proibições S0. Regras do Banco/Meta não são inventadas pelo Diretor ou pela IA administrativa.

## 6. Governança transversal

- **[DN]** Cadastro das bases institucionais e de concessionária é exclusivamente da **Prumo**, inclusive por Diretor com MCP; concessionária fornece informações para avaliação mas não edita seu conteúdo diretamente.
- **[DN/DA]** Consultor humano não edita ficha cadastral. Diretor por MCP atua em trilha administrativa separada, sujeita a confirmação e proteção de auditoria. Não usar isso para tornar a correção manual humana fluxo rotineiro de contingência F03.
- **[DA]** Gestão da equipe/fila, leitura de conversas por Gestor e restrições de dados brutos D3/D4 continuam submetidas às suas autorizações de domínio, sem novo superusuário de IA na operação de cliente.
- **[DN/DA]** Escopos das concessionárias permanecem isolados em qualquer consulta/relatório/edição. Diretor pode administrar diferentes lojas quando autorizado, mas isso não permite fundir histórico dos clientes ou expor dados da loja B na interação comercial da A.
- **[R]** Definir identidade/autenticação/expiração do consentimento, tratamento de exportação, capacidade da API MCP específica, separação de logs, limites de volume, retenção, aprovação de conteúdo, prevenção de abuso, controle de versões/reversão e segregação de funções no processo físico.

## 7. Roteiro de cenários para futura aceitação [P]

1. Exclusão em massa sem segunda confirmação: **negada**; confirmação de outro Diretor: **negada**; mesmo ator, confirmação exata e atualizada: executar o permitido uma vez.
2. Pedido “apague todos os logs de auditoria do MCP” mesmo com confirmação válida: **negado** pela própria camada de autorização.
3. Diretoria consulta o histórico do MCP: permitido conforme leitura; nenhuma operação de update/delete de registros antigos é exposta.
4. Comando para criar tabela/coluna/migration ou alterar isolamento entre concessionárias: negado, mesmo com confirmação.
5. Guia semântico propõe base com contexto de campanha, metadados e vigência; a S0 aceita apenas campos/espaço de loja autorizados.
6. Pedido de criar habilidade dependente de API externa **não implementada**: registra-se proposta, nenhuma ferramenta nova é executada.
7. Após alterar comportamento F01 via configuração permitida, S0 continua negando ação fora da regra.
8. Incidente F03 tem trilha de diagnóstico e reparo técnico fora do MCP operacional; não liberar edição de ficha por Consultor como atalho.

**Rastreabilidade:** pacote Drive 17/10 docs 06, 10, 31, 36 e 41; decisões posteriores de Diretoria neste alinhamento; S0 PR #1 (controle de domínio), OpenAI PR #3 (contrato de IA), PRs #8/#12 (ponte F03) em estado Draft. Contradições explicitadas na matriz AL-IA-04.
