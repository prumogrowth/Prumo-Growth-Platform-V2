# S0/S1 ↔ Meta M09 — cadastro técnico, snapshot e revogação (candidato 0.1)

**Data:** 31/10/2026. **Issue canônica:** https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8.
**Classificação:** `S0S1_META_REGISTRY_0_1_CANDIDATE_ONLY`. Proposta técnica para revisão interfrentes; **não é contrato ratificado, API publicada, cadastro operacional ou homologação produtiva**.

## 1. Proveniência e limites verificáveis

- Base documental S0/S1: OPS-03 `4e1534f632539d265e8c1e5a504627c452e081c2`, descendente direto de OPS-02 `7d3232f59aab35265c3aa7fb5ab5ab2f06d5d047` e I86 `a0c4eaf2720bd6cf2bd756544498f8f185f005fc`. OPS-03 = `S0S1_OPS03_LAB_PARTIAL`, sem REVOKE hospedado homologado. Este documento não toca em competências de Diretores.
- Fonte S0 Meta Ingress **independente, somente leitura**: `01ffdb093013664b73b18d23f92aac2202578210` (implementação certificada anteriormente em `9e3077d222df2b3184ee6ea568fdac7c9da75567`). `integration/s0_meta_ingress/schema.sql`, `ingress.py`, `control.py`, `test_ingress.py`, e `docs/contratos/s0_meta_ingress/*` são referência para reaproveitamento; schema `s0_meta_lab` **exclusivamente PG17 descartável**, não tabela canônica instalada.
- Meta consumidora independente: `integrations/whatsapp-meta/credential-routing.ts` e `wa09-asset-onboarding-audit.ts` da branch `feat/meta-s0-physical-interop-ack-guard-20261031`, lidos em `4260b3accf4930026f7f74e902f5962472d89057`. Ficam sob propriedade Meta. A fixture `wa-meta-credential-routing.v0.1-proposed` não é fonte S0.
- Evidências Meta M09: SHA `1cfe4f4bd76d970de8b6b935244447943c4d08d4`, CI `41209617874` (1.248 testes offline, 18 verificações cruzadas) conforme comentário Meta #8; M10 adicional permanece sem identidade/custódia operacional. Nenhuma dessas provas estabelece titularidade real.
- Não há integração comprovada entre OPS-03 e a trilha Meta Ingress. Pins e manifesto podem ser usados para consulta e testes, **não** são incorporação, merge, migração ou promoção a produção.

## 2. Responsabilidade autoritativa e fronteiras

**S0/S1 é proprietária do cadastro técnico e das decisões de validade, vínculo, grant e revogação.** Meta é consumidora de uma projeção autorizada; provedores Meta/Infra e Proprietário comprovam titularidade e delegação efetivas por processo próprio. App, WABA e número informados por payload externo são apenas valores a confrontar, nunca concessão de escopo.

O vínculo entre `concessionaria_id` canônico e `tenant` da fixture S0 Meta Ingress precisa de **mapeamento explícito verificado pela S0**. Não assumir que strings de tenant, nomes de rota, IDs WABA ou número telefônico equivalem a concessionária, empresa proprietária ou grant. Uma única App/WABA não deve cruzar concessionárias conforme WDC-02/03; telefone e `canal_id` devem ser globalmente únicos no registro efetivo. Mudança de titularidade/migração de App exige fluxo governado próprio, não simples mutação de grant.

O snapshot de leitura não concede envio, ACK, publicação de F01, agendamento F02, efeitos comerciais nem privilégios humanos. A #2 define ingresso/recibos e política HTTP; a #10 define PRE_DISPATCH; a #7 define planejamento F02; não duplicar tais políticas no registro M09.

## 3. Contrato de leitura proposto

**Nome/versionamento:** `prumo.s0.meta.registry.snapshot/0.1-candidate`.
**Porta:** chamada interna S0 por serviço M2M autenticado, nunca endpoint público/RPC exposto por esta versão. Dois usos previstos: `resolve_trusted_route` para GET/POST pelo contexto de infraestrutura confiável; `read_scoped_channel` para uma loja/canal após autenticação e autorização S0. Revisão e grants são consultados novamente antes da decisão sensível posterior. A resolução de slot de HMAC POST *antes* da verificação da assinatura pode usar somente referência de roteamento confiável, jamais App/WABA declarado no POST.

