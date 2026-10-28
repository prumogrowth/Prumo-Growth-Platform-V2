# S0/S1 — checkpoint I85 — bootstrap Auth/GoTrue e Diretoria sintética

28/10/2026 (America/Recife). Implementação laboratorial efetiva; **não é homologação de produção**.

## Estado, commits e certificação

- Base congelada: I84 código `6852a4f509df8466e35da46ba995a4ac2ed5e1f7`, checkpoint `3bf948fe67d439d93f6c848300ea2e5e053311ed`, CI40622136488 SUCCESS.
- Branch exclusiva: `exp/s0-s1-i85-bootstrap-auth-diretor-20261028`.
- PR Draft #42: https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/42, base experimental I84, sem merge.
- **Commit de código certificado I85: `840b2db7299d024c03ced2e5120b241a23046a0e`.**
- **CI40664481472: SUCCESS 5/5 jobs**, https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40664481472
  - `credential-logging-preflight` SUCCESS (segredos);
  - `s1-pinned-i54-i78-regressions` SUCCESS (S1 original);
  - `real-history-and-cfi` SUCCESS (Auth, PostgREST, PostgreSQL 17, Edge I79–I83 e regressões pertinentes);
  - `local-operation` SUCCESS (I84 independente);
  - `i85-real-auth-bootstrap` SUCCESS (I85 nova jornada).
- Artifact I85 `s0-s1-i85-real-auth-bootstrap`, ID GitHub Actions **12805308256** (retenção de 14 dias); apenas o JSON reduzido `prumo_i85_journey.json`, sem tokens/senhas.
- Artifact I84 `s0-s1-i84-local-operation` ID **12805971397**; regressão dedicada I83 ID **12806321739**; catálogo ownership I81 ID **12805532388**.
- Este checkpoint é **documental posterior ao HEAD do código testado**. Nenhuma mudança de lógica é implicada pelo registro deste arquivo.

## Código e separação de responsabilidade

Novos arquivos:
`integration/i85/{bootstrap.py,__main__.py,__init__.py,test_journey.py}`,
`.github/workflows/exp-s0-s1-i85-auth-bootstrap.yml`,
`docs/contratos/i85_auth/BOOTSTRAP_E_RECONCILIACAO_V1.md`.

Nenhum arquivo I79–I84, SQL de negócio, Edge, frontend, main ou Supabase hospedado foi alterado. O operador I84 continua sem fixtures humanas, sem senha Auth, sem criação de Diretoria. A camada I85 é uma **ferramenta administrativa técnica local** separada dos endpoints HTTP; não é segunda API, outro cadastro, função de UI ou camada paralela de sessão.

A identidade sintética é criada pelo GoTrue real com service_role **somente na máquina de instalação local verificada** (não na Edge). O UUID verificado em `auth.users` e na leitura administrativa GoTrue é a identidade S0/S1. Cadastro organizacional ordinário I79 `REGISTER` continua exigindo UUID Auth existente. Diretoria inicial exige opt-in técnico `PRUMO_I85_DIRECTOR_APPROVAL=AUTHORIZE_SYNTHETIC_DIRECTOR_ONLY_IN_OWNED_DISPOSABLE_LAB`, associado ao UUID e à identidade física da stack I84. Instalação `postgres` local usa transação, checa ausência de outra competência/classificação e insere a mesma identidade nas três estruturas canônicas: `public.atores`, `prumo_private.s1_responsaveis_plataforma`, `public.equipe_prumo_s1`. Servidor Edge I83 mantém login `prumo_s1_admin_edge_local` restrito: nenhum Auth service_role, owner assumível, privilégio extra ou endpoint de bootstrap.

## Resultado da jornada I85 real

`integration/i85.test_journey`: **um teste E2E encadeado**, com **13 pontos de prova**, não 13 testes independentes. Logs e metadados do job `122736690298`:

