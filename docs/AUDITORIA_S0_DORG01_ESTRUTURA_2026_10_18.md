# Auditoria profunda S0 × D-ORG-01 — identidade Prumo, multiloja e casos

**Data:** 18/10/2026. **Escopo:** revisão orientada ao impacto da decisão D-ORG-01 sobre **todas as migrações S0 versionadas** (001–037, inclusive reparos 034/036A), políticas RLS, serviços `prumo_private`, gateway, `backend/identity_boundary.py`, fixtures, suites PostgreSQL e decisões S0. PR #1 permanece Draft. Este relatório não é uma homologação geral de segurança: examina especificamente o modelo organizacional Prumo.

**Diretriz:** gestores e operadores pertencem à **equipe Prumo**, não às concessionárias; dedicação exclusiva não altera empregador; a mesma pessoa pode atuar em múltiplas lojas por concessão explícita; gestor da Prumo autorizado pode autoatribuir-se caso (D41-04); dados das concessionárias permanecem separados. `DEC-WA-05` continua tratando somente da **titularidade Meta por concessionária**.

## Evidência de inspeção do S0 existente

| Camada | Evidência concreta | Parecer D-ORG-01 |
| --- | --- | --- |
| Identidade | `202610170001_s0_foundation.sql`: `public.atores(id)` referencia `auth.users(id)`; **não contém** `concessionaria_id` nem empregador | **Compatível** com identidade da Prumo centralizada; **não comprova** pertencimento à Prumo |
| Autorização por loja | `public.vinculos_papel_escopo(ator_id,concessionaria_id,papel,valido_desde,valido_ate)`; múltiplas linhas para o mesmo ator | **Compatível** com N concessionárias e concessões independentes; não existe unicidade que obrigue ator a uma loja |
| D2 gerencial | RLS `002`, `004`, `008`, `012`, `016`, `019`, `020`: `EXISTS` por `auth.uid()`, papel e **loja da linha** | Correto como princípio: gestor autorizado pode ver **todas** as lojas concedidas, não uma loja empregadora |
| Operação por caso | `003`, `004`, `008`: casos, `atribuicoes_humanas`, atribuição com FK loja/caso, role atual de gestor/operador, uma atribuição vigente por caso | Compatível com operador Prumo atendendo casos de A e B sem aceder a casos não atribuídos; autoatribuição do gestor já autorizada |
| Revogação | políticas `valido_ate` e atribuição `encerrada_em`, ambas recalculadas em leitura/escrita; `s0_extended.sql` comprova autoatribuição e cessação de leitura após revogar vínculo | Bloqueio dinâmico já existe; **encerramento/rebalanceamento de atribuição após revogação de escopo NÃO é automático** |
| Serviços comerciais C01/C04/C05/C07/C08 | funções privadas verificam `p_ator`, `p_loja` e `v.papel='gestor'`; gateway amarra ator à sessão via `auth.sessions` no fluxo existente | Alinhados quanto ao **escopo declarado por operação**; continuam os limites prévios de `SECURITY DEFINER postgres` |
| Canal/Meta | `canais_loja` e correlatas usam `concessionaria_id`, nunca suposto empregador | Coerente: titularidade App/WABA/emissor da concessionária ≠ pertencimento da equipe |
| Estado comercial | oito valores em `ciclos_comerciais`, independentes de identidade do atendente | Sem alteração D-ORG-01 |

## Achados e decisões

**DORG-S0-01 — nenhuma alteração estrutural obrigatória nas tabelas-base para suportar profissionais multiloja.** Uma identidade única já admite N concessões por `vinculos_papel_escopo`. **NÃO** adicionar `concessionaria_id` obrigatório a `atores`, nem duplicar identidades por loja, nem substituir o escopo por um papel global.

**DORG-S0-02 — pertencimento à Prumo não é atributo verificável do S0 atual — gap real de modelagem pré-produção (prioridade alta).** A existência de `auth.users`/linha em `atores` **não prova que essa pessoa é integrante da Prumo**. Hoje o conjunto de concessões se apoia na ação de cadastramento privilegiada, sem entidade central de equipe/organização, estado do profissional, ou fluxo formal de admissão/desligamento. As permissões SQL não permitem autoconcessão por `authenticated`, o que reduz risco imediato; entretanto, **é preciso definir na S1-002** a fonte autorizada de identidade Prumo, quem valida ingresso/saída, quem emite/revoga concessões, e o efeito do desligamento em todas as lojas. **Não modelar isso como campo `organization_id` controlável pelo cliente.** Nenhum DML/migration para emprego foi inventado por esta auditoria.

