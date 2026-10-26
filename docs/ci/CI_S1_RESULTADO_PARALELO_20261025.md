# CI/S1 — resultado do candidato paralelo I29/I30

Data local: 25/10/2026, America/Sao_Paulo (execuções 22:43–22:52; timestamps
brutos em UTC nos JSONs). Issue #3. Branch exclusiva:
`exp/ci-s1-consolidacao-20261025`; checkout inicial confirmado no commit remoto
`9780f407703c402fd56567f04c34640127ce5253`, sem trabalhar na `main`.

## Resultado

**O candidato reduziu 20,1% dos intervalos somados de runner frente aos controles,
com a mesma cobertura observada. A latência ficou praticamente igual; não há
prova de aceleração consistente frente aos controles paralelos.**

[TRECHO COMERCIAL INTERNO EXCLUÍDO DA VERSÃO PÚBLICA]
- P2: 361 → 289 s de runner (**−19,9%**); feedback desde criação 150 → 154 s.
- Somando as duas rodadas: **711 → 568 s**, economia de **143 s (20,1%)**.
  Média por rodada: 355,5 → 284 s de runner; feedback 149,5 → 149 s.
- Frente ao agregador serial, feedback médio **233,5 → 149 s (−36,2%)**,
  mas runner total **459 → 568 s (+23,7%)**. O candidato é um compromisso
  entre consumo e resposta; não domina o serial nos dois critérios.
- **8 workflows / 14 jobs concluídos SUCCESS**, sem retries ou cancelamentos.
  Orçamento observado das comparações completas: 1.738 s de jobs (28min58s),
  incluindo controles, serial e candidato, não apenas a execução candidata.

Esses intervalos não são cobrança oficial, CPU ou memória medidas. Duas rodadas
não estabelecem significância estatística; a diferença de feedback de −5/+4 s
é compatível com variação de imagem, rede, CPU, disco e escalonamento dos runners.

## Comparação no mesmo SHA

P1: `c42dd9298b2adb32058e7ddb9f345852f86791c0`.
P2: `31af366d2e6c8d59bc34e7e4dc8a2490521cae15`.
A única diferença entre P1/P2 é documentação de disparo; código, workflows,
testes, versões e inventário são idênticos. Cada rodada compara os três modos
no próprio SHA, sem reutilizar resultados de commits diferentes.

