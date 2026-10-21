# WA-06D/A — roteiro PostgreSQL descartável para atomicidade de ingresso

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Data:** 18/10/2026. **Estado: [P], preparado e NÃO executado em PostgreSQL.** Entrega pequena da frente WhatsApp/Meta para revisão conjunta com a S0. Não é migration, API, autenticação ou instalação.

## Entrega

Arquivo: [`integrations/whatsapp-meta/lab/wa06d_pg17_atomicity.sql`](../../../integrations/whatsapp-meta/lab/wa06d_pg17_atomicity.sql), blob Git `775ad5909a5f269281d7d122c2b8475e7f41d154`.

O roteiro usa **7 tabelas temporárias**, uma função de teste `pg_temp.wa06d_accept`, um conjunto de **11 verificações candidatas** e `ROLLBACK` no final. Ele não cria tabelas em `public` ou `prumo_private`, nem modifica migrations S0. Integração conceitual revisada com S0-029/032/033: lote, corpo de teste, nonce, ocorrência própria, tarefa e marcador de recibo coexistem na mesma transação. O corpo é **sintético em claro**, não armazenamento protegido de produção.

**Execução desejada apenas quando houver PG17 descartável local:**
`psql -X -v ON_ERROR_STOP=1 -f integrations/whatsapp-meta/lab/wa06d_pg17_atomicity.sql`.
Não executar com URL de Supabase hospedado. A execução esperada emitirá `WA06D-01..11 PASS` e, por fim, `ROLLBACK`. Exigir logs e revisão antes de registrar aprovação.

## Matriz de testes planejados — não executados

| Gate | Invariante sob teste |
|---|---|
| WA06D-01 | lote grava juntos corpo, nonce, ocorrência, tarefa e marcador de recibo |
| WA06D-02 | replay idêntico ou novo nonce para lote idêntico não duplica tarefas |
| WA06D-03 | nonce em lote diferente não passa |
| WA06D-04 | mesma solicitação com corpo alterado é negada |
| WA06D-05 | falha injetada após corpo desfaz tudo |
| WA06D-06 | falha após ocorrência desfaz tudo |
| WA06D-07 | nova tentativa válida após rollback funciona |
| WA06D-08 | callbacks repetidos com mesmo `wamid` e posições distintas são preservados |
| WA06D-09 | mistura entre concessionárias do mesmo App é negada |
| WA06D-10 | canal revogado na fixture bloqueia novos ingressos |
| WA06D-11 | marcador de recibo é consultável **dentro** da transação, não uma prova pós-commit |

**Evidência disponível nesta sessão:** leitura do arquivo publicado no GitHub + **8 verificações estruturais estáticas aprovadas**, incluindo `BEGIN/ROLLBACK`, sete tabelas TEMP, onze marcadores, ausência de `SECURITY DEFINER` e DDL operacional. O ambiente disponível possui `pg_config 17.11`, **mas não tem `psql`, `postgres`, `initdb` ou `pg_ctl`**. Portanto **0/11 testes PostgreSQL foram executados** e não se presume que o SQL passará na primeira execução. Correções futuras, caso necessárias, serão registradas como etapa separada.

## Gaps explicitamente fora desta etapa

1. `p_principal` é texto **injetado por fixture**, não identidade autenticada. A tabela de escopo é TEMP com dados fictícios. Ausência de validação de HMAC Meta, prova interna, identidade revogável, papel mínimo/RLS e algoritmo de assinatura WA-06B.
2. `sha256` é consistência não HMAC/autorização. Corpo em tabela TEMP não é sigilo, retenção nem backup de produção.
3. O marcador `IN_TX_ONLY` não autoriza HTTP 200: teste termina em `ROLLBACK`, e nenhuma prova de commit **pós-transação**, `COMMIT_UNKNOWN` ou recuperação em outra sessão foi executada.
4. Sem concorrência em duas sessões, rotação de chaves simultânea, `service_role`/GoTrue/REST, DDL S0 aprovado, contrato de erros e ACK DEC-WA-06.
5. WA-07/CF-OP-02 regula mensagens de saída, janela Meta 24h, templates e `sent` comprovado; este ensaio é somente **ingresso** e não altera C03/C06/C09/C12.

**Dependência [R S0]:** avaliar se a proposta PG deve ser adaptada às tabelas já existentes do núcleo, sem criar novo schema comercial nem misturar S0-037F mock com identidade Meta real. A futura WA-06D/B precisa rodar testes PG17 e depois exercício de múltiplas sessões para revogação/recibo. DEC-WA-04/06 continuam pendentes; PRs Draft; não executar CI pago, deploy, migrations hosted, Graph/Meta ou POC concessionária de demonstração sem aprovação.

