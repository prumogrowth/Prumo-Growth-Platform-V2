# OFF-10 — handoff de publicação isolada e gate da frente OpenAI (31/10/2026)

**Estado: BLOQUEADO POR TRANSPORTE DOS ARQUIVOS; NÃO É PUBLICAÇÃO DO PATCH OU ACEITE.**

## Origem auditada

- Conta de trabalho: `herdeirosdoalento`, permissões GitHub `write` verificadas.
- Base oficial OFF-01: commit `394512327cd3756dfbe61ff970a6279c354b6565`, árvore `87a3ce85b2ead682038d4bee104ca47dd006c971`.
- Pacote ZIP local `OAI_OFF_02_A_08_PATCH_AUDITADO_2026_10_31.zip`, SHA-256 `9116f713198d9c8b3061874d9c6c2dcb2a4045c384b02feaad4ca334b39b0feb`, **28 arquivos** (27 listados com digest SHA-256 + manifesto). Todos os 27 hashes conferiram no ambiente local.
- Meta do gate: **678 = 342 herdados + 336 novos**. O gate exige **um commit diretamente filho da OFF-01, somente com os 28 arquivos**; não adicionar um workflow ou este registro no mesmo commit candidato.
- Teste herdado real: [CI 41261591040](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41261591040), **342 PASS** no commit OFF-01 isolado, sem patch.
- Testes locais reproduzidos neste ciclo: **172 PASS / 0 FAIL F01+F02**. F03 101 PASS no harness isolado na execução anterior; OFF-02 63 reportados no teste separado anterior. **Não confundir resultados de ambientes distintos com 678 PASS.**
- Verificações preventivas do publicador local: pacote íntegro PASS; ZIP adulterado, manifesto ausente e arquivo extra BLOQUEADOS.

## Por que ainda falta a publicação

O terminal com o ZIP local não tem saída de rede/DNS para GitHub. O conector autenticado pode criar refs, árvores, blobs e arquivos no GitHub, **mas não recebe diretamente o conteúdo de caminhos `/mnt/data`**. A branch de preparação não carrega o ZIP. Um commit com arquivos inventados, omitidos ou substituídos seria inválido; por isso não foi criado.

## Próximo passo técnico

1. Disponibilizar os 28 arquivos de bytes idênticos à origem auditada ao canal de escrita GitHub.
2. Criar branch candidata **distinta desta staging** a partir do commit OFF-01 e **um único commit** contendo apenas esses 28 arquivos.
3. Executar `node docs/integracoes/openai/e04_offline_lab/patch-preflight.mjs` na árvore completa, exigir exatamente 678 testes PASS, zero fail/skip, manifesto íntegro e pai/árvore fixados; divulgar o run/commit e revisar o diff antes de qualquer aceite.
4. Sem merge, produção, Graph/Meta, chamadas a modelos, operações bancárias, decisões S0 ou homologação por inferência.

Demandas S0/Meta permanecem nas Issues #5, #6, #7, #9, #11, #12; futura síntese de F01/F02/F03 na #13.
