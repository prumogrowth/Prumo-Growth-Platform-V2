# G1 — encaminhamento manual da fila sem titular — candidato interno v1

Referência: Issue #17; data da entrega: 2026-10-26 (America/Sao_Paulo).
Escopo executável: PostgreSQL 17, GoTrue e PostgREST descartáveis. Não é endpoint
público, migration hospedada, autorização de envio ou homologação da UI.

## Recuperação e decisão de reutilização

- S0/PR #18: `88af4aea3aeb2c403bab4c078fdc04d560f2cba0`, preservado como base.
  O código CFI-01/PR #13 e o registro F02 não foram reimplementados.
- S1: `b71ebf4479c9a0a3527519471cca04ec7e178e18`, consultado sem escrita.
  I76: código `781fc839165ae3e420ff6b435f3e1f95b3f2db5a`, CI
  [40413807995](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40413807995)
  concluído com sucesso, incluindo 7 cenários I76. Dois Gestores podem compartilhar
  a fila da loja e disputar assunção pessoal; isso não implementava encaminhamento.
- Busca antes de implementar: inventário de declarações SQL/backend em 18 branches
  não Meta, registrado em `integration/g1/equivalence_scan.json`. Há distribuição,
  assunção e movimento I61 de caso já atribuído; não foi localizada porta canônica
  equivalente ao encaminhamento solicitado. Protótipos de fila não substituem I54.
- Contrato funcional S1-002 §§4–5 e Issue #17 já distinguem as três operações e A2.
  A implementação aplica essas regras; não cria regras de venda ou novas permissões.
- A frente `META-S0-TEMPLATE-CATALOG-05` não foi consultada nem incorporada.

Reuso físico, com SHA-256 conferido antes de instalar: 27 fontes SQL S1, listadas
em `integration/g1/s1_sources.json`. I54 fornece a fila e distribuição; I55 a
assunção assinada; I56 serialização por contato e reconciliação; I57/I58 os guards
de grant/Gestor; I61 a exceção canônica; I62 sua revogação assinada; I63 a RLS.
O carregador existente de histórico ganhou somente a opção de manifesto interno.

## Entrada interna e identidade

Porta: `S0ManualQueueHandoffLocal.execute(authorization, payload)`, reutilizando
uma instância real de `S0CFI01AtomicCommandsLocal` e seu verificador GoTrue.
Formato candidato `s0.g1.manual-queue.v1`, identificado pela classe/assinatura SQL
e pelo domínio HMAC; o JSON não tem seletor arbitrário de versão.

| Campo exato | Fonte e validação |
| --- | --- |
| `loja_id` | UUID canônico, não nulo; autorização é conferida no banco |
| `ciclo_id` | UUID canônico; precisa pertencer à loja e a lead com sinal na fila I54 |
| `consultor_id` | UUID canônico; destino diferente do Gestor e pertencente à própria equipe |
| `versao_esperada` | inteiro estrito `1 <= n < 9223372036854775807`, CAS da **fila I54** |
| `chave_idempotencia` | 8–128 caracteres ASCII `[A-Za-z0-9._:-]` |

Não são aceitos campos extras, ator, sessão, papel, exceção pré-fabricada ou versão
de caso fornecidos pelo cliente. Ator e `session_id` vêm do Bearer validado no
GoTrue real. A transação revalida `auth.sessions`, `not_after`, equipe ativa e
concessão vigente do Gestor à loja. A versão da fila não substitui as decisões
pendentes UI/S0 D1–D4 sobre versões de caso/ciclo.

HMAC SHA-256 com domínio `s0-g1-manual-queue-local-v1` vincula ator, sessão, loja,
ciclo, destino, versão, chave de idempotência, ID de chave, emissão e nonce UUID.
Janela: 30 segundos passados, 5 segundos de tolerância futura, com nova checagem
ao final dos locks. Reusa a chave e a tabela de nonces CFI-01 existentes, sem
aceitar MAC CFI/F02 como prova G1. Senha SQL isolada não autoriza o comando.

## Atomicidade e autoridade após espera

