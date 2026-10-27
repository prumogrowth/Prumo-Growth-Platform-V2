# S0/030 — Correções de auditoria 028/029 e compatibilização DEC-WA-05

**Escopo:** PostgreSQL 17 **efêmero**, fixtures sintéticas e código privado no PR #1. DEC-WA-01/02/03 continuam aprovadas como direção. **DEC-WA-05** é posterior e **aprovada somente quanto à titularidade:** cada concessionária controla seu próprio App, WABA, número, credenciais e concessão de acesso; Prumo integra sob autorização. Não confundir titularidade com onboarding, homologação ou autorização de operar. DEC-WA-04 (ambiente definitivo) e DEC-WA-06 (retenção/segredos/continuidade) continuam pendentes.

## Fonte documental

- PR #2, HEAD lido `af19a89cc737507d63d12018dc76004bc688a323`, `docs/integracoes/whatsapp-meta/decisao-titularidade-meta-por-concessionaria-v1_0.md` (DEC-WA-05), `interface-compartilhada-s0-meta-v0_1.md` e `revisao-cruzada-wa01b-s0-028-029-v0_1.md`.
- Migrações S0 001–006, 008–029 e contrato de permissões vigente. **Não alterar as migrações históricas 028/029**; correção aditiva 030.

## Implementação da migration `202610180030_s0_replay_multicanal_fixture.sql`

1. **A-01 — replay da pendência:** reimplementa via `CREATE OR REPLACE` a ponte privada `receber_mensagem_identidade_s0`. Antes do resolvedor, trava e busca pendência existente por loja/canal/ID externo. Duplicata com dados idênticos retorna `ALREADY_PENDING`; número ou texto conflitante lança `23505`, não silencia `ON CONFLICT DO NOTHING`. Pendência legítima não ativa IA.
2. **A-05 — integridade:** constrange `eventos_identidade_s0` a apontar alias do **mesmo lead e concessionária** por FK composta; impede alias marcado como confirmado com chave de variante ausente/incorreta.
3. **A-02 — ensaio multicanal:** adiciona `meta_apps_fixture_s0` e `meta_canais_fixture_s0` exclusivamente em `prumo_private`, com identificadores `FIXTURE_*`, FKs compostas e App de teste vinculável a **uma** concessionária e vários emissores. Esse cadastro **não** representa App real nem autoriza mudança de `canais_loja`. A função `aceitar_lote_multicanal_fixture_s0` recebe itens de múltiplos canais em **uma transação**, resolve escopo exclusivamente do registro interno fictício, rejeita claims de loja/canal no corpo e reverte **todo** o lote se houver remetente desconhecido, desvio ou conflito.
4. **A-03 — referência recuperável sintética:** adiciona `payload_fixture_s0` e campos de correlação ao inbox já existente, vinculando uma `fixture_ref` estritamente fictícia a cada evento novo do caminho 030. O legado 029 **continua metadata-only**, portanto **não é** contrato de ACK Meta real. Não há cofre, cifragem, durabilidade de arquivos externos ou retenção aprovada.
5. **Callbacks:** a chave sintética de status discrimina ID da mensagem + tipo de status + timestamp do provedor; **não** presume que `statuses[].id` seja ID único do callback. Ainda exige revisão semântica dos campos de status Meta para dedupe real.
6. **A-04 — formatação:** o parser Meta da frente #2 expõe identificador técnico sem `+`; a S0/028 usa formato com `+`. **Não** foi introduzido conversor operacional nem prova móvel real. A normalização só poderá ser vinculada após contrato seguro de proveniência, especialmente para distinguir fixo/celular, reciclagem e conflito.

**Limites de acesso:** tudo permanece `SECURITY INVOKER`, com `current_user='postgres'` para ensaio, sem EXECUTE de `anon`, `authenticated`, `service_role` ou `prumo_s0_gateway`. Nenhum worker, endpoint, webhook, segredo real, número comercial, chamada Graph, ACK HTTP ou envio liberado. RLS ativada nas novas tabelas privadas. Ainda não existe um papel de serviço reduzido para esses protótipos.

