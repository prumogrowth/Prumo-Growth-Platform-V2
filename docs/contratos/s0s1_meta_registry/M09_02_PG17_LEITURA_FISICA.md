# S0/S1 M09-02 — leitura física do vínculo PG17 (laboratório)

Data: 31/10/2026. Issue canônica: https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8.

**Situação:** `S0S1_M09_PG17_BINDING_LAB_PARTIAL`, implementado diretamente. Este incremento prova parte da leitura transacional da fixture S0/Meta Ingress, **não** conclui a registry canônica, o consumo Meta, o M2M real ou o M09 operacional.

## Proveniência e escopo

- Base de implementação M09-01: `0eb820de082503d9ec8a4caa26636a9686b32a5a`, com 32 casos sintéticos e CI anterior de sucesso.
- Fonte PG17 **pinada de outra linha**: `01ffdb093013664b73b18d23f92aac2202578210`, `integration/s0_meta_ingress/schema.sql` e `lab.py`. A CI faz checkout independente do SHA e valida seu `HEAD`; nenhuma cópia da fonte é alterada ou promovida para S0 hospedada.
- Implementação M09-02: `integration/s0s1_m09_registry/pg17_binding.py`; evidência `test_pg17_binding.py`; workflow `.github/workflows/exp-s0s1-m09-pg17.yml`. Diff da base de M09-01 até o SHA funcional `32de32d403a24825567b7efdec4f540b5d5ba014`: exatamente esses **três arquivos novos**, cinco commits na branch, sem mudança em fontes S0 original, Meta ou Supabase.
- Execução [GitHub Actions 41252991226](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41252991226) no SHA funcional `32de32d403a24825567b7efdec4f540b5d5ba014`: **completed/success**, dois jobs `success`; verificação de delta e 32 testes sintéticos herdados PASS (reexecução otimizada) e **11/11 casos físicos PG17 PASS**, sem skip no job físico. Os 11 testes usam Docker PG17 com recurso exclusivo e política de limpeza herdada do lab pinado. Testes físicos não alteram a fonte herdada.

## O que está demonstrado

A porta `prumo.s0.meta.registry.pg17-binding-lab/0.1-candidate` recebe principal M2M e host **resolvidos externamente em fixture**; não extrai autorização de webhook, IA ou payload. Na transação PG17 de menor privilégio, verifica rota→principal→binding sob `FOR SHARE`, versões físicas de rota/binding/principal, validade do principal pelo relógio do banco, grant técnico por canal, mapeamento explícito tenant→concessionária e unicidade global de número/WABA entre rotas. Fecha a conexão e devolve prova de leitura laboratorial ou decisão tipada negativa, sem segredo, slot, autorização HTTP ou Graph.

Os testes físicos cobrem leitura, readback/digest, versões stale, revogação por controle/installer, escopos de loja, M2M ausente ou diferente, duplicidade global, mapeamento indevido, consentimento técnico inexistente para Graph/POST, RLS do runtime contra mutação e expiração.

**Distinção essencial:** o schema PG17 pinado **não possui `app_revision` nem `grant_revision` independentes**. Não se inventou valor. A saída física usa `versions={route,binding,principal}`, `unproven_revisions=['app','grant']`, `ownership_evidence_state=UNVERIFIED` e `delegation_evidence_state=UNVERIFIED`. Não atende ainda ao `snapshot.schema.json` M09-01 completo nem ao formato de consumo `credential-routing.ts`. `snapshot_ref` é digest de correlação, não assinatura ou lease. A consulta física é instantânea; não autoriza operação externa posterior sem recheck.

## Gaps e próxima responsabilidade

**S0/S1:** definir a fonte canônica e revisão transacional separada para App/grant, identidade M2M autenticamente verificada e interface de leitura/recheck de uso físico. Estudar bloqueios/concorrência e revogação atômica real entre rotas, principals, grants e despacho, em ambiente segregado. O uso de `FOR SHARE` aqui preserva apenas a ordem da fixture; não foi homologado contrato de locks entre bancos/serviços.

**Meta:** revisar o formato proposto, identificar requisitos mínimos para adaptador WA-04A/M09 e manter offline até ratificação. O teste de 11 casos físicos não valida consumidor Meta ou Graph.

**Infra/Proprietário:** provar titularidade/delegação de App/WABA/número, inventário operacional e custódia de segredos/pins em fonte externa. Sem tal prova não existe onboarding real.

Não houve alteração de DDL/ACL hospedada, exposição de token, merge, deploy, alteração de entidade comercial, envio, ACK HTTP ou nomeação de Diretor. A Issue #2 permanece o contrato independente de HTTP/recibo; #10 controla o eventual PRE_DISPATCH.
