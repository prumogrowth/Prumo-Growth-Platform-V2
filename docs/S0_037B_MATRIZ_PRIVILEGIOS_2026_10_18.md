# S0-037B — Matriz executável de RLS e DML comercial (somente ensaio negativo)

**Data:** 18/10/2026. **Status:** proposta de prova sintética; verificar CI antes de declarar aceite. Frente principal: PR #1 `feat/s0-fundacao-prumo`; contrato Meta permanece separado no PR #2, ambos Draft. DEC-WA-01/02/03 e DEC-WA-05 preservadas. DEC-WA-04/06 seguem pendentes.

## Objetivo e limites precisos

O S0-037A comprovou que `ALTER OWNER` direto nas wrappers `gateway_cancelar_plano_s0` e `gateway_conciliar_c07_s0` quebra as funções `SECURITY INVOKER` legadas (`current_user='postgres'`) e que `SELECT` não atravessa uma RLS sem política. Este incremento testa **somente** o que permissões estritas por loja permitem em SQL de laboratório e quais gates de sessão/auditoria ainda faltam.

**Não há migration nova, alteração de RLS operacional, role/conta persistente, novo worker, HMAC, segredo real, canal, envio WhatsApp nem execução no Supabase hospedado.** O arquivo `supabase/tests/s0_037b_matriz_rls_escrita.sql` inicia `BEGIN`, cria `prumo_s0_probe_037b` temporariamente, habilita grants e políticas exclusivamente **para IDs fictícios constantes** (loja A), executa ensaios e termina com `ROLLBACK`. Não confiar em `current_setting` arbitrário fornecido por uma sessão como evidência de tenant/autorização. A função C08/C07 comercial real não é reescrita nem chamada sob owner substituto.

## Matriz de dependências (não é plano aprovado de GRANT permanente)

| Operação | Recurso / capacidade do algoritmo original | Prova 037B / gate |
|---|---|---|
| C08/C07 | `auth.sessions` consulta com `FOR KEY SHARE`, `user_id=ator`, sessão viva | **Bloqueado para papel probe**; jamais conceder `SELECT` irrestrito ao owner técnico; precisa modelo seguro de sessão + trava/revogação |
| Ambas | `vinculos_papel_escopo` gestor ativo, escopo e `statement_timestamp()` | Modelo operacional exige gestor autenticado e vínculo válido; probe usa escopo constante de teste, **não autentica gestor** |
| C08 | `leads_loja` SELECT+lock; `planos_recontato_sinteticos` SELECT/FOR UPDATE+UPDATE; `envios_template_sinteticos` SELECT/FOR UPDATE+UPDATE; `eventos_envio_template_sinteticos` INSERT | Ensaio verifica leitura loja A, negação loja B, UPDATE com `versao=1` e trilha append-only, **sem teste de sessão/lock end-to-end** |
| C07 | `pendencias_reconciliacao_c07_sinteticas` SELECT/FOR UPDATE+UPDATE; `eventos_callback_sinteticos`, `envios_template_sinteticos`, `planos`, `leads` SELECT/locks; `associacoes_callback_c07_sinteticas` INSERT opcional; `auditoria_reconciliacao_c07_sintetica` INSERT | Ensaio apenas `ENCERRAR_SEM_PROVA` sintético em A, com versão+auditoria. **VINCULAR_SINTETICAMENTE** e locks integrados ainda exigem prova distinta |
| Ambas | `prumo_private.auditoria_gateway_s0` INSERT e fingerprint da sessão | Tabela privada sem proteção RLS específica para um novo owner; **não recebeu INSERT/SELECT**. Gate bloqueante |
| Ambas | `prumo_s0_signer` HMAC/nonce e `prumo_s0_signed_executor` | Sem mudança. O papel `prumo_s0_gateway` continua com somente duas entradas assinadas; papel probe não ingressa na cadeia |
| Auditoria | triggers/constraints de eventos C07 e C08; validação de CAS e escopo de FKs | Ensaio de SQL direto com FKs/RLS apenas; não afirma que isso reproduz atomicamente o código do domínio |

## Exposição deliberada do perigo de GRANT

