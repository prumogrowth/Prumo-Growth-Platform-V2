# CI/S1 — candidato paralelo I29/I30

Branch exclusiva: `exp/ci-s1-consolidacao-20261025`. Fonte original verificada:
`9780f407703c402fd56567f04c34640127ce5253`. Issue #3 e cinco relatórios prévios
lidos. Nenhuma alteração em código produtivo, testes existentes, migrations,
workflows oficiais ou branches de outras frentes. Sem build de aplicação,
merge ou deploy.

## Hipótese

Os agregadores seriais anteriores pouparam runners, mas acrescentaram 54 s
(I27/I28) e 96 s (I29/I30) ao tempo dos jobs críticos. O novo candidato mantém
dois E2Es paralelos em runners separados, remove os dois jobs unitários
independentes e executa cada arquivo unitário uma única vez, enquanto o
respectivo banco inicializa. Não compartilha banco, volumes, identidade,
certificados, portas de um mesmo host nem fixtures entre os gates.

- I29: I23/I25/I26/I27 (63 testes), seguido do script I29 completo (105 cenários).
- I30: I28/I29/I30 (45 testes), seguido do script I30 completo (120 cenários).
- União dos 20 arquivos dos gates `compileall` dos controles mantida em I30.
- Cada arquivo unittest roda em processo próprio, como nos controles.
- Falha de unitário ou preparação impede E2E; falha de E2E ou limpeza reprova.
- Matrix `fail-fast: false` permite observar os dois gates mesmo se um falhar.
- Verificador exige cada marcador E2E exato uma vez e o marcador final;
  também rejeita suítes unitárias vazias, falhas ou skips.
- Artefatos de sete dias contêm IDs, descrições de cenários, logs unitários e
  tempos; não incluem `.env`, certificados, bancos ou logs de credenciais.

Mapa 1:1: `CI_S1_I29_I30_SCENARIO_MAP_20261025.json` (108 IDs unitários,
225 descrições de cenários e 20 alvos de sintaxe). Os scripts e testes E2E
originais são executados sem alterações. Isso preserva o escopo I29/I30;
não certifica outros gates da S1.

## Validação local

108/108 testes unitários aprovados em dois processos paralelos (shards 63/45),
com testes originais inalterados. Sintaxe Python e Bash e estrutura YAML
verificadas. O validador de marcadores passou testes sintéticos de aceitação
e rejeição de cenário ausente, duplicado, extra ou marcador final ausente
nos dois gates. Fixtures sintéticas não são execução E2E.

O sandbox inicial bloqueou sockets, inclusive o proxy e loopback. As execuções
autorizadas fora desse bloqueio permitiram `git fetch` e os unitários. A cópia
local corresponde ao commit remoto, com SHAs dos 439 blobs e árvore validados.
A CLI Supabase e `psql` não estão instalados neste executor; E2E real e duração
comparável serão medidos nos runners GitHub, com CLI 2.84.2 e psycopg 3.2.13
iguais aos controles. Documentação CLI consultada via MCP; changelog HTTP
indisponível no sandbox. Nenhuma versão ou configuração Supabase alterada.

## Medição e aceite

Rodadas controladas devem disparar no mesmo SHA: controles I29/I30, agregado
serial e candidato paralelo. Registrar falhas reais, contagens e todos os jobs;
não usar apenas resultado verde. Medir soma dos intervalos de jobs, intervalo
entre início do primeiro e conclusão do último, e latência desde criação dos
runs (inclui fila). Sem afirmar economia faturável, ganho futuro garantido ou
aprovação de promoção sem aceite do owner S1.

Estado: candidato pronto para medição; resultados remotos ainda pendentes.
Rollback: remover somente o workflow e scripts novos nesta branch. Os controles,
serial e workflows oficiais continuam disponíveis e intactos.
