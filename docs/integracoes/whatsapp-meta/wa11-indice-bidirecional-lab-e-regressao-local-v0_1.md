# WA-11 — vínculo bidirecional tentativa técnica ↔ wamid (offline)

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Data:** 19/10/2026. **Escopo:** PR #2 Draft, somente laboratório Node.js/TypeScript, sem Meta Graph, banco hospedado, credenciais, mensagens reais, merge ou deploy.

## Lacuna concreta (após WA-10)

O `FakeAttemptBindingLedger` da WA-10 já recusava a **mesma tentativa** apontando para **dois wamids**. Porém, quando chamado diretamente, ainda permitia que um **mesmo wamid** de App/WABA/emissor fosse associado a **tentativas diferentes**. O `FakeMetaStatusReconciler` já possuía uma proteção própria por chave de mensagem, mas o ledger isolado não garantia ambos os sentidos. Havia também múltiplas leituras do objeto de entrada após a validação, permitindo inconsistência com propriedades interceptadas por `Proxy`.

## Implementação de código

- `integrations/whatsapp-meta/attempt-binding.ts`: adiciona índice direto `[app_ref, waba_id, phone_number_id, provider_message_id]` além do índice inverso `[app_ref, concessionaria_id, attempt_id]`; a tupla técnica integral deve ser idêntica nos dois índices para um replay `SAME`. Qualquer colisão retorna `CONFLICT` **antes** de gravar qualquer índice. A inserção é síncrona e exclusivamente em memória, não é atomicidade PostgreSQL.
- O validador gera um único snapshot por descritores próprios de dados (sem accessors ou campos extras), usando seus valores para validar e inserir. Isso evita alternância entre leitura validada e leitura utilizada na associação. Não equivale a autenticação do chamador ou validação do escopo pela S0.
- `integrations/whatsapp-meta/attempt-binding.test.ts`: adiciona `WA11-01..07` (colisão direta, isolamento App/WABA/emissor, tentativa de troca de loja, ausência de mutação em conflitos, capacidade e objeto adversarial com `Proxy`). O caso antigo `WA10-09` passa a usar um wamid único por tentativa, pois a fixture anterior não atendia à nova invariante de unicidade direta.

A entrada continua exigindo referência Graph tecnicamente aceita pelo chamador e escopo pré-validado. **Nenhum dos índices concede envio, ACK, retry, estado comercial nem prova entrega.** A S0 permanece autoridade comercial e deverá implementar as unicidades duráveis transacionalmente, após aprovação do contrato.

## Evidências realmente executadas

Ambiente: Node.js **v22.16.0**, TypeScript local, checkout **parcial reconstruído** a partir dos arquivos GitHub e com SHA de blob conferido. Nenhum CI, API externa ou custo acionado.

1. Baseline WA-10 original: SHA `e50c98da1ba090ffc7bee6c68f515c4595a7da88` e teste `1132bc1a509d4a42cdb2e703fb0047d7281e1a6b` → **11/11 PASS**.
2. Prova do defeito: com `WA11-01..07` e código original, **18 cenários, 13 PASS / 5 FAIL**; falhas nos casos 01, 04, 05, 06 e 07.
3. Após correção, `run-offline-tests.sh --binding` → **18/18 PASS** (11 WA-10 + 7 WA-11).
4. `run-offline-tests.sh --unit` (WA-09, sem alteração) → **11/11 PASS**.
5. Execução combinada local `node --experimental-strip-types --test --test-concurrency=1 integrations/whatsapp-meta/{attempt-binding,status-evidence}.test.ts` → **29/29 PASS**.
6. `tsc --strict --noEmit --skipLibCheck --target ES2022 --module NodeNext --moduleResolution NodeNext integrations/whatsapp-meta/attempt-binding.ts` → **PASS**. O typecheck integral de todos os testes não foi executado.
7. Executor `run-offline-tests.sh` reproduzido com SHA `65657cc248d1e99277dd86d115a6a9fac9d651d7`: `bash -n` → **PASS**; `--all` com checkout parcial → **exit 66**, corretamente recusando a ausência de 27 suítes. **Não é aprovação da regressão completa.**

Blobs verificados entre os arquivos locais testados e GitHub após atualização:
- `attempt-binding.ts`: `ea6a4ad61ebed6a08824d4c18410434ff07c2563`
- `attempt-binding.test.ts`: `e5ae026a1de80891db614fb83afbda6b70f821c6`
- `status-evidence.ts` (inalterado): `50095d75216f13686782476e8f6143d64933f42d`
- `status-evidence.test.ts` (inalterado): `bde56f1245b0ee635bc2874950599fc1bd941dd4`

## Pendências e próxima execução

- `--focus` e `--all` **não executados** sobre checkout integral. Em especial, **REC-36..39 e REC-01..39 continuam sem reexecução integrada comprovada nesta retomada**; não inferir compatibilidade de compilação/regressão para o conciliador completo a partir do teste do ledger.
- PostgreSQL local WA-06D (20 cenários) e S0-040 (5 cenários) não foram executados nesta retomada.
- S0 deve definir e testar esquema/índices transacionais, escopo confiável, `COMMIT_UNKNOWN`, idempotência e trilha de ocorrências antes de uso operacional. PR #1, PR #5 e os oito estados comerciais não foram alterados.
- Próximo gate: checkout integral → `--focus` / `--all`; posteriormente PostgreSQL 17 descartável, com aprovação do contrato de persistência. APIs reais permanecem etapa final dependente de autorização específica.

**Situação: incremento estrutural entregue e testado isoladamente; regressão integrada e homologação real NÃO atestadas.**
