# I84 — relatório e evidências da operação local

27/10/2026, America/Sao_Paulo. PR Draft #40, base PR #38/I83 preservada.
Não houve merge, deploy, migração hospedada, dados reais ou chamada Meta/OpenAI.

## Desenvolvimento efetivo

CLI `python3 -m local_admin`, independente de unittest/harness, com inicialização
nova, preparação sem humanos, emissão dedicada, worker TypeScript/Deno separado,
status técnico, rotação/reinício, revogação, retirada, recuperação conservadora e
descarte verificado. O operador não importa cenários de teste para executá-los.
As dependências de catálogo usam os leitores de metadados I81/I83 existentes;
nenhuma criação de pessoas/casos ocorre em init/prepare/provision/serve/status.

O provisionador I83 continua sendo a única implementação de geração, SCRAM,
material HMAC, janela privada de logging, cofre, validade, rotação e retirada.
Do I79/I80 continuam todas as portas, estados e verificações de domínio. A Edge
HTTP `prumo.admin.v1` continua sendo TypeScript/Deno, não um servidor Python.
Owners, guards I46/I57/I61, RLS, sessão GoTrue, competência do Diretor, nonce,
CAS, idempotência, auditoria e constraints diferidas não foram substituídos.

Mudanças de arquivos:

- `local_admin/{boundary,environment,bootstrap,custody,worker,operation,__main__}.py`,
  `__init__.py`, `dependencies.json`: operador e manifesto das fontes certificadas.
- `integration/history/prepare_s1_profile.py`: exporta a verificação existente,
  sem alterar os bytes SQL; rejeição explícita inclusive com Python -O.
- `integration/i79/install_local.py`: exporta o construtor existente, mantendo
  a mesma adaptação I54 já certificada e validando a fonte sem assert removível.
- `integration/i82/gateway_local.py`: leitura/carga existente recebe ambiente
  opcional, stderr privado e timeout; consumidor anterior preserva o default.
- `integration/i84/test_boundary.py`, `test_journey.py`, `capture.py`: proteções físicas e jornada
  real. Somente o módulo de teste cria humanos sintéticos e faz bootstrap local.
- `.github/workflows/exp-s0-s1-i84-local-operation.yml`: stacks separadas para
  regressões anteriores e operação autônoma. Arquiva só JSON de metadados/provas.
- Documentação I84 e checkpoint correspondente.

Nenhuma função SQL de negócio, migration hospedada, regra crítica em TypeScript,
novo login/cofre ou concessão comercial foi adicionada. Nenhuma branch S1,
Frontend, Meta ou F02 foi alterada.

## Certificação

Execução inicial: commit `e233491af8136b74b4115839aa468049003dd6db`,
[CI40618687010 SUCCESS](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40618687010).
Todos os quatro jobs passaram; jornada independente de 12 provas em 51,381s.
Artefato inicial `12786283033`, ZIP SHA256
`ffadb5b8a4d465d6099b2470a76f3f92f29008df49030371a772682a81d9f379`.

Revisão intermediária `434f3ec70f4837b9312ca30d6e1a384224231fad`, também aprovada nos quatro jobs.
[CI40620010744](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40620010744)
SUCCESS na revisão intermediária. O candidato final abaixo inclui a restrição
de rede local descoberta na revisão do CLI.
O job operacional `122592164967` já passou: jornada com 15 provas em 104,215s,
8 testes físicos em modo normal e os mesmos 8 com -O.

Artefato operacional `12787166249` (14 dias), ZIP SHA256:
`1d9fab494c44410985f2941b5552f616e13cff0934c3feff4849407904dd1d17`.
Conteúdo permitido:

- `prumo_i84_catalog_initial.json`, SHA256
  `37e6fa07cf033c0e57d9f8bf5d71abdb882fc85510e0722503425a449e2eac03`.
