# E04/S0-F03 — Revisão humana auditável de identidade, PostgreSQL 17

**Data:** 24/10/2026. **Repositório oficial e único de escrita:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`. **Branch:** `feat/oai-s0-f03-history-port-20261023`. **PR #1:** Draft contra `feat/s0-cfi01-f03-auth-preflight-20261020`, nunca contra `main`. Sem merge, deploy, dados pessoais, Meta/WhatsApp, API OpenAI real ou Supabase hospedado.

## Evidência física

[GitHub Actions #40087638366](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40087638366) — **SUCCESS** em **PostgreSQL 17.11** e ambiente inteiramente descartável, commit `e1ed668f1b8a2dd57fd7082700cef767813cb5c4`:
- **84/84 testes da S0 CFI-01** (`Ran 84 tests ... OK`);
- **183/183 testes F03** (`Ran 183 tests ... OK`), incluindo **95 testes de integração física PG17**;
- **267/267 testes PASS** no total, **16 testes novos** (`test_80` a `test_95`) de revisão humana e governança.

A primeira execução com os 16 testes novos, [#40087521444](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40087521444), teve **três falhas em critérios de teste**: as contagens de linhas eram globais para toda a suíte, sem filtro por loja/caso, e por isso incluíam registros de cenários anteriores. O código de contagem dos testes foi corrigido para a combinação `concessionaria_id,caso_id`; na nova execução, todos os 267 passaram. Não ocultar a rodada inicial, nem confundir logs de negação esperada com falhas de implementação.

## Entrega: auditoria S0 do trabalho humano

[Fixture de revisão humana](../supabase/tests/s0_f03_identity_human_review_local_only.sql) **somente local**, carregada pelo [executor de testes](../scripts/run-s0-f03-pg17-local.sh):
- Nova tabela `prumo_private.cfi01_f03_identity_human_reviews_local`, com um único recibo para combinação **loja + pendência + caso**, vinculado a candidato de lead, atribuição, ator, sessão, versão do ciclo e versão da identidade; guarda o tipo da decisão humana e **SHA-256 da evidência**, sem armazenar o texto da evidência no recibo.
- Valores de decisão permitidos: `ESCALATE_REVIEW`, `CANDIDATE_POSSIBLY_RELATED`, `CANDIDATE_NOT_RELATED`. São **pareceres consultivos**, não identificação civil ratificada nem resolução da pendência.
- Gatilho confere escopo de concessionária, caso, lead, atribuição ativa, sessão S0 e versões; bloqueia UPDATE/DELETE, nega acesso direto a `anon`, `authenticated` e `service_role` e mantém a tabela com RLS habilitado.
- Restrição composta foi criada para FK da pendência da S0/028; os registros de pendência preexistentes não são migrados ou alterados.

[Porta Python interna da S0](../backend/s0_f03_identity_human_review_local.py):
- `record_human_identity_review_local` só aceita um `IdentityProvider` do lado S0 e um `HumanReviewRequest` estritamente tipado, sem aceitar ID de ator, sessão ou loja fornecidos pela F03 como verdade.
- Confere sessão ativa `auth.sessions`, bloqueia a **equipe S1 antes do caso**, exige operador/gestor com concessão vigente e atribuição ativa no caso, valida versão do ciclo e **versão independente de identidade**, confere que o telefone pendente é candidato exato, variante brasileira ou alias já ligado ao lead, e grava uma prova append-only.
- Pedidos repetidos idênticos do mesmo ator são idempotentes. Decisões concorrentes diferentes não geram dois recibos. Resposta contém **apenas estado** (`*_REVIEW_ONLY` ou falha), sem número, segredo, conteúdo ou prova.
- Uma decisão `CANDIDATE_NOT_RELATED` **não desbloqueia** a reserva CAS da F03: a pendência original continua exigindo resolução explícita pela S0.

## Limites não cobertos — nenhum gate de produção

1. O teste de autenticação injeta **`LocalIdentity` fictícia** e as sessões são representadas por `auth.sessions` na fixture: isto **não testa o GoTrue real**, JWT externo, consentimento nem autorização de produção. A verificação S1 do laboratório usa dados sintéticos de equipe e concessão; nenhuma rota HTTP ou permissão a IA foi aberta.
2. O recibo humano é um **registro de revisão**, não uma decisão de qual lead pertence ao número, não faz merge de identidade, não altera a pendência original e não remove a trava de CAS F03. A S0 precisará de **protocolo de resolução e ratificação**, possivelmente com prova de identificação adicional e conferência sob concorrência, antes de liberar pendências.
3. Para produção ainda faltam domínio operacional de ficha/catálogo, prova de conteúdo multimídia, política/rotação HMAC real, gate LGPD e transação única de aplicação de campo com CAS, versões reais e autorização S0.
4. O SQL está guardado em `supabase/tests/` e **não é migration**; nenhuma credencial real foi usada. A conexão da fixture exige localhost e banco descartável; a integração F03 continua `REVIEW_ONLY`.

**Próxima etapa:** criar fluxo ratificado de resolução de pendência na S0 com prova de identidade/evidência, histórico imutável e revalidação de autorização antes de retirar o bloqueio conservador, sem nunca permitir que F03 escolha a identidade autonomamente.
