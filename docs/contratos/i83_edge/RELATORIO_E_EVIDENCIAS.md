# I83 — execução e evidências do provisionamento Edge dedicado

27/10/2026, America/Sao_Paulo. Base PR Draft #35, checkpoint 3dec252e5711c075781984d899d6c46b66b8ec74,
código I82 c8817429184d4fb3d5bef29cb9e99d6f2b970f63, CI40554841552 SUCCESS.
Branch própria `exp/s0-s1-i83-edge-provisionamento-20261027`, PR Draft #38.
Estado de integração: **certificada em laboratório**, CI40595963445 SUCCESS;
nenhuma aprovação hospedada.

## Recuperação e escopo

HEAD I82 rechecado em 3dec252, S1 original em 8780b576, sem execução posterior
nessas fontes antes de implementar. PRs novos #36/#37 pertencem à Meta e não
foram incorporados. Contratos/checkpoints I79–I82, DTO prumo.admin.v1 e ADR vigente
recuperados. ADR na fonte F02 mais recente a69f601f mantém arquitetura Supabase
com backend Edge e futuro servidor→OpenAI, sem autorizar implantação.

Nenhum trabalho F02/Meta/Frontend duplicado. F02 G01–G06 parciais/G07 pendente.
Não há branch de outra frente modificada, merge, deploy, produção, usuário real,
credencial real, migração hospedada ou chamada OpenAI/Meta.

Skills Supabase e práticas PostgreSQL utilizadas. Documentação atual de secrets
Edge/custom roles consultada pelo MCP, sem acessar projeto hospedado. Changelog
HTTP indisponível pelo proxy local nesta execução; não se desativou TLS ou proxy.
O runtime e o driver continuam fixados na versão certificada pela I82; não foi
introduzida migração de SDK/chave publishable ou autenticação alternativa.

## Implementação

Login específico `prumo_s1_admin_edge_local`, criado NOLOGIN/sem senha, recebe
apenas USAGE privado, CONNECT local e EXECUTE das mesmas duas portas assinadas
I79/I80. Não representa a identidade humana. O provisionador separado gera senha
SQL e HMAC independentes com secrets, validade técnica curta e arquivo temporário
protegido. Valor real de senha nunca é interpolado em SQL; utiliza-se SCRAM.

O cofre `prumo_private.s1_i83_edge_credentials` é owned pelo novo custodiante
NOLOGIN, com RLS. O executor HMAC existente só lê/bloqueia a chave no contexto
do session_user dedicado; não recebe UPDATE do material. Diretor, sessão viva,
cargo/chefia, CAS, prévia, locks, nonce e auditoria permanecem nas portas existentes.

O ledger de nonce possui FK para o cadastro antigo. Para reutilizá-lo sem dar à
chave Edge autoridade em outros domínios, o cadastro antigo recebe apenas anchor
inativo com bytes zero. Material real existe só no cofre dedicado. As portas
administrativas antigas continuam compatíveis com o login anterior e suas chaves;
não há fallback do perfil dedicado para elas. Demais portas não são reescritas.

As quatro funções existentes conservam owner/security/config/assinatura. Mudanças
limitam-se a admitir o login técnico dedicado e selecionar/revalidar sua chave.
Guard I46/I57/I61, RLS de dados, owners I81, fence DDL I82, validação diferida e
contrato HTTP não são substituídos por TypeScript nem por novo domínio comercial.

Rotação serializa provisionadores e confirma substituição da senha/chave com
revogação e apagamento do HMAC antigo. SHARE da chave ordena revogação e operações;
validade é reavaliada após esperas. Senha SQL expirada/revogada barra conexão nova;
sessão já aberta precisa da barreira da chave transacional. Nenhum login consegue
reativar o segredo ou assumir os owners.

## Arquivos

