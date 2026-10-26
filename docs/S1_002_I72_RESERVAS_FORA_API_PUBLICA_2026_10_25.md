# I72 — reservas fora da API pública (laboratório)

Data: 25/10/2026. Escopo estrito: `feat/s1-002-equipe-prumo`. Candidato **somente** em `supabase/tests/`; nenhuma migration hospedada, alteração na `main`, merge ou Issue #3.

## Falha concreta e decisão

A I71 precisava conceder `INSERT` em `public.s1_70_export_reservas` ao papel `authenticated` para que a RPC pública `SECURITY INVOKER` reservasse quota. Isso tornava a tabela um endpoint REST de inserção direta: um Gestor com grant vigente podia consumir reservas sem pedir exportação.

A I72 **não adiciona** `SECURITY DEFINER` à RPC pública e não usa `request.path`, cabeçalhos ou GUC controlável pelo cliente como prova de autoridade. Em vez disso, move a tabela existente para o esquema interno `prumo_export_ledger`, não publicado pela configuração PostgREST. Mantém a mesma OID, linhas históricas, índices, trigger, política RLS e `INSERT` restrito por colunas. Apenas `authenticated` recebe `USAGE` no novo schema para a RPC invocadora conseguir reservar; não recebe `SELECT/UPDATE/DELETE`. `anon` e `service_role` não recebem `USAGE` no esquema.

Três funções I71 existentes são recompiladas sobre **exatamente** a nova referência qualificada: trigger de quota, RPC pública invocadora e expurgo administrativo. A recompilação usa `pg_get_functiondef` somente em uma lista fechada de três funções certificadas e substituição literal do nome da tabela, com preflight e auditoria pós-condições. ACLs e estados de segurança anteriores permanecem.

## Provas exigidas

- PostgreSQL 17 na suíte sintética existente após I71: presença da política RLS original, ausência de relação pública, RPC legítima com quota, operador sem grant, trilha aceita preservada e rotina de limpeza sobre a nova tabela; rollback exterior.
- GoTrue real + PostgREST descartável na mesma stack I71: `POST/GET /rest/v1/s1_70_export_reservas` deixa de ser rota válida, inclusive para o próprio Gestor; `Content-Profile` não expõe o schema; RPC I71 continua exportando e debitando quota; usuário sem autorização continua sem resultados; expurgo ainda funciona.
- Preservar testes I52–I71 antes de I72; nenhum workflow de outra frente alterado.

## Limites explícitos e próximos gates

I72 elimina o caminho HTTP **direto pela API pública** nas configurações testadas, **não** é fronteira de confiança contra um usuário que obtenha acesso SQL executável com o papel `authenticated`: tal usuário ainda pode inserir uma reserva própria, pois `SECURITY INVOKER` exige o grant SQL. Resolver o abuso em presença de SQL arbitrário exige gateway autenticado/assinado com papel de banco dedicado, sem criar função pública privilegiada. Também permanecem pendentes exportações alternativas S0, quotas globais por loja, rate-limit de borda e registro de recusas não relacionadas à quota.

O schema interno **não pode** ser incluído em `pgrst.db_schemas` nem liberado por profile na implantação. Políticas candidatas I63–I72 continuam exclusivamente nas fixtures locais; proteção definitiva requer revisão de ameaça, controles operacionais, LGPD e gate de integração.

## Evidência

Status de CI: aguardando resultados das execuções ligadas ao commit I72. Verificar logs de workflow com `PASS I72-01..06` (PG17) e `PASS I72-E2E-01..07` (GoTrue real) antes de certificar. Um commit salvo não equivale a certificação.
