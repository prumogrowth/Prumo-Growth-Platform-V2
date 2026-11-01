# OFF-05 — Relatório de implementação e auditoria offline

**Data:** 31/10/2026. **Estado:** módulo F01 desenvolvido e testado localmente; NÃO HOMOLOGADO.

## Entrega

Adições locais `docs/integracoes/openai/e04_offline_lab/f01-sales-boundary.mjs`,
`docs/integracoes/openai/e04_offline_lab/tests/f01-sales-boundary.test.mjs`, este relatório, especificação e evidência de execução. Nenhuma alteração em código S0/S1, Meta, Frontend, arquivos herdados da OFF-01, configurações ou credenciais.

## Testes

Executados em Node 22.16.0, `node --test`:
- **100 testes novos OFF-05 aprovados**, 0 falhas.
- **169 testes aprovados na execução combinada OFF-04 + OFF-05**, 0 falhas.
- As validações incluem regras de handoff humano irreversível, falta de grant, versões, opt-out, fontes históricas/vencidas, aliases/claims, injeção como dado, STT incerto, JSON duplicado, getters, replay, respostas tardias, proveniência e ausência de efeitos produtivos.

**Não testado neste lote:** a árvore S2 original, os 342 testes S2+OFF-01 anteriormente reportados, os testes OFF-02/03 porque dependem dos módulos herdados ausentes no pacote incremental, CI GitHub, interoperabilidade física ou todos os 70 oráculos E02. Portanto não anunciar execução do total acumulado. F01 sintética não demonstra segurança de geração, moderação de conteúdo real nem autorização S0.

## Auditoria e limitações

A revisão de código incluiu correções locais durante a execução: condição explícita `DENIED` para handoff pré-modelo; verificação de replay em bytes e proposta de fingerprint; validação por descritores de acessores em opções, journal e auditoria; prazo e vigência da fonte rechecados no retorno. Testes adversariais cobrem os reparos. Sem chamadas reais.

**Risco aceito só para laboratório:** texto livre não pode ser semanticamente certificado por regex, código de claim ou alias; as claims/autorizações/instantes do envelope são fixtures manipuláveis e dependem de integração autenticada S0. A guarda de evento não é ledger transacional. Exposição acidental de texto potencialmente pessoal por um host que ignore a regra de minimização não é evitada apenas por aliases. Falta política ratificada de STT/TTS, preços, fontes de conhecimento e janela Meta.

## Próxima fase

- Registrar dependência S0 F01 sem duplicar #2/#7/#8/#10, revisar respostas na mesma Issue.
- Publicar patches OFF-02/03/04/05 em branch específica após reconstrução/validação do ancestral OFF-01 e regressão completa; não afirmar que houve commit ou CI agora.
- Confrontar E01/E02/S2 e executar bateria conjunta, sem recuperar A38 por substituição.
- A frente OpenAI pode desenvolver materiais e corpus de testes independentemente; integrações só após ratificação dos responsáveis.
