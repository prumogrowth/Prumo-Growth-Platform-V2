# E04/S0 — Selo local append-only do histórico multi-casos F03 (23/10/2026)

> **NOVO SELO DE CONTEÚDO (23/10/2026):** além do selo de metadados deste relatório histórico, o [módulo adicional HMAC persistente](../backend/s0_f03_bound_content_seal_local.py) vincula a prova textual ao manifesto. [CI PG17 executada e aprovada: 177/177](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40032787969), com 23 testes físicos F03 e 15 testes adicionais do fluxo de rechecagem. [Registro técnico detalhado](./S0_F03_HMAC_PERSISTIDO_PG17_177_TESTES_2026_10_23.md). Continua `REVIEW_ONLY`, sem autorização de conteúdo/modelo e sem homologação de rotatividade das chaves.

> **VALIDAÇÃO FÍSICA CONCLUÍDA — 23/10/2026:** [relatório do GitHub Actions](./S0_F03_PG17_CI_HMAC_2026_10_23.md): **153/153 testes PASS em PostgreSQL 17.11**, com 84 S0 e 69 F03 (24 leitor, 31 selo, 14 PG17). A fixture SQL, gatilhos e ACL foram exercitados no banco descartável. Novo [módulo HMAC S0](../backend/s0_f03_content_integrity_local.py) detecta alteração de texto, mas não possui ainda selo HMAC persistente/versão de chave ou autorização de fornecer conteúdo à IA. Menções abaixo a PG17 não executado descrevem **o estado anterior a essa validação**.

> **Integração física preparada, não executada (23/10/2026):** [executor manual PG17](../scripts/run-s0-f03-pg17-local.sh), [11 testes físicos](../backend/tests/test_s0_f03_pg17_integration.py) e [relatório com comandos, critérios e lacunas](./S0_F03_PG17_EXECUTOR_E_LACUNA_CONTEUDO_2026_10_23.md). A sintaxe foi verificada; três tentativas de apontar o runner para alvo remoto/incorreto ou PGHOST redirecionado foram recusadas. **0/11 cenários rodados em PostgreSQL real** neste ambiente (PG17 e psql indisponíveis). A suíte evidencia explicitamente que alteração do **texto** histórico não muda o hash de pertencimento de mensagens; portanto `REVIEW_ONLY` não pode virar autorização de conteúdo F03.

**Situação:** desenvolvimento real de código na S0 compartilhada, como autorizado pelo responsável, exclusivamente em laboratório. **Ainda não homologado fisicamente** contra PostgreSQL 17, GoTrue/S1/S0 reais, mídia ou dados de clientes. Não usar como contrato de execução de F03. PR #16 empilhado sobre PR #12, mantendo ambas as branches originais intactas.

## Entrega

- [`backend/s0_f03_history_seal_local.py`](../backend/s0_f03_history_seal_local.py) — composição do leitor S0 multi-casos do próprio PR #16, da ponte S0 de rechecagem autenticada e do registro local append-only. O método `seal` faz inspeção/autorização S0 antes, compara outro recorte do histórico, reinspeciona antes de gravar, persiste somente IDs/metadados e reinspeciona após gravar. `verify` compara novamente histórico atual, pessoa, corte, hash, contagens e JSON persistido. Eventos obsoletos, repetidos com dados divergentes, falta de prova e falha de leitura **recusam**.
- [`supabase/tests/s0_f03_history_seal_local_only.sql`](../supabase/tests/s0_f03_history_seal_local_only.sql) — **fixture SQL descartável**, não é migração. Tabela `prumo_private.cfi01_f03_history_seals_local` com FK/identidade local, integridade de caso/loja/lead/corte/recibo verificada por trigger no insert, índice único por loja+encerramento, trigger que impede update/delete, RLS e revogação de acesso anônimo/autenticado. **Não contém texto de mensagens, nem ficha, nem evidência bancária**. Não aplicar à Supabase hospedada.
- [`backend/tests/test_s0_f03_history_seal_local.py`](../backend/tests/test_s0_f03_history_seal_local.py) — **31 testes unitários**, cobrindo hash canônico, sequência temporal, escopo, ausência de watermark, falha de autorização, replay idempotente, conflito de hash persistido, leituras divergentes e consultas SQL parametrizadas.

## Evidência executada, sem extrapolação

`python -m unittest backend.tests.test_s0_f03_history_seal_local -q`: **31/31 PASS**, Python 3.13 em diretório isolado. Este diretório contém **fac-símiles mínimos dos módulos S0 preexistentes**, utilizados somente para possibilitar testes de unidade das novas funções e drivers PG simulados. Os três arquivos de implementação, teste e fixture foram comparados com os blobs publicados; **os dois Python coincidem byte a byte com os testes executados**.

**Não** houve execução de SQL real, PostgreSQL 17, teste contra o checkout completo da S0, verificação de assinatura real, GitHub Actions ou integração F03 com modelo. Não contabilizar como 31 cenários homologados dos 70 SYN de E02.

## Limites técnicos atuais (deliberados)

- **Append-only não é o mesmo que completude.** O selo conserva os IDs visíveis naquele instante, mas não impede que mensagens retrodatadas sejam incluídas posteriormente por outras transações; `verify` poderá identificá-las e exigir revisão, não afirmar que eram impossíveis.
- Uma mudança entre a leitura e a persistência também pode ocorrer. A nova camada realiza rechecagens antes/depois e retorna falha fechada ao detectar diferença, mas **não** oferece uma transação única que feche todas as possibilidades de corrida. Não expor texto/mídia nem conceder proposta F03 antes de contrato transacional físico.
- Mesmo com um hash igual, **a S0 ainda não comprovou identidade multi-telefone, versões independentes de ficha/caso/catálogo, consentimento, escopo LGPD, provas semânticas e política de aplicação idempotente**.
- Estados do novo módulo: `SEALED_REVIEW_ONLY`, `ALREADY_SEALED_REVIEW_ONLY` e `MATCHES_LIVE_REVIEW_ONLY` são **apenas relatórios administrativos de laboratório**. Não existe `F03_READY`, `APPLIED`, `SENT` ou `PERDIDO` neste contrato.

## Próxima evolução direta da S0 por esta mesma frente OpenAI

1. Executar fixture e testes em PostgreSQL 17 descartável com a base S0 real e PR #12, verificando ACL/RLS, triggers e corrida de inserção retrodatada.
2. Se for necessário servir histórico ao modelo, projetar concessão estritamente autorizada e minimizada, separada do selo de metadados, com versões independentes e media unavailable sem conteúdo inventado.
3. Implementar recheck transacional final e contrato de aplicação em ficha pela S0 após o resultado F03 — nunca o modelo executando SQL/status.
4. Reconciliar alterações se a branch S0 base avançar. **Sem merge automático, sem alterar outros PRs e sem E05/API pagas.**
