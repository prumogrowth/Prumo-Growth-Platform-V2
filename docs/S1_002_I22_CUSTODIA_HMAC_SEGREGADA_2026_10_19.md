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

## Resultado auditado do CI

**[GitHub Actions #39348523980 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39348523980)**, SHA testado `772b627f45d6a891cead0abfa86cf98a049d58dc`, job `118386886398`. Logs inspecionados: **S1KEY-01..33 = 33/33 PASS**. O runner aplicou 50 migrations S0/S1 efetivas, as fixtures locais I20, I21 e I22, criou contas GoTrue sintéticas e verificou fluxos gerenciais autorizados/negados com HMAC transacional, revogação de sessão, timestamps curtos, nonce de uso único e rotação de chave.

Resultados adicionais 28–33: o verificador e `chaves` pertencem a `prumo_s1_i22_custodio`; `invocar` e `nonces` continuam propriedade de `prumo_s1_i21_executor`; o executor foi impedido de executar SELECT/UPDATE direto nas chaves, incluindo tentativas SQL reais sob sua role; o custódio não acessa interfaces gerenciais, `auth.sessions` ou nonce; login SQL não recebe `SET ROLE` custódio nem `EXECUTE verificar_hmac`; nenhuma role recebe `CREATE` persistente no schema e a separação sobrevive à rotação.

O ensaio inicial [#39348215134](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39348215134) falhou durante a transferência de propriedade da tabela de chaves: PostgreSQL gerenciado não considerou o administrador proprietário efetivo da tabela do I21. A fixture foi corrigida com associação temporária `GRANT ... WITH INHERIT FALSE, SET TRUE`, mudança de ownership como dono atual e revogação dessa associação **antes do COMMIT**, dentro de transação DDL única. Essa associação não permanece no estado final (confirmado pelas provas I22-30/32). O código final foi aceito no CI citado acima.

**Parecer:** GO para continuidade em sandbox, **NO-GO para produção**. Não é migração operacional, não instala gateway HTTP nem muda funções comerciais ou Supabase hospedado.


## Riscos remanescentes e gates NO-GO

A própria role de custódia é proprietária da tabela de chaves e da função verificadora, portanto *não equivale a Vault/HSM ou a sigilo frente a um administrador do PostgreSQL*. A role executora ainda possui a tabela de nonces; exige política de retenção/backup e proteção contra comprometimento privilegiado. Todas as funções `prumo_s1_*` desse teste continuam restritas ao Docker CI; as fachadas I14/051 ainda têm proprietário privilegiado em seu próprio limite.

Continuam obrigatórios gateway HTTP endurecido (TLS, proteção de origem e CSRF conforme autenticação, limitação de requisições, logs de recusas sem informações sensíveis), proteção/rotação central de segredos, separação dos serviços de assinatura e banco, auditoria de escalation em `SECURITY DEFINER`, integração da UI gerencial, política de chefia/equipe e conclusão humana S0. Segurança sintética **não** autoriza merge, deploy, produção, Meta ou uso de clientes reais.

**Parecer:** NO-GO de produção; GO apenas para trabalho e testes locais depois da verificação completa.
