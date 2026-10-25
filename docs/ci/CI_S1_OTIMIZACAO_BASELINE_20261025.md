# Otimização experimental do CI/S1 — baseline e controle de regressão

Data: 2026-10-25. Escopo: experimento isolado da Issue #3. Não altera nenhum workflow vigente da S1, não libera merge, implantação nem redução de testes.

## Fonte congelada
- Branch de origem: `feat/s1-002-equipe-prumo`.
- Commit base: `1b56375739017eeb5f3608f1bad2b294eb6c89dc` (I68).
- Branch experimental: `exp/ci-s1-consolidacao-20261025`. Desenvolvimento da frente continua na branch de origem; comparação futura deverá ser feita no mesmo SHA de fonte, se possível.

## Evidência histórica de possível duplicação
- Commit de referência: `c50af9de` (não é o commit base do experimento).
- A partir dos registros de GitHub Actions, um único commit acionou **13 workflows**, com **23 jobs**, todos concluídos como sucesso, em execuções independentes.
- Soma dos intervalos `started_at` a `completed_at` de todos os jobs: aproximadamente **33,70 runner-minutes observados**, não equivale necessariamente ao valor faturado pelo GitHub.
- Em workflows I27, I28, I31 e I37 identificou-se inicialização repetida de `supabase/setup-cli`, GoTrue, PostgREST, cliente SQL, `psycopg`, e suítes unitárias cumulativas. As execuções de integração têm cenários exclusivos; sucesso do I37 isoladamente **não substitui** os testes específicos dos anteriores.
- Exemplo: [I31 Actions](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40193208441).

## Critérios antes de propor qualquer substituição
1. Fazer inventário 1:1 dos casos de teste por workflow e seus gatilhos de `paths`, incluindo segurança (revogação, mTLS, rotação, witness, HMAC, RLS, CAS, concorrência).
2. Investigar se as suítes E2E aceitam compartilhar a mesma inicialização do GoTrue/PostgREST. **Não presumir** independência de estado: testes com falha/reinício, rotação, revogação e relógios podem precisar de isolamento próprio.
3. Implementar candidato exclusivamente nesta branch experimental. Sem criar workflow em `main`; evitar efeitos colaterais em CI de PRs ou na S1 de produção.
4. Medir no mesmo commit: todos os testes obrigatórios, resultados, somatório do tempo de **jobs** e eventuais flakies/falhas. Apresentar logs e matriz de equivalência.
5. Caso um teste perca cobertura ou uma etapa passe a gerar falsos positivos/negativos, rejeitar o experimento. Não desativar workflows nem mudar branch oficial sem revisão do owner S1 e autorização.

## Não objetivos
- Consolidar branches de produto, alterar funções comerciais, conectar Meta/OpenAI real, mexer em segredos, mexer em migrations e automatizar merge/deploy.

## Resultado do primeiro ensaio experimental (25/10/2026)
- [GitHub Actions run #40199747311](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40199747311): **SUCCESS**, duração do job de `13:54:21Z` a `13:57:32Z` (**3 min 11 s**).
- O log confirma as cinco suítes unitárias com `Ran 30 + 10 + 10 + 13 + 15 = 78 tests` (78 casos, não 68), `S1-002/I27: 80/80` e `S1-002/I28: 93/93`.
- Duas pilhas GoTrue/PostgREST efêmeras independentes: I27 em **105 segundos** (incluiu download de imagem no runner) e I28 em **54 segundos**.
- Controle histórico correspondente aos mesmos workflows I27/I28 no commit `c50af9de`: **5,55 minutos** somados dos quatro jobs. Comparação exploratória, ainda **não isócrona nem isocommit**.
- O primeiro ensaio sugere redução de cerca de **43%** no somatório do tempo de jobs, com ressalvas de cache, imagem, hardware, alterações de código posteriores e diferença de configurações.
- **Não** desativar workflows vigentes antes de repetir e comprovar cobertura 1:1 e reprodutibilidade.

Esta atualização documental provoca intencionalmente uma segunda execução do workflow experimental, **sem alterar código de S1 ou workflow**; seu resultado será analisado separadamente.
