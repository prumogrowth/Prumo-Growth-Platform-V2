# OFF-06 — Gate de consolidação e relatório de reprodução (candidato offline)

**31/10/2026 — situação: PARCIAL COM BLOQUEIO DE REGRESSÃO.** Este documento não significa que OFF-02/03/04/05 foram incorporadas à árvore oficial, homologadas ou testadas integralmente.

## Base e delta
- Base declarada e verificada previamente no GitHub: OFF-01 `394512327cd3756dfbe61ff970a6279c354b6565`, árvore `87a3ce85b2ead682038d4bee104ca47dd006c971`.
- Arquivo cumulativo local anterior à auditoria: `OAI_OFF_02_03_04_05_CANDIDATO_CUMULATIVO_2026_10_31.zip`, SHA-256 `0787a97776ba25d7d41b76ee72b1e4116a16a8f9931be2e8e7250bf5fa9888db`.
- Os 25 arquivos anteriores são adições novas sob `docs/integracoes/openai/`; o presente lote acrescenta somente este relatório, `e04_offline_lab/patch-preflight.mjs` e `e04_offline_lab/patch-files.sha256.json`. Nenhum arquivo herdado é substituído.
- A transferência do checkout Git oficial para o terminal local não está disponível (DNS de `github.com` inacessível); os pacotes locais **não** incluem `core.mjs`, `journey.mjs`, `f03-commit-gate.mjs` etc. nem os testes OFF-01. Nunca substituir esses módulos por stubs para alegar PASS.

## Evidência reproduzida nesta execução
- Node.js `22.16.0` e Git `2.47.3` no ambiente local.
- `node --test tests/f01-sales-boundary.test.mjs tests/f02-plan-boundary.test.mjs`: **169/169 PASS**, zero falhas, zero skip. Evidência no arquivo local `oai_off06_recheck_f01f02.txt` distribuído separadamente da árvore candidata.
- `node --test tests/*.test.mjs` sobre o ZIP **isolado**: 169 PASS e **2 arquivos de suíte falharam por `ERR_MODULE_NOT_FOUND`** (`core.mjs` e `f03-commit-gate.mjs`). Não são duas falhas de assertiva: a ausência dos arquivos herdados impediu o carregamento das suítes OFF-02/OFF-03. **Não declarar 325 PASS nesta execução.**
- `patch-preflight.mjs`: 27 arquivos com SHA-256 conferidos no manifesto; sem checkout Git da base, retorna intencionalmente `OFF01_CHECKOUT_REQUIRED`, exit 2. Alterar um byte em `f02-plan-boundary.mjs` dispara `PATCH_BYTES_CHANGED`, exit 2 (teste adversarial confirmado).
- Não há execução GitHub Actions deste lote nem commit novo. As contagens OFF-02 61 PASS e OFF-03 95 PASS são relatadas pelos respectivos lotes anteriores; não foram repetidas cumulativamente nesta rodada.

## Verificador técnico incluído
`node docs/integracoes/openai/e04_offline_lab/patch-preflight.mjs` é uma porta **offline**, sem rede ou escrita Git. Ele:
1. confere hash de cada novo arquivo regular e rejeita substituição, symlink, caminho divergente e manifesto incompleto;
2. exige o pai imutável OFF-01 e sua árvore exata; aceita pré-commit apenas quando `HEAD` é OFF-01 e o delta inteiro está não rastreado; pós-commit, exige um commit filho único de OFF-01 com exatamente as novas adições;
3. bloqueia mudanças em qualquer arquivo herdado e trabalho local adicional;
4. executa `npm --prefix docs/integracoes/openai/e04_offline_lab test` com **todas** as suítes originais + novas, exigindo **667 testes PASS**, zero falhas e zero skip. É um número **esperado**, 342 herdados reportados + 61+95+69+100; ainda **não observado** em execução cumulativa.

Somente depois da execução real do gate e inspeção da árvore/CI é possível afirmar regressão cumulativa. Um resultado positivo seria certificação local delimitada, não autorização para produção.

## Instruções de implantação futura em branch isolada (não executadas)
1. Criar branch nova do commit exato OFF-01 `3945123`, sem alterar outras frentes.
2. Extrair o ZIP candidato na raiz desse checkout, somente como 28 adições novas (`docs/integracoes/openai/`).
3. Executar o verificador antes do commit; falha bloqueia a publicação. Confirmar manualmente que nenhuma escrita cruzada ou secreta foi introduzida.
4. Após PASS, gerar **um commit isolado** e executar o verificador novamente no estado commitado. Publicar apenas a branch, com SHA, tree, logs e revisão; sem merge/PR automático/deploy.
5. Testar separadamente a fonte histórica A38 em sua referência exata. Se indisponível, continuar `HISTORICAL_SOURCE_UNRECOVERED`, não substituir por um snapshot recente.

