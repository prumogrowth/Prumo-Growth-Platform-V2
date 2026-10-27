# META-S0-TEMPLATE-CATALOG-05 — 0.1-candidate

26/10/2026, America/Sao_Paulo. **CANDIDATO NÃO RATIFICADO. TESTES EXCLUSIVAMENTE FICTÍCIOS.**

Branch auxiliar exclusiva aux/meta-s0-template-catalog-05-20261026, base PR #15 / 45618df4fc135c33d59b087a98efd5ef53f30c04. Não modifica builders, migrations, backend S0 ou branches Meta/S1/Frontend. Não implementa transporte, envio, M2M, reserva, ACK ou locks.

## Diagnóstico e checkpoints

O handoff cloud-quick-reply-catalog-handoff-2026-10-26.md foi lido integralmente no HEAD do PR #15. Os dois builders, seus 42 testes originais e as bibliotecas/testes de catálogo WA17A/B e seleção WA25/26 foram inspecionados. Foram inventariadas as 38 migrations S0 do PR #18, buscando catálogos existentes.

| Fonte recuperada | HEAD | Checkpoint executável / CI histórico confirmado por GET |
|---|---|---|
| PR #15 Meta quick replies | 45618df4fc135c33d59b087a98efd5ef53f30c04 | b1d926c6cdee4de3d19676dd83182802b4dd5770 / 40403869847 success |
| PR #14 quatro contratos Meta/S0 | 31bb84fa524f4ecfdf02360988471d7f989506d7 | 92703c34fd4a2b9bae0d00768969c7c53cc16da3 / 40370618576 success |
| PR #16 S0 consolidada | b298252c26c69f668b3c3fdb86e9252faff9e44b | 8be6e194bfb5b8694c1010ff8560c8ec19ed4fd8 / 40405271785 success |
| PR #18 S0/F02 revisão | 88af4aea3aeb2c403bab4c078fdc04d560f2cba0 | 4a3d248d46fad5c195398324b3ee98ae6236365f / 40414847271 success |

PRs #9/#11 também recuperados como proveniência; #16/#18 são a continuidade S0 mais recente encontrada na coleção de PRs abertos, consultada sem alterar frentes. Timelines dos PRs #14/#15/#18 retornaram vazias pelo conector; nenhuma aprovação conjunta foi inferida. Certificações históricas são fontes de leitura, não testes novos desta tarefa. Paths/blobs e documentos consultados estão no source-manifest.json.

### Componentes existentes: aproveitar, não duplicar

| Componente | Papel já existente | Tratamento |
|---|---|---|
| graph-template.ts | Descriptor C06 TEXT, header/body/footer, parâmetros e cinco campos de escopo | Importação inalterada |
| graph-template-interactive.ts | Projeção sobre builder base, 1–3 QUICK_REPLY e catálogo offline.v1 | Importação inalterada |
| template-catalog-control.ts / WA17A | BODY legado, submissão/revisão e congelamento de fontes; status depende de sync confiado | Preservado; não virou fonte de aprovação |
| template-mcp-multiformat.ts / WA17B | Composição MCP, slots, labels, bindings e preview completo | Reutilizado para validar definição e mapear fontes; nenhum novo builder |
| template-purpose-eligibility.ts / WA25 | Finalidades, grants, seleção e recheck | Mantido separado; sem reimplementar políticas |
| s0-template-purpose-bridge.ts / WA26 | Portas fictícias scope/policy/catalog em PLAN/RESERVE/PRE_DISPATCH | Fonte de limites; não transação/identidade reais |
| catalogo_templates_sinteticos, migration 012 | id, loja, código, versão, aprovado_simulacao | **Não é aprovação Meta nem manifesto completo** |
| S0 PR #18 | Pedidos autenticados PENDING_EVIDENCE | Não comprova template, consentimento ou disposição Meta |
| S0 PR #16 / PR #14 | C1–C7 continuam pendentes; issuer/FileStore/ranks não operacionais | Preservados; não reutilizar principal humano como M2M |

