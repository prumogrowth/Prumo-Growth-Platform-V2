# Auditoria geral independente da frente Meta/WhatsApp — M01 a M20

**Data:** 01/11/2026. **Repositório:** `prumogrowth/Prumo-Growth-Platform-V2`. **Branch:** `feat/meta-s0-physical-interop-ack-guard-20261031`. **Natureza:** revisão transversal após auditorias individuais, incluindo correções de código, testes adversariais e validação CI. **Escopo de responsabilidade:** frente Meta/WhatsApp; não assumir poderes de S0/S1, Infra ou OpenAI/F02. **M21 não iniciada neste ciclo.**

## Parecer executivo

**Foram encontrados problemas reais e corrigidos:** seleção de referências de credenciais a partir de objetos com getters, divergência de limites e semântica UTF-8 entre a preparação Graph e a M17, leitura de resposta Graph via propriedades não protegidas, roteamento GET/POST com campos mutáveis/getters fora da região segura e contagem CI rígida incompatível com os novos testes. Não houve evidência, nos módulos e testes revisados, de uma autorização legítima de produção surgindo a partir de fixtures; **isso não comprova ausência absoluta de falhas ou homologação operacional**.

**Base:** 73 módulos TypeScript de produção/laboratório e 79 arquivos `.test.ts` sob `integrations/whatsapp-meta/`, além de 129 documentos no diretório canônico de integração presentes no inventário inicial desta auditoria. Foram inspecionados o inventário completo, arquivos centrais de autorização/roteamento, Graph, ingresso, templates, consentimento, identidade humana, tentativas, status, WDC-13, recuperação e scripts PG17; foi feita varredura estática de condições de I/O, flags de autoridade e referências de testes/CI e revisão aprofundada dos fluxos de maior risco. **Não foi uma prova formal linha a linha, nem um pentest de rede nem homologação S0.**

## Achados corrigidos e controles novos

### AG-META-01 — roteamento de credenciais com getters, mutação e estrutura implícita

**Local:** `integrations/whatsapp-meta/credential-routing.ts`.

O caminho original `selectMetaCredential` / `resolveSignedMetaChannel` validava objetos fornecidos pelo host acessando diretamente campos de App, canais, slots, escopo e consulta. Mesmo sendo um laboratório, um objeto com getter malicioso podia executar código durante a seleção de referências de segredo ou provocar erro não tratado. Objetos mutáveis podiam alterar campos sem uma fotografia própria de dados.

**Correção:** snapshots locais por descriptors de **dados próprios**, protótipo simples, arrays densos limitados, escopos e campos estritos para cadastro e consulta. Getters, propriedades herdadas ou extras, arrays malformados e aliases de slot continuam rejeitados. O retorno apenas identifica um nome de slot; nenhuma credencial real é resolvida ou enviada. **10 regressões `AUD-GLOBAL-CRED-01..10`**, preservando seleção separada GET/HMAC/Graph e flags de produção falsas.

### AG-META-02 — conteúdo Graph diferente da fronteira de assinatura humana M17

**Local:** `integrations/whatsapp-meta/graph-outbound.ts`.

A preparação Graph de texto livre limitava o corpo a **4.096 code points**, enquanto a M17 usa limite conservador de **4.096 bytes UTF-8** e recusa normalização inconsistente e caracteres de controle/formatadores. Uma mensagem Unicode poderia satisfazer o limite da preparação Graph e exceder o limite operacional do laboratório M17, ou conter separadores/invisíveis capazes de alterar o texto visualmente apresentado.

**Correção:** limite conservador local em bytes UTF-8, texto NFC, proibição de controles/formatadores/surrogates isolados/separadores Zl/Zp, permitindo LF para parágrafos normais. Isso é **política de coerência LAB**, não afirmação de um limite universal da API Meta. **5 regressões específicas de Unicode/bytes**.

### AG-META-03 — leitura indevida de getters e formas ambíguas no classificador Graph

