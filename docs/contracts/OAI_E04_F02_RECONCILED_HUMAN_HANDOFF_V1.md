# E04 F02 — solicitação de ratificação humana pós-humana reconciliada (handoff para Codex/S0)

**Data:** 2026-10-26 (America/Recife). **Responsabilidade:** F02 desenvolve contrato isolado; **Codex é o responsável principal pelo núcleo oficial S0**. **Escopo:** laboratório E04, branch `feat/oai-s0-f03-history-port-20261023`, PR #1 Draft, **sem aprovação para integração ou execução real**.

## Resultado efetivo e referência imutável

- Módulo novo **somente F02**: `backend/f02_reconciled_human_authorization_handoff.py`. Nenhuma importação do núcleo S0, conexão a banco, serviço de IA, rede, código de agendamento, Meta ou mutação de ficha. Apenas validação e hash SHA-256 de um **pedido não autenticado**.
- Testes novos: `backend/tests/test_f02_reconciled_human_authorization_handoff.py` (21 testes unitários, escopo, versões, integridade, estados, normalização UTC, idempotência, recusa de permissões declaradas) e dois cenários sintéticos físicos #329–330 acrescentados **somente à suíte experimental da branch** em `backend/tests/test_s0_f03_pg17_integration.py` (não ao núcleo oficial S0). `scripts/run-s0-f03-pg17-local.sh` inclui o módulo de teste, mas nenhum arquivo `.github/workflows` foi editado.
- **GitHub Actions #40294600994 SUCCESS**: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40294600994, código `f9215c26b4a5a39df49d95ecd320a5c461432f4b`. **84/84 S0 + 537/537 F02/F03 Python, inclusive 330 testes físicos PG17**, e **269/269 Node** no S2 fixado. Total **890 verificações em suítes distintas**, não 890 jornadas completas nem os 70 oráculos E02 homologados.
- Primeira execução deste acréscimo (#40294195792) falhou num cenário negativo que buscava ler uma testemunha C08 inexistente para envio previamente `reservado`. A correção **não produziu recibo fictício**: passou `None` (prova ausente) para a validação estrita, produzindo recusa. Novo CI integral passou. A S0/C08 original não foi alterada.

## Formato de entrada tipada, sem confiança

**`ClaimedS0Evidence`** recebe UUIDs de `shop_id`, `lead_id`, `case_id`, `closure_id`, a classificação `LOCAL_LEGACY_EVIDENCE_REVIEW_ONLY`, origem `LOCAL_OBSERVED_ORIGIN_REVIEW_ONLY`, marcador `E04_SYNTHETIC_S0_C08_REVIEW`, hashes hexadecimais de 64 caracteres de recibo F03, testemunha C08 local, ledger e intenção humana sintética. Esses campos são **afirmações não verificadas pelo módulo F02**, mesmo que tenham sido extraídos de fixtures físicas.

Também recebe explicitamente `EXTERNAL_DISPATCH_UNVERIFIED` e `HUMAN_OPERATIONAL_AUTHORIZATION_NOT_RATIFIED`. O código **rejeita** valores declarados `META_CANCELLED` ou `APPROVED`; o modelo ou cliente não podem se autoconceder autoridade.

**`ReviewOnlyProposal`** recebe mesmo escopo de loja/lead/caso/fechamento, canal, template, versão canônica de template `vN`, versão de política, horário proposto com fuso, chave de idempotência e ação **exata** `REQUEST_S0_HUMAN_RATIFICATION_ONLY`. O módulo valida escopo comum, formato, classe exata das dataclasses, timestamps timezone-aware e nenhuma ação `SEND_NOW`.

**`HandoffResult`** contém apenas `status`, `untrusted_request_sha256` opcional e `contract_version=F02_S0_RECONCILED_HUMAN_HANDOFF_V1`. O retorno bem-sucedido `HANDOFF_REVIEW_ONLY` significa **somente documento apto à revisão independente**, nunca envio ou aprovação. SHA-256 é calculado sobre JSON canônico dos campos com timestamps normalizados para UTC; não é assinatura HMAC, token, recibo S0 ou prova contra um remetente malicioso. Nenhuma senha ou dado conversacional é armazenado.

## Condições que devem ser resolvidas PELO CODEX/S0 antes de incorporação

1. **Autenticidade do recibo e escopo:** autenticar principal e sessão reais, conferir no próprio S0 o HMAC, case/cycle, tenant/lead, versões, cutoff F03 e titularidade das provas. Não aceitar os valores de `ClaimedS0Evidence` como afirmações confiáveis; uma cadeia de caracteres de 64 hex não prova origem legítima.
2. **Aprovação humana operacional separada:** definir ato ratificado por gestor habilitado S1, finalidade, limites, validade, cancelamento/revogação e trilha de auditoria. O registro sintético da intenção não substitui aprovação operacional.
3. **Transporte e opt-out:** confirmar de forma independente o estado de mensagens antes `reservado` junto ao provedor externo, política atual de templates Meta, base legal/consentimento real, opt-out posterior e elegibilidade antes do eventual envio.
4. **Controle transacional:** definir quem pode transformar pedido de revisão em futura decisão S0 assinada, com idempotência, expiração, concorrência e rechecagem imediata antes de reservar qualquer novo plano. Este módulo **não implementa** essa transformação.
5. **Integração sob coordenação:** Code Review do Codex, branch específica de integração, execução de regressões E02/S0/S1/S2, rollback, aprovação explícita antes da `main`; implementação no Supabase hospedado continua adiada até autorização para a integração geral.

## Garantias negativas demonstradas

- No #329, a cadeia PG17 realmente observada antes do caso humano, cancelada C08 e conciliada pela S0 gera apenas o hash de pedido F02; o banco fica sem minuta pós-humana nova e sem envio ativo.
- No #330, uma tentativa anteriormente reservada não gera testemunha C08 válida. A F02 recebe prova ausente e retorna `DENIED_MALFORMED` sem hash, independentemente de qualquer tentativa de assumir cancelamento.
- Nenhuma alteração ao núcleo oficial S0, C04 legado, workflow de outras frentes, Supabase hospedado, Meta, clientes reais, `main`, Issue #3 ou execução em produção.

**Status para Codex:** `F02_REVIEW_HANDOFF_ONLY_NOT_AUTHORIZED_FOR_S0_PROMOTION`. O PR #1 continua Draft e todos os desenvolvimentos anteriores seguem válidos como propostas isoladas.
