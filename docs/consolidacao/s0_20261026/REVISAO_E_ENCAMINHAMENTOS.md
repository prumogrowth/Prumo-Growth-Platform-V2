# S0 principal — consolidação de histórico, CFI e contratos candidatos

26/10/2026, America/Sao_Paulo. Branch própria `exp/s0-consolidacao-sessao-historico-20261026`, derivada **exatamente do PR #13 `c79020f16f9ed36dcc00257e7e8aa133b5739867`**. Sem merge automático de auxiliares, deploy, produção, credenciais reais, Graph ou migrations hospedadas. S0 permanece responsável pela integração e pela conferência dos checkpoints das frentes.

## Checkpoints e escopo real

| Entrega | Fonte recuperada | Tratamento nesta proposta |
|---|---|---|
| UI/S0 PR #11 | `ddec1b80444bfde871d43a02d0ee94b9ed7cde11` | Candidato preservado byte a byte; D1–D4 não ratificadas |
| Catálogo PR #12 | `e3bf423a8fbf2064e536c416364c8cc318f1998a` | Inventário/diagnóstico técnico aproveitado; não importado nem usado para ampliar dados/permissões |
| CFI PR #13 | `c79020f16f9ed36dcc00257e7e8aa133b5739867`; execução `350a9dd` | Base direta; runtime, testes, helpers, SQL e correção precommit preservados |
| Meta PR #14 | `31bb84fa524f4ecfdf02360988471d7f989506d7`; modelo `92703c3` | Revisão em checkout destacado; modelo não incorporado ao backend |
| S1 atual | `d3e9f0a053e16d90190696dd59cec6d77b7f1e73` | Descoberto após o catálogo; duas revisões I75D posteriores a `e868b5d`, sem mudança de migrations/I63. Fontes SQL fixadas e verificadas para perfil físico descartável |
| Frontend atual | `e44a14dbc89e8c443bed08ea06c20a1f16f4ac12` | Consulta de referência; nenhuma branch ou implementação alterada |

Os reviews, comentários de revisão e conversa dos PRs #11/#14 consultados não apresentaram aprovação conjunta. Isso não substitui deliberação da coordenação. Catálogo de classes de dados D2/D3/D4 da Issue #10 **não é** a lista de decisões de protocolo UI D1–D4.

## Lacuna confirmada e correção funcional

A RLS S0 e a candidata S1/I63 verificavam ator, atribuição/concessão/equipe, mas não a sessão viva. O PR #12 demonstrou isso por SQL sintético. Nesta proposta a lacuna é reproduzida pela **mesma requisição GET PostgREST com JWT realmente emitido pelo GoTrue, ainda não expirado, depois do logout real e da remoção da sua auth.sessions**. Antes da barreira o conteúdo continua visível; depois ela nega a próxima leitura.

`supabase/tests/s0_history_session_gate_local_only.sql` instala uma barreira experimental **restritiva SELECT** nos onze objetos do catálogo: leads, ciclos, casos, atribuições, conversas, mensagens, itens/reencontros de lote, eventos de status, lotes e canais. Ela se combina por AND com S0 e I63, sem substituir suas regras. Não introduz SELECT permissivo, grants de domínio, escrita, função comercial, endpoint ou acesso documental.

O helper privado sem argumentos deriva ator/sessão exclusivamente do contexto JWT confiado pelo PostgREST, exige papel authenticated, JWT não expirado, sessão com dono correspondente e not_after vivo. Não aceita identificador de outro ator/sessão como argumento. O schema dedicado não está exposto pela API; authenticated não recebe USAGE em prumo_private, acesso direto a auth.sessions ou EXECUTE no helper CFI de tupla arbitrária. O helper continua postgres-owned pela restrição de acesso a auth.sessions já encontrada no PR #9, com search_path vazio e retorno booleano mínimo. Nenhum novo login/owner superprivilegiado foi criado.

**Compatibilidade real GET:** a primeira implementação tentou delegar ao helper CFI com FOR SHARE. A execução real devolveu HTTP 405: PostgREST usa transações READ ONLY para GET/HEAD. A versão final reaproveita a condição ator/sessão/not_after, por SELECT sem row lock, próprio para leitura; o helper CFI e seus locks não mudaram. O cenário 19 reproduz fisicamente SQLSTATE 25006 no helper CFI dentro de transação READ ONLY e comprova a leitura pelo predicado adequado.