**Entradas (definidas pelo servidor, não pela IA/webhook):**
- `request_ref` único de correlação sem poderes de autenticação; `purpose` enum `GET_VERIFY_TOKEN | POST_APP_SECRET | GRAPH_ACCESS_TOKEN | REGISTRY_READ`;
- `principal_ref`, `issuer_ref`, `audience`, `scope` e revisão de chave resolvidos pelo verificador M2M confiável; a alegação do chamador não satisfaz autenticação;
- `trusted_route_ref`/revisão de roteamento obtidos do host de ingresso **ou** `trusted_scope` `(concessionaria_id, app_ref, canal_id, waba_id, phone_number_id)` derivado de operação autenticada na S0;
- `expected_revisions` opcionais para detecção de stale (rota, App, vínculo e grant), sem permitir aceitar versão maior inventada; relógio do servidor define validade.

**Projeção autorizada (somente backend de confiança):**
- `schema`, `snapshot_ref`, `observed_at`, `source_revision`/digest S0 de integridade, `concessionaria_id`, `app_ref`, `route_ref`, `canal_id`, `waba_id`, `phone_number_id`, `active`, `valid_from`, `valid_until`;
- revisões **distintas** de rota, App, vínculo, grant e principal M2M (não condensar em contador fictício); escopos/grants técnicos efetivos da loja/canal e situação de revogação;
- `slot_ref` **somente da finalidade técnica solicitada**, na projeção privilegiada do adaptador que efetivamente precisa buscar credencial; token, App Secret, verify token e segredo Graph nunca retornam. A projeção ordinária não inclui slot refs;
- `ownership_evidence_state` e `delegation_evidence_state` declarados `UNVERIFIED` até comprovação independente externa; nenhuma `provider_verified=true` por igualdade de fixtures;
- `production_authorized=false`, `send_authorized=false`, `external_http_ack=false`, `commercial_transition_authorized=false` para toda resposta desta versão candidata.

**Decisões tipadas:** `SNAPSHOT_CANDIDATE_ONLY`, `DENIED`, `STALE_OR_REVOKED`, `CONFLICT`, `UNAVAILABLE`. Resultado candidato positivo significa *projeção de leitura laboratorial*; nunca `ONBOARDED`, `SEND_AUTHORIZED` ou `ACK_ELIGIBLE`. Motivos negativos sanitizados, sem expor se uma loja/rota inacessível existe, nem dados ou slots secretos. Não usar booleans externos para substituir essa decisão.

**Recheck obrigatório:** snapshots não são bearer, leases nem tickets de envio. Uma mudança ou revogação de rota/App/principal/vínculo/grant invalida sua versão; recheck da fonte S0 no limite de uso evita TOCTOU. Na instância transacional em laboratório, preservar a ordem de locks da fonte de referência (rota → principal → bindings ordenados) e CAS do controle. Não declarar ordem global integrada S0/S1/Meta antes de auditar mutadores, FKs e gatilhos das fontes reais. Falha/timeout/commit incerto nunca vira autorização; não executar retry Graph ou HTTP externo automaticamente.

## 4. Critérios de teste da futura porta S0

**Positivos:** leitura autorizada isolada para uma loja com duas WABAs, canais distintos, revisão conhecida e grant M2M válido; reconsulta idempotente sem mutação; alteração de revisão detectada após desativação; projeções diferentes para host privilegiado e consumidor comum.

**Negativos:** ausência de principal/autenticação falsa/JWT humano; propósito técnico não autorizado; outra loja/App/tenant; canal inativo, grant revogado, route/App stale, número duplicado, WABA ligada a outra loja, slot indevido ou ausente; payload forjado criando `canal_id`; respostas de recurso indisponível, concorrência entre snapshot e revogação, replay exato/divergente, troca de vínculo com CAS errado, resultado de commit incerto e saída contendo segredo/PII. Testar que `GET` de challenge não equivale a ACK POST e que `GRAPH_ACCESS_TOKEN` não autoriza despacho.

