# CFI-01 — aceite de LABORATÓRIO: GoTrue real + S0 atômica com login restrito

**Data 21/10/2026. PR #12 Draft. Nenhum merge, deploy, Supabase remoto ou dados de clientes.** Esta evidência fecha especificamente a correção de compatibilidade com Auth/pgcrypto no Supabase efêmero, não a integração F03 nem o aceite de produção.

## Evidência reproduzida

- **[GitHub Actions #39634684379 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39634684379)**: instância efêmera real do Supabase Auth/GoTrue e PostgreSQL 17; a suíte original S0 Auth/REST passou e a suíte CFI01-AUTH passou **8/8** no **novo** `S0CFI01AtomicCommandsLocal` com função SQL transacional assinada por HMAC/nonce, sem conexão `postgres` para `capture`/`recheck`.
- **[GitHub Actions #39634624388 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39634624388)**: **133/133 testes unitários e 73/73 físicos PostgreSQL 17**. Os novos testes verificam que o proprietário S0 atômico **não** possui `USAGE/SELECT` direto sobre `auth.sessions`, que a função de sessão é inacessível ao login SQL e a papéis de navegador, e que sessão revogada bloqueia a operação.
- Em GoTrue real, **CFI01-AUTH-01..08** cobriram: captura com token legítimo, rechecagem do mesmo recibo, outro operador autenticado bloqueado, JWT adulterado rejeitado pelo GoTrue, suspensão S1, nova mensagem que invalida snapshot, exclusão de sessão GoTrue e ausência de alteração comercial/duplicação de evento. A instância foi desligada ao fim.

## Falhas encontradas e corrigidas, sem afrouxar ACL

1. O PostgreSQL local aceita grants sobre `auth.sessions` que o Supabase gerenciado **não permite ao instalador**. A tentativa antiga gerava warnings `no privileges were granted for auth / sessions` e negava a captura. Removemos os GRANTs diretos. A função `prumo_private.cfi01_session_valid_local(actor,session)`, **SECURITY DEFINER de `postgres` com apenas uma busca exata e `FOR KEY SHARE`**, é chamada dentro da transação da função atômica, e seu EXECUTE é permitido somente ao proprietário atômico NOLOGIN. `public`, `anon`, `authenticated`, `service_role` e o login restrito têm EXECUTE revogado. Isto segue a estratégia já usada na S0 para C07/C08: um helper estreito pode precisar do owner privilegiado sem que **toda a transação** retorne a esse owner.
2. A função de assinatura também era negada porque `pgcrypto` fica no schema `extensions` no Supabase CLI. Assim como a migração S0/027 faz para o signer, a fixture agora descobre o schema da extensão em `pg_catalog.pg_extension` e concede ao **proprietário atômico NOLOGIN apenas** `USAGE` no schema encontrado e `EXECUTE` de `hmac(bytea,bytea,text)` e `digest(bytea,text)`. Não concede qualquer acesso ao login SQL ou ao modelo F03.
3. O diagnóstico temporário de SQL foi **retirado** do script `scripts/test_s0_cfi01_auth_rest_local.py` após identificar e corrigir a ACL de `pgcrypto`. A suíte foi executada novamente com o código limpo, sem a rota alternativa de diagnóstico.

## Fronteira realmente validada

```text
token JWT emitido por GoTrue real
 -> backend S0: validação /auth/v1/user
 -> assinatura HMAC server-side (operação, ator, sessão, caso,
    versão, evento, chave idempotente, timestamp e nonce)
 -> login SQL restrito (SEM SELECT/INSERT direto em mensagens/recibos)
 -> função S0 atomic SECURITY DEFINER owner NOLOGIN, NOSUPERUSER,
    NOBYPASSRLS; verifica sessão via helper estreito postgres-owned,
    equipe S1/caso/atribuição/concessão/status/versão/mensagens,
    calcula fingerprint e grava/recheca recibo com locks e nonce
 -> resultado técnico CAPTURED_LOCAL_ONLY / VERIFIED_REVIEW_ONLY_LOCAL
```

A proteção do segredo HMAC e os credenciais nesta fixture são **públicos e somente para banco sintético descartável**. O CI não é implantação. A operação não expõe contexto de controle para OpenAI e não altera a ficha, os oito status comerciais, remessa bancária, vendas ou registros de recontato.

## O que continua bloqueado antes dos dois marcos combinados

1. **Contrato S0↔F03/FV-02:** `expected_cycle_version` físico versus `expected_case_version` candidato; campos, catálogo, form_version, payload minimizado de conversas, revisão OAI-05/OAI-07 e autorização de uso dos dados. Nenhuma decisão de contrato foi inventada para encerrar este teste.
2. **F03 em execução efetiva:** adaptar `begin/recheck` do PR #8 à operação S0 com envelope canônico; garantir que mensagem nova/revogação invalidem resultado e impedir que modelo se autorize.
3. **Aplicação idempotente da ficha D3/F03:** operação S0 de negócio sob transação e auditoria próprias, limitada a campos ratificados; manter prova bancária independente e recontatos F02 separados.
4. **Produção:** migrar fixture SQL para migration revisada, definir gestão/rotação real de segredos, auditoria operacional, princípio do menor privilégio no helper `postgres`, gestão de alterações, observabilidade, teste adversarial ampliado e autorização explícita de merge/deploy.
5. **n8n:** sua presença como intermediário continua **pendente**; estes testes exercitam backend S0→GoTrue/PostgreSQL, sem ligação direta OpenAI→SQL ou dependência de n8n.

**Situação de governança:** PR #12 e #8 ainda são Draft. O gate de autenticação/fechamento técnico **em laboratório** passou; a conciliação e a substituição de permissões/efeitos na F03 ainda não estão integradas. A pausa para dúvidas seguida de auditoria geral só após os dois marcos, sem declarar trabalho faltante como concluído.


## Validação adicional após retirada do diagnóstico temporário

- **[GitHub Actions #39637758555 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39637758555)**: GoTrue real + função de sessão estreita + HMAC/nonce + função atômica de proprietário sem superusuário, com a rota temporária de diagnóstico **removida**; **8/8 CFI01-AUTH** e testes S0 Auth/REST anteriores passaram. Instância Supabase efêmera encerrada, sem contato com banco remoto.
- **[GitHub Actions #39637726654 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39637726654)**: **73/73 testes físicos PostgreSQL 17** e **133/133 unitários** aprovados na mesma versão de código limpa.
- Essa evidência confirma a correção da compatibilidade em laboratório mesmo sem probe de SQL auxiliar. O executor permanece sem acesso SQL direto a conversas, mensagens e auth.sessions; a pequena função de checagem de sessão permanece privilegiada, executável apenas pelo proprietário sem login da função atômica.

**Prontidão:** concluído apenas o incremento de engenharia do executor atômico e autenticação S0/CFI-01 em laboratório. O contrato canônico S0↔F03, o tratamento autorizado do conteúdo das mensagens, a aplicação idempotente dos campos da ficha e os controles/segredos reais de produção ainda NÃO foram concluídos. Não abrir auditoria geral nem afirmar que os dois marcos combinados foram integralmente encerrados.
