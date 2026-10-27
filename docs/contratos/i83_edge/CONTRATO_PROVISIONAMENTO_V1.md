# I83 — provisionamento dedicado da borda administrativa local, v1

27/10/2026, America/Sao_Paulo. Continuidade I82/PR #35, código c881742,
checkpoint 3dec252, CI40554841552 SUCCESS. Implementação exclusiva de laboratório;
contrato HTTP prumo.admin.v1 inalterado e ainda candidato para o Frontend.

## Responsabilidades

| Responsabilidade | Identidade/capacidade |
| --- | --- |
| Instalação descartável | postgres no DB postgres loopback PG17, opt-in explícito; não entregue à Edge |
| Custódia SQL | prumo_s1_edge_custodian_local, NOLOGIN/NOINHERIT/NOBYPASSRLS, owner somente do cofre dedicado |
| Execução técnica Edge | prumo_s1_admin_edge_local, NOINHERIT/NOSUPERUSER/NOCREATEDB/NOCREATEROLE/NOREPLICATION/NOBYPASSRLS, connection limit 4, senha e validade temporárias |
| HMAC e nonce transacionais | executor NOLOGIN existente prumo_s0_g1_executor_local; mesmas portas assinadas I79/I80 |
| Domínio administrativo | prumo_s1_admin_domain_local I81, sem mudança de owner/grants de dados |
| Constraints diferidas | prumo_s1_professional_validator_local I81, sem mudança de owner/ACL |
| Identidade e competência humana | usuário/sessão GoTrue verificados + cargo Diretor e competência canônica revalidados no SQL |

Login técnico não representa um Diretor, não escolhe ator/sessão e não substitui
HMAC. Chave publishable/anon permanece identificador público do gateway, nunca
segredo administrativo. Nenhum token de serviço com bypass RLS é usado.

## Instalação, material e ativação

O delta SQL recusa ambiente sem opt-in, identidade técnica diferente, versão de
PG ou hashes/configs/owners/ACLs inesperados. A transação cria dois papéis e o
cofre privado `prumo_private.s1_i83_edge_credentials`, inicialmente sem material.
O login começa NOLOGIN e sem senha; não há material estático em arquivo SQL.

Somente USAGE do schema privado, CONNECT do DB local e EXECUTE das duas portas
assinadas I79/I80 são concedidos ao login. Sem DML/SELECT em tabelas de domínio,
Auth, chave, nonce, prévia, auditoria ou I61; sem membership nos executores,
domínio, validador ou custodiante. Defaults públicos do PostgreSQL, incluindo
catálogo e eventuais capacidades TEMP, não são uma concessão de negócio nova.
Não se altera PUBLIC global para retirar direitos de outras frentes.

`integration/i83/provision_local.py` exige DSN de instalação loopback fixo e
opt-in. Gera senha SQL e HMAC independentes por secrets, sem valores fixos.
Antes de enviar qualquer material, a conexão confiável exige uma janela de
logging com SET LOCAL, sem novo grant de parâmetro e com restauração automática
no COMMIT/ROLLBACK. Se essa proteção não puder ser estabelecida, a emissão é
recusada. Não altera logging da aplicação, GUC global ou auditoria de domínio.
Um preflight físico prova ausência de material no log antes da suíte completa.
A senha vira verificador SCRAM no cliente. Verificador e HMAC são transmitidos
por parâmetros vinculados para a própria conexão/transação; blocos anônimos
INVOKER fixos gravam o material e convertem exceções antes de propagá-las. Não
há material em literal SQL transmitido, função privilegiada persistente nova ou
redução do limiar de logging de erros. Falhas reais de senha e de CHECK com bytes
são parte do preflight físico de não vazamento. Persistido no banco, o HMAC real fica apenas no cofre dedicado. Cadastro, validade e chave são
preparados no banco; o servidor define a janela técnica de uma hora do ensaio.
Isso não estabelece política comercial ou prazo produtivo.

A FK existente de nonce/auditoria continua apontando para o cadastro de chaves
original. Para preservá-la, cada key_id novo recebe ali uma **referência inativa
com bytes zero**. Ela não contém o HMAC da Edge e não autentica as portas antigas.
A tabela nova contém o material real, enabled, not_before, expires_at e tombstone
de revogação. RLS só permite a leitura pelo executor HMAC quando session_user é
o login Edge dedicado. O executor pode adquirir FOR SHARE via UPDATE(key_id),
com WITH CHECK(false) impedindo alteração da linha. O login não acessa o cofre.

