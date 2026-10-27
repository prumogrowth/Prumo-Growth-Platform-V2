# Retorno objetivo à F02

27/10/2026. Resposta documental ao pacote `OAI_E04_F02_S0_INTEGRATION_HANDOFF_V1.json`, para revisão pelo Codex principal. Não ratifica contrato, operação ou envio.

**Fontes atuais:** F02/PR #1 `dc18e41034329647f38737a8d8b87befcdd94eb6`, CI 40480580349 SUCCESS; S0/F02/PR #18 `88af4aea3aeb2c403bab4c078fdc04d560f2cba0`, executável `4a3d248…`/CI 40414847271 SUCCESS. Continuidade S0/S1 posterior: PR #26 I79, HEAD `8068db1…`, executável `ab96b5d…`/CI 40484344324 SUCCESS.

| Gate | Parecer | O que falta para fechar |
|---|---|---|
| G01 | PARCIALMENTE ATENDIDO | Pin/schema compatíveis; versão e evolução ainda não ratificadas |
| G02 | PARCIALMENTE ATENDIDO | Registro real interno existe; faltam transporte autenticado até F02, lookup após perda de binding e decisão entre sessões |
| G03 | PARCIALMENTE ATENDIDO | Contexto CFI físico existe; quatro testemunhas seguem alegadas, sem verificação integrada na S0 |
| G04 | PARCIALMENTE ATENDIDO | I79 fornece cargo/chefia/administração; falta ato F02 de Gestor distinto com escopo/validade/revogação |
| G05 | PARCIALMENTE ATENDIDO | Contratos/classificadores Meta disponíveis; fontes de consentimento/opt-out/template/disposição e last mile pendentes |
| G06 | PARCIALMENTE ATENDIDO | Clock/expiração técnica existem; política temporal/minimização/retenção de negócio pendente |
| G07 | PENDENTE | Jornada física interfrentes ainda não demonstrada |

O status parcial reconhece componentes; **todos os bloqueios operacionais do manifest continuam**. A16–A18 permanecem INTEGRATION_PENDING; A25 continua LAB_VERIFIED, sem promoção.

O schema pinado tem o mesmo blob `61598ba702dc03f9f715673118c88f9359e64113` em S0 e I79. Os três módulos puros de handoff/lifecycle/recovery não sofreram drift; não precisam ser reconstruídos. A reexecução auxiliar de 197 testes puros passou. Nenhum desses resultados autentica uma projection recebida de chamador.

A F02 pode continuar suas validações/classificadores isolados, preservar proposta/evidência/janela/chave originais e manter os sete blockers. A emissão ao registro não pode ser presumida por flags ou hashes locais. `RECORDED`, `CURRENT` e `REPLAY` são apenas revisão; `UNAVAILABLE` pede consulta autorizada pela chave original quando o caminho estiver disponível, sem inventar rollback, nova chave ou envio. Estado terminal não é reaberto por timeline omitida.

Diferenças preservadas: unicidade S0 loja+ator+chave versus hipóteses por encerramento; janela voluntária S0 versus 48h/24h–7d de laboratório; capturador/sessão CFI originais versus futuro ratificador; cancelamento C08 local versus disposição externa incerta. `CFI_CONTEXT_ONLY_F02_EVIDENCE_PENDING`, `NOT_IMPLEMENTED_CONTRACT_PENDING` e flags operacionais falsas continuam válidos.

**Próximo retorno útil da F02/F03:** mapa dos quatro produtores/provas e do handover físico, reaproveitando o código existente conforme H01. A I79/G2 pertence ao principal S0/S1; não é necessário pedir outra implementação de identidade/chefia à S1. Ver [matriz completa](01_MATRIZ_G01_G07.md), [evidências](02_EVIDENCIAS_E_LACUNAS.md) e [plano](03_PRIORIZACAO_S0.md).
