# WA-44 — Adaptador JavaScript para contrato interno S0/044, com prova física PostgreSQL 17

**24/10/2026 · Somente laboratório local · Novo repositório oficial [0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA) · [PR S0/Meta #2 Draft](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/2).**

## O problema resolvido

WA-43 demonstrou que o material de HMAC do receptor **S0/044** confere entre **Python e PostgreSQL**, mas não havia uma implementação JavaScript correspondente na branch da ponte S0, nem teste de envio sintético JavaScript → receptor PG17. A WA-44 acrescenta um emissor **de laboratório**, sob `supabase/tests/`, sem criar API, módulo exposto à aplicação ou alterar a Meta/Graph.

`s0_wa_048_meta_handoff_adapter.mjs` converte SOMENTE dois registros **fictícios e cruzados** (registro do App/WABA/Phone e vínculo da tentativa S0) mais um status sintético em uma tupla de **15 campos**. Nega por padrão: loja, App ou canal divergentes, revisão obsoleta, ID de tentativa/intent inválido, evento sem formato, informações extras/getters/proxy, nonce inválido e timestamp inválido. Assina com **HMAC-SHA256** (segredo sintético separado de qualquer Meta App Secret), propósito literal `FORENSIC_APPEND_ONLY` e prefixo `prumo-meta-handoff-lab-v1`. Reproduz byte a byte o material da função PG17 `prumo_private.meta_material_handoff_fixture_s0` testada na WA-43.

**A interface é um artefato de teste, não uma credencial de serviço.** A nomenclatura `registry` e `binding` refere-se a *fixtures injetadas*, não a uma origem autenticada. Uma requisição HTTP/IA não pode fornecer essas informações como verdade autoritativa. A exigência de autenticação do serviço e a obtenção dos bindings S0 via canal seguro seguem pendentes.

## Evidências automatizadas e limites

- `supabase/tests/s0_wa_048_meta_handoff_adapter.test.mjs`: 20 testes locais de validação, canonicalização e HMAC + 7 provas físicas contra o mesmo banco PG17 descartável do CI.
- Provas PostgreSQL: **material canônico JS↔PG**, **HMAC JS↔pgcrypto**, **handoff com MAC correta**, rejeição de evento adulterado, replay recusado, MAC incompatível no formato WA34-JSON recusada e inexistência de flags comerciais de envio/ACK.
- O script tem proteção explícita: `PRUMO_TEST_DATABASE_URL` deve apontar exclusivamente para `127.0.0.1:5432/prumo_s0_test_ci` com usuário `postgres`. Não aceita overrides de conexão `PGHOST`/similares nem utiliza credenciais de produção.
- `scripts/run-s0-local.sh` e workflow `wa39-s0-meta-offline.yml`: regressão S0 completa e as provas WA39 (18), WA40 (25), WA41 (16), WA42 (23), WA43 (18) e WA44 (27) no exato HEAD antes de declarar homologação de laboratório.

## Fronteira de integração ainda NÃO desenvolvida

WA34/35, na branch [`docs/whatsapp-meta-concessionária de demonstração-poc-20261017`](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/tree/docs/whatsapp-meta-concessionária de demonstração-poc-20261017), emitem um pacote distinto: HMAC de JSON ordenado e contexto `issuer/audience`, vínculo e `binding_revision`. A WA-44 **não valida nem aceita o pacote WA34/35**; seu candidato é produzido com fixtures S0 separadas. Para interoperabilidade real falta contrato formal de identidade emissora, audiência, versão, escopo, nonce e evidência HMAC Meta **sobre os bytes brutos**, acordado com a frente responsável pela Meta.

A gravação final do domínio S0 continua sob wrapper `SECURITY DEFINER` de `postgres` **somente na simulação**, não sob uma identidade mínima produtiva. O registro forense não é autorização para envio, campanha, IA, confirmação de entrega comercial, ACK HTTP, ou reenvio Graph. Esta etapa não implanta Supabase hospedado, não movimenta número da concessionária-piloto e não usa tokens reais.

## S1 e responsabilidade interfrentes

**Nenhuma alteração da S1 é necessária para WA-44.** A prova é exclusivamente de assinatura interna, vinculação técnica S0 e status forense. A futura ativação comercial **continua bloqueada** até a equipe proprietária da S1 decidir escopo/cessão de atendimento, revogação de concessões humanas e ordem de locks conjunta; não presumir que uma assinatura Meta autorize Consultor, Gestor ou Diretor. Comunicar essas dependências ao responsável S1 antes de implementação que as exija.

**Estado:** somente considerar WA-44 testada após o workflow do novo repositório concluir com sucesso e todos os marcadores. PR continua Draft, sem merge na `main`.
