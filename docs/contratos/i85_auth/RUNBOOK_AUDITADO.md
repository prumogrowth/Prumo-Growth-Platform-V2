# I85 — runbooks auditados, exclusivamente laboratório

28/10/2026, America/Sao_Paulo. Este procedimento não nomeia pessoa real, não é
I86, não promove o HTTP candidato a contrato Frontend aprovado e não serve para
Supabase hospedado. O relatório delimita a revisão de código/CI efetivamente aceita.

## Bootstrap sintético

Na branch I85, Linux/Docker local confiável, CLI Supabase 2.84.2, requirements S0
instalados e checkout S1 somente leitura em 8780b576. A stack deve ser nova,
não vinculada e sem usuários ou Diretoria preexistentes. Nunca adotar outra stack.

```sh
export PRUMO_I84_DISPOSABLE=YES
export PRUMO_I85_DISPOSABLE=YES
python3 -m local_admin init
python3 -m local_admin prepare --s1-source /caminho/s1-em-8780b576
python3 -m local_admin provision
python3 -m local_admin serve
python3 -m integration.i85 init
python3 -m integration.i85 create --label director
export PRUMO_I85_DIRECTOR_APPROVAL=AUTHORIZE_SYNTHETIC_DIRECTOR_ONLY_IN_OWNED_DISPOSABLE_LAB
python3 -m integration.i85 authorize-director
unset PRUMO_I85_DIRECTOR_APPROVAL
python3 -m integration.i85 grant-director
python3 -m integration.i85 status
```

O opt-in é intenção técnica local; não é assinatura corporativa ou autorização
comercial. A aprovação guarda UUID canônico, marcador físico e ID técnico. A
custódia é única por UID/projeto e ambas as interfaces suportadas (CLI e métodos
Python públicos) usam a mesma trava não bloqueante e releitura. Um segundo
instalador não pode escolher outro diretório para contornar a custódia. A defesa
SQL adicional serializa candidatos canônicos distintos e recusa toda competência
ou classificação anterior, inclusive revogada. Root/Docker host deliberadamente
malicioso continua fora dessa fronteira: já controla SQL e arquivos.

O perfil Edge I85 não recebe service_role, URL SQL postgres ou chave JWT do
instalador. Usa o Runtime/launcher oficial fixado, os arquivos I82 sem mudanças e
somente o login/chave I83 próprios. O servidor fica na rede local verificada,
sem Docker socket ou custódia I85 montados, com fonte somente leitura. O uso
administrativo da service_role é do instalador; GoTrue/Kong continuam infraestrutura
confiável que valida suas próprias chaves. Nunca passar service_role ao navegador.

Se o worker foi iniciado antes do opt-in I85, `init` deve recusar o perfil legado.
Retirar o worker reconhecido com I84 e servir novamente sob o perfil restrito;
não contornar a recusa. Depois de marcada a stack como I85, remover o opt-in não
deve selecionar silenciosamente o perfil legado. Não executar outra versão do
operador ou outro checkout contra o mesmo laboratório.

## Reconciliação de identidade ou COMMIT

```sh
python3 -m integration.i85 reconcile-identity --label director
python3 -m integration.i85 reconcile-authority
```

CREATE_UNKNOWN não significa ausência de usuário. A reconciliação consulta SQL
Auth e GET administrativo GoTrue, conferindo UUID/email exatos. Nunca emite outro
POST. Se o usuário não existe, permanece BLOCKED: não gerar email/senha/UUID
substitutos para tornar o ensaio verde. COMMIT_UNKNOWN só vira ACTIVE se as três
estruturas canônicas e a aprovação do mesmo UUID forem comprovadas. Zero linhas
não autoriza novo grant, pois a operação pode ter sido interrompida ou ainda
carecer de prova. O operador pode optar por destruir o laboratório inteiro,
preservando evidência; isso não é reexecução de bootstrap no mesmo banco.

A I85 v2 recusa arquivos v1 em vez de inventar conversão de aprovação antiga.
Journals antigos/incertos devem ser preservados e retirados pelo procedimento de
laboratório descartado, não copiados para uma stack nova. Instâncias Python que
já observaram um laboratório não podem retargetar outro após troca da stack.

## Escrita interrompida, resíduos e auditoria parcial

```sh
python3 -m integration.i85 recover-journal
```

O comando é explícito, serializado e não faz POST Auth nem INSERT de Diretoria.
Snapshots exatos de arquivos correntes e resíduos ficam em `evidence/`, dentro
da mesma custódia 0700/0600, antes de alterar qualquer original. Não exportar essa
pasta: snapshots de secrets também são material sensível. Um plano durável permite
repetir somente a recuperação de arquivos, sem repetir operações de negócio.

Confirmação staged ACTIVE/CONFIRMED não é aceita como sucesso: conserva
COMMIT_UNKNOWN/CREATE_UNKNOWN e exige reconciliação canônica posterior. Aprovação
staged é marcada approval_pending e exige novamente o opt-in técnico, preservando
o ID da aprovação. Não ratifica autoridade automaticamente. Intentos staged de
COMMIT ou revogação são conservados como desconhecidos. Auditoria parcial tem o
prefixo completo reconstituído e o original integral retido para investigação.