A biblioteca WA17B substitui a diretriz antiga de autoria exclusivamente manual. Autoria HUMAN_SPECIFIED/AI_ASSISTED/AI_GENERATED não implica autorização ou aprovação. Não se cria editor, catálogo paralelo, tabela ou serviço de sync nesta tarefa.

## Bloqueio de origem autêntica

**Não foi encontrada, nas fontes recuperadas, uma implementação produtiva autenticada que entregue status Meta + identidade/revisão + manifesto completo atual.** WA17 tem transições puras que exigem sync confiado futuro; a tabela S0 é explicitamente sintética; WA26 injeta mocks; PR #18 armazena alegações de evidência. Não basta reaproveitar um booleano ou copiar a palavra APPROVED.

Origem proposta para ratificação, **não implementada**:

1. Adaptador administrativo Meta/Infra autenticado obtém status efetivo e definição completa para o provider_template_id exato, na App/WABA correta, com recibo de observação e tratamento de erro/perda de sync. Um 2xx de criação/submissão ou string fornecida pelo usuário não é aprovação.
2. Catálogo interno já previsto por WA17 vincula provider ID, nome/idioma, conteúdo/componentes observados e versão local imutável. Não supor que Meta emita template_revision_ref ou catalog_revision; são referências locais atribuídas pelo backend.
3. Binding S0 vincula concessionária, canal, App, WABA, phone e sua revisão. Compartilhar WABA ou template entre lojas não cria concessão cruzada.
4. Mapeamentos posicionais de fontes seguem o congelamento WA17B por versão aprovada. Política de payload QUICK_REPLY é **da Prumo/S0**, separada do status Meta.
5. Serviço de catálogo emite leitura consistente e cabeça atual, invalida ao receber pausa/rejeição/alteração e revalida no caminho de reserva/dispatch existente quando esses contratos forem ratificados.

Se listagem estiver paginada, reduzida, sem componentes ou sem prova de escopo, completar a recuperação pelo ID antes de declarar schema completo; nunca preencher por fixture, preview ou fallback do builder. Formato real de sync/recibo, autenticação, armazenamento, ACL e retenção dependem de decisões abaixo. Não se chamou Graph para resolver esse bloqueio.

**Caminho produtivo desta entrega:** readProductionTemplateCatalog(query) retorna sempre DENIED / SOURCE_NOT_IMPLEMENTED. Nenhum parâmetro habilita uma fonte real. createFixtureCatalogReader exige DISPOSABLE_CATALOG_05_ONLY e aceita somente origem LAB_FIXTURE / SYNTHETIC_NOT_META_APPROVAL. Um resultado laboratorial positivo permanece meta_approval_verified:false, production_authorized:false.

## Contrato de snapshot interno

Versão literal: **prumo.meta-s0.template-catalog/0.1-candidate**. DTOs readonly exportados em contract.ts: Scope, CatalogQuery, SupportedDefinition, CatalogRecord, CatalogHead, CatalogBundle. Entrada de fonte é unknown, validada em runtime; não receber snapshot supostamente confiável do browser/IA/ingressor.

### Consulta e identidade

Consulta exata: template_name, language_code, expected_template_revision_ref, expected_catalog_revision, expected_binding_revision. Escopo vem da composição do host confiado, separado da consulta. O catálogo não contém destinatário, consentimento, caso, versão de ciclo, concessão humana ou reserva de tentativa.