**Garantia exata:** a sessão é avaliada no snapshot da instrução de leitura; nova consulta READ COMMITTED após revogação confirmada é negada. Revogação ainda não confirmada pode coexistir com leitura da versão anteriormente confirmada. Não se promete cancelar query em andamento, desfazer bytes/cache já entregues ou manter a revogação esperando uma leitura HTTP terminar. O teste de duas conexões cobre DELETE/expiração ainda não confirmados, COMMIT e ROLLBACK; o teste READ ONLY mostra logout completando enquanto a transação de leitura está aberta e a instrução seguinte sendo negada. Comandos CFI continuam exigindo locks transacionais e mantendo suas garantias mais fortes.

A checagem não adiciona pausa de intake, direitos comerciais, minimização de campo ou regra de retenção. Timeouts de inatividade/configuração não materializados como not_after/DELETE continuam limitados pelo funcionamento GoTrue/JWT existente; não se declara resolução de todos os controles produtivos de sessão. Clientes SQL que possam forjar request.jwt.claims continuam fora da fronteira de confiança: authenticated é papel de execução da API, não credencial distribuível ao browser. service_role/BYPASSRLS e o instalador continuam identidades privilegiadas fora da barreira TO authenticated; não se afirma que esta policy restrinja essas identidades, nem se amplia seu uso.

## Validação e preservação

**CI final [40405271785](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40405271785), job `121861289648`: SUCCESS no SHA executável `8be6e194bfb5b8694c1010ff8560c8ec19ed4fd8`.** Logs conferidos: 173 unitários, 18 famílias Auth/REST, dez CFI originais, 19 cenários de histórico S0, 32 CFI restritos e 19 de histórico com S1/I63. As onze tabelas possuem controle positivo antes do logout. Nenhum cenário real foi ignorado; cleanup `Stopped supabase local development setup.` confirmado. A revisão intermediária `6c7898b` também passou o fluxo completo, mas ainda tinha quatro tabelas administrativas vazias no seed; o checkpoint final fortalece a prova sem alterar runtime.

Os identificadores de execução, SHAs, resultados e excertos sanitizados ficam em `EVIDENCIAS.json`, ao lado deste relatório. O primeiro run que revelou o problema READ ONLY é mantido como falha, com testes posteriores não executados separados dos aprovados. A certificação final só vale para seu SHA executável exato; este fechamento documental não altera código.

A suíte `integration/history/test_session_history.py` usa GoTrue/PostgREST/PG17 reais, sem emissor JWT de teste, fake de identidade, replacement de HTTP ou resultado SQL fabricado. O teste adversarial de claims SQL é identificado separadamente: ele não autentica tokens alterados por HTTP. Inclui dados positivos nas onze tabelas antes do logout e controles positivos/negativos por loja/contato/equipe, logout com JWT ainda válido, not_after, concessão/atribuição/chefia revogadas, assinatura inválida, anon, ACLs privadas, escrita sintética corrente versus caso antigo/supervisão, READ ONLY, concorrência/COMMIT/ROLLBACK, sessões distintas, instalação atômica e ausência de efeitos CFI.

O primeiro perfil usa a S0 atual mais a referência S1/038 já instalada pelo teste CFI, sem I63. O segundo perfil instala os **21 arquivos originais S1/039–059 e a fixture original I63**, lidos de checkout destacado no SHA fixado. Migrations comuns e referência S1/038 são comparadas byte a byte; os 22 arquivos têm SHA-256 no manifesto. Nenhuma fonte S1 é editada, promovida a migration S0 ou aplicada fora do stack novo. Isso testa composição de laboratório, não ratificação da I63 nem certificação completa de I64–I75D. Os novos sete testes I75D da S1 foram consultados, não recontados como execução desta proposta.

A CI mantém os 173 unitários, Auth/REST/RLS e dez cenários CFI originais; executa os 32 cenários do PR #13 **depois de instalar a barreira**. Nenhum cenário ou verificação de proveniência é removido. Runtime CFI, fixtures anteriores, schemas UI, vetores e migrations S0 permanecem inalterados. A instalação compara catálogos/ACLs/helpers antes/depois e testa recusa sem opt-in e rollback de reinstalação.

## Parecer técnico sobre Meta/S0 — sem ratificação operacional