**DORG-S0-03 — alocação/dedicação exclusiva e revogação de acesso não são a mesma coisa (prioridade alta antes de operação).** O S0 contém concessão por loja e atribuição vigente por caso, mas **não** representa escala/dedicação preferencial/exclusiva nem transação de redistribuição de carteira ao revogar uma concessão. Revogação bloqueia leitura/escrita pelo profissional (RLS), **mas pode deixar uma atribuição de caso tecnicamente ativa**, demandando remanejamento privilegiado e auditado. S1-002 deve definir estado de alocação organizacional **separado de privilégio**, transferências atomizadas/locks e política de esvaziamento de carteira na suspensão/desligamento.

**DORG-S0-04 — ações de gestor multiloja e autoatribuição são permitidas estruturalmente; suíte específica estava ausente.** `s0_extended.sql` já prova autoatribuição numa única loja, e `s0_isolation.sql` isola gestores diferentes. Faltava regressão explícita de **mesmo gestor A+B**, **mesmo operador designado em A+B**, revogação somente de B mantendo A e comprovação de que o operador sem caso não vê o catálogo. Acrescentado `supabase/tests/s0_dorg01_multiloja_prumo.sql`, **BEGIN/ROLLBACK**, que exercita as políticas já existentes, sem migração nova.

**DORG-S0-05 — papel `responsavel` permanece sem redefinição automática.** `vinculos_papel_escopo.papel` aceita `gestor`, `operador`, `responsavel`, mas o último não autoriza D2 ou escrita operacional nas políticas inspecionadas. Não pressupor vínculo laboral, papel bancário ou representante da concessionária sem decisão específica. Caso esse papel evolua, revisar contrato e origem de identidade, não conceder permissão global.

**DORG-S0-06 — menor privilégio comercial, GoTrue e D3/D4 continuam gates separados.** As experiências 037A–F não transferiram owners comerciais. D-ORG-01 não libera alteração de `SECURITY DEFINER postgres`, grants permanentes, integração bancária, WA real, sessões remotas ou produção. As verificações de `auth.sessions` da cadeia assinada e acesso a D3/D4 permanecem pendências próprias.

## Regressões executáveis propostas no S0

`supabase/tests/s0_dorg01_multiloja_prumo.sql` é integrado ao runner `scripts/run-s0-local.sh` **somente para PostgreSQL 17 descartável**:

- **DORG-S0-01:** uma identidade com várias concessões; atribuição em loja não concedida rejeitada pelo trigger.
- **DORG-S0-02:** gestor Prumo com concessões A+B lê D2 A+B; C, sem concessão, é invisível.
- **DORG-S0-03:** operador com concessões A+B vê apenas casos A/B designados; profissional exclusivo de A sem caso não vê nada.
- **DORG-S0-04:** gestor autoatribui caso A e pode registrar mensagem sintética; ex-operador deixa de enxergar A.
- **DORG-S0-05:** revogar apenas B corta acesso B para gestor e operador, preserva acesso A e identidade Prumo; a atribuição B ainda existe para futura rotina de redistribuição.
- **DORG-S0-06:** identidade autenticada sem concessão não pode acessar dados de loja nem conceder papel a si mesma.

**Status:** validação ainda depende do CI do commit. Não marcar PASS antes de inspecionar os logs.

## Parecer preliminar

**Sem reconstrução do S0.** Há **mudanças necessárias antes da S1 conectada**: (a) contrato de pertencimento/ciclo de vida da equipe Prumo com emissão e revogação privilegiadas; (b) gestão de escopos múltiplos e escala exclusiva separada de permissões; (c) redistribuição auditável de casos quando profissional perde acesso; (d) prova integrada com GoTrue/RLS e transações reais. Proponho esses itens como requisitos/gates de **S1-002**, não como migrations prematuras S0. O reforço de testes S0 é aditivo, reversível e não altera a semântica comercial existente.
