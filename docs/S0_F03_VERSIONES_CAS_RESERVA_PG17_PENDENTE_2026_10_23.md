# E04/S0 F03 — Vetores independentes e reserva CAS consultiva (23/10/2026)

> **Diagnóstico adicional — falha transversal dos runners:** um workflow independente da frente Meta, [WA39 #40038431638](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40038431638), também foi marcado `failure` com **`runner_id=0` e `steps=[]`**, em horário próximo. Isso reforça impedimento compartilhado do GitHub Actions (runner/cotas/política/conta), mas **não demonstra qual causa específica**. A configuração de conta e as anotações do job precisam ser vistas pelo responsável no GitHub. Não modificar a frente Meta nem afirmar que o CAS passou testes físicos.

**Situação:** código de laboratório implementado no PR #16, ainda **não homologado no PostgreSQL 17** nesta rodada porque o GitHub Actions não iniciou o runner. Este incremento permanece estritamente sintético; não altera fichas, campos, catálogo real, status comercial, banco ou API OpenAI.

## Objetivo e escopo real

A F03 precisa saber se a informação extraída de um histórico continua válida no momento da decisão. A versão do **ciclo comercial não basta**, pois a ficha, o catálogo, o caso, a atribuição humana e a identidade do cliente podem mudar independentemente. Os módulos atuais registram o fechamento humano e as provas de histórico/HMAC, mas ainda não disponibilizavam estas cinco versões como fontes independentes.

Foi criada a fixture SQL [`s0_f03_versions_reservation_local_only.sql`](../supabase/tests/s0_f03_versions_reservation_local_only.sql), **não** migration:
- `cfi01_f03_catalog_versions_local`: versão por concessionária.
- `cfi01_f03_lead_versions_local`: versões independentes de ficha e identidade por cliente/loja.
- `cfi01_f03_case_versions_local`: versões de caso e atribuição humana, vinculadas ao caso S0 e ao seu lead.
- `cfi01_f03_reservations_local`: recibo append-only **somente consultivo** de proposta, único por concessionária+evento de encerramento, referenciando a prova HMAC persistida. Um trigger confere loja/caso/lead/chave e outro proíbe UPDATE/DELETE. RLS e grants negam acesso direto a `anon`, `authenticated` e `service_role`.

O [`backend/s0_f03_version_reservation_local.py`](../backend/s0_f03_version_reservation_local.py) implementa `VersionVector(form,catalog,case,assignment,identity)` e **reserva uma proposta sem aplicá-la**. O fluxo:
1. A ponte `S0F03LocalVersionReservationBridge` exige `MATCHES_REVIEW_ONLY` do verificador autenticado S0 do HMAC/histórico antes de chamar o backend e novamente após a operação.
2. A S0 recupera do encerramento **a pessoa real**, bloqueia em ordem fixa o catálogo da loja, a versão da pessoa e a versão do caso, confere vínculo com atribuição humana ativa, versão do ciclo do caso e existência da prova HMAC persistida.
3. Compara **as cinco versões físicas de fixture** e a versão da chave. Se faltar prova, fonte ou houver desatualização, retorna recusa sem criar recibo. Se houver correspondência, insere o recibo com `ON CONFLICT DO NOTHING`; reprocessamento da mesma requisição/proposta/vetor devolve `ALREADY_HANDLED_REVIEW_ONLY`; tentativa concorrente diferente para o mesmo encerramento devolve `CONFLICT_REVIEW_REQUIRED`.
4. **Não incrementa nem altera versões da ficha, nem escreve campos da ficha**; não faz operação de "vendido"/"perdido", Meta, banco ou modelo. É **reserva consultiva**, não transação de aplicação cadastral.

## Cenários preparados para testes

- [`backend/tests/test_s0_f03_pg17_integration.py`](../backend/tests/test_s0_f03_pg17_integration.py): acrescidos **18 testes físicos** (24–41) de PG17; total desta suíte: **41**. Testam cinco versões independentes, ciclo divergente, ausência de fonte/prova, encerramento da atribuição, idempotência, dois escritores idênticos e dois concorrentes com propostas conflitantes, imutabilidade e ACL da reserva, inexistência de atualização de ficha/status e retomada após mudança de versão.
- [`backend/tests/test_s0_f03_version_reservation_local.py`](../backend/tests/test_s0_f03_version_reservation_local.py): **18 novos testes unitários**, cobrindo tipos, vetor inválido, erro de banco, isolamento do DSN, autenticação antes/depois da operação, revogação, sigilo do retorno e versão inválida.
- [`scripts/run-s0-f03-pg17-local.sh`](../scripts/run-s0-f03-pg17-local.sh): inclui agora a fixture nova e os 18 testes unitários além das suítes já validadas. **Resultado esperado, se todos aprovarem:** 84 S0 existentes + 24 leitor F03 + 31 selo metadados + 15 autorização HMAC + 18 CAS unitários + 41 físicos F03 = **213 testes**. **213 não é uma contagem aprovada**, só soma das suítes preparadas.

## Diagnóstico de execução e transparência

A última execução comprovadamente **aprovada** antes desta alteração é [GitHub Actions #40032787969](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40032787969): **177/177 PASS no PostgreSQL 17.11**.

Ao publicar esta alteração, o GitHub criou novas execuções, incluindo [#40038892619](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40038892619) e [#40038713852](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40038713852), todas registradas como **failure**. **O ponto crucial:** o GitHub registrou `runner_id=0`, zero etapas iniciadas (`steps=[]`) e conclusão em poucos segundos, e o download de logs retornou **`BlobNotFound`**. **Nenhum erro de código/SQL nem origem precisa do bloqueio foi confirmado.** A API de checks informa duas anotações, mas a ferramenta conectada não permitiu ler o conteúdo delas. É possível haver uma restrição de disponibilidade, política ou faturamento do Actions, **mas não há prova suficiente para declarar qual**.

**Ação para destravar o ambiente:** abrir [o último job do Actions](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40038892619) no GitHub e conferir a mensagem de erro/aviso no topo da execução (em especial questões de limite, cobrança, permissão ou runner). Se houver exigência de ajuste administrativo, o responsável pode encaminhar **o texto da mensagem**, sem compartilhar credenciais. Nenhuma instalação no computador, Supabase de produção ou API OpenAI é necessária.

## Limites de arquitetura ainda abertos

Essas versões são **fixtures S0 de laboratório**, não os registros reais de versão da ficha/catálogo em produção. A reserva serializa disputas pelo **mesmo evento de encerramento**, mas não aplica campos e ainda não representa CAS de escrita numa ficha operacional compartilhada por múltiplos casos. Para avançar, conectar as versões aos escritores S0 reais, catálogo ratificado, evidências campo a campo, mídia e transação final única de aplicação, com auditoria e política LGPD. Sem permissão para criar status comerciais, novos campos ou usar E05.

**Separação de responsabilidade:** a frente OpenAI desenvolve a adaptação S0 diretamente, sem depender de uma equipe S0 exclusiva. PR #12 não deve ser modificado; PRs continuam em Draft.
