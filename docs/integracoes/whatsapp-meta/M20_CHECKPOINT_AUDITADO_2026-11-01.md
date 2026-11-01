# M20 — checkpoint auditado do checklist

**Data:** 01/11/2026. **Status da frente Meta:** laboratório offline, sem aceite operacional S0.

- [x] **M20-A —** [implementação WDC-13 candidata](../../../integrations/whatsapp-meta/wa20-wdc13-cadence-preflight-offline.ts), estritamente sem I/O e sem transição comercial, com verificações de escopo, sequência, tentativas, intenções e referência única de evento, causalidade dos timestamps e reset condicionado a falha/pendência anterior.
- [x] **M20-B —** [80 testes M20](../../../integrations/whatsapp-meta/wa20-wdc13-cadence-preflight-offline.test.ts), 60 iniciais + 20 regressões de auditoria, [CI funcional 41351099767](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41351099767): 1.982/1.982 Meta offline; PG17 18/18 históricos de ingresso independente; dois jobs `success`, scanner ACK aprovado.
- [x] **M20-C —** [documentação](M20_WDC13_CADENCIA_PREFLIGHT_OFFLINE_2026-11-01.md) e [auditoria](AUDITORIA_M20_WDC13_CADENCIA_2026-11-01.md), saída `wa20-wdc13-snapshot.lab.v0.2`, entradas LAB v0.1, WDC-13 e C09 exclusivamente S0, WA-39 [Issue #9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9).
- [ ] **M20-D —** S0/S1/Infra/OpenAI ratificar e integrar contrato autenticado/durável de `sent` e falha definitiva correlacionados por tentativa e cadência, replay/idempotência, regra de duas consecutivas e reset, tratamento de late evidence e efeitos WDC-13/C09 com trilha transacional. Não há autorização Graph, produção, SQL/HTTP ACK ou envio.
- [ ] **Marco principal M20 —** regra integrada à S0 e homologada fisicamente.

**Nota sobre consolidação:** o arquivo principal `CHECKLIST_CONCLUSAO_META.md` contém a linha legada M20 e sua edição não pôde ser concluída pela ferramenta de GitHub (bloqueio de segurança da ferramenta). Este checkpoint e o mapa de interfrentes registram o estado atual auditado **sem declarar que a linha legada foi atualizada**. Não editar/contornar esse bloqueio sem resolver a permissão de origem.
