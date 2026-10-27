# G1 / Issue #17 — implementação e reprodução

Entrega S0 de 2026-10-26 (America/Sao_Paulo), branch própria
`exp/s0-g1-encaminhamento-manual-20261026`, baseada no PR #18. Contrato e limitações:
[CONTRATO_G1_MANUAL_V1.md](CONTRATO_G1_MANUAL_V1.md).

## Causa da dependência

A fila I54/I76 tinha distribuição automática e assunção pessoal pelo Gestor.
I61 movia caso já atribuído. Não havia porta canônica autenticada para criar,
a partir da fila sem titular, uma atribuição ao Consultor da própria equipe e,
somente se necessário, a exceção por caso/atribuição sem grant geral da loja.
Não se tratava de corrigir a assunção I76 nem de repetir I74 ou Meta.

## Código entregue

- `43262c15e301ddc8458cec49cad0b5704a28d014`: operação G1, SQL privado,
  contrato validado, reuso físico de I54–I62 e testes reais iniciais.
- `d5e6c658e487c295babf0ef04fc5cb9d9f2dffe7`: árvore completa com preparação
  de chave pelo custodiante explícito I22, sem grants adicionais.
- `33c0abf41c011144c696b726d1f7794ac0a31402`: fechamento garantido da conexão
  inclusive quando o COMMIT falha por constraint adiada, runner S1 corrigido,
  provas adicionais de RLS interloja e retentativa simultânea.
- `d53c40a6ef55e82d2282c482b299cff1dbf990bd`: instalação do delta separada da
  criação de dados G1 para preservar os pressupostos dos aceites antigos I61.

O backend S0 existente e suas funções CFI-01/F02 não foram reescritos. O único
arquivo existente alterado foi o carregador de fontes de laboratório, com
`--manifest` opcional e padrão anterior preservado. O restante é adição isolada.
Não foram alterados arquivos de migrations oficiais ou branches de outras frentes.

## Histórico de execução e limites das primeiras tentativas

1. [40433034433](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40433034433),
   commit `43262c1`: regressões anteriores passaram; G1 não iniciou porque o
   instalador não herda acesso à tabela de chaves I22. Corrigido com `SET ROLE`
   explícito do custodiante já existente, depois `RESET ROLE`.
2. O commit intermediário `10429301ebe2649ced08da09687ce19dbf9ef848` publicou
   árvore incompleta na branch experimental. Corrigido por fast-forward em
   `d5e6c658`, com igualdade do tree SHA remoto e `git write-tree` local conferida.
   Nenhuma branch alheia foi escrita. Não é checkpoint utilizável.
3. [40433999975](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40433999975),
   commit `d5e6c658`: 34/34 cenários G1 reais passaram, assim como as regressões.
   O runner dos aceites antigos falhou por ausência de `PYTHONPATH=.`; corrigido.
   O teste de falha adiada também revelou conexão aberta no caminho excepcional
   do driver: adicionado fechamento explícito com `contextlib.closing`, e os
   testes de falha agora verificam ausência de sessão SQL adicional aberta.
4. [40434466185](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40434466185),
   commit `33c0abf4`: 36/36 G1 reais, 272 unitários e regressões CFI/F02/histórico
   passaram. I54 8/8, I56 6/6, I57 5/5 e I58 6/6 passaram. O aceite I61 chegou
   a 05, mas seu `SELECT id ... WHERE revogada_em IS NULL` sem filtro de escopo
   escolheu exceção de outro cenário; seu count global de eventos também pressupõe
   tabela vazia. O SQL original não foi editado: agora roda após instalar o DDL
   G1 e antes de popular os registros G1. O teste autenticado G1-22 revogou a
   exceção correta com sucesso no mesmo ambiente. Nenhum guard foi afrouxado.

Não se usa nenhuma dessas tentativas parciais como certificação completa.
O arquivo de evidências da entrega identifica a execução final e seu commit.

## Execução final certificada no ambiente descartável

[CI 40434954253](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40434954253)
— **SUCCESS**, commit `d53c40a6ef55e82d2282c482b299cff1dbf990bd`, job
`121961301434`, início `2026-10-27T01:50:44Z`, conclusão `01:54:08Z` (204 s).

| Camada | Resultado |
| --- | --- |
| Unitários S0/F02 + compatibilidade G1 | 272/272; 264 preservados e 8 novos |
| G1 GoTrue/PostgreSQL/PostgREST reais | 36/36, 8,207 s na suíte |
| CFI-01/F02 reais preservados | 56/56 = 32 CFI-01 + 24 F02 |
| Histórico real | 19/19 S0 + 19/19 perfil S1/I63 |
| Bootstrap Auth/CFI real | 18 famílias Auth e 10 cenários CFI-01 |
| SQL S1 original, identidades sintéticas | 34/34: I54 8, I56 6, I57 5, I58 6, I61 9 |
| Fechamento de conexões / descarte da stack | sem ResourceWarning; cleanup SUCCESS |

Hashes dos arquivos executáveis, nomes dos 36 testes, marcadores dos 34 aceites
SQL e identificação de run/job estão em [evidencias.json](evidencias.json).
O commit seguinte de documentação não altera a árvore executável certificada.