**Provas esperadas:** testes positivos/negativos adversariais, diferenças de escopo, confirmação de que fonte/código original não mudaram, commits e árvore exatos, CI por SHA, classificação do ambiente (sintético, PG17 físico descartável, hospedado não executado). Não somar subconjuntos de testes. Sem CI ou ambiente disponível, registrar **não executado**, nunca PASS.

## 5. Pendências de decisão e aceite

**S0/S1:** escolher e evidenciar a futura fonte persistente canônica, o mecanismo de identidade M2M e recheck, os mutadores/ACL/versões e a relação entre `concessionaria_id` e tenant técnico; mostrar testes físicos de isolamento/concorrência. O laboratório S0 já possui registro/revogação **fixture**, não homologação dessa fonte real.

**Meta:** revisar nomes/campos, exigência de slot por finalidade e compatibilidade com `credential-routing.ts`/WA-09; oferecer consumidor de teste offline sem introduzir S0 paralela.

**Infra/Proprietário:** comprovar em fonte Meta titularidade e delegação reais, inventário e histórico de ativos, custódia de secret slots/KMS, rotação/revogação e competências administrativas de cadastro. Nenhum ato real, mudança de política de segurança, schema/ACL hospedados ou migração está autorizado por esta minuta.

## 6. Missão Codex delimitada — S0S1-M09-01 (somente após encaminhamento explícito ao executor)

**Objetivo:** entregar *porta de leitura/recheck laboratorial* que implementa o contrato candidato e produz matriz de testes; **não** cadastrar ativos reais nem operar Meta/Infra. O contrato pode receber ajustes versionados após parecer da Meta, sem declarar sua ratificação.

**Base e escopo:** partir do commit documental que contém este contrato na branch `coord/s0s1-m09-contract-20261031`, em branch nova `exp/s0s1-m09-snapshot-lab-20261031`; nunca partir de `main` por suposição. Congelar SHA, árvore e inventário antes do primeiro commit. Leitura pinada da fonte S0 Meta Ingress `01ffdb093013664b73b18d23f92aac2202578210` e consumidora Meta `4260b3accf4930026f7f74e902f5962472d89057`. Verificar ancestralidade OPS-03 e distância dos pins independentes. Não copiar cegamente código de outras branches; se for necessário consumir blob, manifestar origem, SHA e escopo.

**Arquivos autorizados:** exclusivamente novos arquivos sob `integration/s0s1_m09_registry/`, `docs/contratos/s0s1_meta_registry/` e workflow experimental próprio de testes em `.github/workflows/` se demonstradamente necessário. Não modificar `integration/s0_meta_ingress/`, `integration/i86/`, `integration/s0s1_ops03/`, `backend/`, `supabase/`, `integrations/whatsapp-meta/`, `main` ou estruturas hospedadas; nenhuma migration. Se for impossível sem alterar uma fonte protegida, registrar dependência e parar antes de alterar.

**Abordagem:** definir provider de leitura S0 confiável e injetável e política negativa por padrão; exercitar com fixture PG17 descartável reutilizada por pin, sem instalar esquema S0 Meta Ingress em banco herdado. Não criar pseudoautenticação produtiva; fixture M2M separada da declaração de recibo e da requisição. `concessionaria_id` deve vir de mapeamento explícito confiável, não igualar automaticamente ao `tenant` do lab. Demonstrar snapshot versionado, revogação/CAS, isolamento, replay/concorrência e projeção sanitizada; sem liberar endpoint externo. Conservar toda autorização produtiva/comercial false. Preferir testes de contrato e integração física isolada a inventar nova camada de persistência.

**Gate de auditoria:** executar testes adversariais positivos/negativos e regressões dos módulos tocados, verificar blob/tree, exclusividade do diff, no secrets/PII, descarte do PG17, status CI por commit e preservação das fontes. Separar resultados locais/CI/PG físico/hospedado. Publicar branch, commit, comandos, número real de testes, resultados, limitações e próxima dependência; sem PR merge, deploy ou operação produtiva. Entregar à coordenação S0/S1 para auditoria e, depois, resposta na #8 para aceite Meta. **Não reivindicar M09 operacional só porque o ensaio passou.**
