# LiberaCred — Auditoria transversal da frente S0/S1 (01/11/2026)

**Status:** `AUDITORIA_CONCLUIDA_COM_AJUSTES_PRIORITARIOS`. **Não homologar integração operacional.**  
**Base congelada auditada:** `45f15c831c3f6a7479a686622d92247f07005000` (S0 PRE_DISPATCH v0.2 → Meta M18).  
**Branch exclusiva de auditoria:** `audit/s0s1-cross-frontier-20261101`.  
**Código de implementação modificado pela auditoria:** **nenhum**. Apenas teste de contraprovas, workflow e este relatório.  
**Objetivo:** identificar conflitos/invariantes frágeis precocemente, não promover ambientes nem declarar a frente inteira incorreta.

## 1. Parecer executivo

**A orientação geral está alinhada; a consistência transversal ainda NÃO está pronta para o próximo salto operacional.** Os incrementos preservam isolamento experimental, tranches de autorização, cinco revisões M09, exceção/controle humano, diferenciação entre `STAGED` e `COMMITTED`, consentimento e ausência de efeitos comerciais antes de fonte autorizada. Há regressões específicas com PG17 real e checagens dos consumidores originais. Testes verdes provam somente os invariantes exercitados.

A auditoria **demonstrou cinco contraprovas físicas** no readback/cancelamento do PRE_DISPATCH v0.2 sob PostgreSQL 17 descartável. Todas as respostas continuam **sem Graph/send/produção**, portanto são **falhas de coerência e de revalidação candidatas**, e **NÃO** prova de que uma mensagem foi efetivamente disparada ou um dado real exposto.

**Deliberação sugerida:** adiar a próxima integração de autenticação/handoff M18-D; fazer incremento corretivo isolado `S0-PD02-AUD-FIX`, preservar contratos versionados, provar as negativas com PG17 e obter revisão Meta #10; depois reavaliar sequência de identidade hospedada. Não interromper trabalho de desenho em outras frentes nem fazer merge/deploy.

## 2. Base do produto e autorização

A fonte de produto [`projeto_liberacred_consolidacao_ideias_v0_2_auditada.md`](fonte de projeto, 10/10/2026) prioriza nova operação comercial terceirizada, segregação de carteiras por concessionária, IA Vendedora versus IA Analista que altera só configurações externas autorizadas, IA Gestora e orquestrador determinístico; aprendizado com evidência e aprovação, privacidade e rastreabilidade. Banco Yamaha: manifestação favorável de gerente **somente relatada verbalmente**; não há autorização escrita de cadastro, automação financeira ou acesso a sistemas do banco. Remuneração ~2,5% **hipótese não confirmada**. A direção é multi-loja com humano responsável por atos sensíveis, não um produto apenas SaaS.

O documento de 10/10 inicialmente dizia planejar sem implementação; a decisão **posterior** de 01/11 `AUTORIZADO_DESENVOLVIMENTO_ISOLADO` ratifica branch/CI/PG17 sintético e coordenação, **sem** permitir host/Supabase produtivo, Graph, credenciais, dados reais, migração, merge, operação bancária ou comercial. [Decisão e matriz de responsabilidades](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/95186006964f2e29b330164b5cda189fa65768aa/docs/contratos/s0s1_meta_registry/DECISAO_ESCOPO_INTEGRACAO_FRENTES_2026_11_01.md). Não há conflito de autorização entre as duas datas quando se respeita a cronologia.

## 3. Contraprovas REPRODUZIDAS em PG17 (achados próprios; prioridade P1)