## Pendências de contrato, sem duplicação de Issues
- [#5](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/5): histórico multicases, identidade e cutoff F03; S0 respondeu `EM_ANALISE`, sem contrato ratificado.
- [#6](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/6): catálogo, prova semântica e aplicação F03; S0 `EM_ANALISE`.
- [#7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7): pedido F02, elegibilidade e continuidade; S0 `EM_ANALISE`, Meta confirmou separação.
- [#9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9): Meta publicou WA-39 v0.1 candidato no SHA `94338c3a36293f23dd88afe7773d5c1e622a1a8f`; OpenAI enviou parecer técnico de campos mínimos, correlação, idempotência e leitura S0 na própria Issue. Não foi aprovado operacionalmente.
- [#10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10): recheck S0 antes do envio Meta; distinto de F02.
- [#11](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/11): posse F01, handoff irreversível e recheck de publicação; aguardando S0.
- [#12](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/12): seleção comercial e vigência de conhecimento F01; aguardando S0.

**Conclusão:** o conteúdo novo OFF-04/05 foi reproduzido sem falhas; a publicação e a regressão de OFF-02/03 + herdados **permanecem bloqueadas**, não foram implicitamente aprovadas. Todas as decisões S0/Meta e custos/segredos/produção permanecem fora de escopo.


## Revisão de regressão independente — 31/10/2026 (OFF-06.1)

- Recuperados **seis módulos de execução S2 do commit fixado OFF-01** via GitHub, verificando que seus Git blob SHA-1 coincidem exatamente com os originais: `core`, `f03-commit-gate`, `journey`, `plan-lifecycle`, `template-frequency` e `transport-evidence`. Não há alteração destes módulos na distribuição de patches.
- Rodados **331 testes novos reais (Node 22.16.0)**: OFF-02 **63**, OFF-03 **99**, OFF-04 **69**, OFF-05 **100**. `331 PASS`, `0 FAIL`, `0 SKIP`. Testes novos não alegam integração física ou provam operação S0.
- **Correção de contagem:** os documentos históricos citavam 61/95 novos para OFF-02/03, mas os arquivos de teste entregues contêm e executam efetivamente **63/99**. A soma correta esperada, **se** a regressão herdada continuar com os 342 PASS historicamente relatados, é **673 = 342 + 331**, e não 667. O verificador passa a exigir 673.
- **Reproduzidos 5 cenários negativos** do `patch-preflight.mjs`: sem checkout OFF-01, arquivo alterado, symlink, manifesto inválido e commit Git incorreto: todos negados (exit 2). Os 27 bytes/hashes de arquivo do manifesto foram conferidos localmente antes de mutação.
- **Não executado:** testes herdados 342, porque a cópia de trabalho não contém os oito artefatos de testes/preflight/manifesto OFF-01 que ainda exigem checkout Git oficial; clone direto indisponível neste ambiente. Desta forma, **673 é critério alvo não alcançado**, e `PATCH_GATE_PASS`, CI GitHub, homologação, merge ou produção NÃO são declarados. A38 histórica permanece não recuperada.
- Próxima atividade independente: montar o checkout Git oficial em `394512327cd3756dfbe61ff970a6279c354b6565`, sobrepor somente as 28 adições autorizadas e executar `node docs/integracoes/openai/e04_offline_lab/patch-preflight.mjs`; revisar qualquer diferença de contagem/versão antes de commit. Nenhum arquivo de S0, Meta, Frontend ou S2 original deve ser alterado.

## Auditoria preventiva OFF-07 (31/10/2026) — atualização candidata, sem homologação

Esta seção **prevalece apenas quanto à contagem da suíte nova e ao gate** sobre números históricos citados anteriormente neste documento. Quatro testes de regressão adicionados: 1 F01, 2 F02 e 1 F03. A meta **condicional** do gate passa a **677 = 342 herdados historicamente relatados + 335 novos**. Os 342 herdados continuam **não reexecutados** neste ambiente; logo, 677 não é resultado observado.

Reparos locais, todos fail-closed e sem efeitos de negócio: resposta com `nowMs` anterior à emissão resulta em `REVIEW_REQUIRED/CLOCK` para F01/F02; continuidade F02 com `attemptIds=[]` é inválida; F03 com suporte apenas de fala da IA não é promovida a `PROPOSED` sem fonte humana/cliente terminal citada (retorna `REVIEW_REQUIRED/AUTHORSHIP`); `patch-preflight` confere também `expected_full_tests` no manifesto, paths canônicos e ausência de symlink nos diretórios ancestrais. **Não foi realizada ratificação S0/Meta, nem alteração de seus arquivos.**

Execução de auditoria atual: 272/272 testes de OFF-03/04/05 aprovados com o `core.mjs` original de S2 (SHA blob `f5be662cc7db925f99802cc251f432b90fb0aa15`), 0 falhas. Os 63 testes OFF-02 não foram repetidos nesta execução por falta de outros módulos herdados; os 331/331 do relatório OFF-06.1 são uma execução anterior do candidato antes destes reparos. A meta 677 depende de checkout completo e deve ser demonstrada, não inferida.


## Auditoria preventiva OFF-08 (31/10/2026) — citação obsoleta corrigida

**Novo defeito reproduzido:** se uma fonte mais recente corrigir uma afirmação anterior usando o mesmo valor, a F03 podia aceitar `sourceAliases` com as duas fontes, incluindo uma referência já corrigida, e retornar `PROPOSED`. A validação agora exige que **cada alias citado**, e não apenas algum alias do conjunto, corresponda a uma afirmação terminal não corrigida do mesmo campo/valor. Referência obsoleta retorna `SOURCE_INVALID/OBSOLETE_CITATION` sem aplicar ou inferir fatos. Teste `AUD-F03-101` reproduz o defeito antes do reparo e seu bloqueio após o reparo; a fonte atual isolada permanece elegível como proposta.

**Execução local isolada:** F01 101/101 e F02 71/71 PASS, via módulos novos reais. F03 101/101 PASS usando código F03 de produção candidata inalterado exceto pelo reparo e cópia byte-equivalente do parser estrito (sem as importações de S2 não utilizadas naquele caminho); esta execução **não constitui regressão oficial S2/OFF-01 nem teste com toda a árvore original**. Nenhuma chamada a provedor ou S0. A meta **condicional** de regressão passa a **678 = 342 herdados relatados + 336 novos (63+101+71+101)**. É um alvo não alcançado; a suíte OFF-02 e os 342 herdados ainda exigem o checkout Git oficial.
