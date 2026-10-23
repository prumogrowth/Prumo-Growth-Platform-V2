# S1-002 / I48 — auditoria S0/013–037 e autorização contextual C04

**Corte:** 23/10/2026. **Classificação:** protótipo RLS [P], regressão em ambiente local [T], integração operacional e decisão A2 [R]. Não aplicar ao Supabase hospedado, não executar Meta, não fazer merge.

## Origem e risco comprovável

A S0/016 cria `evidencias_elegibilidade_sinteticas` e `supressoes_contato_sinteticas`, legíveis a `gestor` por concessão da loja. A concessão não é prova de supervisão de uma equipe nem de autorização por caso. Os registros são sintéticos e **não constituem consentimento jurídico nem prova Meta**. O I48 verifica se o Gestor ativo consegue enxergar registros de outra equipe e de lead sem caso no mesmo estabelecimento. A suspensão S1 é negada indiretamente pela RLS dos vínculos, conforme o I47.

As migrations S0/023–027 e S0/036–037 instituem `prumo_s0_gateway`, `prumo_s0_signer` e `prumo_s0_signed_executor`, funções privilegiadas e provas HMAC. A propriedade de funções e o direito efetivo de execução precisam ser examinados no catálogo; um `SECURITY DEFINER` isolado não demonstra violação nem segurança final.

## Entregas exclusivas de laboratório

- `scripts/test_s1_002_i48_optout_acl.py`: executado após I47, reutiliza JWTs GoTrue reais e PostgREST no Supabase CLI descartável. Extrai **somente DDL, GRANTs e RLS originais** do início da migration S0/016. Não aplica suas substituições de rotinas nem seu REVOKE global, porque a stack reduzida não tem a ordem cronológica S0/S1 completa.
- `supabase/tests/s1_070_optout_escopo_local_only.sql`: seis policies candidatas. Combinam restrição AND ao lead/caso autorizado I45, permissão OR à equipe sem concessão genérica da loja e exigência de ator S1 ativo. Lead sem caso permanece sem leitura até a S0 pactuar uma projeção.
- `supabase/tests/s1_071_gateway_acl_catalog_local_only.sql`: valida catálogo real na regressão PG17 que carrega S0/001–037 completa. Confere papéis sem login, owner das funções assinadas, `EXECUTE` de gateway assinado e negação de execução/leitura dos segredos por cliente autenticado.
- `scripts/test_s1_002_i48_acl_crosswalk.py`: inventário estático JSON de migrations S0/013–037, tabelas, funções, SECURITY DEFINER e policies. Não substitui ACL catalogada nem os testes existentes de concorrência da S0.
- Gatilhos CI PG17 e GoTrue atualizados para executar o incremento junto às regressões anteriores.

## Critérios de teste

1. **I48-01:** leitura original por loja alcança evidências/supressões de outras equipes e lead sem caso.
2. **I48-02:** S1 suspenso já é negado pela RLS indireta antes da policy candidata.
3. **I48-03:** leitura candidata limita-se a contatos com caso autorizado; nega lead sem caso e outsider.
4. **I48-04:** revogação de concessão de loja preserva o acesso contextual de equipe.
5. **I48-05:** encerramento da chefia após COMMIT revoga a leitura com o mesmo JWT.
6. **I48-06:** mensagem com `caso_id IS NULL` segue fail-closed; cliente não insere evidência/supressão via REST; seis policies presentes.
7. **I48-CATALOG / I48-SOURCE:** conferência da fronteira de roles do gateway assinado e inventário das migrations de S0.

## Limites explícitos

São evidências de laboratório, não de migração homologada. A sequência PG17 testa todas as migrations S0 e funções, mas não opera GoTrue real; a stack GoTrue testa somente a fatia DDL/RLS de S0/016, sem seus procedimentos internos finais. Os testes de mudança de chefia constatam o efeito **após commit**, não corrida em duas sessões dos candidatos I48. Os testes já existentes da S0 cobrem concorrência em outros contratos; não equivalem a integração pronta.

A S0 continua autoridade de leads, ciclos, casos, mensagens, fila, opt-out, callbacks e eventos. Não foi autorizado inferir acesso ao inbox sem `caso_id`, usar evidência fictícia como consentimento real nem expor D3/D4. A2 permanece [R]. **PR #5 Draft, sem deploy ou merge.**

## Evidências

Preencher somente após observar os jobs completos e seus logs.
