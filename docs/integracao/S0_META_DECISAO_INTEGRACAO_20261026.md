# S0 / WhatsApp–Meta — avaliação e preparação de integração

Data: 26/10/2026. Responsável: Codex/S0. **Decisão: aceitar o reaproveitamento experimental com as adaptações abaixo; integração operacional bloqueada.** Não autoriza merge, deploy, migrations hospedadas, IAM real, webhook público, Graph API, ACK ou envio. PR #6/I74 não foi reimplementado.

## Checkpoints recuperados

| Frente | SHA recuperado | Papel nesta avaliação |
|---|---|---|
| S0 / PR #4 | `060b472b03e9e7b89f5b3d7e19b72b98836f106d` | Base da branch própria; captura/recheck CFI-01 e seus testes preservados |
| Meta / PR #2 | `04c2a355bf8ab5765855f82ab3de2062e2d5bd67` | Auditoria e handoff obrigatórios lidos integralmente; somente documentos depois do código certificado |
| Meta, código | `cb4b27f2ec3ea77c0f8305c3c87387bddc5c7d6d` | WA39–68, 823 verificações históricas; CI original 40297190899 |
| Runtime CFI-01 | `948891714f632adb6179cf3a11f362a6eb914f91` | Fonte fixada pelo workflow S0 real; não adiciona/altera migrations compartilhadas |
| S1 | `6a40448` | Inclui adoção I74 `ad252bd`, certificação `c1828f3` e proposta I75; sem alteração nesta missão |
| I74 / PR #6 | `8e91bd9f1e7d1e80d677d8334a529a58782c978c` | Dependência já entregue; nenhuma cópia de implementação |

Branch própria: `exp/s0-meta-integracao-auditoria-20261026`, descendente da S0, sem merge/cherry-pick das frentes. Base compartilhada S0/Meta: `75095fe`. Os 86 caminhos do PR Meta (84 originais + dois documentos) foram inventariados; as 12 migrations e módulos centrais de ingestão/ponte/parser/HTTP foram revisados. Isso não constitui pentest ou revisão linha a linha de todos os testes históricos.

## Diagnóstico de compatibilidade

- **Schema:** Meta acrescenta 043–054 à mesma base 001–042; não altera os módulos de backend S0. A composição verifica igualdade de **cada migration compartilhada** antes de materializar qualquer arquivo. Divergência futura aborta; não substitui schema atual por uma cópia histórica. CFI-01 usa fixtures próprias sob `supabase/tests/`; ausência de conflito de nomes não comprova integração transacional entre as duas rotas.
- **Tenant/canal/tentativa:** WA45 seleciona registry e binding internamente; SQL confere concessionária, canal, app, WABA, phone, intenção, attempt, correlation, recipient e wamid. O evento externo não escolhe concessionária. `tenantRef` do laboratório é um alias técnico; não se converte automaticamente em `store_ref` UUID do CFI-01/S1.
- **Identificadores:** `WA46_...` é SHA-256 de `[WABA,phone,wamid,recipient,status,timestamp]`, não ID oficial de callback Meta. `bodySha256` cobre bytes brutos e difere entre variantes; não equivale ao digest da conversa CFI-01 nem ao digest de metadados F03. `bindingRevision` é verificado por portas de laboratório antes da emissão; não é versão de caso/ciclo/atribuição aprovada nem integra o wire SQL de 15 campos.
- **Protocolos:** HMAC externo bruto, HMAC interno `prumo-meta-handoff-lab-v1|FORENSIC_APPEND_ONLY|...` e provas humanas GoTrue/S0 são domínios distintos. WA34 JSON não é wire-compatible com S0/044. Não houve tradução de assinatura, reutilização de chave, bypass de sessão ou contrato UI→S0 inventado.
- **Estados:** `sent/delivered/read/failed` viram observação forense não verificada. `LAB_*` não equivale a entrega, autorização de envio, fechamento, APPLIED ou alteração de caso. HTTP 202 é recibo de loopback. Flags comerciais continuam falsas, mesmo após cancelamento ou replay.
- **Frontend/OpenAI/F03:** callback forense não entra como mensagem inbound, conversa elegível, recibo CFI-01, evidência F03 ou proposta de campo. A composição executa os 58 testes atuais, incluindo compatibilidade fixada das outras frentes. Não conecta essas superfícies sem contrato aprovado.
- **S1:** revogação de concessão/equipe/atribuição humana não é a revogação de chave técnica Meta. A transação CFI-01 real já tem evidências separadas; as WAs não provam autorização S1. Não foi feito teste conjunto GoTrue+Meta nesta missão nem se afirma que exista rota operacional entre elas.

