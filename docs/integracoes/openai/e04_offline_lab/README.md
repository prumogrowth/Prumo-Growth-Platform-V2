# E04 — Laboratório offline isolado OpenAI (v0.1)

**Início autorizado pelo responsável:** 22/10/2026, solicitação expressa para implementar E04 offline com dados fictícios, na branch `feat/s2-openai-adapter-sintetico` / PR #3. **Esta autorização substitui o bloqueio E04 anterior apenas neste escopo.** Não autoriza E05, billing/chaves, chamadas remotas, Meta/Banco, dados reais, deploy, migração S0, outros PRs nem merge.

## O que foi implementado

- `core.mjs`: funções puras, **sem dependências npm**, banco, arquivo, rede ou efeitos de negócio; são **validadores candidatos**, não SDK OpenAI nem contrato físico S0.
  - `versionGate`: negação por autenticação/concessão/tenant **antes** de discutir versões; versão de ciclo ≠ versão de caso/ficha/catálogo/atribuição.
  - `validateF01`: protege posse IA, handoff, ausência de roster de consultores, fontes de loja atual e ofertas ativas, e rejeita pedido de mutação enviado no retorno.
  - `validateF02`: exige solicitação **separada** S0, opt-out explicitamente falso, rota humana após humano, templates existentes na loja/finalidade/versão, limite/ordem/horários; não permite slots, status ou reivindicação de `sent`.
  - `prepareF03History`: somente encerramento humano autenticado; fonte de todos os casos da **mesma pessoa/loja** até cutoff; metadata de mídia indisponível sem transcrição inventada; vincula versão observada do snapshot ao contexto.
  - `validateF03Proposal`: confere código de catálogo, fonte na seleção, opcionais, essenciais e conflitos; sugestão de `perdido` exige referência a desistência verificada pelo fixture S0; `vendido`/remessa não são ações.
- `tests/offline.test.mjs`: **50 casos sintéticos** distribuídos por portão S0, F01, F02 e F03. Os casos testam apenas a lógica deste laboratório, **não** exaurem os 70 cenários E02 nem executam a IA.
- `package.json`: comando de testes com o `node:test` nativo; nenhuma instalação de pacote é necessária.

## Execução local/reproduzível

Requer Node.js com módulos ESM e `node:test` (preferível Node 22, sem internet). Na raiz do repositório:

```bash
node --test docs/integracoes/openai/e04_offline_lab/tests/offline.test.mjs
```

Ou na pasta deste laboratório:

```bash
npm test
```

**Registro honesto de prova desta rodada:** os mesmos corpos de `core.mjs` e `tests/offline.test.mjs`, recém escritos no PR, foram executados em um **runtime JS V8 isolado** com assertivas `equal` e `deepEqual` equivalentes, após adaptação apenas dos imports nativos para carregar as funções em memória: **50/50 verificações passaram**. **Não** afirmamos execução de `node --test` ou de CI sobre o checkout; isso permanece como verificação complementar futura. **Nenhuma** chamada API ou ambiente remoto foi envolvida.

## Fronteiras e limitações importantes

1. Entrada `scope`, catálogo, versão, declaração `verifiedWithdrawalSourceIds`, template elegível, fechamento e fontes são **simulações de decisões já tomadas pela S0**, jamais concedidas por cliente/modelo. Não aceitar esses campos de um provedor real como prova de autenticação ou consentimento.
2. Snapshot do laboratório usa **sequência global sintética por pessoa/loja**. A versão física S0 do PR #12 só atesta recibo local por caso; manifesto multi-casos, multi-telefone, fonte multimodal, catálogo e autorização permanecem **[R/V]**. Não plugar este stub ao recibo físico por mera coincidência de nomes.
3. `validateF03Proposal` valida **rastreabilidade declarada e estrutura**, **não verifica semanticamente** que o texto da fonte prova um valor financeiro: isso exige gabarito de conteúdo, qualidade do modelo e política de aplicação S0; jamais autoaplicar diretamente.
4. `PROPOSED` é **apenas proposta**, não texto enviado, evento de negócio, remessa, C09 ou cadastro modificado. Nenhuma função persiste dados, agenda mensagens, edita conhecimento ou chama MCP; situação atual de remessa/venda é exclusiva S0/humano com provas apropriadas.
5. Não há mocks HTTP/n8n, STT/TTS, SDK, prompts produtivos, segredos, preços nem modelos reais. Extensão deve continuar **dentro da pasta da frente OpenAI** até conciliação com S0/Meta.

## Correspondência documental (parcial)

| Suite | Documentos/situações cobertos de modo preliminar |
|---|---|
| GATE01..06 | S0 autoridade, versão stale/denied, SNAP F03, SYN-08/09/10 |
| F01_01..10 | SYN-17/18/27/28/57/58/60, sem roster e handoff |
| F02_01..13 | SYN-47/48/49/50/55, templates/cadeias só propostos, sem status `sent` físico |
| F03_01..21 | SYN-02/07/08/09/10/33/34/39/43/45/46/69, cutoff, fonte multi-caso e propostas |

**Não** marcar esses SYN como `PASS` na matriz E02: testes unitários de guarda não são homologação de integração, execução dos fixtures originais ou prova de qualidade do modelo. Cada correspondência é parcial.

**Próximo incremento E04 elegível:** reforçar schemas de evidência/versão e cobertura de cenários negativos sobre o próprio adaptador sintético; converter oráculos em testes estruturados **após** ratificação dos contratos físicos. **E05 continua completamente vedada sem autorização independente.**
