# AUDITORIA — Composição Meta Cloud, mutabilidade assíncrona e custo de processamento

**Data:** 27/10/2026. **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`. **Base auditada:** PR #34 (`c1143ec62160d47ba0177e28187fad1433bb403f`). **Branch de auditoria:** `audit/meta-cloud-composed-snapshot-performance-20261027`.

## Escopo e métodos

Auditoria de segurança/correção concorrente e desempenho **somente offline** da leitura composta `inspectSignedMetaComposedWebhook()`, do verificador compartilhado `inspectCloudWebhookForHandoff()` e do leitor de reação que o consome. Dados, chaves e eventos são sintéticos. Não foi realizado teste de carga de produção, nem GET/POST Graph API, Supabase, webhook HTTP público ou envio.

Foi confirmada a árvore GitHub certificada do PR #34 antes de modificar código. Reaproveitamos os leitores anteriores, sem substituir parser base, HMAC real, políticas comerciais ou decisões S0.

## Achado A1 — Escopo e limites mutáveis entre awaits

**Classificação:** defeito reproduzido de segurança da fronteira técnica (integridade de escopo); criticidade operacional depende de como o host futuro fornecerá objetos de configuração. **Não é prova de exploração externa.**

O compositor original guardava referências para `trustedRoute` e `limits`, sem capturar seus valores antes das operações assíncronas. Os leitores recapturavam tais referências após `await`, de modo que o escopo WABA/phone e a política de limites poderiam divergir dentro de uma única inspeção.

Prova RED de adversarial audit: [run #40584914309](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40584914309). **Quatro testes falharam na versão original**, incluindo a aceitação de uma solicitação cuja rota confiável original não correspondia ao callback assinado, após alteração da rota durante o HMAC. Também foram reproduzidas negações indevidas com alterações midflight em rota e limites.

**Reparo:** `cloud-composed-observation-handoff.ts` tira `Object.freeze` snapshots **dos valores primitivos** `waba_id`, `phone_number_id`, `revision`, `maxBodyBytes` e `maxEvents` antes do primeiro `await`; uma única cópia do corpo continua sendo utilizada. Esses valores estáveis são passados ao verificador base e aos cinco leitores especializados. Não é introduzida forma de contornar autenticação.

## Achado A2 — Mesmo risco no verificador compartilhado, quando usado sozinho

A função `inspectCloudWebhookForHandoff()` também aceitava a rota confiável por referência até depois da verificação assíncrona. Esse código pode ser utilizado **diretamente** por outros consumidores, inclusive pela leitura de reações.

Prova RED complementar: [run #40585337343](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40585337343). **Três testes novos falharam**, demonstrando tanto aceitação incorreta como negativa incorreta ao mudar a rota durante o HMAC. Um teste comprovou o mesmo comportamento pela chamada direta ao leitor de reações.

**Reparo:** `cloud-webhook-handoff.ts` também captura e congela uma cópia primitiva de `trustedRoute` e `limits` antes de esperar a verificação HMAC. A checagem de escopo após o HMAC utiliza exclusivamente essa cópia; `route_revision` também corresponde ao snapshot inicial. Os cinco leitores anteriores continuam chamando o mesmo verificador, sem novos bypasses.

**Limitação:** esta auditoria não certifica todas as outras rotas históricas de ingresso Meta (por exemplo `routed-webhook.ts` com portas S0 fake) ou integração produtiva. A solução se aplica às funções concretamente testadas nesta branch.

## Provas GREEN, invariantes e limites

[CI Green #40585443312](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40585443312) no commit de correção `0cae14bdd4d7da8f3c753a0264f9e4aa724c89a0`:

- **17/17** testes adversariais: mutações de rota/limites após invocação, isolamento de escopo em paralelo, view de bytes original alterada pelo chamador, verificação HMAC, eventos repetidos, múltiplas changes, volume de 100 eventos, negativa integral no 101º, limite exato de bytes, manipulador de getter hostil.
- **174/174** regressões focadas: composição, falhas de status, unsupported inbound, mídia, reações, seleções e ingress/HMAC anteriores.
- Todos os testes produziram zero falhas após os reparos.
- A política de `ack_allowed=false`, `s0_write_authorized=false`, `send_authorized=false`, `retry_external=false` e `exactly_once_guaranteed=false` foi mantida.

Essas provas são suficientes para afirmar que **a falha reproduzida neste escopo foi corrigida no laboratório**, não que a plataforma está autorizada para produção.

## Achado A3 — Custo mensurado, não defeito de segurança

A composição atual usa **6 verificações HMAC**, além de múltiplas decodificações e parses JSON: uma verificação do leitor genérico mais uma para cada um dos cinco leitores especializados. O benchmark compara o caminho genérico único ao caminho de composição, medindo o tempo integral de cada função — **não isola matematicamente o custo exclusivo de HMAC**.

Benchmark reprodutível: `integrations/whatsapp-meta/cloud-composed-performance-audit.ts`. Execução Green acima; Node.js 22, runner hospedado GitHub, warm-up de 12 iterações por modo e **40 amostras por modo** em ordem alternada; payloads sintéticos.

| Eventos | Tamanho do payload | Genérico p50 (ms) | Composto p50 (ms) | Razão p50 | Composto p95 (ms) |
|---:|---:|---:|---:|---:|---:|
| 1 | 351 bytes | 0,054 | 0,360 | 6,62× | 0,732 |
| 25 | 3.307 bytes | 0,112 | 1,121 | 10,03× | 4,379 |
| 100 | 12.609 bytes | 0,254 | 2,279 | 8,96× | 4,859 |

**Interpretação:** a sobrecarga é real, mas as medidas são diagnósticas. Resultados variam com ruído de CI, JIT, CPU, concorrência, distribuição dos tipos de callback e tamanho dos corpos. Não se pode inferir p95 de produção, throughput de servidor, equivalência mobile, SLA ou custo fixo 6× de cada HMAC. Nenhum limite temporal rígido foi colocado no CI porque a máquina hospedada tem ruído e isso incentivaria conclusões falsas.

### Recomendação

Não eliminar as HMACs duplicadas agora: os leitores especializados atuais **não aceitam** um tipo/artefato interno de verificação já autenticada. Uma redução segura exigiria uma interface de snapshot autenticado, lacrada e escopada, revisão da cadeia de confiança, testes de replay/mutação/escopo, testes comparativos com a versão de seis HMACs e autorização de arquitetura para integração real. Essa melhoria pode ser estudada numa próxima tarefa técnica independente; **não é necessária solicitação S0 nova agora** para manter o laboratório.

## Governança

Arquivos da auditoria: `cloud-composed-security-audit.test.ts`, `cloud-composed-performance-audit.ts` e workflow `meta-cloud-composed-audit-offline.yml`; reparos restritos aos dois módulos de inspeção. Nenhuma alteração em S0/S1, schema, banco produtivo, credenciais ou serviços externos. PR permanece Draft, sem merge/deploy/ACK operacional. Contratos candidatos S0 dos PRs #14 e #19 continuam sem ratificação.

**Atenção:** qualquer novo commit documental exige nova verificação de CI no SHA final; o sucesso #40585443312 foi obtido no SHA explicitado acima, e não certifica automaticamente commits posteriores.
