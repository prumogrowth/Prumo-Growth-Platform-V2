# WA-17B — Templates WhatsApp multimídia geridos por IA através de MCP

**Data:** 20/10/2026. **PR:** #2, Draft, sem deploy/merge. **Decisão nova do responsável:** o meio principal de administração da plataforma é **MCP**, operado por uma IA ou outro cliente autorizado. A IA pode inserir exatamente o texto que o responsável disser ou **gerar o conteúdo inteiro quando solicitado**. A restrição anterior “apenas cadastro manual/sem texto gerado pela IA” está **revogada**. A tela administrativa é opcional; ela não é a única porta de cadastro.

## 1. Fluxo desejado

1. Responsável autenticado ou IA à qual ele delegou permissões chama o servidor MCP da Prumo: “crie um template com imagem, corpo com nome do cliente e um botão ‘Simular agora’ apontando para uma URL”.
2. O MCP do serviço — **não o modelo de linguagem por si só** — resolve identidade do responsável, agente/delegação, tenant, WABA, capacidade de editar/submeter, versão e registro de mídia; não aceita `concessionaria_id` declarado pela IA como autoridade.
3. A IA organiza o rascunho em componentes tipados e pode criar o texto se o responsável autorizou essa geração. `origin` identifica `HUMAN_SPECIFIED`, `AI_ASSISTED` ou `AI_GENERATED` apenas para auditoria, sem ampliar permissões.
4. O motor salva no catálogo versionado. Com autorização administrativa aplicável, solicita à Meta criação/revisão pela Graph API de **gerenciamento de templates**; essa etapa exige autenticação e mídia verificada pela Meta.
5. O serviço persiste ID recebido, evidência de solicitação, status de processamento e consultas/webhooks autenticados. Recibo de API não significa aprovado. Rejeição, pausa/desativação e mudanças de categoria devem ser observadas.
6. O responsável pode pedir à IA via MCP para ligar `body.1` a `cliente.nome`, `body.2` a `operador.nome`, `button.0.url.1` a `caso.codigo`, sem alterar texto e URL-base aprovados. Mapeamento versionado com auditoria.
7. Só num fluxo de disparo **distinto** e devidamente autorizado, motor resolve parâmetros, confere consentimento/opt-out, política Meta, janela, estado S0, canal, template aprovado e idempotência. A IA não recebe permissão comercial automaticamente.

O MCP precisa servir também plataformas de terceiros desenvolvidas pelo responsável, desde que autenticadas e autorizadas: as ferramentas não devem depender de um agente ou fornecedor de IA particular.

## 2. Formatos e capacidades

| Componente | Recursos reconhecidos | Situação da WA-17B |
|---|---|---|
| BODY | Texto com placeholders `{{1}}`, `{{2}}` e exemplos | Contrato offline |
| HEADER | TEXTO; IMAGE; VIDEO; DOCUMENT | Contrato offline; mídia requer handle verificado |
| FOOTER | Texto simples | Contrato offline |
| BUTTONS | QUICK_REPLY, PHONE_NUMBER, URL estática e dinâmica | Contrato offline |
| Valores separados | Variáveis em BODY, HEADER e URL de botão | Contrato offline por `slot_key` |
| Outros | LOCATION, COPY_CODE, FLOW, catálogo/múltiplos produtos, AUTHENTICATION, CAROUSEL, recursos especiais | Reservados no *capability registry*; sem suporte automático ou validação conclusiva |

Nem todas as combinações são necessariamente aceitas. A WA-17B aplica uma **política inicial deliberadamente conservadora** para texto, número de botões e formato de URL. Esses limites são do protótipo, **não afirmação de limites da Meta**. Versão da API, novos formatos, categorias e limites precisam ser validados antes de habilitar cada capacidade na integração oficial.

### Botões URL e variáveis

Um botão possui `label` (o texto exibido) e `url` (destino). Exemplo fictício:

```json
{
  "kind": "URL",
  "label": "Simular agora",
  "url": "https://example.com/consulta/{{1}}",
  "example_suffix": "codigo_exemplo"
}
```

O identificador `button.0.url.1` é configurado depois como fonte segura, por exemplo `caso.codigo`. O vínculo não pode montar URL arbitrária a partir de texto fornecido pelo cliente; a URL-base precisa ser previamente validada e o domínio autorizado pelo backend. O sufixo de exemplo é fictício; exemplos reais para revisão devem respeitar política e privacidade.

Para mídias, `asset_ref` guarda apenas referência interna do arquivo. **Não é upload na Meta**. Antes de submeter, o adaptador de mídia autenticado deve comprovar o vínculo entre ativo/tenant/WABA e o handle de mídia aceito pela Meta, com política de tamanho, tipo, expiração, segurança e armazenamento.

