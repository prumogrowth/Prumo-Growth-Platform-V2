# WA-17 — Gestão manual de templates e configuração posterior das variáveis

> **Errata da diretriz (20/10/2026):** este relatório WA-17A registrou o recorte inicial de criação manual. A decisão mais recente do responsável o **substitui** como arquitetura-alvo: a criação e administração ocorrerão **principalmente via MCP** conectado a uma IA, que poderá copiar o texto fornecido **ou gerar novos textos a pedido**; a estrutura deverá suportar HEADER multimídia, FOOTER e botões URL, QUICK_REPLY, PHONE_NUMBER e capacidades avançadas por módulos. A implementação WA-17A segue apenas como biblioteca legada BODY-only. [Nova especificação WA-17B](./wa17b-mcp-templates-multimidia-ia-delegada-2026-10-20.md). Sem chamada Meta real.

**Data:** 20/10/2026. **PR #2:** Draft, sem merge/deploy/API Graph real.

## 1. Origem e decisão de produto

**A documentação vigente já exigia** a estrutura relacional lógica `catalogo_templates`, separada de `envios_template` e `mensagens` (fonte do projeto: `documentos/09_Estrutura_Mensagens_Templates_v4_6.md`). O documento consolidado prevê uma biblioteca inicialmente manual, solicitação de criação pela API e consulta à situação de aprovação na Meta (`projeto_liberacred_consolidacao_ideias_v0_2_auditada.md`, seção 9.2).

**Esclarecimento solicitado pelo responsável em 20/10/2026:** os responsáveis autorizados devem poder **inserir eles mesmos o conteúdo** de novos templates na plataforma, solicitar a submissão à Meta por meio da plataforma e **editar depois o mapeamento das variáveis**, como nome do cliente, nome do operador e novas fontes reconhecidas pelo sistema. **A plataforma não precisa gerar textos de templates.** A IA não ganha autorização para escrever ou publicar modelos autonomamente por causa desta funcionalidade.

### Duas configurações que não podem ser confundidas

1. **Texto/estrutura submetida à Meta:** nome, idioma, categoria, componentes e posições `{{1}}`, `{{2}}`; exemplos fictícios fornecidos para avaliação. Alteração do texto exige **nova versão de conteúdo e revisão pela Meta**, sem sobrescrever versões antigas associadas a envios.
2. **Fonte interna de cada posição:** mapeamento `{{1}} -> cliente.nome`, `{{2}} -> operador.nome` ou `caso.codigo`. Essa configuração é **da Prumo**, revisável com controle de versão, sem mudar o texto posicional submetido. Mudanças semânticas relevantes continuam sujeitas à política administrativa/comercial interna. Não presumir que trocar fontes mude aprovação Meta: conteúdo permanece idêntico.

Exemplo fictício, fornecido somente para ilustrar a interface (não é um template criado nem enviado):
- Texto manual: `Olá {{1}}, quem acompanha seu atendimento é {{2}}.`
- Mapa inicial: `1=cliente.nome`, `2=operador.nome`.
- Mapa alternativo: `1=cliente.nome`, `2=caso.codigo`, somente se permitido e compatível com o propósito do template aprovado.
- Valores reais são resolvidos **na hora do uso pelo backend autorizado**, sem armazená-los no texto-base e sem enviar amostras de dados pessoais ao pedido de aprovação.

## 2. Tela/painel a implementar — interface administrativa, não chat livre

**Caminho proposto:** Administração → WhatsApp/Meta → Templates.

**Visão de lista:** concessionária autorizada, conta Meta associada (WABA e/ou conta de mensagens conforme modelo vigente), nome, idioma, categoria, versão de conteúdo, estado recebido da Meta, revisão do mapeamento, datas e autor. Filtrar por estado; não mostrar modelos de outra concessionária.

**Ação “Novo template” — formulário:**
- Loja/concessionária (derivada das permissões do ator, não de ID livre), conta Meta autorizada, nome técnico do template, idioma, categoria;
- editor manual do conteúdo (`BODY` inicial; futuramente `HEADER`, `FOOTER`, botões, mídia, localização e outras categorias sob contrato específico);
- detecção e listagem automática das posições `{{1}}`, `{{2}}`, ...; exigência de exemplos fictícios por posição, sem CPF, telefone real, dados de crédito ou dados sensíveis;
- prévia de revisão; botões “Salvar rascunho”, “Solicitar aprovação” e acesso ao resultado, sujeitos a permissões e confirmação administrativa quando exigida.

**Ação “Variáveis” — seção independente e posterior:**
- Cada posição imutável do texto é exibida com seletor de **fonte autorizada por registro interno de fontes**, por exemplo `cliente.nome`, `operador.nome`, `concessionaria.nome`, `caso.codigo`;
- novos campos podem ser **cadastrados no registro seguro de fontes** após revisão do backend; não há expressão executável, código arbitrário, SQL livre ou acesso irrestrito ao banco;
- guardar `mapping_revision`, ator autenticado, justificativa e histórico de antes/depois; bloquear salvamento com revisão obsoleta;
- prévia com dados fictícios; se o valor necessário estiver vazio no envio real, **bloquear** o envio em vez de enviar `{{1}}` ou texto improvisado.

**Ação “Estado da Meta”:** mostrar claramente `IN_REVIEW/PENDING`, `APPROVED`, `REJECTED`, `PAUSED`, `DISABLED` e motivo quando retornado, além de última sincronização. **Aprovação deve vir de uma resposta autenticada da Meta**, não do usuário clicar em “Aprovar” nem de um HTTP 2xx de cadastro.

