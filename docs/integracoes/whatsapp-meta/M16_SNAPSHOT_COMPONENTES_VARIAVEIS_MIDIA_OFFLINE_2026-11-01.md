# M16 — Snapshot de templates, variáveis, mídia e botões (OFFLINE)

**Data:** 01/11/2026. **Frente:** WhatsApp/Meta. **Estado:** M16-A/B/C em laboratório; M16-D e marco principal dependem de S0/Infra, aprovação Meta e MCP autenticado. **Nenhuma aprovação real, Graph, MCP operacional ou envio.**

## Reutilização e fronteira

M16 não cria um segundo editor: usa a implementação existente [WA-17B](../../../integrations/whatsapp-meta/template-mcp-multiformat.ts) para validar BODY/HEADER/FOOTER, botões URL/PHONE_NUMBER/QUICK_REPLY, mídia IMAGE/VIDEO/DOCUMENT como **asset_ref interno** e slots `body.n`, `header.n`, `button.n.url.1`, com fontes declaradas no registro sintético. A WA-17A BODY-only permanece para compatibilidade, sem promover status de aprovação.

O [contrato MCP WA-17B](../../../integrations/whatsapp-meta/mcp-template-tools.v0.json) define ações administrativas **documentais**, não um servidor MCP instalado. A IA delegada pode propor textos e componentes; um serviço MCP futuro precisará autenticar o responsável, a delegação e a concessionária, aplicar confirmação e CAS de versões, registrar antes/depois e usar apenas um gateway Meta autorizado. Essa responsabilidade é de outra frente. **M16 não implanta, chama nem modifica ferramentas MCP operacionais**.

O observador Graph atual [`graph-template-provider-observation.ts`](../../../integrations/whatsapp-meta/graph-template-provider-observation.ts) só normaliza HEADER TEXT, BODY, FOOTER e QUICK_REPLY (subconjunto). **Não** validar HEADER de imagem/vídeo/documento, URL ou PHONE_NUMBER via esse observador como se fosse aprovação completa. O digest M13 `provider_components_sha256` se aplica ao subconjunto compatível e tampouco autentica Meta.

## M16-A — Composição congelada em laboratório

Novo [`wa16-template-snapshot-offline.ts`](../../../integrations/whatsapp-meta/wa16-template-snapshot-offline.ts):

- `freezeWa16TemplateOffline(raw)`: recebe exclusivamente fixture `wa16-template-freeze.lab.v0.1` com seleção, tenant UUID/WABA, template_ref/version_ref, `content_version`, `mapping_revision`, `media_revision`, relógio, origem WA-17B, bindings completos, lista de fontes supostamente autorizadas, evidência de mídia ou `null`, e `review_state:'LAB_REPORTED_APPROVED'`. O estado reportado **não prova aprovação**.
- Entrada validada como dados próprios: sem getters, símbolos, arrays esparsos, protótipos hostis, ciclos, campos extras, profundidade/tamanho abusivos. Antes de chamar o editor WA-17B, faz cópia interna imutável dos dados.
- Reusa `composeMcpTemplateDraft` e `mapMcpTemplateSources`. Para cada slot do conteúdo congelado, exige uma fonte declarada na fixture de registro. Fontes não registradas, slots obsoletos, buracos nas posições e bindings incompletos negam. A revisão `mapping_revision` do contrato de laboratório é separada do helper local WA-17B; o backend futuro deve autenticar a revisão/cursor.
- Conteúdo, exemplos, categoria, autoria, BODY/HEADER/FOOTER, botões, URLs e slots compõem `component_sha256`. Uma alteração visível ou alteração da versão produz outro digest.
- Slots ordenados pela posição, fontes de cada slot e versão de mapeamento compõem `binding_sha256`. Uma alteração de fonte sob a mesma versão não passa no recheck.
- Para HEADER IMAGE/VIDEO/DOCUMENT, exige fixture adicional escopada à **mesma concessionária e WABA**, mesmo `asset_ref`, tipo, MIME permitido localmente, SHA-256 do ativo, revisão do ativo igual à `media_revision`, estado `LAB_READY`, janela temporal e leitura recente. A evidência e escopo compõem `media_sha256`. Sem cabeçalho de mídia, `media_evidence` deve ser `null` e `media_revision=0`.
- `snapshot_sha256` liga versão de conteúdo, versão do mapeamento, revisão de mídia, escopo, categoria/composição validada e os três digests. É só um **hash técnico determinístico**, sem assinatura, procedência, persistência nem independência das fontes.
- Retorno `wa16-frozen-snapshot.lab.v0.1` somente com escopo/versões/digests, contagem de slots e tipo de mídia; não revela texto, valores das variáveis, asset_ref, destino de botão, URL, número telefônico, conteúdo de mensagem nem token/handle de mídia.
- `recheckWa16TemplateOffline(candidate,freshFixture)`: reconstrói a projeção inteira de outra fixture injetada e só devolve `LAB_RECHECKED_UNVERIFIED` se todos os campos coincidirem; caso contrário nega. Não oferece snapshot real em banco, lock, CAS, replay journal, transação, Graph ou autoridade comercial.

