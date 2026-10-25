# I65 — Inventário de caminhos indiretos via RPC, SECURITY DEFINER e views

**25 de outubro de 2026.** Execução estritamente na branch `feat/s1-002-equipe-prumo`, nos bancos descartáveis PostgreSQL 17 e Supabase CLI. Nenhum schema ou função de produção foi alterado.

## Risco e decisão de segurança

O I64 demonstrou e fechou, em políticas candidatas, as leituras brutas D2 por concessão ampla da loja. Porém **RLS de tabela não impede** um `SECURITY DEFINER` público (seu owner pode ignorar RLS) ou uma view com privilégios do proprietário de devolver os mesmos dados. `security_barrier=true` não equivale a `security_invoker=true`. Por isso I65 audita **capacidade SQL de leitura**, não apenas nomes de arquivos.

O `supabase/tests/s1_091_rpc_view_surface_guard_local_only.sql` contém um detector baseado em `pg_catalog` que bloqueia: (i) funções `SECURITY DEFINER` acessíveis a `anon/authenticated` dentro de `public`, (ii) views/materialized views em `public` com SELECT para estas roles sem segurança do invocador, e (iii) `USAGE` de cliente no schema inteiro `prumo_private`. Inspeciona também `search_path` de todos os definers desse schema. A verificação mantém um achado separado, **não omitido**, de que o contrato legado `prumo_s1_interface` ainda concede `USAGE` e `EXECUTE` a `authenticated`; ele depende de não ser incluído na lista de schemas expostos do PostgREST. Essa capacidade não foi promovida ou declarada segura para produção.

O teste inverte a prova usual: cria propositalmente **uma função pública definer que conta exceções privadas** e **uma view pública owner-rights sobre a tabela I61**, concede permissões à role autenticada e comprova que o detector identifica exatamente as duas vulnerabilidades e que a leitura é possível apesar de a tabela privada proibir SELECT direto. Depois revoga `EXECUTE/SELECT` e prova a negação com a mesma role. O experimento é feito em `BEGIN/ROLLBACK` no teste I64; as armadilhas não sobrevivem ao commit e não existem na branch como migrations.

## Escopo

Teste catalogal não equivale à prova de todas as funções SQL nem da infraestrutura de rede, JWT/KMS, edges e RPC externas. O escopo visa os objetos atuais de `public` e o schema privado canônico; schemas futuramente expostos e funções de serviço com elevação explícita exigem nova revisão. O PostgREST do ambiente GoTrue local deve ainda provar por HTTP que os nomes de RPC privada não são atingíveis e que o scanner percebe a exposição caso uma view/definer deliberada seja ativada.

**Sem qualquer deploy ou promoção de políticas.** Evidências da CI serão registradas após aprovação.

## Prova HTTP assinada e scanner reutilizável

O scanner foi extraído para `supabase/tests/s1_091a_rpc_view_catalog_scanner_local_only.sql` para a mesma lógica ser executada em PG17 e GoTrue/PostgREST efêmero. O red-team PG17 importa este arquivo e faz oito verificações com rollback; `scripts/test_s1_002_i65_rpc_view_surface_e2e.py` é chamado após I64 e usa a mesma sessão real para demonstrar leitura indevida quando a RPC/view **de propósito** recebe privilégios, corte de acesso por `REVOKE` e `DROP` de ambos os objetos. O ensaio distingue claramente **vulnerabilidade deliberadamente injetada** de exposição observada nos objetos legítimos. Nenhum objeto malicioso foi inserido em migration operacional.
