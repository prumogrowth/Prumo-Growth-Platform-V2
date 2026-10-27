# I82 — borda administrativa HTTP local, candidato v1

27/10/2026, America/Sao_Paulo. Base: I81/PR #32 `c267c56`, código `4ba266d`.
I79/I80 e suas fontes de autoridade continuam os mesmos contratos. Esta borda
experimental não ratifica telas, comandos comerciais ou implantação hospedada.
ADR `ADR-2026-10-27-SUPABASE-OPENAI-DIRECT` consultada na fonte F02
`175f2ad50d39b2b59cbb18e2953330a7ff6f1709`, sem incorporar essa branch.

## Caminho real e autoridade

Cliente local → Kong/Edge Runtime Supabase → TypeScript/Deno → GET GoTrue
`/auth/v1/user` → identidade/sessão do token verificado → HMAC de servidor →
login SQL restrito existente → I79/I80 signed → domínio administrativo I81 →
validação de recibo → constraints diferidas I81 → COMMIT confirmado → retorno HTTP.

Python só prepara e verifica fixtures/testes; não serve API nem executa dentro
da Edge. Nenhum worker externo obrigatório, n8n, OpenAI ou Meta neste caminho.
PostgreSQL continua fonte de estado e alçada. Não se replica autorização em TS.

A Edge chama apenas as funções privadas assinadas I79/I80, via TCP com
`postgres@3.4.7`, prepare=false e parâmetros vinculados. Não utiliza PostgREST
para expor função privada, credencial postgres, service_role, SET ROLE ou DML.
O login, as tabelas de chave/nonce e o executor HMAC existentes são reutilizados;
não se concedem novos privilégios comerciais de G1/I54/I55/I62.

Autenticação ocorre em toda chamada no GoTrue real. Só depois de HTTP200 são
lidos sub/session_id/exp do JWT para vincular o usuário retornado. Payload não
contém ator/sessão, alçada, grants ou papel administrativo. user_metadata não
autoriza nada. Sessão viva e competência do Diretor são novamente verificadas
com os locks originais no PostgreSQL. Cargo Gestor não confere competência de
Diretor, mesmo com concessão de loja ou subordinados.

## URLs e entrada

Somente em stack local descartável, sem endpoint hospedado:

| Método e caminho externo | Comandos |
| --- | --- |
| POST `/functions/v1/prumo-admin-i82/v1/i79` | REGISTER, ACTIVATE, TRANSFER |
| POST `/functions/v1/prumo-admin-i82/v1/i80` | INVENTORY, PREVIEW, APPLY |

Cabeçalhos: `Authorization: Bearer <JWT GoTrue>`, `Content-Type: application/json`
e apikey publishable/anon local usado no gateway. Segredos de servidor nunca
vêm do cliente. Não há parâmetros de query nem rota comercial adicional.

Envelope estrito de dois campos: `version: "prumo.admin.v1"`, `command: {...}`.
Campos desconhecidos, inclusive actor_id/session_id/diretor_id, são recusados.
Não há defaults que escolham cargo, chefia ou aplicação por omissão.

I79 contém os seis campos já existentes: action, target_id, cargo, manager_id,
expected_relationship_id, idempotency_key. **No HTTP, expected_relationship_id
é string decimal canônica**, de `"0"` a `"9223372036854775807"`. Nunca Number
arredondado pelo JavaScript. A tradução gera o mesmo bigint/material HMAC da
porta Python original, cujo DTO interno continua usando int. Os IDs de relação
das respostas já eram strings no SQL I79/I80 e permanecem assim.

```json
{
  "version": "prumo.admin.v1",
  "command": {
    "action": "REGISTER",
    "target_id": "33333333-3333-4333-8333-333333333333",
    "cargo": "consultor",
    "manager_id": null,
    "expected_relationship_id": "0",
    "idempotency_key": "cadastro-local-0001"
  }
}
```

Esse exemplo não cria usuário Auth: REGISTER admite UUID GoTrue já existente e
cria cadastro organizacional pendente. ACTIVATE Gestor exige pendente/cargo
Gestor/manager_id null; ACTIVATE Consultor exige Gestor explícito e chefia válida
no COMMIT. TRANSFER exige Consultor ativo, ID da chefia anterior >0 e novo Gestor
explícito. Não transfere casos nem concede loja.

