# E04/S0-F03 — preparação de integração física PostgreSQL 17 descartável (23/10/2026)

> **ATUALIZAÇÃO DE EXECUÇÃO REAL — 23/10/2026:** os testes físicos que estavam pendentes **foram executados** no GitHub Actions. [Relatório auditado](./S0_F03_PG17_CI_HMAC_2026_10_23.md): [run #40027116504](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40027116504) **150/150 PASS**, seguida de [run #40027635632](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40027635632) **153/153 PASS**, incluindo **14 testes físicos F03**. Novo leitor S0 [HMAC-SHA256 de conteúdo](../backend/s0_f03_content_integrity_local.py) detecta alteração de texto do caso anterior em PG17. A seção original de 0/11 abaixo é registro histórico **anterior** ao CI, não situação atual. O HMAC ainda não está persistido/associado a um grant F03.

**Estado:** scripts e suíte de integração publicados no PR #16, sem execução física nesta sessão. A S0 é infraestrutura compartilhada e esta adaptação é desenvolvida pela frente OpenAI, sem editar o PR #12. Não há nenhuma chamada a Supabase hospedado, cliente real, API Meta/OpenAI, migração ou deploy.

## Materiais executáveis

- [Executor manual `scripts/run-s0-f03-pg17-local.sh`](../scripts/run-s0-f03-pg17-local.sh): **não** é workflow de disparo automático; exige `PRUMO_TEST_DATABASE_URL` explicitamente apontando para `localhost/127.0.0.1/::1` e o nome **exato** `/prumo_s0_test_cfi01`; rejeita opções da URL e variáveis `PGHOST/PGHOSTADDR/PGPORT/PGDATABASE/PGUSER/PGSERVICE/...` que poderiam redirecionar a conexão. Reaproveita o executor CFI-01 físico já existente, exige versão **PostgreSQL 17**, instala a fixture SQL **somente na base descartável** e executa as suites F03 de leitor, selo e integração física.
- [11 testes físicos `backend/tests/test_s0_f03_pg17_integration.py`](../backend/tests/test_s0_f03_pg17_integration.py): classe com `skipUnless` para banco estritamente local de fixture, cenários sintéticos de autenticação/S1/encerramento real da S0 existente, leitura multi-casos do mesmo lead/loja, persistência apenas de metadados, idempotência, inserção retrodatada em caso histórico, gatilho de vínculo caso/lead, imutabilidade contra UPDATE/DELETE, negação de leitura ao papel `authenticated`, conflito em replay, isolamento entre lojas e pessoas.
- O teste **11** mostra explicitamente a lacuna de segurança: alterar `conteudo_sintetico` de mensagem de caso antigo preserva os IDs e o hash **de pertencimento**. O selo não prova integridade de conteúdo. O teste documenta o problema para impedir um falso gate de liberação de F03, não para aceitá-lo como comportamento de produção.

## Execução manual em ambiente autorizado

Pré-requisitos: **PostgreSQL 17 local descartável** disponível, binários `psql` e cliente `psycopg[binary]`, usuário de fixture local, `PRUMO_TEST_DATABASE_URL` com banco vazio preparado e todo o checkout do PR #16. Usar **somente dados inventados**.

```sh
export PRUMO_TEST_DATABASE_URL='postgresql://postgres:postgres@127.0.0.1:5432/prumo_s0_test_cfi01'
bash scripts/run-s0-f03-pg17-local.sh
```

O script roda também o bootstrap e os testes PG17 CFI-01/S0 preexistentes no início. **Não** executa migrações hospedadas e **não** deve ser apontado para Supabase remota. Não criar/ativar GitHub Actions ou tarefas cobradas para testar sem avaliação separada de custo.

## Evidência desta rodada: somente verificações sem PG17

1. **Sintaxe do novo teste Python:** `python3 -m py_compile` passou, sem executar importações de produção.
2. **Sintaxe do executor Shell:** `bash -n` passou.
3. **Três ensaios negativos reais do executor:** remoto `hosted.example.com`, nome `/postgres` em localhost e `PGHOST` forçado foram todos **recusados com exit 1 antes de conectar**.
4. **Arquivos do GitHub conferidos por SHA de blob com arquivos validados localmente:** teste com 11 cenários = `751dc40f5a6968166993553a3883266dab6ade1c`, runner = `ef3a5c29f0e131d202907b042b3586aeb72d9874`.
5. **O servidor PostgreSQL/psql não estão instalados neste ambiente**, portanto **0/11 testes físicos executados aqui**. Os 24+31 testes anteriores de contrato/leitura e selo passaram isoladamente com dublês de S0/PG em rodada anterior; **não foram repetidos nesta sessão nem autorizam declarar 66 testes PG17 aprovados**.

## Próximo código necessário para fechar o gate F03

- Ligar o histórico a uma **prova de integridade de conteúdo** protegida contra ataque de dicionário e sem vazamento (por exemplo HMAC com chave retida exclusivamente na S0); validar também conteúdo de mídia e alterações retroativas. A prova de pertencimento de IDs atual é **insuficiente**.
- Dar ao manifesto completo um fechamento **transacional** que impeça janelas de inserção retrodatada e confira identidade/ciclo/caso/atribuição de forma atômica, com concorrência entre consumidores.
- Separar versão física da ficha/catálogo/caso da versão do ciclo e habilitar concessão mínima de leitura do conteúdo para F03 somente depois de autorização S0 ratificada; recheck/cancelamento antes da gravação.
- Executar o conjunto em PG17 realmente descartável, auditar RLS, triggers, múltiplas transações e rechecks; corrigir falhas encontradas. **Não promover qualquer estado REVIEW_ONLY a autorização de F03**.

**Gates:** E04 offline autorizado; E05 API real, custos, hosted Supabase, dados reais, deploy e merge continuam não autorizados.
