# S0/S1 M09-05 — auditoria de compatibilidade com WA-04A e WA-09 (offline + PG17)

**Data:** 31/10/2026 (America/Recife). **Classificação:** `S0S1_M09_05_SCOPED_META_AUDIT_LAB_ONLY`. **Issue:** https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8.

## Fonte de verdade e limites

- Base de trabalho S0/S1: M09-04 `b128e662409dc876a9bd728c72e524d1e1baed08`. Fonte física histórica PG17 em checkout independente `01ffdb093013664b73b18d23f92aac2202578210`, sem modificações.
- Fonte Meta **pinada sem alteração**: `745f54acd8255bea728c5ab7c87848d5018ad66b`; blobs `integrations/whatsapp-meta/credential-routing.ts` `2f817ef4e8e047e852867e4c30dd083769e32389` e `wa09-asset-onboarding-audit.ts` `1622ca8fa56f37a57203ed84fd5e0eaa524a49a6`. Os respectivos testes originais são executados pelo Node 22 em checkout independente, sem reescrever Meta.
- Branch M09-05: `exp/s0s1-m09-meta-bridge-20261031`. Novos arquivos apenas sob `integration/s0s1_m09_registry/`, workflow próprio e este documento.
- **Não houve contrato de consumo ratificado com a Meta**. Não modificar `integrations/whatsapp-meta/`, não criar novo `TrustedMetaRegistry` fabricado nem converter fixtures em dados do provedor.

## Incompatibilidade técnica constatada e decisão de desenho

A fonte Meta WA-04A (`wa-meta-credential-routing.v0.1-proposed`) exige um `TrustedMetaRegistry` com os três nomes `get_verify_token`, `post_app_secret`, `graph_access_token` juntos por App, e uma revisão singular `expected_revision`. WA-09 usa o mesmo registro e duas listas de ativos **não autenticadas**. Entretanto, M09-04 devolve uma resposta por escopo após leitura assinada PG17, com **cinco revisões distintas** (route, App, binding, grant, principal) e **sem slots**.

**Por segurança, não se converte essa resposta em `TrustedMetaRegistry`.** Uma adaptação direta precisaria inventar revisões e três slots (violação de minimização) ou consultar indevidamente credenciais. Essa incompatibilidade fica explícita em vez de ser mascarada por sucesso sintético.

A nova porta `inspectM09ForMetaOffline` oferece **somente auditoria de compatibilidade de escopo**. Recebe a resposta candidata M09-04 como JSON **não confiável**, e escopo/revisões esperados separadamente; valida forma exata sem executar getters, vínculo loja/App/rota/canal/WABA/número, cinco revisões, digest e flags negativas. Um pareamento positivo retorna `LAB_SCOPE_MATCHED_UNVERIFIED`, com **todas** as flags de privilégio/autoridade falsas. Uma recusa retorna `DENIED` com motivo sanitizado. Não devolve slot, WABA, telefone, token, segredo nem suposta autorização de Graph/ACK/envio.

**Observação crítica:** o TypeScript NÃO verifica a assinatura Ed25519 da resposta M09-04; a autenticidade pertence ao processo S0 que gerou a consulta. Uma resposta JSON forjada pode obter resultado de **pareamento estrutural de laboratório**, mas jamais concede autoridade. A porta não é substituto de canal M2M autenticado nem fonte externa do provedor.

## Testes e provas

- [CI funcional M09-05 run 41266572022](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41266572022) no SHA `af149c689f2046666b01ecc8c558f5cbd4d03f0b`: `completed/success`, **dois jobs success**. A primeira tentativa `acd6e56b7705ddb8e23b7970abb456229cf868e7` não iniciou jobs devido a expressão `runner.temp` no contexto global do job; corrigida para `$RUNNER_TEMP` em etapa própria. Não classificar essa primeira execução como teste que passou.
- **24/24 casos próprios** da ponte na execução de integração física, incluindo getter, Proxy, shape e campos extras, versões 5D, outra loja, outra WABA/phone, falsas flags, tentativa de usar propósito GET/POST/Graph, fonte simulada e resposta assinada produzida no PG17 descartável.
- **63/63 testes originais Meta WA-04A/WA-09** executados no checkout pinado e imutável, mostrando que suas fixtures antigas continuam funcionando **offline**, sem elevá-las a fonte S0.
- Na execução física, um script usa a fixture de leitura assinada M09-04 para gerar **uma resposta verdadeira do laboratório PG17** sem exportar chave privada/segredo/assinatura. O Node consome o JSON, confere os cinco vínculos/revisões e mantém `production_authorized/send_authorized/ack_allowed/graph_authorized=false`. O PG17, schema e custódia são descartados com a verificação de catálogo original; nenhum servidor ou Graph é iniciado.
- Os resultados acima não significam `24 + 63 + 72` testes novos. Os **72** casos de M09-01 a M09-04 já foram provados em CI anterior; M09-05 adiciona **24 casos distintos** na ponte e reaproveita **63 casos Meta existentes**. A CI deste incremento **não reexecuta todas** as 72 regressões anteriores, apenas as invoca na geração de fixture assinada e no contrato Meta pinado.
- O commit que acrescenta este relatório será validado por outra CI do SHA final, com auditoria da lista exata de cinco arquivos (quatro técnicos + documento).

## Condições pendentes

1. **Meta** revisa e ratifica ou rejeita uma nova interface *scoped, purpose-specific* por adaptador privilegiado, sem exigência de entregar os três slots ao consumidor. Sem isso, WA-04A/WA-09 originais **não consomem diretamente** a saída M09-04.
2. **Infra/Proprietário** comprovam titularidade/delegação dos ativos Meta, trust anchors, custódia/rotação de credenciais e política operacional de hosts. Nenhum identificador de Business/App/WABA no teste é prova de posse real.
3. **S0/S1** substitui a fixture de host, ratifica canal autenticado e mapeamento `tenant`↔loja, e obtém fonte hospedada controlada, HA/recovery, retenção de nonces e política de recheck. Nada disso é concedido por esta auditoria.
4. As Issues #2 (ingresso/recibo/HTTP ACK), #7 (F02) e #10 (PRE_DISPATCH) mantêm competências separadas; não há envio, Graph, mudança comercial, deploy nem merge.

**Próxima tarefa:** obter da Meta parecer específico sobre a nova projeção `scoped` de auditabilidade, depois desenvolver **consumidor experimental de finalidade única** com slots restritos, somente se houver contrato revisado, mantendo a fonte S0 autoritativa. Sem autorização para produção.
