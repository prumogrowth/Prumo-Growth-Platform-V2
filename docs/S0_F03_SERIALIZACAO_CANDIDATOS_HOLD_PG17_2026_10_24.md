# E04 S0/F03 — serialização de candidatos de identidade

Data: 24/10/2026. Ambiente exclusivo PG17 descartável, PR #1 Draft contra S0; nenhuma alteração em main/produção.

## Camada implementada

A fixture `supabase/tests/s0_f03_identity_scope_serialization_local_only.sql` instala advisory lock transacional por concessionária, acionado tanto pela verificação de HOLD como por toda inserção, atualização ou exclusão de pendências, aliases ou leads na S0 sintética. A leitura consulta a concessionária por recibo imutável antes do lock, revalida o recibo e verifica todos os leads candidatos distintos (telefone primário ou alias, com comparação variante BR existente). Dois candidatos implicam `CONFLICT_REVIEW_REQUIRED`; nunca há associação automática. Escritores de outras lojas continuam independentes.

## Limites

A serialização vale apenas no ponto transacional e pressupõe que todas as rotas de escrita nessas fontes mantenham os gatilhos e usem o banco em READ COMMITTED. Uma escrita posterior ao commit permanece possível e obriga nova verificação. A cadeia tríplice HMAC permanece auditável e imutável; `CURRENT_HOLD_ONLY` não dá leitura F03, CAS cadastral, exclusão de pendência ou resolução civil. Fixture E04, não migração hospedada.

## Validação

Seis novos cenários físicos PG17 `test_154`–`test_159`: vários leads candidatos, alias de lead concorrente, inserção concorrente de pendência, inserção concorrente de alias, isolamento entre lojas e verificação diante de inserção não commitada. O baseline 325/325 pertence ao commit anterior `cf6690bd...`; novos totais exigem resultado do Actions no novo HEAD.

Próximo passo: ficha/catalogo operacionais e aplicação S0 campo a campo sob CAS; sem promover HOLD a autorização.

## Certificação física concluída

**GitHub Actions SUCCESS:** https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40144520216

**Commit de código executado:** `e5490c849430ba59fd0d02705874b77c8d0c055e` — PostgreSQL 17.11.

- **84/84** testes S0 CFI-01: `Ran 84 tests ... OK`.
- **247/247** testes F03: `Ran 247 tests ... OK`.
- Destes, **159/159 testes físicos PostgreSQL** (`test_01` até `test_159`).
- **Total geral: 331/331 testes aprovados.**
- Os cenários `test_154` a `test_159` aparecem individualmente como `ok` nos logs.
- Os erros PostgreSQL de permissão, imutabilidade e timeout exibidos no log são **resultados adversariais esperados**; a suíte terminou em `OK`.
- Esta atualização documental não altera o código testado e não requer reexecutar os testes por si só.

Os bloqueios valem no instante transacional; nenhuma garantia de ausência de inserções futuras nem grant F03 foi criada.
