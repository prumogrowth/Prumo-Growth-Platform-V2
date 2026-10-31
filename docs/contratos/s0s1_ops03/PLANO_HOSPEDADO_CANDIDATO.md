# OPS-03 — compatibilidade experimental e limites da operação hospedada

30/10/2026, America/Sao_Paulo. Somente laboratório sintético descartável.
Sem instalação, diagnóstico ou ato administrativo no Supabase hospedado.

## Decisão preservada

O proprietário ou humano expressamente autorizado opera no ambiente administrativo
Supabase; atualmente o responsável é o proprietário. Acesso ao Dashboard não é
automaticamente autorização organizacional. Nenhum módulo na Prumo, API/Edge de
Diretores, executor MCP/IA ou processo operacional automatizado é criado.

Base OPS-02: 7d3232f59aab35265c3aa7fb5ab5ab2f06d5d047, árvore
574c69e6c232c7ebb1e8719721fb8283c439dbbe, descendente direto do checkpoint
I86/CM-01 a0c4eaf2720bd6cf2bd756544498f8f185f005fc. Os dois worktrees e todas
as fontes, migrations, gates e evidências anteriores permanecem intactos.
Branch exclusiva: exp/s0-s1-ops03-hosted-parity-20261030.

## Implementação e alcance real

hosted_compat_v1.json separa contrato, evidência física, documentação, hipóteses
hospedadas e decisões humanas. Nenhuma evidência local homologa produção.

diagnostic.sql executa BEGIN READ ONLY, consulta catálogos e devolve versão,
principais SQL, objetos/colunas esperados, constraints, trigger profissional,
privilégios efetivos, memberships técnicos e propriedades das rotinas privadas.
Não lê linhas de usuários, sessões, competência ou negócio; não exporta senhas,
tokens, corpos de funções ou dados pessoais. Não concede autorização. O teste
físico confirma a transação read-only. A execução hospedada não ocorre nesta missão.
Resultados ausentes/incompatíveis são bloqueios a investigar, não autorização para
adaptar o banco real automaticamente. Exposição REST/GraphQL e versão GoTrue não
podem ser completamente inferidas desse SQL e ficam explicitamente não verificadas.

hosted_candidate.sql é um **adaptador de controle laboratorial**, não uma versão
instalável em produção. Suas quatro rotinas INVOKER no schema prumo_ops03_manual
mantêm search_path vazio e delegam ao núcleo I86 intacto. Instalação e todas as
chamadas passam pelo guard original: PG17, postgres/postgres, READ COMMITTED e
marca I84 de banco descartável. Sem o núcleo/guard, a instalação aborta antes de
criar o schema. Não há opção, parâmetro ou variável para habilitar perfil hospedado.

Assim são reaproveitados integralmente CAS, locks, precondições de identidade,
idempotência, transação/auditoria, REVOKE atômico de laboratório e reconciliação.
O adaptador não modifica nem substitui funções I86. Testes conferem seus corpos,
ACLs e propriedades antes/depois, além do catálogo herdado I81/I83.

APPOINT continua recusando Gestor/Consultor ou ator incompleto. REACTIVATE exige
novo ato explícito do mesmo Diretor histórico. Vários Diretores são permitidos.
Não há quórum, segundo aprovador, mandato, limite numérico ou sucessão automática.
I85 não é reutilizado e seu journal não pode surgir no laboratório.

## Bloqueio técnico que a missão não mascara

O REVOKE do controle ainda faz o corte de auth.sessions pela implementação I86,
somente no banco descartável. **Não foi implementado REVOKE hospedado suportado.**
Uma cópia desse adaptador no hospedado não resolve o problema e não é autorizada.

A documentação descreve logout global do Auth por chamada independente. Ela não
documenta participação na transação PostgreSQL já aberta pelo operador. Os novos
ensaios medem duas propriedades, sem fornecer um executor bifásico:

1. Logout Auth confirmado pode sobreviver ao rollback de uma transação separada
   da competência. Logo, essa composição não tem a garantia atômica do I86.
2. Competência retirada pode negar a operação mesmo enquanto a sessão ainda existe.
   Esse resultado não significa que o corte de sessões já foi concluído.

Esses updates de competência existem apenas como fixtures de contraexemplo,
isolados por alvo sintético. Nunca são apresentados como atos I86 auditados ou
procedimento operacional. A revogação realmente implementada continua sendo a
do núcleo certificado e mantém sua garantia. Nenhum teste herdado é removido.

Logout global retira refresh tokens das sessões existentes; não é banimento nem
impede por si só novo login. JWT emitido pode continuar não expirado. CFI/I79/I80
devem continuar verificando sessão viva e competência canônica. A nova autenticação
não reativa competência e REACTIVATE não restaura sessões antigas.

Não se afirma impossibilidade universal de qualquer mecanismo futuro: a paridade
de uma interface suportada hospedada **não foi comprovada**. Também não se usa a
ausência de documentação como prova de proibição de todo DML em auth.sessions.
O changelog de schemas gerenciados impõe restrições específicas de DDL e DML de
tabelas de migrations; não estabelece sozinho suporte ao algoritmo I86 completo.

