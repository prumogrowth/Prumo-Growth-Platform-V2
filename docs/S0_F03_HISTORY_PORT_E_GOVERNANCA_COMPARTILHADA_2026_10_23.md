# S0 compartilhada — adaptação necessária à F03, sem bloquear na ausência de equipe exclusiva

> **Incremento posterior — selo persistente local (23/10/2026):** [documentação do módulo append-only](./S0_F03_HISTORY_SEAL_APPEND_ONLY_2026_10_23.md), [código](../backend/s0_f03_history_seal_local.py), [31 testes](../backend/tests/test_s0_f03_history_seal_local.py) e [fixture SQL local](../supabase/tests/s0_f03_history_seal_local_only.sql). O novo registro conserva metadados de pertencimento das mensagens com rechecagens S0 antes e depois, sem conteúdo e sem autorização de execução F03. **31 testes Python locais aprovados com dublês S0/PG; nenhuma validação PG17 física**. A evolução é autorada pela frente OpenAI na S0 compartilhada, em PR #16 independente.

**Data:** 23/10/2026. **Origem:** esclarecimento e autorização expressa do responsável. **Estado:** implementação offline em branch própria empilhada sobre o PR #12; não foi efetuado merge, deploy, migração nem intervenção na branch de outra frente.

## Decisão de governança — responsabilidade de implementação

A **S0 não possui atualmente uma frente dedicada e exclusiva**. Existiu uma frente anterior que a construiu, mas ela foi realocada. A S0 é infraestrutura **compartilhada**: quando uma frente funcional (inclusive OpenAI F01, F02 e F03) necessita de novas operações, **essa própria frente deve implementar/adaptar a S0**, mantendo as interfaces existentes, o isolamento das branches e a regressão das demais frentes. **Não esperar indefinidamente por uma frente S0 inexistente.**

A frente OpenAI continua responsável por **F01, F02 e F03 inteiras**, inclusive a parte S0 necessária ao contrato de cada função. Na S0, a autoridade real de autenticação, autorização, seleção de escopo, persistência e decisão comercial permanece estrutural; essa separação de competências **não transfere a F03 para outra frente**.

Estratégia segura para esta adaptação: partir do commit S0 `948891714f632adb6179cf3a11f362a6eb914f91` (PR #12), implementar em branch **`feat/oai-s0-f03-history-port-20261023`** e abrir um **PR independente com base na branch S0**. Isso evita editar a branch ativa do PR #12 ou aplicar alterações em outras frentes. Reconciliar/rebasear se o PR #12 avançar, testar regressões e só então avaliar integração; **nenhum merge automático**.

## Gap concreto e implementação nova

O recibo S0 existente `backend/s0_cfi01_f03_receipt_bridge_local.py` prova, após GoTrue/S1/HMAC e PG local, apenas **snapshot de mensagens de um caso**; não entrega histórico integral multi-casos da mesma pessoa/loja, catálogo ou versões independentes de ficha/caso. O leitor novo **não altera esse módulo existente**.

- `backend/s0_f03_history_manifest_local.py`: porta S0 local que exige **duas** verificações do recibo atual via `S0CFI01F03ReceiptBridgeLocal.recheck`, antes/depois da consulta. Busca `lead_id` e o corte `registrado_em` **do banco**, associados ao evento e ao hash original, sem aceitar identidade/loja/corte do cliente ou modelo.
- Consulta delimitada por `m.concessionaria_id`, `v.lead_id` e `m.criada_em <= e.registrado_em`, incluindo casos diferentes da mesma pessoa **naquela loja**; ordena por timestamp e ID, recusa registros duplicados, fora do corte, não verificados ou com watermark do fechamento ausente.
- Utiliza o **mesmo bloqueio de DSN PostgreSQL descartável local** da S0 existente, por composição: não herda métodos de captura/escrita do backend. Transação de leitura `REPEATABLE READ READ ONLY`, sem SQL de atualização, migrations, credenciais ou chamadas OpenAI.
- Retorna **somente metadados agregados** (quantidade de mensagens, casos e hash SHA256 dos IDs/proveniência), sem conteúdo de clientes. Sempre `REVIEW_ONLY_NOT_FROZEN` quando elegível: **isso NÃO autoriza F03 real nem aplicação da ficha**.
- Rejeita consulta sem recheck autenticado e restringe acesso ao leitor S0 concreto, evitando usar dados arbitrários enviados pelo modelo como autorização.
- `backend/tests/test_s0_f03_history_manifest_local.py`: **24 cenários unitários** cobrindo vínculo multi-casos, autorização, revogação, cutoff, ausência de watermark, duplicidade, cronologia, isolamento e segurança do leitor.

## Evidências e limites

**24/24 testes locais aprovados em Python 3.13**, com **fac-símiles estritamente de teste** das classes S0 importadas; quatro dos cenários exercitam a execução de consulta via driver PostgreSQL simulado; a implementação e os testes publicados tiveram seus hashes Git comparados byte a byte com os arquivos executados. **Os testes ainda precisam rodar dentro do checkout completo S0 com suas classes reais e em PostgreSQL 17 descartável.** Não afirmar CI, PG17 ou GoTrue real nesta rodada.

A seleção feita por timestamp em transação de leitura não congela de forma durável **todos os casos**: uma nova inserção retrodatada pode alterar seleção histórica. Assim, mesmo com 2 rechecks a porta **não afirma `historyComplete` nem libera conteúdo**. Para promover a F03 é preciso evento imutável de manifesto multi-casos (evidências+hash+cutoff), acesso autorizado a texto/mídia, versão da ficha/catálogo/caso/identidade distintas, retenção e política física de aplicação idempotente com lock/compare-and-swap na S0. O resultado `REVIEW_ONLY_NOT_FROZEN` é explícito, nunca `VERIFIED_FULL_HISTORY`.

**Próxima fase E04**: homologar leitura real em fixture S0 PG17 (ainda não executada), incorporar congelamento multi-casos, recheck transacional e contrato de proposta F03. E05 (OpenAI API/Meta/Banco/dados reais), deploy e merge continuam fora da autorização atual.