| Arquivo | Alteração |
| --- | --- |
| `supabase/tests/s1_i83_edge_credentials_local_only.sql` | delta local atômico, preflight, dois papéis, cofre privado, RLS restrita e quatro patches de admissão/assinatura |
| `supabase/functions/prumo-admin-i82/runtime.ts` | perfil dedicado explícito, sem fallback ou mudança do HTTP/DTO |
| `integration/i82/test_edge.py` | hook único de configuração do servidor; mesmos 20 testes e comportamento padrão preservados |
| `integration/i83/provision_local.py` | instalação, geração, SCRAM, rotação, revogação, retirada e arquivo protegido; sem imprimir material |
| `integration/i83/install_local.py` | instalação explícita sem gerar segredo/ativar login |
| `integration/i83/catalog.py` | metadados/ACL antes/depois/final e equivalência dos corpos históricos |
| `integration/i83/test_logging_preflight.py` | preflight físico rápido de material/logging, sem novo privilégio; bloqueia a suíte longa se não demonstrado |
| `integration/i83/test_provisioning.py` | recusas e rollback reais de instalação |
| `integration/i83/contract_test.ts` | duas negativas/compatibilidade de configuração Deno, além das 12 I82 |
| `integration/i83/test_edge.py` | reaproveita 20 cenários I82 sob credencial dedicada; acrescenta isolamento/revogação/rotação/expiração e descarte |
| `.github/workflows/exp-s0-s1-i83-edge-provisionamento.yml` | baseline completo, instalação e runtime Edge real em stack nova, metadados e cleanup |

Python é provisionador/fixture, não runtime da Edge ou autenticação paralela.
Nenhum fonte de negócio I79/I80/I81 é reescrito. São adaptados somente o seletor
de configuração e a injeção de configuração técnica no laboratório I82.

## Execuções parciais

[CI40589532934](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40589532934),
código 1cacd7b: baseline completo e 20 I82 antigos aprovados; 3 recusas de
instalação I83, delta aplicado e I79 62/I80 33/I81 14 após delta aprovados.
Preparação da credencial falhou antes da suíte dedicada: **zero** cenários I83
executados. Não certifica integração. Diagnóstico não revelou valores.

A revisão encontrou sintaxe inválida na emissão de VALID UNTIL: literal datetime
adaptado pelo driver acrescentava ::timestamptz, não admitido por ALTER ROLE.
O parser PG17 reproduziu a recusa e aceitou ISO string sem cast. A correção usa
string ISO devidamente quotada. Diagnóstico agora limita-se a estágio fixo e
SQLSTATE, sem mensagens/detalhes/SQL/valores. O CI seguinte é necessário para
comprovar que não há outro bloqueio físico.

Na mesma revisão, o inventário foi ampliado para novos ACLs por coluna/schema/DB,
com comparação dos objetos originais. Não se exige que o cofre novo inexista no
catálogo final nem se retira sua RLS para obter igualdade. Cada corpo histórico
é recomposto removendo somente as mudanças técnicas esperadas, comparando SHA.

## Reprodução e custódia

Workflow próprio, somente branch I83, sem link de projeto. Reutiliza a stack e
perfis de regressão I82, depois executa:

```bash
PYTHONPATH=. python3 integration/i83/catalog.py before
PYTHONPATH=. python3 integration/i83/test_provisioning.py
PYTHONPATH=. python3 integration/i83/install_local.py
PYTHONPATH=. python3 integration/i83/catalog.py after
PYTHONPATH=. python3 integration/i79/test_professionals.py
PYTHONPATH=. python3 integration/i80/test_regularization.py
PYTHONPATH=. python3 integration/i81/test_ownership.py
PYTHONPATH=. python3 integration/i83/test_edge.py
PYTHONPATH=. python3 integration/i83/catalog.py final
```

Requer os opt-ins das fundações e PRUMO_I83_DISPOSABLE_TEST=YES. A preparação de
credencial é função explícita do instalador local e é consumida pelo harness da
Edge sem colocá-la em argv/stdout. Não há segredo de exemplo para copiar.