## Auditoria das 12 migrations

Todas continuam **fixtures não publicáveis**, disponibilizadas por patches fora de `supabase/migrations/`. Números abaixo são sufixos `2026102300NN`. Dependem da base S0 e pgcrypto; papéis finais são restritos, mas instalador/proprietários históricos incluem postgres e associações administrativas de laboratório. Não são instaladores idempotentes de Supabase gerenciado.

| Migration | Dependência/efeito e risco | Decisão |
|---|---|---|
| 43 `status_forense` | Depende 040–042/outbox. Tabelas RLS, histórico imutável, trigger de vínculo sem FK para preservar negativa TRUNCATE. Writer invoker postgres; sem guard individual original | **Adaptar:** guard inicial e transação; aproveitar invariantes/testes, não owner postgres operacional |
| 44 `handoff_assinado` | Depende 43 e roles S0. Chave/nonce próprios, material 15 campos, TTL -30/+5 s. Wrapper definer postgres e SET ROLE de teste; sem guard de banco original | **Adaptar:** guard/transação; **rejeitar uso operacional** dessa identidade/owner |
| 45 `isolar_verificador` | Depende 44. Signer NOLOGIN com SELECT de segredo e INSERT nonce; wrapper de domínio ainda postgres. Associação SET administrativa persiste na fixture | **Adaptar:** guard/transação; custódia/instalador reais pendentes |
| 46 `key_revocation_lock` | Depende 45. Advisory `wa42-meta-key` compartilhado entre verificação e revogação até COMMIT. Sem guard de banco original; não é revogação S1 | **Adaptar:** guard/transação; aproveitar prova de revogação técnica |
| 47 `shadow_non_superuser` | Depende wire 44/pgcrypto. Executor restrito, cliente sintético, chave/nonce/shadow próprios. Não escreve histórico original | **Aproveitar** como regressão de privilégios; instalação isolada/atômica; **rejeitar shadow como entrega final** |
| 48 `scoped_non_superuser` | Depende 47/040–042. SELECT policies USING true para join técnico, sem snapshot de estado bloqueado | **Aproveitar** como teste histórico; rota selada em 54, não reabrir |
| 49 `restricted_authoritative_forensic` | Depende 43/47/48. Writer restrito no histórico original; guard de vínculo UPDATE(id), policy CHECK true original; ordem antiga key→event | **Adaptar:** CHECK false no guard, transação; manter reparo 52 e selagem 54 |
| 50 `forensic_conflict_parity` | Depende 49. Verificador nonce-only evita shadow e dá paridade de conflito; event→key, ainda sem lock de outbox | **Aproveitar** como biblioteca/prova histórica, nunca rota externa após 54 |
| 51 `outbox_lock_cancel_race` | Depende 50/outbox. Guard SELECT+UPDATE(id) e FOR SHARE; CHECK true original admitia DML id. Caminho outbox→event→key | **Adaptar:** CHECK false e prova de lock preservado; base da rota final |
| 52 `lock_order_repair` | Reescreve função 49 conservando OID/owner/ACL; corrige key→event para event→key. Requer administrador do laboratório | **Aproveitar** reparo/provas; não reconstruir a inversão histórica |
| 53 `wa40_lock_order` | Reescreve wrapper histórico 44/45; binding/outbox→event→wa42-key. Definer postgres continua somente no legado | **Aproveitar** teste cruzado; **rejeitar wrapper privilegiado como API** |
| 54 `single_entry_seal` | Depende 51 e **fase tardia** depois das regressões antigas. WA55 chama WA52; revoga cliente nas portas 48–52 e ingress WA40; restaura apenas chamada interna do writer | **Adaptar** orquestração explícita, guard/transação; não aplicar por glob antecipadamente |

RLS dos novos históricos/chaves/nonces e tabelas base Meta está habilitada. SELECT policies `USING true` são para roles técnicas NOLOGIN específicas; não são autorização por usuário/tenant. A limitação de escopo depende do join dentro do definer. O proprietário das tabelas de fixture continua postgres, sem promessa de FORCE RLS contra o administrador. Isso é bloqueador de transplantar o DDL como arquitetura produtiva.

## Revisão dos controles e decisões por componente