JSON parcial, duplicado, não finito, UUID divergente, segredo órfão, múltiplos
candidatos incompatíveis, permissões alteradas, hardlinks/symlinks ou plano sem
prova permanecem BLOCKED. Não apagar `.next`, não fazer chmod amplo e não escrever
NONE/REVOKED manualmente. Não se promete recuperação automática de toda falha de
energia/daemon. Os bloqueios têm caminho explícito de descarte do laboratório.

## Revogação e sessões

```sh
python3 -m integration.i85 revoke-director
python3 -m integration.i85 reconcile-authority
```

A revogação é monotônica: atualiza competência global para ativo=false e retira
sessões. Pode ser explicitamente retomada em REVOKE_UNKNOWN ou repetida em REVOKED
para retirar sessões posteriores; jamais reativa cargo/competência. Os locks
seguem sessões → ator → equipe → competência. Uma trava curta de tabela Auth,
usando a capacidade de instalação já existente, impede novas inserções durante
esse corte e fecha o problema de sessões fantasmas. Não é grant para a Edge nem
projeto de provisionamento hospedado; interrompe brevemente escritas Auth locais.

Se houve falha após COMMIT, a reconciliação pode confirmar REVOKED sem nova
mutação. Se a transação sofreu rollback, permanece desconhecida e exige o comando
explícito de revogação; não há retry positivo ou rebootstrap automático.

**Cargo Diretor/estado ativo não são competência.** I79 exige equipe ativa,
cargo explícito e competência global ativo=true; I80 e consumidores S1 pertinentes
também revalidam a competência. A classificação remanescente é identidade/histórico
organizacional, não permissão. Não foi convertida em suspensão/desligamento,
nem foram apagados atores, história, intake, concessões ou casos.

A retirada de sessão no corte não bane a conta nem troca sua senha. Novo login
Auth pode ocorrer e deve continuar sem administração (403), sem depender de JWT
renovado ou cache de cargo. A matriz registra o comportamento observado do
refresh token, sem prometer invalidação criptográfica universal de JWT. Operações
sensíveis verificam sessão/competência novamente no SQL. Se login concorrente
criar sessão após COMMIT e antes da confirmação de zero sessões, a confirmação
pode bloquear; repetir a retirada explicitamente ou descartar a stack inteira.
Não inventar banimento de conta, prazo comercial ou transferência de Diretoria.

O bootstrap é único por laboratório. Tombstone de competência e classificação
impedem nova nomeação, inclusive após revogação. Futuras nomeações ordinárias,
substituição de titular e política de conta exigem contrato específico fora desta
I85; não são autorizadas pela aprovação sintética inicial.

## Descarte normal e interrupções de dispose

```sh
python3 -m integration.i85 revoke-director
python3 -m integration.i85 dispose
python3 -m local_admin down
```

`dispose` revalida SQL, não confia em um journal que diga NONE/REVOKED. Recusa
competência ativa, resultado desconhecido e identidade ainda não reconciliada.
Persiste intenção, move atomicamente a custódia para `.disposing` e retira os
arquivos privados. Depois guarda somente uma prova técnica sem segredos em
`.disposed`. Se interrompido, executar `dispose` novamente: não executar init,
não recriar os arquivos que já foram retirados e não promover nenhuma fase.

Dispose não exclui usuários GoTrue nem histórico S1: a destruição completa das
identidades sintéticas depende de `local_admin down`, com volumes/rede/containers
verificados ausentes. Não reutilizar tokens ou journals em outra stack. Não há
alegação de destruição forense de RAM/WAL/cache ou backups externos.

## Abandono explícito de laboratório incerto

Primeiro preservar as provas e diagnosticar. Se a retomada não puder ser provada,
a alternativa é destruir **somente a stack própria identificada**, mantendo a
incerteza documentada. Não mudar a fase local para fingir revogação.

```sh
python3 -m local_admin down
export PRUMO_I85_ABANDON=PRESERVE_EVIDENCE_AFTER_VERIFIED_LAB_DISCARD
python3 -m integration.i85 abandon-after-stack-down
unset PRUMO_I85_ABANDON
```

O abandono só é admitido com tombstone I84 DISCARDED da mesma engine/token/DB/rede
e inventário físico vazio. Retira senhas e seus snapshots, preserva journal,
auditoria e hashes não secretos num diretório `.abandoned-*` privado para análise.
A saída declara essa retenção. Não transplanta a aprovação/identidade para outra
stack. Resíduo de init sem nascimento físico comprovável continua bloqueado para
intervenção técnica; nunca remover recursos de terceiros ou adotar outra stack.

Nos testes, cada caso usa uma stack nova e encerra a própria stack. Nenhum teste
apaga histórico de equipe, desliga trigger ou concede privilégios para reutilizar
um banco. Artefatos permitem apenas resultados, contagens, hashes e provas de
limpeza; nunca diretórios privados, senhas, JWTs, service_role, HMAC ou logs brutos.
