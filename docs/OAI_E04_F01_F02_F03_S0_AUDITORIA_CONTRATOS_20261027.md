# Auditoria direta F01/F02/F03 ↔ S0 — 27/10/2026
**Escopo:** leitura comparativa de fontes GitHub. Nenhuma alteração nas branches ou runtime da S0. Não é homologação operacional nem auditoria de segurança exaustiva.

## Fontes consultadas
- F02 HEAD `2171d9a17e6d3e345cc52b432294ad1a244f16e0`, CI #40492836774 SUCCESS: `prepare_handoff`, `ReviewWindow`, `inspect_claimed_proof_binding` e testes A27.
- S0/F02 PR #18 HEAD `88af4aea3aeb2c403bab4c078fdc04d560f2cba0`: `backend/s0_f02_review_registry_local.py` (somente leitura), contrato de registro e CI física #40414847271.
- S2/OpenAI F01/F02/F03 HEAD `ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c`: `journey.mjs`, `f03-commit-gate.mjs` e `plan-lifecycle.mjs` (somente leitura).
- Código S0/F03 inspecionado, sem alteração: `s0_f03_history_manifest_local.py`, `s0_f02_legacy_observed_origin_local.py`; auditoria auxiliar S0 `7c282df5f6e5942729f15187c199dffb5e872797`.

## Achados
1. **Divisão de responsabilidade:** titularidade ratificada pelo usuário na ADR; não terceirizar comparação F01/F02/F03 ou leitura de S0.
2. **Divergência concreta corrigida na F02:** `prepare_handoff` calcula SHA256 da proposta e alegações, **sem janela**. O `prepare_document` da S0 persiste `requested_at`/`expires_at` no documento integral e sua idempotência considera o documento/prazo. O validador anterior aceitava envelope candidato sem vínculo de janela. Agora exige `ReviewWindow`, `review_window` e igualdade por instante UTC, bloqueando trocas, truncamento, inversão e mudança DST. Não se tenta verificar autenticidade S0 nem reproduzir HMAC S0.
3. **Semântica temporal pendente, não falha S0:** S0 lê mensagens F03 com `m.criada_em <= closure_at`. O `observed_at` candidato F02 é hora de **inspeção alegada**, não hora do evento original. Não transportar a desigualdade `closure_at <= observed_at <= cutoff_at <= proposed_at` para timestamps das fontes reais; acertar contrato por prova antes da integração.
4. **Produtores não equivalem a provas atestadas:** `S0F03LocalHistoryManifestBridge.inspect` fornece contexto/metadados de histórico; não entrega diretamente o hash de recibo F03 final. Os quatro hashes `ClaimedS0Evidence` permanecem alegações. HMAC/autenticidade/revogações precisam de fontes S0 no futuro.
5. **Jornada OpenAI ainda offline:** `evaluateOfflineJourney`, `evaluateF03CommitCandidate` e `reconcileF02Plan` são funções sem I/O; as booleans S0 vêm de fixtures. Não inferir jornada física F01/F03/F02 de testes separados.
6. **Edição S0 agora:** nenhum erro novo obrigando patch S0 foi demonstrado nesta revisão. Lacunas já conhecidas G02/G03/G04/G07 são decisões/implementações da S0 quando chegarem à etapa aprovada, e não motivo para solicitar nova auditoria geral.

**Limites:** avaliação dos contratos e funções citadas, não inventário completo, não reexecução da suíte S0 no ambiente original. A regressão GitHub Actions da F02 verifica o novo ajuste depois do commit.

## Próxima integração
Preservar os sete gates sem autorização; F01/F02/F03 são auditados e ajustados nesta frente. Somente uma necessidade específica comprovada no domínio transacional S0 poderá ser encaminhada a sua frente, com contrato, linha de código, impacto, negativos e critério de aceite. Sem revisão geral delegada.
