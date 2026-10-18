# WA-06C — verificação independente do formato Meta → S0 em Python e TypeScript

**Data:** 18/10/2026. **Estado:** [P/V local]. **Escopo:** conferir apenas a *compatibilidade da serialização* candidata WA-06B. Não confundir com validação de HMAC real, identidade de serviço, autorização S0, consumo transacional de nonce, persistência protegida ou ACK Meta.

## 1. Contexto e objetivo

A WA-06B criou `canonicalizeInternalProofV1` em TypeScript, com ordem estável e bytes prefixados pelo comprimento. O primeiro vetor de hash fora registrado, mas ainda não existia uma segunda implementação em outra linguagem capaz de verificar autonomamente a especificação.

**Incremento WA-06C concluído:** foram versionados dois arquivos de teste de referência no PR #2, **sem adicionar um novo simulador de ingresso em memória**:

- `integrations/whatsapp-meta/wa06c_reference.py`: algoritmo escrito independentemente em Python padrão, com `struct.pack('>I', comprimento)`, prefixo de domínio e ordem de campos explícita; os testes de unidade auditam cinco cenários fixos. É uma **referência de consistência** para fixtures, não parser/verificador de entrada externa.
- `integrations/whatsapp-meta/wa06c-crossruntime.test.ts`: importa o encoder WA-06B já existente (blob `1dc5fddd1893d69151043a1a5ea70fcc03a0c34f`) e exige exatamente os tamanhos/hashes da referência Python. Inclui três negativas adicionais.

## 2. Vetores de referência verificados

| Cenário | Bytes | SHA-256 dos bytes serializados |
| --- | ---: | --- |
| BASE: callback `delivered` | 585 | `c94993710cfc4a90d41314c89026385e7cbd446753b2fa7d0ec0cc7f65083209` |
| NONCE_ROTATED: outra referência `nonce_ref` | 585 | `219aec893fc30e0f96870d1170643033c8b169515c853085dc58baba6ef3e549` |
| CALLBACK_REPEAT: duas ocorrências legítimas com o mesmo `wamid` | 736 | `577cad6732765d18b4ee62af0feef71d2c62c86023a8ecd406f8ca3e2977f5e5` |
| TWO_CHANNELS: dois canais da mesma App | 736 | `444411a4acf020fb799fd3aeb78b85f77ec0b482f0d10fdf1d91508e1b9cb267` |
| READ_STATUS: mesmo contexto, `read` em vez de `delivered` | 580 | `9dc572689a0ec12fdb45b6b21f8ddddad44aa1f10d1ef6acd32a911f1889eb93` |

Esses SHA-256 são **checagens determinísticas de consistência** e não provam a origem de uma mensagem. O `statuses[].id` continua sendo referência de mensagem, não identificador universal de callback. O consumo único do nonce permanece um requisito de banco S0 **a implementar**.

## 3. Evidência efetivamente executada

Os arquivos **idênticos aos publicados** foram testados localmente:

- **Python 3.13.5**, execução `python wa06c_reference.py`: **2/2 métodos unittest PASS**, um deles com os **cinco subtestes de vetores** e o outro verificando que os quatro cenários distintos produzem resultados diferentes do baseline.
- **Node.js 22.16.0**, execução `node --experimental-strip-types --test wa06c-crossruntime.test.ts`: **8/8 testes PASS** — cinco comparações com os valores Python e três verificações de ordem de campos/alteração de status e canal/rejeição de campos inesperados e flag ACK.
- **TypeScript 5.8.3**, `tsc --noEmit --strict` nos arquivos `internal-proof-wire-v1.ts` e `wa06c-crossruntime.test.ts`: **PASS**, usando `@types/node` local e uma **declaração temporária de tipo** para a interface `S0HandoffCandidate` importada da WA-05C. Isso **não** constitui typecheck completo nem compilação de toda a branch.
- Hash de blob Git idêntico ao arquivo local executado: `wa06c_reference.py` = `03c14661d98bb701167cd4524aaa0eca29acf11a`; `wa06c-crossruntime.test.ts` = `b30b1b72fdb0cd7d484580d0f464d9e3a9a75064`. O arquivo WA-06B exercitado permaneceu idêntico ao Git, SHA `1dc5fddd1893d69151043a1a5ea70fcc03a0c34f`.