Ordem local da nova operação:

1. Chave de assinatura `FOR SHARE`, inserção do nonce, sessão viva `FOR SHARE`.
2. Ciclo `FOR SHARE`, lead da loja `FOR UPDATE`, fila canônica `FOR UPDATE`.
   O ciclo vem antes do lead para respeitar o escritor de status I56; o lock
   `KEY SHARE` de FK usado nos caminhos antigos permanece compatível.
3. Linhas de equipe do Gestor e destino em ordem UUID `FOR SHARE`, depois leitura
   do estado ativo; relações do destino ordenadas por ID, depois própria equipe.
4. Guard I58 do Gestor/loja; grants do destino ordenados por ID. Intake é lido sob
   a mesma linha de equipe que `s1_definir_intake` usa como barreira de escrita.
5. Repetição de I58 e da sessão após todas as esperas: expiração pelo relógio do
   servidor também recusa. Relação encerrada ou equipe inativa não é elegível.

Não se filtra estado elegível antes de adquirir os locks das linhas existentes.
O destino não pode ser o próprio Gestor, Responsável da plataforma ou chefe de
equipe ativa. Grant vigente na loja com papel diferente de operador não é usado
para conceder exceção de Consultor. A2 impede **nova atribuição** a destino com
intake pausado, mesmo com exceção anterior. Pausa não revoga acesso ao caso antigo.

Para uma nova solicitação: exigir fila pendente e versão igual, ausência de caso
para o mesmo contato/loja (regra canônica I54/I56), status humano ainda válido.
Criar caso e reservar UUID da atribuição. Com grant vigente de operador, inserir
atribuição normal sem exceção. Sem esse grant, inserir exceção I61 vinculada ao
caso e ao UUID reservado, depois atribuição. A FK I61 já é `DEFERRABLE INITIALLY
DEFERRED`; os triggers I52/I57/I61 originais verificam a prova durante o INSERT.

Na mesma transação: evento I61 `CRIADA` quando aplicável, fila atribuída com versão
incrementada, evento **`ENCAMINHADO`** no ledger I54/I56 existente, recibo de
idempotência e auditoria ligada ao nonce. Não inserir `vinculos_papel_escopo`.
Falha de exceção, atribuição, auditoria, constraint adiada ou validação da resposta
antes do COMMIT impede retorno de sucesso e reverte os fatos quando o rollback
é confirmado. Perda de conexão durante COMMIT retorna `UNAVAILABLE`, sem afirmar
que o resultado incerto foi desfeito: retentar a mesma chave para reconciliação.

O lock comum do lead/fila faz a nova operação competir com os comandos originais
de distribuição/assunção. O vencedor define o caso; o perdedor encontra CAS
obsoleto. Não há transferência silenciosa nem substituição do titular existente.
Isso é uma ordem local comprovada para os escritores testados, não certificação
global de todos os módulos ou dos contratos Meta/S0.

## Idempotência, resposta e recusas

Escopo durável: `(gestor_id, concessionaria_id, chave_idempotencia)`. Vincula ciclo,
destino e versão original. Retentativa com nova prova/nonce, mesmo escopo e payload
retorna os mesmos IDs; não cria outro caso, atribuição, exceção ou evento de fila.
Acrescenta somente auditoria da leitura idempotente e nonce. Mudança de payload
gera conflito. Retentativa continua sujeita à sessão, equipe, grant, intake e
atribuição/exceção vigentes; não reativa exceção revogada nem alonga sua validade.

Resposta técnica com nove campos exatos: `outcome`, `request_id`, `store_id`,
`cycle_id`, `consultant_id`, `case_id`, `assignment_id`, `exception_id` (nulo no
caminho normal), `version` (versão original + 1). O adaptador confere tipos, UUIDs,
escopo e versão antes do COMMIT, preservando o princípio do PR #13.

