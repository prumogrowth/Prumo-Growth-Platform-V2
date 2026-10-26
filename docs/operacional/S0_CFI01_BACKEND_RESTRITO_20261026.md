# S0 — CFI-01 consolidado, privilégios por coluna e auditoria transacional

26/10/2026. Continuidade de `060b472b03e9e7b89f5b3d7e19b72b98836f106d`, PR #4. Branch própria: `exp/s0-cfi01-principal-restrito-20261026`. **Backend executável e comprovado em ambiente descartável; não é aprovação de implantação ou contrato UI/F03.**

## Problema escolhido e resultado útil

A operação existente `capture_human_closure` / `recheck_human_closure` já autenticava no GoTrue e assinava uma transação SQL. Contudo, o checkpoint S0 dependia de um segundo checkout (`9488917`) para importar seu runtime; o executor tinha SELECT/INSERT por tabela e UPDATE de domínio além das colunas de lock, as três tabelas privadas não tinham RLS e cada recheck deixava apenas um nonce, sem trilha explícita da operação. A validação da resposta SQL em Python ocorria **depois** do COMMIT.

Esta proposta consolida **os mesmos sete módulos existentes** no backend S0 e melhora seu caminho atômico. Agora o servidor S0 pode importar `S0CFI01AtomicCommandsLocal` e `S0CFI01CommunicationLocal` do próprio checkout e executar captura/recheck, autenticando no GoTrue, validando sessão/permissões no banco e persistindo nonce, recibo técnico e auditoria juntos. O processo usa somente o login SQL restrito; não abre conexão postgres para executar a operação. Postgres aparece no provisionamento e nas asserções administrativas do laboratório.

A função continua sendo **recibo técnico de revisão**, não fechamento comercial, extração F03, envio ou escrita em ficha. A operação é existente e interna ao servidor; não foi criada rota HTTP, comando UI ou arquitetura alternativa.

## Código reaproveitado e mudanças

- Origem fixada: `948891714f632adb6179cf3a11f362a6eb914f91`. `integration/cfi01/runtime_sources.json` guarda SHA, blob e SHA256 **originais** dos 16 arquivos selecionados; hashes originais não afirmam igualdade dos arquivos modificados.
- Sete módulos consolidados: `s0_cfi01_atomic_commands_local`, `s0_cfi01_authenticated_commands_local`, `s0_cfi01_signed_prerequisite_local`, `s0_human_closure_event_local`, `s0_human_closure_recheck_local`, `s0_s1_closure_authority_local`, `s0_cfi01_f03_receipt_bridge_local` em `backend/`. Seis preservam bytes da origem. A biblioteca antiga de comandos privilegiados permanece referência de laboratório, sem registro de rota; a fachada atual exige o gateway atômico concreto.
- `backend/s0_cfi01_atomic_commands_local.py`: decodificação/validação de todos os campos da resposta dentro da conexão transacional; resultado inválido lança recusa e provoca rollback antes de retornar. Conexão só faz COMMIT após validação. Assinatura, TTL, payload e enum de resultados preservados.
- Quatro testes unitários de runtime reaproveitados; juntamente com os 58 existentes, somam **156 testes locais**. Os 20 de compatibilidade entre frentes estão preservados.
- Quatro fixtures recuperadas em `supabase/tests/s0_cfi01_*local_only.sql`, com mudanças concentradas em `s0_cfi01_atomic_owner_local_only.sql`. Não são migrations de produção.
- `scripts/test_s0_cfi01_auth_rest_local.py`: recupera os dez cenários reais originais; acrescenta somente o opt-in SQL de instalação na mesma conexão psql.
- `integration/cfi01/test_restricted_backend.py`: herda os **14 testes do checkpoint sem modificá-los** e acrescenta 14 cenários, sobre a implementação real. Chaves HMAC e senha SQL aleatórias geradas no laboratório; a chave publicada na fixture é desativada antes desta suíte.
- `.github/workflows/exp-s0-cfi01-restricted-backend.yml`: executa o próprio checkout, sem segundo checkout/runtime externo. CLI Supabase 2.84.2, driver psycopg 3.2.9 e Node22. Workflows oficiais preservados.

