# FV-S0-UQ-01 — Fronteira candidata de leituras S0 → Frontend

**Data:** 20/10/2026. **Natureza:** proposta testada localmente, NÃO contrato API/RLS aprovado, NÃO integração, NÃO homologação S0. **Escopo de edição:** somente `frontend/`, branch `feat/frontend-plataforma-visual`. A prioridade expressa do responsável permanece a **funcionalidade**, não o refinamento cosmético.

## Fontes e precedência

1. **Normativo 40 (17/10, [P]):** UQ01–UQ09, envelope com `schema_version`, `request_id`, `source_of_truth_version/as_of`, `returned_projection`, `records[]`, `next_cursor`, `leitura_minimizada`, `outcome/reason_code`; backend/gateway é responsável por autenticação, contexto e autorização.
2. **Normativos 26 e 13A ([D]/[P]):** comandos C01–C24 e eventos; oito status comerciais; entrega/aceite não equivalem a envio comprovado, venda/recusa não derivam de silêncio, banco e WhatsApp têm fontes de verdade externas. UQ não substitui comando.
3. **Decisão 41 de 17/10 ([D]):** gestor supervisiona conversas D2 de lojas concedidas, sem liberação geral de D3/D4; gestor designado como operador atua apenas no próprio caso. MCP possui apenas duas famílias iniciais de escrita autorizadas, com dupla confirmação e auditoria.
4. **Orientação DIRETA mais recente de 19/10, registrada em `frontend/docs/21_FV_G2_01_GESTAO_POR_OPERADORES_E_PAUSA_GLOBAL_2026_10_19.md` ([D]):** supervisão organizada por **equipes de operadores**; a pausa de entrada de leads é por operador, em todas as lojas concedidas, e gestor não concede lojas. O próprio registro marca a política exata de leitura D2 por interseção equipe+loja como **pendente S0/S1** e aponta a divergência com a redação de 17/10. **Não interpretar a decisão mais antiga de D2 por loja como permissão atual automática de ler outras equipes.** Não substituir a divergência por um filtro JavaScript; decidir e aplicar no backend.

## Famílias conceituais — leitura, não comandos

| Família [P] | Uso no frontend | Limite principal |
|---|---|---|
| UQ01 | O1: casos do operador | Só atribuições ativas autorizadas; resumo sem diálogo ou ficha |
| UQ02 | O2: conversa humana | Fonte S0; D2 da equipe/loja conforme política S0 pendente; escrita só pelo designado |
| UQ03 | O3: ficha/versões | D3 somente sob alçada; não inventar catálogo final de documentos |
| UQ04 | O4: linha do tempo bancária | Resumo gerencial sem prova D4 bruta; retorno/remessa dependem de evidência |
| UQ05 | O5: continuidade pós-marco | Novo caso/ciclo humano; não alterar retrospectivamente venda ou remessa |
| UQ06 | G1/G2: fila e atribuições | Equipe e lojas concedidas; gestor não cria concessão nem altera acesso local |
| UQ07 | G4: lotes | A proposta de leitura por loja deve ser reconciliada com equipe/elegibilidade S1-002 |
| UQ08 | G3: indicadores | Agregados autorizados da equipe e loja; sem SLA inventado ou identificação cruzada |
| UQ09 | O2/G3: estado técnico de envio | Aceite da API, entrega, leitura e envio efetivo não são sinônimos |

## Módulo candidato versionado

- **`frontend/visual/s0-read-contract.mjs`** é uma função pura independente de UI. Não chama rede, API, Meta, Banco, Supabase, n8n ou storage.
- `stageProposedS0ReadEnvelope(response, expected)` compara `query_id`, `query_version`, `request_id`, `correlation_id`, `actor_id`, `scope_ref` e `returned_projection` com o contexto esperado, exige `schema_version='s0-ui-read-proposal/0.1'`, origem, instante, `records[]`, sinal explícito `leitura_minimizada` e resultado proposto `APPLIED`.
- **Toda resposta negada, parcial, vencida, fora de escopo, sem versão ou malformada devolve somente** `UNTRUSTED_READ_PROJECTION`, lista vazia e cursor nulo — não reflete identificadores ou registros da resposta. A resposta íntegra é copiada antes de passar para a camada seguinte.
- `scope_ref`, `leitura_minimizada` e outros campos fornecidos como metadados **NÃO autenticam** o retorno. A checagem de eco protege apenas contra trocas acidentais de resposta/contexto. **S0 deve conceder escopo por sessão individual verificada, carregar dados já minimizados e restringir queries via políticas de servidor**; testar/RLS antes de integrar dados reais.
- Nomes de campos adicionados aqui para ensaio (`scope_ref`, `query_id` e forma de `outcome.status='APPLIED'`) são **candidatos de interface**, não formatos normativos aprovados. Não inventar endpoint, mecanismo de login, tabela de dados ou campo cadastral obrigatório para satisfazer o mock.
- **Não integrado ao `app.mjs`**: a interface atual continua usando exclusivamente as fixtures existentes. Introduzir transporte somente após contrato e autorização de S0.

## Evidências técnicas executadas

- Cópia integral do frontend reconstruída anteriormente a partir do ZIP autenticado por Git blobs do commit `50cc951e52c5ac5ca125e93416b2cad45f416ee9`, mais sete alterações do frontend conferidas por hash até `0a7d462b9e6096d411b5b42d3807ea358a3ff104`.
- Novos arquivos `s0-read-contract.mjs` e `tests/s0-read-contract.test.mjs` confrontados byte a byte por hash Git entre ambiente Node e branch.
- `node --test --test-reporter=tap tests/*.test.mjs`: **200/200 PASS, 0 FAIL, 0 SKIP**. Desses, **7 testes novos** exercitam as nove famílias e as falhas por escopo, ator, correlação, versão, projeção, formato, cursor, retorno negado e dados copiados.
- **Mutação negativa** retirando artificialmente o vínculo por `scope_ref`: **1/7 falhou como esperado**; fonte foi restaurada antes da execução normal.
- `CHROMIUM_EXECUTABLE=/usr/bin/chromium python tests/browser.smoke.py`: **PASS** em 1440×900, 900×780, 390×844, 320×640, casos pós-marco, templates, gestão e contas suspensas. Isso é **regressão** da UI antiga, não teste de integração S0.

## Pendências de deliberação entre frentes

O responsável já definiu gestão por operadores, mas o S0/S1 deve estabelecer de forma testável a interseção **gestor ↔ equipe ↔ operador ↔ loja ↔ caso**, inclusive D2, atribuição a si, revogação, troca de equipe e lote. Necessário fixar também versões de envelope, campos e projeções D0–D7, fontes de prova, erros, paginação/cursor opaco vinculado à identidade e política de cache/revogação; todos sob autorização e LGPD/Meta/Banco apropriados.

**Veredito:** fronteira candidata funcionalmente testada **apenas com dados sintéticos**; nenhuma função operacional liberada. **FV-UI-013 ainda não homologada no runner Git**, 19F permanece em **69/100**. Nenhuma alteração em Supabase, backend, Meta, produção, merge ou deploy.
