# S0-040 — integridade do mapeamento Meta por canal (apoio à frente WhatsApp)

**Data:** 19/10/2026. **Status:** correção de desenvolvimento em branch Draft, **não executada nem homologada em PostgreSQL nesta etapa**. Solicitação: autorização expressa para desenvolver ajustes S0 necessários à frente Meta, mantendo a equipe principal concentrada na S1.

## Falha encontrada

A migration sintética S0-030 criava `prumo_private.meta_canais_fixture_s0` com `UNIQUE(phone_number_ref)` e FKs de posse por loja, mas **não exigia unicidade de `canal_id`**. Consequentemente, o mesmo canal interno de uma concessionária poderia receber uma **segunda associação com outro WABA/número**, gerando ambiguidade na validação de origem e divergindo do contrato de prova interna WA-06B/DEC-WA-05. Achado por revisão estática da DDL; **não é reprodução de exploração em banco ou ambiente real**.

## Alteração estritamente limitada

- `supabase/migrations/202610190040_s0_meta_canal_emissor_unico_fixture.sql`: adiciona `UNIQUE(concessionaria_id,canal_id)` à **tabela de fixture S0-030**, sem substituir migrações existentes, ampliar grants, instalar canal real ou tocar tabelas comerciais. Mapeamento inverso já é restringido por `UNIQUE(phone_number_ref)`. Se houver mapeamento duplicado preexistente, PostgreSQL falhará de forma explícita ao aplicar a constraint; **não há exclusão de dados automática**.
- `supabase/tests/s0_wa_040_meta_binding.sql`: **cinco gates planejados WA40-01..05**, dentro de `BEGIN/ROLLBACK`: canal não recebe segundo WABA/emissor; um número não vincula outro canal; App não aponta para loja alheia; **dois canais distintos da mesma App/loja** podem ingressar na função S0-030 com replay correto; ausência de permissões públicas/gateway sobre fixture.
- `scripts/run-s0-local.sh`: carrega a nova migration **após as migrations já presentes** e roda WA40 depois do teste S0-030, exclusivamente quando o usuário executar o runner protegido de banco descartável local `prumo_s0_test_*`.
- A numeração 040 não depende da migração S1-039 (em outra frente), mas seu ordenamento final deve ser revalidado antes da integração dos PRs.

## Evidência e limites

**Verificação estática:** três arquivos publicados e relidos no GitHub; nomes de migration/teste no runner conferidos; código isolado de fixtures, sem alteração do primeiro diagrama de arquitetura, sem grant, RPC, IAM real ou Graph.

**Resultados de execução:** **WA40-01..05 = 0/5 executados em PostgreSQL nesta etapa**. Este ambiente não possui `psql`, `postgres`, `initdb` ou `pg_ctl`. Não atribuir `PASS` e não confundir os testes S0 anteriores, feitos em CI em outros commits, com esta revisão. Integrar e testar sob PG17 descartável e Supabase local antes de considerar merge. Não usar runtime real / token / Supabase hospedado.

**Gates ainda abertos:** identidade de serviço autenticada fora do corpo Meta, vínculo App/WABA/phone com vigência e autorização verificadas, prova HMAC, nonce transacional, payload integral protegido, ocorrências posicionais, ACK só após COMMIT durável, `COMMIT_UNKNOWN` e normas DEC-WA-04/06. Não reutilizar `aceitar_lote_multicanal_fixture_s0` como ingresso operacional: aceita mistura de lojas no mesmo lote de fixture, diferente do enquadramento autenticado por App do contrato real.

**Decisão de escopo:** GO para desenvolvimento limitado da S0 em apoio à Meta; **NO-GO** para afirmar integração real, autenticação, aceite HTTP, migrar banco comercial, alterar POC concessionária de demonstração, gerar custos ou mesclar PR sem gates.