## Testes e evidência

- `supabase/tests/s0_wa_030_auditoria.sql`: replay idempotente de pendência e payload divergente; alias com FK cruzada negada; lote 2 inbound + 2 status distribuído em 2 lojas; status diferentes com mesmo message ID; rollback integral; tentativa de escolher loja via payload; privilégios.
- `scripts/test_s0_wa_030_concurrency.sh`: **duas conexões PostgreSQL simultâneas** inserindo variantes 8 e 9; 1 lead/ciclo com 2 mensagens; disputa de lease com `FOR UPDATE SKIP LOCKED` e recuperação de lease expirado por relógio simulado.
- Regressões anteriores, 24 testes Python e os testes WA 028/029 continuam no runner protegido `scripts/run-s0-local.sh`.
- **Registrar somente evidência confirmada pelo CI, e não como aprovação Meta/GoTrue/PostgREST.** O teste Auth/REST gerenciado para migração 030 continua separado e não é automaticamente acionado.

## Riscos pendentes (NO-GO para implantação/integração real)

- Não existe serviço interno autenticado de aceite, registry Meta verificado, isolamento de segredos por App nem mapeamento com vigência histórica.
- O `payload_fixture_s0` é só marcador em tabela sintética; não é conteúdo Meta protegido, não possui prova de retenção ou recovery, e **não satisfaz** `commit_state='COMMITTED'` da guarda WA-01B. A função 030 deliberadamente retorna `FIXTURE_BATCH_STORED`.
- Inbox 029 pode gravar evento sem payload e não deve receber ACK real, mesmo após 030. Não existe worker de aplicação C02/C07, replay manual seguro, DLQ funcional nem tratamento real de saída incerta.
- C01 antigo ainda não passa pelo resolvedor 8↔9; a flag `p_mobile_confirmado` é ficção de teste e não deve jamais vir do payload Meta como prova de pessoa. Resolver rotação, números reciclados, múltiplas pessoas e observação de aliases antes do uso real.
- HMAC interno da S0/027 e HMAC Meta são protocolos e segredos diferentes; as wrappers comerciais `SECURITY DEFINER postgres` ainda dependem de revisão de menor privilégio.
- DEC-WA-04 e DEC-WA-06 continuam pendentes; DEC-WA-05 aprova propriedade por loja, **não** alteração em ativos da concessionária de demonstração/terceiros, nem onboarding ou envio.
- A migração 030 não altera `public.canais_loja` nem cria vínculo operacional WABA/Meta. Todas as referências `FIXTURE_*` são estritamente laboratoriais.

## Retorno necessário à frente WhatsApp/Meta (PR #2)

1. Confirmar os campos mínimos do envelope por item e a política de POST agregado em múltiplos Apps/canais assinados independentemente; não converter a função de fixture em RPC pública.
2. Explicitar fonte da autenticação do App para seleção da chave HMAC e o momento de associação app→WABA→emissor→loja, com histórico de vigência e tratamento de App revogado.
3. Homologar idempotência de callbacks sem ID único de evento; estabelecer fingerprint canônico que não crie falso conflito quando a Meta variar representação numérica de um remetente.
4. A política de recibo WA-01B só pode vir de transação interna real **com conteúdo recuperável** e decisão final de quarentena aprovada em DEC-WA-06. Não emitir HTTP 200 pelo protótipo 030.
5. Atualizar materiais normativos que ainda digam que App/WABA/número pertence à gestora; preservar a exclusividade de cada emissor e o isolamento do cliente por loja.

**Gate:** GO para engenharia local sintética e revisão cruzada; NO-GO para PR merge, Supabase hospedado, Meta real, credenciais comerciais, produção, contratação ou integração API pública.
