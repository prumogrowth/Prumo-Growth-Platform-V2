# WA-27 — PostgreSQL 17: isolamento RLS e revogações da ponte S0/Meta

**22/10/2026 · PR [#2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2) · Escopo: WhatsApp/Meta, PG17 descartável.** Continuação [WA-25](./wa25-finalidades-grants-filtro-candidatos-offline-2026-10-22.md) e [WA-26](./wa26-ponte-s0-catalogo-politicas-fases-offline-2026-10-22.md).

## Resultado validado

**GitHub Actions [#39857438202](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39857438202)**, commit `b67f58f488eff268934785334075d7e10f168187`: **3/3 jobs SUCCESS**. Node 22 manteve **567/567 testes PASS**. O job WA-15C/S0 PostgreSQL 17 acrescentou **14/14 verificações WA27 PASS**, além de seus testes anteriores WA15C/WA16B. WA06D PG17 seguiu verde.

## O que foi implementado

O CI prepara um **schema isolado `wa27_lab`**, sem tocar as tabelas nem as migrações de S0. Cria três papéis fictícios **NOLOGIN** com permissão **somente SELECT** (loja A, loja B, sem escopo); três tabelas independentes de `scopes`, `policies`, `catalogs` com `ENABLE/FORCE ROW LEVEL SECURITY`; e política RLS que só permite linhas do `current_user` de teste.

Um processo PostgreSQL 17 descartável, com banco inicializado a partir das migrations S0 Draft, realiza leituras **REPEATABLE READ + READ ONLY** sob cada papel, sem edição das fontes S0. Os resultados JSON são entregues ao **código TypeScript real da WA-26** por portas *fake* de leitura. Não são dados de clientes reais.

Passam as verificações:
1. O mesmo `selection_ref` retorna somente os dados e templates da loja A ou B conforme o papel; papel sem escopo retorna vazio; privilégios de escrita são negados.
2. PLAN, RESERVE e PRE_DISPATCH reconhecem catálogo/consentimento fictícios válidos, mas mantêm `send_authorized:false`.
3. Após **COMMIT e nova sessão SQL**, o opt-out da A bloqueia a A; template Meta pausado, retirada de grant e alteração de identidade/revisão bloqueiam o uso. A B permanece isolada e não recebe alterações da A.
4. Tickets do PLAN anterior são recusados quando a revisão autenticável simulada mudou. Nenhuma resposta produz `Graph POST`, token ou autorização de produção.

Arquivos de laboratório, todos de propriedade desta frente:
- `integrations/whatsapp-meta/lab/wa27_pg17_setup.sql`, `wa27_pg17_read.sql`.
- `wa27_pg17_optout.sql`, `wa27_pg17_pause.sql`, `wa27_pg17_revoke_grant.sql`, `wa27_pg17_revoke_actor.sql`.
- `wa27-assert-pg17-ports.ts`: executor de 14 verificações sobre snapshots efetivamente retornados pelo banco.
- `.github/workflows/whatsapp-meta-offline.yml`: gate WA-27 adicionado após os testes cross-branch existentes. O papel fake é escolhido explicitamente pelo CI.

## Limites que permanecem (não inferir homologação)

**Isto NÃO é a S0 autenticada.** Os papéis são `NOLOGIN`, concedidos e selecionados pelo runner de laboratório com privilégio de administrador. Eles **não** implementam identidade real via GoTrue/JWT, concessões S1, RLS produtiva, autorização por caso nem isolamento de credenciais Meta. O `selection_ref` ainda não é uma prova assinada de S0.

As leituras separadas por fase e as sessões distintas provam a rejeição de revisões/opt-out alterados **após COMMIT**, mas **não** provam ausência de corrida **entre o último read e o dispatch**. `REPEATABLE READ` da sessão de leitura não substitui transação de reserva/lock ou portão operacional atômico. Nem testes de carga/concor­rência real, nem transações de envio, ACK, Graph, campanha/oferta real, consentimento legal, multi-dispositivo ou revogação concorrente foram homologados.

**Próxima integração dependente das outras frentes:** definir a porta confiável de S0/S1 para (1) identidade/tenant/caso, (2) catálogo de grants e versão, (3) consentimento + campanha vigente, (4) transação de reserva/rechecagem; só depois fornecer serviço autenticado, sem autorizar envio por um retorno de fixture.

Nenhum merge, deploy ou mudança nos arquivos da S0, S1, OpenAI ou frontend ocorreu.
