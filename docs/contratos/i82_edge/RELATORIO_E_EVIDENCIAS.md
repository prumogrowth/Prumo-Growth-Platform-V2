# I82 — execução da borda administrativa Edge local

27/10/2026, America/Sao_Paulo. Base exata I81 `c267c56` / PR #32,
código I81 `4ba266d`, CI 40543117528 SUCCESS. Branch original S1 `8780b576`
e I79/I80/I81 preservadas. Contrato: [CONTRATO_HTTP_V1.md](CONTRATO_HTTP_V1.md).

## Implementação e reaproveitamento

A borda TypeScript/Deno traduz HTTP para os seis comandos existentes I79/I80.
GoTrue verifica Bearer no servidor; usuário e session_id só são vinculados depois
da verificação. HMAC e SQL parametrizado alcançam as funções assinadas pelo
login restrito existente. Sem segunda autenticação, regras comerciais em TS,
PostgREST privado, credencial postgres ou poderes novos de Gestor.

O Python não executa na Edge: permanece como fixture, consumidor HTTP de teste
e referência de compatibilidade. SQL continua responsável por sessão viva,
Diretor, cargo/chefia explícitos, prévia, CAS, idempotência, locks, revogação I61,
auditoria e constraints no COMMIT. I79/I80/I81 não são reimplementadas.

HTTP usa envelope prumo.admin.v1 e ID de relação em decimal string, preservando
bigint sem arredondamento. Valida campos fechados, nulls, UUID/hash/chaves,
limites de bytes/tempo e JSON duplicado. Recibo é validado antes do COMMIT;
resposta de sucesso exige confirmação da transação. UNKNOWN e ausência de
resposta exigem reconciliação com a mesma chave, nunca retry automático cego.
Não significam rollback nem conclusão comercial.

O delta SQL insere somente uma chamada no início de cada ponte I79/I80 para
um helper INVOKER privado. Os dados de I81 não ganham novos grants. ACCESS SHARE
mantido até COMMIT serializa alterações estruturais metadata-only, cujas colunas
são conferidas antes da operação. DDL não revisado bloqueia o comando; original
restante dos corpos, owners, ACL/policies, triggers e constraints são comparados.

## Arquivos de implementação e testes

| Arquivo novo | Responsabilidade |
| --- | --- |
| `supabase/functions/prumo-admin-i82/index.ts` | entrada efetiva Deno.serve |
| `supabase/functions/prumo-admin-i82/handler.ts` | roteamento, limites, CORS, envelope, erros e resultado incerto |
| `supabase/functions/prumo-admin-i82/contract.ts` | DTOs estritos, bigint, validação precommit, material HMAC idêntico ao Python |
| `supabase/functions/prumo-admin-i82/runtime.ts` | configuração local, identidade GoTrue, assinatura WebCrypto e transporte transacional PostgreSQL |
| `supabase/functions/prumo-admin-i82/deno.json`, `deno.lock` | dependência fixada e integridade |
| `supabase/tests/s1_i82_metadata_fence_local_only.sql` | delta SQL guardado, sem migration hospedada |
| `integration/i82/install_local.py`, `catalog.py` | opt-in/loopback, instalação e atestação física de compatibilidade |
| `integration/i82/compat_vectors.json`, `test_codec_compat.py`, `contract_test.ts` | vetores sintéticos, comparação Python e testes de fronteira Deno |
| `integration/i82/test_edge.py` | fluxos HTTP contra Edge Runtime, GoTrue e PG17 reais |
| `integration/i82/gateway_local.py` | remove somente o CORS curinga do serviço Functions no gateway descartável e restaura o config original |
| `integration/i82/sanitize_runtime_log.py` | diagnósticos internos limitados, sem mensagens/credenciais |
| `.github/workflows/exp-s0-s1-i82-edge.yml` | suites certificadas + runtime Edge real e catálogo final |

Nenhum executável histórico é editado no Git. SQL é delta explícito e mínimo no
catálogo descartável; não se incorpora PR candidato inteiro nem se altera branch
do Frontend/F02/Meta/S1 original. Arquivos e hashes finais são registrados na
evidência de fechamento, com o commit efetivamente executado pelo CI.

## Ambiente, segurança e limites

