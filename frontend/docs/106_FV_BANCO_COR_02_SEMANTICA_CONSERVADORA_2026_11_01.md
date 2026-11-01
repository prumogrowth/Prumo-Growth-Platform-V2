# FV-BANCO-COR-02 — Correção semântica conservadora da fila

**Data:** 01/11/2026. **Origem:** [FV-BANCO-AUD-01](./105_FV_BANCO_AUD_01_AUDITORIA_INDEPENDENTE_2026_11_01.md), [Issue #15](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/15). **Branch:** `fix/fv-banco-aud-02-fail-closed-20261101`, filha de `d50e259b9b96e6ca3094b3caefdaacd615e2f93c`.

## Ajustes executados somente sobre demonstração

- BAN-AUD-01: `bankProjection.phase === 'unavailable'` é **desconhecido**, não remessa ausente. Exigir `not_submitted` explícito no seletor; solicitação não comprovada, retorno pendente e todos os outros estados são excluídos.
- BAN-AUD-02: enquanto a S0 não definir quais lacunas são opcionais, o seletor exige ficha `persisted` confirmada, sem `missing` e sem `conflicts`, além de aptidão confirmada e versionada. É uma **restrição apenas do protótipo**, não regra comercial definitiva. Não inferir aptidão pela aparência da ficha.
- BAN-AUD-03/07: um novo caso vinculado a remessa anterior ou com snapshot bancário existente **não representa autorização de segunda remessa**. Excluir esses cenários até a S0 fornecer operação/ciclo autorizado com prova versionada.
- BAN-AUD-04: testes negativos incluídos; testes positivos usam um caso novo **estritamente local ao teste**, sem simular concessão S0 produtiva. A fixture `A-114` pós-remessa deixa de aparecer como cadastro novo apto.
- O padrão autorizado de lista é `{id,name}` (ID somente chave interna), sem rótulo de pronto ou PII no item.

## Estado visual separado

O aplicativo ainda possui `bank-dialog`, `team-dialog` e seleção ampla por `accessible()`: **o lote visual de páginas próprias não está concluído**. Não tratar o sucesso da CI da correção semântica como aprovação do fluxo visual. A tela Banco final deve consumir `projectBankReadyList()` e revalidar `bankReadyCaseForSelection()` no instante de selecionar, sem marcar conversa lida.

## Portas S0/S1 em aberto

Responder **na Issue #15** à distinção entre aptidão da ficha, remessa não iniciada, lacunas essenciais/opcionais, prova de tentativa em curso, novo ciclo versus acompanhamento de remessa anterior, autorização de segunda remessa, snapshot e idempotência. Frontend não decide essa semântica sozinho.

Nenhum token, dado bancário real, Graph, endpoint S0, ACL, RLS, deploy, merge nem envio real foi usado. `FULL LOCAL ACCEPTANCE: PASS` da branch será registrado somente após executar a CI correspondente. Revisão independente requerida para aceite.
