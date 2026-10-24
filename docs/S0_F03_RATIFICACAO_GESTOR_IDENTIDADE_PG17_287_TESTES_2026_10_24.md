# E04/S0-F03 — Ratificação independente de identidade e 287 testes PG17

**Data:** 24/10/2026. **Único repositório oficial:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`.
**Branch de trabalho:** `feat/oai-s0-f03-history-port-20261023`, [PR Draft #1](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/1), base `feat/s0-cfi01-f03-auth-preflight-20261020` (não `main`). Somente E04 offline, banco e pessoas sintéticas. Sem merge, deploy ou escrita no repositório antigo.

## Prova física realizada

[GitHub Actions #40125810316](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40125810316) rodou no PostgreSQL **17.11**, com conclusão **SUCCESS** no commit `695fc22ceddcb70ac3a530024f0bd889d547ed7d`.

- **84/84 S0** (`Ran 84 tests ... OK`).
- **203/203 F03** (`Ran 203 tests ... OK`), dos quais **115 testes físicos PG17 F03**.
- **287/287 PASS** no total.
- Testes novos **96–115**, 20/20 físicos, executados e aprovados: gestor independente, papel de gestor por loja, equipe S1 ativa, sessão, parecer inicial adequado, idempotência, concorrência de dois gestores, versões atuais, alteração posterior da pendência, SQL contra inserção fraudulenta, ACL/RLS, imutabilidade e **CAS F03 ainda bloqueado**.

## Novo contrato e delimitação de autoridade

O contrato anterior, [`backend/s0_f03_identity_human_review_local.py`](../backend/s0_f03_identity_human_review_local.py), permite ao operador autorizado registrar um parecer de revisão sobre pendência sintética S0/028; **não é resolução**.

Criado [`backend/s0_f03_identity_ratification_local.py`](../backend/s0_f03_identity_ratification_local.py), consumindo esse parecer como entrada imutável. Somente **outro ator humano** com:
- sessão corrente válida em `auth.sessions`;
- membro `ativo` de `public.equipe_prumo_s1` (trava S1 antes de caso, conforme fluxo S0);
- papel `gestor` ativo e escopado à concessionária;
- registro original `CANDIDATE_NOT_RELATED` do operador **diferente**;
- mesmo caso, mesma pendência e mesmas versões de ciclo e identidade ainda vigentes;
- pendência que continua possível candidata daquele lead por telefone exato, variante BR ou alias;

pode criar um **recibo de ratificação somente de auditoria** `RATIFIED_AUDIT_ONLY`. A operação é idempotente apenas para repetição idêntica; concorrentes diferentes são recusados. A função confere uma `IdentityProvider` confiável no servidor S0, nunca um gestor escolhido pelo modelo, e retorna somente estado, sem telefone, texto, prova, dados de identidade ou tokens.

Criada a fixture [`supabase/tests/s0_f03_identity_ratification_local_only.sql`](../supabase/tests/s0_f03_identity_ratification_local_only.sql) (NÃO migration): tabela append-only `prumo_private.cfi01_f03_identity_ratifications_local`, vinculada por FK composta à revisão `concessionaria_id + pendencia_id + caso_id` e por FK a `revisao_id`. Guarda gestor, sessão, versões, SHA256 da evidência e chave idempotente, sem conteúdo. Trigger impõe revisão original negativa, identidade e ciclo atuais, papel de gestor, S1, segundo ator distinto e sessão; UPDATE/DELETE sempre proibidos, sem grants diretos a `authenticated` e com RLS.

O executor [`scripts/run-s0-f03-pg17-local.sh`](../scripts/run-s0-f03-pg17-local.sh) inclui a fixture, e [`backend/tests/test_s0_f03_pg17_integration.py`](../backend/tests/test_s0_f03_pg17_integration.py) passa a ter **115 testes físicos**.

## O que NÃO foi liberado

1. **A ratificação não fecha a pendência S0/028.** Mesmo após dois atos humanos, `_PENDING_IDENTITY` continua devolvendo `CONFLICT_REVIEW_REQUIRED` para F03, testado no cenário 112. Não há novo mapeamento civil, redirecionamento de lead, reabertura F01, autorização de conteúdo, alteração de ficha, status comercial nem integração Meta/banco.
2. **Isto ainda não é homologação de identidade real.** O teste usou `LocalIdentity` com sessão S0/S1 no banco descartável, **não o GoTrue hospedado real**, nem comprovou coleta/evidência de identificação civil ou consentimento.
3. **Falta o protocolo S0 de resolução final:** ratificação da evidência material, revisão de conflitos cruzados, versão de pendências/alias sob concorrência, emissão de recibo de resolução verificável, validade temporal e rechecagem no mesmo ponto de decisão. O mero recibo `RATIFIED_AUDIT_ONLY` deliberadamente não autoriza remoção do bloqueio. Isso requer projeto e testes físicos adicionais antes de qualquer conexão a escritores de ficha.
4. Também continuam fora deste escopo: domínio operacional de ficha/catálogo, transação final CAS com auditoria campo a campo, mídia/áudio/anexos, gestão real de chave HMAC/rotação, política LGPD de leitura mínima, grant de conteúdo F03 e E05/API OpenAI real.

## Evidência de falha corrigida antes da aprovação

O desenvolvimento anterior e os testes de revisão humana já foram concluídos em [run #40087771450](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40087771450) com **267/267 PASS**. A nova validação física ratifica o incremento de **20 testes**, totalizando 287. Alterações e testes deste relatório permanecem dentro do PR Draft #1 e não fazem merge.

**Dependências externas para continuar E04:** nenhuma. O PostgreSQL 17 descartável do GitHub Actions está acessível; não solicitar credenciais ou acesso à produção.
