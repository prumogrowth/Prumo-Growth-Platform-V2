# I86 manual — implementação e bloqueio de validação física

28/10/2026, America/Sao_Paulo. **LAB_BLOCKED**.
Código candidato não equivale a código certificado.

## Estado recuperado e isolamento

Repositório 0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA.
I86 recuperada em dbf49ab19b73766d60678c4ce6f7dea56cd66c9b,
código c1b66cb009a56e2049148f118395ab5cb98dc4ea, CI40731718955 SUCCESS,
PR49 Draft. I85 preservada em3cab3d57619cc1157698a08ac26f34e0c363f6dd.

A branch exp/s1-i86-manual-director-20261028 não existia antes da escrita;
foi criada exatamente de dbf49ab, sem force, merge, rebase ou fonte Meta.
Worktree próprio /workspace/prumo-i86-manual.
[PR Draft51](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/51)
tem como base a branch I86 histórica, ainda no checkpoint informado.

Somente integration/i86/**, docs/contratos/i86_authority/** e
.github/workflows/exp-s1-i86-manual-director.yml foram editados/criados.
O checker fixa base/tree, todos os commits e pendências locais, inclusive
edit/revert, renomes, remoções, ignorados e modos perigosos. O workflow anterior
não integra a nova allowlist. Não foi aberto recurso de outra conversa.

## Política efetivamente ratificada

A instrução do responsável estabelece que somente operador humano autorizado,
em ambiente administrativo restrito do Supabase, pode nomear, retirar, modificar
ou recuperar autoridade. Diretoria comum, Gerência, Consultoria, JWT, metadata,
service_role, Edge, MCP e IA não são autorização organizacional.

DECISOES.json reclassifica D01–D05: manual exclusivo e evidência do ato ratificados;
nominalidade do operador, custódia/evidência operacionais e continuidade específica
continuam sem definição/homologação. Quórum, segunda aprovação, prazo e política
emergencial não foram inventados nem tornados pré-requisitos implícitos.
Vários Diretores são permitidos; não existe limite global implementado.

O contrato manual revisão2 prevalece sobre a interpretação histórica de
pendência universal das decisões. O observador v1 e suas respostas continuam
compatíveis e sem poder de aprovação.

## Código implementado

| Arquivo | Efeito |
| --- | --- |
| integration/i86/manual/procedure.sql | Schema privado, funções INVOKER, APPOINT/REVOKE/REACTIVATE, CAS, ledger/auditoria imutáveis, reconciliação |
| integration/i86/manual/policy.py | Política MANUAL_PRIVILEGED_ONLY, aplicação/MCP/IA desabilitados, continuidade ainda não escolhida |
| integration/i86/manual/test_policy.py | Quatro provas de modelo, sem inferir quórum/limite ou habilitar aplicação |
| integration/i86/manual/lab_support.py | Apoio exclusivamente de testes em VM descartável; Auth sintético gerado em memória, contexto técnico verificado |
| integration/i86/manual/crash_probe.py | Processo de teste para SIGKILL antes/depois do COMMIT, sem parâmetros sensíveis em argv |
| integration/i86/manual/test_real.py |31 cenários reais planejados, incluindo negativas, múltiplos Diretores, falhas e regressões das seis portas |
| integration/i86/scope.py e test_scope.py | Nova base/branch/workflow exatos e13 testes adversariais, sem relaxar a fiscalização |
| Novo workflow exclusivo | Gate local/CI e três jobs físicos separados: I85, observador I86 e fronteira manual |

Não há backend/MCP/CLI operacional que nomeie. O SQL exige contexto já
privilegiado, não o concede a quem chamou. Nenhum papel, membership, grant
herdado, owner NOLOGIN, migration oficial ou SECURITY DEFINER novo foi criado.
Essas são propriedades do código; sua efetividade no PG17 ainda precisa da CI.

## Comportamento projetado, ainda sem prova física desta revisão

O alvo é UUID Auth existente. APPOINT aceita identidade ainda não vinculada;
insere ator/equipe/competência em um COMMIT. Outros cargos ou ator incompleto
são recusados, sem reclassificar chefias/carteiras por inferência.
REVOKE mantém classificação histórica, inativa competência e retira sessões.
REACTIVATE exige novo ato explícito, sem recriar sessões antigas ou reabrir I85.
A retirada negativa permanece possível para Auth banido; concessões positivas
o recusam, sem desbanir ou alterar o usuário.

Referências/digest de evidência e operador são vinculados ao ato. A auditoria
grava SQL session/effective principal e horário, não senha/token/PII textual.
Advisory locks por ato/alvo protegem idempotência e atores ausentes; revogação
segue sessões→ator→equipe→competência. Auth.users usa NOWAIT para evitar espera
inversa com GoTrue. Constraints diferidas permanecem ativas.

O retorno da função é explicitamente provisório: caller_commit_required=true.
Reconciliação apenas lê. Visibilidade MVCC READ COMMITTED e xid8 distinguem
registro confirmado de registro próprio ainda não confirmado. Estado alterado
não é restaurado por replay; ausência/COMMIT incerto não disparam retry automático.

SQL principal, digest fornecido e referências não comprovam presença humana.
Um programa com a mesma credencial postgres pode executar o mesmo SQL; RLS não
é barreira contra infraestrutura comprometida. Custódia fora de IA/MCP,
autorização nominal e origem da evidência permanecem controles externos.
Os testes positivos são simulações sintéticas autorizadas, não nomeações humanas.

## Validação local executada

- 13 testes de escopo PASS, incluindo proteção do workflow I86 anterior.
- 5 testes históricos de DTO/modelo e4 de política manual PASS.
- Os22 passaram também com Python -O, sem depender de assert de produção.
- 288 unidades backend PASS.
- AST dos módulos Python e parse YAML do novo workflow PASS.
- Checker sobre as alterações reais PASS, sem edição protegida.

O ambiente local não possui PostgreSQL, Supabase CLI, psycopg ou parser SQL.
O proxy shell não está acessível. Nenhum Docker/Supabase local foi iniciado:
não houve como usar laboratório físico próprio com a segurança exigida.
Não foram usados mocks para atribuir PASS a SQL/GoTrue/Edge.

## CI efetivamente observada

Código candidato: **96a7c5ff054ec3be9d15237803914ac247292e61**.
Tree bd8379a5e708f15f89c951492a3c9299e2e6ddbb.
[CI40774122852](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40774122852),
tentativas1 e2, ambas FAILURE antes de qualquer step/runner.

| Tentativa | Job inicial | Runner | Steps | Jobs físicos |
| --- | --- | --- | --- | --- |
|1 |123118796369 scope-and-model FAILURE | não atribuído |0 | três SKIPPED |
|2 |123119407534 scope-and-model FAILURE | não atribuído |0 | três SKIPPED |

Foi feita somente uma repetição do job falho para descartar falha transitória;
o resultado persistiu e não houve loop de novas execuções. Nenhum caso físico
foi executado. Não há artifacts no run; logs de job retornaram404/BlobNotFound.
Os detalhes de check-run/annotations não estão disponíveis pelo conector usado;
a página pública também não pôde ser lida. A causa subjacente não é confirmada,
portanto não se atribui a quota/billing/configuração por suposição.

EVIDENCIA_CI_BLOQUEADA.json persiste os metadados selecionados das duas tentativas.
Esse arquivo é evidência documental obtida pela API, não artifact de teste.
MATRIZ_VALIDACAO.json marca cada um dos31 casos NOT_TESTED/BLOCKED_NO_RUNNER.
CI do checker, catálogo efetivo, ACL/RLS, transações, concorrência, Auth/Edge,
MCP técnico simulado e descarte físico permanecem sem nova comprovação.

## Regressões, I85 e Meta

Os códigos I85 e canônicos S0/S1, backend, migrations, Edge, Frontend, contratos
Meta e integration/s0_meta_ingress não foram alterados. O bootstrap I85 não é
chamado pelo instrumento positivo: os testes criam apenas fixtures Auth via
transporte já existente. Um job independente preserva a jornada I85 original;
outro reexecuta o observador I86. Nesta CI ficaram SKIPPED, portanto não são
declarados aprovados. Os baselines anteriores mantêm seu alcance histórico.

Não há dependência de webhook, M2M, ACK, recibo, template, envio ou outra branch.
Nenhum conflito exigiu alteração compartilhada. Se a execução posterior revelar
essa necessidade, a mudança deverá ser encaminhada sem executá-la aqui.

## Limites e recomendação

**LAB_BLOCKED**: falta executar/inspecionar as provas físicas e CI final.
Não existe código SQL certificado nesta continuidade, apesar de código e testes
estarem preparados. A operação hospedada continua bloqueada também por identidade/
custódia do operador, evidência externa e homologação do provisionamento.
A substituição composta e conversão de cargos existentes não são implementadas.

Próxima ação concreta da orquestração: verificar a falha de inicialização de
runner na interface administrativa do GitHub, sem mudar o código para mascará-la;
reexecutar o workflow nesta branch. Só após os quatro jobs concluídos, inspeção
de logs/artifacts,31 casos novos, regressões herdadas e descarte efetivo caberá
recomendação LAB_CLOSED/LAB_CONDITIONAL conforme as provas.

Documentação posterior ao candidato é separada e sem alteração de runtime; seu
SHA fica no histórico/PR. Não houve merge, deploy, Supabase hospedado,
credencial produtiva, usuários/Diretores reais ou integração com a frente Meta.
