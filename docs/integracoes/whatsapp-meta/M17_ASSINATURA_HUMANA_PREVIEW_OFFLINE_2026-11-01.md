# M17 — Assinatura humana nas mensagens textuais livres (LAB offline)

**Data:** 01/11/2026. **Frente:** WhatsApp/Meta. **Escopo:** composição/preview **exclusivamente offline**. **Estado:** M17-A/B/C em implementação de laboratório, **M17-D e marco principal abertos**. Não há sessão S0 autenticada, HTTP, Graph, envio real, política de janela de produção ou efeito comercial.

## Decisões funcionais e precedência

A [WA-21](wa21-papeis-diretor-gestor-consultor-assinatura-2026-10-21.md) prevalece sobre exemplos históricos [WA-20](wa20-identificacao-visivel-atendente-assinatura-mensagem-2026-10-21.md):
- `Consultor Nome:\nMensagem original`
- `Gestor Nome:\nMensagem original`
- `Diretor Nome:\nMensagem original`

O formato vale para **cada texto livre escrito por humano** com cargo vigente e autorização S0, no contexto do atendimento. É texto visível no corpo da mensagem, **não remetente nativo Meta**, cargo concedido ou comprovante de envio. Não assinar textos redigidos exclusivamente por IA/sistema, não prefixar templates já aprovados pela Meta nem usar essa regra para contornar janela Meta. A decisão sobre legenda/mídia depende de contrato específico e não é ampliada aqui.

## M17-A — Prévia de composição de prefixo

`integrations/whatsapp-meta/wa17-human-message-signature-offline.ts` introduz duas funções puras:
- `previewWa17HumanSignatureOffline(request,sessionClaim,caseClaim)`
- `recheckWa17HumanSignatureOffline(previousPreview,freshRequest,freshSessionClaim,freshCaseClaim)`

Todos os objetos são **alegações injetadas no laboratório**, com schemas estritos `wa17-human-free-text-request.lab.v0.1`, `wa17-s0-session-claim.lab.v0.1` e `wa17-s0-case-claim.lab.v0.1`. A requisição **não aceita** `role`, `display_name` ou `actor_ref` fornecidos pelo cliente/IA. Os dois outros objetos simulam o que um futuro S0 autenticado deveria garantir. Conferem loja, WABA, caso, autor/atribuição, cargo atual, revisão de sessão/identidade/caso/atribuição e idade do snapshot. Não aceitam IA, sistema, templates ou captions como solicitação de assinatura.

Para simular a elegibilidade do texto livre, o caso de laboratório deve indicar `assigned_human:true`, `handoff_state:'HUMAN'`, `free_text_window:'CLAIMED_OPEN'`, `can_send_free_text:true` e `opt_out:false`. Essas condições **não comprovam** autorização ou opt-in real. O corpo precisa ser texto não vazio, normalizado NFC, sem caracteres de controle invisíveis e sem cabeçalho inicial de Consultor/Gestor/Diretor digitado pelo usuário; falha segura contra falsificação ou assinatura duplicada. A composição final tem limite conservador **4096 bytes UTF-8** somente neste laboratório, sem afirmar que é o limite universal de Graph.

A saída `wa17-human-prefix-preview.lab.v0.1` conserva escopo, `intent_ref`, ator/cargo/nome **alegados**, revisões, `draft_sha256`, `composed_sha256` e **`composed_text` exato** para conferência pelo painel. É informação privada do atendimento e **não pode ser entregue como ferramenta ao modelo ou publicada em logs indiscriminadamente**. Uma negativa retorna apenas motivo tipado e flags falsas, sem nome/mensagem. A revisão da prévia precisa sempre receber a solicitação **original**, não `composed_text`, e comparar a nova composição/revisões com o preview antigo. Tentativa de retry reenviando texto já assinado é recusada.

Todas as respostas, mesmo positivas, mantêm `identity_verified=false`, `authorization_verified=false`, `send_authorized=false`, `production_authorized=false`, `graph_dispatch_authorized=false`. O resultado positivo é `LAB_HUMAN_PREFIX_UNVERIFIED` ou `LAB_RECHECKED_UNVERIFIED`, **não uma assinatura digital**.

## M17-B — Provas adversariais e limites

`integrations/whatsapp-meta/wa17-human-message-signature-offline.test.ts` inclui **56 cenários M17-01..56** para Consultor/Gestor/Diretor, nomes com acento, isolamento de concessionária/WABA/caso, atuação de humano distinto, janela fechada, opt-out, atribuição/handoff, observações antigas/futuras, supressão de mensagem IA/sistema/template/mídia, tentativa de forjar cargo/nome no request ou no corpo, getters não executados, caracteres invisíveis, limites de tamanho e recheck após troca de ator/cargo/versão, sem mensagem parcial.

**Evidência CI:** registrar o run final após aprovação dos dois jobs. O conjunto anterior da Meta tinha 1.629 testes; com 56 testes M17 espera-se **1.685 Meta offline**. O conjunto de 18 provas físicas históricas PG17 é do **ingresso S0/Meta**, não testa a autoria humana M17.

## M17-C — Fronteira S0 e integração futura

1. S0/S1 autenticará a sessão humana real e extrairá `actor_ref`, `role` e `display_name` somente do cadastro vigente; manterá atribuição ao caso e vínculo à loja/instância. Não permitir que IA, front-end ou texto livre declarem cargo, nome, conta ou permissão.
2. S0 fará recheck **na etapa efetiva de envio** da janela Meta, política/consentimento/opt-out, estado humano do caso, revisões de identidade/cargo/atribuição, canal, destino e idempotência/reserva, sem tratar as flags de laboratório como permissão. A [Issue #10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10) coordena a autoridade transacional do PRE_DISPATCH; a prova de canal/identidade depende da [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8).
3. S0 manterá conteúdo original e conteúdo final efetivamente enviado, `autor_snapshot`/cargo/nome e IDs de intenção/tentativa num histórico imutável e protegido. Trocas futuras de nome/cargo não reescrevem autoria anterior. O resultado do transporte é recebido da Meta separadamente; `text.body` assinado não prova `sent`, `delivered` ou `read`.
4. Reenvio/retry só pode reutilizar a **mesma intenção e corpo final persistidos** sob o contrato S0; a M17 não faz commit, não implementa reenvio e não prova idempotência física.
5. Se a mensagem for template aprovado, **não anexar prefixo arbitrário**: cargo/nome apenas por conteúdo ou slot previamente aprovado e preenchido de fonte S0 autorizada. Mídia/legenda aguardam decisão específica; este módulo não os atende.
6. Não promover a entrega recente S0 de PRE_DISPATCH PG17 (`prumo.s0.pre-dispatch.pg17/0.1-lab-only`) a fonte de identidade autenticada; seu aceite e aplicação real pertencem aos proprietários das frentes.

**Status:** M17-A/B/C são apenas evidência offline; **M17-D e marco principal [ ]** até autorização/integração S0/S1/Infra e testes físicos do fluxo correto. Sem Graph, merge, deploy, HTTP ACK, banco produtivo ou envio de mensagem.
