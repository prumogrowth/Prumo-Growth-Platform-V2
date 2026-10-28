# Meta Cloud — convergência das auditorias #36, #37 e #39

**Data:** 28/10/2026. **Base:** PR #39, SHA `92c67bb0b0d07a67eff1861fdff0769d692832c1`. **Branch:** `audit/meta-cloud-convergence-20261028-v1`. Implementação experimental offline, não ratificada.

## Estado e motivação

Os PRs #36 e #37 surgiram em paralelo a partir do mesmo PR #34, e ambos protegeram a configuração confiável do compositor. O PR #37 acrescentou seleção de leitores com HMAC preservada; o PR #39, empilhado sobre #37, acrescentou validação sintática de identificadores técnicos.

**Diferença não incorporada na cadeia #37 → #39:** o PR #36 também corrigiu `cloud-webhook-handoff.ts` diretamente, protegendo os leitores individuais que utilizam essa fronteira e que não herdam necessariamente o snapshot de configuração do compositor. Por isso, o verde do #39 não assegurava a segurança do verificador compartilhado.

## Auditoria vermelho/verde

Foi adicionada `cloud-convergence-scope.test.ts`, com **12 testes** sobre o comportamento direto da fronteira HMAC e dos leitores de seleções, reações, mídias, mensagens não suportadas e erros de status. Também testa a manutenção das decisões do compositor seletivo e do guard de identidades técnicas do PR #39.

- **RED — GitHub Actions #40662148803** (`87890fa061d00b8791c5bbda60df398e05f0c22d`): 4/12 passaram e **8/12 falharam** na base #39, demonstrando a lacuna em caminhos diretos.
- **GREEN de implementação — GitHub Actions #40662227982** (`255a38b8b7b1b0db95c8dd02b715d25486e86a82`): 12/12 aprovados, após o reparo.
- Workflow final `meta-cloud-convergence-offline.yml`: executa **12 testes novos e 214 regressões focadas** da cadeia #37/#39 e todos os leitores especializados. A verificação no **HEAD final exato** é obrigatória antes de declarar a integração candidata certificada.

## Alteração de código

Somente `integrations/whatsapp-meta/cloud-webhook-handoff.ts` recebeu ajuste de lógica: antes do primeiro `await`, o verificador cria snapshots congelados dos campos primitivos `waba_id`, `phone_number_id`, `revision`, `maxBodyBytes` e `maxEvents`. A verificação de validade da rota, os limites, o parse autenticado, a checagem do escopo e o `route_revision` devolvido passam a usar esses snapshots. O efeito é equivalente ao reparo independente do PR #36 para essa fronteira.

A composição de #39 **não foi substituída**: mantém a seleção por tipos verificados, 1–6 HMACs de acordo com o lote, guard de identificadores, atomicidade de negação, ausência de dedupe durável e todas as flags de autoridade falsas.

## Resolução futura da sobreposição

Esta branch é uma **candidata de convergência**, não um merge executado nem uma instrução para mesclar automaticamente. O PR #36 contém outras alterações/documentos e permanece Draft. Se esse PR for integrado primeiro, deve-se reconciliar ou retirar a alteração sobreposta de `cloud-webhook-handoff.ts` ao avaliar esta branch, evitando que duas versões concorrentes sejam mescladas sem revisão.

A validação efetiva dos formatos com provedor Meta real e a semântica de S0, ingestão durável, ACK, retry, mensagens enviadas, clientes e permissões continuam **fora do escopo**. Não houve Graph GET/POST, token/segredo real, HTTP 200, Supabase, S0/S1, deploy, merge ou dados pessoais reais.

**Dependência nova imediata de outra frente:** nenhuma. Contratos candidatos dos PRs #14/#19 não ratificados.