## WA-06D/A2 — proteção do executor local (18/10/2026)

**Reparo auditado:** a linha de comando original para `psql` poderia ser usada manualmente com uma conexão não descartável. Acrescentado `integrations/whatsapp-meta/lab/run-wa06d-local.sh`, que aceita somente um argumento `wa06d_test_<sufixo>`, fixa `-h 127.0.0.1 -p 5432`, recusa nomes de produção/URLs/parâmetros extras, limpa `PGHOSTADDR` (override libpq potencialmente remoto), `PGSERVICE`, `PGSERVICEFILE` e `PGOPTIONS`, e se nega a continuar sem `psql`. A restrição é de execução local; um túnel/encaminhamento de portas configurado fora do programa não é detectável, então **usar somente banco efetivamente descartável**. Não há conexão de banco nesta entrega.

O teste versionado `integrations/whatsapp-meta/lab/test_wa06d_runner.py` usa **psql falso**, sem qualquer conexão SQL. **5/5 testes Python PASS locais** e `bash -n` PASS. Entre os testes estão URL/nome real, argumentos extras, `psql` ausente, conexão fixada ao loopback e variável `PGHOSTADDR` remota propositalmente presente, comprovadamente eliminada. Blobs Git idênticos aos arquivos executados: runner `1d8cfc533712f12a0d77b357fc08862a4b96ebe2`, testes `6b350156226bb2d3e84c61fefbb9a5707ca537f5`.

**Comando recomendado quando houver PostgreSQL local descartável já provisionado:**
`bash integrations/whatsapp-meta/lab/run-wa06d-local.sh wa06d_test_scratch`

**Contagem honesta:** **5/5 testes do protetor de execução aprovados; 0/11 testes SQL PostgreSQL executados**. O SQL continua candidato, pode precisar de correções ao ser executado; tampouco houve prova de durabilidade pós-commit nem concorrência em duas sessões, muito menos autenticação de produção.

## WA-06D/A3 — reparo de identidade posicional e 14 casos (18/10/2026)

**Falha identificada na revisão pré-execução:** a tabela TEMP de ocorrências usava `UNIQUE(batch,kind,item_index)`, insuficiente para um POST Meta com `entry[]` e `changes[]` agregados: dois eventos legítimos em entradas diferentes podem compartilhar o mesmo índice de item. O contrato WA-05C/WA-06B exige **quatro coordenadas** `entry_index + change_index + array_kind(messages|statuses) + item_index`. Este é um **achado de inspeção técnica**, não falha reproduzida em PostgreSQL.

**Reparo em código SQL publicado** no blob `e011969413332565bc4c3e1e37490f5ad99d5ac8`: acrescenta `entry_index` e `change_index` com validação de tipo/limites, troca a unicidade pela posição completa, preserva callbacks com mesmo `wamid` em posições distintas e restaura o canal da fixture depois do teste de revogação WA06D-10 para que testes posteriores não sejam contaminados. Continua isolado em TEMP, sem DDL S0.

**A matriz foi ampliada dos 11 casos originais para 14 casos candidatos:**
- `WA06D-12`: duas posições `entry[]` diferentes com o mesmo `item_index=0` são legítimas e geram duas ocorrências/tarefas.
- `WA06D-13`: repetição da **mesma posição completa** falha, com rollback integral de batch, corpo, nonce, ocorrências e recibo.
- `WA06D-14`: dois canais válidos e distintos da mesma Meta App/concessionária são admitidos.

**Verificações realmente realizadas:** 11 critérios estáticos conferidos diretamente no conteúdo publicado — sete tabelas TEMP, função `pg_temp`, quatro coordenadas na chave, todos os 14 marcadores, ausência de índice antigo, fixtures multientrada/dois canais, negativa de duplicação, restauração pós-revogação, BEGIN/ROLLBACK e ausência de DDL persistente. Estas verificações **NÃO executam SQL**. O ambiente segue sem `postgres`, `psql`, `initdb` ou `pg_ctl`, portanto **0/14 testes PostgreSQL executados**, inclusive 0/11 originais. Não considerar versão anterior como validada nem concluir WA-06D.

**Próxima dependência [R S0]:** executar e revisar a sintaxe/resultado em PG17 descartável; se necessário, reparar e reexecutar. Depois de execução local aprovada, desenvolver separadamente concorrência, autenticação de workload, nonce/revogação transacionais e recibo pós-commit/COMMIT_UNKNOWN. Nenhum ACK, token, Meta real, hospedagem ou migração autorizado por esta etapa.