| Componente | Classificação | Razão e limite |
|---|---|---|
| WA39 histórico append-only, replay/variantes/conflito | **Aproveitar** | Regressões reaproveitadas; nenhuma conversão em ACK/efeito comercial |
| WA43/44 material HMAC e testes de bytes | **Aproveitar** | Material exato, campos vinculados e domínio distintos; não nova credencial |
| WA45 registro/binding por portas internas | **Adaptar** | Bom limite de entrada; portas injetadas não autenticam serviço nem asseguram revisão persistida |
| WA46 HMAC de Buffer bruto | **Aproveitar** no perfil restrito | Cópia antes de await, timingSafeEqual, rechecks do registry; segredo e fonte de registry ainda sintéticos |
| WA47 acordo de assinaturas | **Aproveitar** como teste | Não tratar assinatura WA34 como equivalente |
| WA48/49 shadow | **Rejeitar** como caminho integrado | Histórico de teste útil, mas não rota canônica; WA55 sela acesso direto |
| WA50–55 owner/ACL/nonce/outbox | **Adaptar** | Guards de lock sem DML, isolamento e ordem explícita; desenho de instalação/custódia operacional separado |
| WA56 ponte bruto→WA55 | **Aproveitar** no laboratório | Revalida bytes/evento/ticket/MAC/recibo; só recibo forense lab_only |
| WA57–66 listener, crash/restart/replay/corridas | **Aproveitar** como harness | 127.0.0.1, 4 slots, 16 sockets, teto 262144; não ingress Meta ou SLO |
| WA67 JSON/Unicode | **Aproveitar** no perfil laboratorial estrito | Rejeitar duplicatas após unescape, BOM, UTF-8 inválido e surrogate órfão; preservar bytes, sem normalização Unicode |
| WA68 limites de parser | **Pendente** para ingresso operacional | 48 níveis/2048 nomes/4096 nós mantidos; JSON.parse roda antes do scanner, sem hard cap de CPU/latência |
| Payloads Meta reais/batches/campos opcionais | **Pendente** | Parser aceita um status com shape exato; extras e múltiplos status recusados. Exigir contrato/amostras autorizadas antes de relaxar |
| IAM/M2M, KMS, tenant revocation S1, ACK/Graph, retenção/LGPD | **Pendente** | Não implementados nem aprovados por 823 testes |

**Ordem de locks:** caminho final WA55→WA52: resolve candidato de escopo, bloqueia outbox FOR SHARE, advisory `wa39:<binding>:<event>`, advisory `wa48-key:<key>`, HMAC/nonce/histórico, COMMIT. Trigger de vínculo obtém KEY SHARE no insert. Vínculos técnicos são imutáveis nesse laboratório; não se generaliza a um registry mutável de produção. Revogação usa mesmo namespace de chave; cancelamento espera o lock da outbox e não reabre estado. Reparos 52/53 evitam inversões das portas históricas. Ordem global com futuras transações S1/registry ainda precisa ser definida e testada, não inferida.

**Identidade/custódia:** seis roles técnicas NOLOGIN, sem SUPERUSER/BYPASSRLS/CREATEROLE/CREATEDB/REPLICATION. Suítes WA48+ habilitam explicitamente um **cliente LOGIN sintético temporário**, com senha aleatória local; não é proprietário nem membro dos executores. Cluster descartável é removido ao fim. Legados privilegiados persistem no catálogo, mas não são executáveis pelo cliente/anon/authenticated/service_role. Não se exige que o catálogo contenha somente funções operacionais inexistentes.

**Nonces:** INSERT e histórico na mesma transação; rollback/replay/concorrência/revogação já exercitados pelas WAs. WA40 e WA48 têm tabelas e domínios próprios; não se juntam a nonces humanos CFI-01 ou S1/I74. Retenção/expurgo/limites de volume e isolamento de custódia continuam decisões operacionais.

## Tratamento dos achados do fechamento Meta

