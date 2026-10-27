# I81 — ownership administrativo restrito, candidato experimental v1

27/10/2026, America/Sao_Paulo. Base exata: I80/PR #30,
`cfeca5f39d9744340f5f362c2f65a4b201e2d5f5`. Não substitui os contratos I79/I80.
Não é migration hospedada, endpoint, novo sistema de cargos ou autorização comercial.

## Problema e limite da mudança

A I46 instituiu negação de escrita de equipe quando `current_user <> postgres`,
inclusive se um GRANT indevido ou BYPASSRLS aparecer. As pontes I79/I80 executavam
com owner postgres para satisfazer esse guard e seus triggers INVOKER. No COMMIT,
a constraint I79 precisa executar depois do retorno do DEFINER, quando o chamador
SQL já não possui os privilégios da ponte. Uma troca cega de owner perde essa
validação ou leva a grants excessivos para o login.

A I57 preserva locks e rechecagem de concessão na atribuição canônica. A I61
acrescenta uma prova privada limitada a loja/caso/atribuição/operador, que exige
executor de casos postgres, chefia e contas ativas e exceção não revogada.
Regularização administrativa não cria atribuição, caso ou exceção: não precisa
receber a autoridade desses comandos. Revogar exceção é diferente de concedê-la.

O delta separa o domínio administrativo I79/I80. Não altera o ownership do
dispatcher G1, I54/I55/I62, remanejamento ou outros módulos comerciais S0.
Esses owners anteriores permanecem um escopo de endurecimento separado.

## Owners e fronteiras

| Objeto / responsabilidade | Antes | Depois |
| --- | --- | --- |
| `s1_i79_admin_bridge(...)`, DEFINER | postgres | `prumo_s1_admin_domain_local` |
| `s1_i80_bridge(...)`, DEFINER | postgres | `prumo_s1_admin_domain_local` |
| `s1_i79_consistencia()`, DEFINER, constraint diferida | postgres | `prumo_s1_professional_validator_local` |
| I79/I80 signed, HMAC/nonce | `prumo_s0_g1_executor_local` | mesmo owner e corpos |
| Tabelas, schemas, I46 e helpers INVOKER | owners existentes | mesmos owners |
| I57/I61 e comandos de casos | owners existentes | mesmos owners, corpos e grants |
| `cfi01_session_valid_local` | postgres, leitura Auth limitada | mesma função existente |
| `s1_i81_auth_identity_exists(uuid,boolean)` | não existe | postgres, somente existência/lock de UUID Auth |

Ambos os novos owners são NOLOGIN, NOINHERIT, NOSUPERUSER, NOCREATEDB,
NOCREATEROLE, NOREPLICATION e NOBYPASSRLS. Não recebem CREATE em schema no estado
final, ownership de tabela, credencial ou membership de outro papel.

O login SQL continua executando apenas os comandos assinados já existentes.
Não recebe EXECUTE nas pontes, helpers ou validador, DML privado nem membership
nos owners. `anon`, `authenticated` e `service_role` continuam sem a porta
assinada ou EXECUTE privado. BYPASSRLS do service_role não supera ACL/guard.

**Instalação e PostgreSQL 17:** a transferência usa um grant temporário com
SET=true ao instalador, revogado na mesma transação. PG17 mantém também o vínculo
ADMIN-only de criação para postgres, concedido pelo bootstrap, com INHERIT=false
e SET=false. Ele é inventariado com grantor e não equivale a poder assumir o
owner. O instalador já administra o banco; não se atribui essa competência ao
login da aplicação. Qualquer vínculo executável remanescente dos novos owners
ou membership para outro consumidor faz o aceite falhar. Não se tenta contornar
o bootstrap ou obter superuser para apagar um vínculo administrativo inerte.

## Grants e RLS do domínio

O domínio recebe somente os objetos usados pelas pontes originais:

- leitura dos metadados de equipe, chefia, competência global, concessões,
  intake, atribuições, casos e exceções que compõem a prévia/CAS;
- INSERT de identidade organizacional por UUID existente e cadastro pendente;
  UPDATE de cargo/estado de profissional que não seja Diretor;
- INSERT de chefia e UPDATE apenas de `encerrado_em`, sob os guards I79;
- UPDATE somente de `revogada_em` I61 e INSERT de evento com autoria preservada;
- SELECT/INSERT de prévias, recibos e auditoria imutáveis I79/I80;
- USAGE nas duas sequences de chefia/evento I61 e EXECUTE nos helpers exatos.

Não recebe leitura de chaves, senhas, sessões Auth, email ou mensagens, inserção
de nonce, criação de exceção, atribuição/caso ou concessão, alteração de intake,
diretoria ou escopo de loja. Não ganha DELETE, TRUNCATE nem GRANT OPTION gerais.

Para SELECT FOR UPDATE/SHARE, as colunas de lock têm ACL UPDATE específica e
policy UPDATE com `USING(true) WITH CHECK(false)`. Isso permite bloquear a linha,
mas não confirmar nem um UPDATE de ID para o mesmo valor. O domínio administrativo
não vira escritor de caso, concessão, intake ou competência por receber esse ACL.