I80 contém os nove campos originais: action, target_id, cargo, manager_id,
expected_sha256, preview_id, cursor, limit, idempotency_key.

| Ação | Campos obrigatórios e efeito |
| --- | --- |
| INVENTORY | proposta/hash/prévia nulos, cursor UUID ou null, limit inteiro 1–50; página administrativa minimizada |
| PREVIEW | alvo/cargo explícitos, Gestor ou null, hash do item do inventário, preview_id/cursor null, limit=0; persiste READY/BLOCKED, não aplica |
| APPLY | mesmos alvo/cargo/Gestor, ID e hash do contexto da prévia, cursor null, limit=0; aplica explicitamente uma vez sob CAS |

```json
{
  "version": "prumo.admin.v1",
  "command": {
    "action": "INVENTORY",
    "target_id": null,
    "cargo": null,
    "manager_id": null,
    "expected_sha256": null,
    "preview_id": null,
    "cursor": null,
    "limit": 50,
    "idempotency_key": "inventario-local-0001"
  }
}
```

Hashes continuam SHA-256 lowercase de 64 caracteres. UUIDs canônicos lowercase
não nulos. Chaves de idempotência ASCII 8–128, conjunto A–Z/a–z/0–9/ponto/
underscore/dois-pontos/hífen. Request máximo 8192 bytes, UTF-8 válido, JSON sem
chaves duplicadas (inclusive escapadas), arrays, conteúdo extra ou profundidade
acima de seis. Forma e valores são validados; regras de negócio seguem no SQL.

## Resposta e resultado incerto

Envelope fechado: version, correlation_id, state, commit, scope, receipt.
scope é sempre `ADMINISTRATIVE_ONLY`. Correlation ID é UUID gerado pelo servidor,
não ator nem chave de idempotência; também retorna no X-Request-ID. Cabeçalhos
Cache-Control:no-store e X-Content-Type-Options:nosniff. Sem JWT, sessão, segredo,
email, diagnóstico SQL, stack trace ou credencial na resposta.

| HTTP | state | commit | Interpretação |
| --- | --- | --- | --- |
| 200 | APPLIED/ALREADY_APPLIED/INVENTORY/READY/BLOCKED | CONFIRMED | transação que produziu o recibo confirmada; READY/BLOCKED de PREVIEW não aplicam cadastro |
| 400/413/415 | INPUT_REJECTED | NOT_ATTEMPTED | formato/limite inválido; sem tentativa de domínio |
| 401 | DENIED | NOT_ATTEMPTED | autenticação recusada antes do SQL |
| 403 | DENIED | NOT_ATTEMPTED ou REJECTED | origem recusada, ou núcleo rejeitou sessão/autoridade/guard |
| 409 | STALE/CONFLICT/CONCURRENT_CHANGE/EXPIRED/BLOCKED | REJECTED | negativa transacional original; revisar estado/prévia conforme o caso |
| 429 | BUSY | NOT_ATTEMPTED | limite técnico de concorrência do worker; Retry-After:1 |
| 503 | UNAVAILABLE | NOT_ATTEMPTED ou UNKNOWN | indisponibilidade anterior ao SQL ou resultado transacional não conhecido |
| 404/405 | NOT_FOUND/METHOD_NOT_ALLOWED | NOT_ATTEMPTED | rota/método sem comando |

receipt é null em erro. Em sucesso contém somente a projeção validada pelo
adaptador equivalente ao Python: metadados administrativos I79 ou inventário/
prévia/aplicação I80 existentes. Binding, campos, contagens e tipos do recibo
são validados **dentro** da transação antes de COMMIT. Sucesso só é retornado
depois do acknowledgment do COMMIT, incluindo as constraints diferidas.

UNKNOWN é conservador: falha de conexão, resultado inválido ou erro não
classificado depois da tentativa SQL não comprova rollback. A Edge não faz
retry automático. **Ausência de resposta/timeout no cliente também é incerta**,
mesmo se o servidor confirmou e a resposta se perdeu. Reconciliar com o mesmo
comando/chave, mesma sessão quando exigida pela I80, e autoridade ainda vigente.
Não gerar outra chave para repetir uma mutação possivelmente confirmada.
Revogação posterior pode impedir reconciliação; uma negativa atual não prova
que a operação anterior foi desfeita. Não existe bypass administrativo para isso.

