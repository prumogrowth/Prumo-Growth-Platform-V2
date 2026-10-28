# I84 — operação administrativa local descartável, v1

Continuidade do PR #38 / I83, código `462b23a`, checkpoint `df7ea64`.
Branch própria `exp/s0-s1-i84-operacao-edge-local-20261027`, PR Draft #40.
Somente laboratório. Não é instalação, migração ou homologação hospedada.

## Pré-requisitos e identidade do ambiente

Linux, Docker local em `/var/run/docker.sock`, Supabase CLI **2.84.2**, Python
com `backend/requirements-s0-local.txt`, checkout desta branch e checkout somente
leitura da S1 no commit `8780b576aa18bd3983c063339e2e42d2452af22c`.
Não executar a stack de testes simultaneamente: compartilham o nome local
`prumo-s0-auth-ci` e as portas 54321/54322. O operador recusa adotar stack/volume
preexistente, inclusive stack criada pela suíte. Requer criação inteiramente nova.

O operador não aceita URL, projeto remoto, identidade humana, senha ou HMAC em
argumentos. Recusa link `supabase/.temp/project-ref`, configuração diferente do
manifesto, CLI diferente e endereços fora do loopback fixo. Docker sempre local.
Confirma engine Docker, ID físico do DB e marcador aleatório no comentário do
banco; não cria tabela de identidade ou segundo cofre. Não abrir as portas locais
à rede nem executar em máquina compartilhada com usuários não confiáveis.

## Sequência operacional independente da suíte

Executar na raiz do checkout experimental:

```sh
python3 -m pip install -r backend/requirements-s0-local.txt
export PRUMO_I84_DISPOSABLE=YES
python3 -m local_admin init
python3 -m local_admin prepare --s1-source /caminho/checkout-s1-somente-leitura
python3 -m local_admin provision
python3 -m local_admin serve
python3 -m local_admin status
python3 -m local_admin rotate
python3 -m local_admin revoke
python3 -m local_admin worker-stop
python3 -m local_admin down
```

A opção global `--state-dir /tmp/prumo-admin-i84-<identificador>` precede o
subcomando e precisa ser usada consistentemente. Default:
`/tmp/prumo-admin-i84-<uid>`. Diretório 0700, arquivos 0600, não usar symlinks.
Nunca executar `cat edge.env`, `supabase status` sem captura protegida,
`docker inspect` completo ou enviar arquivos privados a diagnóstico/CI.
O CLI imprime somente JSON técnico permitido, sem segredos/URLs/identidades.

| Comando | Efeito |
| --- | --- |
| `init` | Recusa recursos anteriores; inicia stack nova e registra identidade física |
| `prepare --s1-source …` | Verifica hashes e instala dependências certificadas, sem executar testes nem criar humanos/casos |
| `provision` | Emite material I83 no mesmo login/cofre; nunca usa perfil compartilhado |
| `serve` | Inicia TypeScript/Deno real e confirma nova identidade do container e perfil dedicado |
| `status` | Fase, geração, pendência, validade, identidade/configuração do worker e readiness técnico |
| `rotate` | Retira worker, troca material atomicamente pela I83 e reinicia quando estava servindo |
| `restart` | Retira worker atual e inicia container novo com a mesma configuração válida |
| `revoke` | I83 retira material, NOLOGIN/password NULL, encerra sessões SQL; worker antigo não recupera autoridade |
| `worker-stop` | Retira processo/container identificados, restaura Kong; remove env após revogação |
| `recover` | Após emissão incerta, **somente revoga/retira**, sem gerar credencial ou repetir negócio |
| `down` | Retira material, encerra stack sem backup, verifica containers/volumes/rede ausentes |

`status.ready` confirma disponibilidade técnica e credencial válida. Não representa
prova de autoridade de Diretor, chamada comercial ou integração Frontend aceita.
O operador não possui comando de bootstrap de Diretor: a criação de usuários e
competência administrativa continua sendo gate separado. A jornada automatizada
cria humanos sintéticos exclusivamente no módulo de teste, após `prepare`.

## Reutilização e privilégios

