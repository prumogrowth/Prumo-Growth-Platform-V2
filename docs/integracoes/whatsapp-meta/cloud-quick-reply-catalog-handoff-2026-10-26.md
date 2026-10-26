# Meta Cloud API — templates interativos de resposta rápida, sem envio

**26/10/2026 — proposta incremental da frente WhatsApp/Meta.** Base: PR #8; branch independente `feat/meta-cloud-interactive-template-20261026`. PR #14 / `aux/meta-s0-contracts-20261026` permanece intacto. Nenhum merge, deploy, conta Meta, token, webhook público, banco ou modificação S0/S1.

## Lacuna demonstrada e reaproveitamento

O preparador existente `graph-template.ts` permite templates C06 de **texto posicional** (HEADER e BODY de texto, FOOTER opcional), mas rejeita corretamente componentes BUTTON e mídia. WA17 e contratos WA36/37 controlam catálogo/ratificação no laboratório. PR #14 já modela reserva de tentativa, observação externa, ingresso M2M e lock; não se deve recriar esses serviços.

A documentação oficial Meta mostra templates aprovados com componente `button`, `sub_type: "quick_reply"`, `index: "0"` e parâmetros `[{type:"payload",payload:"..."}]`, inclusive em conjunto com componentes de texto. Fonte primária: https://www.postman.com/meta/whatsapp-business-platform/request/lwtlz1k/send-message-template-interactive . O corpo do request é `POST /{Phone-Number-ID}/messages` com `type:"template"`; o código **não realiza POST**.

## Implementação efetiva e escopo exato

`integrations/whatsapp-meta/graph-template-interactive.ts` acrescenta um builder puro:
`prepareGraphQuickReplyTemplateRequest(intent, trustedBaseTextSnapshot, trustedScope, trustedCompleteButtonCatalog, apiVersion)`.

- Chama `prepareGraphTemplateRequest` **sem modificar seu comportamento**, reutilizando o controle de C06, formato de Graph, destino, revisão, catálogo-base de texto, parâmetros e binding de escopo.
- Recebe um **segundo manifesto de catálogo completo** apenas para botões QUICK_REPLY estáticos; exige `approval:"APPROVED"`, `schema_complete:true`, versão literal, template/language/revision e cinco campos de escopo consistentes com o builder-base.
- Aceita **1–3 quick replies** ordenados em índices inteiros exatos `0..n-1`. Payloads são valores opacos ASCII controlados pelo catálogo confiado (`[A-Za-z0-9_.:-]`, 1–128); não são gerados a partir de mensagem, telefone ou input do usuário. Não aceita CTA URL, chamada, links, mídia, extras, protótipos não simples, getters ou botões parcialmente declarados.
- O catálogo-base de texto é uma **projeção somente dos componentes TEXT**, que permanece válida para a validação preexistente; é OBRIGATÓRIO que um serviço confiável comprove que o catálogo estendido descreve o template aprovado completo, não apenas um objeto JSON alegando `APPROVED`.
- Retorna um descritor **inerte** com caminho relativo Graph e corpo de template. Não contém Authorization, base URL, request headers de autenticação, token, método `fetch`, cliente Supabase nem `send_authorized`. Contém **PII no destino e eventualmente parâmetros**: não registrar o descritor em logs.
- Mensagem enviada, ACK, janela de 24h, consentimento, opt-out, permissão, versão de intenção, número de remetente e catálogo devem ser aprovados **pela S0 antes de qualquer futuro Graph POST**. O builder não substitui a reserva e o begin candidatos do PR #14.

**Limitações intencionais:** mídia/CTA URL e payloads dinâmicos por cliente continuam não suportados. Não prometer que payloads estáticos são adequados a todos os fluxos comerciais, nem que Graph aceitou algum envio.

## Testes e CI

`graph-template-interactive.test.ts` implementa **18 testes exclusivos**: payload Graph/ordem, 1–3 botões, inexistência de quarto botão, duplicata de índice, CTA/URL não suportados, caracteres/PII no payload, catálogo PENDING/PAUSED, divergências de revisão/escopo, pré-validações existentes do C06, protótipos/accessors e campos injetados.

`.github/workflows/meta-cloud-interactive-template.yml`: executa 18 novos testes e **161 regressões selecionadas** dos adaptadores Meta já existentes (HMAC, routing, texto/template, WA36/37, webhook handoff, wire observation). Não repete WA39–68 nem as 52 provas candidatas do PR #14. Zero dependências externas.

## Dependência objetiva de catálogo — encaminhar à S0/Codex quando integrar

**META-S0-TEMPLATE-CATALOG-05 (novo requisito específico da interface):**

A S0 deverá fornecer um **snapshot de template por concessionária e canal** que provenha de catálogo confiável, com status efetivo de aprovação Meta, `template_name`, `language_code`, `template_revision_ref`, manifesto completo de componentes TEXT + QUICK_REPLY ordenados e vínculo à origem WABA/phone. Exigir ainda regra de emissão e revisão de payloads opacos: estáticos aprovados, ou valores dinâmicos **exclusivamente** gerados e assinados pelo backend.

**Critérios positivos:** quando o catálogo é atual/aprovado e a elegibilidade C06 + consentimento + opt-out foi revalidada, a S0 pode fornecer descriptor inerte e uma reserva autorizada independente; payloads dos botões são provenientes do manifesto S0, não do ingressor.

**Critérios negativos:** catálogo PENDING/PAUSED, revisão divergente, escopo de outra loja/phone, índice ausente/duplicado, componente URL/mídia não contratado, payload de entrada de usuário, opt-out e snapshot desatualizado **não podem iniciar Graph POST**. O processo de homologação deve testar templates realmente aprovados por Meta antes de habilitar rede.

**Titular:** Codex/S0 + catálogo Meta/Infra; políticas comerciais/S1 responsáveis por opt-in/finalidade. **Este requisito não bloqueia novas implementações independentes**, mas bloqueia o uso operacional dessa funcionalidade.

## Protocolo de handoff

Revisar este PR Draft e os contratos PR #7, #8 e #14; manter as branches sem merge automático. Apenas ratificação formal e homologação em sandbox controlado podem permitir transporte real e envios. Até lá, o catálogo de botões é fixture offline e **não concede autorização comercial**.