Stack nova, não vinculada, PG17/GoTrue/PostgREST/Edge Runtime. Deno verificado
localmente 2.2.8; CLI Supabase 2.84.2 e psycopg 3.2.9 herdados do checkpoint.
Segredos SQL/HMAC sintéticos são gerados pela fixture existente, em arquivo de
ambiente temporário chmod0600, apagado ao fechar os testes. Não há secret no Git,
HTTP/DTO ou artefato. Vetores com chave pública fixa são somente codec, não Auth.

A configuração local recusa URLs hospedadas/login privilegiado e exige opt-in.
Auth URL e DB URL internos usam nomes exatos dos containers da stack descartável.
CLI functions serve --no-verify-jwt deixa a autenticação no handler GoTrue real
e no SQL; nenhuma operação administrativa aceita JWT só decodificado. A camada
não lê service_role, não expõe função SQL privada e não usa dados reais.

Pool e concorrência são limites por worker, não controle distribuído de taxa ou
quota de negócio. Custódia/login/chave compartilhados do laboratório, TLS e
provisionamento/homologação produtivos ainda precisam de desenho e validação.
DDL em objetos fora das duas tabelas metadata-only continua exigindo governança;
o fence não substitui revisão de tipos/constraints/policies ou todo o catálogo.

ADR Supabase + backend servidor→OpenAI recuperada na fonte F02 atual, sem
incorporá-la. Changelog público Supabase retornou HTTP403 pela rede; documentação
MCP atual de Edge/Auth/Database consultada, sem acessar Supabase hospedado.
Deno local usou CAs do sistema para o proxy, preservando verificação TLS.

## Tentativas registradas

- [40549209419](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40549209419),
  código 35d6621: typecheck/12 Deno/codec e todos os perfis I79/I80/I81 e SQL
  passaram; Edge executou 20 cenários, com 3 negativas aprovadas, 16 falhas e
  1 erro de alias no teste do proxy. Chamadas autenticadas falharam UNKNOWN,
  logo a integração não foi certificada. Não se inferiu sucesso do baseline.
- [40551255788](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40551255788),
  código 12a20f4: probe inicial autenticado falhou antes de executar a suíte.
  Diagnóstico interno sem mensagem/payload/credencial confirmou ENOTFOUND em
  node:dns no Edge Runtime 1.73.0 / Deno 2.1.4. GoTrue passou; problema de
  resolução do destino SQL, não de grant, RLS, HMAC ou autoridade de Diretor.
  Alias http.client no proxy corrigido, campos fechados reforçados e CREATE
  de schema dos owners incluído no aceite de catálogo.

O ajuste subsequente usa IPv4 obtido da rede do próprio container DB descartável,
fixado no driver por configuração exclusivamente do servidor. Não aceita endereço
no DTO, IP público ou endpoint cloud de metadados, nem faz fallback de host. A
credencial restrita e o núcleo SQL permanecem os mesmos. Supabase local usa a
mesma stack e o mesmo driver fixado; não se resolve a falha por RPC público ou
proprietário superprivilegiado. Tentativas parciais não certificam a entrega.

- [40552937146](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40552937146),
  código 9dad3a5: probe SQL passou; 20 cenários HTTP executados, 19 aprovados.
  Única falha: Kong CLI sobrescreveu Allow-Origin por `*`. Fluxos autenticados,
  revogações, CAS, concorrência, rollback diferido e resposta perdida passaram,
  mas a entrega completa continuou não certificada. Template upstream CLI
  2.84.2 confirmou plugin CORS sem configuração no serviço functions-v1.

A correção local subsequente remove somente esse plugin Functions, deixando
Auth/REST e request-transformer inalterados, recarrega o Kong e compara o
readback. Ao encerrar, restaura byte a byte o arquivo original. Nenhum config
com bearer sintético é impresso, versionado ou incluído nos artefatos. O caso
HTTP20 passa a exigir também OPTIONS real aceito e header indevido recusado.

## Reprodução

Executar o workflow próprio em checkout desta branch, sem vincular projeto.
Ele preserva o bootstrap e as regressões I81, obtém catálogo I82 before, instala
o fence e obtém after, executa novamente I79/I80, inicia functions serve com
credenciais descartáveis e roda test_edge.py, então atesta final e faz cleanup.

