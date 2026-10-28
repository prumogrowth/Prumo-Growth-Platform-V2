# I86 — provisionamento manual exclusivo de Diretores, revisão 2

28/10/2026, America/Sao_Paulo. Base: dbf49ab19b73766d60678c4ce6f7dea56cd66c9b.
Política ratificada pela instrução expressa do responsável pelo projeto nesta
continuidade. Detalhes técnicos de implantação hospedada não estão homologados.

## Política ratificada e fronteira

Somente operador humano autorizado, em ambiente administrativo restrito do
Supabase, pode conceder, modificar, recuperar ou retirar autoridade de Diretor.
Diretores, Gestores, Consultores, IA, MCPs, automações, APIs e Edge comuns não
recebem esse poder. Cargo, JWT, metadados, service_role e permissão administrativa
ordinária não são autorização organizacional. Pode haver vários Diretores;
nenhum limite numérico, quórum, segunda aprovação ou prazo foi inventado.

I79–I85 continuam separando identidade GoTrue, classificação e competência
global. A retirada nega novos atos, inclusive com token antigo; conta Auth e
classificação histórica não são suspensas/apagadas automaticamente.

## Instrumento e alcance laboratorial

integration/i86/manual/procedure.sql instala funções INVOKER e duas tabelas
privadas no schema prumo_i86_manual. Não é migration oficial nem RPC; não
aparece em public, no frontend, Edge ou MCP. Todos os privilégios de clientes,
service_role, login Edge e login compartilhado são retirados desses objetos.
Nenhum papel, membership, grant de dados herdado ou owner NOLOGIN é alterado.

O contexto PostgreSQL do ensaio exige session_user=postgres, current_user=postgres,
PG17, banco local marcado pelo I84 e READ COMMITTED. A função não concede essa
capacidade: o chamador já a possui. Um SET ROLE, claim ou GUC alegando
manual=true não autentica o operador. RLS não impede uma conta de infraestrutura
comprometida de alterar o banco ou os próprios controles.

O banco não distingue humano e programa usando a mesma credencial privilegiada.
Bloquear sua disponibilidade a MCP/IA/automação, autenticar nominalmente o humano
e validar a origem do registro manual são controles operacionais externos.
Os testes positivos simulam o contexto técnico em laboratório sintético,
expressamente autorizado pela missão; não certificam presença humana,
identidade corporativa ou aprovação de pessoa real. O suporte positivo Python
fica somente em módulos de teste, com guard de VM descartável, sem CLI operacional.

## Atos suportados

| Ato explícito | Precondição e efeito |
| --- | --- |
| APPOINT | UUID GoTrue existente/usável e ainda sem ator/equipe/competência; insere ator, competência ativa e equipe Diretor/ativo atomicamente |
| REVOKE | Diretor canônico ativo; torna competência inativa e retira sessões na mesma transação |
| REACTIVATE | Mesmo Diretor canônico histórico, competência inativa; ativa somente mediante novo ato manual explícito; nunca recria sessões revogadas |

A nomeação de profissional já vinculado a outro cargo ou de ator legado
incompleto permanece recusada: não há conversão automática de Gestor/Consultor,
limpeza de chefia, casos ou concessões. Essa regularização exige desenho
específico, não edição indiscriminada das tabelas para contornar o procedimento.

Substituição é composta por atos humanos explícitos, não um comando que
transfira poderes automaticamente. A sequência, continuidade e eventual intervalo
sem Diretor não foram decididos; nenhum fluxo automático é implementado.
I85 continua bootstrap único e não é chamado por este instrumento. Recuperar
o último Diretor já classificado usa REACTIVATE manual, sem rebootstrap.

## Identidade, CAS, locks e auditoria

O alvo é o UUID canônico Auth, não email ou metadata. SQL protege sua existência
e recusa concessão/reativação de identidade excluída/banida; uma retirada negativa
continua possível para identidade banida. Não cria, desbane ou muda usuário Auth.
O login humano da aplicação continua passando por GoTrue e CFI-01 nas seis
portas existentes, sem usar a credencial técnica do operador.