Commits de implementação: `804683482fd0cb1da967997ab68eee4c914f788d` (consolidação, RLS e auditoria); `1cd15ae3cff916e783f5cf29e8bb6547a68d0472` (verificação explícita do executor no teste e prova pré-assinada de expiração); `1b4f2841d513fb971c93379636414bf686784beb` (grants por coluna). O último commit de documentação não altera o código certificado.

## Fronteiras de autenticação e autorização

1. `SupabaseGoTrueVerifier` existente chama `/auth/v1/user` real; só depois usa sub/session_id para vincular a sessão ao usuário verificado. Não confia em ator, loja, permissões ou `user_metadata` fornecidos no payload.
2. O backend assina o material CFI existente com operação, ator, sessão, caso, versão física de ciclo, evento, chave de idempotência, key_id, timestamp e nonce. A senha SQL não substitui essa assinatura.
3. A função privada exige o login SQL específico, HMAC válido e chave ativa, então consulta a sessão real e faz os gates existentes de equipe S1, concessionária ativa, caso/ciclo/atribuição e concessão.
4. A sessão deve existir, pertencer ao ator e ter `not_after` nulo ou futuro. O helper agora usa **FOR SHARE**, que também serializa atualização de `not_after`, além da exclusão por logout. O instante da verificação é o ponto de autorização da sessão na transação; não se promete monitoramento contínuo do relógio até a resposta de rede.
5. Ordem mantida: chave HMAC → sessão → equipe S1 → caso/ciclo/loja/atribuição → concessão → conversas → mensagens → recibo → nonce/auditoria. Não muda a ordem preexistente das transações CFI; não aprova uma ordem global com futuras operações S1/Meta. Os locks são exercitados com relações reais `pg_blocking_pids`, não somente sleeps.
6. Permissões, novas mensagens, versão e metadados do recibo são revalidados na mesma transação. Não converte versão de caso em ciclo nem revisão em APPLIED.

O helper de sessão é a exceção privilegiada preservada: `postgres` é seu owner porque o Supabase reserva a tabela `auth.sessions`; recebe apenas actor/session e devolve booleano sob lock. O executor não recebe USAGE em auth, SELECT de sessões nem EXECUTE público no helper. A exceção é parte da base de confiança e precisa de revisão antes de implantação.

## Privilégios e auditoria

| Superfície | Resultado implementado |
|---|---|
| Login SQL da aplicação | Sem direitos diretos em sessão, caso, mensagem, chave, nonce, recibo ou auditoria; não pode assumir o executor. Rota antiga `cfi01_signed_prerequisite_local` selada para esse login |
| Owner do executor | NOLOGIN, NOINHERIT, NOSUPERUSER, NOBYPASSRLS, NOCREATEROLE, NOCREATEDB, NOREPLICATION; `search_path` vazio |
| SELECT | Somente colunas efetivamente consultadas em onze tabelas. Não lê `casos_humanos.lead_id`, `mensagens.id_externo`, timestamps de recibo/nonce nem herda novos campos por grant de tabela |
| INSERT | Somente colunas usadas em nonce, recibo e auditoria. Não pode fornecer `recorded_at` da auditoria |
| Locks | UPDATE somente na coluna de identidade necessária; policies UPDATE com `USING true / WITH CHECK false` impedem DML. Teste negativo comprova `current_user` antes de tentar UPDATE; falha de GRANT não conta como recusa de DML |
| RLS privado | Habilitado em chaves, nonces, recibos e nova auditoria; policies específicas do owner. Roles API não ganham acesso |
| Recibos e auditoria | Triggers recusam UPDATE/DELETE/TRUNCATE, inclusive tentativa comum do instalador. Administrador capaz de alterar/remover DDL permanece fora dessa garantia |
| Nova auditoria | Uma linha por nonce aceito: operação, ator/sessão, loja/caso/versão, key_id, recibo, resultado e timestamp do banco. Sem Bearer, segredo, MAC ou conteúdo de mensagem |
| Atomicidade | Auditoria, nonce e recibo na mesma transação. Falha no INSERT de auditoria ou resultado SQL inválido desfaz todos; retry com a mesma chave lógica permanece seguro |