| Campo/grupo do registro | Tipo e semântica |
|---|---|
| contract | Literal versionado acima |
| scope | concessionaria_id, canal_id, meta_app_ref, meta_waba_id, phone_number_id, todos vinculados |
| binding_revision | Revisão local do vínculo técnico, independente do catálogo |
| catalog_revision | Revisão local de material: conteúdo/bindings/política; string decimal positiva canônica int64 |
| template_revision_ref | Referência opaca local para versão revisada; não é provider ID ou versão Graph |
| content_version / mapping_revision | Revisões locais congeladas da definição e fontes; não derivadas de case/cycle |
| provider_template_id | ID Meta correspondente; não prova status por si só |
| meta_status | APPROVED/PENDING/PAUSED/REJECTED/DISABLED; somente APPROVED permite teste estrutural positivo |
| schema_complete | true só tem valor probatório com fonte real completa; fixture afirma apenas cenário |
| parameter_format | POSITIONAL_TEXT_ONLY neste perfil |
| definition | Definição WA17B completa do subconjunto TEXT + QUICK_REPLY, incluindo textos e labels |
| approved_components | Manifesto completo normalizado do provedor, em ordem, sem campos omitidos/desconhecidos |
| mappings | Mapa posicional WA17B para fontes registradas pelo host; não são valores pessoais resolvidos |
| quick_reply_policy | Política Prumo STATIC_BACKEND_CATALOG, policy_ref/revision_ref e payloads por índice |
| source | Fonte/observação e instantes separados de status e manifesto; neste código apenas LAB_FIXTURE |

Não normalizar IDs, telefone ou idioma para procurar equivalência. O perfil WA17B aqui reutilizado admite idioma de duas letras com região opcional e WABA/phone numéricos; os builders podem aceitar domínios mais amplos. Esses casos mais amplos não são automaticamente aprovados pela interface candidata. Não converter revisões numéricas de outros domínios nem arredondar int64 para Number.

### Manifesto completo e integridade

Manifesto suportado: HEADER opcional de TEXT, BODY obrigatório, FOOTER TEXT opcional sem slots, BUTTONS opcional contendo somente QUICK_REPLY. Campo ausente/desconhecido, mídia/URL/PHONE_NUMBER/Flow/carrossel/NAMED ou quinto componente nunca é descartado para tornar o objeto compatível.

O adapter chama composeMcpTemplateDraft e mapMcpTemplateSources existentes para validar slots, posições contíguas, exemplos fictícios, labels, limites e registro de fontes. Usa prepareMcpTemplateReview para obter projeção de conteúdo; remove somente os exemplos de submissão antes da comparação. Exemplos não integram o manifesto normalizado de conteúdo aprovado. Textos, labels, tipos e ordem de todos os componentes restantes devem coincidir integralmente com approved_components. Um preview WA17B continua draft/meta_approved:false: é um validador de forma, não recibo Meta.

Não se recria a lógica de placeholder, autoria, mapeamento ou serialização Graph. O adapter restringe BODY a até dez parâmetros, de acordo com o builder já certificado; HEADER segue até um. Mapeamentos precisam cobrir todos os slots, sem fonte desconhecida/extras.

CatalogHead contém source_ref/source_epoch/record_sha256 e identidades/revisões/status do registro. SHA-256 é calculado sobre JSON UTF-8 de dados com chaves de objetos ordenadas lexicograficamente, arrays em ordem, strings preservadas, sem normalização Unicode. record_sha256 cobre registro inteiro, incluindo escopo, conteúdo, bindings, política e observações. **Hash não autentica fonte nem comprova aprovação**.

Entrada é copiada por own data descriptors: nega getters, símbolos, protótipos exóticos, arrays esparsos e excesso de estrutura. Orçamento de fixture: 16 níveis, 4096 nós, arrays 100, objetos 64 propriedades e strings 8192 unidades UTF-16. Não é orçamento de parser público ou requisito produtivo ratificado.

### QUICK_REPLY: definição Meta e payload S0

Meta define tipo/ordem/label dos botões aprovados. Os valores opacos enviados como payload são uma política local distinta; **não se afirma que Meta aprovou cada payload**. O registro deve ligar essa política versionada ao manifesto exato e às fontes congeladas.

Perfil implementado: 1–3 QUICK_REPLY quando há botões; índices inteiros exatos 0..n-1, quantidade igual à definição completa. Payloads estáticos de catálogo [A-Za-z0-9_.:-], 1–128 caracteres. Campos extras, parameters arbitrário, payload dinâmico/URL/texto do usuário e índices ausentes/duplicados/strings são negados. A gramática não comprova ausência de PII; a governança do registro opaco continua necessária.

