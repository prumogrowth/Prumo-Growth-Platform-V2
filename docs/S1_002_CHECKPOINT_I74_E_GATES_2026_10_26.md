# S1-002 — Checkpoint após I74 e retomada por gates

**Data:** 26/10/2026. **Branch:** `feat/s1-002-equipe-prumo`. **Marco de código certificado:** `ad252bdccb56aafa3f0846b33d3fe965bcf74fa6`. **Escopo:** somente CI descartável PG17/GoTrue, sem merge, migrations hospedadas, deploy, S0 oficial ou `main`.

## I74 incorporada e aceita nesta frente

A frente S0/Codex publicou em [PR Draft #6](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/6) a resolução da [Issue #5](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/issues/5). A S1 revisou e transportou, **por commit próprio**, exatamente os quatro arquivos indicados:

1. `supabase/tests/s1_108_export_signed_executor_local_only.sql` (blob `da0878bcad796f9b10e678ddb4ddb53988718a75`).
2. `scripts/test_s1_002_i74_signed_export_e2e.py` (blob `f489515fab96e7d1ec6f152c476114f08e39cfd7`).
3. `scripts/test_s0_i74_provisioning.py` (blob `91e3f695cbb6976fb45d8b35da889c2b1652ad0c`).
4. `scripts/test_s0_i74_security_e2e.py` (blob `ced88334ca4c86ab695c3b3fdfb9440721988966`).

Somente o filtro `paths` do workflow **oficial S1** `.github/workflows/s1-002-i37-intake-signed-local.yml` foi ampliado para os dois helpers. **Nenhum workflow experimental `exp-s0-i74-*` foi importado.** O corpo HMAC/nonce/sessão/exportação manteve o hash informado pelo Codex; a alteração é o instalador transacional de propriedade restrita e o lock mínimo das chaves.

### Certificação reexecutada na S1, mesmo commit

| Evidência | Resultado |
| --- | --- |
| [PG17 oficial #40307390136](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40307390136), job `121519756929` | **SUCCESS**, `PASS I74-01..06` (6/6), regressões S0/S1 I52–I73, ROLLBACK experimental final |
| [GoTrue/PostgREST oficial #40307390037](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40307390037), job `121519756694` | **SUCCESS**, `PASS I74-E2E-01..08` (8/8), `PASS I74-PROV-01..04` (4/4), `PASS I74-SEC-01..03` (3/3), após I74 conclui `S1INTAKE-147/148` e `S1-002/I37: 132 older E2E and 16 new I37 gates PASS.` |
| Mesmo workflow, job `121519756342` | **SUCCESS**; logs somam **179 testes unitários**, incluindo 4 testes I74 |

Logs verificados por marcadores, resultado dos jobs e SHA dos runs. Exceção anterior #40294183275 permanece documentada como falha **pré-adoção**; não é contada como aceite. O trabalho do Codex no PR #6 é evidência auxiliar, não substitui a própria certificação.

### Limites de segurança constatados

- **Owner** `prumo_s1_export_executor` NOLOGIN, sem superusuário/BYPASSRLS; função `SECURITY DEFINER` somente em schema privado e com `search_path` vazio. RPC comercial original permanece `SECURITY INVOKER`.
- **Installer** `postgres` obtém SET/CREATE somente durante a instalação e tem as opções de membership anteriores restauradas, com abort/rollback atômico.
- **Chaves**: SELECT FOR SHARE requer UPDATE(id), mas RLS tem política UPDATE `WITH CHECK false`; não há UPDATE(secret/active). Probes negam DML do executor.
- **Gateway**: login assinado não recebe membership/SET ROLE no executor nem acesso direto a chaves, nonce, ledger ou RPC legada.
- **HMAC/nonce**: identidade GoTrue autenticada, material vinculado a parâmetros, consumo único atômico, bloqueio de concorrência e recusa de provas inválidas/replay; sessão revogada e chave desativada não geram nova reserva nem nonce persistido.
- **RLS S0**: grant de loja revogado não revela dados; quotas não avançam em negativas; scanner de exposição I65 permanece limpo.

**Resultado:** I74 **certificada apenas no laboratório desta frente**, sem homologação operacional, não autoriza rollout. Custódia operacional de segredos, rate limit de borda, retenção/LGPD, comportamento frente a administradores privilegiados e exportações alternativas permanecem riscos independentes.

## Retomada: seis gates de produto, sem repetir etapas aprovadas

O mapa inicial é `docs/S1_002_I50_REVALIDACAO_E_GATES_2026_10_23.md`, mas está **desatualizado** em relação a I51–I74. A decisão **A2 está fechada pela I51** (nova atribuição para Consultor com intake pausado proibida); não reabrir discussão usando o texto histórico I50.

| Gate | Já realizado em bancada / contrato atual | Pendência real para fechar |
| --- | --- | --- |
| **G1 — fila/distribuição** | I52 guarda intake; I54 produtor de fila no domínio S0 com CAS; I55 gateway GoTrue/HMAC para lista e assunção; I56–I59 integridade, titularidade e revogação | Homologar integração com **serviços S0 efetivamente executados**, origem do evento humano, falhas/retries, UI de Gestor e regras completas de elegibilidade. Não reescrever I49/I50 mocks ou fila I54 |
| **G2 — equipe/RBAC** | I51 decisão A2; I52/I53 intake versionado e assinado; grants, transferências e revogações revalidados | Fechar autoridade do Diretor/chefia, ciclo real de concessões e serviços/telas de gestão, inclusive pausa/retomada sem suspender conta |
| **G3 — histórico/exceções** | I61 exceção por caso canônica; I62 gateway assinado; I63 RLS candidata 8 policies; I64–I68 guardas de superfícies indiretas/projeções | Matriz completa objeto/coluna D2/D3/D4, mídias/anexos, políticas definitivas e composição integrada com produtores S0; aprovar risco de leitura por equipe e revogação |
| **G4 — primeiro contato/indicador** | Regra COUNT/DOT/NONE e contratos de indicador documentados anteriormente; sinais de fila não provam sinal de entrega de mensagem | Integrar **evento real** de primeira ação humana e estados enviado/entregue, transferências e reset por conclusão com Meta/S0; validar dados e UI |
| **G5 — conclusão/F03** | Contratos e propostas experimentais S0/CFI existem em branches separadas | Alinhar com Codex a sequência real de fechamento, locks/versões, retorno ao Consultor/Gestor, elegibilidade por caso e homologação Banco |
| **G6 — aceite operacional** | PG17, GoTrue/PostgREST e testes negativos extensivos, incluindo I74 | Revisão cruzada S0/S1, homologação multi-loja ponta a ponta, UI, deploy controlado e aprovação de retenção, LGPD, custódia, rate limit, observabilidade |

**Próxima execução recomendada (I75):** auditoria de prontidão **G3** orientada a objeto e coluna (D2/D3/D4, mídias, indiretos), conciliando as políticas candidatas I63–I68 com os consumidores reais e identificando exatamente quais interfaces/entitlements ainda dependem da S0. Produzir contrato de integração e testes negativos isolados; **não promover migrações nem refazer permissões já testadas**. A infraestrutura operacional S0 e as dependências que requeiram alterações do núcleo permanecem sob coordenação do Codex.

**Checkpoint:** I74 laboratório PASS; S1-002 como produto **ainda aberta em G1–G6**, sem percentual total inferível de uma contagem de execuções. Issue #3 de otimização CI continua fora do escopo.

## Checkpoint I75B — 26/10/2026

**I75B implementada e certificada como INVENTÁRIO ESTÁTICO, não como RLS operacional:** commit `40336b7b3ff7de2d7d864333ffad4135c480f2c1`; [PG17 oficial #40312496327](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40312496327) SUCCESS, 6 unitários + 3/3 gates I75B, regressões I63–I74 preservadas. Varredura: 57 migrations, 45 tabelas adicionais, 25 arquivos runtime, 11 superfícies canônicas e 8 policies I63 somente de bancada. [Relatório I75B](S1_002_I75B_G3_INVENTARIO_EXECUTAVEL_2026_10_26.md). Artefato JSON disponível nesse workflow.

**Próximo objetivo I75C:** confrontar com o catálogo S0 físico as outras superfícies, D2/D3/D4 e mídia/anexo, por objeto, coluna e finalidade, e preparar provas reais de autorização/revogação. Proibido declarar G3 concluído a partir de análise lexical. Nenhuma alteração na S0, `main` ou produção.

## Checkpoint I75C — 26/10/2026

**I75C concluída somente como catálogo efetivo PG17/ACL por coluna, não como aceite operacional do G3.** [Workflow oficial PG17 #40354941900](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40354941900), código `ff63fdf392aecd547e33c1676dcd422093042710`, job `121684756516`: **SUCCESS** com 8/8 testes unitários I75C, 4/4 marcadores I75C e regressões I74 6/6 preservadas. Confirmadas 11 tabelas com RLS, sem SELECT anon nessas tabelas e colunas, e nenhuma policy experimental I63 persistida. Artefato JSON `s1-002-i75c-effective-g3-catalog` (ID `12665866195`). [Relatório I75C](S1_002_I75C_CATALOGO_EFETIVO_G3_2026_10_26.md).

**Dependência externa declarada:** [Issue #10 — S0/Codex: catálogo real D2/D3/D4 e mídias/anexos](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/issues/10), sem pedido de acesso a produção ou de alteração S0. PRs S0 #9 e Meta #8 são referências a conciliar, não código automaticamente promovido. **I75D** depende desse retorno para testar endpoints reais de anexo/histórico. Continuar G1/G2/G4/G5/G6 independentemente quando possível; não chamar G3 concluído com varredura estática ou ACL de laboratório.

## Checkpoint I75D — 26/10/2026

**Retorno S0/Issue #10 incorporado como referência de contrato, sem copiar o código do PR #12**: [relatório da auxiliar](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/e3bf423a8fbf2064e536c416364c8cc318f1998a/docs/contratos/g3_issue10/RELATORIO_CONTRATO_S0_S1_G3_20261026.md). Código I75D da S1 certificado no commit `d3e9f0a053e16d90190696dd59cec6d77b7f1e73`, [GoTrue/PostgREST oficial #40403944872](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40403944872): **7/7 I75D-E2E**, além de I63 6/6, I74 8/8 e regressões finais S1INTAKE-147/148; 179 unitários no job separado. Provas reais de histórico por ciclo do mesmo contato, telefone repetido em outra loja, outra equipe, proibição de escrita histórica, revogação I61 e teardown seguro. [Relatório técnico I75D](S1_002_I75D_GOTRUE_HISTORICO_CRUZADO_2026_10_26.md).

**G3 continua PARCIAL.** Revoke I61 **não** equivale a revogação de sessão no SELECT; correção da leitura após logout pertence à S0/Codex principal e deve ser testada de forma independente. Serviços reais de mídia/anexo/download não estão identificados, e D3/D4/retencão/mascaramento precisam de contrato de Produto/LGPD/S0. Nenhuma migration foi promovida; sem alteração de núcleo S0, `main`, Meta, produção ou Issue #3. A correção sintética do primeiro run #40403455399 foi estritamente de formatação de UUID de limpeza; apenas #40403944872 certifica a I75D completa.

## Checkpoint I76 — G1 / 26/10/2026

**I76 certificada em bancada GoTrue real, NÃO homologação operacional G1.** [Workflow oficial #40413807995](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40413807995) sobre commit `781fc839165ae3e420ff6b435f3e1f95b3f2db5a`: **SUCCESS** (jobs GoTrue `121890912677`, unitários `121890913191`), com **7/7 PASS I76-G1-01..07**, regressões I75D 7/7, I74 E2E e encerramento I37/S1INTAKE-148, **179 testes unitários**. Dois Gestores de equipes distintas autorizados à mesma loja veem apenas pendências sem titular, disputam assunção com CAS, produzem um dono por caso e perdem acesso após revogação do grant; nenhum vínculo entre equipes ou grant de laboratório foi mantido. [Relatório I76](S1_002_I76_G1_FILA_MULTIGESTORES_2026_10_26.md).

**Dependência específica G1 na S0:** [Issue #17](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/issues/17) — encaminhar lead da fila sem titular **manualmente a Consultor da própria equipe**, sem confundir com assunção pelo Gestor/auto-distribuição; precisa de A2, caso+atribuição+exceção por caso, CAS, locks e rollback na S0. Não duplicar operação oficial. Outros bloqueios G1: evento de primeiro contato comprovado, UI, Meta, integração operacional e ensaios conjuntos. **PR Draft S0 #16** propõe correção de sessão do histórico G3, ainda não incorporada nem homologada na S1. G1/G2/G3/G4/G5/G6 permanecem abertos como produto; não inferir `% de conclusão` a partir das execuções de bancada.

Nenhuma alteração na `main`, código S0 oficial, banco hospedado ou deploy. Próxima atividade independente: validar a matriz de permissões G2 para o Diretor/chefia, ou prosseguir no G1 com contratos de sinais humanos desde que tenha base S0 verificável.

## Checkpoint I77 — G1/PR Draft #20 — 27/10/2026

**I77 ACEITE TÉCNICO EXPERIMENTAL CERTIFICADO NA PRÓPRIA S1** no commit `de15329dae304583c269b8516b997e4ccdee5a4c`: [workflow #40471384039](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40471384039) **SUCCESS**, jobs `122079118585` (regressão PG17 S1) e `122079118758` (reprodução G1 pinada). I77 **34/34 fontes S1 SHA-256** verificadas sem drift e evento **`ENCAMINHADO`** no mesmo ledger com eventos I54/I56 preservados. Testes G1 **36/36 reais**; unitários PR20 **272/272**; histórico S0 e I63 **38/38**, CFI/F02 **56/56** e SQL legado S1 I54/I56/I57/I58/I61 **34/34**. Artifact `s1-002-i77-pr20-pinned-compatibility`, ID `12718975482`. [Relatório I77](S1_002_I77_G1_PR20_ACEITE_TECNICO_2026_10_27.md).

A reprodução usa checkout do código S0 certificado `d53c40a6ef55e82d2282c482b299cff1dbf990bd` e checkout do HEAD S1 **somente em runner efêmero**, sem copiar runtime, migrations, roles ou arquivo de negócio S0 para S1. O workflow original S0 do PR #20 **não** foi importado. A primeira tentativa #40471191964 falhou por refspec escapado antes da execução G1 e não é aceite; correção somente na sintaxe do workflow.

**G1 continua PARCIAL como produto:** bridge de negócio owner `postgres` requer separação/provisionamento aprovado e revisão por Codex/S0, API/UI, primeiro contato humano, integração produtiva, concorrência de outros escritores e homologação final. [Issue #17](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/issues/17) permanece aberta para conclusão operacional. Nenhuma liberação de `main`, deploy, Supabase hospedado, integração Meta ou Banco. Outros gates G2–G6 continuam em aberto. **Próxima frente independente:** I78/G2 — matriz verificável de Diretor/Gestor/Consultor, unicidade da chefia e ciclo administrativo; não duplicar S0.

## Checkpoint I78 / G2 — 27/10/2026

**I78 certificada somente em laboratório PG17; G2 operacional PARCIAL.** Código `f8268bc35c4701a8b522a66504e080628673b11d`, [workflow oficial S1 #40475205913](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40475205913): **SUCCESS** no job S1 PG17 `122091627557`, **8/8 marcadores I78-G2-01..08**, regressão I75B/I75C, I74 6/6 e rollback de objetos experimentais; job G1 I77 `122091627917` **SUCCESS**, preservando G1 real 36/36, S0/F02 272 unitários, CFI/F02 56 e histórico S0/I63 38. [Relatório I78](S1_002_I78_G2_CHEFIA_DIRETOR_2026_10_27.md).

**Resultado funcional:** já existe índice que garante *no máximo um* Gestor ativo por Consultor; a S1 ainda permite profissional ativo sem chefia, pois não há ativação/onboarding atômicos e papel Gestor global independente de seus subordinados. Função candidata de transferência exclusiva do Diretor com CAS foi testada **apenas em `pg_temp`, BEGIN/ROLLBACK**, sem JWT, endpoint, migration ou autorização de produção. Pausa histórica global I11 não deve substituir pausa de **intake** vigente I51/I52. [Issue #23](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/issues/23) abre fechamento real de G2 (identidade/cargo/chefia, gateway/controles do Diretor, UI e corridas/autorização).

A primeira execução #40474811714 falhou por fixture do Gestor antigo sem subordinados, antes do CAS; correção estrita e nova execução aprovadas, sem mudança estrutural de permissões. **G1 técnico I77 aceito em laboratório**, G1 operacional parcial; **G2 parcial**, G3–G6 continuam em aberto. Sem merge, deploy, Supabase hospedado nem alterações S0/Meta.