**Local:** `integrations/whatsapp-meta/graph-outbound.ts`.

O classificador Graph consultava `observation.kind`, `response_json.messages`, `message.id` e `response_json.error` diretamente. Objetos adversariais de ensaio poderiam executar getters ou provocar exceções; um `transport_error` com campos de resposta HTTP adicionais não era recusado pela própria camada WA-02A.

**Correção:** validação de formato do objeto de observação, acesso somente a propriedades de dados próprias, extração segura de `messages[0].id` e `error.code/subcode` e negativa de formas contraditórias. Na ausência de prova técnica bem formada, o resultado é `UNCERTAIN_EXTERNAL`, **sem retry automático**. HTTP 2xx com `wamid` continua somente `API_ACCEPTED` — jamais `sent`, `delivered` ou `read`. **7 regressões de objetos hostis/ambiguidade**, totalizando 12 novas no teste Graph junto ao achado AG-META-02.

### AG-META-04 — roteamento de webhook lido fora do snapshot seguro

**Local:** `integrations/whatsapp-meta/routed-webhook.ts`.

O GET e o POST inspecionavam `request.route`, `raw_query`, `raw_body` e `signature_header` antes de entrar no bloco protegido contra exceções. Uma propriedade com getter podia executar ação não prevista ou interromper a inspeção; rota fornecida como referência mutável podia variar durante a resolução assíncrona do slot HMAC.

**Correção:** captura inicial sem invocar getter, com campos próprios/dados e validação estrita da rota, preservando cópia do corpo POST antes das operações assíncronas. O roteamento usa a cópia local, nunca reclassifica `GET` ou `POST` como autoridade ACK. **8 regressões `AUD-GLOBAL-ROUTE-01..08`**, incluindo alteração da rota pelo resolver, getters aninhados e propriedades injetadas.

### AG-META-05 — contagem CI desatualizada após ampliação de cobertura

**Local:** `.github/workflows/meta-s0-ed25519-receipt-interop-offline.yml`.

O grupo de regressões de interface tinha **369 testes** e o pipeline exigia exatamente essa contagem. Os oito novos testes de roteamento elevaram o total a **377** e todos passaram, mas o job falhou até que sua asserção fosse atualizada. **Correção:** esperado atualizado para 377 testes/377 passes, preservando o requisito de zero falhas. O run intermediário de falha é parte do registro corretivo, **não** evidência de aprovação.

## Validação integrada

- **Base anterior:** `4f40b569f000fbe259244b59442e8dc4d158dedb`, [CI 41351345794](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41351345794): **1.982/1.982 Meta offline**, 18/18 PG17 históricos separados, dois jobs verdes.
- **Regressões da auditoria geral:** **30 casos novos** (credenciais 10, Graph 12, roteamento 8).
- **CI funcional pós-correções:** commit `dcb02d097233ccd38672903f849edfd066d66acd`, [CI 41358439295](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41358439295): **2.012/2.012 Meta offline**, **377/377 regressões de interface no job específico**, scanner lexical ACK aprovado, **18/18 PG17 históricos independentes**, dois jobs `success`.
- O grupo PG17 verifica **ingresso S0/Meta no PostgreSQL descartável**, não autentica WDC-13, F02, PRE_DISPATCH operacional, status real Graph, consentimento ou autorização de envio.
- Após o commit deste relatório, conferir o CI **no HEAD exato da branch** antes de registrar conclusão documental.

## Estado global dos marcos

