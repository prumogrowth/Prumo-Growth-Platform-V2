# I81 — relatório de ownership administrativo

27/10/2026, America/Sao_Paulo. Continuidade I80/PR #30, base cfeca5f.
PR experimental #32; contrato em [CONTRATO_OWNERSHIP_V1.md](CONTRATO_OWNERSHIP_V1.md).

## Causa e implementação

I46 exige executor técnico postgres nas escritas de equipe e de seus eventos.
I57/I61 protegem atribuição e prova de exceção de caso; não precisam conceder
esse poder à regularização administrativa. I79 também exige validar no COMMIT,
quando a função DEFINER já retornou ao login SQL sem privilégios de tabela.

O delta transfere somente duas pontes de negócio para
`prumo_s1_admin_domain_local` e o validador de constraint para
`prumo_s1_professional_validator_local`. Ambos NOLOGIN/NOBYPASSRLS e sem membros
executáveis ou CREATE de schema no estado final. O login conserva apenas EXECUTE
assinado; não assume o owner e não recebe DML administrativo direto.

I46 mantém erro, INVOKER e triggers, acrescentando só o owner inacessível do
domínio na whitelist. I57/I61 e demais guards/constraints continuam anexados e
ativos; prova I61 permanece restrita ao executor de casos. Os oito corpos
prerequisitos são conferidos por SHA-256 antes da instalação. Guard, ACL de ponte
ou configuração divergentes são recusados sem aplicar um reparo presumido.

A identidade Auth é consultada por uma função booleana privada mínima,
preservando FOR SHARE no cadastro e rechecagem após espera; a sessão viva usa
CFI-01 já existente. Nenhum segundo catálogo de identidade/cargo/permissão.
HMAC/nonce/CAS/idempotência/auditoria e contratos I79/I80 continuam os originais.
A instalação só muda catálogo/ACL/policies/owners; não regulariza pessoas.

## Arquivos

| Arquivo novo | Função |
| --- | --- |
| `supabase/tests/s1_i81_admin_ownership_local_only.sql` | delta transacional com preflight, owners, ACL e policies específicas |
| `integration/i81/install_local.py` | opt-in e loopback existentes, instalação atômica |
| `integration/i81/prerequisites.json` | fontes e hashes dos oito corpos certificados |
| `integration/i81/catalog.py` | inventário efetivo antes/depois/final e comparação de consumidores |
| `integration/i81/test_provisioning.py` | recusas e rollback integral de DDL |
| `integration/i81/test_cutover.py` | prévia I80 criada antes e aplicada após o cutover |
| `integration/i81/test_ownership.py` | probes de papel/ACL/guards, Auth lock, COMMIT e CFI real |
| `.github/workflows/exp-s0-s1-i81-ownership.yml` | regressões históricas separadas e stack integrada nova |

Nenhum arquivo executável já existente da base I80 ou da S1 original foi
reescrito. As alterações funcionais SQL são um delta explícito no catálogo
**descartável**, não edições das migrations históricas ou cópia de PR completo.
S1 original rechecado em 8780b576, I79 em 8068db1 e I80 em cfeca5f.

## Instalação e privilégios

A transferência usa SET temporário para postgres; PG17 conserva em paralelo a
membership ADMIN-only automática de criação, com INHERIT=false e SET=false.
O catálogo registra grantor/opções separadamente. Isso é competência de
instalação, não membership da aplicação. Não se usa superuser para contornar a
restrição; qualquer membership executável dos novos owners ou concessão a outro
consumidor bloqueia o gate.

Tabelas mantêm owner e RLS. As policies novas são apenas para os NOLOGIN e não
alteram as dos usuários. O domínio lê o contexto administrativo e grava somente
cadastro/estado/cargo, chefia, revogação I61 e registros imutáveis autorizados.
Locks em concessões, casos, atribuições, intake e competência usam UPDATE de ID
com WITH CHECK(false), sem autorizar modificação de linha. O validador só lê e
bloqueia equipe/chefia/competência, sem poder ativar ou reclassificar alguém.

Leitura de `xmin` exige SELECT de tabela no PG17. A lista exata metadata-only de
casos/atribuições é conferida antes desse grant; uma coluna nova recusa a instalação.
Não se retira a proteção ABA. DDL posterior também exige revisão: a checagem não
é um monitor de ALTER TABLE, e SELECT de tabela acompanha colunas futuras.

O domínio não recebe chave, nonce, email, sessões, mensagens, dispatcher,
atribuição, nova exceção, grant geral ou intake. SQL login/anon/authenticated/
service_role continuam sem função privada, tabelas privadas e direito de assumir
executor. Os consumidores antigos são comparados por privilégios efetivos antes
e depois; a perda intencional de EXECUTE implícito do antigo owner postgres nas
três funções transferidas é separada desse aceite.

## Certificação final

