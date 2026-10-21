# WA-20 — Identificação visível do operador nas mensagens WhatsApp

**Data da pesquisa:** 21/10/2026 · **Classe:** [D] desejo funcional do responsável de identificar o atendente para o cliente; [V] verificação de capacidade Meta; [P] contrato/decisões de apresentação para implementação futura; [T] não implementado e não homologado em conta Meta. **Etapa documental somente.** Nenhuma chamada à Graph API real.

> **ATUALIZAÇÃO NORMATIVA WA-21 (21/10/2026) — REGRA DE PRECEDÊNCIA:** o responsável fechou o formato antes deixado aberto. Os cargos agora se chamam **Diretor** (antigo papel “responsável”), **Gestor** (mantido) e **Consultor** (antigo “operador”). Para texto livre de autoria humana, a plataforma deverá acrescentar automaticamente `Consultor Fulano:\nMensagem`, `Gestor Ciclano:\nMensagem` ou `Diretor Beltrano:\nMensagem`, conforme o cargo e autor reais autenticados. **O antigo exemplo “Mariana — Atendimento” e a declaração de que o formato/frequência estavam sem decisão são SUPERADOS.** Para templates Meta continuam valendo apenas conteúdo/slots aprovados. Fonte de decisão: [WA-21](./wa21-papeis-diretor-gestor-consultor-assinatura-2026-10-21.md). A implementação continua pendente.

## 1. Pergunta e resposta técnica

O responsável observou plataformas de atendimento que exibem o **nome do atendente imediatamente antes da mensagem** no WhatsApp do cliente. Deseja incluir essa capacidade na plataforma.

**Resposta baseada na API oficial disponível:** nos exemplos públicos oficiais de **WhatsApp Cloud API → POST /{Phone-Number-ID}/messages**, o emissor é o **número empresarial**, e a mensagem de texto contém `text.body`. **Não foi identificado um campo documentado do envio padrão de texto para escolher um usuário/operador como “remetente visual nativo” de cada balão WhatsApp.** Plataformas multiagente podem:
- **Exibir o operador apenas em SUA interface interna** de atendimento, sobre a mensagem, sem que esse nome exista no WhatsApp do cliente; e/ou
- **Incluir no texto efetivamente enviado** uma linha de identificação/assinatura gerada pelo backend, de modo que o cliente também a veja. O WhatsApp mostra essa linha como texto comum da mensagem, não como identidade Meta independente.

**Exemplo de referência histórica abaixo [SUPERADO PELA WA-21], e NÃO por layout especial da Meta:**

```text
Mariana — Atendimento
Bom dia! Posso ajudar com as informações da sua motocicleta?
```

Este exemplo é histórico. O padrão **já decidido** encontra-se na WA-21: `Consultor Mariana:\nBom dia!...`, com alternativas `Gestor Nome:\n...` e `Diretor Nome:\n...`. O cargo + nome + dois pontos não é mais proposta aberta.

**Referências Meta (pesquisadas em 21/10/2026):**
- Send Text Message, coleção oficial: https://www.postman.com/meta/whatsapp-business-platform/request/8gvd47s/send-text-message
- WhatsApp Cloud API, documentação oficial da coleção: https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api
- Get Business Profile (perfil da empresa, não autoria por agente): https://www.postman.com/meta/whatsapp-business-platform/request/i21qxwn/get-business-profile
- Send Message Template Interactive, payload de template previamente definido/aprovado: https://www.postman.com/meta/whatsapp-business-platform/request/lwtlz1k/send-message-template-interactive

**Limite da evidência:** a ausência de `agent_name` ou similar nesses contratos oficiais de envio **não prova a inexistência eterna de recursos do provedor**; exige reconferir a versão real da Meta antes de uma integração de produção. Não criar parâmetro Graph não documentado.

## 2. Decisão de produto e fronteira da decisão

- [D] **Desejo aprovado para planejamento:** identificar o **operador humano** no WhatsApp do cliente nas mensagens que ele enviar através da plataforma, de forma automática, sem digitar seu nome a cada envio.
- [E] Já estava previsto no pacote 17/10 que a tela O2 da plataforma mostre **mensagens com autores/horários** (`documentos/24_Caderno_Telas_Fluxos_Aceite_Operacional_v0_1.md`) e que `mensagens.remetente_tipo` distinga cliente, IA, humano e sistema (`documentos/09_Estrutura_Mensagens_Templates_v4_6.md`). Isso NÃO fornecia assinatura VISÍVEL ao cliente.
- [P] Realização mais simples: o backend **compõe o texto de saída com uma linha de identificação gerada a partir da conta do operador autenticado**, enquanto a interface interna pode mostrar cabeçalho visual independente.
- [D] **Atualizada pela WA-21:** a plataforma identifica **automaticamente os humanos** com prefixo `Consultor Nome:`, `Gestor Nome:` ou `Diretor Nome:` antes do texto enviado. O padrão documentado para texto livre é a assinatura em cada mensagem humana correspondente; futuras exceções para outros meios precisam de decisão específica. Nome legível derivado do cadastro autenticado.
- [R] Mensagens de IA, sistema e operador como TEMPLATE, mensagens com mídia/legenda e textos de suporte a templates podem merecer políticas distintas. **Não atribuir assinatura humana a mensagem escrita exclusivamente pela IA.**
- [V] Se um aplicativo intermediário/BSP oferecer rótulos proprietários por agente, tratar isso como recurso **da plataforma específica**, não nativo garantido da Meta.

## 3. Contrato recomendado de autoria e identidade [P]