[Suíte de auditoria apenas de testes](../..//audit/s0s1_20261101/test_pg17_counterexamples.py), [CI 41352399455](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41352399455) no SHA preliminar `47adca9b95e3a7f1eaa3929d05a984388b604dce`: 2/2 jobs `success`. **Cinco contraprovas = cinco defeitos observáveis**, não cinco provas de correção. A execução carrega também 27 testes v0.2 importados no módulo, mais regressões v0.2, v0.1 e M09 (27/24/18); esses testes repetidos não são contabilizados como novos. O workflow valida que NENHUM arquivo da implementação auditada foi modificado.

**AUD-PD-01 — Readback perde vínculo de finalidade do template (P1).** Após `reserve` e `COMMIT`, alterar `s0_pre_dispatch_lab.templates.template_purpose_ref` sem elevar `revision` permite que `readback` ainda retorne `LAB_COMMITTED_RECEIPT_NO_DISPATCH`. A reserva original exige a igualdade de finalidade; o readback posterior não. **Prova física:** `test_01_template_purpose_modified_without_revision_not_detected`. Código original: `integration/s0s1_pre_dispatch/pg17_service.py` (`_check`: linhas ~130–135); código v0.2: `integration/s0s1_pre_dispatch_v02/pg17_service.py` (readback: ~233–255). **Correção:** conferir a finalidade da fonte e confrontar com `request` original/recibo; proteger os campos de alterações silenciosas em escritores reais.

**AUD-PD-02 — Readback perde vínculo de finalidade do grant (P1).** Mudar `s0_pre_dispatch_lab.grants.template_purpose_ref` sem alterar `revision` também preserva `LAB_COMMITTED_RECEIPT_NO_DISPATCH`. `_check` original exige a finalidade; readback só compara `grant.active` e `revision`. **Prova:** `test_02_grant_template_purpose_modified_without_revision_not_detected`. **Correção:** revalidar finalidade e identidade completas do grant e tornar mudanças de escopo sempre versionadas / auditadas.

**AUD-PD-03 — Readback M09 parcial ignora escopo do número no grant (P1).** Alterar `s0_m09_lab.grants.phone_number_id` do emissor `200001` para `299999` sem revision bump é **detectado na porta M09 point-of-use original**, mas **não** no readback v0.2: ele confere App, cinco contadores e binding phone, porém não confronta `grant.phone_number_id` nem `grant.waba_id/route_ref`. **Prova:** `test_03_m09_grant_phone_modified_without_revision_not_detected`. **Correção:** reusar função de verificação integral *read-only* M09 ou projetar checker transacional comum, sem registrar check externo fictício; preservar lock/ordem e tenant.

**AUD-PD-04 — Readback aceita perda de quota/slot por reset silencioso (P1).** Depois de consumir o slot 1, redefinir `quotas.consumed=0` sem alterar `revision/observed_at/valid_until` preserva a confirmação de recibo com `quota_slot_recorded_lab_only=1`. O readback v0.2 não prova que o contador ainda cobre o slot reservado; o registro original de quota não possui journal independente de eventos consumidos. **Prova:** `test_04_quota_counter_reset_without_revision_not_detected`. **Correção:** controle monotônico ou ledger de debits/slots por intento; comparar slot, revisão, período, transação e evitar resets destrutivos, inclusive via gatilhos/ACLs. Atenção a quota operacional real ≠ quota PG17 fixture.

**AUD-PD-05 — Cancelamento aceita WABA divergente (P1).** Um `HostScope` com mesmo store/App/route/channel/phone, porém `waba_id` alterado, consegue `LAB_CANCEL_STAGED_BEFORE_COMMIT` e cancela o recibo. O `cancel` compara cinco campos e **não** o WABA nem `principal/issuer/autoridade`. **Prova:** `test_05_cancel_accepts_different_waba_in_supplied_scope`. **Correção:** chave de autorização completa + principal atestado, escopo de WABA e digest original, com teste cross-tenant/cross-App e revogação. A prova usa admin sintético, não um agente externo real.

**Interpretação obrigatória:** esses testes foram construídos como **contraprovas** que passam *quando uma lacuna permanece*. A CI verde **não** significa que os cinco controles estão corretos; significa que os comportamentos indesejados foram demonstrados de modo reprodutível em PG17. Após correções, inverter testes para exigir `DENIED/STALE` e manter regressão negativa permanente. Não há evidência de exploração, violação de dados reais, Graph real ou incidente comercial.

## 4. Riscos estruturais transversais (P1/P2; verificados em código/documentação, nem todos com contraprova dinâmica)

| ID | Pri. | Verificação | Risco / medida antes de operar |
|---|---|---|---|
| AUD-ARQ-01 | P1 | `readback` v0.2 executa múltiplos `SELECT` independentes sem snapshot/lock comum (`pg17_service.py` ~188–290). | Mudança concorrente de fonte entre leituras pode produzir fotografia incoerente. Em sistema hospedado: transação read-only com isolamento/locks compatíveis com escritores reais, prova CAS, readback e cancelamento coordenados; ensaiar mutações concorrentes/ABA. |
| AUD-ARQ-02 | P1 | `S0-M18` v0.2 não emite identidade/hashes/revisões autenticados vinculando `stage` e `readback`; o adaptador de Meta retorna `unbound_to_meta_attempt=true` e `m18_dispatch_candidate=null`. | É uma **proteção correta no laboratório**, mas contrato incompleto. Nunca promover `durable_lab_observed` a prova de um intento específico. Formalizar (attempt/intent/selection/nonce/digest/scoped principal), canonicalização e trust anchor. |
| AUD-ARQ-03 | P1 | M18 original Meta só aceita S0 v0.1 (`prumo.s0.pre-dispatch.pg17/0.1-lab-only`); a v0.2 é recusada explicitamente. M09 5 revisões independentes vs `registry_revision` escalar; `concessionaria_id` Meta UUID vs `store-A` fixture S0; template/version/content/recipient não têm mapeamento ratificado. | **Não converter por renomeação**. Versionar projeção específica M18-D ratificada pelo consumidor, com mapeamento semântico e testes adversariais, sem implicar que certificado Meta ou consentimento tenha sido comprovado. |
| AUD-ARQ-04 | P1 | No checkpoint GitHub do auditado, `main` vs `45f15c8` aparecem **683 commits ahead e 2 behind** (`compare_commits`, `status=diverged`). | Risco de dívida de integração/branch proliferação e conflito futuro. Montar manifesto de SHAs/ancestrais e matriz de contratos aceitos antes de rebase/merge; não interpretar a métrica de ahead como 683 mudanças exclusivas da S0 recente. Nenhum merge autorizado pela decisão atual. |
| AUD-ARQ-05 | P1 para acesso hosted | OPS-03 documenta que o REVOKE hospedado de competência/Logout Auth não tem atomicidade comprovada nem suporte operacional de reprodução das garantias I86 de banco descartável. | Não copiar o adaptador local para Supabase hospedado. Exigir decisão Infra/Proprietário, revogação e reconciliação/revalidação de sessão e competência no canal suportado. |
| AUD-ARQ-06 | P1 futura | A porta F02 original, a porta PRE_DISPATCH v0.1 e o novo wrapper de ciclo v0.1 coexistem e são chamáveis no laboratório. | Ao criar API hosted, **não** expor rotas antigas capazes de contornar gates mais novos. Um único ponto de decisão precisa incorporar M09, F01/F02/ciclo, consentimento, template, quota, reserva, cancelamento e auditoria. |
| AUD-ARQ-07 | P2 | Os testes de interoperabilidade validam muitas negativas, mas são **suites de SHAs pinados e fixtures isoladas**; os consumidores Meta/OpenAI/Frontend podem avançar independentemente. | Definir versões/compatibilidade por contrato e CI de matriz multi-frente, sem confundir skip offline com pass nem sucesso de teste sintético com E2E integrado. |
| AUD-ARQ-08 | P2 | Plano mestre v0.2 (10/10) contém conceitos de IA Gestora/Analista, fontes comerciais, comissão, cadastros, CRM, F03/Resumo, atribuição de lead próprio. Camadas S0 hoje privilegiam controles técnicos. | Não perder o objetivo de **terceirização comercial governada**, medição e aprendizado separado da IA Vendedora. Adotar rastreabilidade de requisitos de negócio para cada fronteira ao escolher MVP; não construir somente uma suíte de WA-39/Graph. |
| AUD-ARQ-09 | P1 externa, não defeito de código | Banco Yamaha autorizou verbalmente segundo relato, **não formalmente**. Ativos Meta, concessões App/WABA/phone, credenciais, consentimento, titularidade, fonte comercial e tarifa/remuneração dependem de confirmação. | Nenhum cadastro, fechamento bancário, uso de cliente real, envio WhatsApp ou afirmação financeira antes de atos/contratos necessários. |
| AUD-ARQ-10 | P2 | Meta M19/M20 #9 e S0 F03/#5/#6 dependem de `sent`/falha definitivos e status autenticados; dois simuladores M19 não compartilham fonte ratificada. | `API_ACCEPTED` ≠ `sent`; não aplicar duas falhas WDC-13/C09 ou comissão a partir de preview. Ledger de ocorrência com lote/posição/hash/HMAC/attempt/wamid/ordem e recheck S0. |

## 5. Estado observado por área

| Área S0/S1 | Entrega representativa | Parecer |
|---|---|---|
| S1 / OPS02–03, I79–I86 | Governança e revogação testadas em ambientes descartáveis; limites hosted explicitados | **Protótipo cuidadoso**; bloqueado para execução hospedada. |
| M09-01..08 | Snapshot, registry App/WABA/grant, Ed25519 fixture, propósitos, rechecks e point-of-use em PG17 | **Boa separação de revisões e escopo em laboratório**; falta fonte operacional e custódia. |
| F01 #11/#12 | Posse IA, handoff humano definitivo, seleção de fontes comerciais e revisão/aliases sem publicar | **Direção correta**, sem prova de fonte comercial real ou semântica. |
| F02 #7 | Ciclo/atribuição independentes corrigidos e aceitos apenas como mapeamento candidato OFF-18; controlador de ciclo assinado em fixture | **Correção demonstrada em lab**; falta autoridade de ciclo hosted e review integrado. |
| Frontend #14 | Histórico de titular, abertura sem compositor, readback de cutoff e revisão de UI candidata | **Aceite técnico candidato do Frontend**; sem ACL/identidade HTTP real. |
| PRE_DISPATCH v0.1/v0.2 #10 | Quota, reserva/cancelamento, tentativa/intent e readback + M18 adapter | **Requer correções P1 demonstradas** antes do próximo incremento autenticado. |
| Meta M18/M19/M20 #10/#9 | M18-D não autorizado; status/reconciliação/cadência offline | **Integração de transporte real ainda não ratificada**. |
| F03/Resumo #5/#6/#13 | Demanda interfrentes identificada; consumidores sintéticos e roteiro | **Dependência de aplicação real sob S0 e fonte segura**. |

**Importante:** trata-se de auditoria transversal de código e contratos prioritários, CI e cinco mutações físicas. **Não é** inspeção linha a linha de todos os 683 commits de diferença com main, nem revisão independente de normas bancárias, LGPD, APIs hospedadas, KMS, dados produtivos ou payloads de cliente. Essas lacunas não devem ser apresentadas como aprovadas.

## 6. Plano de remediação e gates para retomar avanço

**G0 — Congelamento técnico da fronteira PRE_DISPATCH → M18 (AGORA).** Manter `graph_dispatch_authorized=false` e `m18_dispatch_candidate=null`; não avançar identidade/lease operacional ainda. Manter experimentos isolados permitidos.

**G1 — Reparo das cinco contraprovas (primeiro incremento).** Implementar checker completo e comum de finalidade/template/grant/campaign e M09, validação de cancelamento por escopo/identidade, quota monotônica e ledger/slot. Exigir teste de *mutação sem revision bump* com resposta `STALE/DENIED`. Rever permissões de escritores que consigam contornar incrementos de revisão. O retorno ainda é `LAB_ONLY`.

**G2 — Atomicidade e semântica de versão.** Recheck com snapshot consistente e política de lock/CAS para múltiplos writers; terminalidade de cancelamento/opt-out, replay após revogação, isolamento cross-store, quorum de origem de timestamps/quota; contrato canônico de IDs/UUID, `plan_revision`, cinco revisões M09 e SHA de corpo/recipiente. CI com consumidores Meta e OpenAI pinados nos SHAs ratificados.

**G3 — Governança de integração.** Manifesto de contratos, SHAs, provas, aceites expressos e dependências, matriz de branches, plano de integração/merge (com aprovação separada). Fixar baseline confiável para que cada frente não desenvolva sobre snapshot desatualizado.

**G4 — Só depois:** desenhar principal hospedado/attestation por `attempt/intent/selection/nonce`, KMS e token de curta duração, outbox/lease externo e smoke E2E autorizado separadamente com Meta/Infra/Proprietário, sem usar a autorização atual para produção.

### Critério de conclusão da auditoria

Esta auditoria pode ser considerada **concluída documentalmente**, mas o código auditado **não pode receber parecer `SEM_PENDENCIAS`** porque cinco contraprovas P1 foram demonstradas. Reavaliar G1/G2 com provas **inversas** (negações físicas) e, depois, retomar sequência de integração. Nenhuma remediação foi aplicada à implementação nesta branch de auditoria.