**[CI 40543117528 — SUCCESS](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40543117528)**,
no código [4ba266d04b47fcb8036352970456d0dd5b2d09a7](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/commit/4ba266d04b47fcb8036352970456d0dd5b2d09a7),
tree `e3865ca4a5fb8fc76d43c0fb98b20a737854a049`. Jobs integrados
`122326483705` e histórico `122326484256`, ambos SUCCESS.
Início 16:39:51Z, conclusão registrada 16:45:56Z — 13:39:51 a 13:45:56 em
America/Sao_Paulo, 365 segundos entre esses registros. Cleanup confirmado e
nenhum ResourceWarning. O commit documental posterior não muda o código.

| Camada | Resultado |
| --- | --- |
| Recusas/rollback DDL I81 | **6/6**, inclusive grant inesperado e nova coluna sem revisão |
| Cutover com prévia anterior | **1/1**, sessão real do Diretor, mesmo snapshot/sem renovação de prazo |
| Segurança/integração I81 | **14/14**, SQL/GoTrue/PostgREST reais conforme cada cenário |
| I79/G1 após owner restrito | **62/62**, sem reescrever os testes originais |
| I80 após owner restrito | **33/33**, sem reescrever os testes originais |
| Baseline anterior ao delta | G1 36/36, I79 62/62, I80 33/33 |
| CFI/F02 e histórico existentes | 56/56, 19/19 S0 e 19/19 I63 |
| Unitários S0/F02/G1/I79/I80 | 288/288, também executados localmente |
| Unitários nativos S1/catalogo | 179 + 6 I75B + 8 I75C = 193/193 |
| SQL canônico sintético | 34/34 I54/I56/I57/I58/I61 |
| S1 histórico PG17 | I54–I74/I78 e catálogos I46/I48/I75B/I75C PASS |

Os **21 novos cenários** são 6 controles transacionais de instalação, 1 cutover
e 14 probes/fluxos, sem confundir um teste DDL com autenticação de negócio.
Repetições I79/I80 antes/depois são regressões comparativas, não testes inéditos.
O job I78 está no checkout original: seu teste de órfão documenta a lacuna
pré-I79; depois do delta, o validador restrito rejeita órfão no COMMIT.
Não há nova certificação independente I75D/I76 ou percentual de gate operacional.

### Evidência de ownership e segurança

Catálogo passou de **105 para 106 funções** (somente o adaptador Auth mínimo),
**57 triggers e 418 constraints preservados**, policies de 108 para 145,
somente pelos 37 escopos específicos dos dois NOLOGIN. Todos os owners de tabela,
flags RLS e privilégios efetivos dos consumidores originais foram preservados,
com a exceção intencional do antigo EXECUTE implícito de owner postgres nas três
funções transferidas. Nenhum privilégio novo foi dado a consumidor de aplicação.

Os catálogos **after e final são exatamente iguais**, depois de todas as
regressões e probes. Vínculos novos restantes: apenas postgres ADMIN=true,
INHERIT=false, SET=false, grantor supabase_admin. SET ROLE do login SQL para
postgres/executor/domínio/validador falhou efetivamente.

O observador descartável registrou `current_user` do domínio nas duas pontes e
do validador na checagem diferida. Nenhuma escrita administrativa ou validação
profissional observada precisou executar como postgres. O observador foi removido
e o helper original restaurado byte a byte; os catálogos confirmam isso.

Probes mostraram I46 recusando clientes mesmo sob GRANT acidental de INSERT;
negação de chamadas/tabelas privadas e leitura de segredo/Auth; domínio sem
poder criar caso/atribuição/exceção ou alterar concessão/intake/Diretoria;
validador sem DML de estado; RLS bloqueando mutações de colunas concedidas só
para lock; constraints diferidas/rollback; identidade Auth deletada durante
espera; PostgREST sem RPC administrativa pública. A prova I61 continuou false
no domínio mesmo sob EXECUTE e leitura de loja concedidos temporariamente no
probe revertido, com as demais condições da exceção verdadeiras.

CFI-01 após o cutover: Consultor admitido pela I79 sob novo owner recebeu caso
G1 canônico; captura e recheck técnicos passaram, outro Consultor foi recusado
e a revogação de concessão invalidou o recheck. Nenhum resultado foi promovido
a conclusão comercial ou contrato UI ratificado.

[Evidências duráveis, nomes dos testes, ACLs e hashes](evidencias.json).
[Artefato completo dos três catálogos](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40543117528/artifacts/12750878937),
ZIP SHA-256 `4544afb70aee2b0413b5eb4368b796ca50c64d91ab15c862ac2ae106c13e68a5`.

## Tentativas de validação registradas

- [40539838296](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40539838296),
  código `2f96867`: baseline I79/I80 e job nativo passaram; cutover recusado por
  tratar ADMIN-only automático do PG17 como membership executável. O SQL de
  instalação foi revertido integralmente. O catálogo confirmou as opções
  INHERIT=false/SET=false dos vínculos de criação, com grantor supabase_admin.
