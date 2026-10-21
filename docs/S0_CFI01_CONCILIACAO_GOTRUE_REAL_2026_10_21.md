# CFI-01 — GoTrue REAL, S0/S1 e fechamento humano: aceite de laboratório

**21/10/2026 · PR #12 Draft · NO-GO para merge/deploy/produção.**

## Evidência executada, não inferida

**[GitHub Actions #39588160832 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39588160832)**. Reutilizou o workflow S0 já existente `.github/workflows/s0-auth-rest.yml` e iniciou **Supabase Auth/GoTrue verdadeiro, PostgREST e PostgreSQL 17** em ambiente **efêmero e descartável**. A suíte anterior `scripts/test_s0_auth_rest_local.py` terminou com sucesso. Logo depois, a suíte aditiva `scripts/test_s0_cfi01_auth_rest_local.py` validou os seguintes **oito** cenários reais de autenticação e dados sintéticos:

1. `CFI01-AUTH-01`: login/sessão emitidos por GoTrue real; comando S0 de conclusão grava exatamente um recibo técnico local, após verificar equipe, atribuição, loja e versão no PostgreSQL.
2. `CFI01-AUTH-02`: segundo comando `recheck_human_closure` consulta novamente GoTrue e comprova o mesmo recibo/contexto.
3. `CFI01-AUTH-03`: outro usuário **autenticado** no GoTrue, sem atribuição ao caso, não consegue capturá-lo.
4. `CFI01-AUTH-04`: payload do JWT adulterado sem recalcular a assinatura é rejeitado pelo **GoTrue real**. A primeira tentativa de teste falhou por alterar apenas um caractere final Base64URL potencialmente não significativo; o teste foi corrigido para mudar o `sub` decodificado mantendo assinatura original, e a segunda execução passou. Não havia prova de bypass de assinatura.
5. `CFI01-AUTH-05`: suspensão da equipe S1 no PostgreSQL impede rechecagem mesmo com JWT GoTrue ainda existente.
6. `CFI01-AUTH-06`: nova mensagem no caso invalida o snapshot do recibo, retornando `STALE`.
7. `CFI01-AUTH-07`: exclusão da sessão **real** de GoTrue no PostgreSQL impede a rechecagem.
8. `CFI01-AUTH-08`: exatamente um evento técnico gravado; status comercial preservado, sem remessa bancária ou venda inferida.

No mesmo incremento, **[GitHub Actions #39588140002](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39588140002)** e o [run anterior #39587055367](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39587055367) confirmaram o banco descartável com **133/133 testes unitários e 37/37 testes físicos PostgreSQL 17**. Os números representam **suítes distintas**, não a regressão histórica F03 (210 casos), nem uma integração com IA real.

O workflow GoTrue encerrou os contêineres (`supabase stop --no-backup`). O rótulo temporário `run-auth-integration` usado para disparar a execução foi **removido** do PR após o aceite para evitar gasto de runner repetido. **Nenhuma** credencial de clientes, dados reais, Supabase hospedado ou API comercial OpenAI/Meta/Banco foi acessada.

## Código concreto desta frente e fronteira

- `backend/s0_cfi01_authenticated_commands_local.py` cria a entrada S0 com allowlist exata `capture_human_closure`/`recheck_human_closure`. Reutiliza o `SupabaseGoTrueVerifier` existente em `backend/identity_boundary.py`, que chama `/auth/v1/user` e liga `sub` e `session_id` ao usuário verificado. Cada comando revalida a identidade, independentemente.
- O mesmo comando chama o backend S0/S1 do PR #12: checagem `auth.sessions`, equipe S1 ativa, caso e atribuição vigente, concessão da loja, versão física do ciclo e recorte de conversas/mensagens sob transação/locks. Cliente não fornece `actor_id`, `concessionaria_id`, grant, status bancário ou resposta de modelo como autoridade.
- `backend/tests/test_s0_cfi01_authenticated_commands_local.py`: 20 testes de contrato GoTrue com resposta HTTP simulada, incluindo rejeição de dados extras do navegador e tratamento de falhas. `backend/tests/cfi01_signed_http_auth_fixture.py`: servidor HTTP assinado **sintético** somente para testes de assinatura; distinto do **GoTrue real** no workflow Supabase.
- `scripts/test_s0_cfi01_auth_rest_local.py` executa a prova GoTrue **real**. Utiliza migração S1 038 copiada **byte por byte** para `supabase/tests/`, mais fixture privada de evento CFI-01 **apenas no banco descartável**. Nenhuma das duas é migration nova de produção.
- A conexão privilegiada ao banco `postgres` local permanece EXCLUSIVA de laboratório. O caminho `/postgres` da CLI Supabase só é permitido para a porta 54322 com `PRUMO_CFI01_SUPABASE_LOCAL_AUTH_TEST=1` e host loopback, sob bloqueio de redirecionamentos libpq.

## Decisão de prontidão e condições remanescentes

**Concluído COM PROVA:** autenticação pelo GoTrue **verdadeiro** no laboratório, chamada S0 específica `capture/recheck`, consulta a concessões reais de tabelas S0/S1 e idempotência/revogação/rechecagem transacional no PG17. Esta parte da substituição dos indicadores ficcionais passou a usar identidades e sessões reais **de ambiente descartável**, sem autorização extraída de IA.

**Ainda NÃO concluído — não declarar GO de produção nem F03 integrada:**
1. **Executor de banco com privilégio mínimo + segundo fator assinado** para esta operação específica. O fluxo CFI-01 testado ainda usa `postgres` na CLI/local; a engenharia de HMAC/nonce já existente na S0 vale para C07/C08, **não é autorização CFI-01**. Exige operação própria com auditoria e políticas de sessão.
2. **Contrato S0↔OAI/FV canônico**, ainda divergente: `expected_cycle_version` é coluna física `ciclos_comerciais.versao_registro`; `expected_case_version` da ponte OpenAI/FV é candidato, NÃO implementado na S0. Também faltam `form_version`, catálogo permitido, versão de políticas e recorte minimizado das mensagens.
3. **Conector real S0→F03**, devolvendo apenas o recorte autorizado e minimizado de mensagens, sem expor atributos de controle (ator, grant, loja, atribuição, chave idempotente). `S0_VALIDATION_REQUIRED` continua PROPOSTA, não gravação.
4. **Aplicação transacional dos campos sugeridos** mediante parser e catálogo ratificados e `recheck` na mesma transação de persistência, com autoria/auditoria e proteção contra atualização concorrente. Nunca inferir banco enviado/aprovado ou venda por fala da IA.
5. **Casos S1 excepcionais por caso** permanecem bloqueados na porta normal, sem importação de fixture S1 055 como concessão operacional. Retomar somente com contrato próprio e teste físico.

**Ordem de trabalho pactuada:** este marco autenticação do laboratório foi concluído; a conciliação do contrato F03 e a substituição **integral em produto** ainda NÃO. Só após esses marcos, preparar pausa para dúvidas e auditoria geral. Se a próxima sessão for para **decidir** catálogo/envelope/escopo, essas dependências devem ser discutidas como pendências, não escondidas nem anunciadas como homologadas.

**Governança:** PR #12 S0 e PR #8 OpenAI continuam Draft. Sem merge/deploy, dados reais de clientes ou processamento OpenAI pago.
