# Prumo S0 — redução de privilégios do verificador HMAC (17/10/2026)

**Escopo:** somente migração candidata e testes fictícios na branch privada. Sem deploy, dados reais, secret manager operacional, MCP ou integração externa.

## Motivação

O gateway já exigia duas provas distintas: login SQL restrito e HMAC de curta duração, vinculados à operação e a uma sessão GoTrue validada pelo backend. Contudo, o verificador de HMAC executava como **proprietário privilegiado `postgres`**. Essa elevação era maior que sua tarefa de conferir assinaturas e consumir um nonce.

O termo **segredo**, neste projeto, refere-se a material que deve ficar confidencial: senha SQL, chave HMAC, token de acesso de terceiros ou credenciais de serviço. A migration **não contém segredo operacional**. O HMAC fictício do teste não é segredo real nem apropriado para produção.

## Mudança incremental 027

- Cria `prumo_s0_signer` como papel PostgreSQL **NOLOGIN/NOINHERIT**, sem `SUPERUSER`, `CREATEROLE`, `CREATEDB`, replicação ou `BYPASSRLS`; recusa migração se o papel tiver privilégios mais amplos ou for concedido a membros não administrativos. Associações administrativas internas a `postgres`/`supabase_admin`, quando criadas pelo Supabase, são permitidas; não representam acesso de usuários comuns.
- Altera **somente** o proprietário de `prumo_private.gateway_validar_prova_s0` para esse papel. Mantém `SECURITY DEFINER` e `search_path=''`, no esquema privado sem RPC externa.
- Concede apenas leitura das colunas estritamente necessárias da tabela de chaves HMAC, inserção do nonce e leitura do nonce retornado, USAGE do esquema privado e acesso à função HMAC do `pgcrypto`. **Não concede UPDATE do material secreto, leitura de leads, sessão de usuário ou execução das wrappers comerciais**.
- `FOR SHARE` exigiria privilégio SQL de UPDATE até mesmo num SELECT. Para manter o verificador incapaz de atualizar a chave, a validação e a função administrativa de ativação/revogação obtêm o mesmo **advisory lock transacional** derivado da chave antes de ler/modificar o estado. O lock só cobre caminhos oficiais da aplicação; alterações diretas feitas por superusuários não respeitam obrigatoriamente esse protocolo.
- As wrappers que efetivamente cancelam plano e reconciliam C07 permanecem com proprietário `postgres` **por compatibilidade com as funções de domínio existentes**. Isso ainda é um risco a tratar e significa que o gateway como um todo **não foi rebaixado para privilégio mínimo**.
- Chave HMAC continua armazenada na instância PostgreSQL; o papel sem login apenas compartimentaliza leitura interna. Um cofre externo com identidade de serviço própria, separação de credenciais, rotação e recuperação continua não implementado.

## Testes

`supabase/tests/s0_gateway_isolamento_verificador.sql` verifica propriedade da função, `NOLOGIN`, ausência de membros, ACL não exposta, ausência de leitura comercial/sessões e restrição das duas wrappers.

As regressões existentes `GW-01..07`, `KEY-01..05`, `AUTH-01..14`, idempotência/concorrência e o teste unitário Python precisam continuar passando.

**Gate:** GO exclusivamente para desenvolvimento local sintético após regressão; **NO-GO** para merge, produção, dados reais, credencial operacional, Meta, Banco, OpenAI ou aplicação da migration no Supabase hospedado. O relatório de aceite deve distinguir validação PostgreSQL da suíte GoTrue/REST, caso esta última não seja reexecutada.

## Evidência PostgreSQL

[GitHub Actions PostgreSQL 17 #39086116542 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39086116542): OWNER-01..03, GW-01..07, KEY-01..05, 24 testes unitários e regressões anteriores. Inclui bloqueio de papel não administrativo e assinatura com proprietário restrito. A primeira tentativa Auth/REST revelou uma associação administrativa padrão do Supabase não prevista; a política foi ajustada para permitir somente administradores `postgres`/`supabase_admin`, preservando as negativas para outros membros. O aceite GoTrue/REST da versão ajustada deve ser registrado separadamente.

## Parecer após auditoria cruzada PostgreSQL/Supabase — 17/10/2026

- [**PG 17 #39087193113 — PASS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39087193113). O proprietário `prumo_s0_signer` não possui acesso comercial, LOGIN ou CREATE persistente no esquema privado.
- Em Supabase local, `postgres` pode não ser superusuário. A migration concede somente a esse administrador `SET TRUE, INHERIT FALSE` no novo papel, evitando tocar `supabase_admin` (papel reservado). Para a transferência da função, `CREATE` é concedido ao proprietário apenas durante um bloco SQL atômico e imediatamente revogado.
- A validação integrada antes dessa última correção [#39086997963](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39086997963) **FALHOU** durante o `ALTER FUNCTION OWNER` por ausência de `CREATE` no esquema. A correção passou no PostgreSQL, mas **ainda não foi repetida em GoTrue/PostgREST local** por controle da franquia GitHub. Não rotular o ambiente Supabase 027 como aprovado.
- **Risco ainda aberto**: duas wrappers comerciais continuam de propriedade `postgres`; o verificador HMAC usa segredo da mesma instância Postgres, não um cofre de segredos independente. Rotação operacional real, coleta durável de negativas e recuperação não estão implantadas.
