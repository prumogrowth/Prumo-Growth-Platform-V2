# I85 — auditoria independente, saneamento e recomendação laboratorial

28/10/2026, America/Sao_Paulo. Resultado da auditoria: **I85_LAB_CLOSED**, exclusivamente no escopo laboratorial descrito. CI e artefatos finais concluídos e inspecionados. Não é I86 nem autorização de produção.

## A. Estado recuperado

Repositório `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`, PR Draft #42,
branch `exp/s0-s1-i85-bootstrap-auth-diretor-20261028`.
HEAD inicial remoto confirmado antes de escrever:
`0d3beb4f9e0ee32ce088c591125b9d61ef43173f`.
Código anterior `840b2db7299d024c03ced2e5120b241a23046a0e`,
[CI40664481472 SUCCESS](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40664481472), cinco jobs.
Foram recuperados os 15 commits entre I84 e esse HEAD, os sete arquivos do delta,
PR/CI/checkpoint/contrato e código integral bootstrap/CLI/jornada/workflow.
Nenhum avanço remoto posterior foi encontrado antes da primeira escrita.

Base I84 PR #40: código `6852a4f509df8466e35da46ba995a4ac2ed5e1f7`,
checkpoint `3bf948fe67d439d93f6c848300ea2e5e053311ed`, CI40622136488 SUCCESS.
Contratos/relatórios I79–I84 e HTTP candidato prumo.admin.v1 considerados; as
fontes S1 reutilizadas são fixadas em `8780b576aa18bd3983c063339e2e42d2452af22c`.
A aprovação anterior não foi adotada como prova de fechamento: era uma jornada
única de 13 pontos e não cobria SIGKILL ou candidatos iniciais distintos.

## B. Achados confirmados e decisões

| ID | Gravidade / impacto | Evidência e conclusão |
| --- | --- | --- |
| F01 | ALTA: privilégio de instalação disponível no runtime | O CLI 2.84.2 injeta SUPABASE_SERVICE_ROLE_KEY, SUPABASE_DB_URL e SUPABASE_INTERNAL_JWT_SECRET; o template encaminha as duas primeiras ao user worker. Logo, não usar esses valores em runtime.ts não significa não recebê-los. Fonte oficial fixada e prova física de ausência no perfil I85; afirmações anteriores retificadas. |
| F02 | ALTA: exclusividade/confiabilidade do journal dependia do chamador | Só a CLI tinha flock; métodos Python suportados operavam estado previamente carregado. Chamadas independentes podiam ultrapassar a exclusividade ou escrever snapshot obsoleto. Todas as operações públicas suportadas agora travam, releem e conferem a identidade física; instância antiga não retargeta nova stack. |
| F03 | MÉDIA: .next bloqueia gravação/recuperação | Reproduzido localmente com SIGKILL real entre fsync e replace de boundary.save; arquivo original e .next permanecem, próxima escrita gera FileExistsError. I84 não foi editada diretamente: I85 usa escrita própria e recuperação explícita, retendo os bytes como evidência. |
| F04 | ALTA: init/dispose interrompidos sem retomada comprovável | Init podia deixar diretório/state sem secrets; dispose apagava secrets/state antes do restante. Nascimento físico, recuperação de init, intenção de descarte e diretório .disposing permitem retomada sem repetir Auth/SQL. Provas de SIGKILL independentes. |
| F05 | ALTA: ordem de locks invertida na revogação | Versão anterior tomava competência antes de DELETE auth.sessions. I79/I80 tomam sessão antes da competência. O padrão antigo foi reproduzido fisicamente com deadlock 40P01 e rollback; correção segue sessões→ator→equipe→competência, com trava Auth curta impedindo novas sessões durante o corte. |
| F06 | ALTA: REVOKE_UNKNOWN podia manter autoridade sem comando de retirada retomável | Reconcile só confirma estado; se a transação não confirmou, revoke recusava a fase. Revoke agora pode ser explicitamente retomada em UNKNOWN e repetida em REVOKED: somente redução de autoridade/retirada de sessões, sem reativação. |
| F07 | ALTA: dispose confiava na fase local | Journal NONE/REVOKED divergente do SQL podia ser apagado. Status, reparo e descarte agora confrontam a autoridade canônica; divergência mantém bloqueio e evidência. |
| F08 | MÉDIA: diagnóstico de CLI podia ecoar argumento | Executado o __main__ original, isoladamente, com marcador fictício: saída 2, marcador no stderr. Não foi usado segredo real. Parser atual retorna código fixo; testes de erro também não ecoam material detectado. |
| F09 | MÉDIA: validação de integridade incompleta | Versão inicial verificava somente version/identities. Journal v2 valida forma, fases, UUIDs/labels, aprovação, vínculo físico e correspondência de segredos; JSON duplicado/não finito, permissões e links são recusados. |
| F10 | ALTA: opt-in tardio/downgrade do perfil | Perfil legado servido antes de I85 não pode ser aceito no bootstrap. Nascimento/tombstone da mesma stack exige perfil restrito mesmo se opt-in for retirado. Negativa e reprodução física dos nomes privilegiados no perfil antigo são parte da suíte final. |