Diretório de ambiente 0700/arquivo 0600 fora do Git. A Edge dedicada recebe só sua
senha/HMAC; fixture de regressão pode continuar usando credenciais independentes
anteriores para seed, nunca entregues ao worker dedicado. O HMAC real não aparece
no anchor original nem no navegador. Artefatos só contêm metadados e provas sem
valores. O startup do CLI é redirecionado a arquivo privado não arquivado.

Cada retirada/restart inspeciona logs dos próprios containers em memória, sem
imprimir matches, e remove o container portador do ambiente. Fechamento revoga e
zera material, desativa login/limpa senha, termina conexões e remove arquivo,
mesmo se uma inspeção falhar. Stack/volumes são removidos no cleanup final.
Não é promessa de destruição forense de RAM/páginas/WAL, nem gestão produtiva de
segredos/rotação de alta disponibilidade.

## Limites

Contrato Frontend ainda candidato; revisão não bloqueia este provisionamento.
Classificações/chefias e conflitos legados continuam decisões explícitas do Diretor.
Bootstrap/convite Auth, UI, permissões de Gestor e funções comerciais não são criados.

Defaults públicos do PostgreSQL e capacidades de catálogo/TEMP são inventariados;
não são DML privado ou privilégios de domínio, e não se revoga PUBLIC global para
afetar outros consumidores. Novos helpers/DDL continuam exigindo revisão. O fence
I82 protege a forma de duas tabelas metadata-only, não todo DDL do banco.

TLS, gestão de segredos produtiva, configuração hospedada, rotação sem downtime,
controle distribuído de abuso e homologação continuam bloqueados. Adaptações de
Docker/Kong/CORS são locais. O gate G2 e a Issue #23 permanecem abertos.

## Segunda tentativa e isolamento do runtime

[CI40590611979](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40590611979),
código ab33a2c: instalação e regressões completas passaram; preparação da
credencial avançou, mas o probe inicial HTTP e a inspeção de logs falharam antes
da suíte dedicada. Zero cenários dedicados executados; entrega não certificada.
Cleanup SQL posterior à falha executou, sem valores no diagnóstico.

O harness anterior aceitava GET405 de um container I82 ainda em execução antes
de o CLI novo substituir o worker. Inspeção do CLI fixado confirmou que encerrar
serve não retira o container. O novo harness remove/verifica a ausência do worker
anterior antes de fornecer credenciais e exige identidade de container diferente.
Acrescenta probe SQL físico autenticado do login dedicado antes de iniciar a Edge;
essa prova não substitui os 20 cenários HTTP. Eventual falha informa somente
SQLSTATE e nome fixo de estágio, sem payload/segredo ou erro SQL detalhado.

## Terceira tentativa: gate de material em logs

[CI40592162977](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40592162977),
código 51b11c4: probe SQL dedicado e identidade de container novo confirmados;
os **20 cenários HTTP I82 com a nova credencial passaram**, assim como os dois
primeiros testes de isolamento/escopo. Ao preparar a primeira rotação, a inspeção
física encontrou material de credencial em log e interrompeu o restart. As
negativas seguintes sofreram efeitos da indisponibilidade, não certificaram
rotação. A suíte executou 35 métodos, resultado 13 falhas/1 erro; gate bloqueado.
Nenhum valor foi impresso no diagnóstico ou enviado como artefato.

A configuração Supabase upstream consultada usa log_statement=ddl; ALTER ROLE
com verificador SCRAM também exige proteção contra registro do material. A nova
janela privada usa somente SET LOCAL na conexão de provisionamento confiável:
log_statement=none, parâmetros de logging limitados e pgaudit.log=none quando
presente. Não altera GUC global/por-role, não concede SET em parâmetro, não
interfere na conexão da aplicação nem em tabelas de auditoria de negócio. Se o
instalador existente não puder configurar a janela, recusa ANTES de transmitir
material; não se resolve por novo privilégio ou role mais poderoso.