As novas policies são exclusivas dos owners, sem mudar as policies dos usuários.
RLS permanece habilitada, sem novo BYPASSRLS e sem transferir a tabela ao owner.
As pontes continuam verificando Diretor real e escopo depois dos locks; a policy
de leitura de metadados do serviço não autoriza um chamador humano por si só.

`xmin`, usado pelo CAS I80 já certificado, exige SELECT de tabela no PG17,
mesmo quando todas as colunas usuais têm SELECT individual. Casos/atribuições
recebem essa leitura necessária; o instalador confere antes a lista exata de
colunas metadata-only da base (IDs, datas, origem e motivo codificado). Coluna
nova ou conteúdo não revisado impede o provisionamento, sem conceder leitura
automaticamente. Não se remove `xmin` nem a proteção ABA para evitar esse ACL.
A guarda atua na instalação; DDL posterior exige nova revisão de schema/ACL.
Não é um monitor de DDL: SELECT de tabela também cobre colunas futuras caso um
instalador privilegiado as adicione fora desse processo. A ponte mantém projeção
fixa de metadados e nenhum consumidor recebe acesso direto ao papel.

O validador recebe apenas leitura de equipe/chefia/competência, lock de equipe
com WITH CHECK(false) e EXECUTE de `s1_i79_validar_profissional`. Não pode mudar
estado/cargo/chefia, escrever auditoria de aplicação ou chamar a administração.

## Guards e autenticação preservados

I46 continua INVOKER, com o mesmo erro e triggers. A única extensão é um nome
exato de owner inacessível ao cliente na lista de executores. Não usa JWT,
`request.jwt.claims`, GUC de “admin”, subordinados ou grants para inferir papel.
Grants acidentais de tabela para um cliente continuam barrados pelo guard.

I57/I61 não recebem novo executor. O teste concede EXECUTE de prova I61 ao domínio
**só em uma transação de teste revertida**: mesmo assim a prova retorna false,
pois esse papel não é o executor de casos. As regras de concessão, intake,
unicidade de chefia, FK adiada da exceção e imutabilidade continuam ativas.

REGISTER troca apenas a consulta direta Auth pela função booleana privada;
mantém o FOR SHARE de `auth.users`, inclusive rechecagem após espera. I80 troca
apenas a expressão de existência, preservando os campos e semântica do snapshot.
O domínio não precisa de acesso ao schema Auth. A consulta de sessão viva é a
mesma função CFI-01, com o mesmo lock e prazo de `auth.sessions`.

HMAC, domínios de assinatura, chaves, nonces, janela temporal, fontes de identidade,
autoridade do Diretor, CAS, idempotência, ordem de locks, recibos e auditoria
I79/I80 permanecem os anteriores. A troca não invalida uma prévia ainda válida
nem renova seu prazo. Não altera o estado de qualquer profissional por instalar.

## Provisionamento e aceite

Opt-in duplo, loopback pelo `local_env` existente, PG17, banco descartável e
current_user/session_user postgres. Corpos SHA-256, owner, modo de segurança e
configuração de oito funções de dependência devem coincidir com a base
certificada. ACL inesperado de ponte ou papel HMAC desviado impede instalação.
Não há fallback para um objeto desconhecido ou substituição por código novo.

O SQL é uma única transação: guards/policies/grants/owners/roles voltam ao estado
anterior se qualquer passo falhar. Replicar a instalação sobre um estado já
alterado falha por precondição; não há “reparo” silencioso de permissões.

O workflow executa baseline, recusas e rollback de DDL, cutover com prévia real,
I79/G1 e I80 completos após a troca, ataques de privilégios e catálogo final.
Catálogos não contêm linhas de negócio/Auth, segredos ou provas HMAC. Incluem
owners, grantors, ACLs efetivos, bodies por hash, policies, triggers, constraints
e `pg_depend`. Dependências PL/pgSQL não são todas registradas por pg_depend;
os fluxos e probes físicos complementam o inventário, sem alegar um grafo
estático completo de todo runtime futuro.

## Limites e continuidade

O aceite certifica a separação administrativa somente no ambiente descartável.
Permanecem bootstrap/gestão de roles, privilégio de instalação, custódia e rotação
de credenciais, observabilidade/retenção, homologação e migrations produtivas.
Os dois helpers Auth de escopo limitado continuam postgres-owned; a escrita
administrativa e validação profissional não executam como postgres.

Não há endpoint nem runtime operacional nesta entrega. A etapa seguinte, após
CI de ownership conclusivo, é preparar a borda administrativa em Edge Functions
**local**, conforme ADR Supabase, reutilizando I79/I80 sem outra autenticação.
Não é autorização de deploy, migration hospedada ou servidor→OpenAI comercial.

F02 permanece sem implementação nova: G01–G06 parciais, G07 pendente. Não se
repete a auditoria G01–G07 ou H01. I79/I80/I81 não ratificam revisão comercial.
