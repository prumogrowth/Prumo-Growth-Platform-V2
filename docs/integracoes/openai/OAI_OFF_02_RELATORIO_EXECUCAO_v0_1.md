# OAI-OFF-02 — Relatório de execução local (31/10/2026)

**Status honesto:** `PARTIAL_WITH_BLOCKERS` — fronteira candidata implementada e validada localmente; publicação GitHub e regressão integral de 342 testes herdados não concluídas neste ambiente. **Não** chamar isto de entrega integrada/homologada.

## Origem e escopo

Repositório oficial: `prumogrowth/Prumo-Growth-Platform-V2`.
Base fixada (consulta GitHub): OFF-01 commit `394512327cd3756dfbe61ff970a6279c354b6565`, árvore `87a3ce85b2ead682038d4bee104ca47dd006c971`. Base S2 ancestral `1747cb0fee2a95322dc768044bafe9817d8cc540`. Branch de trabalho pretendida `feat/oai-off02-typed-boundary-20261031`; **nenhuma branch nova foi publicada** a partir do ambiente de execução.

A internet/host Git não estava acessível ao terminal de execução (`Could not resolve host: github.com`). Os seis arquivos S2 relevantes foram reconstruídos **byte a byte** das fontes já consultadas no GitHub: `core.mjs`, `journey.mjs`, `f03-commit-gate.mjs`, `plan-lifecycle.mjs`, `template-frequency.mjs`, `transport-evidence.mjs`; seus IDs `git hash-object` conferiram, respectivamente:

```
f5be662cc7db925f99802cc251f432b90fb0aa15
b5ecf051e7bc30d5653ab214ffff6e731f6bbded
13b60983b824bcbe145eb708d8b503e10aa45ba9
fb21fe91ad9c6b4e8de9cf6be79ef42127b30655
b9e9cfbf9be4fe58778a26e60cedeaf545e14713
7a7d13490e53ebc32ef3f2fdb4fbd47e61cadb20
```

O `package.json` local também conferiu pelo blob `9364ed6bf049ce4944292349524a6dd30d1344c2`. Nenhum arquivo S2/OFF-01 da base deve ser alterado ao aplicar o pacote. O pacote/patch contém **apenas arquivos novos**.

## Arquivos novos para aplicar sobre a base OFF-01

1. `docs/integracoes/openai/e04_offline_lab/typed-boundary.mjs`: schema privado, projeção allowlisted, parsing estrito, retorno tipado, timeout/replay e audit log sanitizado.
2. `docs/integracoes/openai/e04_offline_lab/s2-guard-links.mjs`: reuso de `journey`, `f03-commit-gate`, `plan-lifecycle`, `template-frequency`, `transport-evidence` por interfaces sintéticas sem autoridade.
3. `docs/integracoes/openai/e04_offline_lab/tests/typed-boundary.test.mjs`: 61 testes nativos positivos/adversariais.
4. `docs/integracoes/openai/OAI_OFF_02_FRONTEIRA_TIPADA_CANDIDATA_v0_1.md`: contrato lógico e riscos.
5. `docs/integracoes/openai/OAI_OFF_02_MATRIZ_E02_ESTRUTURAL_v0_1.md`: rastreabilidade parcial, sem PASS E02.
6. `docs/integracoes/openai/OAI_OFF_02_RELATORIO_EXECUCAO_v0_1.md`: este relatório.

## Testes efetivamente executados

- Node.js **22.16.0**, npm disponível; Git **2.47.3**, POSIX local.
- `node --test .../tests/typed-boundary.test.mjs`: **61/61 PASS**, zero fail, zero skip.
- `npm test` com o `package.json` original e **somente a suíte nova** presente no checkout local: **61/61 PASS**. Este `npm test` **não** representa os 342 testes herdados, que não estavam no checkout de execução.
- A contagem anterior de 269 testes S2 + 73 testes OFF-01 = 342 pertence ao **relatório anterior do Codex**, não foi reexecutada nesta entrega.
- `git hash-object` de sete arquivos S2/package coincidentes com os blobs oficiais. Não é prova de execução de testes antigos.
- O preflight com os quatro checkouts e `--operation a38` **não** foi reexecutado; ausência da fonte histórica permanece um bloqueio.

