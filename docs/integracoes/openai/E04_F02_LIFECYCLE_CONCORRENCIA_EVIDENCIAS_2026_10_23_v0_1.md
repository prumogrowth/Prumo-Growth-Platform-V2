# E04 — Ciclo de vida F02 offline: concorrência, evidências e rechecagem S0 (v0.1)

**Data:** 23/10/2026. **Estado:** primeira implementação **executada** em laboratório isolado. Código e testes na branch OpenAI do PR #3, dentro da E04 explicitamente autorizada pelo responsável. **Não** constitui contrato físico, enum S0/Meta ratificado, implementação de envio, autorização de custo/API ou execução dos 70 oráculos SYN documentais.

## 1. Escopo implementado

- [`plan-lifecycle.mjs`](./e04_offline_lab/plan-lifecycle.mjs): função pura `reconcileF02Plan(scope,plan,events)` com parâmetros de **fixture S0 simulada**, nenhum I/O ou efeito comercial.
- [`plan-lifecycle.test.mjs`](./e04_offline_lab/tests/plan-lifecycle.test.mjs): **53 testes nativos Node** cobrindo versões independentes, idempotência de eventos, reconciliação por sequência S0 fictícia, recibos pendentes, opt-out, handoff, recontato pós-humano, eventual `sent` final e bloqueio 131049.
- Não instala dependências npm. A suíte existente do projeto usa `node --test tests/*.test.mjs` no [laboratório E04](./e04_offline_lab/README.md); o glob passa a incluir este novo teste.

## 2. Semântica de resultado — somente diagnóstico

| Resultado offline candidato | Interpretação | Ação vedada |
|---|---|---|
| `DENIED` | Grant/tenant/opt-out/autorização S0 não elegível ou vínculo comercial incompatível | Não revelar plano nem consultar a Meta |
| `STALE` | Versão de caso, catálogo ou cadeia mudou, separadamente | Não reutilizar planejamento antigo |
| `INVALID_INPUT` | Payload de fixture malformado, outro escopo, templates/tentativas incompatíveis | Não inferir fontes, versões ou estado |
| `REVIEW_REQUIRED` | Provas não verificadas, evento contraditório, falha definitiva sem contrato S0/Meta ou colisão | Não decidir cliente perdido nem tentar novamente por conta própria |
| `CANCELLED` | Cancelamento/opt-out/handoff incompatível atestado em evento | Não reativar cadeia de IA |
| `HOLD_FOR_S0_REVIEW` | Novo inbound ou handoff humano que exige validação de elegibilidade | Não reiniciar F01 após humano |
| `META_ECOSYSTEM_REVIEW` | Rejeição 131049 atestada na fixture | Não interpretar como desistência ou uma das duas falhas técnicas qualificadas |
| `AWAITING_META_PROOF` | `API_ACCEPTED`, `QUEUED` ou `UNKNOWN` antes de prova terminal | Não reenviar cegamente nem começar relógio C09 |
| `NOT_DUE` | Próxima tentativa futura no relógio do teste | Não agendar envio |
| `READY_FOR_S0_RECHECK` | Próxima tentativa fictícia elegível a **nova avaliação externa S0** | **Não** é grant, intenção enfileirada, transporte Meta nem promessa de envio |
| `FINAL_SENT_EVIDENCE_ONLY` | Prova terminal `SENT` do template final simulada | Não marcar entregue/lido, vendido ou perdido; sem relógio C09 executado |

`NO_PENDING_ATTEMPT` representa plano sem tentativa futura dentro do recorte, não evento comercial.

## 3. Guardas e exemplos de testes

1. **Pré-condição explícita [P]:** `authenticated`, `authorized`, `tenantAllowed`, `planAuthorized` verdadeiros e `optOut=false` vêm da **S0 fictícia**, não do modelo ou do cliente; negar antes de vazar existência/versões.
2. **Correlação [P]:** `storeId`, `personId`, `caseId`, `planId`, versões `caseVersion`, `catalogVersion`, `chainVersion` e tentativas com ID, template e versão próprios. Esses nomes **não** são schemas S0 ratificados; `chainVersion` não substitui versão de ciclo comercial.
3. **Recontato [DN]:** rota `post_human` é humana, não retoma `seller_ai`; conclusão F03 por si só **não cria** plano. O evento de plano autorizado deve vir separadamente da S0.
4. **Recibos [P]:** tentativa em `API_ACCEPTED`/`QUEUED`/`UNKNOWN` espera prova; `SENT` verificado autoriza no máximo procurar a próxima tentativa e revalidar; `DEFINITIVE_FAILED` exige revisão, não perda automática.
5. **Ambiguidade [P]:** evento não verificado, duplicata com payload contraditório, estados terminais incompatíveis da mesma tentativa e sequência colidida levam a `REVIEW_REQUIRED`. Replay idêntico é neutro, inclusive com ordem de propriedades diferente; a ordem de entrada não precisa ser cronológica.
6. **Meta [V/P/R]:** o código 131049 sinaliza restrição de ecossistema, não um limite universal de dois templates/dia; só produz hold/revisão. O controle local de frequência é separado em [`template-frequency.mjs`](./e04_offline_lab/template-frequency.mjs).
7. **Finalidade bancária [DN]:** nenhuma saída muda estado comercial, autoaplica F03, agenda Meta, calcula C09 em produção ou infere prova Banco.

## 4. Evidência de execução efetiva

**Node.js 22.16.0**, comando executado no diretório isolado:

```bash
node --test tests/plan-lifecycle.test.mjs
```

**Resultado verificado:** **53 testes**, **53 PASS**, **0 FAIL**, **0 skipped**. A execução verificou os dois arquivos locais e seus hashes Git blob:
- `plan-lifecycle.mjs`: `fb21fe91ad9c6b4e8de9cf6be79ef42127b30655`
- `tests/plan-lifecycle.test.mjs`: `c1b5586dbd490fb7f045d443f882849fd8b4841e`

Após os commits, ambos os hashes foram reconsultados na branch GitHub e **coincidiram integralmente** com os arquivos Node testados. Isto prova **este recorte unitário**, não CI completa/produção. Os **66 testes F02 frequência+transporte** foram verificados no Node na rodada anterior e os **50 antigos F01/F02/F03** tiveram prova anterior em V8, não rerun Node nesta rodada. Não somar 169 testes como uma execução única do runner.

## 5. Dependências não superadas

**Permanecem [R/V]:** semântica física de evento, autenticação e sequência S0/Meta, contratos de `sent`/falha, classificação 131049, regras C09 por fase/status, limite local configurado de verdade, vínculo de pessoa/número entre lojas, retenção, catálogo e versão/assinatura do plano. Issues [#6](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6) e [#15](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/15) seguem referências para homologação.

**Estado:** E04 offline em desenvolvimento; E03-A..H adiadas e E05 não autorizada, sem segredo, pagamento, mídia real, deploy, merge ou edição das outras frentes.
