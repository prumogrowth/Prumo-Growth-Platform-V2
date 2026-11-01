# OFF-04 — Registro de implementação e auditoria local

**Data:** 31/10/2026 | **Estado:** DELIVERED_OFFLINE_CANDIDATE / REGRESSÃO GERAL PENDENTE

## Proveniência

Base de documentação e código local: `OAI_OFF_02_03_CUMULATIVO_CORRIGIDO_2026-10-31.zip`, patch incremental sobre OFF-01 `394512327cd3756dfbe61ff970a6279c354b6565` (árvore `87a3ce85b2ead682038d4bee104ca47dd006c971`). O conteúdo cumulativo está incluído no pacote deste lote. Não há commit Git remoto da OFF-02/03 ou OFF-04 criado por esta execução; não foi possível clonar o repositório pelo terminal sem resolução DNS. Isso **não** significa que a árvore Git foi reproduzida: o pacote local é um patch a aplicar e rever sobre a OFF-01.

## Arquivos adicionados na OFF-04

- `e04_offline_lab/f02-plan-boundary.mjs`: borda tipada e continuidade candidata pura.
- `e04_offline_lab/tests/f02-plan-boundary.test.mjs`: 69 testes Node nativos.
- `OAI_OFF_04_PLANEJAMENTO_F02_CANDIDATO_v0_1.md`: contrato e limites.
- `OAI_OFF_04_RELATORIO_EXECUCAO_v0_1.md`: este registro.

Os arquivos antigos de OFF-02/03 corrigidos seguem byte a byte no pacote, sem alterações neste lote. Não houve alteração S0/S1, Meta, Frontend, schema SQL ou serviços.

## Provas realizadas

- Node.js 22.16.0; `node --test docs/integracoes/openai/e04_offline_lab/tests/f02-plan-boundary.test.mjs`: **69 testes, 69 PASS, 0 FAIL, 0 SKIP**.
- `node --check` do novo módulo e da nova suíte: **PASS**.
- Inspeção estática do novo módulo: zero imports de bibliotecas, nenhuma operação de arquivo, rede, DB, subprocesso, credencial, SDK, envio ou relógio real.
- Negativas: revogação > stale; tenant/pessoa/caso/cadeia; consentimento sintético por `optOut`; handoff definitivo; template inativo, não aprovado, de outra loja/finalidade ou versão; JSON duplicado; getters; resposta tardia; slots e `tool_calls`; replay exato/divergente; evento inter-tenant; `API_ACCEPTED`/`UNKNOWN` ≠ `sent`; `131049` sem perda; conflito de `SENT` e falha definitiva.

**Não executados:** 342 testes S2/OFF-01, 162 testes OFF-02/03 e as 70 fixtures E02 — bases não presentes integralmente no pacote. O total aritmético esperado em checkout completo, se não houver mudanças nas contagens anteriores, é **573**, não um resultado executado. A38 não recuperada; homologação S0/Meta inexistente.

## Segurança e observações

Privacidade: `f02ProviderView` usa apenas aliases, versão, finalidade, horários e instrução F02, sem IDs reais de loja/pessoa/caso, segredo, HMAC, sessão, recibo, grants ou consentimento. Inputs arbitrários com accessors/propriedades extras falham. Propostas malformadas nunca geram envio ou agendamento; output conserva `sendAuthorized:false` etc. IDs/hash/fingerprint da fixture não são prova de autenticação ou autorização física.

**Limitações internas ainda abertas:** regressão completa em checkout OFF-01, publicação em branch própria sem merge, compatibilidade S2 com toda a borda OFF-04, cobertura de testes de injeção por corpus E02, validação semântica de conteúdo e política temporal produtiva. OFF-04 não sana o aceite pendente OFF-02/03 nem prova S0. Próxima tarefa independente: executar regressão integrada e resolver diferenças, mantendo Issues #7/#9/#10 registradas e sem duplicação.