A API continua em `supabase/functions/prumo-admin-i82`, HTTP `prumo.admin.v1`,
seis comandos I79/I80 sem mudanças. Python coordena infraestrutura/custódia,
não executa como API nem duplica a autoridade SQL. O instalador local permanece
`postgres` e não é entregue à Edge. Reutiliza integralmente o gerador, SCRAM,
janela de logging privado, cofre, validade, rotação, revogação e env da I83.

Permanecem `prumo_s1_admin_edge_local`, `prumo_s1_edge_custodian_local`, owners
NOLOGIN I81 e executor HMAC existentes. Nenhum novo papel, membership, grant de
negócio, endpoint ou regra comercial. As funções de verificação de fontes S1 e
construção I79 foram extraídas para reutilização, sem mudar o SQL resultante.
As verificações de fonte/admissão do operador permanecem ativas com Python -O.
O helper Kong I82 admite ambiente explícito para garantir Docker local, mantendo
o comportamento anterior por default.

Após instalar os bytes históricos, `prepare` põe logins `prumo_*` compartilhados
em NOLOGIN/password NULL e desativa as chaves compartilhadas da instalação
histórica, somente nessa stack nova. A Edge nunca recebe esses valores. Essa
quarentena impede uso operacional das credenciais laboratoriais publicadas nas
fixtures antigas. Não suspende contas humanas, intake ou concessões comerciais.
As regressões históricas que precisam dessas fixtures rodam em **outra stack**.

Antes/depois são comparados owners, ACLs, memberships, RLS, funções/hashes,
triggers, constraints e dependências pelo catálogo I83. Só o bit LOGIN do login
dedicado varia durante a emissão; metadados devem voltar exatamente ao estado
pós-prepare após revogação. A revisão de DDL metadata-only I81/I82 permanece
obrigatória: mudança de fonte ou catálogo bloqueia operação, sem auto-grants.

## Falhas, concorrência e resultado incerto

Trava flock por usuário/projeto cobre todos os diretórios operacionais; I83
mantém advisory lock e locks SQL de chaves. Jornal fsync antecede alterações de
credenciais. Não apagar manualmente o lock enquanto houver operação.
Falha depois de possível COMMIT deixa fase UNCERTAIN: `provision`/`rotate` não
repetem automaticamente. Executar `recover`, conferir REVOKED e então decidir
explicitamente por nova emissão. Uma operação de negócio cuja resposta se perdeu
continua reconciliável pela **mesma chave idempotente**, conforme I82; timeout
não comprova rollback, cancelamento ou autorização para comando substituto.

Instalação parcial de dependências não é retomada/reaplicada às cegas: descartar
stack identificada e começar stack nova. Identidade física divergente, worker
não reconhecido ou restauração Kong não comprovada bloqueiam a operação. Não
matar processos/containers de terceiros nem contornar guards para recuperar.
O operador Linux/Docker é confiável; o journal privado não protege contra root
malicioso, Docker comprometido ou alteração maliciosa do próprio checkout.

Rotação exige reinício, com indisponibilidade. Sem promessa de zero downtime.
O ajuste local de Kong/CORS e o IP Docker são restauráveis/adaptações locais,
sem conversão automática para Supabase hospedado.

## Custódia, descarte e gates

Arquivo de material existente I83, privado fora do repositório; atualização
atômica e sem valor em argv, stdout/stderr, resposta HTTP ou artefato. Logs são
capturados privadamente; varredura compara valores em memória e só permite
metadados explícitos nos artefatos. `down` remove env/log/catálogo privado e
volumes/containers/rede, preservando tombstone técnico sem segredos. Não alega
destruição forense de RAM, WAL, cache do host, imagens Docker ou backups externos.
O diretório tombstone e o lock podem permanecer. `init` pode iniciar nova stack
após DISCARDED comprovado e sem recursos/arquivos de material, preservando o
tombstone anterior em previous.json; também é possível usar outro identificador.
Não apagar registro ainda em uso.

TLS, custódia produtiva, abuso distribuído, bootstrap Auth, homologação, rollout
e revisão Frontend são gates distintos. Produção/hospedado bloqueados. Não houve
chamada Meta/OpenAI, alteração Frontend ou nova auditoria F02; G01–G06 parciais e
G07 pendente permanecem. I79/I80 não ratificam revisão comercial F02.
