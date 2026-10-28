# I85 — Bootstrap Auth/GoTrue e Diretoria sintética, laboratório v1

Data: 28/10/2026. Base documental I84 `3bf948f`, código I84 `6852a4f`, PR Draft #40.
Branch própria: `exp/s0-s1-i85-bootstrap-auth-diretor-20261028`. **Candidato experimental ainda não certificado:** asserções executáveis não substituem CI real.

## Modelo de autoridade e fronteiras

São três competências distintas: identidade autenticada de GoTrue, competência global inicial do Diretor em `prumo_private.s1_responsaveis_plataforma` e administração ordinária I79/I80 por Edge `prumo.admin.v1`. Uma identidade Auth isolada não ganha cargo, equipe, concessões ou privilégio administrativo. Os UUIDs são emitidos por GoTrue e posteriormente confrontados, sem remapeamento, com `auth.users`, consulta administrativa autenticada do GoTrue e cadastro S0/S1. Nenhum campo user_metadata/JWT enviado pelo navegador/identificador cliente é fonte de nomeação.

**Fonte confiável exclusivamente no laboratório:** instalador técnico que controla fisicamente stack local nova I84, PG17 de instalação e chave service_role retornada **apenas** pelo CLI local verificado, combinado com comando explícito `authorize-director` e opt-in exato `PRUMO_I85_DIRECTOR_APPROVAL=AUTHORIZE_SYNTHETIC_DIRECTOR_ONLY_IN_OWNED_DISPOSABLE_LAB`. Essa aprovação é vinculada ao UUID sintético previamente verificado e ao token da identidade física da stack. O operador e o host Linux/Docker são parte da fronteira de confiança; não é homologação da aprovação por gestor humano, matriz organizacional, mandato comercial ou cadeia produtiva de custódia.

A Edge **não recebe** a chave service_role nem novas operações: continua usando o login I83 restrito e as portas SQL existentes. A credencial local de instalador não vira login comercial, API Python permanente, endpoint público ou self-service. No bootstrap inicial, `postgres` local (que já é o instalador certificado) é a única identidade de banco que insere diretamente nas três estruturas canônicas: `public.atores`, `prumo_private.s1_responsaveis_plataforma`, `public.equipe_prumo_s1`. A transação realiza locks e recusa qualquer autoridade/classificação Diretor prévia; não promove identidades existentes automaticamente. Nunca muda REGISTER para criar Auth.

## Sequência técnica, exclusivamente stack nova e não vinculada

Pré-condições: I84 `init`, `prepare`, opcional `provision`/`serve` e `PRUMO_I84_DISPOSABLE=YES`. Fixar também `PRUMO_I85_DISPOSABLE=YES`. Na raiz do checkout I85:

```sh
python3 -m integration.i85 init
python3 -m integration.i85 create --label director
python3 -m integration.i85 create --label manager
python3 -m integration.i85 create --label manager2
python3 -m integration.i85 create --label consultant
python3 -m integration.i85 create --label legacy
python3 -m integration.i85 create --label outsider
# APROVAÇÃO EXPLÍCITA DO INSTALADOR PARA SINTÉTICO, NUNCA DO FRONTEND
export PRUMO_I85_DIRECTOR_APPROVAL=AUTHORIZE_SYNTHETIC_DIRECTOR_ONLY_IN_OWNED_DISPOSABLE_LAB
python3 -m integration.i85 authorize-director
unset PRUMO_I85_DIRECTOR_APPROVAL
python3 -m integration.i85 grant-director
python3 -m integration.i85 status
# Após ensaios e antes de descartar I84
python3 -m integration.i85 revoke-director
python3 -m integration.i85 dispose
python3 -m local_admin down
```

Rótulos são exclusivamente de fixtures sintéticas; `legacy` não insere cadastro S0/S1 por si só, e o ensaio cria seu registro histórico pendente intencionalmente. **Nunca usar e-mail real**. GoTrue recebe e-mail `@example.invalid`, senha forte temporária e confirmação local. Senhas são geradas pelo processo técnico, persistidas em diretório privado temporário com 0700/0600 e nunca passadas por argv, stdout, Edge ou artefatos permitidos. Serviço administrativo Auth não vai para o navegador. `dispose` retira segredos e journal da máquina após conclusão; a prova resumida deve ser registrada separadamente antes do descarte. Não equivale a sobrescrita forense.

