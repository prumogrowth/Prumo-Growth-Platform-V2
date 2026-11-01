# Auditoria corretiva M17 — autoria humana em mensagens WhatsApp

**Data:** 01/11/2026. **Frente:** WhatsApp/Meta, branch `feat/meta-s0-physical-interop-ack-guard-20261031`. **Escopo:** `integrations/whatsapp-meta/wa17-human-message-signature-offline.ts`, testes correspondentes, decisões WA-20/WA-21 e dependência de identidade da S0/S1 na Issue #10. Nenhum envio, Graph, SQL, autenticação ou endpoint.

## Regra aprovada e controles preservados

A [WA-21](wa21-papeis-diretor-gestor-consultor-assinatura-2026-10-21.md) determina prefixo visível **`Consultor Nome:\nMensagem`**, **`Gestor Nome:\nMensagem`** ou **`Diretor Nome:\nMensagem`** em cada **texto livre humano**. É parte do corpo da mensagem, não campo de remetente Meta. Para templates só texto/slots aprovados; não prefixar mensagem IA/sistema ou legenda/mídia por analogia. A M17 atual é **somente uma simulação** de decisões que pertencem à S0/S1, mesmo que a fixture diga `CLAIMED_ACTIVE`, `CLAIMED_OPEN` ou `opt_out:false`.

## Achados e correções

**AUD-M17-01 — falsificação de cargo em linhas interiores (corrigido).** A expressão inicial recusava um cabeçalho `Diretor Nome:` no **começo** do rascunho, mas aceitava `Olá!\nDiretor Ana Silva:\n...`, inclusive com espaços de indentação. O corpo composto poderia aparecer como duas falas com credenciais humanas diferentes sob um único `Consultor`. O detector agora recusa padrões de cargo humano em início de qualquer linha, com indentação horizontal, com razão `DUPLICATE_OR_FORGED_PREFIX`. A detecção é conservadora, não pretende reconhecer todas as falsificações visuais ou linguísticas possíveis.

**AUD-M17-02 — quebras visuais Unicode e substituição de byte (corrigido).** O filtro removia LF para permitir corpo multiline e recusava controles `Cc/Cf`, mas não `Zl/Zp` nem surrogates isolados `Cs`. Quebras Unicode visualmente equivalentes a outra linha e UTF-16 inválido podiam alterar interpretação/renderização e bytes no transporte. O filtro agora nega `Cc/Cf/Cs/Zl/Zp` (exceto LF explícito) e mantém o limite laboratorial de 4.096 bytes UTF-8 do texto composto.

**AUD-M17-03 — checksum apenas do corpo não vinculava escopo/autor/intenção (endurecido).** `composed_sha256` era SHA-256 do texto visível. Dois intents ou casos distintos com a mesma assinatura compartilhavam esse hash; a comparação por campos no recheck ainda os diferenciava, mas o hash isolado não era identificador de contexto. A saída **`wa17-human-prefix-preview.lab.v0.2`** adiciona `context_sha256` de um domínio canônico que inclui seleção, concessionária, WABA, caso, intenção, autor, cargo/nome, quatro revisões, `draft_sha256` e `composed_sha256`. Isso **não é MAC/assinatura**, não autentica a fonte ou previne replay/ABA. O conteúdo original continua não exposto em respostas negativas.

**AUD-M17-04 — prévia anterior não verificava seu próprio vínculo texto↔autor↔rascunho (endurecido).** O validador de prévia anteriormente verificava campos/tipos e hash de `composed_text`, mas não se o corpo começava com o cargo/nome declarados nem se a parte após o prefixo correspondia ao `draft_sha256`. Antes de comparar ao novo recheck, exige agora o cabeçalho exato WA-21, normalização/nome consistente, digest do rascunho, ausência de cabeçalho humano aninhado, hash do composto e hash de contexto. A saída antiga `v0.1` é intencionalmente recusada, pois o domínio de consistência foi alterado. Essa validação não torna um snapshot alegado autêntico.

## Regressões e evidências

- **56 testes M17-01..56** anteriores preservados.
- **20 testes AUD-M17-57..76** adicionais: cabeçalho falso posterior/indentado, corpo comum com várias linhas, separadores `U+2028/U+2029`, surrogate isolado, caráter de formatação, ligação de case/intenção/seleção/autor ao novo digest, adulteração de cargo/texto/digest, rejeição da versão anterior, nome hífen válido.
- **Evidência funcional:** SHA `c70eac68fecccc481ca0191ece42b96fb3fcc770`, [CI 41309801562](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41309801562) — **1.705/1.705 testes Meta offline**, **76 M17**, scanner ACK lexical aprovado, **18/18 provas PG17** históricas de ingresso físico S0/Meta no job independente, **dois jobs `success`**. As PG17 **não comprovam autoria M17**. Runs intermediários do código sem a suíte integral não constituem homologação final da auditoria.

## Decisões e limites entre frentes

- [ ] A S0/S1 deve **autenticar de verdade** sessão/principal humano, papel atual, nome e atribuição ao caso por loja/WABA, sem tomar alegações do front-end ou da IA como fonte. O laboratório atual não emite `identity_verified:true`.
- [ ] S0 deve controlar janela de texto livre, handoff, consentimento/opt-out, autorização específica de ação e versão do caso, transação `PRE_DISPATCH`, reserva/recibo/readback, idempotência e recuperação; [Issue #10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10). A interface de App/WABA/grants permanece na [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8). O PG17 `prumo.s0.pre-dispatch.pg17/0.1-lab-only` não é integrado à M17 e não autoriza Graph.
- [ ] O histórico operacional deve preservar **identidade técnica imutável**, cargo/nome no instante e bytes/versão do corpo efetivamente transmitido. Alterar o nome depois não reescreve histórico; `sent/delivered/read` depende de provas Meta distintas.
- [ ] O host deve manter `composed_text` **privado**; o hash é rastreabilidade laboratorial, não token/credencial ou prova de identidade. Deve impedir que texto de IA/sistema se passe por humano pela origem e pelo controle de posse do caso — filtros de conteúdo sozinhos não bastam.
- [ ] Templates e mídia não herdam a regra do texto livre; assinatura em template exige slot ou conteúdo previamente aprovado pela Meta, com fonte S0. Nenhuma simulação M17 concede permissão de envio, alteração comercial ou poder MCP.

**Parecer:** M17-A/B/C **concluídas e auditadas somente offline**; M17-D e M17 principal continuam `[ ]`. Retornos mantêm `identity_verified=false`, `authorization_verified=false`, `send_authorized=false`, `production_authorized=false`, `graph_dispatch_authorized=false`. Nenhum Graph real, envio, SQL, HTTP ACK, merge/deploy ou produção.