Foram lidos contratos, guia, protocol.mjs, candidate.mjs, lab-store.mjs e lock-plan.mjs do PR #14. Conferidos os sete blobs de proveniência. Foram reproduzidos localmente **52/52 testes do modelo + 161/161 regressões Meta**, sem rede/Graph, em checkout destacado e Node 24.19.0. O primeiro comando com o runtime com configuração herdada falhou no arquivo de subprocessos; com NODE_OPTIONS/NODE_PATH vazios o mesmo código passou integralmente. O CI Node 22 da auxiliar é evidência histórica própria, não nova execução PG/M2M desta tarefa.

| Componente | Classificação S0 | Fundamentação / limite |
|---|---|---|
| Classificadores Cloud e verificação do webhook bruto | **Aproveitar** como componentes técnicos existentes | Importações preservadas e regressões conferidas; assinatura externa Meta não concede principal M2M ou direito comercial |
| DISPATCH-01 reserva/begin | **Adaptar; operacional pendente C1/C2/C5** | CAS, ocupação e begin único são bons requisitos. Booleanos de fixture não são fontes autoritativas; faltam bindings SQL, fences e transporte. Não transplantar o CandidateLab como backend |
| DISPATCH-02 observação/incerteza | **Aproveitar separação; adaptar ACL C3/C6** | 2xx não prova entrega; timeout/not_attempted após begin não libera retry. Observe/read/review usam ACL técnica no modelo. Acesso após revogação humana e autoridade do conciliador precisam aprovação explícita; revisão não pode liberar slot/ficha/cadência |
| ACK-03 | **Adaptar; pendente C3/C4/C6** | Separação HMAC Meta/M2M/humano e lote inteiro são requisitos úteis. FileStore prova fsync/rename single-process, não commit PG/HA/ACK HTTP. Não usar senha SQL, principal GoTrue ou assinatura Meta como autorização do worker |
| LOCK-04 | **Adaptar; ordem global pendente C5** | Mantém ordem local outbox→evento→chave do caminho final WA55/WA52. Ranks não mapeiam sessão, namespaces reais, modos, FK/triggers e todos os revogadores. Planner de listas não é gerenciador físico de locks |
| FileStore, issuer e gates sintéticos | **Rejeitar como implementação operacional; aproveitar só como fixtures** | Não promovidos para backend/migrations. Snapshot, mutex e durabilidade local não certificam serviço distribuído, RLS, M2M ou envio |

**Ordens físicas e autoridade:** o CFI atual toma chave CFI → sessão → equipe → recursos de caso/ciclo/loja/atribuição → concessão → conversas/mensagens → recibo/nonce/auditoria. O SELECT conjunto FOR UPDATE não estabelece por si só ordem determinística entre todas as relações de seu JOIN. A proposta rankeia TECHNICAL_KEY depois de S1, e nem explicita a sessão. As chaves CFI e Meta são relações distintas: isso **não prova deadlock entre esses caminhos**, mas impede chamar a lista candidata de ordem global já compatível. Não reordenar CFI certificado só para satisfazer ranks abstratos.

A leitura nova é read-only e não adquire row locks para disputar esses fences. Os testes físicos de sessão desta proposta não certificam dispatch Meta ou C5. A composição guardada do PR #7 continua a fonte para futuro laboratório; não reexecutamos WA39–68 nem tratamos as 823 provas históricas como integração operacional.

**Provas físicas preparadas para a próxima etapa, condicionadas ao contrato faltante:** usar o compositor guardado do PR #7, sem importar fixtures para migrations oficiais. Após C1/C3/C5 mapear recursos reais, testar com dois clientes: cancelamento/opt-out/concessão/atribuição versus reserve/begin nas duas ordens; revogação de key/registry versus append integral; nonce/item/auditoria com falha/rollback; replay/readback sob perda de resposta; lote multi-evento com locks ordenados, FKs/triggers, 40001/40P01 e zero I/O externo no retry SQL. Não há nesta S0 fonte aprovada para reserve/begin/ACK que permita declarar essas provas como integração concluída. O plano não autoriza Graph nem ativação.

## Decisões e encaminhamento pela S0

Responsáveis abaixo são **propostos para coordenação**, não concessão de aprovação. Todos continuam PENDENTES. S0 organiza interfaces, evidências e gates; cada frente conserva a responsabilidade pelo próprio domínio.