## Máquina de reconciliação

- Antes da criação GoTrue, o journal privado registra e-mail aleatório sintético e segredo protegido, fase `CREATE_UNKNOWN`. A perda de resposta **não** dispara outro POST; `reconcile-identity --label LABEL` consulta `auth.users` pelo e-mail e `GET /auth/v1/admin/users/{uuid}` pelo UUID resultante. Discordância de UUID, email ou ausência de confirmação bloqueia. O UUID é preservado; não há escolha por correspondência frouxa.
- A aprovação separada é vinculado a UUID e identidade física do banco. Antes do COMMIT do Diretor a fase passa a `COMMIT_UNKNOWN`. As três inserções canônicas são realizadas em **uma transação PG17** com lock; após resposta perdida, `reconcile-authority` verifica exatamente um registro competente, mesmo UUID e equipe Diretor ativa. Nunca refaz a inserção potencialmente confirmada e não autoriza outra pessoa por conveniência.
- Revogação em transação atualiza `ativo=false` da competência canônica e apaga sessões GoTrue do Diretor sintético, seguida de prova de estado. Fase `REVOKE_UNKNOWN` exige reconciliação explícita e não pode reativar Diretoria. JWT antigo/sessão não recupera autoridade. Repetição de grant, novo Diretor sem autorização e identidades divergentes são bloqueados.
- Estado incerto não pode ser apagado por `dispose`: requer intervenção administrativa, recuperação comprovada ou descarte da **stack descartável inteira** sem transplante de poderes. Os limites entre criação GoTrue e COMMIT PostgreSQL permanecem não atômicos.
- Jornal técnico local append-only por esta ferramenta, fsync e sem valores de segredo/PII textual de e-mail; o host confiável pode alterar arquivos: não é trilha imutável/tamper-evident externa nem log hospedado.

## Garantias herdadas, sem novos privilégios

Preservar todos os owners NOLOGIN I81 (`prumo_s1_admin_domain_local`, `prumo_s1_professional_validator_local`, `prumo_s0_g1_executor_local`, custodiante I83), I83 executor de borda `prumo_s1_admin_edge_local`, triggers, constraints, grants, RLS, HMAC, nonce, idempotência, CAS, prova de sessão viva e resultado UNKNOWN da I82. O operador não altera DDL e não instala novas tabelas, grants ou funções de negócio. O instalador postgres permanece exclusivamente na máquina de laboratório, não no runtime Edge.

## Teste de aceitação e fronteira do frontend

A suíte `integration/i85/test_journey.py` é desenhada para exigir stack I84 real servida (PG17, GoTrue, PostgREST, Deno Edge), exercer as seis ações HTTP, negar Diretor sem competência, negar Gestor/Consultor/outro usuário, repetir uma operação concorrente e verificar idempotência, autorizar sintético explicitamente, simular perda de resposta de Auth e de confirmação após COMMIT, reconciliar sem refazer, recusar UUID divergente, revogar competência/sessões e comparar catálogo I83 pós-prepare. **Só reportar PASS quando o CI real terminar e fornecer provas.** Não usar somente testes unitários como selo de integração.

A futura UI do Diretor precisará: ator autenticado por GoTrue, consulta segura de cargo/competência sem confiar em metadados cliente, comando estrito `prumo.admin.v1`, UUID de profissional Auth já criado por fluxo autorizado separado, gestor escolhido explicitamente, `expected_relationship_id` como string decimal, hash SHA-256 de inventário, `preview_id`, `idempotency_key`, estados `CONFIRMED/UNKNOWN` e mensagens de negativa sem leaks. Não levar bootstrap/segredo service_role para interface. **Solicitar revisão de DTO à frente Frontend**; nenhuma branch, prévia ou contrato UI foi aprovada por esta implementação.

## Gates

Somente sintéticos descartáveis. Nenhum usuário real, migração hospedada, TLS produtivo, custódia hospedada, controle distribuído de abuso, auditoria externa imutável, homologação, rollout, merge, Meta, OpenAI ou F02. **Autoridade inicial de Diretor real bloqueada** até fonte de autorização organizacional documentada, identificação/aceite do titular e política produtiva de custódia/revogação. A aprovação técnica local acima não é delegável ao produto. Esta entrega não certifica recuperação universal de crash/daemon ou inconsistência GoTrue/PG fora dos cenários ensaiados.