**Edição de conteúdo aprovado:** “Criar nova versão” cria novo rascunho com `local_id` e nome distinto para revisão; mantém a versão antiga e seus envios. O texto original não é sobrescrito. A substituição/edição direta na Meta, se posteriormente desejada, exige validação das regras atuais antes de implementar.

## 3. Fluxo e governança

1. Responsável autenticado abre o formulário e escreve o template manualmente.
2. Salva rascunho; a aplicação valida nome, idioma, categoria, tamanho, posições e exemplos.
3. Solicita submissão. O backend revalida permissão na conta de mensagens do escopo e realiza chamada de gerenciamento de templates na Meta, **apenas depois de autorizada e implementada essa conexão**.
4. A plataforma grava ID Meta, versão e evidência da solicitação, marcando **EM REVISÃO**, nunca APROVADO por suposição.
5. Serviço autenticado consulta/recebe status da Meta; mudanças `APPROVED/REJECTED/PAUSED/DISABLED` invalidam elegibilidade imediatamente onde necessário.
6. Responsável configura ou altera fontes de `{{n}}`, sem reescrever conteúdo.
7. O motor de envio só pode montar parâmetros de template **aprovado**, com variáveis resolvidas e outros gates: consentimento, opt-out, janela, canal, titularidade, autorização de negócio, idempotência e limites Meta. A aprovação **não autoriza automaticamente um disparo**.
8. Auditoria de operação de autoria/alteração, inclusive tentativas e rejeições, separada da trilha de envio; versões e snapshots preservados por `envios_template`.

**Autorização:** apenas responsável/administrador com escopo pode criar/submeter/mudar mapeamentos; operadores podem ser fontes de variáveis e visualizar o que seu perfil permitir, mas não ganham poder de aprovar na Meta. A conta do ator deve ser verificada; quando via ChatGPT/MCP, seguir identidade individual, segunda confirmação e auditoria imutável descritas em `documentos/10_Identidade_e_Auditoria_Administrativa_v4_1.md`. O módulo TypeScript puro não substitui essa camada.

## 4. Implementado agora (WA-17A)

**Arquivo:** `integrations/whatsapp-meta/template-catalog-control.ts`.

Funções puras, sem HTTP ou escrita em banco:
- `createManualTemplate` valida rascunho com texto humano, exemplos e posições contíguas.
- `prepareMetaReviewPayload` prepara corpo para gerenciamento Meta, **sem executar chamada Graph**.
- `recordReviewSubmission` guarda no objeto imutável o ID confirmado pelo adaptador externo, mantendo `IN_REVIEW`.
- `applyVerifiedMetaStatus` modela a atualização recebida por sincronização **que ainda precisará autenticar a origem**.
- `configureVariableSources` altera somente o mapa posicional contra um registro de fontes fornecido pelo backend, com `mapping_revision`.
- `createEditedContentVersion` separa conteúdo novo em outro rascunho, sem adulterar a versão aprovada.
- `prepareApprovedTemplateParameters` forma apenas os parâmetros dinâmicos, **send_authorized:false** e **network_performed:false**.

**Testes escritos:** `integrations/whatsapp-meta/template-catalog-control.test.ts`, casos WA17-01..18. Cobrem estados, ciclo de revisão, versões imutáveis, mapeamento flexível, consentimento não presumido, erros em fontes/valores, revisões obsoletas, escopo de concessionária, não autorização de envio e rejeição de metadados inesperados, tokens e getters em rascunhos.

**Limite v0:** suporta apenas templates de texto `BODY` com variáveis posicionais e categorias `MARKETING`/`UTILITY`. Esse é um **recorte de implementação**, não afirmação de que a Meta só aceita essas formas. `AUTHENTICATION` tem regras próprias; mídia, cabeçalhos, rodapés, botões, outros parâmetros e formatos nomeados precisam de contratos próprios. A versão exata da Graph API e a identidade da conta proprietária dos templates exigem verificação no onboarding, inclusive à luz da evolução das contas Meta em 2026.

## 5. Pendências explícitas

**Ainda não implementados:** tela efetiva do painel, persistência relacional física de `catalogo_templates` e do mapa de variáveis, registro de fontes autorizado por concessionária, identidade/autorização/confirmacão administrativa, adaptador Graph autenticado para POST/GET de templates, armazenamento de recibo de revisão e sincronização da Meta, auditoria de alterações, integração de envio e políticas operacionais. **Nenhum template foi submetido à Meta nesta etapa.**

**CI da WA-17:** há 18 testes definidos, mas um resultado GitHub Actions para esses testes só poderá ser declarado após consultar os logs do commit correspondente. Os gates anteriores WA15C, WA06D e Meta 479/479 NÃO comprovam esta funcionalidade.

## Referências externas verificadas

- Meta/WhatsApp Business — guia de gerenciamento de templates: https://whatsappbusiness.com/pt-br/blog/manage-message-templates-whatsapp-business-api/
- Meta Postman oficial — criar template: https://www.postman.com/meta/whatsapp-business-platform/request/uzphwqw/create-template-w-text-header-text-body-text-footer-and-2-quick-reply-buttons
- Meta Postman oficial — listar templates: https://www.postman.com/meta/whatsapp-business-platform/request/qtgr0i7/get-all-templates-default-fields
- Meta Postman oficial — editar: https://www.postman.com/meta/whatsapp-business-platform/request/bpcsm6i/edit-template
- WhatsApp Business Messaging Policy: https://business.whatsapp.com/policy/preview?lang=pt_BR