```bash
PYTHONPATH=. python3 integration/i82/catalog.py before
PYTHONPATH=. python3 integration/i82/install_local.py
PYTHONPATH=. python3 integration/i82/catalog.py after
PYTHONPATH=. python3 integration/i79/test_professionals.py
PYTHONPATH=. python3 integration/i80/test_regularization.py
PYTHONPATH=. python3 integration/i82/test_edge.py
PYTHONPATH=. python3 integration/i82/catalog.py final
```

Requer os opt-ins anteriores e PRUMO_I82_DISPOSABLE_TEST=YES. O teste faz o
provisionamento de ambiente e inicia/encerra o CLI local, sem deploy. Cleanup
final sempre executa supabase stop --no-backup. Não reutilizar em projeto real.

## Coordenação e continuidade

Contrato HTTP candidato pode ser avaliado pelo Frontend sem alterar sua branch.
Prévia visual continua sem aceite de produto. Não há implementação de interface
nesta execução nem promoção do contrato para produção. I79/I80 seguem exigindo
cargo/chefia explícitos e decisões administrativas do Diretor para ambiguidades.

G2 operacional permanece parcial. F02 G01–G06 parciais/G07 pendente, nenhuma
ratificação comercial ou nova auditoria/H01. Sem merge, deploy, credencial ou
cliente real, migration hospedada ou chamada OpenAI/Meta.

## Fechamento certificado

**[CI 40554841552 — SUCCESS](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40554841552)**
no código **[c8817429184d4fb3d5bef29cb9e99d6f2b970f63](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/commit/c8817429184d4fb3d5bef29cb9e99d6f2b970f63)**,
tree `3c529f119441019c8948a1dec7a7d3bea1b1bc13`. Jobs integrado
`122368004210` e nativo `122368003850`, ambos SUCCESS. Início 17:53:40Z,
atualização final 18:00:28Z (408 segundos entre esses registros). Cleanup
`supabase stop --no-backup` confirmado; nenhum ResourceWarning.
Commit documental posterior conserva o código executado.

| Prova executada | Resultado |
| --- | --- |
| HTTP → Edge Runtime Supabase → GoTrue → PG17 | **20/20**, 33,063s para a suíte, sem simular a autenticação positiva |
| DTO/HTTP/JSON/HMAC Deno | **12/12**, também executados localmente |
| Paridade Python/TypeScript | **1 teste / 7 vetores**, seis comandos e bigint máximo; fixture sintética, sem autoridade operacional |
| I79/G1 após o fence I82 | **62/62**, testes históricos inalterados |
| I80 após o fence I82 | **33/33**, testes históricos inalterados |
| I81 instalação/cutover/segurança | **6 + 1 + 14**, todos aprovados novamente |
| I79/I80 antes e depois da I81 | **62/62 + 33/33** em cada perfil comparativo |
| G1 anterior à I79 | **36/36** |
| CFI-01/F02 existentes | **56/56** |
| Sessão/histórico S0 e perfil I63 | **19/19 em cada perfil** |
| Unitários S0 existentes | **288/288**, também executados localmente |
| Unitários S1/catálogo existentes | **179 + 6 + 8 = 193/193** |
| SQL fila/exceção com identidades de fixture | **34/34**, não confundir com os cenários GoTrue |
| S1 nativa PG17 | I54–I74/I78, I46/I48/I75B/I75C PASS |
| Catálogo I82 | before/after/final validados; **after = final** |

Os 20 cenários HTTP novos estão nominados em [evidencias.json](evidencias.json).
Cobrem cadastro/ativação, Gestor recusado, expiração/logout/assinatura inválida,
identidade não escolhida no JSON, CAS/transferência/replay, inventário e prévia
sem aplicação, APPLY explícito/stale/concorrente, vínculo de sessão/Diretor,
revogação durante espera, rollback parcial e na constraint diferida, perda real
de resposta após COMMIT, DDL incompatível e disputa de ALTER TABLE, acesso SQL/RPC
privado recusado, duas equipes/lojas, legado bloqueado e CORS/OPTIONS reais.

O teste de resposta perdida usa um proxy **só de teste**: primeiro recebe o 200
real da Edge após COMMIT, depois encerra a conexão do cliente sem entregar a
resposta. A repetição com mesma chave retorna ALREADY_APPLIED e o mesmo request_id.
Não há header de falha ou bypass no handler. O teste diferido comprova o caso
oposto: falha no COMMIT nunca retorna sucesso e não deixa alteração parcial.

