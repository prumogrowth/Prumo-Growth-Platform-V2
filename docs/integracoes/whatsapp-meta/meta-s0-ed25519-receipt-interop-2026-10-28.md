# Meta × S0 — verificação Ed25519 de recibo LAB (compatibilidade PR #48)

**Data:** 28/10/2026. **Fonte S0 consultada somente em leitura:** [PR #48](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/48), branch `exp/s0-meta-ingress-01-20261028`, HEAD documental `cb4a43480df0e71cfe497e528d3519b2043201ac`, código certificado `9e3077d222df2b3184ee6ea568fdac7c9da75567`, [CI #40730388157 SUCCESS](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40730388157). Fontes exatas: `integration/s0_meta_ingress/protocol.py`, `ingress.py`, `schema.sql`, `CONTRATO_CANDIDATO_V1.md`, `MATRIZES_E_INTERFACES.md` e `CHECKPOINT.md`.

**Base Meta:** PR #47, SHA `6ea8cef9fed6351cfb09efb91dc970889d07e1c9`.

## Resultado de recuperação do Codex/S0

O PR #48 concluiu a **frente S0_META_INGRESS_01_LAB_CLOSED** (não produção): M2M Ed25519, Meta HMAC sintético verificado à parte, PostgreSQL 17.6 com commit e readback, autenticação/escopo técnico por canal, lote multicanal na **mesma App e concessionária** e recibo S0 Ed25519 reconstruível. A S0 apresentou 49/49 testes físicos, 213 modelos/regressões, 12 testes de escopo e regressões backend/FS. O SHA documental posterior usa `[skip ci]` e não equivale a uma segunda certificação do código. O laboratório usa chaves efêmeras/isoladas e não concede `HTTP 200` externo, envio, atendimento, autorização comercial, direitos humanos, migrations produtivas nem serviço hospedado.

**Diferença de contrato importante:** o PR #48 não retorna o recibo antigo `meta-s0-receipt.v0.1-proposed` baseado em campos `COMMITTED`; emite `{body,signature}`, com assinatura Ed25519 sobre o domínio ASCII `PRUMO/S0-META-INGRESS/RECEIPT/LAB/v1\0` mais JSON canonicalizado segundo Python `json.dumps(...,sort_keys=True,separators=(',', ':'),ensure_ascii=False,allow_nan=False)`. O consumidor **não pode confiar na chave pública copiada de dentro do recibo**. A chave deve estar previamente fixada por uma fonte confiável independente.

## Novo leitor da frente Meta

`integrations/whatsapp-meta/cloud-s0-ed25519-receipt-interop.ts` oferece `inspectPinnedS0LabReceipt(rawBody,receipt,trustedExpected,trustedS0PublicKey)`, **somente laboratório e sem I/O**.

- Recebe **bytes físicos originais** do webhook, chave pública raw Ed25519 de 32 bytes **pré-fixada pela camada confiável** e contexto técnico confiado: App, rota, revisão (decimal string), instância S0, identidade/revisão do signer, emissor/chave/revisão do principal M2M original, contagem e lista exata de `(waba,phone,channel,tenant,revision)` esperados.
- Verifica esquema fechado do recibo S0 (versão, `DURABLY_COMMITTED` assinado, estado de não produção, campos obrigatórios, UUIDs de ocorrências únicos, contagem 1–100, digest dos bindings, identidades e revisão). Confere `raw_sha256` contra os bytes físicos da própria chamada.
- Confere `receipt_public_key` embutida contra a âncora fornecida separadamente; cria uma chave pública SPKI Ed25519 a partir dos 32 bytes confiados e verifica a assinatura **sobre o domínio exato e JSON canônico**.
- Mantém `ack_allowed`, `http_ack_allowed`, `http_response_authorized`, `production_authorized`, `durable_receipt_verified`, `commit_verified`, `m2m_verified`, `send_authorized`, `s0_write_authorized`, `replay_suppression_authorized` e demais flags **false**, inclusive quando a assinatura confere. `S0_LAB_SIGNATURE_AND_CONTEXT_MATCH_UNRATIFIED` significa **somente** consistência criptográfica/local com a âncora suprida, não comprovação autônoma de commit ou fonte do trust anchor.
- Não autentica Meta HMAC da requisição, principal M2M emissor da chamada, revalidação em DB, mutadores do registry, política HTTP ou status operacional. Essas garantias exigem componentes/contratos independentes antes de qualquer ACK.
- A implementação de canonicalização é deliberadamente restrita a chaves ASCII, inteiros seguros, texto UTF-8, objetos/arrays acíclicos sem getters. Um documento válido em Python com formato fora desse subconjunto é recusado conservadoramente, **não normalizado silenciosamente**. É necessário homologar demais casos S0 sob ambiente conjunto antes de ratificar produção.

## Teste de interoperabilidade e limitações

`cloud-s0-ed25519-receipt-interop.vector.json` contém vetor público sintético **gerado independentemente em Python** com o domínio Ed25519 e algoritmo `canonical()` da especificação do PR #48. Não contém chave privada nem dados reais e **não é um recibo capturado de PG17/S0 real**. O vetor foi verificado isoladamente em Node.js com `crypto.verify` e digest Python/Node de bindings idêntico. Este teste é de algoritmo/contrato, não de E2E com serviço PostgreSQL da S0.

`cloud-s0-ed25519-receipt-interop.test.ts`: 36 testes com assinatura válida, flags não autoritativas, chave incorreta/autossugerida, assinatura adulterada, escopo da rota/App, revisão/instância, bytes físicos e whitespace, binding/canal/concessionária/phone/revisão, contagem, timestamp, provas `COMMITTED` falsas, propriedades extras/getters, ausência de âncora e replay.

`.github/workflows/meta-s0-ed25519-receipt-interop-offline.yml` exige **36 novos + 369 regressões focadas = 405 testes**, mais o scanner estático de referência ao helper de ACK anterior. Esta entrega **só poderá ser chamada certificada após CI SUCCESS no HEAD exato**. Uma falha do workflow sem logs não prova falha nem sucesso dos testes; registrar como **CI_INDETERMINADO** até evidência verificável.

## Solicitações restantes e ownership

| Destino | Necessidade | Situação |
|---|---|---|
| Meta/Infra + S0 | Homologar um vetor assinado **gerado pelo runtime PG17** do PR #48 consumido pelo verificador Meta, em execução isolada | Próxima auditoria de interoperabilidade; sem mudar fontes S0 |
| Meta/Infra | Desenvolver ingressor real externo, custódia/âncoras Ed25519, HTTP/TLS, retry, limites, isolamento, fonte de App Secret | **Pendente de contrato de produção** |
| S0/Infra | Registro real de chaves, canal, App, revisão; HA/readback, retenção LGPD, política de invalidos/backpressure | **Pendente produtivo**, sem correção imediata do código LAB comprovada |
| S0/Meta | Catálogo PR #19 e autorização de envio/negócio | Fora do escopo do ingresso e da presente verificação |

**Regra de isolamento:** esta branch adiciona somente código/testes/docs/workflow da frente Meta. Nenhum arquivo, PR, branch, migration, SQL, credencial, serviço ou código S0/S1 foi editado; PR #48 continua Draft e seu laboratório permanece não produtivo. Sem merge, deploy, envio, Graph, webhook público, HTTP ACK ou testes contra usuários reais.

## Atualização de continuidade — 28/10/2026

- O contrato esperado da Meta foi tornado mais restrito: `m2m_issuer`, `m2m_key_id` e `m2m_key_revision` passaram a ser campos obrigatórios da **expectativa confiada**, conferidos com o corpo S0 criptograficamente assinado. Os testes INTEROP-33 a INTEROP-36 negam identidade ou revisão M2M divergente e revisão não canônica. Essa melhoria não altera o S0 e não concede direito de ACK.
- **Comprovação criptográfica independente no ambiente de auditoria:** Python/cryptography verificou a assinatura Ed25519 do vetor sem importar o código Meta; Node.js 22 verificou a mesma assinatura com chave pública SPKI e rejeitou bytes adulterados; SHA256 dos bytes físicos = `9738e94f102f69ef2d58c6fb3460bb30846c833ac8b161e5e0594d62e38a6042`; SHA256 canônico dos bindings = `c5f0316ce941fd73f330a3283580de9562426601660992053921d385f2fc96be`. Isso é **prova isolada do vetor**, não execução da suíte Node completa, nem recibo físico do runtime S0.
- O GitHub Actions na branch Meta continuou `FAILURE` antes de apresentar qualquer etapa executada. Exemplo: [run 40788902824](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40788902824), concluído em aproximadamente quatro segundos com job de `steps=null`. Os logs retornaram `BlobNotFound` nas tentativas de inspeção. A [frente I86 manual / PR #51](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/51) relatou independentemente o mesmo bloqueio anterior à atribuição do runner. **A causa raiz da infraestrutura não foi comprovada; não atribuir automaticamente a cobrança/franquia.**
- Os 405 testes (36 novos + 369 históricos) **não estão certificados no HEAD atual**. Nenhum skip ou bypass de gate foi introduzido. Exigir execução real com logs, 0 falhas e CI SUCCESS após restabelecimento do executor.
- Uma prova de ponta a ponta com recibo criado pelo `Ingress.call()` físico PostgreSQL17 do PR #48 **ainda não aconteceu**. A equipe de orquestração deverá validar essa interoperabilidade e, somente após ratificação da arquitetura/custódia, discutir política HTTP com S0/Meta/Infra. A própria S0 permanece LAB_CLOSED, não produtiva.