No experimento, o papel probe recebe temporariamente `UPDATE` em colunas de estado comercial técnico e `INSERT` em tabelas de auditoria escopadas. Isso prova **somente** que um acesso de escrita SQL pode alterar A e não B na política artificial. Como esse acesso **não está ligado a uma validação HMAC, sessão, ator e finalidade**, **seria inseguro mantê-lo em qualquer role autenticável ou passá-lo ao gateway real**. Por isso, todos os GRANTs, policies e dados são revertidos; nenhum deles integra uma migration. `BYPASSRLS` e `SUPERUSER` jamais são concedidos.

As verificações OWNER37B-01..05 caracterizam respectivamente: cenário de A/B com telefone igual e pendências separadas; RLS/versão e cancelamento sintético de A; C07 encerramento sintético de A com auditoria; inacessibilidade de dados de B, da auditoria privada e das funções comerciais; e não alteração dos grants da cadeia real. A correlação de callbacks WA-01C, `statuses[].id` e os bloqueios de dedupe permanecem fora do escopo.

## Gates pendentes para eventual mudança comercial real

1. Projetar o verificador de sessão com escopo mínimo e **revogação imediata** sem oferecer ao papel de domínio SELECT irrestrito em `auth.sessions`; comprovar a semântica do lock durante o commit.
2. Projeto completo de `FOR UPDATE`, `WITH CHECK`, tabelas de auditoria privadas e FKs/triggers para **ambas** as decisões C07 (`ENCERRAR_SEM_PROVA` e `VINCULAR_SINTETICAMENTE`) sob role sem `BYPASSRLS`.
3. Redesenhar a verificação interna `current_user='postgres'` sem torná-la um bypass por `SET ROLE` ou um parâmetro/GUC controlado pelo cliente.
4. Evitar que SQL direto contorne HMAC+nonce; comprovar sessão/loja/versão/idempotência em uma **única** função transacional autorizada.
5. Preservar concorrência, locks, trilha de auditoria e a matriz gestor/operador, inclusive cross-store, replays, sessão revogada e negação sob papéis `anon`, `authenticated`, `service_role`, `prumo_s0_gateway`.
6. Homologar a futura migração no PostgreSQL 17 **e** GoTrue/PostgREST Supabase **local gerenciado** antes de qualquer merge/deploy.

**Resultado interpretável:** GO para análise de RLS em dados fictícios; **NO-GO** para transferir as duas wrappers ou habilitar worker comercial. A saída deste ensaio é matriz/prova de limitação, não autorização de operação ou arquitetura final de permissões.

## Aceite efetivo do ensaio PostgreSQL — 18/10/2026

[**GitHub Actions PostgreSQL 17 #39126117200 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39126117200), commit de código `bd6772ce82a86ec8591cbb161d83e5f14f09bfdf`. Logs inspecionados: `OWNER37B-01..05 PASS`, todos os testes SQL e de concorrência prévios, **24 testes Python — OK**; nenhum erro do job.

**Conclusões estritas:** em duas lojas fictícias, com mesmo telefone de contato em leads comerciais distintos, o papel transitório `prumo_s0_probe_037b` com políticas explícitas de loja A só pôde ler/atualizar registros A; o UPDATE versionado de plano/envio C08 e o encerramento fictício de pendência C07 mais seus registros de auditoria passaram. A loja B permaneceu oculta e sem alterações. **Todos os grants, policies, dados e role desse experimento foram revertidos pelo `ROLLBACK`.**

**Não aprovado:** esta prova não representa a implementação real de `FOR UPDATE` com sessão GoTrue, não verifica HMAC/nonce em cada UPDATE direto, não fornece autorização de gestor, não inclui a decisão C07 `VINCULAR_SINTETICAMENTE` e não resolve a escrita em `prumo_private.auditoria_gateway_s0`. Conceder o mesmo DML diretamente ao gateway real seria um bypass da cadeia de autorização. As duas wrappers comerciais continuam `SECURITY DEFINER postgres`.

**Auth/REST:** este incremento não alterou migrations/runtime/ACL persistentes; o workflow GoTrue/PostgREST local não foi repetido aqui. Última evidência integrada da baseline [#39122948236 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122948236).

**Decisão técnica:** seguir apenas para elaboração de um modelo autorizado de sessão/escopo/execução que elimine o DML SQL direto, acompanhado por plano de testes completo das duas alternativas C07, de concorrência, de revogação de sessão e de auditoria. Nenhum deploy, merge ou acesso comercial autorizado.