Prazos de prévia, versões/CAS, I61, nonce e relógio continuam os do SQL. O frontend
não usa um relógio próprio para autorizar, renova prévia por replay ou interpreta
qualquer state como conclusão de venda, envio ou ratificação comercial F02.

## Segurança, DDL e privilégios

Owners I81 preservados: domínio `prumo_s1_admin_domain_local`, validador
`prumo_s1_professional_validator_local`, HMAC `prumo_s0_g1_executor_local`.
RLS, I46/I57/I61, índices, locks e constraints não são substituídos pela borda.
Login/API roles não ganham EXECUTE em helpers, tabela privada ou membership.

O único delta SQL é um helper **INVOKER** privado e uma chamada no início de
cada ponte administrativa. Usa SELECT já existente do domínio para manter
ACCESS SHARE nas tabelas metadata-only até COMMIT e confere colunas exatas.
ALTER TABLE ACCESS EXCLUSIVE espera; DDL já confirmado não revisado é recusado
com I82_SCHEMA_REVIEW_REQUIRED. Não se remove xmin/ABA nem se amplia grant para
resolver uma alteração de schema. A instalação verifica os hashes I81 e conserva
exatamente o resto dos corpos das pontes. Não é um bloqueio de todo DDL do banco:
Outros objetos/policies/grants ainda exigem governança e revisão de catálogo.

Ambiente exige opt-in PRUMO_I82_DISPOSABLE=YES, URLs loopback ou nomes Docker
exatos da stack efêmera, login SQL restrito específico e chave de teste existente.
URLs hospedadas, owner SQL e origem remota são recusados. Senha/chave sintéticas
são geradas por fixture e entregues em arquivo temporário chmod0600 fora do Git;
não são parâmetros HTTP. Para o driver npm no runtime fixado, o provisionador
consulta somente NetworkSettings.Networks do container local esperado e fixa seu
IPv4 privado da rede supabase_network_prumo-s0-auth-ci. O driver usa esse endereço
em vez do resolvedor Node que respondeu ENOTFOUND para o nome do DB. O pin é
servidor-only, não campo HTTP; IP público/metadata de nuvem, ausência de pin no
perfil Docker e override de destino no perfil loopback são recusados. Não há
fallback automático para outro host ou aumento de privilégio.

Supabase CLI pode injetar credenciais padrão do ambiente:
a implementação não lê nem usa service_role.

Limites técnicos: body deadline de 5s; Auth timeout 5s; conexão 5s; lock_timeout
8s/statement_timeout 15s existentes; pool por worker máximo 2, prepare=false;
até quatro requisições simultâneas por worker. Isso não é quota comercial nem
rate limiting global/distribuído. CORS só para origem localhost configurada,
sem wildcard/credentials. O template CLI 2.84.2 possui plugin CORS curinga no
serviço Functions; o ensaio remove somente esse plugin no Kong descartável e
restaura integralmente a configuração ao encerrar. Auth/REST e transformadores
de autorização não são alterados. OPTIONS então chega ao handler, que valida
origem, POST e headers permitidos. Esse ajuste não é provisionamento hospedado.
Sem origem, chamadas servidor→servidor são aceitas
com a mesma autenticação obrigatória.

O CLI local usa --no-verify-jwt para deixar a autenticação no handler via GoTrue
real e no SQL; não representa uma porta administrativa sem autenticação. O
próprio handler nega Bearer ausente e nunca confia apenas em decodificar JWT.
Essa configuração é exclusiva do ensaio local, não um perfil de deploy.

## Fronteiras ainda não aprovadas

Sem criação/convite Auth, UI administrativa, bootstrap de Diretor, exposição de
CRUD/tabelas, endpoint comercial, OpenAI, Meta, migração hospedada ou deploy.
Custódia/rotação/escopo produtivo de credenciais e separação futura do login/chave
compartilhados do laboratório exigem provisionamento/homologação próprios; não
se amplia o login para isso. O Python permanece para comparação e testes,
TypeScript executa a borda e SQL executa o núcleo.

Frontend pode avaliar este candidato e o [mapa legível por máquina](http_contract_v1.json).
Nenhuma branch/interface visual foi modificada nem prévia visual foi aceita por
esta implementação. Decisões administrativas explícitas da I80 continuam com
o Diretor; contratos UI/comerciais pendentes não são ratificados. F02 G01–G06
parciais/G07 pendente, sem repetir auditoria ou H01.
