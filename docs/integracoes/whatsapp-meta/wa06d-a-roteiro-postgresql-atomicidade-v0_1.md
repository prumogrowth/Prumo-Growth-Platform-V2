# WA-06D/A — roteiro PostgreSQL descartável para atomicidade de ingresso

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
