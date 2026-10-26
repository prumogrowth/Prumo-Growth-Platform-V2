# S0 — auditoria de retomada e núcleo operacional

25/10/2026, horário de São Paulo (runs também datados 26/10 em UTC).
Repositório: `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`.

**Parecer: núcleo avançado em laboratório, ainda não operacional.** Aprovação de
SQL, concorrência, GoTrue local ou transporte loopback comprova aquele recorte;
não comprova integração hospedada, autorização comercial ou APIs externas.

## Recuperação e branch própria

Base da fundação S0: `75095fe9b6050c704df37c663bb92595bc6513b6`.
Nova branch `feat/s0-auditoria-nucleo-operacional-20261025`, em worktree separado.
A branch CI anterior foi preservada. Não houve cherry-pick, merge, sobrescrita de
outra frente ou reinício de esquema. As branches derivadas abaixo contêm trabalho
não integrado; a fundação não deve ser tratada como cópia de todos esses avanços.

| Branch | SHA observado | Papel/estado |
| --- | --- | --- |
| `main` | `dace737ab7afb7ae3f5a3a6f5cb522e6def8b43a` | Commit inicial; não representa produto integrado |
| `feat/s0-fundacao-prumo` | `75095fe9b6050c704df37c663bb92595bc6513b6` | Fundação, C01/C02/C04/C07/C08 sintéticos, HMAC/ACL, política candidata e precedência S0-043/044/045 |
| `feat/s0-cfi01-f03-auth-preflight-20261020` | `948891714f632adb6179cf3a11f362a6eb914f91` | Recibo atômico de conclusão, captura/recheck e ponte F03 com contrato pendente |
| `coord/s0-openai-cfi01-c09-20261019` | `d1e1ebefb7bf1bef24a18d8f24078a381e7c1647` | Coordenação de contratos CFI-01, CF-OP-02/C09; não integração operacional |
| `feat/oai-s0-f03-history-port-20261023` | `26cb7d73beb10a08e0f7dc9c3a5c287d183db67f` | PR #1 Draft; histórico, HMAC, CAS, mídia sintética, minuta e reconciliação C08 local |
| `feat/wa39-s0-meta-forensic-bridge-20261023` | `54d790dc7eb2cf73c564ad0cfea0496554bf9287` | PR #2 Draft; ponte forense WA39–66 PG17/loopback, sem ACK/Graph |
| `docs/whatsapp-meta-concessionária de demonstração-poc-20261017` | `d9cd4b8f1de222324c92f2fec8053b0b91dcfe5d` | Contratos Meta até WA38 e matriz de aceite WA36/37 |
| `feat/s1-002-equipe-prumo` | `3cfa2b77c733fd36f1284e3adfd45fa198720162` | S1 até I73; fila/atribuição/escopo e segurança de exportação em laboratório |
| `feat/frontend-plataforma-visual` | `6d245d11e23bb3b0918d8594e87d242f2fbad815` | Interface sintética até FV-UI-057; não conectada ao núcleo |
| `feat/s2-openai-adapter-sintetico` | `ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c` | Validação/propostas locais, sem autoridade S0 ou API OpenAI real |
| `docs/cf-op-02-cadeias-contextuais-20261018` | `ce7bbdd8171c2a28903b60d9c2b2ade4584b91e8` | Contrato de cadeias, não runtime |
| `exp/ci-s1-consolidacao-20261025` | `31ac07bf860d67ff935fa0c96c1cc00224f06f8b` | Experimento CI independente; não base de S0 |

Esses SHAs são um checkpoint de leitura, não tentativa de congelar outras frentes.
Referências históricas a PRs/issues de `prumogrowth/Prumo-Growth---Platform`
não são os mesmos números do repositório atual. A única issue aberta encontrada
na consulta inicial foi #3, de CI S1; não é backlog operacional S0.

## PRs pendentes e evidência atual

