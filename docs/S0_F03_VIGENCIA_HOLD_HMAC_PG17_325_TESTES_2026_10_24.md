# E04/S0-F03 — Vigência do fechamento de identidade em leitura: 325 testes PG17

**Data:** 24/10/2026. **Repositório oficial e único de escrita:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`. **Branch:** `feat/oai-s0-f03-history-port-20261023`; [PR #1 Draft](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/1), base `feat/s0-cfi01-f03-auth-preflight-20261020` (não `main`). E04 sintética e sem deploy.

## Comprovação física

[GitHub Actions #40138198314](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40138198314), commit `bb5c7f7681108d4144b510e31664b1254a1ccd38`: **SUCCESS, PostgreSQL 17.11**.

- **84/84 testes S0 CFI-01**: `Ran 84 tests ... OK`.
- **241/241 testes F03**: `Ran 241 tests ... OK`, sendo **153 testes F03 físicos no PostgreSQL** (além de 24 do leitor, 31 de selo, 15 da barreira HMAC, 18 da reserva CAS unitária).
- **325/325 testes PASS**, com **18 cenários novos PG17 `test_136` a `test_153`** efetivamente executados.

A primeira tentativa [#40138051443](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40138051443) terminou com **um erro no cenário 139**: o teste tentou atualizar `motivo` com o valor `MOTIVO_ATUALIZADO`, proibido pelo CHECK da migração S0/028. O fixture foi corrigido para **`NEEDS_REVIEW`**, valor permitido, e a suíte completa passou. Isso era um erro do teste, não indicação de que o verificador liberava indevidamente o conteúdo.

## Implementação

A [porta de verificação S0](../backend/s0_f03_identity_resolution_verify_local.py) foi adicionada após a [cadeia tripla HOLD de revisão, ratificação e fechamento](./S0_F03_FECHAMENTO_TRIPLO_HMAC_PG17_307_TESTES_2026_10_24.md).

**A verificação não cria registros nem autoriza a F03.** Exige `IdentityProvider` servidor, sessão existente, equipe S1 ativa, ator igual ao gestor que assinou o fechamento e papel `gestor` vigente na mesma concessionária. No mesmo acesso transacional, confere cadeia revisão–ratificação–fechamento, os três atores distintos, atribuição humana ainda válida, versões do ciclo/identidade persistidas e fontes atuais.

Recalcula o **HMAC-SHA256** da pendência sintética a partir de seu registro atual — canal, id externo, telefone, texto, motivo, timestamp e identificadores de escopo — usando a chave fornecida pelo servidor S0 em runtime. Compara em tempo constante ao HMAC imutável armazenado no recibo. Versão de chave divergente, texto/telefone/motivo alterados, alias novo que aumenta a versão, ciclo ou atribuição mudados tornam o recibo **`STALE_REVIEW_REQUIRED`**.

Além do recibo original, a porta procura por **outra pendência** na mesma concessionária compatível com telefone principal ou alias do cliente, incluindo variante brasileira da S0/028. Se encontra, devolve **`CONFLICT_REVIEW_REQUIRED`**, mesmo quando o HMAC original ainda confere. Um número sem correspondência ou de outra concessionária não causa esse bloqueio.

Quando todos os controles locais conferem, o resultado é **somente `CURRENT_HOLD_ONLY`**, sem retornar cliente, telefone, texto, segredo ou prova. Não é uma permissão de uso do histórico, não altera o estado da pendência S0/028 e nunca libera CAS F03.

## Cobertura adversarial adicional

[18 casos físicos PG17](../backend/tests/test_s0_f03_pg17_integration.py): recibo válido sob HOLD, resultado sem dados, reserva F03 permanecendo recusada, mutação posterior de texto/motivo/telefone, alteração de alias/telefone principal, ciclo alterado, atribuição encerrada, segunda pendência surgida posteriormente, pendências não relacionadas na mesma ou outra concessionária, gestor diferente, sessão desconhecida, chave HMAC ou versão errada, permissão de gestor expirada, S1 ausente e pedido de escopo/chave inválidos.

## Limitações obrigatórias: NÃO promover o HOLD a grant

1. O teste de leitura usa *snapshot transacional com locks nas linhas existentes*. **Não prova ausência de phantoms:** outro escritor S0 pode inserir uma pendência compatível após o SELECT ou enquanto ela está sendo consultada se não obedecer um bloqueio de escopo comum. Para um futuro gate de liberação, falta serializar também os escritores e a verificação em uma única regra S0 ou uma estratégia equivalente ratificada; o estado HOLD é intencional.
2. Apenas **um recibo de pendência** tem HMAC comprovado. Outras pendências que ainda não tenham chegado a uma linha do banco, todos os candidatos multilead e variações futuras da regra de telefone **não** são globalmente certificados. Não tomar `CURRENT_HOLD_ONLY` como resolução civil.
3. Fontes de ficha e catálogo ainda são sintéticas; não existe operação homologada de campo real da ficha com CAS, prova de mídia, armazenamento/rotação real de HMAC, LGPD de acesso mínimo ou fluxo GoTrue hospedado. Nenhum usuário real foi autenticado.
4. A cadeia de três humanos continua **AUDIT/HOLD_ONLY**. A S0 não remove a pendência, a F01 não retoma o atendimento após handoff, F02 é independente, e F03 nunca recebe por esta via permissão para ler conteúdo ou alterar cadastros.
5. Nenhum merge, deploy, E05, serviço Meta/OpenAI pago ou banco de produção foi executado. `main`, a base S0 e a branch principal OpenAI permaneceram fora das operações desta entrega.

**Próxima etapa técnica:** bloquear colisões entre **múltiplos leads candidatos** e a criação concorrente de pendências com mecanismo S0 que garanta uma visão consistente no ponto da decisão, antes de sequer considerar criar um gate de liberação independente da F03.
