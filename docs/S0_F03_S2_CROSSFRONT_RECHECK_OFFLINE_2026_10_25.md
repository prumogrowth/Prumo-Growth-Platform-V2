# Integração interfrentes E04 — F03 JS e S0 física

Data 2026-10-25; branch feat/oai-s0-f03-history-port-20261023, PR #1 Draft. Apenas laboratório E04, sem Supabase hospedado, Meta, OpenAI API, dados reais, merge ou deploy.

Foi criado o módulo backend/s0_f03_crossfront_contract_local.py. Ele não aceita autorização dada pelo JavaScript; aceita apenas status S0_RECHECK_ONLY, fieldCodes ordenados e snapshotRef em SHA-256. A S0 confere independentemente HMAC autenticado no contexto de laboratório, reserva CAS persistida, versão de ficha/catálogo/caso/atribuição/identidade, unicidade de candidatos de identidade, campos permitidos, hash dos valores e histórico de origem físico.

O retorno positivo é apenas REVIEW_ONLY e não grava nenhum campo. A aplicação sintética por gestor é uma porta diferente da S0, protegida por identidade/sessão/S1 e aprovação humana simulada.

O GitHub Actions da branch S0 faz checkout adicional e FIXO do commit S2 ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c para pasta temporária .s2-e04-source, executa as suítes Node oficiais do E04, então executa PG17. O script Python invoca o JS realmente vindo da S2 para criar o retorno de F03 e o inspeciona contra os recibos físicos S0 em 8 cenários. A autenticidade da sessão na interface histórica desta prova é um dublê S0 isolado de teste; nenhuma confiança produtiva é derivada de flags JS como authenticated, verified, historyComplete.

Os novos testes também protegem contra um JS que alegue escrita autorizada, campo estrangeiro, versão antiga, hash de snapshot falso, histórico HMAC modificado, identidade duplicada e intrusão de campos não previstos.

Os testes físicos de interfrentes só são executados quando PRUMO_S2_F03_GATE_PATH é fornecido pelo checkout fixado; fora disso são skip explicitamente declarado. A workflow deve ser considerada prova de compatibilidade E04 entre contratos, NÃO validação geral F01/F02/Meta/S1 real ou da aplicação de dados de cliente.

Resultado numérico, SHA de código e link de CI devem ser acrescentados após a confirmação de sucesso nos logs.

## Execução certificada

**GitHub Actions [#40189226546](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40189226546) — SUCCESS** sobre commit de código `eb37fe621026866a14c178f0d85a9b5c4481033c`, PostgreSQL **17.11** descartável, com checkout independente S2 fixado em `ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c`.

- Testes nativos `node --test` da S2, executados **de fato no runner**: **269/269 PASS, 0 FAIL, 0 SKIP**. Isto supera a lacuna anterior de execução conjunta Node, mas NÃO equivale aos 70 oráculos SYN documentais de E02.
- Testes físicos PG17 e unitários: **84/84 S0**, **316/316 F03**, somados **400/400 PASS** nesta bateria Python. A F03 contém **203 testes físicos PG17**; os 8 novos cenários físicos 196–203 de interfrentes passaram.
- 9 testes unitários novos do formato de envelope S2↔S0 também passaram. **Os totais Node e Python são conjuntos distintos:** 269 Node + 400 Python = 669 verificações de laboratório executadas no mesmo job, não um único teste E2E completo de produto.
- O teste físico de ponte utiliza um dublê S0 de *autorização histórica* (não autenticação real), mas a verificação de conteúdo/HMAC, reserva, versões, identidade, catálogo e banco é real no PG17 descartável. Sem direitos F03 de escrita ou leitura real.
- Não houve merge, deploy, instalação em Supabase hospedado, chamada Meta/OpenAI API ou manuseio de dados de clientes.

**Próximo gate:** traduzir o envelope das propostas (fontes e valores) para evidência rastreável tipada pela S0 sem aceitar alegações de autenticidade da IA; confrontar as políticas E02/SYN e o fluxo F01→humano→F03→F02 com as assinaturas S0/S1/Meta em fixtures mais completas. Supabase remoto continua adiado conforme a decisão do responsável.