As mesmas duas funções assinadas escolhem a fonte da chave por session_user:
login antigo continua usando suas chaves antigas; login Edge consulta somente
o cofre dedicado. Não há fallback de chave. Somente o predicado técnico das duas
pontes é adaptado para aceitar a segunda identidade técnica; ACL, owner e todas
as verificações de identidade humana/domínio continuam iguais.

## Custódia local e runtime

Material de execução existe em memória do provisionador/worker e arquivo fora
do Git, dentro de diretório 0700, arquivo 0600. Atualização de arquivo usa criação
exclusiva, NOFOLLOW e replace; não há segredo em argumento de shell, resposta
HTTP, navegador ou documento. Valores não são impressos em sucesso ou erro de
provisionamento. Não há fixture operacional reutilizável com segredo publicado.
Vetores públicos I82 continuam apenas exemplos de codec, nunca chaves instaladas.

O worker recebe PRUMO_I83_DEDICATED=YES e a mesma configuração HTTP I82, agora
com o login próprio. Esse perfil recusa login compartilhado/privilegiado; não
volta silenciosamente ao perfil anterior em caso de falha. Os testes antigos
podem usar explicitamente o perfil I82 para preservar o baseline.

IP Docker fixado no servidor e ajuste temporário de Kong/CORS continuam adaptações
locais da I82, com restauração. Não são configuração hospedada. Não há endpoint
de administração de chaves, novo backend Python ou segunda autenticação.

## Rotação, revogação e resultado incerto

Rotação confiável serializa provisionadores, bloqueia chaves antigas em ordem,
revoga/apaga material antigo, cadastra nova chave e substitui senha/validade SQL
na mesma transação. O worker local é reiniciado com o novo arquivo. Não promete
cutover sem indisponibilidade: worker antigo fica recusado até receber a chave.

FOR SHARE da chave é mantido até COMMIT. Se a operação adquirir a chave primeiro,
a revogação espera a confirmação/rollback; se a revogação confirmar primeiro,
o comando é recusado. Isso não é cancelamento retroativo de operação confirmada.
Além da validade inicial, o SQL revalida a validade temporal após as esperas de
domínio, preservando o recheck original da janela de prova HMAC.

Trocar senha/VALID UNTIL/NOLOGIN controla novas conexões PostgreSQL; isoladamente
não revoga sessões SQL já abertas. A barreira de execução é a chave transacional
revogada/expirada. As duas camadas são testadas separadamente. Uma conexão antiga
não recupera autoridade usando material revogado; o login não pode reativá-lo.

Idempotência continua por Diretor/comando/chave de requisição I79/I80, não por
credencial técnica. Nonce permanece global no mesmo ledger. Trocar credencial
não reaplica operação e não renova automaticamente prévia I80 ou competência.
Timeout/ausência de resposta não prova rollback. Reconciliar a mesma requisição,
com sessão humana/autoridade vigentes e credencial técnica válida; sem retry
silencioso ou bypass quando a alçada humana tiver sido revogada.

## Descarte e provas

No fechamento, retirar o worker e seu ambiente, revogar/apagar material no cofre,
NOLOGIN/PASSWORD NULL, terminar conexões do login, remover arquivo temporário e
verificar catálogo. Manter somente tombstones e referências inativas necessários
ao histórico da transação até destruir a stack com stop --no-backup.

A limpeza lógica não é promessa de sobrescrita forense de páginas, RAM, WAL ou
snapshots. A stack e os volumes são descartáveis; não há backup/retention do
material de credenciais em artefatos. Custódia produtiva exige homologação própria.

Inventários antes/depois/final contêm apenas metadados e ACLs. Provas de limpeza
não incluem key_id/segredo/senha/verificador/JWT. O teste lê logs próprios em
memória para procurar valores de credenciais, sem imprimir ou arquivar esses
logs brutos. Falha de diagnóstico não pode impedir a tentativa de descarte.

## Limites preservados

Sem convite/criação Auth, bootstrap de Diretor, UI, concessões comerciais novas,
chamadas OpenAI/Meta, n8n, backend externo obrigatório, migração hospedada ou deploy.
Revisão de DTO com Frontend continua necessária, sem bloquear este incremento.
F02 mantém seus bloqueios, G01–G06 parciais/G07 pendente. G2/Issue #23 abertos.

TLS, serviço produtivo de segredos, rotação automática/alta disponibilidade,
controle distribuído de abuso, revisão de todo DDL e homologação do Supabase
hospedado não são certificados por este ensaio.