- `prumo_i84_catalog.json`, SHA256
  `0886c423043370b29ad0a52945fe3037410c0939f4b41965f3aef013acbd02a6`.
- `prumo_i84_journey.json`, SHA256
  `f9a3a7637a65ec65c995a65787750bb7e38606bcf24f90b9d0ad838ce80d8d03`.

O comprovante da jornada completa tem generation=4, material_removed=true,
resources_absent=true, retirement_verified=true, catalog_equal=true e
secret_matches=0. A segunda stack foi interrompida após duas dependências SQL,
antes de instalar I83 ou emitir material; seu partial_cleanup tem
retirement_verified=false porque **não existia credencial I83 a retirar**,
material_removed=true e resources_absent=true. Isso não substitui o comprovante
positivo de retirada do primeiro ambiente completo.


Revisão de rede `7d6b621f75f951b66fd7e76af02092b7c9478cab`,
[CI40621246678](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40621246678),
job operacional `122596285186` aprovado, 16 provas em 104,765s.
A execução global foi cancelada automaticamente pela concorrência após a
publicação da revisão de diagnósticos; não conta como certificação global.
Certificação final na revisão seguinte, com diagnósticos de ensaio protegidos.

A revisão de fonte do CLI fixado confirmou o aviso literal
`All services bind to 0.0.0.0 (network-accessible, not just localhost)` em
[internal/start/start.go v2.84.2](https://github.com/supabase/cli/blob/v2.84.2/internal/start/start.go).
O helper Docker preserva rede preexistente:
[internal/utils/docker.go](https://github.com/supabase/cli/blob/v2.84.2/internal/utils/docker.go).
A correção I84 cria somente sua bridge privada com default host_binding_ipv4
127.0.0.1 e confere bindings efetivos de DB/Kong, não apenas URLs de cliente.
Registra ID da rede, rejeita substituição ou bind público e retira rede residual
somente por ID reconhecido, após confirmar ausência de containers/volumes.
Não altera defaults globais do daemon, firewall ou infraestrutura hospedada.

**Código certificado `6852a4f509df8466e35da46ba995a4ac2ed5e1f7`**,
[CI40622136488](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40622136488),
**SUCCESS nos quatro jobs**: preflight `122598842822`, S1 nativa
`122598843140`, regressões reais `122599550782`, operador `122599550828`.
16 pontos na jornada real, 121,974s; 9 unidades em 0,079s e mesmas 9 com -O em
0,081s. Todas as regressões pertinentes concluíram com sucesso.
A revisão final protege também os diagnósticos de falha da própria suíte: a
asserção que detectar material não imprime o valor encontrado. Prova com marcador
sintético verifica isso; nenhuma credencial é usada como fixture dessa unidade.

Artefato **final** de operação `12788177118` (14 dias), SHA256 do ZIP:
`087ea6914405bc16203422ef9173073b2c0a25ae190b0e1bfd78dd992681c044`.
Os dois catálogos têm exatamente os hashes da revisão intermediária acima;
prova final `prumo_i84_journey.json`, SHA256
`95f6cca05cc6e8dfa699bd5c0ffaee613d573ffcbd0e5e9bd4e16dc80daf76b3`,
acrescenta network_loopback=true. Limpeza completa principal continua comprovada,
assim como o descarte da segunda instalação parcial, sem material I83 emitido.

A regressão final executou 20 HTTP I82 em 32,690s e 35 I83 dedicados
(20 HTTP + 15 credenciais) em 57,193s. Após I83: I79/G1 62/62,
I80 33/33 e I81 14/14; catálogos after=final, sem material ativo ou sessão.
288 unidades S0, 14 Deno, codec de sete vetores e regressão nativa I54–I78
aprovados. Não foram observadas falhas nem ResourceWarning nos logs finais de operação e regressão Edge.

Artefato de regressão I83 `12788003505`, SHA256 ZIP:
`190f251d51d65d71c4695b54451cd20849f87cc20e361b8a0d20bb757c01fb9f`.
Preflight privado `12788345663`, SHA256 ZIP:
`e6752a082e21d93b186fc872779ec17c40fbbf37f85059ba21758bf3c109830d`.
Os artefatos expiram em 14 dias; contratos, workflow, fontes e hashes persistem
no Git para repetição/verificação. Evidências são stacks locais dos runners,
sem Supabase hospedado.

## Matriz verificável

| Grupo | Evidência aprovada |
| --- | --- |
| Operador | 9 verificações físicas/diagnósticas, também com Python -O: opt-in, perms, symlink, caminhos, flock entre processos, erro sem eco, material ausente/inválido, projeto hospedado/fonte nova, detecção de segredo sem eco |
| Jornada I84 | Stack nova sem humanos; provisionamento; runtime dedicado; Diretor GoTrue e REGISTER real; rotação; mesma chave sem reaplicação; senha antiga recusada; reinício físico; revogação e worker antigo recusado; retirada; recuperação de pós-COMMIT; igualdade de catálogo; limpeza |
| Rede local | Prova física de publicação DB/Kong somente em loopback, ID/opção da bridge e descarte |
| Negativas adicionais | Arquivo/config divergente não dá readiness; nova inicialização após descarte; dependências SQL parcialmente instaladas; confirmação de encerramento perdida, com reconciliação sem DB |
| HTTP I82 | 20 métodos existentes, sem mudanças, além da repetição no perfil dedicado |
| Credenciais I83 | 35 métodos = 20 HTTP I82 + 15 negativos de credenciais reais; três recusas do instalador |
| I79/G1 | 62 métodos, incluindo as 36 regressões G1 sob cargos explícitos |
| I80 | 33 métodos, prévia/APPLY/CAS/concorrência/revogação/preservação |
| I81 | 14 métodos físicos, seis recusas de instalação e cutover, catálogos antes/depois/final |
| CFI/histórico | 56 métodos CFI/registro F02 e 19 por perfil de histórico, com GoTrue/PostgREST reais |
| Compatibilidade | 288 unitários S0, 14 Deno, codec Python/TypeScript com sete vetores, S1 nativa I54–I78 e unidades originais |

A unidade da jornada I84 é **um teste encadeado**, com pontos de prova nomeados;
não se apresenta cada assert como teste E2E independente. As falhas injetadas
interrompem somente escrita/controle local depois de operações reais. Não há
mock de autenticação, PostgreSQL, resultado HTTP ou regra de domínio. O ensaio
pós-COMMIT interrompe a gravação do env depois de emissão SQL efetiva; não se
apresenta como homologação de todas as falhas possíveis de rede/COMMIT.
A perda de resposta HTTP após COMMIT e reconciliação mantém o ensaio real I82.

## Ownership, grants e isolamento

Inventário físico final (escopo S0/S1; preparação reaplica somente definições
anteriores certificadas):

| Metadado | Base nova antes de preparar | Após preparar / após retirar |
| --- | ---: | ---: |
| Papéis do inventário | 4 | 12 |
| Memberships do inventário | 19 | 32 |
| Funções | 46 | 107 |
| Tabelas | 46 | 83 |
| Políticas RLS | 27 | 147 |
| Triggers | 11 | 57 |
| Constraints | 277 | 422 |

Bridges I79/I80 continuam SECURITY DEFINER com owner
`prumo_s1_admin_domain_local`. Portas assinadas permanecem SECURITY DEFINER com
owner `prumo_s0_g1_executor_local`; cofre continua RLS enabled e owner
`prumo_s1_edge_custodian_local`. Validador NOLOGIN I81 permanece separado.
Login Edge tem USAGE apenas public/prumo_private, sem CREATE, sem USAGE em Auth
ou schema signed-I20 e sem privilégios de dados nas tabelas inventariadas.
Essas capacidades não se ampliam no ciclo operacional.

Catálogo operacional pós-prepare/final da execução inicial, confirmado novamente:

12 papéis do escopo, 32 memberships, 107 funções, 83 tabelas,
147 políticas, 57 triggers e 422 constraints. Pós-prepare = após retirada.
Somente LOGIN do executor varia durante a emissão; chave/senha/validade não são
copiadas para o catálogo. Login dedicado tem exatamente EXECUTE nas duas portas
assinadas I79/I80, sem acesso de dados às tabelas de domínio/Auth/cofre e sem
membership executável em owners. Domínio/validador/custodiante permanecem NOLOGIN.

A diferença de 33 memberships da stack histórica I83 para 32 da operação é a
**ausência da fixture `prumo_gateway_ci`** criada pela suíte Auth/REST anterior;
o operador não instala essa fixture de teste. Não houve remoção de membership
comercial. As duas flags LOGIN diferentes no catálogo são a quarentena explícita
de `prumo_cfi01_pgtest_login` e `prumo_s1_signed_login_ci`: NOLOGIN/password NULL.
Defaults públicos CONNECT/TEMP permanecem, sem CREATE ou poder comercial novo.

O manifesto verifica 62 fontes locais e 27 arquivos S1 por hashes/commit. Não
aceita nova migration/fonte Edge não revisada ou seed adicional. Cache Deno
node_modules fica fora do manifesto de fontes; dependência é a já fixada no
lock I82. DDL metadata-only continua exigindo revisão I81/I82; deriva de
catálogo/fonte bloqueia execução, sem tentar conceder permissões reparadoras.

## Custódia e recuperação

Diretório temporário 0700 e env/journal 0600, NOFOLLOW, escrita exclusiva e replace;
journal fsync antes das alterações. Não há segredo em argv, status, resposta,
mensagem de erro, Git ou artefato permitido. Valores transitórios são comparados
em memória com logs próprios de DB/Auth/Kong/worker e com respostas do ensaio.
Preflight I83 prova a janela de logging antes da emissão.

Emissão com possível COMMIT deixa UNCERTAIN; recuperação somente retira material,
NOLOGIN/password NULL e sessões, sem emitir novamente ou reaplicar negócio.
Renovação exige ordem explícita posterior. Flock não é herdado pelo worker;
advisory lock/locks de chave continuam na I83. Processo só é retirado com PID,
starttime e container reconhecidos; readiness verifica configuração, container
em execução e resposta técnica, não autoridade humana.

Descarte conserva somente tombstone técnico e lock sem material. Credenciais e
logs privados são removidos, assim como containers, volumes e rede da stack.
Não se alega destruição forense de RAM/WAL/cache, imagens Docker ou backups
externos. Não arquivar diretório de custódia nem logs brutos.

## Limites e próxima execução

O operador Linux/Docker/checkout é confiável e de uso técnico local. Se o processo
morrer antes de registrar identidade suficiente dos recursos, se houver recurso
substituído/de terceiro ou drift Kong não reconciliável, a recuperação automática
fica bloqueada: não se adota nem apaga recurso por conveniência. O ensaio cobre
falhas parciais controladas; não certifica todos os pontos de crash/daemon.

Rotação exige retirada/reinício, sem zero downtime. TLS, custódia produtiva,
abuso distribuído, bootstrap Auth/Diretor, homologação e rollout continuam gates
separados. Revisão Frontend do HTTP I82 ainda necessária; nenhuma integração
visual aceita por esta execução. Hospedado/produção permanecem bloqueados.
F02 G01–G06 parciais/G07 pendente, sem nova auditoria ou autorização comercial.

Próxima execução segura: ensaiar e definir o bootstrap/recuperação Auth/Diretor
exclusivamente local e preparar o consumo administrativo do contrato I82 com a
revisão do Frontend. Não criar autoridade humana por inferência nem iniciar
migração hospedada como extensão desta certificação.
