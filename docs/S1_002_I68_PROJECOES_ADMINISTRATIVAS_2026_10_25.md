# I68 — projeções administrativas mínimas e contagens sem exposição de cabeçalhos

**25/10/2026. Candidato apenas no PG17 e Supabase CLI descartáveis; nenhum deploy.**

## Risco corrigido no candidato

O I67 restringe **linhas**, mas a autorização original S0 concedia `SELECT` irrestrito de **colunas** em `itens_lote`, `reencontros_lote` e `eventos_status_comercial`. Um usuário poderia consultar `SELECT *` sobre sua própria linha e obter campos irrelevantes para a interface, por exemplo motivo de rejeição, metadados ou status anterior. Isolamento por equipe não implica automaticamente minimização de dados.

O candidato `supabase/tests/s1_096_admin_projection_invoker_candidate_local_only.sql` retira os três grants de tabela e concede apenas colunas explicitamente permitidas ao papel `authenticated`. Não muda RLS I63/I64/I67 nem adiciona `SELECT` a `anon` ou `service_role`. **Projeção de colunas permitidas também na exportação REST; `select=*` ou campos não autorizados devem ser rejeitados.**

## Metadados compartilhados sem desbloquear tabelas

São criadas duas **views PostgreSQL 17 com `security_invoker=true`**, no schema `public`, com `GRANT SELECT` somente a `authenticated` e sem SECURITY DEFINER. Sua consulta depende das RLS e ACL das próprias tabelas-base. A view de lote `s1_68_lotes_equipe` retorna somente `concessionaria_id, lote_ref, itens_autorizados`, onde a contagem considera **itens aceitos efetivamente visíveis para o Gestor** — nunca total do lote. A view `s1_68_canais_equipe` retorna somente `concessionaria_id, canal_ref, conversas_autorizadas`, condicionada a concessão vigente de `gestor` à concessionária e às conversas visíveis ao próprio usuário via I63. Não lê `canais_loja`, `lotes_importacao` nem identificadores de emissores. Os cabeçalhos permanecem sob quarentena I64.

Os UUIDs retornados são referências opacas de objetos compartilhados, não os conteúdos dos cabeçalhos. O aplicativo deverá usar nomes amigáveis autorizados em contrato separado, caso necessários. Estas views **não são endpoint de exportação de produção**: só prova local de viabilidade de projeção agregada com invoker-RLS.

## Evidência e limites

O aceite PG17 `supabase/tests/s1_097_admin_projection_invoker_aceite.sql` simula dois Gestores em um lote/canal compartilhado; exige contagens específicas e distintas, bloqueia leitura de colunas proibidas, comprova que a sessão de um Consultor não ganha resumo administrativo e testa corte imediato após expirar grant. A prova GoTrue real repete via HTTP e verifica que `select=*` das três tabelas resulta em negação de coluna. Todos os objetos são descartados por ROLLBACK ou exclusão da stack efêmera.

**Atenção:** bloquear motivos/PKs/status anterior pode exigir adaptação de consumidores legítimos ainda não inventariados. D2/D3/D4 não foram liberados de modo amplo, acesso legado I66 permanece fechado, e este candidato não altera banco hospedado nem serve como autorização de publicação.

## Prova HTTP com token real

`scripts/test_s1_002_i68_admin_projection_e2e.py` reutiliza os dois Gestores de I67 e adiciona uma conversa simulada ao canal compartilhado para a segunda equipe. Comprova antes da mudança que uma coluna excedente (motivo de rejeição) podia ser solicitada via Data API. Depois do candidato, confirma negação de `select=*` e campos retirados, preservação de projeções explicitamente permitidas, segurança invocadora das duas views, contagem de **1 item por Gestor** no mesmo lote e **2 versus 1 conversa** no mesmo canal, negação ao Consultor excepcional/anon, manutenção de cabeçalhos privados e corte imediato na mesma sessão após revogar a concessão à loja. Logs pendentes de certificação.

## Certificação final de laboratório — 25/10/2026

**PostgreSQL 17: SUCCESS.** [Workflow #40197800959](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40197800959), job `121182342749`, commit de implementação `b59e958f6c849b655579892e877f2b919aba1427`. Logs conferidos: `PASS I68-01` a `PASS I68-09` — **9/9**. Comparadas duas equipes em mesmo lote e canal; bloqueadas colunas indevidas (ID da linha, motivo da rejeição, motivo do reencontro e status anterior); consultor excepcional não recebe contagens; revogação da loja elimina imediatamente as contagens. Conjunto de testes S0+S1 I52–I68 passou e políticas/dados sintéticos reverteram por `ROLLBACK`.

**GoTrue real + PostgREST: SUCCESS.** [Workflow #40198009571](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40198009571), jobs `121182958762` (E2E) e `121182958677` (unitários), ambos SUCCESS; commit testado `28be93f58d2eff4e5e98852769c5a4d76a5eff49`. Logs `PASS I68-E2E-01` até `PASS I68-E2E-08` — **8/8**. Antes da restrição, confirmou-se que a role conseguia pedir campos extras; depois, `select=*` ou seleção de colunas retiradas devolvem negação real de banco. Projeções autorizadas funcionam. Duas equipes veem `1` item autorizado cada no lote físico compartilhado; no canal compartilhado, as contagens são `2` e `1` conversas, respectivamente; nenhuma leitura bruta de cabeçalhos é concedida. Consultor excepcional e `anon` não leem as views. Revogação e restauração de concessão funcionam com o **mesmo JWT**. As regressões I67 e anteriores seguiram verdes.

**Inspeção de superfície SQL:** ambas as views são `security_invoker=true`, não `SECURITY DEFINER`; o scanner catalogal I65 retorna zero exposições do tipo proprietário. As políticas e ACL I63–I67 continuam vigentes somente nas fixtures locais. Nenhum operador recebeu acesso global a cabeçalho, nome/chave de importação ou identificador de emissor.

### Limites reais

O certificado cobre o PostgreSQL 17 e a stack GoTrue/PostgREST **efêmera**, não o Supabase hospedado nem a configuração real de schemas/roles. As projeções ainda podem revelar UUIDs opacos compartilhados, números de casos acessíveis por conta e outros metadados mínimos; isso demanda avaliação de UX, minimização e necessidade legítima antes de permitir exportação externa. É necessário inventariar outros consumidores que ainda esperam `SELECT *` e revisar permissões em tabelas de casos/conversas/mensagens, além de limites de paginação, taxa, auditoria de exportações e mascaramento. **Não houve deploy, migration hospedada, alteração na main ou publicação de endpoint de produção.**