| Rodada | Modo | Jobs | Soma de runner | Intervalo dos jobs | Desde criação até último job | Runs |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| P1 | Controles I29 + I30 | 4 | 350 s | 146 s | 149 s | [#40255607197](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40255607197), [#40255607185](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40255607185) |
| P1 | Serial | 1 | 236 s | 236 s | 240 s | [#40255607217](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40255607217) |
| P1 | Paralelo candidato | 2 | 279 s | 141 s | 144 s | [#40255607214](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40255607214) |
| P2 | Controles I29 + I30 | 4 | 361 s | 147 s | 150 s | [#40256016509](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40256016509), [#40256016312](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40256016312) |
| P2 | Serial | 1 | 223 s | 223 s | 227 s | [#40256016350](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40256016350) |
| P2 | Paralelo candidato | 2 | 289 s | 151 s | 154 s | [#40256016301](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40256016301) |

Soma de runner = soma de `completed_at − started_at` dos jobs. Intervalo dos
jobs = última conclusão − primeiro início por modo. Feedback = última conclusão
de job − primeira criação de run do modo, incluindo espera inicial; não mede
entrega de notificação à interface. Controles agrupam os dois workflows.

## Mudança incremental

Novo workflow `.github/workflows/exp-s1-i29-i30-parallel.yml`, restrito à branch
experimental, com matriz de dois runners independentes e `fail-fast: false`.
Os unitários rodam durante a inicialização do respectivo Supabase descartável:
I29 recebe I23/I25/I26/I27 (63 casos) e I30 recebe I28/I29/I30 (45 casos).
Cada arquivo mantém processo próprio. Depois, cada job executa o E2E original
completo em seu banco exclusivo. Não se compartilham banco, volumes, fixtures,
identidades ou certificados entre os jobs.

De quatro jobs de controle para dois; de 201 execuções unitárias cumulativas
para 108 casos únicos, uma vez cada. Mantidos dois bancos e os gates de sintaxe
com a união dos 20 arquivos dos controles. CLI 2.84.2, psycopg 3.2.13 e lista de
serviços excluídos iguais aos controles. Nada foi removido dos E2Es para ganhar
tempo. A espera do startup esconde os unitários do caminho crítico quando há
folga; o download das imagens continua dominando o tempo de resposta.

## Cobertura e falhas

Mapa rastreável: `CI_S1_I29_I30_SCENARIO_MAP_20261025.json`, com 108 IDs unitários,
225 descrições E2E e 20 alvos de sintaxe. Logs dos três modos nas duas rodadas
contêm todos os 108 IDs unitários esperados; no controle há 93 repetições.
I29 preserva 105/105 cenários; I30 preserva 120/120.

O novo verificador exige cada descrição E2E exata uma vez e o marcador final,
antes de aprovar. Sua primeira descrição inclui o número de migrations e é
calculada dos mesmos runners originais. Também reprova teste unitário vazio,
falha, skip ou contagem incompleta da suíte descoberta. Os scripts e testes
originais, migrations e código de domínio estão inalterados.

Nos logs publicados dos controles e serial, GitHub mascara a expressão
`Bearer independente` no cenário 36 de cada E2E. A comparação externa validou
225 IDs, 223 descrições exatas e as duas descrições com essa normalização
explícita. O candidato validou todas as 225 descrições completas dentro dos
runners, antes da publicação. Não se contou o marcador final como substituto
dos cenários individuais.

Validação local: 108/108 unitários nos shards reais, além de um smoke I30 de
15/15; Bash, YAML e sintaxe dos 20 arquivos verificados. Testes sintéticos do
validador aceitaram as duas listas completas e rejeitaram oito mutações (caso
faltante, duplicado, extra ou total final ausente). Seis ensaios sintéticos de
orquestração cobriram sucesso, falha unitária, startup, E2E, limpeza e marcador
faltante, verificando propagação de erro e limpeza. Isso não substitui E2E real;
os E2Es reais foram executados nos oito runs citados.

A primeira tentativa local I30 encontrou bloqueio de sockets no sandbox e rodou
zero testes; foi registrada como bloqueio e repetida com acesso de loopback,
passando. O acesso Git também foi recuperado; checkout, árvore e 439 blobs
foram conferidos com os SHAs do GitHub. Não houve build da aplicação.

## Evidências e limites

`evidence/P1_I29_I30_20261025.json` e `P2_I29_I30_20261025.json` preservam IDs dos
runs/jobs, SHA, timestamps, passos e trechos relevantes dos logs. O resumo
calculado está em `evidence/SUMMARY_I29_I30_20261025.json`; os testes locais em
`evidence/LOCAL_I29_I30_20261025.json`.

`evidence/ARTIFACTS_I29_I30_20261025.json` registra IDs, digest e metadados dos
quatro artefatos de IDs e cenários dos candidatos, disponíveis nos runs por sete
dias. Nenhum `.env`, certificado, chave ou banco foi incluído. O conector gerou
ZIPs, mas o download local pelo domínio de arquivos recebeu 403 da política de
rede; os ZIPs não foram reabertos localmente. As conclusões usam logs acessíveis
e os gates executados nos runners. Os JSONs de evidência persistem após a
expiração dos artefatos temporários.

## Decisão e próximos limites

Candidato experimental com economia repetida e cobertura preservada no escopo
I29/I30, mantendo feedback próximo do controle e muito menor que o serial.
**Não declarar atendido um requisito de acelerar consistentemente o controle.**
Para reduzir mais o tempo, o próximo alvo é startup/download das duas stacks;
qualquer cache ou mudança de serviços precisa de novo A/B e verificação de
isolamento. Não compartilhar banco nem cortar verificações de segurança.

Nenhum workflow oficial, controle ou serial foi alterado/desativado. Não houve
escrita em branches oficiais, merge, deploy ou reconstrução do produto. Promoção
continua condicionada ao aceite do owner S1 e verificação dos checks obrigatórios.
Rollback: reverter apenas os commits experimentais, mantendo os workflows
oficiais disponíveis.

Recalcular e verificar cada rodada: `python3 docs/ci/evidence/verify_i29_i30.py
docs/ci/evidence/P1_I29_I30_20261025.json` (trocar P1 por P2 na repetição).