## 3. Ferramentas MCP previstas

O servidor MCP — **ainda não instalado nem registrado na WA-17B** — deverá oferecer ações com JSON Schema estrito e documentação de escopo:

```text
templates.capabilities
templates.list / templates.get
templates.create_draft
templates.edit_draft_components
templates.preview
templates.configure_variable_sources
templates.prepare_review
templates.submit_for_meta_review
templates.sync_meta_status
templates.new_content_version
templates.audit_history
```

Separar permissões de `draft.write`, `media.manage`, `variables.write`, `review.submit`, `review.status.read` e `audit.read`, sempre sob escopo de WABA/tenant e ator/delegação, com transações/idempotência/auditoria. O responsável pode autorizar a IA a **redigir** sem lhe conceder automaticamente permissão para **submeter ou disparar**; políticas de delegação podem permitir submissão dentro dos limites aprovados, conforme fluxo administrativo documentado.

**Ações mutáveis:** registrar `request_id` de idempotência e autoria, validar revisão esperada, manter evidência do antes/depois e motivo. Tool output não pode afirmar `APPROVED` sem confirmação autenticada da Meta. Impedir que instruções recebidas em conversa com clientes sejam tratadas como comandos de administração (proteção contra prompt injection).

## 4. Desenvolvimento publicado

- `integrations/whatsapp-meta/template-mcp-multiformat.ts`: contrato TypeScript puro de componentes e capacidades, origem de criação por IA ou humano, validações de forma, snapshots de mídia, botões URL estáticos/dinâmicos e posições de variável em BODY/HEADER/BUTTON; composição do JSON de **solicitação futura** à Meta, sem Graph/HTTP, e catálogo de nomes de ferramentas MCP planejadas.
- `integrations/whatsapp-meta/template-mcp-multiformat.test.ts`: **16 testes WA17B-01..16 preparados**, cobrindo imagem, vídeo, documento, texto, rodapé, URL dinâmica, ligação de fontes, formatos futuros negados, conteúdo gerado por IA, ausência de permissão de envio, recusa a URLs e campos suspeitos.
- `integrations/whatsapp-meta/mcp-template-tools.v0.json`: contrato JSON Schema com **12 operações MCP** previstas (criar, editar, fazer prévia, mapear fontes, solicitar revisão, consultar status e auditoria), `additionalProperties:false`, sem aceitação de campos `principal_id` ou token do chamador. **Não é ainda registro de ferramentas em um servidor MCP executável.**
- `integrations/whatsapp-meta/template-catalog-control.ts`: WA-17A BODY-only preservada por compatibilidade; **não é mais o teto de formatos nem a única forma de autoria**.
- [Issue #11](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/11): atualizada para registrar MCP como entrada principal e mídia/botões como capacidades da arquitetura.

**Evidência:** código e testes publicados no GitHub, mas **sem CI confirmado para WA-17B** até esta atualização. Não chamar 14/14 de PASS. WA-16 anterior também tinha testes preparados mas ainda sem execução confirmada.

## 5. Próximos gates necessários

**Não implementados:** servidor MCP de fato; autenticação/delegação do responsável e agente; banco persistente `catalogo_templates`/versões e vínculo de envios; ferramenta real para upload/associação de mídia; integração com Graph API Meta para criar/consultar/atualizar; validação de esquema oficial por versão; domínio com allowlist de URLs; auditoria transacional; provas CI de isolamento tenant e fluxo completo com Graph fake. Nenhum template real enviado à Meta.

## Fontes de Meta consultadas (20/10/2026)

- Exemplos oficiais do Postman Meta: [imagem + CTA](https://www.postman.com/meta/whatsapp-business-platform/request/n3jhmr4/create-template-w-image-header-text-body-text-footer-and-2-call-to-action-buttons), [documento + botões URL/telefone](https://www.postman.com/meta/whatsapp-business-platform/request/ep5w4rc/create-template-w-document-header-text-body-a-phone-number-button-and-a-url-button), [texto + respostas rápidas](https://www.postman.com/meta/whatsapp-business-platform/request/uvx80vi/create-template-w-text-header-text-body-text-footer-and-2-quick-reply-buttons), [catálogo](https://www.postman.com/meta/whatsapp-business-platform/request/ark9lha/create-catalog-template), [múltiplos produtos](https://www.postman.com/meta/whatsapp-business-platform/request/a4is22v/create-multi-product-message-template) e [edição](https://www.postman.com/meta/whatsapp-business-platform/request/bpcsm6i/edit-template).
- [Exemplo oficial de envio de template com parâmetros e botões](https://www.postman.com/meta/whatsapp-business-platform/request/lwtlz1k/send-message-template-interactive).
