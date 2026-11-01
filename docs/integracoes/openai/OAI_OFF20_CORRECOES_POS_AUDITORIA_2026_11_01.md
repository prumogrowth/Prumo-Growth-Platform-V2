# AUD-OAI-20 — Correções remanescentes após auditoria OFF-19

**Data:** 01/11/2026. **Escopo:** correções **da frente OpenAI**, ainda exclusivamente offline. Não há alteração de contratos da S0/Meta, banco, Frontend ou autorização de operações reais.

## Base e decisão

A OFF-19 concluiu [968/968 testes Node e 24/24 verificações AST S0](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41339079856), porém registrou duas superfícies sob responsabilidade direta da OpenAI ainda não resolvidas:

1. `AUD19-P3`: funções legadas do `core.mjs` acessavam campos fornecidos por chamadores **antes** de validar integralmente as estruturas, permitindo getters/protótipos/arrays esparsos em caminhos não cobertos pela correção de `versionGate`.
2. `AUD19-P2`: `responses-shape-preflight-lab.mjs` retornava `candidateRaw` (texto não confiável do modelo), que um consumidor futuro poderia encaminhar sem passar pelo validador específico da F01/F02/F03 e pelas decisões S0.

Esses riscos foram tratados neste lote **antes** de prosseguir no desenvolvimento com a Meta ou com testes pagos da API.

## Correções incorporadas (LAB)

### AUD20-01 — Pré-validação de toda árvore em core.mjs

`validateF01`, `validateF02`, `prepareF03History`, `validateF03Proposal` agora rejeitam uma entrada hostil **antes de ler o primeiro campo de negócio**, por meio de `safeTree`: propriedades próprias de dados, objetos simples/null, arrays densos, sem funções/getters, ciclos, symbols, protótipos alterados ou estruturas recursivas profundas. `onlyKeys` passou a conferir protótipo simples, descritores de dados e chaves próprias permitidas, em lugar de `Object.keys` isoladamente.

**Limites:** verificações sintéticas JavaScript não provam segurança de um objeto `Proxy` com traps no mesmo processo, tampouco são autorização de S0. O `core.mjs` continua um componente interno de laboratório, **não** deve ser importado diretamente por endpoint externo ou exposto a dados reais sem host confiável, normalização e contrato autenticado.

### AUD20-02 — Quarentena de saída Responses

`inspectResponsesShape` **não devolve mais `candidateRaw`** mesmo quando reconhece um JSON com `schemaVersion/providerTag` compatíveis. O resultado de êxito mantém apenas `UNTRUSTED_JSON_CANDIDATE` e a operação, com sinalizadores `candidateRawExposed=false`, `requiresDomainEvaluation=true` e **todos os grants e permissões `false`**. Respostas negativas também não contêm o conteúdo.

**Mudança proposital incompatível no contrato de laboratório:** `prumo.openai.responses-preflight-result/0.1-lab` evoluiu para `.../0.2-lab`. Os testes OFF-16 foram atualizados para exigir ausência de `candidateRaw`. Não há consumidores reais ligados à versão anterior. **Nunca interpretar o êxito de formato como segurança semântica ou autorização de publicação**. Futura integração precisará passar texto não confiável, por caminho controlado, aos validadores específicos F01/F02/F03 e ao recheck S0. Esse transporte seguro **ainda não existe** e não está sendo inventado por esta correção.

## Testes e verificação

- 22 novos testes `off20-remediation.test.mjs`: entradas com getters não executados, fontes com protótipos, arrays esparsos, ciclos, validação de campos F01/F02/F03 e ausência de conteúdo bruto em três pré-validadores.
- Testes herdados OFF-16 revistos para quebra declarada do schema `0.2-lab`.
- **Meta de CI:** 990 testes Node (968 herdados + 22 novos), 0 falhas/ignorado, **24 testes Python AST** S0 pinados, executados separadamente.
- Gate de delta exige somente os arquivos `core.mjs`, `responses-shape-preflight-lab.mjs`, seus testes, documentação e workflow da frente OpenAI, sem alteração S0/Meta/Frontend/Supabase.

## Situação remanescente

| Item | Situação após este lote |
|---|---|
| AUD19-01/02 (versões e relógio) | **Corrigidos OFF-19**, ainda sem promoção operacional |
| AUD19-P2 (exposição acidental de candidateRaw pela OFF-16) | **Mitigado OFF-20 com remoção de campo e schema v0.2**, ainda sem sink real e sem avaliação semântica |
| AUD19-P3 (getters e estruturas hostis em core.mjs) | **Endurecimento OFF-20**, ainda somente offline; não promover o módulo a endpoint |
| S0/Meta/Graph/consentimento/PG hospedado | **Pendente de terceiros**, não pode ser corrigido unilateralmente |
| Conteúdo bancário oficial e manifestação documental | **Pendente de autorização externa**, não derivável de testes técnicos |
| IA Analista/Otimizadora e IA Gestora | **Futuras trilhas de produto**; não alegar que estão implementadas pela frente F01/F02/F03 |
| Testes semânticos de modelo real | **Ainda não iniciados**, exigem missão explícita, orçamento e credencial em segredo protegido |
| Merge, release, produção | **Não autorizado** |

**Parecer após primeiro CI validado:** `REMEDIACAO_INTERNA_OFFLINE_APROVADA_COM_BLOQUEIOS_EXPLICITOS`. [GitHub Actions 41345415665](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41345415665) confirmou **990/990 Node PASS**, 0 FAIL, 0 SKIP e **24/24 Python AST da S0 pinada PASS** (suítes distintas); o relatório e o roteiro serão revalidados em novo CI após seu commit de fechamento. Isso não equivale a uma frente livre de todo risco nem dispensa homologação externa. Nenhuma chamada OpenAI/Meta real, uso de dados de cliente, alteração de banco, merge ou deploy.
