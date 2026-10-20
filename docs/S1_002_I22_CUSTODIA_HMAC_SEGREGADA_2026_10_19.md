# S1-002/I22 — Separação da custódia HMAC e execução gerencial (19/10/2026)

**Estado: candidato local no GitHub**, sem produção. Escopo exclusivo de `feat/s1-002-equipe-prumo`, PR #5 Draft. Nenhuma migration nova nem interação com Supabase hospedado.

## Motivo

O I21 (CI 27/27) reduziu o proprietário da função `prumo_s1_signed_i20.invocar` a um executor `NOLOGIN`, mas a mesma role ainda **possuía a tabela de chaves HMAC** e a tabela de nonces. Essa concentração de privilégios não é necessária: o executor precisa apenas **solicitar uma verificação criptográfica** e consumir um nonce de uso único, e nunca ler o segredo.

## Implementação isolada

A fixture `supabase/tests/s1_022_chave_custodio_separado_local_only.sql` é aplicada depois de I20 e I21 **somente** no banco PostgreSQL descartável da CI.

- `prumo_s1_i22_custodio`: role `NOLOGIN / NOINHERIT / NOBYPASSRLS`, sem `SUPERUSER/CREATEROLE/CREATEDB`, dona apenas da tabela de chave `chaves` e da função `verificar_hmac`; sem `SELECT auth.sessions`, acesso bruto ao domínio, uso de `prumo_s1_interface`, escrita em nonces ou capacidade de executar o comando completo `invocar`.
- `prumo_s1_i21_executor`: mantém a propriedade de `invocar` e `nonces`; perde totalmente `SELECT/INSERT/UPDATE/DELETE` sobre `chaves`. Pode apenas executar `verificar_hmac` (retorno `void`) e chamar as três fachadas internas preexistentes I14; não cria objetos no schema.
- `prumo_s1_signed_login_ci`: mantém apenas USAGE do schema e EXECUTE de `invocar`. Não pode se tornar executor/custódio, chamar o verificador diretamente nem acessar tabelas de chave/nonces.
- `verificar_hmac`: `SECURITY DEFINER SET search_path=''`, owned pela custódia, checa argumento e chave ativa/tempo, calcula HMAC-SHA256 com `pgcrypto` e rejeita prova inválida. **Não retorna bytes, chave, hash, texto livre nem indicador útil de custódia**: apenas retorna sucesso vazio ou falha genérica. A função só é executável pelo executor interno, não via Data API ou login.
- `invocar`: continua efetuando allowlist de três operações e janela temporal curta, chama `verificar_hmac`, consome nonce na **mesma transação** e só depois estabelece as claims para I14/I15 revalidarem GoTrue e vínculos por equipe. Não precisa ler a chave e não concede um RPC `public`.

A custódia e a rotina de validação compartilham um advisory transaction lock por `chave_id` com o **procedimento administrativo de revogação da CI**. Isso impede validação concorrente de uma chave revogada sem sincronização. As alterações de owner e grants são executadas numa transação DDL única com `CREATE` temporário, depois revogado; o login da aplicação não recebe capacidade de `SET ROLE`.

## Testes I22

`scripts/test_s1_002_i22_key_custody_local.py` repete I21-01..27, incluindo 50 migrations S0/S1 reais, GoTrue HTTP, movimento por equipe, pausa global, reativação, HMAC inválida, replay, logout e nova chave. Os cenários novos I22-28..33 auditam:

- owner e atributos do custódio `NOLOGIN`;
- ausência de acesso da role executora a qualquer coluna/DML da chave;
- ausência de acesso do custódio a nonce, funções gerenciais e `auth.sessions`;
- recusas efetivas de `SELECT segredo` e de `UPDATE chaves` sob a role executora;
- inexistência de `EXECUTE verificar_hmac` ou `SET ROLE custódio` pelo login SQL;
- preservação de owners e ausência de `CREATE` após rotação da chave.

**Resultado CI:** pendente até inspeção de logs.

## Riscos remanescentes e gates NO-GO

A própria role de custódia é proprietária da tabela de chaves e da função verificadora, portanto *não equivale a Vault/HSM ou a sigilo frente a um administrador do PostgreSQL*. A role executora ainda possui a tabela de nonces; exige política de retenção/backup e proteção contra comprometimento privilegiado. Todas as funções `prumo_s1_*` desse teste continuam restritas ao Docker CI; as fachadas I14/051 ainda têm proprietário privilegiado em seu próprio limite.

Continuam obrigatórios gateway HTTP endurecido (TLS, proteção de origem e CSRF conforme autenticação, limitação de requisições, logs de recusas sem informações sensíveis), proteção/rotação central de segredos, separação dos serviços de assinatura e banco, auditoria de escalation em `SECURITY DEFINER`, integração da UI gerencial, política de chefia/equipe e conclusão humana S0. Segurança sintética **não** autoriza merge, deploy, produção, Meta ou uso de clientes reais.

**Parecer:** NO-GO de produção; GO apenas para trabalho e testes locais depois da verificação completa.