Rastreabilidade dos achados para provas independentes:

| Achado | Código/prova correspondente |
| --- | --- |
| F01/F10 | `edge_profile.py`, `runtime_main/source.json`; resistência 050 e 052, inspeção física de nomes Env; fonte [CLI v2.84.2 serve.go](https://github.com/supabase/cli/blob/v2.84.2/internal/functions/serve/serve.go) e [main.ts](https://github.com/supabase/cli/blob/v2.84.2/internal/functions/serve/templates/main.ts). |
| F02 | Decorador `serialized`, `owned` e validação do caminho; resistência 014, 021, 030, 031 e 080. Testes de aprovação pública/custódia são distintos da defesa adicional SQL com dois candidatos. |
| F03/F09 | `storage.py` e `recover_journal`; sete unidades de filesystem; resistência 024, 032, 070 e 071. A reprodução da escrita herdada usa filho real morto por SIGKILL, retendo os dois conteúdos divergentes. |
| F04 | `init`, nascimento físico e `dispose`; resistência 000/001 e 060/061/062. Interrupções incompletas sem proveniência continuam recusadas. |
| F05 | `revoke_director`; 044 reproduz o padrão anterior com SQLSTATE 40P01 e rollback; 045 exige HTTP real bloqueado, drenagem antes do corte e recusa após o corte. |
| F06 | 040/041/042: rollback e confirmação de COMMIT/sessões; 043: JWT anterior, refresh e login posterior sem recuperação administrativa. |
| F07 | `_checked_status`, `_disposal_proof`; 031 e 070 recusam exclusão de journal NONE quando SQL prova autoridade. |
| F08 | `__main__.py` usa Parser I84 sem eco; `test_cli_never_echoes_unknown_arguments_or_choices`. Original executado com marcador sintético, sem segredos, exit2 e eco no stderr; SHA256 do arquivo original `f163374bdf96bab1e141f73034b3c0cd870ad1f9017b31387faa8c562e9ac2fd`. |

A exposição F01 não é prova de exploração remota/RCE: o código I82 não fazia uso
dessas variáveis, mas a fronteira de privilégio declarada era falsa. Correção
remove as credenciais do container desde a criação; não concede superuser ou
contorna SQL/RLS. O uso administrativo cliente da service_role fica no host
instalador; Auth/Kong são infraestrutura confiável emissora/validadora de chaves.

Hipóteses descartadas: cargo Diretor/estado ativo isolados não concedem a
administração I79/I80; identidades Auth/metadados não concedem competência;
CREATE_UNKNOWN não precisa de segundo POST para reconciliar; os seis comandos
podem funcionar no Runtime oficial sem credenciais de instalação. As provas
finais e as limitações constam na matriz, sem inferir produção.

## C. Correções e impacto sobre contratos anteriores

- `integration/i85/bootstrap.py`: comandos serializados, binding estável por
  instância, journal v2, verificação canônica, aprovação recuperada pendente,
  transação de grant extraída sem nova porta pública, ordem de revogação,
  retomada negativa, descarte em duas fases e abandono após lab destruído.
- `integration/i85/storage.py`: arquivos 0600/diretórios 0700, fsync, rename,
  nomes temporários únicos, leitura estrita, hardlinks/symlinks recusados,
  retenção de falha, snapshots privados e recuperação explícita. Não é cofre
  substituto da I83; não contém material produtivo nem trilha WORM.
- `integration/i85/__main__.py`: parser sem eco, comandos adicionais de recuperação
  e abandono, sem endpoint HTTP ou identidade escolhida pelo cliente.
- `integration/i85/edge_profile.py`, `runtime_main/{index.ts,source.json,LICENSE}`:
  mesmo Runtime v1.73.0 e template oficial CLI v2.84.2 não modificado, fonte e
  hash registrados. Fonte I82 somente leitura, usuário do host sem capacidades
  adicionais, sem socket Docker/custódia montados; Env explicitamente restrito.
  Acesso ao Docker apenas pelo socket Unix existente do instalador, não listener.
- `local_admin/worker.py` **somente na branch I85**: seleção/validação/retirada
  do perfil restrito. Sem marca I85 e sem opt-in, a regressão I84 preserva o
  caminho anterior. A branch I84 certificada não foi modificada. Ver
  [impacto registrado antes da alteração](IMPACTO_DA_AUDITORIA_EM_COMPONENTES_ANTERIORES.md).
- `test_filesystem.py`, `fault_driver.py`, `test_resistance.py`, `test_journey.py`
  e workflow I85: resistência real e captura segura, mantendo a jornada anterior.
  Driver de falhas é ferramenta de teste do instalador, nunca montada na Edge.
- Contrato/checkpoint históricos foram identificados como históricos; runbook,
  matriz e relatório reconciliam o escopo. Nenhuma regra comercial, SQL de
  negócio, grant, tabela, função/owner I79–I83 ou arquivo TypeScript I82 alterado.

## D. Matriz de validação

A matriz estruturada contém um registro por requisito/prova, cenário, resultado,
localização da evidência e limite. Uma recusa esperada pode ser uma prova PASS de
comportamento **operacional BLOCKED**; não equivale a uma função recuperada.
A jornada E2E continua sendo **um teste com 13 pontos**, não 13 testes.
A suíte de resistência usa uma stack inteiramente nova por teste. Não apaga
histórico de equipe nem desabilita triggers para reutilizar banco.

Estados possíveis: PASS, FAIL, BLOCKED, NOT_TESTED. Na primeira rodada:
26/27 casos reais PASS; teste 045 FAIL por instrumentação incorreta de contenção,
não execução demonstrada da drenagem. O teste bloqueava atores, mas INVENTORY
bloqueia equipe. O alvo foi corrigido, mantendo as exigências de espera, ausência
de deadlock, COMMIT prévio e recusa posterior. Resultados parciais não fecharam I85.
A revisão final inclui casos de criação concorrente e opt-in tardio, além de
captura de material órfão e observações explícitas de refresh.

Provas sem mock de resultado: GoTrue/PostgreSQL/PostgREST/Edge são reais. Os
wrappers determinísticos somente param um processo em pontos de I/O/SQL reais;
o controlador aplica SIGKILL e verifica persistência/rollback. Há unidades locais
de falha de syscall, identificadas como tais, que não substituem integração.
No teste SQL com dois candidatos distintos, o helper privado de transação é
chamado por dois processos de instalação para testar a defesa SQL adicional;
não se finge que uma segunda custódia pública de bootstrap é suportada. A
exclusividade normal é testada separadamente pela interface pública.

## E. Certificação técnica e histórico de execuções

Código inicial auditado: 0d3beb4/840b2db. Correções iniciais:
`f53c9f149aeab969a9d8cfbad8787dacd6838368` e
`1b328df5e24f897361af994e4a6fbd89789df8d1`.
[CI40675928138](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40675928138):
**FAIL**, cinco jobs aprovados e resistência 26/27, sem testes ignorados.
Jornada única I85/13 pontos sob perfil restrito passou em 21,861s;
I84/CFI/S1 e custódia herdadas passaram. Artefato de resistência inicial
12812166249, SHA256 ZIP
`505cc7d7bc3258059a01baf13cadb18b994e49e8cabb6ff3644ac2778500ab98`.
Não é certificado global do código final.

Código certificado nesta revisão laboratorial:
`062c90ffbe2b223c1d6bb08f614e7a1b6a898201`, tree
`ba8dc0e5f3ff5847c12f56be7a55b59e87fb48b5`.
[CI40680048140](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40680048140):
**SUCCESS, seis jobs**, concluída em 28/10/2026 08:56:16 BRT (11:56:16 UTC).

| Job | ID | Resultado |
| --- | --- | --- |
| s1-pinned-i54-i78-regressions | [122788160038](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40680048140/job/122788160038) | SUCCESS |
| credential-logging-preflight | [122788160545](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40680048140/job/122788160545) | SUCCESS |
| real-history-and-cfi | [122789075496](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40680048140/job/122789075496) | SUCCESS |
| local-operation | [122789075525](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40680048140/job/122789075525) | SUCCESS |
| i85-real-auth-bootstrap | [122789075586](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40680048140/job/122789075586) | SUCCESS |
| i85-real-resistance | [122789075598](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40680048140/job/122789075598) | SUCCESS |

Resistência real: **29/29**, **1601,005s**, zero skips, zero NOT_TESTED entre
os 29 casos planejados. Os 29 registros de limpeza comprovam catálogo igual,
recursos ausentes e senhas privadas retiradas. O caso 045 agora comprovou a
drenagem HTTP que a primeira instrumentação não alcançou. O padrão anterior
reproduziu 40P01; o corrigido não deixou deadlock ou autoridade duplicada.
Observações reais: refresh após revogação **REJECTED**; novo login Auth
**AUTHENTICATED_ADMIN_DENIED**; perfil legado tinha nomes de variáveis
privilegiadas, perfil I85 não os tem e não volta ao legado ao remover o opt-in.

Filesystem/CLI: 7/7 normal e 7/7 Python -O; boundary I84: 9/9 em ambos.
Jornada I85: um teste, 13 pontos, 24,932s. I84: um teste, 16 pontos,
96,407s e descarte DISCARDED físico. Backend288, Deno14 e codec1 passaram.
CFI32 + registro F02 24, histórico19 em dois perfis, G1 36, I79/G1 62,
I80 33, I81 14, I82 HTTP20 e I83 35 passaram nos estágios herdados.
A repetição deliberada I79/I80 após cada instalação preserva os respectivos
contratos; não são somadas como novas funcionalidades ou gates comerciais.

Todos os 11 ZIPs finais foram baixados e inspecionados; hashes de ZIP/membros
estão na matriz versionada. Inventários estáticos S1 I46/I48/I75B não foram
confundidos com grants efetivos ou conclusão de G3/F02. Os artefatos têm retenção
original de 14 dias; matriz preserva resultados, observações, limpeza e hashes,
sem copiar journals, segredos, dumps ou logs brutos.

| Evidência principal | Artifact ID | SHA256 do ZIP |
| --- | --- | --- |
| I85 jornada | 12811789480 | `393b8ede1f002f62f3e7807571a2de04fb32a3b1903bdca722bbb7bbebbb3af1` |
| I84 operação | 12811714884 | `e55cc32151135915af6d15574461d7f3586eff43248fcc1103e6018411841ca8` |
| I81 catálogo | 12812353340 | `fb38e5477eb69e630a6e7dcbfd04f87691532b6d2bbf51bdc5719bda530def38` |
| I82 catálogo/diagnóstico saneado | 12812248747 | `91916e9d368eba6ebe4a19ccbc740ac325867ba5b605b7160e483fce5a9b50cc` |
| I83 catálogo/custódia | 12812583893 | `8931bf47f2c960cc17bbf59ae4975963143fbda07472c0933ef846da8632ddbb` |
| I85 resistência | 12813622741 | `809c56d574c8a398138cc381b34e24e0b4263e0bd9f4564954b701c297c97858` |

JSON de resistência SHA256
`14910b4b603dd50b29be92a63a2b94af3c95c285d73c6be91607e1ccd3b37f40`.
I83 final CLEANED: zero chave ativa/secreta, login SQL desabilitado, senha NULL,
zero sessões SQL, env/container sensível retirados e logs sem valores detectados.
I85 não exportou segredos; a jornada acusa zero correspondências nos logs.

Commit documental do contrato/runbook/matriz/checkpoint: `f00dfaab50301ccdd75db8dab9aa561a55251a99`.
Este relatório vem em commit documental subsequente, identificado no histórico do
arquivo e no PR #42. `[skip ci]` limita-se a esses commits de documentação após
o teste: o código/workflow/runtime permanecem exatamente no SHA certificado acima.

## F. Integridade do projeto e limites

As únicas atualizações de ref desta auditoria são na branch I85, com expected_sha
sem force. PR #42 permanece Draft e não merged; Issue #23 permanece aberta.
Refs originais rechecadas: I84 `3bf948fe67d439d93f6c848300ea2e5e053311ed`, S1 `8780b576aa18bd3983c063339e2e42d2452af22c`; main remota e origin/main local coincidem em `dace737ab7afb7ae3f5a3a6f5cb522e6def8b43a`. Worktree I84 permanece limpa. O diff usa I84 3bf948f como base conhecida.
Não houve merge, deploy, alteração de main, Supabase hospedado, credenciais ou
usuários reais, chamadas comerciais, F02 ou Frontend. I86 não foi iniciada.

O perfil legado I82–I84 não passou a ter isolamento de credenciais só porque a
aplicação não as usa. A retificação F01 precisa acompanhar futuras integrações;
esta auditoria certificará apenas o perfil I85 selecionado e comprovado nesta
branch, sem reescrever a branch histórica ou homologar implantação produtiva.

Journals/host/Docker/instalador são confiáveis, não defesa contra root malicioso.
Não há teste destrutivo local nesta máquina do Codex: CLI Supabase não está disponível e a rede shell está restrita; as provas reais ocorrem nos runners CI com stacks descartáveis, não em Supabase hospedado. Unidades filesystem/CLI (16, também com Python -O) e backend (288) foram executadas localmente. Falha de energia/daemon/disco em toda janela possível não é exaustivamente homologada. Estado sem nascimento físico nem prova de stack nova sem mutações, ou sem bytes completos/proveniência comprováveis, bloqueia retomada; o runbook define intervenção/descarte, não
reinserção por inferência. Evidência incerta é retida explicitamente. As chaves JWT de desenvolvimento do CLI não são custódia produtiva nem prova de exclusividade criptográfica entre projetos: a recusa de token antigo em nova stack depende também de sessão/competência canônicas e do vínculo físico demonstrado no caso 080. Segredos
são retirados sem promessa de apagamento forense de RAM/WAL/cache/backups.

### Privilégios antes e depois

Não há DDL de negócio nem concessão adicional na correção I85. Os snapshots I81,
I82 e I83 `after`/`final` foram comparados como objetos JSON completos: iguais
em cada etapa. As diferenças `before`→`after` pertencem às instalações herdadas
I81/I82/I83, não são uma licença para normalizar qualquer divergência posterior.
Cada teste novo compara o catálogo preparado com o catálogo ao final, normalizando
**somente** `rolcanlogin` temporário de `prumo_s1_admin_edge_local` durante serviço.
Owners de domínio, validador e custodiante permanecem NOLOGIN, NOINHERIT,
NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOREPLICATION e NOBYPASSRLS.

| Responsabilidade | Antes da auditoria | Após a correção I85 |
| --- | --- | --- |
| Instalador local | Host com postgres/service_role, esperado para bootstrap sintético | Mesma autoridade confiável; nenhuma função SQL pública nova |
| Runtime Edge | Login/HMAC I83 **e** variáveis privilegiadas injetadas pelo CLI | Somente login/HMAC I83 e variáveis públicas/técnicas necessárias; credenciais de instalação ausentes |
| Diretor humano sintético | UUID Auth + equipe explícita + competência global ativa | Mesmas três condições, com journal/custódia/revogação endurecidos |
| Clientes anon/authenticated/service_role | Sem EXECUTE administrativo privado nem DML privado geral | Mesmas negativas preservadas pelos testes I81/I83; sem endpoint bootstrap |
| Executor I83 ao retirar laboratório | NOLOGIN, senha SQL retirada, nenhuma chave ativa/sessão | Mesmos resultados físicos no artefato12812583893 |

A trava curta de tabela `auth.sessions` na revogação usa capacidade de instalação
já existente. Não transfere essa capacidade à Edge ou ao Diretor e não deve ser
copiada como política de runtime hospedado sem homologação específica.

## G. Recomendação de fechamento

**I85_LAB_CLOSED** — as condições de fechamento **laboratorial** foram atendidas
pelo código acima e pela CI final inspecionada. UUID canônico, aprovação técnica
separada, ausência de autopromoção, resultado incerto conservador, falhas abruptas,
concorrência, revogação, custódia, descarte e regressões têm provas identificadas.
Não há pendência crítica não resolvida dentro desse escopo. Casos que não possuem
prova suficiente de retomada continuam operacionalmente BLOCKED, conforme a
matriz/runbook; isso é recusa segura demonstrada, não recuperação presumida.
Produção e nomeação de Diretor real permanecem fora de escopo e bloqueadas.

## H. Encaminhamento à orquestração

A I85 pode ser submetida à **avaliação final de fechamento pela orquestração**.
Não é necessária outra rodada corretiva para os requisitos laboratoriais
executados nesta auditoria. Priorizar na revisão F01/F10 (fronteira real do
instalador), F05 (ordem dos locks), recuperação de .next e exclusividade de
candidatos. Conferir a matriz por teste e os hashes, não apenas o ícone verde.
Não iniciar I86, não fazer merge ou nomear pessoa real. A orquestração mantém a
decisão posterior e independente sobre fechamento e eventual próxima missão.

Cargo/estado remanescentes após revogação são deliberadamente preservados conforme
I79: identidade/histórico organizacional não são competência global. Nenhuma
mudança automática para suspenso/desligado foi inventada. Bootstrap único recusa
nova nomeação inclusive após revogação; substituição ordinária de Diretor é
contrato separado. Revogar não bane a conta Auth: login posterior pode ser válido,
mas não pode recuperar administração; refresh/cache são confrontados pela sessão
canônica e pela competência em SQL. Detalhes e ações estão no runbook auditado.
