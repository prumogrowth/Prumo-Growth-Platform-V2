# WA-55 — Entrada única assinada e bloqueio tardio dos caminhos históricos (PG17)

**25 de outubro de 2026. Banco descartável `prumo_s0_test_ci`; PR #2 Draft; nenhum deploy em Supabase hospedado.**

## Contrato técnico candidato

Após WA54, o caminho de laboratório com melhor proteção transacional da leitura de estado é a WA52: associação exata do vínculo S0 com App/WABA/phone/intenção/attempt/correlation/recipient/wamid, bloqueio `FOR SHARE` da outbox original, serialização pelo evento WA39, validação HMAC/nonce e lançamento nas tabelas forenses originais. A WA55 envolve essa função com a nova entrada `prumo_private.meta_wa55_single_entry_fixture_s0(...)`, de propriedade `prumo_s0_meta_wa50_writer_lab` (NOLOGIN, não superusuário, sem BYPASSRLS). Ela valida o `session_user` fictício do laboratório, verifica a resposta sem permissão comercial e identifica explicitamente `entrypoint=WA55_PG17_SINGLE_LAB_ONLY`, `runtime_principal_authenticated=false`.

O cliente sintético tem EXECUTE somente na entrada WA55. A função chama internamente WA52, que conserva os controles WA51 de assinatura e os locks WA52, e confirma que não pode conceder envio, ACK, caso ou autorização produtiva. As funções históricas permanecem como código para auditoria, mas não são pontos de entrada disponíveis ao cliente sintético **ao final da regressão**.

## Selagem após regressão: decisão intencional

A migration `202610230054_s0_meta_single_entry_seal_fixture.sql` **não** integra o ciclo inicial de migrations. O arquivo `scripts/run-s0-local.sh` primeiro executa todas as regressões existentes WA39–54 e os scripts de corrida. Somente depois aplica a migration WA55, que cria a entrada restrita e revoga EXECUTE direto do papel cliente nas funções WA48, WA49, WA50, WA51 e WA52, além de revogar o EXECUTE da antiga entrada WA40 do papel fictício de ingresso. Assim é possível provar tanto o comportamento legado quanto a **inacessibilidade dos caminhos antigos na condição final**; não removemos ou silenciamos os testes históricos.

O privilégio de execução interna WA52 do escritor não é revogado, pois é necessário à delegação da entrada única. Da mesma forma, outras funções postgres-only de administração S0/043 não constituem a superfície cliente e **não são seladas por esta migration**.

## Provas

`supabase/tests/s0_wa_059_assert_single_entry_sealed_pg17.py` incorpora 36 marcadores após a selagem: dono/ACL/default deny, rotas legadas inacessíveis, papéis não logáveis, impossibilidade de SET ROLE, privilégio mínimo, vínculo sintético independente, chave HMAC aleatória, escopo negado sem nonce, MAC inválido, observação gravada no ledger S0, replay, variante, divergência em conflito, rollback atômico do nonce, concorrência status-versus-cancelamento com bloqueio efetivo, classificação tardia, revogação, ausência de receipt no shadow e flags comerciais falsas. Somar 36 à base WA39–54 (439) apenas após CI **SUCCESS** no HEAD exato.

## Limites

A WA55 não transforma o papel de laboratório em uma identidade Meta real. O wrapper e a WA52 mantêm limitações de confiança em parâmetros derivados do fixture; o trigger compartilhado WA50 e seu guard `UPDATE(id)` ainda exigem avaliação de menor privilégio. Rotas `postgres` internas e papéis administrativos mantêm acesso poderoso no banco de testes. Não foram executados Meta webhook HTTP real, Graph/ACK, envios, retry, mudanças comerciais, S1, autenticação IAM/M2M real ou deploy Supabase. **Não promover a produção.**

**Dependência da S1:** nenhuma alteração necessária à frente S1 para concluir a WA55. Antes de encadear operações reais, será necessário acordar um contrato de cancelamento e autorização de estado, via solicitação específica.
