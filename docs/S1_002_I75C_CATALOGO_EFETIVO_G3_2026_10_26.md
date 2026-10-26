# S1-002 / I75C — catálogo efetivo PostgreSQL por tabela e coluna

**Data:** 26/10/2026. **Área:** S1-002, branch `feat/s1-002-equipe-prumo`. Laboratório PG17 descartável, sem merge, deploy, migrations hospedadas ou mutações da frente S0.

## Objetivo e fronteira

A I75B [inventariou objetos por leitura estática do repositório](S1_002_I75B_G3_INVENTARIO_EXECUTAVEL_2026_10_26.md), mas não provava ACL/RLS efetivas. A I75C verifica `pg_catalog` no **banco PostgreSQL 17 realmente inicializado pela regressão oficial** da frente, **sem ler linhas comerciais**. A auditoria não pode se tornar uma autorização: RLS presente e falta de `SELECT` de `anon` são garantias negativas parciais, não prova completa de segregação multi-loja.

## Código e verificações implementadas

- `scripts/test_s1_002_i75c_pg17_effective_catalog.py`: exige `CI=true`, URL PostgreSQL em loopback e banco `prumo_s0_test_*`, sem parâmetros/query remotos; chama `psql -X -A -t -v ON_ERROR_STOP=1` por subprocesso e materializa inventário JSON apenas de **metadados** de relações, colunas, ACLs e policies.
- `tests/test_s1_002_i75c_pg17_effective_catalog.py`: 8 testes de contratos em memória, incluindo rejeição de URL remota, tabela ausente, RLS desligada, SELECT de anon por tabela/coluna, policy I63 persistida e alteração de chaves/colunas obrigatórias.
- `.github/workflows/s1-002-postgres.yml`: executa os testes após as migrations S0/S1 e os ensaios sintéticos I52–I74, e arquiva `s1-002-i75c-effective-g3-catalog` como artifact. **Reutiliza workflow oficial**, sem criar outro e sem executar a Issue #3.

O catálogo verifica exatamente as **11 relações canônicas** inventariadas na I75B e a existência de campos de isolamento como `concessionaria_id`, `lead_id`, `caso_id`, `conversa_id` e `canal_id`, conforme cada objeto. Confere RLS ligada, recusa `anon` com SELECT relacional ou por coluna, exige que policies test-only `s1_63_canon_*` não tenham ficado instaladas após rollback, e confirma os campos sintéticos `leads_loja.telefone_cliente_normalizado` e `mensagens.conteudo_sintetico`.

O JSON também indica SELECT de `authenticated` por objeto/coluna **sem afirmar que isso é autorização de produto** (RLS e políticas por caso dependem do ator efetivo), e registra a presença declarada de `storage.objects` / `storage.buckets`. A existência desses objetos, se encontrada, **não aprova URL assinada, leitura de anexos, retenção ou LGPD**.

## Evidências conferidas na própria branch

Código com os testes I75C: `ff63fdf392aecd547e33c1676dcd422093042710`.

[PG17 oficial #40354941900](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40354941900), job `121684756516`: **SUCCESS**, logs com:

- **8/8 testes unitários** do verificador I75C;
- `PASS I75C-01` — 11/11 tabelas canônicas presentes com RLS;
- `PASS I75C-02` — `anon` sem SELECT relacional ou por coluna para essas superfícies;
- `PASS I75C-03` — nenhuma das policies I63 experimentais persistiu no catálogo após os testes;
- `PASS I75C-04` — colunas de contato e mensagem sintéticas catalogadas;
- regressões SQL anteriores, inclusive `I74 6/6` e rollback de objetos experimentais, preservadas.

Artefato **`s1-002-i75c-effective-g3-catalog`**, ID `12665866195`, arquivado no mesmo workflow, mais o inventário I75B anterior.

## Lacunas reais: G3 ainda bloqueado para operação

A auditoria **não** cobre políticas por usuário real em todas as classes D2/D3/D4, leitura/download de mídia/anexo, URLs e cache, bancos externos, OpenAI/F03 ou anexos de conversas históricas. Não converte ACL estrutural em concessão de acesso à ficha. Os aceites positivos/negativos de I61–I74 seguem como evidências de bancada, não de produção.

Foi aberta a [Issue #10 — catálogo físico S0/Meta e D2/D3/D4](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/issues/10). O Codex/S0 deve devolver apenas uma matriz por objeto/campo, fonte e consumidor, com status existente/proposto/ausente, chave loja+contato, regras de revogação/TTL e pendências de retenção. PRs Draft #9 (CFI/F03) e #8 (Meta webhook) são dependências correlatas em outras branches, **não devem ser importados automaticamente**.

**Próxima execução:** I75D confrontará a resposta documentada da S0 com inventários I75B/I75C; criará testes de acesso real apenas para superfícies implementadas e verificáveis. Se S0 não tiver mídia/anexo implementados, manter G3 bloqueado nesse subescopo, sem inventar endpoint, tabela ou evidência. Outros gates S1 podem evoluir independentemente. A I74 permanece certificada em laboratório.