## Privilégios e canal humano futuro

PUBLIC, anon, authenticated, service_role, login Edge, logins técnicos e owners
ordinários não recebem USAGE/EXECUTE no adaptador. Testes verificam ACL efetiva,
membership, owners, chamadas SQL sob papéis restritos e RPC com Diretor, Gestor,
Consultor e service_role. Claims/metadados não mudam essas negativas.

As credenciais comuns não administram Diretores. Custódia do acesso PostgreSQL,
PAT/OAuth/MCP, conta nominal, MFA e autorização do humano são barreiras externas.
O banco não distingue pessoa de programa usando a mesma credencial privilegiada.
Nenhuma conta real é escolhida, criada ou acessada. Os tokens dos ensaios existem
somente em memória na stack loopback e são retirados com ela, sem logs sensíveis.

Uma futura variante hospedada necessitaria decisão explícita de guard e privilégios
compatíveis com o principal real do SQL Editor. Não basta remover a marca I84 ou
aceitar postgres/dashboard_user por conveniência. Grants de negócio e owners
ordinários não podem ser ampliados para obter sucesso.

## Procedimento futuro condicionado à homologação

O roteiro mínimo continua sendo operação humana no SQL Editor: pré-inspeção de
UUID/estado, ato individual com CAS e evidência, transação completa em uma submissão,
confirmação de COMMIT e nova leitura de reconciliação. Submissões separadas do Editor
não devem presumir a mesma conexão. Timeout exige reconciliar o mesmo ato, sem retry
automático. Falha de auditoria/constraint não é sucesso.

O registro nominal do Dashboard ajuda na rastreabilidade, mas referência declarada,
digest e principal SQL não comprovam sozinhos presença humana. A custódia externa
do ato e a política de retenção precisam de confirmação do proprietário. O OPS-02
continua restrito a documentos sintéticos FORMALLY_VALID_UNTRUSTED.

## Testes e reprodução

Localmente, sem dependências nem serviço: executar os testes de escopo/artefatos e
a regressão offline OPS-02 em Python normal e otimizado, com -B. O gate --candidate
aceita somente os dez arquivos novos pendentes sobre a base. O gate padrão exige
um commit atômico e checkout integralmente limpo. Conferir também delta, modos,
blobs e SHA-256 por inventário externo sem importar o checker novo.

```sh
python3 -B -m unittest integration.s0s1_ops03.test_scope integration.s0s1_ops02.test_contract -v
python3 -B -O -m unittest integration.s0s1_ops03.test_scope integration.s0s1_ops02.test_contract -v
python3 -B -m integration.s0s1_ops03.scope --candidate
```

O laboratório físico requer VM GitHub-hosted exclusiva, opt-ins explícitos e prova
de ownership I84/I85. Não se forjam essas variáveis para simular runner local.
O staging exporta somente HEAD confirmado, fixa S1 em
0b0930778c29204904c1c1358a9a7ae9e3fff10b e deixa o checkout revisado limpo.
Reutiliza CLI 2.84.2 e fontes I84–I86 certificadas. Executa os 31 casos herdados e
dez casos OPS-03 com resultados nominais, metadados, análise de segredos, preservação
do catálogo e descarte comprovado da stack. SIGKILL e caminhos de SQL explícito
herdados continuam exercitando o núcleo original; lab.apply_for_test usa o adaptador.

Não há instalação de executor em produção. As chamadas Auth em test_real.py são
fixtures com endpoints fixos de logout/refresh no endereço loopback validado pela
infraestrutura. Não aceitam URL, projeto, usuário real ou credencial por CLI.

Os artifacts, logs e relatórios devem identificar SHA/árvore, testes aprovados,
falhos/não executados, flags de descarte e limites. Uma falha ambiental não é PASS.
Uma falha funcional relevante impede declarar a implementação validada. Os documentos
não antecipam sucesso do run nem contêm autorreferência ao commit que os cria.

## Documentação e decisões seguintes

Consulta em 30/10/2026: signout, sessions, access-control, functions e changelog
oficiais; URLs e achados estão na matriz JSON. Changelog.md foi bloqueado no proxy
e o leitor web não suporta seu MIME; a consulta foi concluída pelo índice HTML
oficial e entradas relevantes, sem contornar a política de rede.

Revisados: restrições de schemas gerenciados (2025), novos defaults de exposição
Data API (2026) e PATs com escopo (2026). Esses achados não autorizam modificar
grants herdados, instalar objetos em Auth nem presumir plano/configuração reais.

Antes de qualquer homologação hospedada, a orquestração deverá decidir entre obter
evidência de suporte ao mecanismo atômico requerido ou autorizar separadamente um
contrato diferente. Não há aceitação implícita de duas etapas nesta missão.
Depois: diagnóstico administrativo somente leitura autorizado, comparação com
contratos instalados e ensaio em ambiente representativo separado, sob novo escopo.
Não iniciar essa atividade, instalar SQL, conceder privilégios ou fazer deploy agora.
