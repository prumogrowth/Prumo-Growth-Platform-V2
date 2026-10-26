# E04 S0/F02 — origem observada de planos, tentativas e cancelamento C04/C08

**Checkpoint de laboratório:** 25/10/2026 (America/Recife). **Branch:** `feat/oai-s0-f03-history-port-20261023`. **Código certificado:** `84b954f1737afbbf2207eaae86317366b2eae923`. **PR #1 Draft**, sem merge nem deploy.

## Lacuna anterior

O atestado HMAC C08 até então vinculava campos `criado_em`, `cancelado_em`, carimbos de tentativas e marcos do atendimento humano. Contudo, esses campos físicos do legado podem ser reescritos pelo administrador PostgreSQL de laboratório. Um plano criado **depois** do caso humano, com `criado_em` artificialmente retroativo, poderia parecer anterior no contrato cronológico anterior. A ausência de um histórico de criação observado exigia uma segunda autoridade.

## Implementação efetiva

- `supabase/tests/s0_f02_c04_origin_ledger_local_only.sql`: instalou **apenas no PostgreSQL 17 descartável** um livro de eventos com trigger `AFTER INSERT/UPDATE` sobre casos humanos, planos C04, tentativas, reservas e eventos C08. Cada captura recebe um horário `statement_timestamp()` cunhado no banco, escopo da concessionária/lead, estágio/entidade e digest SHA-256 da linha capturada. Não há texto de mensagens, payloads de Meta ou dados reais.
- A tabela privada é append-only para os papéis normais, com bloqueio de update/delete, RLS e permissões restritas. Uma identidade superusuária `postgres` **pode alterar estruturas/desabilitar triggers**: este mecanismo é um laboratório S0 e **não é evidência à prova de administrador privilegiado** nem um registro WORM de produção. Não preenche históricos anteriores à instalação do trigger.
- A função restrita `prumo_private.cfi01_f02_check_origin_local(shop,lead,case)` exige que o registro de origem de cada plano e tentativa exista e tenha sido **observado no banco antes** da abertura observada do caso humano; cancelamentos C08 têm de vir depois do caso. Exige consistência de propriedade/escopo, estado cancelado, eventos de cancelamento e hash final da linha contra a observação feita no instante de cancelamento. A ausência de origem, exclusões, adulterações e reservas levam a estados de revisão, nunca a uma autorização.
- Tentativa que passou por `reservado` é reconhecida tanto ao nascer reservada quanto por transição registrada `RESERVE`; o estado `RESERVED_EXTERNAL_UNKNOWN` impede declarar cancelamento externo com base no banco.
- `backend/s0_f02_legacy_observed_origin_local.py`: porta tipada que **primeiro** exige a verificação S0/F03 e o testemunho C08 assinado da frente anterior e **depois** consulta o livro de eventos físico sob transação somente leitura. O retorno de maior confiança é `LOCAL_OBSERVED_ORIGIN_REVIEW_ONLY`. Não cria recontato, não dispara mensagens, não modifica ficha e não concede autoridade ao JavaScript da F02.
- `scripts/run-s0-f03-pg17-local.sh`: inclui apenas o SQL E04 e testes Python próprios da frente. Nenhum arquivo `.github/workflows/*`, branch S1, migração real ou banco Supabase hospedado foi alterado.

## Casos demonstrados

- Um C04 sintético criado **após** a abertura do caso humano, com `criado_em` retroativo, retorna `LATE_OBSERVED_SOURCE`. O antigo comprovante HMAC isolado não consegue transformá-lo em comprovante de origem verdadeira.
- Uma cadeia C04 sintética **realmente observada antes de um novo caso humano criado no banco**, com tentativa programada e cancelamento local C08 subsequente, retorna `LOCAL_ORIGIN_VERIFIED_AUDIT_ONLY` na função privada local, sem envio.
- Mudança posterior do estado final do plano ou do evento C08 resulta `MUTATED_ORIGIN`; alterar `criado_em` depois do cancelamento não restaura a confiança da origem. Reserva prévia resulta `RESERVED_EXTERNAL_UNKNOWN`; histórico ausente e acesso sem privilégios são negados.
- Os registros de origem são parte de um novo gate que precisa ser cumprido em qualquer contrato pós-humano futuro. O **gate de cronologia legado permanece existente**, para detectar também inconsistências de horário e de evento; os dois controles não são intercambiáveis.

## Certificação objetiva

**[GitHub Actions #40252762564 — SUCCESS](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40252762564)** sobre o SHA de código exato `84b954f1737afbbf2207eaae86317366b2eae923`.

- 84/84 testes Python S0, 483/483 testes Python F02/F03, sendo 310 testes físicos PG17 acumulados. **567/567 Python**.
- **269/269 Node** nativos, com S2 fixada em seu SHA de referência. São 836 verificações em duas suítes distintas, **não** 836 jornadas de ponta a ponta nem os 70 oráculos E02 homologados.
- **Novos:** 10 testes físicos #301–310 e 7 unitários de porta/estados. Os cenários reais do laboratório incluem origem correta, data retroativa, trilha de reserva, alteração posterior, ausência de cadeia, RLS e imutabilidade.
- Nenhuma falha foi ocultada; a suíte integral certificada é posterior à inclusão completa dos testes. Códigos intermediários sem suíte completa aprovada não são contados como certificados.

## Limites e próxima frente

- O momento observado é **interno a PostgreSQL**. Hash dos registros demonstra consistência de snapshots, não integridade incondicional contra superusuário, relógio do host adulterado, prova de autorização humana real ou entrega/cancelamento na Meta.
- Cadeias pré-existentes antes da instalação do ledger ficam `MISSING_ORIGIN`: devem ser tratadas por um fluxo de revisão legado distinto, sem geração retroativa de falsos atestados.
- Ainda falta contrato **independente** de planejamento pós-humano, com aceite/assinatura de autorização S0/S1 em runtime real, consentimento, opt-out, catálogo Meta, controle temporal e de frequência, idempotência/estados e autorização de envio separada. C04 pré-humano continua negando casos humanos.
- Manter cada frente na sua branch, preparar integração futura em branch própria com validação e autorização antes da `main`. Issue #3 trata de auditoria inicial da S1 e não autoriza mudanças. Nenhuma alteração nos workflows de outra frente, no Supabase hospedado, nas APIs Meta/OpenAI, em clientes reais ou na main.