## Auditoria de segurança

Testes com canários verificam exclusão de HMAC/IDs privados/credenciais/roster por schemas estritos, isolamento de instruções, rejeição de extras e `tool_calls`, JSON duplicado, protótipos/getters, autorização antes de stale, cutoffs, conflito F03 omitido, versão alterada, replay divergente, 131049 e ausência de `sent` após mera aceitação Meta. Tripwires interceptaram `fetch`, temporizadores, leitura/escrita de arquivo e spawn/exec durante o fluxo sob teste: **zero chamadas**. Revisão estática dos novos módulos não encontrou imports HTTP/FS/processo/SDK, SQL nem clientes hospedados. Hash do replay não prova autorização ou idempotência real.

**Reparos durante desenvolvimento:** inclusão do selo interno de contexto para rejeitar envelopes forjados, congelamento da cópia privada, bloqueio de arrays esparsos, verificação de claims sintéticos F03 além de fonte citada, validação extra antes de hash do replay. Todos passaram na rodada final.

## Dependências à frente S0/Meta (sem modificar outras frentes)

| Necessidade | Evidência disponível | Lacuna / deltas futuros | Consumidor offline |
|---|---|---|---|
| Identidade por loja e pessoa multitelefone | Gate S2 por store/person e documento CFI | Prova física de resolução e anti-fusão entre clientes | `f03Task` + teste multi-casos |
| Manifesto histórico completo até cutoff | Metadados de encerramento e watermark candidatos | Conteúdo multicasos, meios e vínculo transacional S0 | `prepareF03History`, aliases F03 |
| Autorização/mídia/retenção | Flags sintéticas | Fonte real consentida e mídia recuperável | projeção F03 rejeita indisponível |
| Domínios de versão e revisão atômica | S0 OPS-02 posterior a F03 | Recibo físico, copy/precommit e estado atual | `scope.expected/current`; retorno recheck |
| Quatro provas F02, lifecycle e Meta | S2 `plan-lifecycle`, `template-frequency`, `transport-evidence` | Binding S0, consentimento e `sent` assinado/atestado | `runSyntheticGuard` |
| Continuidade entre sessões/replay | Tag e hash locais determinísticos | Livro durável/idempotência S0, clock e concorrência | `simulateOfflineExchange` |
| Opt-out e finalidade segregada | F02 fixture | Prova por loja e versão na S0/Meta | `f02Task` |
| A38 histórica | OFF-01 pin preservado | Fonte `ebf6fe...` não recuperada | bloqueio documental |

A fonte F03 e a S0 OPS-02 têm dois módulos CFI com bytes diferentes. **Não** copiar a versão antiga da F03: a S0 posterior rechecava payload/`expected_receipt` antes do COMMIT. Nada da frente S0 foi alterado.

## Critérios não satisfeitos / próximo passo

Os testes antigos e a fonte A38 não estavam completos no workspace local; por isso não se atribui `DELIVERED_OFFLINE_CANDIDATE` integral nem commit/tree oficial novo. O patch deve ser aplicado sobre **exatamente** `3945123...` em branch exclusiva, então executar `npm test` com as sete suítes originais presentes, verificar os 342 herdados + 61 novos = **403 esperados, não verificados**, inspecionar diff e publicar branch sem merge. O total 399 é projeção matemática, não resultado executado.

O próximo desenvolvimento funcional é OFF-03 F03 (manifesto/histórico/proveniência) em consumidora sintética, sem S0 paralela. Qualquer integração real exige contrato ratificado e autorização separada.