Um job de preflight físico agora precede a suíte completa: stack nova, tentativa
de configurações locais com privilégios existentes, probe NOLOGIN/SCRAM e bytes
sintéticos, inspeção de log em memória, papel removido e configurações restauradas.
Somente metadados sem valores vão ao artefato. A suíte dedicada passa a parar na
primeira falha, preservando diagnóstico e descarte sem erros em cascata.

## Preflight de logging e capacidade existente

[CI40594190450](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40594190450),
código f4d3033: preflight recusado por 42501 antes de transmitir material;
suíte longa pulada. Não é certificado. Defaults já seguros não precisam de SET.
A tentativa intermediária CI40594828856, código c42c327, foi cancelada ao corrigir
a integração com a capacidade documentada do instalador.

A revisão pública do Supautils confirmou: a allowlist existente do papel técnico
é aplicada a VariableSetStmt/SET, não a SELECT set_config. A implementação usa
SET LOCAL literal de uma lista fixa e evita ajustes quando o valor já está seguro.
Não há nova membership, superusuário, GRANT SET ON PARAMETER, ALTER ROLE SET ou
alteração global de logging. Parametrização privada não substitui essa fronteira.
A comprovação exige preflight e suíte completa no mesmo commit de código.

## Fronteira final de material: sem novo privilégio e sem reduzir logging de erros

CI40595036801 / código c97f4ef confirmou a negativa específica de
log_min_error_statement. A suíte longa foi pulada. Não foi concedida permissão
para contornar essa negativa. Esse parâmetro foi removido da dependência.

A escrita final utiliza parâmetros vinculados para armazenar temporariamente
verificador/bytes em GUCs da própria conexão/transação, prefixo prumo_i83.
Blocos anônimos INVOKER fixos usam esses valores para gravar a credencial sob o
papel já autorizado e convertem exceções em erro fixo/SQLSTATE antes de propagá-las.
Não há função privilegiada persistente nova, material em literal SQL transmitido,
segunda autoridade ou mudança no logging da aplicação. SET LOCAL continua
limitado aos parâmetros permitidos e já seguros; o limiar de erros fica intacto.

**Preflight físico do CI40595963445 / código 462b23a — PASS**, job122511819193:
SCRAM válido; falha real de timestamp de senha 22007; falha CHECK23514 com bytes
sintéticos reais; erros cliente e log DB sem valores; papel NOLOGIN de probe
retirado. Configurações antes/depois idênticas: log_statement=ddl,
log_parameter_max_length=-1, log_parameter_max_length_on_error=0,
log_min_error_statement=error, pgaudit.log=none. Somente durante a transação de
material: log_statement=none e log_parameter_max_length=0. Nenhum novo grant.

Artefato12776346252 de preflight contém apenas metadados. Seu conteúdo e hashes
ficam em evidencias.json. Esse PASS não substitui o gate completo da Edge,
regressões, revogação/rotação e catálogo/descarte finais, agora concluído conforme o fechamento certificado abaixo.

## Fechamento certificado da I83

**[CI40595963445 — SUCCESS](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40595963445)**,
código **[462b23a78618eb98f6f986dd2ff8e81c15bd4ce8](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/commit/462b23a78618eb98f6f986dd2ff8e81c15bd4ce8)**,
tree c43f8c61f0653b4ac4a944d8b11f4a95b9552bd3. Jobs preflight122511819193,
S1 nativa122511818765 e integrado122512740733, todos SUCCESS. Registros de início
19:35:20 e atualização final19:47:00 em America/Sao_Paulo, 27/10/2026
(22:35:20Z–22:47:00Z; 700 segundos). Commit documental posterior não altera fonte.