`cfi01_command_audit_local` é trilha técnica interna e privada. Não é histórico comercial ou autorização para a S1 exportá-la. Retenção, consulta operacional e LGPD dessa trilha precisam de decisão antes de produção. Recusas não deixam uma linha de **sucesso** nesta tabela; auditoria durável de tentativas negadas requer um sink protegido fora da transação abortada e não foi falsamente certificada aqui.

SELECT policies do executor usam `USING true` sob role inacessível, enquanto a função confere o escopo autoritativo; não se afirma que o owner tenha RLS por usuário final. Postgres continua owner das tabelas de laboratório. Não se adicionou BYPASSRLS nem owner superprivilegiado ao executor.

## Testes e evidências

O JSON adjacente registra runs/jobs/SHAs/steps e linhas de log conferidas.

**CI final: [40323084692](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40323084692), job `121572723132`, SUCCESS no SHA exato `1b4f2841d513fb971c93379636414bf686784beb`.** Logs conferidos: 156 unitários, 18 famílias Auth/REST, dez marcadores CFI originais, 28 cenários reais do backend restrito e `Stopped supabase local development setup.` Nenhum teste ignorado na suíte final.

| Camada | Evidência |
|---|---|
| Local, sem banco | 156/156 Python; inclui testes S0 existentes e 98 testes de runtime reaproveitados |
| Local, PG17.11 | Instalação SQL, ownership e RLS; 28 testes físicos CFI reaproveitados (57–84 da origem), inclusive concorrência. **Identidade sintética**, não certificados como GoTrue |
| CI, Auth/REST real | Regressão original AUTH-01–18 e negativas adicionais; GoTrue/PostgREST/RLS reais |
| CI, CFI real original | Dez marcadores CFI01-AUTH-01–10, executando o backend consolidado e SQL com as restrições novas |
| CI, backend restrito | 28 cenários reais: 14 herdados do checkpoint e 14 adicionais, com chave/senha aleatórias e chave publicada desativada |

Cenários adicionais 15–28: login mínimo/portas seladas; UPDATE negado sob owner real; captura e recheck auditados; rollback por falha de auditoria; sessão expirada após MAC emitido; revogação de chave e chave publicada recusadas; replay sem auditoria extra; logout bloqueando em transação; revogação de chave aguardando COMMIT; imutabilidade; resposta SQL adulterada que causa rollback; mesmo operador em duas lojas, mesmo telefone e revogação isolada; expiração de sessão concorrente aguardando lock; privilégios por coluna.

O teste de resposta malformada altera **somente a projeção SQL retornada**, mantendo função SQL, GoTrue, assinatura, gravação e banco reais. Isso força o ramo de validação antes do COMMIT; não é stub de autorização nem prova de integração externa.

Revisões anteriores `8046834` e `1cd15ae` passaram seus CIs completos; a revisão final reduziu colunas e também passou sua recertificação completa no SHA exato. Não houve retry de uma falha para declarar sucesso. Container local desta missão removido; cleanup do Supabase do CI deve aparecer nos logs antes do aceite.

## Compatibilidade com S1 e Frontend

Inspeção somente leitura dos checkpoints recentes:

