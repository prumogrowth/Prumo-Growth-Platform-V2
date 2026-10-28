# I86 — diagnóstico, isolamento e interfaces futuras

28/10/2026, America/Sao_Paulo.

## Recuperação antes de editar

Origem I85 confirmada em 3cab3d57619cc1157698a08ac26f34e0c363f6dd, PR42 Draft,
código 062c90ffbe2b223c1d6bb08f614e7a1b6a898201 e CI40680048140 SUCCESS/seis jobs.
A branch exp/s1-i86-governanca-autoridade-20261028 retornou 404 antes da criação;
foi criada exatamente desse SHA, sem force e sem usar main ou Meta.
Worktree próprio: /workspace/prumo-i86. I85 histórica não foi editada.

Inventário remoto recuperou branches e PRs abertos, Issue23 e PR42. Busca I86
governança/autoridade no repositório não encontrou contrato oficial; a base
congelada também não contém módulos/contratos I86. Isso não ratifica esta
proposta: eventual decisão externa posterior deverá ser reconciliada pela
orquestração antes de alterar o bloqueio.

Foram lidos os contratos I79/I80, ownership I81, HTTP I82, provisionamento I83,
operação I84 e bootstrap/runbook/relatório I85, além dos implementadores de
identidade, sessão e portas SQL. A arquitetura Supabase é preservada: Python
continua instrumento experimental, não runtime Edge nem nova autenticação.

## Fontes canônicas e lacunas

| Estrutura | O que comprova | O que não comprova |
| --- | --- | --- |
| auth.users | Identidade emitida pelo GoTrue e UUID canônico | Cargo, nomeação ou poder comercial |
| auth.sessions | Vínculo vivo da sessão, usuário e not_after | Competência organizacional isoladamente |
| public.atores | Existência do mesmo sujeito no domínio S0 | Diretoria por si só |
| public.equipe_prumo_s1 | Cargo e estado explícitos; classificação histórica | Competência global apenas pelo rótulo |
| prumo_private.s1_responsaveis_plataforma | Competência global atual para portas ordinárias | Cadeia de nomeação, mandatos, substituição ou aprovação corporativa |

I79/I80 nunca criam Diretor. I85 é bootstrap único; seu instalador pode retirar
a autoridade sintética e não representa o órgão que nomeará pessoa real.
Registro revogado permanece como tombstone e classificação histórica. Regrant,
substituição e rebootstrap não são mecanismos de recuperação autorizados.

O backend revalida GoTrue e a sessão SQL. Revogação não depende de atualizar
metadados ou esperar expiração do JWT. A I85 já corrigiu a ordem invertida:
sessão → ator → equipe → competência. A nova observação segue essa direção;
depois de linearizar, sua saída é prova histórica, não permissão armazenável.

## Proteção automática

integration/i86/scope.py fixa SHA e tree da base, exige ancestralidade linear e
inspeciona cada commit, além do diff acumulado. Assim, editar e reverter arquivo
herdado não esconde uma violação. Ambos os nomes de rename/copy são verificados,
assim como removidos, modos symlink/gitlink, índice, worktree, não rastreados e
ignorados. Qualquer violação retorna FAIL/exit1 e impede os jobs físicos.

Allowlist literal: integration/i86/**, docs/contratos/i86_authority/** e
.github/workflows/exp-s1-i86-governanca.yml. Não há parâmetro de CLI para mudar
base ou allowlist. Os testes de Git usam repositórios artificiais externos,
sem fazer ataques nos worktrees reais. Relatórios de inventário são gravados
fora do checkout; o checkpoint persistirá seus hashes e o código exato testado.

## Execução física sem conflito de worktree

O ambiente de edição não tem Supabase CLI e a saída shell via proxy está
indisponível para o changelog Supabase. Nenhum daemon/stack local foi iniciado,
removido ou adotado. Documentação de sessões foi consultada pelo conector
Supabase; o cliente/CLI existente continua fixado, sem atualização de dependências.

Cada job físico usa VM GitHub-hosted nova, clone próprio e stack recém-criada
pelo I84. A exportação Git do HEAD verificado fica em diretório privado
RUNNER_TEMP, mantendo os bytes herdados; fontes S1 são fixadas em
8780b576aa18bd3983c063339e2e42d2452af22c e movidas para fora do checkout.
O operador mantém engine/DB/rede/marcador aleatórios e loopback físicos.
Não se escolhe projeto hospedado nem endereço por payload.

Um job executa a jornada I85 original, incluindo os seis comandos I79/I80.
Outro instala somente o schema privado de evidência I86 e executa suas provas.
A instalação usa o privilégio técnico já existente do host, sem novo login,
membership, grants herdados, migrations ou segredo. Não é interface operacional.

## Conflitos e limites de edição

Não foi identificada necessidade de editar código herdado para esta observação.
Caso um teste demonstre falha em I79–I85, a correção deverá ficar bloqueada aqui
e ser encaminhada à orquestração com causa/prova; a allowlist não será ampliada.

O eventual serviço operacional de governança exigirá contrato ratificado,
provisionamento de owner/login mínimo e desenho de auditoria/recuperação
apropriados. Não se promoverá o postgres desta fixture a credencial de API.
Esses pontos são dependências futuras, não implementações escondidas no ensaio.

## Fronteira exclusiva Meta e outras frentes

S0–META–INGRESS–01 permanece proprietária de M2M, webhooks, persistência de lotes,
ACK e recibos de ingestão. Nenhum módulo dessa frente é importado, modificado
ou necessário à CI I86. Não se incorpora branch Meta ou contrato candidato.

Uma futura competência humana para administrar canal/configuração é interface
organizacional a decidir; não autoriza envio, cancelamento externo ou conexão
de canal. F02 comercial e Frontend permanecem intocados. O escopo I86 não fecha
gates G1–G6, G01–G07 ou aceite visual.
