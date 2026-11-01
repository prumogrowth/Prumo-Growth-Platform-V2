# M13 — Conciliação de catálogo e templates Meta (offline)

**Data:** 31/10/2026. **Frente:** WhatsApp/Meta. **Estado:** protótipo de conciliação de metadados sem autoridade operacional. A M13 principal continua aberta.

## Objetivo

Verificar que um catálogo S0 alegado e uma coleção de respostas individuais alegadamente Meta descrevem exatamente os mesmos templates, sem confundir igualdade estrutural com aprovação Meta verdadeira, fonte S0 autentificada, ownership de WABA, permissão comercial ou possibilidade de envio.

## Componentes reutilizados

- `graph-template-provider-observation.ts`: validador preexistente de forma de um detalhe de template Graph, sem origem comprovada.
- `template-purpose-eligibility.ts`: filtro de finalidade/actor/grant do planejador; permanece **separado** desta tarefa.
- `s0-template-purpose-bridge.ts`: rechecagem de política/opt-out/finalidade em fixture; não substituída nem convertida em autorização.
- `wa09-asset-onboarding-audit.ts`: inventário técnico App/WABA/canal; não é a fonte S0 canônica ou prova de titularidade.

## Implementação

- `integrations/whatsapp-meta/wa13-template-catalog-reconciliation.ts`: `reconcileWa13CatalogOffline(hostScope, s0Snapshot, providerSnapshot)`. Versões de laboratório: `wa13-host-scope.lab.v0.1`, `wa13-s0-catalog.lab.v0.1`, `wa13-meta-detail-batch.lab.v0.1`.
- Exige `concessionaria_id`, `app_ref`, `waba_id` e `catalog_revision` idênticos entre host e S0 alegada; WABA do conjunto Meta deve coincidir. Limita idade dos snapshots sintéticos a cinco minutos e recusa data futura. Esse limite é uma **regra de fixture**, não prova que a Meta tenha sido consultada.
- Valida a correspondência completa dos IDs, nome/idioma, categoria e estados em todas as entradas. Recusa lote com faltantes, extras, duplicatas e divergência de versão/identidade. Não faz atualização parcial do catálogo.
- Apenas anota **candidatos estruturais** para template que aparece como `APPROVED` nos dois manifests, localmente ativo, versão atual e válido em `now_ms`. Status `PENDING`, `REJECTED`, `PAUSED`, `DISABLED`, versão não atual, desativação, ainda não vigente ou expirada ficam excluídos. Não há concessão de finalidade, consentimento ou dispatch.
- Rejeita acesso por getters, arrays esparsos, campos inesperados, símbolos e excesso de entradas. Saída sem componentes/texto da mensagem, variáveis, contato de cliente, assinatura, URL/cursor ou segredo.
- Retorna `LAB_CATALOG_RECONCILED_UNVERIFIED` ou `DENIED`. `meta_approval_verified`, `provider_source_authenticated`, `s0_source_authenticated`, `tenant_binding_verified`, `grants_verified`, `consent_verified`, `send_authorized`, `production_authorized` e `actual_sync_performed` são sempre `false`.

## Regressões e CI

43 testes próprios `wa13-template-catalog-reconciliation.test.ts`, incluindo duas concessionárias/WABAs, versão stale, status, expiração, zero candidatos, dupes, alteração de nome, componentes inválidos, injeção de `approved`, listas esparsas e getters. A evidência final será o CI no SHA exato de código e testes; não somar os 43 às verificações físicas PG17, que exercitam outro artefato.

## Dependências e limites

- **S0/S1 e Infra:** fonte canônica autenticada de catálogo, revisão transacional, ownership/delegação Meta, proveniência de detalhe Graph por WABA, freshness/readback e sincronização de alterações externas; [Issue #8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8). As entregas S0 M09-01 e M09-02 são laboratórios (incluindo PG17 parcial), **não aceite de cadastro real**.
- **F02 / OpenAI:** catálogo por finalidade, ator e escopo aprovado para planejamento; [Issue #7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7). F02 não trata esta conciliação sintética como aprovação Meta.
- **PRE_DISPATCH / S0:** recheck vigente de consentimento, opt-out, template/campanha/versão e tentativa transacional [Issue #10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10). Aqui não se reserva nem envia mensagens.
- Sem Graph real, SQL, endpoint, HTTP/ACK, credenciais, merge, deploy ou efeito comercial.

**Conclusão:** validação de consistência entre fontes fictícias, útil para detectar divergências antes da integração de autoridade. A M13 só poderá ser encerrada com sincronização e evidência operacionais ratificadas por S0/Infra/Proprietário.


## Adendo de auditoria — 31/10/2026

A [auditoria de M13](AUDITORIA_M13_CATALOGO_TEMPLATES_2026-10-31.md) encontrou que comparar somente ID, nome, idioma, versão declarada, categoria e status **não** detectava alteração de BODY/BUTTONS de um template preservando `APPROVED`. A entrada sintética S0 agora inclui o campo obrigatório `provider_components_sha256`, calculado sobre os componentes normalizados já suportados pelo inspector Meta. A M13 recusa diferença com `COMPONENT_VERSION_MISMATCH` e mantém um digest técnico no candidato interno. Este hash **não é aprovação comprovada nem assinatura de origem**.

A inspeção do detalhe passou a aceitar somente os campos opcionais já reconhecidos pelo inspector Meta (`parameter_format`, `quality_score`, `rejected_reason`) sem associá-los a concessão de direitos. O digest também exige tipo `string` antes de qualquer regex, evitando coerção `toString` não confiável.

Nova função `recheckWa13CandidateOffline`: recebe candidato anterior e **novas** fixtures de host/catálogo/detalhes; verifica novamente App, loja, WABA, revisão, conteúdo e elegibilidade. Pausa, versão trocada, digest alterado, expiração ou cruzamento de loja devolvem `DENIED`. Mesmo quando `LAB_RECHECKED_UNVERIFIED`, todas as flags produtivas são `false`. Duas leituras em laboratório **não são** garantia transacional, nem previnem mudança ABA ou corrida após o último recheck.

**Evidência atualizada:** 62 testes específicos M13 (43 originais + 19 de auditoria), **1.447/1.447 Meta offline** e **18 PG17** de outro escopo no [CI 41262001974](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41262001974), SHA funcional `745f54acd8255bea728c5ab7c87848d5018ad66b`, 2 jobs `success`. As afirmações históricas de 43/1.428 acima referem-se apenas à versão inicial da M13.
