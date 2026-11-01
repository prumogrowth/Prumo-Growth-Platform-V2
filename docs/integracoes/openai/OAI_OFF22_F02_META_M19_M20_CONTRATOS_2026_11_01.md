# OFF-22 — Revisão de compatibilidade F02 com os contratos Meta M19/M20

**Data:** 01/11/2026. **Status:** laboratório de compatibilidade, **SEM AUTORIZAÇÃO OPERACIONAL**. Base OpenAI OFF-21: `457c7b70eabaa0097350ac708f7768e07da785cf` ([CI 1028/1028](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41357902698)).

## Fontes externas verificadas

A Meta publicou e auditou os contratos de **saída**:
- M19 *Graph/status*, `wa19-graph-status-snapshot.lab.v0.2`; código [Meta `3311caaa91034e93da533ce7748370e239538ecb`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/3311caaa91034e93da533ce7748370e239538ecb/integrations/whatsapp-meta/wa19-status-evidence-reconciliation-offline.ts); [auditoria](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/d314d7bd1f1c87b366544c1eb6afc88c3080ecb3/docs/integracoes/whatsapp-meta/AUDITORIA_M19_RECONCILIACAO_STATUS_2026-11-01.md).
- M19 *vínculo S0 alegado*, `wa19-status-snapshot.lab.v0.2`; [código Meta](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/3311caaa91034e93da533ce7748370e239538ecb/integrations/whatsapp-meta/wa19-status-reconciliation-offline.ts).
- M20 *cadência WDC-13 alegada*, `wa20-wdc13-snapshot.lab.v0.2`; [código Meta auditado `d314d7bd`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/d314d7bd1f1c87b366544c1eb6afc88c3080ecb3/integrations/whatsapp-meta/wa20-wdc13-cadence-preflight-offline.ts).

**São três contratos incompatíveis entre si quanto à origem física, escopo de identidade, contagem, regras de digest e prova de autoridade.** Não contêm, juntos, vínculo **autenticado e comum** tentativa/intenção/ocorrência/cadência que permitiria à OpenAI/F02 concluir `sent`, falha definitiva ou janela C09. A alteração M19 v0.1 → v0.2 corrigiu hash de variantes conflitantes; a M20 v0.1 → v0.2 corrigiu unicidade de `event_ref`, relógios e contagem de resets. Reutilizar versões antigas ou mapear snapshots por nome produz falsa equivalência.

## Entrega da frente OpenAI

`e04_offline_lab/f02-meta-m19-m20-compatibility-lab.mjs` contém função pura `reviewF02MetaM19M20Compatibility` e schemas `prumo.openai.f02-m19-m20-compatibility/0.1-lab` e `...-result/0.1-lab`. Entrada aceita **somente**:
1. preview OFF-11 `prumo.openai.f02-wa39-preview/0.1-lab`, produzida por `previewWa39F02Projection`, com observações `verified:false`;
2. snapshot M19 Graph `v0.2`;
3. snapshot M19 S0 binding `v0.2`;
4. snapshot M20 cadence `v0.2`.

Todas as formas são rígidas (chaves próprias, tipos, contagens, `sha256` estrutural sem confiança, protótipos, acessores, ciclos). Uma alegação de HMAC, S0 authentication, correlation, `sent_verified`, `wdc13_transition_authorized`, `c09_window_authorized`, `automatic_retry_authorized`, `production_authorized` etc. **true** é recusada. `hash` de uma fixture nunca equivale a assinatura. Em vez de retornar dados, o módulo **sempre** fixa autorização e verificação em `false` e classifica:
- `LAB_UNCORRELATED_HOLD / NO_SHARED_AUTHENTICATED_ATTEMPT_ID`: entradas estruturalmente coerentes, mas não correlacionadas por fonte S0 confiável;
- `LAB_FINAL_TEMPLATE_HOLD / NO_AUTHENTICATED_C09_SENT`: alegação `sent` e template final não abrem janela C09;
- `LAB_WDC13_CANDIDATE_HOLD / S0_EXCLUSIVE_COUNTER`: duas falhas sintéticas não autorizam mudança WDC-13, desistência ou replanejamento;
- `LAB_HOLD_UNVERIFIED / CONFLICT_OR_UNCERTAIN`: conflito/quarentena/UNKNOWN impede qualquer conclusão;
- `DENIED` ou `INVALID_INPUT`: versão errada, grant forjado ou objeto hostil.

**Não se constrói um evento `verified:true`** para `reviewF02Continuity`. O resultado omite IDs, conteúdo, `wamid`, digest, telefone, tentativas, timestamps e contagens. Não há runtime Meta, SDK, S0 hospedada, banco, callback, payload de envio ou transição. Não gera retry, C09 nem altera negócio.

## Testes

`e04_offline_lab/tests/f02-meta-m19-m20-compatibility-lab.test.mjs`: **40 casos**, incluindo M19 v0.1 vs v0.2, M20 v0.1 vs v0.2, status de observação, final-template, dois claims de falha consecutiva, variantes conflitantes, HMAC falso, grants falsos, campos extras, protótipos e getters. A meta da branch é regressão **1068/1068 Node** (1028 anteriores +40) e **24/24 Python AST** da S0 F02 pinada, separadamente. Metas não são evidência até CI do SHA definitivo ficar verde.

## Limites operacionais e próximo contrato

- As divergências M19 e M20 são resolvidas **apenas quanto ao reconhecimento dos formatos LAB v0.2 e à negativa de autoridade**; não existe projeção operacional S0 homologada de F02.
- [Issue #9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9): S0/Meta precisam ratificar identidade da ocorrência (batch físico/posição/digest), autenticação de callback HMAC, vínculo `intent_ref/attempt_ref` por loja/caso/fluxo/cadência, sequência/cursor, `wamid`, persistência/readback, correções tardias e classificação definitiva.
- [Issue #7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7): F02 só pode consumir uma **projeção S0 minimizada e autenticada**; a correção de `cycle`/ `assignment` OFF-18 não substitui os demais contratos.
- [Issue #10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10): PRE_DISPATCH v0.2 e M18 ainda são laboratórios e não autorizam Graph/send real.
- WDC-13 e C09 permanecem **decisões S0**, nunca interpretações da IA. `API_ACCEPTED`, `read`, `delivered`, timeout, 131049 e claims M19/M20 **não** viram `sent` ou perda comercial.
- Sem modelo ou chave OpenAI; sem merge, deploy, dados reais, envio ou acesso à produção.

**Parecer somente após CI:** `COMPATIBILIDADE_DE_SCHEMAS_META_LAB_V02_COM_HOLD_EXPLICITO`. Não é conclusão da etapa 08 nem homologação da etapa 10.