Template TEXT sem botões só usa o builder base se o manifesto completo confirmar ausência de BUTTONS e a política estiver vazia. Nunca fazer fallback retirando botões de um template interativo. Requisito futuro de payload dinâmico assinado exige contrato próprio: não implementado ou ratificado aqui.

### Atualidade, rollback e imutabilidade

Ambas as observações (status e manifesto) devem ser atuais, não futuras, com now - observado < maxAgeMs. maxAgeMs é parâmetro explícito da fixture, sem TTL produtivo/default comercial; limite local até uma hora só delimita teste. O clock do reader não pode regredir.

Cada preparo relê a fonte, não usa apenas o snapshot cacheado. Pausa/rejeição/expiração/revisão/binding divergente bloqueiam; nenhum snapshot anterior ganha uso por continuar dentro do TTL. A geração source_epoch identifica mudanças de observação/estado. Mesmo refresh de conteúdo igual exige novo handle.

No mesmo reader, epoch/catalog/binding não podem regredir; uma geração não pode mudar bytes. Uma versão template não pode alterar conteúdo/categoria/provider ID/mapping/content_version. Uma policy_ref/revision_ref não pode trocar payloads. Alterar política requer nova revisão de política e material de catálogo; não requer inferir nova aprovação Meta se só payload local mudou. source_epoch pode mudar status ou renovar observação sem mudar definição.

Também são lembradas observações válidas de negação, como PAUSED, para rejeitar replay posterior de APPROVED antigo. Esses watermarks/mapas são **voláteis e locais**; não são ledger durável ou proteção distribuída. O serviço real deverá persistir revisões e invalidar caches sob concorrência no caminho aprovado. Instantes e head fornecidos por mock não atestam realidade externa.

## Projeções e consumo dos builders

read(query) retorna DENIED com motivo sanitizado, ou LAB_CATALOG_VALIDATED com snapshot congelado e flags falsas. O próprio objeto retornado é vinculado ao reader por WeakMap. JSON clonado, objeto externo ou handle de outro reader são negados; não é bearer nem artefato serializável para outro processo.

prepare(handle,intent,apiVersion) copia intenção antes de await, relê fonte/head e só então gera:

- TrustedTemplateSnapshot de TEXT, **projeção**, não evidência independente de completude global;
- TrustedQuickReplyCatalog com literal histórico prumo.meta.quickreply.catalog.offline.v1, proveniente do mesmo registro; ou null no perfil TEXT sem botões;
- descriptor inerte devolvido por prepareGraphQuickReplyTemplateRequest ou prepareGraphTemplateRequest, sem reimplementar builders.

O antigo campo schema_complete:true da base permanece compatível com seu contrato de projeção TEXT. O manifesto completo pertence ao novo registro e deve justificar as duas projeções juntas. Não produzir base de uma revisão e botões de outra. Não reutilizar um snapshot serializado como fonte confiável.

Intent/receptor/valores de texto são entradas internas **fictícias** nestes testes. Resolução real dos valores contra as fontes registradas pertence ao backend autorizado; esta interface não atesta de onde vieram valores pessoais. Os builders continuam a validar tipos/quantidades/conteúdo dos parâmetros. Eles retornam estruturas sensíveis com destino/texto: não logar descriptor em operação real.

Todas as decisões mantêm send_authorized, production_authorized, ack_allowed, retry_automatically, commercial_effect_authorized e meta_approval_verified falsos. Aprovação técnica de template não resolve finalidade, consentimento, opt-out, janela, concessões, autorização C06, case/cycle ou ocupação da tentativa. WA25/26, S0/S1 e contratos candidatos PR #14 conservam essas fronteiras.

## Implementação e evidência