| Estado | Significado |
| --- | --- |
| `MANUAL_ASSIGNED` | caso/atribuição foram criados e confirmados |
| `ALREADY_MANUAL_ASSIGNED` | mesma solicitação já confirmada, ainda autorizada |
| `INPUT_REJECTED` | formato/versão/chave inválidos |
| `DENIED` | identidade, sessão, concessão ou autoridade insuficiente/revogada |
| `DESTINATION_INELIGIBLE` | destino próprio/equipe incorreta ou papel incompatível |
| `INTAKE_PAUSED` | A2 bloqueia destino, inclusive retentativa do comando |
| `STALE` | fila ou atribuição mudou; não executar nova atribuição automaticamente |
| `IDEMPOTENCY_CONFLICT` | chave já vinculada a outra solicitação |
| `ALREADY_OWNED` | caso já existe embora a fila apresentada pareça pendente |
| `UNAVAILABLE` | falha técnica, timeout, deadlock ou confirmação desconhecida |

Não há retorno de JWT, HMAC, segredo, telefone ou corpo de mensagem. Recusas são
tipadas no adaptador; auditoria durável de sucesso/replay é transacional. Não se
promete registro durável de uma recusa dentro da transação abortada.

## Privilégios e limitação explícita de provisionamento

Instalação restrita a opt-in descartável, PG17 e pré-requisitos canônicos.
O login SQL existente só ganha EXECUTE na porta assinada. `anon`, `authenticated`
e `service_role` não podem executá-la. A nova role executora é NOLOGIN, NOINHERIT,
não superusuária e sem BYPASSRLS; não há membership permanente para o login.
Grants de CREATE e membership de instalação são temporários na transação DDL.
Tabelas privadas de recibos/auditoria usam RLS e bloqueio de alteração/remoção.

**Limitação preservada:** os triggers/commands canônicos I57/I61 exigem
`current_user='postgres'`. Assim como I55/I62, G1 usa ponte privada estreita owned
por `postgres`, inacessível diretamente ao login, e entrada assinada owned pela
role restrita. Não se alteraram os guards S1 para contorná-los. Isso não certifica
ownership integral de negócio com privilégios mínimos para produção; separar
essa autoridade exigirá trabalho coordenado S0/S1 e nova certificação. Não usar
a fixture como migration hospedada nem como comprovação desse gate de produção.

## Arquivos e retomada da S1

- `backend/s0_g1_manual_queue_local.py`: adaptador autenticado interno.
- `supabase/tests/s0_g1_manual_queue_local_only.sql`: delta SQL experimental.
- `backend/tests/test_s0_g1_manual_contract.py`: validação de compatibilidade.
- `integration/g1/`: provas GoTrue/PG, manifesto, busca de equivalência e runner
  das regressões SQL originais S1.
- `integration/history/prepare_s1_profile.py`: opção de manifesto; padrão anterior
  preservado.
- `.github/workflows/exp-s0-g1-manual.yml`: execução somente na branch experimental.

A S1 pode revisar a porta e reproduzir o workflow sem reimplementar distribuição,
assunção ou exceções. Em checkout descartável desta branch, instalar as dependências
e seguir exatamente a ordem do workflow: stack nova, regressões S0, checkout S1
no SHA fixado, carregador com `--manifest integration/g1/s1_sources.json`, perfil
I63, instalação do delta G1, cinco aceites SQL originais e suíte G1. Os aceites
antigos assumem tabela I61 sem dados alheios; executam após o novo DDL, antes dos
dados G1. A suíte gera chaves/credenciais
descartáveis em memória; I22 exige `SET ROLE` explícito do custodiante para prepará-las.
Não copiar dados, chaves ou logins para serviço hospedado.

O delta a revisar para futura integração é a operação, seus dois ledgers privados
e a inclusão de `ENCAMINHADO` no check existente, preservando todos os eventos.
Recertificar contra o HEAD S1 se avançar além do SHA fixado. Nenhuma integração
automática foi realizada na branch S1.

Continuam gates separados: contrato público/UI e sua versão, provisionamento
hospedado, primeiro contato humano comprovado, indicadores, CFI/F03 para Consultor
sem grant geral, transferência de caso atribuído e Meta. O sucesso G1 confirma
atribuição técnica; não confirma contato, envio, agendamento ou venda.