- S1 `3158dbe5e5fe0c10fa5ed437f245c4c9f02a34a2`: tabelas canônicas compartilhadas mantidas; a fixture de equipe 038 é **byte a byte idêntica** à migration `202610180038_s1_equipe_prumo_gate.sql` nesse SHA. Gate de equipe permanece uma condição adicional às concessões e atribuições S0, não uma permissão comercial nova.
- Export S1 nesse SHA continua blob `cb9fb9cf541308fdec1c5c21f6ee02a7a6675145`, já fixado pelos testes de compatibilidade. I74 e PR #6 preservados. O inventário G3/I75B não certifica mídia ou acesso à auditoria nova; nada foi promovido a aprovação G1–G6.
- Frontend `a042ddfed08a7638ebfea3651c294e9058eb86ca`: `frontend/visual/s0-command-result.mjs` continua blob `044cfb95fee6eb8916dadf7de6f77aecdd3d2471`, igual ao contrato fixado. As mudanças recentes são preview/documentação/CI, sem comando CFI operacional ratificado.
- `backend/s0_communication_contract.py` e os 14 cenários transacionais originais permanecem inalterados. `VERIFIED_CONTRACT_PENDING` e projeção `CONTRACT_PENDING` continuam verdadeiros limites; metadados internos não viram payload autorizado para modelo ou cliente.
- Meta/PR #7 e I74/PR #6 não foram copiados, retrabalhados ou incorporados. Nenhuma branch dessas frentes foi alterada.

## Reproduzir, limitações e próximo checkpoint

No próprio checkout desta proposta, usar somente CLI Supabase local **não vinculada**:

```sh
python3 -m pip install -r backend/requirements-s0-local.txt
python3 -m unittest discover -s backend/tests -v
supabase start --exclude realtime,storage-api,imgproxy,mailpit,postgres-meta,studio,edge-runtime,logflare,vector,supavisor
PYTHONPATH=. python3 scripts/test_s0_auth_rest_local.py
PYTHONPATH=. python3 scripts/test_s0_cfi01_auth_rest_local.py
PRUMO_CFI01_TRANSACTIONAL_TEST=YES PYTHONPATH=. python3 integration/cfi01/test_restricted_backend.py
supabase stop --no-backup
```

Sempre remover o stack em finally/cleanup, inclusive em falha, como no workflow. Fixtures usam credenciais publicadas de teste na instalação; não reutilizar em nenhum ambiente persistente. A suíte restrita substitui a senha por valor aleatório e desativa a chave publicada. Não há provisionador de segredo produtivo, migração hospedada, endpoint público ou DSN remoto liberado. Instalação é para banco novo, com opt-in `prumo.cfi01_disposable=YES`, PG17 e postgres; nome de banco/opt-in não tornam um banco hospedado permitido.

Skill Supabase consultada: documentação atual de segurança Data API/RLS por MCP; changelog público bloqueado pelo proxy (403). Nenhum tool de projeto hospedado foi chamado.

**Próximo checkpoint técnico:** SHA executável `1b4f2841d513fb971c93379636414bf686784beb` nesta branch, com CI final aprovado e logs conferidos. `060b472` permanece ponto de origem da S0/PR #4; esta proposta está pronta para revisão, sem merge automático.

**Bloqueios realmente pendentes:** comando e projeção UI→S0; binding de versões caso/ciclo/atribuição/ficha/catálogo; dados minimizados e autoridade F03/OAI-05/07; desenho produtivo de custódia/rotação/instalador; retenção e consumo autorizado da auditoria; ordem global de locks interfrentes; observabilidade e auditoria durável de recusas. Nenhum foi preenchido com valor fictício para dizer que a plataforma está pronta.

**Próximo avanço recomendado:** ratificar o contrato mínimo UI/S0 de captura/recheck, reutilizando este executor, e definir a consulta técnica autorizada da auditoria. Enquanto isso, manter a operação interna ao backend; não conectar a prévia Frontend nem transformar recibo em atualização comercial. Ainda não há plataforma produtiva, integração Meta real ou autorização de deploy.