1. Stack nova PG17/GoTrue sem identidades nem Diretoria.
2. Identidade Auth via administração técnica, UUID físico conferido, reexecução de criação recusada.
3. Resposta perdida após POST real de criação GoTrue, reconciliação por mesmo email/UUID sem segundo POST.
4. Divergência de UUID recusada sem adoção.
5. JWT válido sem competência não autoriza Diretoria; autopromoção/"cargo=diretor" no REGISTER recusadas.
6. Aprovação técnica vinculada ao UUID/stack; resposta perdida após COMMIT real da competência, reconciliada sem segundo insert.
7. REGISTER/ACTIVATE/TRANSFER confirmados via HTTP Edge real, chefia principal/CAS.
8. INVENTORY/PREVIEW/APPLY confirmados; preview não classifica/aplica automaticamente.
9. Gestor, Consultor e usuário não vinculado recusados nas seis operações.
10. Duas requisições simultâneas com chave idempotente única produzem apenas uma mutação.
11. Revogação da competência global e exclusão de sessão GoTrue negam acesso; rebootstrap é recusado. JWT sem competência: 403; sessão apagada: 401.
12. Catálogo físico I83 sem alterações não autorizadas de owners, grants, RLS, triggers e constraints. Somente bit temporário LOGIN de `prumo_s1_admin_edge_local` durante `serve` é normalizado, tal como operador I84.
13. Segredos/journal I85 removidos, sem alegação de apagamento forense.

**Descarte físico da I84 também comprovado após a jornada:** `phase=DISCARDED`, `material_removed=true`, `resources_absent=true`, `retirement_verified=true`. O artefato da jornada inclui apenas rótulos de prova e flags de integração, não arquivos privados.

A execução I85 não reimplementou o histórico G1, I79–I84. Cinco jobs preservam o baseline, inclusive I84 operação autônoma, separação I83, catálogo I81 e HTTP I82, e passagem física pelas migrações descartáveis. Sem auditoria comercial F02 adicional ou alteração de políticas comerciais.

## Recuperação e limites de prova

GoTrue e PostgreSQL **não formam transação distribuída**. `CREATE_UNKNOWN` e `COMMIT_UNKNOWN` são fases duráveis privadas; falha parcial não permite novo POST/INSERT automático. `reconcile-identity` exige mesmo UUID/email no GoTrue/PG. `reconcile-authority` lê competência e equipe canônicas da identidade aprovada. Ausência de prova mantém bloqueio; ninguém vira Diretor para "consertar" o processo. Revogação é confirmada mediante competência inativa e zero sessões sintéticas, sem reativação automática. O journal é fsync local e privado, **não** é log WORM, remoto ou proteção contra root host. `dispose` recusa fase de autoridade ativa/incerta e não promete destruição forense.

O ensaio comprovou perda de resposta e resultado incerto injetados **após ações reais**; não exaure todos os pontos de falha de rede, crash/daemon, entrega parcial de disco ou reconciliação de conflito externo. A recusa a segunda competência é checada pelo código sob lock; não existe teste E2E independente de uma corrida entre duas aprovações administrativas distintas. Também não há credenciais reais, identidade corporativa aprovada, custódia produtiva nem segundo fator. Essas limitações não são mascaradas como PASS total de produção.

## Encaminhamento DTO ao Frontend

Contrato candidato `prumo.admin.v1` segue em `docs/contratos/i82_edge/CONTRATO_HTTP_V1.md`. Interface futura pode consumir `REGISTER, ACTIVATE, TRANSFER, INVENTORY, PREVIEW, APPLY` via Edge, obtendo UUID Auth previamente provisionado por processo aprovado; deve reter `expected_relationship_id` decimal string (não Number JS), `expected_sha256`, `preview_id`, `idempotency_key`, recibos e estados `CONFIRMED/UNKNOWN`; não pode enviar actor/session/role como autoridade, segredo service_role nem operação bootstrap. Revisão DTO/UI depende de aceite independente das prévias de Consultor/Gestor. Nenhuma tela ou branch visual foi modificada; HTTP permanece **candidato**, não aceito pela frente visual.

## Gates e próxima execução segura

**Diretor real bloqueado**: exigir fonte/ato administrativo corporativo de nomeação verificável, identidade do titular, competências de autorização/recuperação e custódia produtiva aprovadas antes de qualquer bootstrap hospedado. Outros gates separados: TLS, credenciais hospedadas, abuso distribuído, trilha imutável operacional, proteção de operador técnico, homologação e rollout; F02 G01–G06 ainda parciais/G07 pendente, sem ratificação comercial. Sem merge, deploy, migration hospedada, usuários reais, OpenAI ou Meta.

**I86 tecnicamente segura:** definir governança/cadeia de nomeação e runbooks produtivos **sem provisionar reais**, auditar explicitamente corridas de duas aprovações, cenários de processo interrompido e falhas de descarte, endurecer proteção de journal e preparar revisão do DTO com a equipe frontend quando as prévias forem aceitas. Nenhuma migração ou promoção real implícita.