- [PR #1](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/1):
  Draft contra `feat/s0-cfi01-f03-auth-preflight-20261020`. Head `26cb7d7`.
  [Run #40257851993](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40257851993)
  SUCCESS no SHA exato. Logs lidos: 84 testes S0 + 514 F02/F03 Python e 269 Node.
  São suítes distintas, não 867 jornadas comerciais. Inclui sequência local
  S0/S1/F03/C08 e revisão de cadeia legada; não autoriza agendamento ou envio.
  O topo da descrição ainda cita checkpoint anterior de 585 Python: preferir
  SHA, logs e código do head em vez de assumir que o texto resume tudo.
- [PR #2](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/2):
  Draft contra `feat/s0-fundacao-prumo`. Head `54d790d`, WA66.
  [Run #40258058272](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40258058272)
  passou no SHA exato; job `121364099115`. Documento WA66 prevê 775 verificações
  acumuladas WA39–66; não converter essa soma em casos de produto ou em aceite
  dos 24 critérios externos WA37. O título/descrição ainda destacam WA60/65.
  A evolução WA67 é da frente Meta; não foi duplicada nesta retomada.

Não havia outros PRs abertos na consulta inicial. A S0 não tem PR atual de
fundação para `main`; isso é estado de governança, não motivo para abrir integração
ou promover as duas branches Draft automaticamente.

## Contratos recuperados e precedência

1. `docs/DECISOES_E_GATES.md`, S0-043/044/045: Diretor/Gestor/Consultor são nomes
   de exibição; identificadores de autorização legados permanecem. Pausa de intake
   não suspende conta. Casos do pausado sem contato comprovado só redistribuem
   dentro da equipe; novos leads podem ir a qualquer equipe elegível da loja;
   fila sem titular exige gestores autorizados e atribuição atômica. IA não
   conhece disponibilidade, equipes ou permissões e não decide destinatário.
2. CF-OP-02 v0.1: conclusão humana, janela Meta e silêncio após template final
   são três marcos diferentes. C09 humano ainda exige matriz de fase/status
   ratificada; banco/vendido/perdido não podem ser inferidos por silêncio.
3. CFI-01 e `S0_CFI01_F03_SNAPSHOT_METADATA_RATIFICATION_GATE_2026_10_21.md` na
   pré-validação: recibo interno captura/revalida em transação S0 autenticada.
   `VERIFIED_CONTRACT_PENDING` não autoriza F03 nem escrita. Versão de ciclo
   não é versão de caso; formulário/catálogo não existem nesse recibo e não
   podem ser inventados pelo cliente, pelo modelo ou por tradução de nomes.
4. Contratos WA36/37: principal máquina independente, assinatura/proveniência,
   segredo segregado, binding por loja/tentativa, nonce atômico, locks, RLS,
   dedupe, ACK, retenção e revogação precisam de aceite interfrentes. Os 12 pares
   P/N propostos não foram homologados só porque testes do pacote passaram.
5. S1 I73: caminho de exportação restringe SQL `authenticated` e valida sessão
   em GoTrue local, mas declara risco restante de login SQL comprometido e
   necessidade de prova independente/anti-replay. Não substituir por adaptador
   S0 antigo de privilégios amplos nem dizer que a API produtiva está pronta.

## Pendências objetivas para operação

| Prioridade | Pendência e impacto | Donos / próxima evidência necessária |
| --- | --- | --- |
| P0 | Contrato canônico UI→S0→F03, IDs, versões de caso/ciclo/atribuição/ficha/catálogo, corte e schema OAI-05/07. Fixtures divergentes não são adaptadores de produção | S0+S1+FV+OpenAI: versão ratificada e prova ponta a ponta contra a mesma base, com revogação/mensagem nova/CAS |
| P0 | Backend operacional de identidade, sessão e autorização mínima. Wrappers comerciais S0 ainda usam `SECURITY DEFINER postgres`; capacidades de 037D/F são mocks, não emissor operacional | S0+Infra: credenciais separadas, assinatura independente/nonce, executor mínimo, auditoria e recuperação transacionais sob RLS, sem RPC privilegiada pública |
| P0 | S0/S1/FV não estão integradas na mesma aplicação/base; provas de fila, exceção por caso, handoff e exportação estão em branches/fixtures próprias | S0+S1+FV: reconciliar concessões e assinaturas; testes positivos/negativos de sessão, loja, troca de titular e privilégio em todas as superfícies |
| P0 | C04 pré-humano bloqueia ciclo humanizado; minuta/reconciliação F02 e cancelamento C08 continuam de revisão/local. Cancelamento Meta de tentativa reservada é desconhecido | S0+OpenAI+Meta: contrato pós-humano separado, autorização humana real e prova de cancelamento externo; nunca ressuscitar plano antigo nem afrouxar C04 |
| P0 | Transporte Meta externo, onboarding/canais, principal M2M, ACK durável, política de retry e prova real de envio/entrega não estão concluídos | Meta+S0+Infra: ratificar WA36/37, titularidade por concessionária, segredos e testes em ambiente explicitamente autorizado |
| P0 | Minimização/LGPD, consentimento, templates/categorias, retenção/exclusão, fonte de catálogo e finalidade não homologados para dados reais | Produto/Jurídico+S0+Meta+OpenAI: decisões versionadas e testes de acesso/expurgo, sem promover mídia sintética a prova real |
| P1 | Plano de integração e migrations entre branches, dependências/nomes, rollback e bootstrap ainda não reconciliados | Donos das frentes: manifestos por SHA, revisão de diffs/ordem/ACL e integração supervisionada futura em branch própria; nenhuma aplicação hospedada nesta etapa |
| P1 | Observabilidade durável, recusas sanitizadas, backup/restauração e falhas/recovery do serviço completo não comprovados | S0+Infra: auditoria consultável, alertas, ensaio de restauração e resposta a commit incerto sem retry cego |
| P1 | UI ainda sintética; limites D2/D3/D4, anexos, prova de contato e estados comerciais exigem integração real autorizada | S0+S1+FV: teste de jornada com sessão e autorização efetivas; não contar leitura, tentativa ou mensagem da IA como contato humano |
| P1 | instituição financeira/remessas/resultado comercial e eventual orquestração n8n não conectados | Produto+Banco+S0: protocolo e prova humana validados; decidir backend/n8n sem inferir que mocks concluíram integração |

**Já concluído no escopo de laboratório e não refeito:** fundação SQL/RLS,
C01/C02 e concorrência, C04 opt-out, C07/C08 sintéticos, identidade GoTrue local,
HMAC/nonce e regressões de ACL, recibo CFI-01, CAS e provas F03 derivadas, ponte
forense WA39–66, fila e escopos S1. Não se criou substituto para esses módulos.
A regressão executada nesta branch serve para validar a correção, não para
anunciar novamente os incrementos históricos como novos.

## Implementação segura desta retomada

Reprodução em `backend/operator_distribution_policy.py`: candidato com
`operator_ref=123` junto de ID textual podia provocar `TypeError` no `sorted`;
`CaseSnapshot` sem identificador/loja podia receber classificação de caminho
manual. Dataclasses não validavam os tipos em runtime.

Validação estrutural agora recusa referências não textuais/vazias, grants
malformados e flags que não sejam booleanos. Não normaliza IDs, não cria grants,
não executa transação e não permite escrita. Tupla de grants vazia é válida e
continua exigindo autorização específica por caso; lista/string não é tratada
como ausência legítima de grant. Versões/identidade ainda precisam vir de S0
confiável e ser revalidadas na transação operacional — este planejador não faz
isso e continua candidato puro. Preservadas as regras de mesma equipe, contato
iniciado/desconhecido, conta ativa, intake, caso terminal e falta de substituto.

Quatro métodos novos de regressão cobrem entradas adversariais em subcasos.
A suíte nova falha contra o módulo original e passa contra a correção. Não é
vulnerabilidade comprovada de acesso ao banco, pois o planejador não tem escrita.

Novo workflow `s0-audit-isolated.yml` roda só nesta branch: mantém o runner SQL
S0 existente e PostgreSQL 17. Não modifica os workflows oficiais e não dispara
CI alheio. Não altera migrations, RLS, credenciais ou contratos operacionais.

## Validação desta branch

- Python: **38/38 PASS**, antes 34 testes existentes + quatro métodos novos.
- Runner `scripts/run-s0-local.sh`: **PASS integral** em PostgreSQL **17.11**
  descartável, incluindo SQL e todas as corridas existentes até WA14C.
- O cliente `psql` do host não estava instalado; o runner utilizou wrapper
  `docker exec -i ... psql`, com checkout montado somente leitura. O servidor
  estava em container dedicado `--network none`, sem porta pública. Mesmas
  migrations/fixtures/scripts originais, banco `prumo_s0_test_audit` exclusivo;
  container removido após conclusão. GoTrue/PostgREST e APIs externas não foram
  repetidos localmente; este delta não modifica autenticação ou SQL.
- Commit executável: `4ea1fe87107f435635a0c7cf650b5b4097b01241`.
- CI GitHub desta branch: **SUCCESS** no SHA executável exato,
  [run #40258537422](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40258537422),
  job `121365581736`: 38/38 Python e runner SQL/concorrência integral aprovados.
  Logs de contagem e marcadores foram lidos; nenhum retry necessário.
- Evidências sanitizadas e manifesto: `S0_EVIDENCIAS_20261025.json`.

## Limite de avanço

GO para correções isoladas e revisão de contratos; NO-GO para declarar núcleo
operacional. Próxima etapa material: ratificação do contrato canônico e revisão
da fronteira de execução/autorização, aproveitando os módulos existentes.
Não há base para inventar política pós-humana, permissões M2M ou consentimento.
Instalação no Supabase hospedado segue reservada à fase de integração geral
explicitamente autorizada. Sem merge, deploy, mudanças em main ou nas frentes
alheias, contato com clientes, Meta, OpenAI paga ou Banco.