Todas as saídas mantêm `send_authorized:false`, `production_authorized:false`, `meta_approval_verified:false`, `media_verified:false` e `mcp_execution_authorized:false`, mesmo quando a fixture diz `LAB_REPORTED_APPROVED` ou `LAB_READY`. Digest não confirma que Meta aprovou componentes nem que a fonte S0 realmente está autorizada.

## M16-B — Evidência adversarial

[44 testes M16](../../../integrations/whatsapp-meta/wa16-template-snapshot-offline.test.ts) `M16-01..44` abrangem alterações de BODY, HEADER, FOOTER, botões, URL dinâmica, exemplos, bindings, revisões, loja/WABA, fontes não autorizadas, slots descontinuados, cabeçalhos não suportados, URLs inseguras, mídia ausente/incompatível/vencida, media asset/SHA diferente, MIME, media de outra loja/WABA, getters e objetos cíclicos, arrays esparsos e adulteração de candidato.

**Evidência funcional:** SHA `b9390ffa374ae0d3eb27c120902b3ece90ced8d1`, [CI 41295741371](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41295741371), **1.617/1.617 casos Meta offline** (1.573 anteriores + 44 M16), scanner lexical ACK sem autoridade. Ambos jobs `success`, **18/18 testes PG17 históricos** e scanner ACK lexical aprovado. Os 18 testes PG17 históricos são do ingresso físico anterior, **não provam congelamento nem upload de mídia M16**. As execuções intermediárias anteriores aos ajustes da fixture de mídia tiveram falhas: estavam mantendo um slot `header.1` textual depois de substituir HEADER TEXT por mídia, corretamente rejeitado pelo motor; a fixture foi corrigida sem flexibilizar o validador.

## M16-C — Contrato e bloqueios de operacionalização

- A plataforma precisa de **catálogo de componentes por versão** autenticado, gravado em S0, com `content_version`, `mapping_revision`, `media_revision`, identidade App/WABA/loja, versões/revisões do catálogo e prova de origem. Nada disso é criado neste laboratório.
- O MCP real deve autenticar principal/delegação, ferramentas e permissões; usar registro de fontes habilitadas por concessionária, CAS de alterações, auditoria imutável e política de confirmação. A frente Meta mantém o núcleo e o contrato, **não o servidor MCP**. A IA autora não pode autenticar o próprio grant, fazer download arbitrário ou executar SQL.
- Mídia necessita host/gateway autenticado para upload e prova do handle retornado pela Meta, tipo MIME/tamanho reais, tenant/WABA e vigência; `asset_ref` ou SHA de fixture **não** são upload nem arquivo seguro por si sós.
- Aprovação de componentes precisa leitura Graph real autenticada por WABA e suporte validado aos formatos MIME/botões aceitos; nenhuma variante atualmente não suportada no observador M13 pode ser promovida por hash semelhante. Estar `APPROVED` não libera envio.
- Durante despacho, a S0 deve preencher cada slot exclusivamente com fonte autorizada, bloquear valor ausente e URL insegura, revalidar consentimento/opt-out, catálogo, versão, status, mídia, canal, janela e idempotência sob PRE_DISPATCH transacional [Issue #10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10). Contrato F02 candidato [#7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7); registry/grants [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8).
- A criação de nova versão de conteúdo aprovado e mudanças no `slot→source` devem seguir **nova revisão auditada** e nova verificação Meta quando aplicável; nunca editar versão congelada por atalho. Não confundir hash com assinatura, serialização, origem de aprovação ou o próprio congelamento persistente.

**Estado:** M16-A/B/C concluídos somente offline sob testes; **M16-D e marco M16 permanecem [ ]** para aprovação real e integração S0/MCP/Graph. Sem merge, deploy, Graph API, MCP operacional, banco produtivo, HTTP ACK, envio ou efeito comercial.


## Adendo de auditoria — 01/11/2026

A [auditoria M16](AUDITORIA_M16_SNAPSHOT_COMPONENTES_2026-11-01.md) complementou o congelamento técnico, sem autorizar Graph/MCP real:

- O domínio de `snapshot_sha256` passa a incluir `selection_ref`; seleção diferente não pode compartilhar o mesmo hash mesmo com conteúdo/template iguais.
- `binding_sha256` agora incorpora **toda a lista sintética `source_registry` ordenada**. Adicionar/remover fonte não utilizada invalida a fotografia; reordenar não. Isto **não autentica** autorização das fontes.
- Strings acima de 8.192 unidades UTF-16 são rejeitadas antes de clonagem e hashing. Não substitui limites de transporte/arquivos da Meta.
- Saída versionada como **`wa16-frozen-snapshot.lab.v0.2`**, evitando confusão de domínios de digest com o contrato de saída v0.1. A fixture de entrada permanece `wa16-template-freeze.lab.v0.1`; candidatos antigos são rejeitados.
- A proteção da evidência de mídia por `concessionaria_id` e WABA já existia no HEAD auditado, com os testes M16-43/44; não foi reimplementada.

**Evidência funcional:** 56 testes específicos (44 originais + 12 AUD-M16-45..56), **1.629/1.629 Meta offline**, scanner ACK lexical aprovado no [CI 41297336878](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41297336878), commit funcional `17fe2f5adf0b21a483960f7b72d8d20421974e2f`. A prova PG17 do ingresso S0 é independente e não autentica componente, arquivo de mídia ou aprovação M16.

M16-D e marco principal permanecem abertos; nenhuma autorização operacional foi concedida.