| Achado original | Resultado desta missão |
|---|---|
| A-01 revisão Codex ausente | Revisão técnica registrada aqui; aceite somente da composição experimental, sem aprovação de merge/operação |
| A-02 guards 043–046 | Corrigido nos patches; as 12 instalações têm guard inicial e transação, com negativas individuais e falhas injetadas |
| A-03 identidade/segredos reais | Continua bloqueador operacional; não criado IAM nem acessadas credenciais reais |
| A-04 ACK/Graph/efeitos comerciais | Continua fora da entrega; não inferido de HTTP 202 ou status delivered |
| A-05 Unicode/orçamentos | Aceite limitado ao perfil laboratorial; budget produtivo e shape real pendentes |
| A-06 stack/carga/observabilidade reais | Continua pendente; PG17 local não certifica homologação Meta/Supabase real |
| A-07 links históricos | Preservados como proveniência; esta proposta aponta somente o repositório oficial atual |
| A-08 aplicação tardia WA55 | Preservada no runner reutilizado e comprovada na cadeia completa; rejeitada aplicação por glob oficial |
| Novo: DML excessivo nos guards | Policy de lock restringida a CHECK false; UPDATE(id) recusado com FOR SHARE funcionando; defeito original reproduzido em rollback |

## Alterações realmente implementadas

Commits executáveis: `e3b3ff65293d340c11fa0686332e7dc85af533d3` (composição/ACL) e `dbcca8b8583e4d31640f765232fb6708260ea36b` (prova final de rollback em cada instalação).

1. `integration/meta/source_manifest.json`: SHA/blob/SHA256 de 53 arquivos reutilizados (12 SQL, 40 módulos/testes e runner), counts dos 823 marcadores. Sem copiar/recriar módulos Meta no backend.
2. `integration/meta/prepare_lab.py`: materializa o código atual S0 + fontes Meta fixadas em diretório temporário novo, fora dos checkouts; valida hashes, colisões e igualdade das migrations compartilhadas; aplica patches verificáveis. Não faz fetch nem acessa banco.
3. `integration/meta/patches/*.patch` (12): cada instalação em BEGIN/COMMIT, guard inicial para postgres/session postgres, PG17 e nome exato `prumo_s0_test_ci`. Corrige ausência individual de guard 043–046 e impede DDL parcial em execução standalone das fixtures. Não é instalador idempotente nem composável dentro de transação chamadora: BEGIN/COMMIT próprios; usar somente o runner em banco novo.
4. Patches 049/051: políticas UPDATE dos guards usam `USING(true) WITH CHECK(false)`. Mantêm ACL UPDATE(id) exigida pelo PostgreSQL para FOR SHARE, mas proíbem toda atualização de linha. Writer/cliente não ganham DML nem membresia.
5. `test_install_guards.py`: 12 recusas individuais no banco local `postgres`, com fingerprint antes/depois de catálogo, roles, memberships, default ACLs e policies.
6. `test_final_security.py`: sete sondas finais, owners/LOGIN sintético, ausência de membros no cliente, RLS/ACL por tabela/coluna, única entrada, reproduz DML permitido pela policy antiga **em rollback** e prova UPDATE(id) negado/lock permitido nos dois guards.
7. `verify_markers.py`: 823 marcadores individuais exatamente uma vez, inclusive SQL NOTICE e WA42-R; não considera apenas marcador final.
8. `catalog_fingerprint.py` e `test_install_atomicity.py`: imediatamente antes de cada instalação normal, executar seu DDL/grants/alterações com dependências reais e injetar divisão por zero antes do COMMIT; exigir SQLSTATE 22012 e fingerprint de catálogo/roles/ACL/policies/triggers/constraints idêntico antes/depois. O runner temporário recebe apenas os hooks destas 12 sondas; sua ordem e todos os testes antigos são preservados.
9. `.github/workflows/exp-s0-meta-compatibility.yml`: CI exclusivo da branch própria, Node22/PG17, 58 testes atuais e cadeia original completa, sem enfraquecer checks antigos.

**Nenhuma mudança em `backend/`, `supabase/`, `scripts/` ou workflows oficiais nesta branch.** Patches só são aplicados ao diretório temporário. Nenhuma migration foi gerada/publicada por CLI ou aplicada em Supabase hospedado. Changelog Supabase público foi tentado e recusado pelo proxy (403); documentação atual RLS/definers foi consultada via MCP. Não há dependência nova de API Supabase.

## Evidências