| ID | Decisão / responsável proposto | Dependência / próximo artefato concreto |
|---|---|---|
| UI D1 | S0 + Frontend + Produto: envelope/comandos/projeção | Confirmar captura/recheck técnicos separados de conclusão comercial; não reutilizar C11/C13/C15 |
| UI D2 | S0 + S1 + Frontend: fonte das versões | Definir leitura autorizada e tipo case/cycle; decimal string int64; nunca alias caso=ciclo |
| UI D3 | S0 + Frontend + S1/Privacidade: lookup de recheck | Resolver vínculo server-owned ator/sessão/caso/captura; handle, correlação, expiração/retry/retenção; aproveitar recibo/auditoria existentes |
| UI D4 | S0 + Frontend + S1/Segurança: transporte e elegibilidade | Bearer TLS versus cookie/BFF/CSRF, refresh/logout, rótulos visuais versus gates existentes; barreira de leitura não ratifica o transporte candidato |
| Meta C1 | S0 + S1: fontes/bindings/revisões de cada gate | Matriz de linhas/colunas e mutadores reais, slot/fingerprint; alinhar significado com UI D2, sem depender do transporte UI nem fundir domínios |
| Meta C2 | S0 + Meta + Produto: lifecycle reserva/begin | Custo de possível não envio, handle/transporte, tombstone/novo intento; depende C1/C3/C5, nunca lease que reenvia sozinho |
| Meta C3 | S0 + Segurança/Infra + Meta: principal M2M | Issuer/audience/ACL/TLS/rotação/custódia, clock/TTL/nonce; domínio distinto de GoTrue e Meta externo |
| Meta C4 | S0 + Meta + Infra: lote/recibo/ACK | Mapeamento PG, commit/readback/falha, política inválidos/backpressure e HTTP; depende C3/C5/C6 |
| Meta C5 | S0 + S1 + Meta: fences/modos/ordem real | Incluir sessão, namespaces distintos de key, concessão/atribuição/opt-out/registry, FKs/triggers e revogadores; comparar ordens existentes antes de código |
| Meta C6 | S0 + Produto/Comercial + Privacidade: evidência e conciliação | Permissão técnica após revogação humana, minimização/retenção/expurgo e autoridade da revisão; não converter resultado técnico em mudança comercial |
| Meta C7 | S0 + Frontend: manter UI D1–D4 | Contrato humano não autentica M2M nem autoriza dispatch; depende D1–D4 e C1/C3 |

### Próximas tarefas concretas

1. **S0/S1:** revisar e integrar explicitamente a barreira de sessão ao perfil de leitura escolhido; executar a suíte nativa I75D com ela, sem editar I63 nem assumir minimização D3/D4. A proposta aqui entrega o patch funcional e os dois perfis de prova.
2. **S0/Frontend:** deliberar D1–D4 para implementar lookup/binding no caminho S0 existente e só depois uma confirmação autenticada de UI em sandbox.
3. **Meta/S0/S1:** entregar para C1/C3/C5 o inventário recurso→linha/namespace→modo→mutador→ordem; indicar quais operações dependem de identidade humana ou apenas técnica. C6 deve explicitar read/review/observe após revogação. Não é necessário iniciar outra execução WA ou reescrever classificadores.
4. **S0/Infra:** após os contratos acima, materializar o adapter PG restrito e os testes físicos listados, sem Graph, ACK externo ou regra comercial nova. Custódia produtiva, owner de helpers auth, orçamento de query/cache, observabilidade e retenção continuam gates separados.

## Reprodução somente descartável

O workflow `exp-s0-consolidacao-historico.yml` fixa CLI 2.84.2, driver 3.2.9 e usa o registry Docker Hub já suportado no PR #13. Não vincula projeto remoto. Executa as regressões originais, `PRUMO_HISTORY_DISPOSABLE_TEST=YES PYTHONPATH=. python3 integration/history/test_session_history.py --profile s0`, os 32 CFI e o segundo perfil após `prepare_s1_profile.py --source-repo <checkout-destacado-no-SHA-do-manifesto>`. O script de perfil recusa ref divergente, arquivo alterado ou DSN fora do loopback local. `supabase stop --no-backup` roda com always, inclusive em falha.

O schema/policies novos são fixtures revisáveis, não migrations aprovadas. A S0 entrega melhoria real no caminho de leitura existente e mantém o gate UI/Meta operacional bloqueado pelas decisões acima. Nenhuma classe documental, permissão de supervisão, função comercial, PR auxiliar ou deploy foi ativado automaticamente.
