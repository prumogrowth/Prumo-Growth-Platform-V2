# CFI-01 — Primeiro gate SQL assinado/restrito (escopo laboratório) — 21/10/2026

**Status: implementação e regressão PostgreSQL 17 física aprovadas no PR #12 Draft; homologação completa NO-GO.**

## Por que esse incremento

A S0 já passou por testes **reais e efêmeros** de GoTrue/Auth+REST para conclusão humana, mas o comando `capture/recheck` ainda usa `postgres` com privilégios elevados em laboratório. A S0 possui HMAC/nonce para C07/C08, **não** para a operação F03/CFI-01. Reutilizá-los como se fossem autorização para concluir atendimento seria violação de fronteira.

Esta frente implementou um mecanismo **próprio da CFI-01**, ainda só em fixture local, com usuário SQL separado, uma função privada `SECURITY DEFINER` de operação allowlisted, chave HMAC específica da fixture e nonce consumido uma única vez.

## Artefatos implementados

- `supabase/tests/s0_cfi01_signed_prerequisite_local_only.sql`: cria **somente em PostgreSQL descartável** o usuário `prumo_cfi01_pgtest_login`, as tabelas privadas de chave e nonce e a função `prumo_private.cfi01_signed_prerequisite_local`. O role SQL **não recebe SELECT/INSERT de tabelas S0, mensagens, auth.sessions, chaves ou recibos**; só EXECUTE nesse gate.
- A assinatura HMAC-SHA256 vincula operação `capture_human_closure` ou `recheck_human_closure`, ator, sessão, caso, versão do ciclo, ID do evento (recheck), timestamp (validade ~30 s) e nonce. O banco verifica chave ativa e assinatura, sessão viva, equipe S1 ativa, atribuição atual, concessionária e vínculo vigentes, status e versão; recheck exige o recibo original com mesmas referências. Nonce repetido é negado.
- `backend/s0_cfi01_signed_prerequisite_local.py`: cliente Python com DSN de usuário restrito, tempo/nonce únicos, assinatura server-side e resultado `SIGNED_PREREQUISITES_ONLY_LOCAL`. Impede conexão a banco remoto ou outro nome/porta e redirecionamento libpq. O código exclui qualquer informação de modelo, dados bancários ou ficha.
- `backend/s0_cfi01_signed_commands_local.py`: encaixa **GoTrue → prova assinada → captura/recheck S0/S1 preexistente**; valida payload estrito e chama GoTrue novamente na última etapa para revogações/races não dependerem só da prova preliminar.
- `backend/tests/test_s0_cfi01_pg17_integration.py`: mais 19 testes físicos. 14 verificam assinatura real no banco, nonce replay, validade e restrições SQL; 5 verificam fluxo completo com gate assinado antes da captura/recheck.
- `scripts/test_s0_cfi01_auth_rest_local.py`: foi adaptado para executar também o gate assinado com GoTrue local real, em workflow efêmero S0. Não usa Supabase hospedado.

## Evidência física já confirmada

[GitHub Actions #39621353969](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39621353969) — **SUCESSO**, 133/133 unitários e 51/51 testes físicos PG17 (14 novos).

[GitHub Actions #39621918613](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39621918613) — **SUCESSO**, 133/133 unitários e **56/56** físicos PG17 (mais cinco testes de encadeamento assinatura→captura/recheck).

Os 8 cenários GoTrue reais anteriores foram [aprovados #39588160832](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39588160832), **antes** desta nova porta assinada. A execução conjunta GoTrue real + HMAC restrito desta rodada deve ter evidência independente; não presumir sucesso só pelas duas suítes separadas.

## Limites técnicos que impedem declarar conclusão do produto

1. A função `SECURITY DEFINER` de laboratório **ainda pertence ao papel privilegiado `postgres`**. Isso demonstra negação de SQL direto ao login restrito, mas **não** demonstra redução de privilégio do proprietário da função. Exige owner isolado, ACL mínima e revisão de RLS no desenho definitivo.
2. **O último passo `capture/recheck` do wrapper ainda usa `postgres` local** em transação separada, após prova assinada. Ainda falta mover a operação completa, a auditoria e a futura gravação dos campos para a função S0 de privilégio mínimo, e impedir ataques por troca de contexto entre as duas transações.
3. Este HMAC de laboratório ainda **não vincula a chave textual de idempotência** ao material da assinatura, embora a captura/rechecagem posterior a valide por caso e recibo. A assinatura definitiva deve vincular o envelope canônico completo da CFI-01, incluindo key e versões ratificadas.
4. A autenticação real GoTrue de ambiente efêmero não é deploy de produção, nem executor assinado definitivo; assinatura e segredo fixos nesta fixture são **valores publicados exclusivamente para testes descartáveis**.
5. O contrato OAI-05/OAI-07, catálogo D3, recorte de mensagens minimizado, fonte bancária real e aplicação transacional de campos elegíveis seguem pendentes. Nenhum modelo F03 foi conectado a esta nova operação.
6. As exceções S1 por caso continuam conservadoramente negadas fora do contrato normal de concessão de loja. Pausa de intake não equivale a revogação de conta.

**Próximo gate de engenharia:** fechar proprietário/credencial mínima e mover efetivamente `capture/recheck` para a operação assinada atômica. Depois definir com o responsável o envelope canônico e a aplicação de campos F03. PR #8 (OpenAI) e PR #12 (S0) permanecem Draft; sem merge/deploy, cliente real, banco ou Meta.