- Local: PostgreSQL 17.11 descartável, Node 24.19.0; 58/58 Python, 823/823 marcadores WA39–68, regressões SQL/concorrência S0 completas, 12/12 guards, 12/12 falhas de instalação com rollback integral, 7/7 sondas finais. Sessões e containers somente deste laboratório.
- CI inicial: [Actions 40311220714](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40311220714), SHA executável `e3b3ff65`; SUCCESS, 823/823 + 58 + 12 guards + 7 sondas. A revisão final `dbcca8b8` acrescenta as 12 falhas injetadas: [Actions 40311987315](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40311987315), job `121535163769`, **SUCCESS no SHA exato**; 823/823 + 58 + 12 guards + 12 rollbacks + 7 sondas, Node22.23.3/PG17.11. Logs conferidos, nenhum marcador duplicado, remoção do container confirmada; passos e evidências no JSON adjacente.
- Asserções auxiliares foram ajustadas durante a inspeção local: NOTICE do psql tem prefixo; cliente sintético das WAs é LOGIN por desenho, ao contrário dos owners. Nenhum teste WA foi removido ou alterado para passar. A prova de DML da política antiga confirmou o defeito antes de certificar a adaptação.
- Histórico CFI-01 real preservado: [40298770078](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40298770078), 14 cenários transacionais sobre GoTrue/PostgREST reais e runtime fixado; [40298769996](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40298769996), 58 testes/regressão S0. **Não recontados como novos testes Meta.**

## Reproduzir e orientar a frente Meta

Em clone autorizado com os dois SHAs disponíveis, cliente psql, Node22+ e PostgreSQL17 **novo e descartável** em localhost:5432:

```sh
git fetch origin feat/wa39-s0-meta-forensic-bridge-20261023
git checkout exp/s0-meta-integracao-auditoria-20261026
python3 integration/meta/prepare_lab.py --destination /tmp/prumo-meta-lab-novo
export PRUMO_TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/prumo_s0_test_ci
export PGPASSWORD=postgres
python3 integration/meta/test_install_guards.py /tmp/prumo-meta-lab-novo
psql -h 127.0.0.1 -U postgres -d postgres -v ON_ERROR_STOP=1 -c 'CREATE DATABASE prumo_s0_test_ci'
python3 -m unittest discover -s backend/tests -v
(cd /tmp/prumo-meta-lab-novo && bash scripts/run-s0-local.sh) > /tmp/prumo-meta-lab.log 2>&1
python3 integration/meta/verify_markers.py /tmp/prumo-meta-lab.log
python3 integration/meta/test_final_security.py /tmp/prumo-meta-security.json
```

Usar credenciais fictícias somente no cluster local; remover esse cluster e diretório temporário ao terminar. Não executar em banco existente. A composição não baixa fontes automaticamente; fetch de SHA ausente é leitura separada explícita. CI faz checkout do SHA exato da Meta. Preservar a aplicação tardia de 054 pelo runner; não usar glob para instalar todas antes dos testes históricos.

**Correções Meta precisamente identificadas:** 043–046 precisam do guard inicial; as 12 instalações standalone precisam do limite transacional; policy `wa50_fk_guard_lock` em 049 e `wa52_guard_outbox_update` em 051 devem usar CHECK false. Os 12 patches desta proposta já implementam isso e passaram a cadeia completa, sem alterar assinaturas, TTLs, IDs, nonces, estados ou regras comerciais. Se a frente Meta for chamada a incorporar, aplicar esses patches ao snapshot indicado e manter os 823 testes, 12 negativas de banco, 12 rollbacks de instalação e 7 sondas; não reabrir rotas seladas. Não copiar os patches para migrations oficiais S0.

**Frente WhatsApp/Meta pode permanecer aguardando.** Nenhuma WA69 é necessária: os reparos estão nesta proposta isolada; não há nova implementação demandada à frente neste momento. Eventual sincronização da sua branch deve ser coordenada, não feita unilateralmente pela S0.

## Gates e retomada do backend S0

Para operação ainda faltam: contrato de ingresso/ACK e payloads Meta reais, identidade M2M/custódia/rotação/revogação do registry, installer mínimo gerenciado sem legado postgres, política global de locks e direitos S1, observabilidade/retries/retention/LGPD e homologação real autorizada. Estes itens exigem decisões e autorização próprias. O perfil WA67 estrito está aceito para este laboratório; não ratifica um parser público do produto nem um budget produtivo WA68.

**Retomar o backend a partir de `060b472b03e9e7b89f5b3d7e19b72b98836f106d` / PR #4**, com runtime CFI-01 `9488917` e os checkpoints reais já certificados. A branch desta auditoria acrescenta somente preparação/testes/documentação, não substitui esse núcleo nem o contrato UI pendente. Próximo avanço recomendado: fechar o binding UI/S0 de versões/comando CFI-01 e a fronteira de autoridade S0/S1 antes de ligar uma operação; Meta aguarda um contrato de ingresso/identidade próprio. Não transformar callback de status em mensagem inbound ou evidência de fechamento.