**Duas informações diferentes e obrigatoriamente separadas:**

1. **Autoria real técnica**, confiável e imutável do ponto de vista do histórico: `concessionaria_id`, `canal_id`, `mensagem_id`, `actor_tipo=OPERADOR|IA|SISTEMA`, `actor_id` vinculado à identidade autenticada/atribuição de caso quando aplicável, `autor_snapshot` exibível à época; preservar evento/direção e status Meta.
2. **Identificação no conteúdo visível**: `assinatura_visivel_ativa`, `assinatura_aplicada`, `nome_exibicao_snapshot`, `texto_original`/referência ao rascunho e `texto_enviado_final` (nome/campos exatos candidatos, não schema aprovado).

**Regras de segurança do contrato:** o backend obtém identidade no serviço de autenticação/atribuição do caso do operador e escopo da concessionária; **não** confia no nome fornecido pela IA, navegador, campo livre ou no destinatário. A assinatura não altera o `Phone-Number-ID`, o WABA nem o perfil comercial; não autoriza uso de outro canal. Histórico preserva o nome exibido na época mesmo após mudança do perfil do funcionário; logging seguro evita duplicar dados pessoais desnecessariamente.

**Composição proposta [P]:** uma função única depois da autorização do texto final, e antes de registrar intenção/mandar a Meta. Registrar **conteúdo exato efetivamente transmitido**, verificação de limites de tamanho, caracteres especiais e ausência de assinatura duplicada, respeitando idempotência de reservas e reenvios. Não repetir a assinatura quando um retry técnico reaproveitar a mesma tentativa. Prévia no painel mostra exatamente o texto que o cliente receberá.

**Mensagens livres:** continuam autorizadas apenas quando houver janela/política Meta que permita texto livre, com handoff/caso e opt-out verificados. A assinatura não permite enviar texto fora da janela de 24h.

**Templates aprovados:** a plataforma **NÃO pode simplesmente prefixar texto arbitrário no payload de um template aprovado**, nem transformar template em mensagem de texto livre fora da janela. Se o template tiver necessidade de assinatura, o texto e a variável de nome devem ser definidos no rascunho e aprovados pela Meta, com os slots/conexões congelados por versão. Durante o envio, **a plataforma preenche** a fonte aprovada (ex.: nome do operador autenticado) e audita o resultado. Caso a assinatura não tenha sido aprovada, enviar apenas conteúdo aprovado ou bloquear/selecionar template autorizado, nunca contornar a aprovação.

**Mídia/legenda/áudio:** não inventar campo de assinatura Meta; a política de identificação por caption, texto acompanhante ou apresentação somente na UI é [R/P] e depende das capacidades da mensagem.

**Handoff ou troca de operador:** identificar o operador correto do momento do envio; nunca anunciar “Mariana” se o caso já estiver atribuído a “João”. Falha no vínculo/autenticação deve bloquear assinatura humana forjada.

## 4. Exemplos de teste futuro (não executados)

| Caso | Prova esperada |
|---|---|
| Consultor A envia texto com janela elegível | A plataforma gera a prévia `Consultor Mariana:\n...` e transmite no `text.body`; atribuição, cargo e snapshot persistidos |
| Outro humano assume o caso | Próxima assinatura reflete **cargo e nome** de Consultor, Gestor ou Diretor B, mantendo histórico do autor A |
| IA responde | Não aparece nome de um humano de forma falsa; rótulo de IA quando definido por política própria |
| Tentativa de falsificar `actor_id`/nome | Backend rejeita identidade injetada e aplica atribuição autenticada |
| Texto enviado novamente por idempotência | Mesma mensagem final, sem prefixo duplicado |
| Janela fechada | Não se usa assinatura para contornar exigência de template |
| Envio de template aprovado sem slot de nome | NÃO anexar prefixo livre; apenas conteúdo/variáveis aprovados |
| Template aprovado com slot permitido de `operador.nome` | Backend resolve valor confiável da mesma concessionária, mantendo o slot congelado |
| Mudança de nome do operador no cadastro | Novas mensagens podem usar nome atual; histórico conserva `nome_exibicao_snapshot` |
| Mídias e legendas | Seguem a política [R/P] por tipo, sem campo Graph inventado |

> **Acompanhamento de implementação futura:** [issue #14 — WA-20: identificação visível do operador](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/14). Registro de produto não aprova envio real nem determina ainda a frequência do prefixo.

## 5. Escopo, documentação e coordenação

- **Frente WhatsApp/Meta:** valida se tipos de mensagem Meta permitem a forma de conteúdo autorizada, adapta texto/caption/template e registra status externos, sem decidir autoria ou permissão humana por conta própria.
- **S0 e interface de operadores:** autenticam operador, preservam atribuição/caso/autoria, configuram política de apresentação/assinatura e apresentam prévia. Não criar tabela paralela de operadores nem acesso de outro tenant.
- **MCP:** não necessário para cada envio operacional. Qualquer administração posterior da regra de apresentação por MCP exigirá ferramentas da outra frente, permissões, confirmação e auditoria próprias.
- **Estado atual [T]:** o projeto já possui contratos de autoria e tela histórica com autores, mas **não há prova de envio real com prefixo automático nem política final definida**. Este documento é a especificação futura, não uma funcionalidade liberada.

**Documentos vigentes de apoio:** [LEIA PRIMEIRO](./README.md), [01 funcional](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md), [00 decisões](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md), [WA-07](./wa07-contrato-janela-e-templates-cf-op-02-v0_1.md) e [02 conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Não modificar código, S0 SQL, CI ou templates Meta reais nesta etapa.