**Delimitação de contagens:** a WA-06C acrescentou **8 testes Node e 2 métodos Python (cinco subtestes de vetores)**. Não reexecutamos a suíte completa histórica WA-05D-AUD1 de 358 casos nem a suíte WA-06B original de 15 neste incremento; não anunciar totais somados como uma suíte única. Não houve GitHub Actions remoto, PostgreSQL, GoTrue/PostgREST, Supabase hospedado, HMAC Meta real ou envio.

## 4. Revisão cruzada e efeito das outras frentes

- **S0 PR #1:** permanece necessária a revisão de fonte confiável de identidade do serviço fora do corpo; owner e GRANT/RLS mínimos; validação temporal, ACL e nonce duráveis; vínculo de App/WABA/emissor/loja/canal revalidado na mesma transação que persiste bytes protegidos, batch, `occurrence_ref`, tarefas e recibo. Uma igualdade de SHA-256 entre linguagens **não** é prova de commit. A S0-037F é laboratório de outro fluxo, não autenticador Meta.
- **S1 PR #5:** controle da equipe humana Prumo não substitui autorização do serviço técnico. Desligar profissional não revoga por inferência a titularidade App/WABA da concessionária, preservando D-ORG-01 e DEC-WA-05.
- **CF-OP-02 PR #7:** diretriz transversal validada para janela Meta 24h, templates de retomada e retorno após handoff, **fora desta etapa**. Preservar especialmente que template não reabre janela livre sem novo inbound, C09 exige prova de envio final e silêncio pós-banco nunca marca mudança comercial. Não alterar C03/C06/C08/C09 ou automações de envio nesta WA-06C.

## 5. Próxima etapa técnica recomendada [R]

**WA-06D, com a S0:** desenvolver e auditar um **teste transacional em PostgreSQL descartável** para consumo de nonce, bloqueio de revogação concorrente, criação atômica de lote/ocorrências/tarefas e emissão/consulta de recibo após commit, usando fontes e papéis de *laboratório* claramente identificados. A implementação operacional dependerá de decisão expressa sobre identidade de workload, segredos, ambiente e retenção (DEC-WA-04/06) e de revisão cruzada formal da S0. Evitar multiplicar simuladores JavaScript de `Map`.

**Gates sem alteração:** a POC `whatsapp-webhook-sandbox` no projeto `projeto-supabase-omitido` permanece intacta; não executar merge, deploy, migrations hospedadas, Graph API ou números reais sem autorização. PRs #1/#2/#5/#7 continuam conforme seus respectivos estados de Draft; manter plano Free e solicitar aprovação antes de custos. `ack_allowed=false` permanece o único resultado permitido no código candidato presente.

## Adendo de auditoria WA-06-AUD1 (18/10/2026)

Os **cinco hashes de referência Python/TypeScript permanecem válidos para entradas coerentes** depois do reparo. A auditoria [WA-06-AUD1](wa06-aud1-auditoria-contrato-atualizado-wa07-v0_1.md) introduziu recusa de lote com `concessionaria_id` misturados sob a mesma App e de contradições no mapeamento emissor/canal; código atual `internal-proof-wire-v1.ts` blob `f4ac80c5e8fe09f4d4ef0ae7673cd8e8f815feeb`, enquanto os números e SHA de origem nesta página continuam identificando o **snapshot anterior**. Testes AUD-01..07: **7/7 PASS local**, incluindo os cinco vetores; não equivale à reexecução da antiga suíte WA-06C 8/8. Contrato WA-07 ainda depende da S0, segurança, `received_at` e prova `sent` [R/V]; sem banco real ou autorização operacional.
