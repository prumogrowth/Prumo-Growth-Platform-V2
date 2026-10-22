# S1-002 / I43 — integração de RLS de equipe, histórico e exceção revogável

**Data:** 22/10/2026. **Fonte normativa:** S1-D05, D12, D13, D18, D19 (contrato funcional 2026-10-22). **Estado:** candidato [T] no PostgreSQL 17 descartável; não é migration de produção ou alteração homologada S0.

## Falha composta identificada
As provas I41 e I42 rodavam separadamente. A RLS `RESTRICTIVE` de I41 exige o escopo próprio/de equipe, mas a exceção I42 autoriza precisamente um Consultor sem grant geral da concessionária. **Com ambas aplicadas, o AND implícito das políticas restritivas volta a negar o caso autorizado**, enquanto a view de resumo executada como dono do laboratório ainda mostra o histórico. Este estado inconsistente é testado explicitamente como `I43-RED`. A primeira execução integrada (#39870328769) também detectou o inverso: a `RESTRICTIVE` de mensagens de I42 negava ao Gestor sem grant geral o histórico de sua equipe, mesmo quando a regra I41 o autorizava. A composição deve substituir **as duas** policies restritivas de mensagens por uma única restrição conjunta, sem deixar uma segunda política com `AND` residual.

## Implementação e prova
- `supabase/tests/s1_061_proto_rls_equipe_local_only.sql`: mesmas funções/policies candidatas I41, extraídas para evitar divergência entre prova isolada e integrada.
- `supabase/tests/s1_062_setup_historico_excecao_local_only.sql`: fixture I53/I54/I55 com dados fictícios e transferência excepcional em loja A.
- `supabase/tests/s1_062_proto_rls_excecao_local_only.sql`: as mesmas funções/policies de exceção I42 para histórico por contato.
- Os testes I41 e I42 isolados passam a reutilizar esses arquivos; continuam `BEGIN/ROLLBACK`.
- `supabase/tests/s1_063_rls_unificada_equipe_excecao_local_only.sql`: importa simultaneamente os dois candidatos e reproduz o conflito; depois substitui *apenas no sandbox transacional* as restrições de casos/atribuições/conversas e **ambas** as restrições de mensagens por guardas **por linha** com `I41 autorizado OR I42 autorizado`. Os critérios já existentes, atribuição atual, `auth.uid()`, concessionária, chefia, revogação e correlação mensagem-caso permanecem aplicados em cada ramo. 
- O runner `scripts/run-s1-002-i12-local.sh` executa I43 na suíte PG17, sem alterar o S0 histórico nem dados reais.

## Aceites do I43
1. **RED:** I42 isolado fornece o histórico, mas a adição das policies I41 corta SELECT enquanto resumo continua visível.
2. **I43-01:** Consultor com exceção válida lê o caso atual e todo o histórico do mesmo contato/loja, sem acesso a outro contato, loja ou coleções S0 brutas.
3. **I43-02:** Gestores da própria equipe, inclusive sem grant geral da loja, veem atendimentos atuais e passados pertinentes, sem acessar outras equipes.
4. **I43-03:** Consultor com grant de concessionária não recupera carteira já transferida só por possuir esse grant.
5. **I43-04:** leitura do histórico não dá envio no caso antigo; envio simulado no caso corrente continua possível.
6. **I43-05:** revogação da exceção corta leitura, resumo e escrita após nova instrução SQL, sem apagar a atribuição vigente no S0.
7. **I43-06:** supervisor mantém acesso à própria equipe e trilha de eventos permanece auditável; todas as mudanças são `ROLLBACK`.

## Limites para a integração real
Esta prova **não** usa JWT real GoTrue, PostgREST, S0 de produção, nem integra dados D3/D4, status/badges, mensagens sem `caso_id` e schemas futuros. As funções `SECURITY DEFINER` e views `security_barrier` precisam de revisão de owner, `search_path`, grants e risco de bypass/enumeração; políticas antigas por loja em outras tabelas continuam amplas e necessitam inventário completo. Transferência para Consultor pausado A2 permanece [R]. A S0 deve concordar sobre a matriz de autoridade e o contrato de histórico antes de converter candidatos em migração.

**Evidência de CI verificada:** [GitHub Actions PG17 #39870601182 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39870601182), job `120143761603`, código SQL I43 testado no commit `f4b642d6a0ddba631e038c9eab6a95af10321d62`. Logs `OBSERVED I43-RED`, `PASS I43-01` a `PASS I43-06/ROLLBACK`, regressões I41, I42 e corridas I40 aprovadas. A execução anterior [#39870328769](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39870328769) reprovou por conflito residual da política restritiva de mensagens I42; foi necessário substituir as **duas** policies restritivas ao aplicar a união. Este sucesso prova **apenas** transações e JWT simulado no PG17. PR #5 continua Draft, sem merge/deploy; ainda não há validação desse candidato com GoTrue/PostgREST reais.
