# Integração interfrentes E04 — F03 JS e S0 física

Data 2026-10-25; branch feat/oai-s0-f03-history-port-20261023, PR #1 Draft. Apenas laboratório E04, sem Supabase hospedado, Meta, OpenAI API, dados reais, merge ou deploy.

Foi criado o módulo backend/s0_f03_crossfront_contract_local.py. Ele não aceita autorização dada pelo JavaScript; aceita apenas status S0_RECHECK_ONLY, fieldCodes ordenados e snapshotRef em SHA-256. A S0 confere independentemente HMAC autenticado no contexto de laboratório, reserva CAS persistida, versão de ficha/catálogo/caso/atribuição/identidade, unicidade de candidatos de identidade, campos permitidos, hash dos valores e histórico de origem físico.

O retorno positivo é apenas REVIEW_ONLY e não grava nenhum campo. A aplicação sintética por gestor é uma porta diferente da S0, protegida por identidade/sessão/S1 e aprovação humana simulada.

O GitHub Actions da branch S0 faz checkout adicional e FIXO do commit S2 ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c para pasta temporária .s2-e04-source, executa as suítes Node oficiais do E04, então executa PG17. O script Python invoca o JS realmente vindo da S2 para criar o retorno de F03 e o inspeciona contra os recibos físicos S0 em 8 cenários. A autenticidade da sessão na interface histórica desta prova é um dublê S0 isolado de teste; nenhuma confiança produtiva é derivada de flags JS como authenticated, verified, historyComplete.

Os novos testes também protegem contra um JS que alegue escrita autorizada, campo estrangeiro, versão antiga, hash de snapshot falso, histórico HMAC modificado, identidade duplicada e intrusão de campos não previstos.

Os testes físicos de interfrentes só são executados quando PRUMO_S2_F03_GATE_PATH é fornecido pelo checkout fixado; fora disso são skip explicitamente declarado. A workflow deve ser considerada prova de compatibilidade E04 entre contratos, NÃO validação geral F01/F02/Meta/S1 real ou da aplicação de dados de cliente.

Resultado numérico, SHA de código e link de CI devem ser acrescentados após a confirmação de sucesso nos logs.