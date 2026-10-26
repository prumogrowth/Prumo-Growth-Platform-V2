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
