# S0/S1 — checkpoint I82 — borda administrativa Edge local

Estado: **certificada em laboratório descartável**, CI40554841552 SUCCESS.
Não constitui autorização hospedada nem conclusão operacional de G2.

## Continuidade

- Base I81: PR Draft #32, código `4ba266d04b47fcb8036352970456d0dd5b2d09a7`,
  checkpoint `c267c5604c1a879726824a3a3f26b7fb63f48127`, CI40543117528 SUCCESS.
- I79/I80 e S1 original `8780b576aa18bd3983c063339e2e42d2452af22c` preservados.
- Branch própria: `exp/s0-s1-i82-edge-administrativa-local-20261027`.
- PR Draft #35, empilhado somente na I81, sem merge de PR candidato completo.
- Código da execução corrente: `c8817429184d4fb3d5bef29cb9e99d6f2b970f63`.
- CI certificado: [40554841552](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40554841552).

## Artefatos

- [Contrato HTTP/DTO v1](contratos/i82_edge/CONTRATO_HTTP_V1.md).
- [Mapa legível por máquina](contratos/i82_edge/http_contract_v1.json).
- [Implementação, tentativas, segurança e reprodução](contratos/i82_edge/RELATORIO_E_EVIDENCIAS.md).
- [Hashes e evidência de fechamento](contratos/i82_edge/evidencias.json).

Edge TypeScript/Deno local → GoTrue real → identidade do servidor/HMAC →
portas assinadas I79/I80 → domínio e validador NOLOGIN da I81 → COMMIT.
Python permanece no laboratório; não é runtime nem API intermediária.
Os seis comandos administrativos existentes são reaproveitados integralmente.

Somente 16 arquivos executáveis/configuração novos; nenhum executável histórico
é reescrito. Delta SQL mínimo insere fence INVOKER nas duas pontes, mantendo
ACCESS SHARE até COMMIT e recusando colunas metadata-only não revisadas.
Owners, grants de dados, policies, triggers e constraints I81 são conservados.

## Evidência certificada

20/20 cenários HTTP reais pela Edge, GoTrue e PG17; 12/12 Deno; 1 teste com
7 vetores de compatibilidade Python/TS; I79/G1 62/62 e I80 33/33 após o fence.
I81 6+1+14, CFI/F02 56/56, histórico 19/19 por perfil, 288 unitários S0 e
193 S1/catálogo, regressões PG17 históricas e 34 checks SQL preservados.
Repetições de perfil não são testes novos. Jobs 122368004210/122368003850.

Catálogos after e final idênticos: 106→107 funções, 57 triggers, 418 constraints,
145 policies e todos os owners/ACLs de dados preservados. Único helper novo
é INVOKER. Owners NOLOGIN e ausência de membership executável ao login mantidas.
Cleanup da stack confirmado; sem ResourceWarning. Hashes/recortes no artefato
12756677846 e em evidencias.json; o commit documental não altera os executáveis.

## Bloqueios e próximo avanço

Não há perfil de deploy, convite/criação Auth, UI, migração hospedada ou operação
real. Compartilhamento de login/chave no laboratório não é custódia produtiva.
Provisionamento dedicado, rotação, TLS, controle global de abuso, governança DDL
e homologação operacional ainda precisam de validação própria.

Próximo avanço: revisar o DTO com o Frontend e
preparar provisionamento local dedicado da borda, separando login/chave/custódia
sem ampliar autoridade. Reexecutar o mesmo contrato e cenários reais antes de
qualquer proposta de homologação hospedada, que exigirá autorização própria.
Não refazer UI visual nem presumir aceite das prévias.

Decisões de classificação/chefia legada continuam explícitas do Diretor.
Nenhuma permissão comercial nova ao Gestor. F02 G01–G06 permanecem parciais e
G07 pendente. CFI-01 permanece captura/recheck técnicos, sem conclusão comercial.
Issue #23 e G2 continuam abertos/parciais.
