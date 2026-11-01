# S0/S1 — M09-03: fonte App/grant persistente candidata em PG17 descartável

**31/10/2026 · Estado:** `S0S1_M09_03_DISPOSABLE_PG17_CANDIDATE`, **sem homologação operacional**. Issue canônica: https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8.

## Proveniência e escopo

- Base M09-02: `06ad474e5c14b198c95235b7776f4d27fe3551fb` (11 testes físicos PG17). Fonte S0 Meta Ingress independente pinada: `01ffdb093013664b73b18d23f92aac2202578210`; não alterada.
- Branch experimental: `exp/s0s1-m09-pg17-registry-20261031`. Arquivos novos: `integration/s0s1_m09_registry/pg17_registry_candidate.sql`, `pg17_registry.py`, `test_pg17_registry.py`, workflow `.github/workflows/exp-s0s1-m09-pg17-registry.yml` e este relatório.
- A extensão SQL só instala no banco exclusivo `s0_meta_ingress_lab` quando PostgreSQL 17, usuário `postgres` e dois guardas explícitos `s0_meta.disposable=YES`, `s0_m09.install=CANDIDATE_ONLY`. Nenhuma alteração de schema, ACL, tabela ou segredo hospedado.
- O teste remove a extensão antes da auditoria de catálogo herdado e o laboratório elimina container, volume e diretório de custódia descartáveis. O código S0/Meta original permanece pinado.

## O que foi implementado

1. **Persistência candidata:** schema `s0_m09_lab` separado, com App por concessionária/tenant/route, revisão App própria, validade e flags não atestadas, WABAs globalmente únicas, grants por `canal_id` com revisão própria, `phone_number_id` globalmente único e secret-slot **referencial** único por propósito e entre Apps.
2. **Leitura física com recheck:** consulta S0 original de rota, principal e binding, mais App e grant na mesma transação PG17, com `FOR SHARE`, identidade resolvida por injeções laboratoriais, confronto de loja/tenant/canal, revisões separadas `route/app/binding/grant/principal`, digest estável para detecção de alterações. Sem expor slot, chave, token ou dados comerciais.
3. **Revogação transacional somente pelo instalador de laboratório:** CAS de quatro revisões, ordem de locks rota original → binding original → App → grant; revoga binding original e grant candidato na mesma transação, incrementa revisões de rota, binding, App e grant. Duas revogações concorrentes: exatamente uma aplica; a outra conflita. O runtime S0 de leitura não recebe direito de escrita ou consulta da tabela de slots.
4. **Bloqueio físico por constraint**, e não por comparação tardia: número único global e WABA não compartilhável entre Apps. Inserções concorrentes com o mesmo número geram um commit e uma recusa de unicidade.

## Evidências verificadas

- [CI funcional 41261853553](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41261853553) no SHA `35805e0bd1442014ab39542a657948f21cd5f4c2`: `completed/success`, **dois jobs success**.
- 32 testes sintéticos herdados, reexecutados com Python normal e otimizado (32 casos distintos, não 64). **13/13 novos casos físicos PG17 PASS** (logs do job físico) e **11/11 casos físicos anteriores PASS** na mesma CI. Total de casos distintos da seleção executada: 32+13+11 = **56**, com classificação dos três grupos separada.
- Testes PG17: versões independentes, recheck stale, rollback por CAS incorreto, revogação cruzada atômica, concorrência de revogação e de número duplicado, RLS contra escrita/leitura de slots, mismatch de origem/tenant, isolamento por loja, principal sintético falso, anti-alias de slots.
- Diff funcional contra M09-02: exatamente quatro novos arquivos de escopo delimitado. O commit documental desta atualização e a mudança consequente de workflow terão uma nova execução CI; não reutilizar o status do SHA funcional como aceite de outro commit.

## Lacunas e próximos gates

- **Ainda não existe fonte S0 canônica instalada em ambiente homologado.** A extensão é laboratório descartável, não migration pronta para Supabase. As regras de App/grant precisam de modelo definitivo e homologação sob autoridade apropriada.
- **M2M continua sintético/injetado:** os casos físicos usam chave/principal cadastrados na fixture, mas não provam assinatura criptográfica do cliente, custódia, trust anchor, rotação ou identidade operacional do host. O próximo incremento S0 deve endereçar assinatura e antirreplay em laboratório, então a fronteira de host/Infra real.
- **O adaptador Meta não consome ainda esta estrutura diretamente.** A projeção `PHYSICAL_REGISTRY_LAB_ONLY` não satisfaz automaticamente `TrustedMetaRegistry` / WA-09 nem autoriza Graph/HTTP. Integração com #2 (ingresso HTTP/recibo) e #10 (PRE_DISPATCH) continuam separadas.
- **Propriedade/delegação de App/WABA/número e custódia real** precisam de comprovação Infra/Proprietário; o status permanece `UNVERIFIED`. Não assumir que fixture, assinatura ou ID de banco é prova do provedor.
- Nenhum envio, segredo real, banco hospedado, deploy, merge, mudança de negócio ou nomeação de Diretor foi realizado. Toda saída de leitura conserva `production_authorized=false`, `send_authorized=false`, `external_http_ack=false` e `commercial_transition_authorized=false`.

**Próximo responsável:** S0/S1 para endurecer M2M e prova de entrada; Meta para compatibilidade de consumo nesta Issue; Infra/Proprietário para os atos reservados.