- [40540907962](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40540907962),
  código `a30b053`: regressões passaram, mas o preflight novo tinha uma expressão
  CASE sem parênteses no IF PL/pgSQL. Corrigida a sintaxe; parser PG17.7/pglast
  7.21 verificou as 48 instruções, cinco blocos e adaptador Auth antes de repetir.
- [40541862881](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40541862881),
  código `28c1244`: cinco controles DDL passaram; instalação confirmou, mas APPLY
  devolveu 42501 em atribuicoes_humanas. Causa: SELECT por coluna não permite
  ler xmin no PG17, mesmo abrangendo as colunas usuais. Ajustado somente SELECT
  das duas tabelas metadata-only, com guarda de formato exato e teste de coluna
  nova. Mantidos CAS/ABA, proibição de DML e todas as projeções do contrato.

Nenhuma dessas execuções parciais certifica ownership funcional. Cada stack foi
removida, sem rollback ou alteração em banco real/hospedado. Não houve concessão
ampla ao login nem remoção de guard para corrigir as falhas.

## Reprodução descartável

Usar o workflow próprio em stack nova e não vinculada, PG17/GoTrue/PostgREST,
CLI 2.84.2 e driver psycopg 3.2.9, preservando os opt-ins/hashes da I80. A sequência
I81, depois de todo bootstrap e baseline I80, é:

```bash
PYTHONPATH=. python3 integration/i81/catalog.py before
PYTHONPATH=. python3 integration/i81/test_provisioning.py
PYTHONPATH=. python3 integration/i81/test_cutover.py
PYTHONPATH=. python3 integration/i81/catalog.py after
PYTHONPATH=. python3 integration/i79/test_professionals.py
PYTHONPATH=. python3 integration/i80/test_regularization.py
PYTHONPATH=. python3 integration/i81/test_ownership.py
PYTHONPATH=. python3 integration/i81/catalog.py final
```

Requer `PRUMO_I81_DISPOSABLE_TEST=YES`, além dos opt-ins antigos. O cutover faz a
instalação uma vez dentro da prova, não deve ser precedido de instalação manual
do mesmo delta. O script install_local é alternativa para ensaio de implantação,
com as mesmas precondições. Reinstalação sobre estado já alterado é recusada.
Cleanup da stack usa `supabase stop --no-backup`, inclusive em falhas.

Os catálogos não contêm dados Auth/negócio nem segredos. pg_depend é parcial para
PL/pgSQL e não substitui os probes físicos. Artefatos completos têm retenção de
14 dias; a evidência durável registra hashes e recorte de owners/grants no repo.

## Limites e próxima execução

Continua sendo SQL/Python experimental de laboratório, sem endpoint, alteração
hospedada ou migração produtiva. Owners postgres de G1/I54/I55/I62 e de outras
rotinas comerciais não foram incorporados a um papel administrativo geral.
Os helpers Auth mínimos continuam postgres-owned, com EXECUTE privado restrito.
Privilégio de instalação/custódia e operação continuam responsabilidades distintas.

Permanecem decisões administrativas da I80: cargo/chefia explícitos, revisão de
perda de acesso I61 e tratamento de vínculos incompatíveis, sem promoção em lote.
Não há nova decisão comercial para trocar um owner técnico por esse domínio.
G2 operacional continua parcial; falta borda/API/UI, provisionamento/retenção e
homologação. F02 G01–G06 continuam parciais e G07 pendente, sem repetir auditoria
ou H01 e sem ratificação de revisão comercial.

Após ownership conclusivo, próxima execução: borda administrativa Edge Functions
**local**, usando contratos I79/I80, mesma autenticação GoTrue e autorização SQL;
sem iniciar migration hospedada, chamada comercial ou deploy. ADR Supabase +
servidor→OpenAI respeitada; SQL não passa a chamar OpenAI.

## Registro de fontes e infraestrutura

PR #30/I80 e branch original S1 sem avanço posterior no início. Listagem de
branches/Issue #23 não encontrou outra implementação equivalente desta missão.
Não houve incorporação de PR candidato inteiro, escrita na S1 original ou nova
auditoria F02. Arquitetura ADR Supabase/Edge local mantida.

Changelog Supabase retornou HTTP403 pela política de rede; a documentação atual
de RLS foi consultada pelo MCP. CLI/driver foram mantidos fixados na infraestrutura
certificada. Parser PG17.7 ficou somente em /tmp; não se adicionou dependência ao
backend nem se reconstruiu o projeto. Nenhum banco hospedado foi consultado.

Sem merge, deploy, credenciais reais, migration hospedada, clientes reais ou
chamadas OpenAI/Meta/comerciais. Issue #23 continua aberta pela integração
operacional G2; este resultado libera somente a próxima preparação local.
