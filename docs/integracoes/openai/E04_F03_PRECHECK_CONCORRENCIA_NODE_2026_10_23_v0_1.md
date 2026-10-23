# E04 — F03: pré-validação de concorrência, proveniência e reprocessamento | v0.1

**Data:** 23/10/2026. **Situação:** implementação offline com dados exclusivamente fictícios, dentro da autorização expressa de E04. **Não** é aplicação real da ficha, permissão S0, processamento por modelo OpenAI, API, operação bancária ou contrato físico homologado.

## Entregas

- [`f03-commit-gate.mjs`](./e04_offline_lab/f03-commit-gate.mjs): função pura `evaluateF03CommitCandidate`; **não grava nada**. Hash Git do código publicado e testado: `fb9727e21c8a013602c17d80d6e3b8ec0aeef9dc`.
- [`tests/f03-commit-gate.test.mjs`](./e04_offline_lab/tests/f03-commit-gate.test.mjs): **42 casos com `node:test`**. Hash Git publicado e testado: `8988ae4f981e05965b78d11efc4b1d137dd0e562`.
- Validação interna do Node.js 22.16.0: **42/42 PASS** para a nova suíte; executada **juntamente com 53 testes F02 disponíveis localmente: 95/95 PASS, 0 FAIL**. Confirmados por `node --test /mnt/data/e04_dev/tests/*.test.mjs`. O arquivo de F02 nesse diretório já estava disponível; **o checkout completo do PR não está presente no ambiente local**. Consequentemente, **não** afirmar execução conjunta pelo Node dos 254 casos publicados no laboratório (50+33+33+53+43+42), nem que os 70 oráculos originais SYN foram executados.
- A rodada anterior verificou **212/212 em V8 isolado com imports `node:test` adaptados**, fato separado da execução atual pelo Node.

## Pré-condições e oráculos do candidato

| Condição | Negativa/saída segura |
|---|---|
| Autorização S0 fictícia revogada, tenant inválido, identidade ou evento de fechamento divergente | `DENIED` antes de expor versões ou fonte |
| Manifesto multi-casos não atestado pela S0, encerramento não confirmado ou snapshot sem referência | `HISTORY_REVIEW_REQUIRED` |
| Versões distintas de **caso, ciclo, ficha, catálogo, atribuição e identidade** não coincidem com as atuais | `STALE` — não sobrescrever ficha recente |
| Mesmo pedido já aplicado com recibo válido da S0 fictícia | `ALREADY_HANDLED`, sem duplicar efeitos |
| Pedido repetido com conteúdo/snapshot/fechamento diferente ou recibo incerto | `REVIEW_REQUIRED` |
| Fonte de outro cliente/loja, depois do cutoff, indisponível ou sem verificação/extratos explícitos | `SOURCE_INVALID` |
| Campo essencial ausente ou conflito entre fontes documentadas | `HUMAN_REVIEW_REQUIRED`; não liberar edição manual de ficha ao Consultor |
| Opcionais ausentes, essenciais presentes e valores explicitamente comprovados na fixture | `S0_RECHECK_ONLY`, **ainda sem aplicar cadastro** |
| Sugestão `perdido` por desistência **explicitamente atestada na fixture** | `COMMERCIAL_ADVISORY_REVIEW`, sem marcar `perdido` |
| Sugestão `vendido`, campo fora do catálogo, valor inventado | Recusa; `vendido` depende de decisão humana e prova bancária |

**Importante sobre o relógio do histórico:** nova mensagem **posterior ao corte de uma conclusão** não modifica retroativamente aquele corte. Ela não torna a evidência histórica falsa por si só. Atualizações efetivas de versão, direitos, atribuição ou catálogo podem impedir aplicar uma proposta antiga e requerem revalidação.

## Fronteira de confiança — não promover stub diretamente à S0

`s0ClosureVerified`, `historyComplete`, `s0Verified`, `claims.explicit`, `prior.s0Verified` e as versões são **afirmações de fixture simulada**, não verificações criptográficas, assinaturas, autorizações de banco de dados ou garantia de verdade dos dados. A aplicação real exigirá que a S0 resolva esses fatos com recibo autenticado, catálogo oficial, permissões, transação concorrente, prova de evidência multimodal e política de retenção.

O recibo local por caso já documentado no PR #12 **não atesta por si só** o manifesto completo de múltiplos casos da mesma pessoa/loja, nem a autenticidade material das extrações. A função não gera mutação SQL, áudio, mensagem Meta, agendamento F02, remessa ao Banco ou alteração de auditoria; sua saída `S0_RECHECK_ONLY` **não** é `PASS` de protocolo S0.

## Pendências

**CFI-01 (issue #4):** obtenção e versionamento do manifesto multi-casos, identidade de múltiplos telefones, autorização de mídia, catálogo de campos, precedência de versões e idempotência **físicas**.

**CF-OP-02/WA-22 (issues #6/#15):** classificação dos recibos Meta, 131049, limites de frequência e relógio C09; seguem independentes deste avanço.

**E02:** os 70 oráculos SYN continuam sem execução original homologada; os 42 testes F03 não podem ser contabilizados como 42/70 SYN aprovados. **E05:** não autorizada; nenhuma credencial, cobrança, chamada paga, serviço real, deploy, merge ou mudança em outras frentes.