Entrada: act_id UUID, action, target UUID, expected_sha256, operator_record_ref,
manual_record_ref e evidence_sha256. Referências são códigos ASCII limitados,
sem texto livre/PII. O hash da evidência vincula o registro, mas não prova sozinho
que sua origem é humana/autorizada. Não existe aprovação booleana por payload.

CAS usa snapshot SQL da existência/classificação/competência e xmin das linhas
canônicas, sem introduzir versão comercial ou mandato. Alterações de metadata
não concedem poder. Os locks técnicos de idempotência/assunto precedem domínio;
REVOKE segue sessões → ator → equipe → competência. Uma trava curta Auth
impede novas sessões durante o corte. A leitura bloqueante de auth.users usa
NOWAIT, evitando espera inversa contra escritores GoTrue que bloqueiam usuário
antes de sessões. Contenção aborta; não remove guard nem faz retry positivo.

Atos repetidos com mesma chave/payload e estado final igual não reaplicam nem
duplicam auditoria. Payload divergente conflita; CAS/estado mudado recusa.
Atos distintos contra o mesmo alvo serializam, inclusive antes de existir ator.
Alvos diferentes podem receber concessões independentes sem contagem global.

Ator, equipe, competência, ato e auditoria confirmam juntos. A auditoria inclui
SQL session/effective principal, backend, horário do servidor e referências do
registro manual; não transforma app name/SQL principal em prova de pessoa humana.
Tabelas são privadas, RLS/FORCE RLS e imutáveis por UPDATE/DELETE/TRUNCATE.
Constraints diferidas I79/I81 permanecem ativas; falha no COMMIT invalida tudo.

## COMMIT incerto e reconciliação

apply_act retorna RECORDED_IN_TRANSACTION ou ALREADY_RECORDED_IN_TRANSACTION,
sempre caller_commit_required=true. O SELECT não é confirmação do COMMIT.
Após confirmar a transação, reconcile_act consulta o mesmo act_id/evidência;
nunca emite nomeação/revogação/reativação. Registro próprio ainda não confirmado
retorna COMMIT_NOT_PROVEN; ausência retorna NOT_PROVEN; registro confirmado
visível e estado coincidente retorna COMMITTED_CURRENT_STATE_VERIFIED.

A visibilidade MVCC READ COMMITTED comprova que registro de outra transação
visível foi confirmado; xid8 diferencia o próprio registro não confirmado.
Não exige novo privilégio global de leitura de status de transações. Se o
estado posterior já mudou, COMMITTED_STATE_CHANGED informa histórico, sem
restaurar a autoridade anterior. Não há retry automático após timeout.

## Reclassificação D01–D05

| Decisão | Ratificado nesta instrução | Ainda não definido/aprovado |
| --- | --- | --- |
| D01 | Somente operador manual autorizado no Supabase; aplicação/Diretor/IA não nomeiam | Identidade nominal, gestão e custódia do acesso privilegiado hospedado |
| D02 | Sem aprovação automática; evidência do ato manual obrigatória | Fonte/validação/retenção operacional da evidência e vínculo nominal; quórum/prazo não definidos e não impostos |
| D03 | Substituição somente manual, sem transferência automática | Sequência e detalhes de continuidade |
| D04 | Recuperação somente humana privilegiada, sem rebootstrap | Operadores e procedimento emergencial efetivos, se houver |
| D05 | Retirada somente manual privilegiada, com revogação eficaz | Gestão operacional do acesso/evidência; não se concede esse poder ao Diretor |

O observador v1 permanece compatível e histórico: seu PENDING_DECISION não é
canal de aprovação. A revisão 2 explicita MANUAL_PRIVILEGED_ONLY sem habilitar
nenhuma operação na aplicação. Veja DECISOES.json para rastreabilidade.

## Limites e integração

Exclusivamente VMs GitHub-hosted separadas, stacks novas, loopback e credenciais
sintéticas. A fiscalização fixa a base I86, os dois diretórios e somente o novo
workflow; o workflow anterior permanece protegido. Nada da Meta é dependência.
Sem produção, Diretor real, deploy, merge, migrations hospedadas ou interface.
Custódia produtiva, identidade do operador, evidência externa e homologação de
provisionamento precisam de decisão própria antes de qualquer uso hospedado.