| Prova real/unitária | Resultado |
| --- | --- |
| Preflight PG17 de sucesso SCRAM + falhas senha/row e não vazamento | **PASS**, limiar de erros e configurações gerais restaurados; sem novo grant |
| Mesmos 20 cenários HTTP I82 sob provisionamento dedicado | **20/20**, Edge Runtime/GoTrue/PG17/PostgREST reais conforme cada fluxo |
| Novos casos de credenciais I83 | **15/15**; suite dedicada total **35/35 em 54,523s** |
| Recusas/rollback de instalação I83 | **3/3**, sem geração de material |
| I79/G1 após delta I83 | **62/62** |
| I80 após delta I83 | **33/33** |
| I81 segurança após delta I83 | **14/14** |
| Perfis anteriores I79/I80 antes/depois I81 e após fence I82 | **62 + 33 por perfil**, preservados |
| I81 instalação/cutover originais | **6 + 1**, aprovados novamente |
| I82 perfil anterior HTTP | **20/20**, antes de instalar I83 |
| Histórico S0/I63 | **19/19 por perfil** |
| CFI/F02 anteriores | **56/56** |
| G1 real anterior à I79 | **36/36** |
| Deno fronteira/configuração | **14/14**: 12 originais I82 + 2 dedicados |
| Codec Python/TS | **1 teste / 7 vetores sintéticos**, não autoridade operacional |
| Unitários existentes S0 / S1 e catálogos | **288 / 193**, aprovados |
| SQL fila/exceção com identidades de fixture | **34/34**; nativo I54–I74/I78, I46/I48/I75B/I75C PASS |
| Catálogo e retirada | **after = final**, material zerado, login desativado/senha NULL, zero sessões |

Perfis/heranças se sobrepõem; não somar repetições como quantidade inédita.
O teste de órfão I78 está no checkout histórico original, anterior à I79. O
perfil integrado mantém exatamente uma chefia de Consultor ativo no COMMIT.
Nenhum PASS deste relatório certifica I75D/I76 ou percentual de gate comercial.
Nenhum ResourceWarning. Stack/volumes descartados com stop --no-backup.

### Isolamento e lifecycle efetivamente demonstrados

O probe inicial autenticou session_user=current_user no login dedicado e confirmou
INVENTORY SQL assinada antes da Edge. O container anterior foi retirado e a nova
identidade física verificada. Os 20 testes originais usaram a Edge dedicada,
sem login/chave compartilhados fornecidos ao worker. A fixture antiga só prepara
atores/casos/situações negativas com autoridade própria de laboratório.

As 15 provas adicionais estão nominadas em evidencias.json: duas portas exatas,
negação de SELECT/DML/GRANT/CREATE/SET ROLE e Auth; cofre/anchor separados; chave
expirada em pool aberto; HMAC inválido/ausente; senha SQL incorreta; rotação nova
válida e antiga recusada inclusive em sessão SQL já aberta; revogação sem restart;
os dois sentidos de disputa entre revogação e comando com blocker PG físico;
reconciliação da mesma requisição após troca de credencial; senha SQL expirada;
expiração da chave durante espera com rollback total; prévia I80 preservada pela
rotação sem ampliar autoridade humana; nonce global recusado entre duas chaves.

Perda real de resposta após COMMIT, replay idempotente, revogação do Diretor sob
locks, concorrência APPLY, rollback parcial/diferido e isolamento entre duas
lojas/equipes continuam nos 20 cenários I82, agora sob as credenciais próprias.
O teste de resposta perdida usa somente proxy de teste, não header de bypass.

Antes de cada retirada/restart, logs dos containers próprios DB/Auth/Kong/Edge e
do CLI são inspecionados em memória contra os valores gerados de senha, SCRAM,
HMAC e DSNs. Nenhum match no fechamento certificado. O controle de erro do
preflight também foi executado contra o log físico, sem emitir valores.
Após a suite: active_or_secret_key_rows=0, senha SQL NULL, NOLOGIN, sessões=0;
container portador de ambiente e arquivo servidor removidos. São verificações
reais, não inferências a partir de teste unitário.

### Owners, grants e inventário antes/depois

