# Auditoria corretiva M16 — snapshot de templates e variáveis

**Data:** 01/11/2026. **Frente:** WhatsApp/Meta. **Escopo:** `wa16-template-snapshot-offline.ts`, testes, núcleo WA-17B e interfaces documentais WA-17/M13/MCP. A M16 principal permanece **aberta**: nenhuma fonte S0/Meta real foi autenticada.

## Parecer e correções

**AUD-M16-01 — seleção não vinculada diretamente ao hash do snapshot.** A M16 incluía `selection_ref` na estrutura de saída e o comparava no recheck, mas não o incluía na composição de `snapshot_sha256`. Dois snapshots de seleções diferentes poderiam carregar o mesmo hash técnico, apesar de resultados distintos na comparação de campos. **Correção:** incluir `selection_ref` no domínio do hash final, mantendo concessionária/WABA/template/versão, componentes, variáveis e mídia. A saída inteira continua sem valor de autorização e o hash não é assinatura.

**AUD-M16-02 — deriva invisível do registro de fontes ainda não usadas.** `binding_sha256` considerava os slots e fontes efetivamente escolhidas, mas não registrava toda a lista sintética de fontes permitidas. Adicionar ou retirar uma fonte não referenciada conservava o mesmo hash, embora o contexto autorizado alegado tivesse mudado. **Correção:** incluir **toda a lista ordenada** `source_registry` no hash dos bindings. Alterar composição recusa o recheck; somente a ordem da lista não muda o resultado. Lista sintética **não é** grant S0.

**AUD-M16-03 — limite de recursos em texto não validado.** A cópia profunda limitava nós e profundidade, mas valores textuais arbitrários, sobretudo da lista de fontes, poderiam ser muito extensos antes do hash. **Correção:** rejeitar strings de entrada com mais de 8.192 unidades UTF-16, antes de clonagem/hashing. O motor WA-17B continua impondo limites mais estritos de texto, botão e URL.

**AUD-M16-04 — domínio de digest mudou sem mudança da versão de saída.** O formato dos campos permanece, mas a interpretação de `snapshot_sha256`/`binding_sha256` mudou. Para impedir confusão com snapshots anteriores, a saída passa de `wa16-frozen-snapshot.lab.v0.1` para **`wa16-frozen-snapshot.lab.v0.2`**, enquanto o contrato **de entrada** `wa16-template-freeze.lab.v0.1` permanece. O recheck de candidatos antigos v0.1 nega `INVALID_CANDIDATE`. Alteração **somente de protocolo LAB**, sem ratificação/produção.

**AUD-M16-05 — proteção preexistente de mídia revisada, sem duplicar implementação.** O código já vinculava a evidência sintética de mídia a `concessionaria_id`, `waba_ref`, `asset_ref`, tipo, MIME, checksum, revisão, idade e validade, com testes M16-43/44 para lojas/WABAs diferentes. Nenhuma brecha nova comprovada nesse vínculo; não reimplementado.

## Evidências e regressões

- Base anterior: **44 casos M16** e **1.617/1.617 testes Meta offline**, CI [41295933084](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41295933084), SHA `1de780df5b52ad862e54700baf3f2c0ae271b5fd`.
- Inclusos **12 novos testes AUD-M16-45..56**, envolvendo alteração da seleção, adição/remoção de fonte não usada, reordenação sem mudança semântica, lista duplicada, strings extensas, fonte selecionada inválida, hashes adulterados e incompatibilidade deliberada de snapshot v0.1. **Expectativa de 56 testes M16 e 1.629 testes Meta offline**, condicionada a evidência do CI do SHA funcional exato; não considerar intermediários como homologação.
- **PG17 18 verificações** históricas, quando presentes, tratam do ingresso Meta/S0, não validam mídia real, aprovação de template, MCP ou snapshot M16 em serviço.

## Pendências que NÃO foram resolvidas

- [ ] S0/Infra: fonte de verdade de `concessionaria_id`, WABA, grants, registro autorizado de fontes de variáveis, revisão transacional/CAS, catalogação e readback persistentes; [Issue #8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8). Os laboratórios M09-07/M09-08 S0 são independentes, sem aceite Meta operacional.
- [ ] Meta real: prova autenticada de criação/aprovação por WABA, componentes suportados, versão e estado; upload/handle de mídia por gateway autorizado. O verificador Graph da M13 não suporta todos os formatos WA-17B.
- [ ] MCP: serviço próprio, principal humano/delegação, confirmação, autorização e trilha de mudanças. O contrato WA-17B não é servidor implantado e não pode administrar Diretores.
- [ ] PRE_DISPATCH: S0 revalida versão, aprovação, consentimento, opt-out e conteúdo na transação que reserva tentativa; [Issue #10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10). Dois snapshots sintéticos não evitam corrida, ABA ou alteração posterior.

**Estado:** M16-A/B/C feitos e auditados apenas em laboratório; **M16-D e M16 principal [ ]**. Toda resposta mantém `send_authorized=false`, `production_authorized=false`, `meta_approval_verified=false`, `media_verified=false` e `mcp_execution_authorized=false`. Não houve Graph, envio, MCP operacional, alteração S0, merge ou deploy.
