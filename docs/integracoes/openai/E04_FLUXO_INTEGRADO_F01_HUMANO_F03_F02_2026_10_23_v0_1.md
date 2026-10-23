# E04 — Fluxo sintético F01 → humano → F03 → F02 | v0.1

**Data:** 23/10/2026. **Fase:** E04 offline expressamente autorizada pelo responsável. **Estado:** implementação do laboratório, não integração com S0/Meta. [P/R] assinaturas e estados físicos continuam sujeitos a ratificação; E05 não foi autorizada.

## 1. Entrega verificável

- [`e04_offline_lab/journey.mjs`](./e04_offline_lab/journey.mjs): `evaluateOfflineJourney(flow)` **pura e sem I/O**; orquestra as guardas pré-existentes em [`core.mjs`](./e04_offline_lab/core.mjs), [`plan-lifecycle.mjs`](./e04_offline_lab/plan-lifecycle.mjs) e [`template-frequency.mjs`](./e04_offline_lab/template-frequency.mjs).
- [`e04_offline_lab/tests/journey.test.mjs`](./e04_offline_lab/tests/journey.test.mjs): 43 casos novos, com cenários positivos e adversariais. Os casos usam **somente pessoas, concessionárias, catálogos, versões e recibos fictícios**.
- `journey.mjs` SHA de conteúdo Git `b5ecf051e7bc30d5653ab214ffff6e731f6bbded`; testes SHA `2f779e94bb6903d0d519049395752e3b33b76b7e`.

## 2. Fronteiras no fluxo

| Transição | Condição do laboratório | Resultado permitido |
|---|---|---|
| Contexto S0 → F01 | Concessionária/caso autenticados, posse IA, sem handoff, fontes comerciais elegíveis e versionadas | **Somente proposta**. Nenhum envio |
| F01 → humano | Evento de handoff **autenticado pela S0 fictícia**, relativo ao mesmo caso | F01 não retorna ao mesmo caso; conteúdo gerado tardiamente não reabilita venda |
| Humano → F03 | **Encerramento expresso autenticado**, histórico da pessoa **na mesma concessionária** até cutoff, versões e catálogo separados | Campos explícitos de todos os casos autorizados, inclusive opcionais, em proposta; sem escrita |
| F03 → eventual F02 | Após F03 válida, **nova solicitação separada** e autenticada da S0, cadeia anterior cancelada e rota humana | F02 somente propõe templates/versões da allowlist; F03 não aciona F02 sozinha |
| F02 → revisão S0/Meta | Plano S0 amarrado à proposta original, categorias autorizadas independentes do modelo, estado da cadeia, frequência local e recusas Meta | **`READY_FOR_S0_RECHECK_ONLY`** ou negação/revisão. Nunca agenda/envia |

Se essencial está ausente ou há conflito na extração F03, a resposta é **`HUMAN_COMPLEMENT_REVIEW`**; não cria cadeia F02. Se a F03 sugere `perdido` por desistência documentada, emite **`COMMERCIAL_ADVISORY_REVIEW`**, não perda comercial, nem recontato automático. `vendido`, negativa bancária e remessa permanecem fora do controle do modelo.

## 3. Controles adversariais e segurança

- Qualquer negação de autorização precede detalhes de dados/versões: não divulgar o caso, templates ou histórico de outro tenant.
- Dados de outro cliente ou de outra concessionária são recusados, inclusive fontes F03 de caso antigo fora do escopo da mesma pessoa/loja.
- Cutoff do encerramento conserva limite histórico: a fonte de mensagem posterior não pode fundamentar extração do encerramento anterior.
- F01 não retorna após handoff; Consultor não edita ficha; a S0 define roteamento de complementos e eventual pedido F02 independente.
- Categoria Meta **vem do catálogo de confiança S0**, não da escolha do modelo: um template MARKETING não vira UTILITY por texto livre.
- `API_ACCEPTED`/`QUEUED`/`UNKNOWN` não provam `sent`; `131049` não é desistência, duas falhas qualificadas ou motivo automático de perda. A política local de exemplo `2/24h` **não** é quota Meta.
- A saída do laboratório não contém campos de envio, status comercial, confirmação bancária, aplicação de ficha, mutação de auditoria, C09 ou tarefa recorrente.
- O sinal `READY_FOR_S0_RECHECK_ONLY` nunca é aprovação de disparo; um backend real precisará de **nova autenticação, autorização, catálogo, consentimento, regras de Meta e concorrência imediatamente antes de enviar**.

**Limite estrutural essencial:** booleans como `authenticatedS0Request` e `closureAuthenticated`, seleções de evidência, controle de posse, catalogação de template e confirmação de transporte são **fixturas declaradas como confiáveis no laboratório**, não assinaturas criptográficas nem validação física de uma S0 ou da Meta. A F03 do laboratório valida forma e fonte declarada, não a veracidade semântica de renda/documento extraído. Esta simplificação não pode ser promovida diretamente a produção.

## 4. Evidência de regressão desta rodada

A partir de **dez arquivos reais recuperados da branch GitHub**, foram executadas as funções e suites em V8 isolado, removendo apenas os imports de `node:test` e `node:assert/strict` e fornecendo equivalentes de `test`, `equal` e `deepEqual` para os casos declarados.

| Suíte | Casos | Resultado |
|---|---:|---|
| Guardas F01/F02/F03 de `offline.test.mjs` | 50 | 50 PASS |
| Recibos Meta | 33 | 33 PASS |
| Frequência local/erro 131049 | 33 | 33 PASS |
| Ciclo de plano F02 | 53 | 53 PASS |
| Jornada integrada | 43 | 43 PASS |
| **Total nesta execução V8** | **212** | **212 PASS, 0 FAIL** |

**Atenção:** a execução conjunta **não foi `node --test` nem CI**. Rodadas anteriores provaram individualmente as suítes de frequência/Meta e ciclo de F02 no Node, mas isso **não** comprova os 212 casos no runner Node. Para a execução futura no Node do repositório:

```sh
cd docs/integracoes/openai/e04_offline_lab
npm test
```

**Os 70 SYN-01..70 da E02 seguem como oráculos documentais originais ainda não executados/homologados segundo seu protocolo próprio.** Os 212 testes unitários **não** são equivalentes a 212 casos de produto aprovados, nem a cobertura oficial E02.

## 5. Pendências para integração real

- **CFI-01 F03:** identidade e manifesto multi-casos físico, mídia, autorização/cutoff, catálogo, versões distintas, aplicação idempotente S0, correções e roteamento humano.
- **CF-OP-02/C09 F02:** semântica física de plano, catálogo/versões/categorias Meta, política local de frequência, erro 131049, provas `sent`, tentativas definitivas e matriz estado/fase.
- **WA-22:** integridade de assinaturas, canal, reserva, retries, relógios, opt-out, WABA e limites adaptativos.
- **E05:** autorização separada para chave, cobrança, custo, modelo, API real, dados sintéticos e ambiente; nenhuma concedida neste marco.

**Situação final:** código e suíte implementados na branch isolada PR #3. Sem dados reais, chamadas externas, credenciais, deploy, migração, merge ou alteração de S0/Meta.