| Faixa | Status auditado | Responsabilidade pendente |
|---|---|---|
| M01–M06 | `[x]` nos itens históricos de decisão, candidatos offline, CI e interoperabilidade S0/Meta em PG17 descartável | **Não** equivale à entrada/saída real homologada |
| M07–M08 | Proteções/ensaios offline; marco principal `[ ]` | ACK/escopo multicanal real ratificados por S0/Meta/Infra |
| M09–M13 | Inventário/identidade/ingresso/catálogo offline; marcos principais `[ ]` | #8 ativos e grants, #2 ingresso/ACK, #10 S0, propriedade/delegação Meta real |
| M14–M16 | Consentimento, prévia F02 e preparação de templates auditados apenas offline; marcos principais `[ ]` | #10 PRE_DISPATCH real, #7 F02, #8 assets e catálogo autenticado |
| M17–M20 | Assinatura humana, anteparo de Graph, duas projeções de status e WDC-13 **auditaram/simularam apenas LAB**; marcos principais `[ ]` | Identidade humana S0, Graph real, WA-39 status, WDC-13 e C09 transacionais sob S0 |
| M21+ | Não iniciados nesta auditoria | Handoff F01/F03; observabilidade, LGPD, escala, políticas externas e E2E/produção futura |

**Não existe integração produtiva** dos snapshots M17/M18/M19/M20 com uma autoridade S0 homologada. Não concatenar as saídas de módulos M19 como se fossem duas provas independentes; seus contratos são diferentes. Os hashes laboratoriais não são HMAC, assinatura de autor, recibo durável ou token de permissão. Um erro 131049, 2xx/wamid, timeout ou status sem fonte S0 não gera decisão comercial, WDC-13 ou C09.

## Discrepância documental remanescente

O checklist principal `docs/integracoes/whatsapp-meta/CHECKLIST_CONCLUSAO_META.md` permanece com a **linha principal legada M20**, que não detalha seu progresso offline. A ferramenta de edição havia bloqueado sua atualização em execução anterior; portanto, não declarar esse arquivo atualizado. A fonte de estado suplementar é [`M20_CHECKPOINT_AUDITADO_2026-11-01.md`](M20_CHECKPOINT_AUDITADO_2026-11-01.md), além do [mapa entre frentes](MAPA_INTERFRENTES_ISSUE4_2026-10-31.md) e do presente relatório. Essa pendência é **documental**, não foi convertida em permissão para mexer no checklist via atalho. Resolver a permissão/integração antes de usar o checklist principal como única fonte de verdade.

## Bloqueios externos que não podem ser “consertados” pela frente Meta sem autorização

1. **#8 / Infra:** cadastro, titularidade, App/WABA/número, vault, grants e credenciais operacionais versionadas.
2. **#2 / S0:** ingresso hospedado, HMAC autenticamente verificado, recibo/cursor durável, readback e regra HTTP/ACK.
3. **#10 / S0:** PRE_DISPATCH transacional, lease externo pós-commit, consentimento/opt-out e idempotência/recovery reais; reserva `pg17/0.1-lab-only` não permite Graph.
4. **#7 / OpenAI/F02:** planejamento de campanhas e templates com contrato ratificado, sem permissão IA para disparo.
5. **#9 / S0, Meta, Infra e OpenAI:** WA-39 status autenticamente correlacionado e projeção F02, falhas definitivas, WDC-13 e C09 **exclusivamente S0**.
6. **M21–M30:** handoff humano F01/F03, LGPD, observabilidade, escala, política Meta vigente, testes E2E real e homologação expressa antes de produção.

## Conclusão e próximo passo

**Correções da auditoria geral implementadas** na branch Meta com 30 regressões adicionais e CI verde. Os achados sanáveis dentro desta frente foram corrigidos; restam bloqueios interfrentes e a divergência documental conhecida. **Não é uma certificação universal “sem falhas”; é o parecer limitado aos módulos e contratos examinados e aos testes executados.**

A M21 pode ser **planejada e implementada apenas como laboratório**, mantendo F01/F03 e handoff real sob S0/S1. Para qualquer homologação/integração real, aguardar aceite interfrentes. **Nenhum Graph, envio, HTTP ACK de produção, SQL produtivo, segredo, efeito comercial, merge ou deploy** foi realizado nesta auditoria.