| Metadado | Antes I83 | Depois e final |
| --- | --- | --- |
| Papéis do recorte / memberships | 10 / 31 | 12 / 33; dois novos papéis, apenas postgres ADMIN-only de instalação |
| Funções / dependências catalogadas | 107 / 204 | **107 / 204**, sem helper persistente novo |
| Tabelas / ACLs por coluna | 82 / 87 | 83 / 92, apenas cofre e cinco colunas de leitura/lock do executor |
| Policies | 145 | 147, duas somente no cofre para o executor HMAC no contexto dedicado |
| Triggers | 57 | **57**, definições e guards originais preservados |
| Constraints | 418 | 422, quatro somente do cofre; originais idênticas |
| Domínio/validador I81 | NOLOGIN e owners restritos | idênticos; nenhuma reversão para postgres |
| Login Edge | inexistente | ativo só no ensaio; final NOLOGIN/sem senha, sem SUPER/CREATEDB/CREATEROLE/REPLICATION/BYPASSRLS/INHERIT |
| Custodiante | inexistente | NOLOGIN, owner do cofre, sem permissões comerciais ou Auth |
| EXECUTE do login em public/private | inexistente | exatamente s1_i79_admin_signed e s1_i80_signed; zero outras funções |
| Dados em tabelas do login | inexistente | zero privilégios efetivos SELECT/INSERT/UPDATE/DELETE/TRUNCATE, inclusive por coluna |
| Schemas Auth / S1 assinado | — | sem USAGE; public/private sem CREATE |
| DB postgres | defaults existentes | CONNECT/TEMP dos defaults públicos, CREATE=false; sem alterar PUBLIC global |

Novas memberships são somente postgres ADMIN=true, INHERIT=false, SET=false,
grantor supabase_admin; nenhuma membership de login/custodiante para outro role.
As permissões SET temporárias do instalador foram revogadas. Cofre owned por
prumo_s1_edge_custodian_local, RLS enabled; executor recebe somente SELECT das
cinco colunas necessárias e UPDATE(key_id) para lock, WITH CHECK(false).
Login não recebe grant de tabela, coluna, cofre, nonce ou autoridade de serviço.

Todos os owners/security/configs originais são idênticos. Apenas ACL das duas
portas assinadas acrescenta EXECUTE ao novo login. Remover as quatro adaptações
previstas de admissão/fonte/recheck recompõe o SHA-256 dos corpos históricos;
todos os outros corpos são idênticos. Privilégios efetivos dos consumidores
originais nos objetos originais são preservados. Catálogo after=final após as
provas de concorrência, falhas e retirada, sem resíduo de probes.

[Artefato dedicado12776997229](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40595963445/artifacts/12776997229),
retenção14 dias: before/after/final, prova de custódia e log interno sanitizado.
ZIP SHA256 7e6194c734236e9ad20a2cbff1c41ded14be1fcd8a02842e3766f25655fda052.
Evidência de logging no artefato12776346252 do mesmo run. Hashes de cada arquivo,
recortes de owners/ACL e os 11 hashes de fonte/CI estão versionados em
evidencias.json, sem material, verificador, senha, key UUID ou dados Auth.

## Continuidade segura

Provisionamento local dedicado funcional e demonstrado: a borda não usa mais
as credenciais compartilhadas no perfil I83. Isso não conclui G2 nem homologa
hospedagem. O perfil I82 anterior permanece apenas para compatibilidade e para
executar as regressões anteriores explicitamente; não é fallback do I83.

Próximo avanço: preparar interface de operação local para emitir/rotacionar/
revogar e servir/retirar o worker fora do harness, reutilizando o provisionador,
sem exibir material. Reexecutar as provas reais e revisar o mesmo DTO com o
Frontend em paralelo. Permanecem bloqueados TLS/secret management produtivos,
rotação sem downtime, controle distribuído de abuso, bootstrap/convite Auth,
aceite operacional e implantação hospedada. Nenhuma decisão comercial foi criada.
