# S1-002/I21 — redução de ownership do executor HMAC (19/10/2026)

**Estado:** incremento local candidato; aceite depende de CI. Apenas branch `feat/s1-002-equipe-prumo`, PR #5 Draft. Sem deploy, migrations operacionais ou alteração no Supabase hospedado.

## Contexto da decisão

I20 comprovou 21/21 cenários GoTrue + HMAC + nonce, mas a fachada assinada `prumo_s1_signed_i20.invocar` continuava `SECURITY DEFINER` pertencente a `postgres`, criando uma elevação privilegiada mais ampla do que a função realmente necessita.

I21 aplica **depois** da fixture I20 o arquivo `supabase/tests/s1_021_executor_owner_local_only.sql`, exclusivamente ao banco efêmero do GitHub Actions. A fachada assinada passa a ser propriedade da role `prumo_s1_i21_executor`, que é `NOLOGIN`, `NOINHERIT`, sem `SUPERUSER`, `CREATEROLE`, `CREATEDB`, `REPLICATION` ou `BYPASSRLS`.

As tabelas temporárias `prumo_s1_signed_i20.chaves` e `nonces` também passam à role executora: isso permite preservar a leitura com `FOR SHARE` e a escrita transacional de nonce sem conceder `UPDATE` arbitrário em tabelas **de terceiros**. O ownership das duas tabelas é uma ressalva: a role executora possui poderes administrativos sobre as próprias tabelas da prova HMAC. Não equivale a custódia final de chaves de menor privilégio; exigirá nova segregação no desenho operacional.

A role pode utilizar apenas o schema interno da prova HMAC, o schema de interface S1, a rotina canônica `material`, o `pgcrypto` necessário e o `EXECUTE` das três fachadas I14/051 preexistentes (elas permanecem propriedade de `postgres`). **Não** recebe schema `prumo_private`, SELECT em `auth.sessions`, leitura comercial S0 ou UPDATE em `public.equipe_prumo_s1`. A checagem da sessão viva continua exclusivamente em I15/052 sob as regras existentes.

O login SQL `prumo_s1_signed_login_ci` continua com USAGE do schema assinado e EXECUTE da única função `invocar`; **não** pertence à role executora, não pode `SET ROLE`, ler chaves ou gravar nonces. A alteração de proprietário não cria endpoints em `public` nem amplia schema exposto da Supabase Data API.

## Testes

O runner `scripts/test_s1_002_i21_executor_local.py` reaplica 50 migrations S0/S1 reais, executa os 21 casos I20 inalterados em significado (sessão GoTrue, equipe, movimento, pausa, retorno, HMAC, replay e rotação da chave), e acrescenta:

- **S1OWN-22:** verificar proprietário real da função `invocar` e das duas tabelas de teste.
- **S1OWN-23:** negar LOGIN, SUPERUSER, CREATEROLE, CREATEDB, REPLICATION, INHERIT e BYPASSRLS à role.
- **S1OWN-24:** conferir que login SQL não é membro do executor, não tem INSERT em nonces, não cria objetos e não consegue `SET ROLE`.
- **S1OWN-25:** comprovar negações de acesso direto a `auth.sessions`, leads S0, UPDATE de equipe e schema `prumo_private`.
- **S1OWN-26:** confirmar que as três funções I14 mantiveram proprietário e isolamento.
- **S1OWN-27:** após revogar a chave anterior, testar uma nova chave gerada aleatoriamente no CI e provisionada no banco descartável.

## Gates ainda abertos

O PostgreSQL `postgres` usado por CI conserva autoridade de manutenção da fixture (apenas local), enquanto o owner NOLOGIN é separado do login operacional. Não há ambiente operacional, gestão de credenciais, HSM/Vault, custódia de chaves, rotação central, RBAC de administradores, HTTP robusto (TLS/rate limiting/controles de origem), auditoria de recusas ou execução de integração S0 de conclusão humana.

**Parecer provisório: NO-GO para produção.** GO apenas para desenvolvimento adicional no sandbox se o CI demonstrar todas as invariantes.