## Provas funcionais da suíte G1

`integration/g1/test_manual_handoff.py`: identidades criadas no GoTrue real,
duas lojas por cenário e dois Gestores de equipes distintas, ambos autorizados
à loja A; somente o primeiro autorizado à loja B. Consultores com/sem grant.

| Cenários | Prova |
| --- | --- |
| 01–05 | grant normal, exceção exata I61, RLS por equipe, destino incorreto/próprio e A2 |
| 06–12 | JWT inválido, sessão expirada, revogação da loja, vínculo alterado após espera, pausa, grant e sessão removida |
| 13–16 | comando I55 assinado original e distribuição I54 original disputam com G1, nas duas ordens |
| 17–22 | dois Gestores, idempotência, payload divergente, replay/tamper de prova, revogação I62 assinada original e corte REST |
| 23–27 | falhas em exceção, atribuição, auditoria, COMMIT adiado e resposta corrompida; rollback e retentativa segura |
| 28–34 | expiração durante espera, logout real, pausa espera atribuição, sem sinal/sem transferência, ACLs, caso externo I56 e loja sem grant |
| 35–36 | uma exceção não revela casos de outra loja/equipe; duas chamadas simultâneas com mesma chave criam um único pedido/caso/atribuição |

As disputas observam locks reais com `pg_blocking_pids`; não inferem concorrência
somente pelo tempo de espera. Injeções de falha são triggers exclusivamente do
banco descartável. Nenhuma identidade é um stub no percurso G1. Os aceites SQL
antigos usam seus próprios sujeitos sintéticos e são contabilizados separadamente.

## Reprodução e próximo passo da S1

1. Revisar o contrato interno v1 e o delta de evento `ENCAMINHADO`. A funcionalidade
   manual/A2 vem do contrato vigente; não requer criar nova regra comercial.
2. Criar checkout próprio desta entrega e stack local **nova e desvinculada**,
   usando CLI 2.84.2 e PostgreSQL 17. A referência completa é o workflow
   `.github/workflows/exp-s0-g1-manual.yml`; ele inclui descarte `always()`.
3. Reexecutar bootstrap Auth/CFI, histórico S0, suíte CFI/F02 e conferir o checkout
   S1 em `b71ebf4479c9a0a3527519471cca04ec7e178e18`.
4. Materializar fontes originais, instalar o delta e conferir as regressões S1 com
   os opt-ins do workflow:

   ```bash
   PYTHONPATH=. python3 integration/history/prepare_s1_profile.py --source-repo work-s1-sources --manifest integration/g1/s1_sources.json
   PYTHONPATH=. python3 integration/history/test_session_history.py --profile i63
   PYTHONPATH=. python3 integration/g1/install_local.py
   ```

5. Executar os cinco aceites SQL originais pelo runner do workflow **antes** da
   suíte `PYTHONPATH=. python3 integration/g1/test_manual_handoff.py`, sem editar
   fontes S1. Assim os aceites já exercitam o novo schema e não selecionam dados
   alheios por seus filtros globais. Se o HEAD S1 tiver avançado, reconciliar e
   fixar novo manifesto após revisão; não simplesmente trocar SHA.
6. Integrar futuramente em PR coordenado, preservando CAS, ordem de locks, RLS,
   I61 e validação pré-COMMIT. A fixture não é migration de produção.

Melhoria encaminhada à S1, sem alteração nesta entrega: em
`s1_085_excecao_caso_canonica_aceite.sql`, restringir a seleção de exceção na prova
06 ao caso/atribuição/Gestor da própria fixture e o count de eventos na prova 07
ao seu ID de exceção. Isso permitirá rodar o aceite original também depois de
dados de outros cenários; não exige mudar a autorização ou o revogador I61.

## Riscos e gates remanescentes

- Ownership de negócio ainda depende da ponte privada `postgres` exigida pelos
  guards legados. Login da aplicação não pode assumir executor nem chamar a
  ponte diretamente; isso não resolve o provisionamento hospedado com owner de
  negócio integralmente restrito.
- A porta e o formato são internos/experimentais. Endpoint, UI, transporte e
  adoção coordenada S0/S1 ainda precisam de revisão. Não se ratificaram D1–D4.
- Pausa recusa também repetição do comando; o caso anteriormente atribuído
  continua legível segundo a RLS vigente. Não há reativação de exceção revogada.
- Timeout/deadlock/falha de confirmação retorna `UNAVAILABLE`; mesma chave
  permite reconciliação sem nova atribuição. Não há retry cego com chave nova.
- Não se certifica ordem global de locks além dos escritores exercitados. CFI/F03
  para Consultor com exceção e sem grant geral permanece gate próprio; não se
  ampliaram grants para habilitá-lo.
- Primeiro contato humano, transferência, indicadores, envio/Meta, venda e
  contrato UI não são concluídos pela criação do caso. A Issue #17 deve ficar
  aberta para revisão e continuidade pela S1, sem auto-close ou merge.

Nenhum merge, deploy, migration hospedada, credencial real ou chamada comercial.