Arquivos auxiliares: contract.ts (tipos e bloqueio produtivo), adapter.ts (leitura/verificação/projeção de fixture), fixtures.ts (somente dados fictícios), catalog.test.ts, source-manifest.json e verify_sources.py. Não há SDK, credencial, banco, HTTP, M2M novo ou migration. O cache local de fontes usado para desenvolvimento não é parte da branch nem um catálogo operacional.

**42 testes novos**: fonte ausente/não confiada, escopo completo, manifesto parcial/divergente, status, índices/quantidades/payloads, parâmetros, int64, integridade, clocks/TTL, pause/replay, revisão imutável, clone de handle, isolamento de memória e await. **120 regressões originais**, sem alterar arquivos: builders 24+18; WA17A 18; WA17B 16; WA25 18; WA26 26. Não reexecuta DISPATCH/ACK/LOCK, WA39–68 ou as suítes PG/GoTrue históricas.

Local: Node 24.19.0, fontes materializadas pelo conector e 13 blobs byte a byte conferidos. Git fetch não conseguiu conectar ao proxy; a branch/remoto são tratados pelo conector. O runner local com subprocessos contabilizou apenas um arquivo, por comportamento do ambiente, e não foi usado como prova de 42 testes. Execução com test-isolation=none produziu TAP de 42/42 e 120/120, sem skips. CI separado Node22.23.3 SUCCESS no SHA e8b49faea3fe11ebc1001600cb271e92009a5bce, run 40433120503: 42/42 novos + 120/120 originais e 13/13 blobs, logs conferidos. Detalhes em EVIDENCIAS.md/JSON.

## Decisões pendentes para ratificação

| ID | Titular proposto | Artefato objetivo necessário |
|---|---|---|
| T1 — fonte autêntica | S0 + Meta/Infra | Serviço/recibo de sync autenticado: status e manifesto completo pelo provider ID/App/WABA, falha de sync/paginação e auditoria |
| T2 — versões e vínculo | S0 + Meta/S1 | Mapeamento local template/content/mapping/catalog/binding/source_epoch e entidades reais; nenhuma versão Meta inventada |
| T3 — normalização e completude | S0 + Meta | Perfil de GET/status real → manifesto sem perda; exemplos vs conteúdo; componentes novos exigem nova versão/validator |
| T4 — payloads opacos | S0 + Produto/Privacidade | Fonte/política/revisão de valores estáticos, efeitos dos choices, isolamento por loja e retenção; dinâmicos separados |
| T5 — atualidade e invalidação | S0 + Infra/Meta | SLO/TTL/clock, entrega de eventos, watermarks duráveis/cache e recheck consistente na reserva/pre-dispatch ratificados |
| T6 — integração e acesso | Codex principal + S0/S1/Meta | ACL técnica/finalidade, contrato de transporte e consumo; manter C1–C7 e DISPATCH/ACK/LOCK pendentes |

Todos PENDENTES. Nenhuma escolha de fixture aprova regra comercial ou operação. Próxima etapa: ratificar fonte/revisões e implementar seu adapter no catálogo existente com testes físicos/observações de sandbox autorizados separadamente. Não promover createFixtureCatalogReader nem liberar Graph substituindo uma flag.

## Reprodução e encaminhamento

~~~sh
python3 integration/meta_s0_template_catalog/verify_sources.py
NODE_OPTIONS='' NODE_PATH='' node --experimental-strip-types --test --test-reporter=tap --test-concurrency=1 integration/meta_s0_template_catalog/catalog.test.ts
~~~

Node22.23.3 no CI; local Node24 pode requerer --test-isolation=none. Workflow auxiliar lista os seis arquivos das 120 regressões. Não precisa npm install, Docker, Supabase, DSN, JWT ou token Meta.

Ler também CONSUMO_FUTURO_META.md e EVIDENCIAS.md. O Codex principal avalia diff/proveniência, T1–T6 e limites antes de integrar. **Sem merge, deploy, Graph real, Supabase hospedado, credenciais reais ou integração final.**