Repetições por perfil e suítes herdadas se sobrepõem; não somar como quantidade
inédita de testes. O I78 nativo reproduz a lacuna histórica anterior à I79;
no perfil integrado posterior, o validador NOLOGIN mantém chefia obrigatória.
Não há certificação nova independente I75D/I76, nem conclusão de gate comercial.

### Owners e grants antes/depois

| Objeto/controle | Antes I82 | Depois e final I82 |
| --- | --- | --- |
| Pontes I79/I80 | DEFINER `prumo_s1_admin_domain_local`, EXEC domínio/outer HMAC | mesmo owner/ACL/config; uma chamada de fence por ponte |
| Constraint `s1_i79_consistencia()` | DEFINER `prumo_s1_professional_validator_local` | corpo, owner e ACL idênticos |
| `s1_i82_metadata_fence()` | inexistente | **INVOKER**, owner técnico postgres; EXEC somente postgres/domínio; sem elevação pelo owner |
| Roles de domínio/validador | NOLOGIN/NOINHERIT, sem SUPER/CREATEDB/CREATEROLE/REPLICATION/BYPASSRLS | idênticas; sem CREATE de schema no final |
| Memberships | 31 no recorte, sem login assumir owners | idênticas; PG17 conserva postgres ADMIN-only, INHERIT=false/SET=false, não executável |
| Tabelas / ACL de coluna / policies | 82 / 87 / 145 no recorte | idênticas, inclusive owners e flags RLS |
| Triggers / constraints | 57 / 418 | idênticos, guards I46/I57/I61 preservados |
| Funções / dependências de catálogo | 106 / 202 | 107 / 204, apenas o helper e suas dependências |
| ACLs efetivos de funções / tabelas | 210 / 700 linhas no recorte | idênticos; helper adicional verificado explicitamente contra roles indevidas |

Catálogo comprova que remover exatamente o prefixo do fence das duas pontes
reproduz o SHA-256 anterior; todos os demais corpos são idênticos. Não há
regressão para owner postgres nas operações administrativas. O helper INVOKER
não lê dados Auth/chave e utiliza somente SELECT/locks já admitidos na I81.
Probes de acesso privado, SET ROLE, DML, HMAC/nonce/I61 e CFI-01 da I81 passaram
novamente. O controle de DDL adicional foi comprovado também pelo HTTP real.

[Artefato 12756677846](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40554841552/artifacts/12756677846):
catálogos before/after/final e log interno sanitizado, retenção de 14 dias.
ZIP SHA-256 `2cb0b3087d426308a31878feecb2dbe22436a30677bd66f61379972a3f2fd1c0`.
Os hashes dos quatro arquivos, os owners/ACLs relevantes e os 16 hashes de
fontes/CI ficam versionados em evidencias.json para auditoria após a retenção.
Nenhum arquivo de ambiente, bearer, segredo HMAC ou senha SQL está no artefato.

### Estado de integração e próxima execução

Os seis comandos funcionam pela borda HTTP **em laboratório descartável** sob
a mesma autoridade SQL I79/I80/I81. A separação entre INVENTORY/PREVIEW/APPLY e
o comportamento de resultado incerto foram exercitados; não há revisão ou
ratificação comercial implícita. O contrato HTTP continua candidato para revisão
conjunta do Frontend, sem aceite das prévias visuais.

Bloqueios para produção: provisionamento e custódia dedicados de login/chave,
rotação, TLS e configuração hospedada, controle de abuso distribuído, governança
de DDL mais ampla e homologação operacional. O pin Docker e ajuste do Kong são
adaptações explícitas do ensaio local, sem promessa de configuração hospedada.
Convite/criação Auth, bootstrap de Diretor e recuperação de resultado quando a
sessão/alçada já foi revogada não foram inventados como novas competências.

Próxima execução recomendada: provisionamento local dedicado da borda, separando
login/chave/custódia do login genérico de laboratório **sem ampliar permissões**,
com os mesmos cenários reais, acompanhado da revisão do DTO pelo Frontend.
Uma implantação hospedada exigirá escopo/autorização próprios e novas evidências.
Issue #23/G2 continuam abertos; S0 permanece responsável pelas integrações.
