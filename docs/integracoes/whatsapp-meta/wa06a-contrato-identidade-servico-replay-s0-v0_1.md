# WA-06A — contrato candidato de autenticação interna, privilégio mínimo e antirreplay Meta → S0

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Data:** 18/10/2026. **Estado:** [P] proposta de interface para revisão cruzada; **não** equivale a DEC-WA-06 aprovada, DDL, API operacional ou homologação. **Base lida:** WA-05C, WA-05D, WA-05D-AUD1 do PR #2; interface compartilhada Meta/S0; S0-033, S0-037D e S0-037F do PR #1. Preservam-se DEC-WA-01/02/03/05, D-ORG-01 e Supabase diretamente no caminho crítico sem n8n inicial.

## 1. Por que este incremento não é outro simulador

WA-05D-AUD1 reproduziu alteração de envelope com recalculo de SHA-256 e corrigiu-a **somente na fixture** por MAC interna com serviço e prazo. A atual prova `FakeInternalServiceProof` assina `JSON.stringify([service_ref,issued,expires,candidate])`; seu prazo máximo é de cinco minutos, mas **não há nonce, `purpose`, `audience`, `key_id`, emissor real ou ledger durável de replay**. `trustedCaller()` e `trustedInternalSigningKey()` são entradas substituíveis do teste. A S0-037F prova padrão NOLOGIN/NOBYPASSRLS com sessão/vínculos **mock**, não identidade Meta operacional. Portanto, acrescentar outro `Map` de simulação não fecharia o gate.

**Entrega WA-06A:** especificar um contrato de fronteira implementável, a matriz de privilégios e os testes de aceite a serem executados na futura implementação S0, **sem escolher prematuramente** o mecanismo de identidade ou o projeto Supabase definitivo.

## 2. Separar cinco provas, sem inferências cruzadas [P]

1. **Origem Meta externa:** POST validado em bytes originais com App Secret específico do App escolhido por rota confiável; seleção e vigência App/WABA/emissor por concessionária. HMAC Meta não autentica chamadas internas S0.
2. **Identidade de workload interna:** gateway S0 obtém o principal autenticado **da camada de transporte/identidade confiável**, nunca de `service_ref` ou `concessionaria_id` presentes no JSON; valida issuer, audience, expiração, revogação e vinculação ao workload. Mecanismo (identidade curta de serviço, mTLS, token de workload com emissor confiável, etc.) **pendente [R/DEC-WA-06]**. Proibido aceitar uma simples declaração `trustedCaller()` como identidade real.
3. **Integridade/finalidade do comando:** prova vinculada ao principal, lote completo, `purpose=meta_s0.ingest`, audiência S0, versão de contrato, rota, revisão, referência do payload, SHA-256 dos bytes e todas as ocorrências. MAC de defesa em profundidade, se adotada, usa chave de serviço segregada de App Secret Meta, verify token GET, token Graph e prova do gateway comercial C07/C08. Não aceitar SHA-256 público como autenticação.
4. **Autorização S0 vigente:** registro interno independente associa principal ativo → permissões `ingest` → rota/App/revisão → **cada** WABA/emissor/canal/concessionária; conjunto permitido é a interseção dessas autorizações, não o que o envelope declara. A concessionária é titular dos recursos Meta; a Prumo é a operadora. Nunca transformar isso em vínculo empregatício da concessionária (D-ORG-01).
5. **Commit e recibo:** assinatura válida e autorização não provam armazenamento. Só S0, após transação durável de payload protegido + batch + ocorrências + tarefas e evidência verificável de commit, poderá responder com recibo autoritativo. Até DEC-WA-06 e homologação, **`ack_allowed=false` em todo código atual**.

## 3. Envelope de solicitação interna v1 — somente proposta [P]

Campos adicionais sobre o `S0HandoffCandidate` atual, não API já publicada:

| Campo | Origem/validação exigida | Observação |
| --- | --- | --- |
| `contract_version`, `proof_version`, `canonicalization_version` | Lista explícita de versões aceitas | Rejeitar versão desconhecida, downgrade ou ambiguidade de serialização |
| `purpose=meta_s0.ingest`, `audience=s0_internal_ingress` | Política de serviço S0 | Não serve para C03/C06/C12 nem C07/C08 comercial |
| `request_ref`, `nonce_ref`, `issued_at`, `expires_at` | Gerados pelo emissor **autenticado**, cobertos pela prova | Únicos por principal/época; não confiar apenas no prazo |
| `service_ref`, `key_epoch` | Identidade confiável + registro S0, conferidos com prova | Claims do corpo não podem criar/elevar identidade; rotação revogável |
| `batch_ref`, `route_ref`, `route_revision`, `app_ref` | Candidato WA-05C, validado de novo em S0 | Um POST pode conter vários canais da **mesma App**, nunca Apps diferentes |
| `protected_payload_ref`, `payload_sha256`, `scope_sha256`, `occurrences[]` | Integridade da captura e recálculo S0 | Escopo integral inclui `event_kind`, `provider_kind`, timestamp e posição |
| `attestation` | Assinatura/verificação de material restrito ao serviço | Algoritmo canônico e assinatura de produção **não definidos** |

**Compatibilidade:** o literal atual `meta-s0-handoff.v0.1-proposed` e a MAC `JSON.stringify` da fixture não são formato definitivo de wire protocol. Antes de RPC/DDL real, publicar vetor canônico versionado (bytes exatos, Unicode, ordenação, números, nomes e inclusão de campos), vetores positivos/negativos entre runtimes e política de rotação. Não reutilizar o helper `createFakeS0ServiceProof` como assinador de payload arbitrário.

## 4. Matriz mínima de privilégios [P]

| Ator | Pode | Não pode |
| --- | --- | --- |
| Endpoint Meta público | Verificar GET; autenticar POST HMAC por App; encaminhar pela identidade interna autorizada | Usar `service_role` genérico para DML comercial, ler todos os segredos ou conceder tenant |
| Workload de ingresso autenticado | Chamar **somente** `meta_s0.ingest` e consulta restrita de recuperação do próprio `request_ref` | SELECT/DML comercial amplo, criar concessões, chamar comandos C07/C08, emitir Graph |
| Verificador/porta S0 restrita | Validar serviço/prova/ACL/nonce, bloquear versão e vínculo, gravar lote/ocorrências/tarefas em transação | Assumir conteúdo do envelope como autorização, ler App Secret Meta/Graph token, dar ACK HTTP em nome da política não aprovada |
| Worker técnico S0 | Claim por lease/fencing com escopo, processar C02/C07 autorizado | Reusar identidade de ingresso para C03/C06/C12, resolver conflito 8↔9 por presunção |
| Adaptador de saída Meta | Despachar **apenas** intenção C03/C06/C12 revalidada pelo núcleo e credencial do App certo | Interpretar Graph 200 como entrega, retry cego de `UNCERTAIN_EXTERNAL`, usar credenciais de outra concessionária |

Nenhum papel/GRANT/RLS concreto foi aprovado. Candidatos exigem owner sem login, sem BYPASSRLS e grants estritos, mas precisam de prova em PostgreSQL/Supabase local gerenciado com revogação concorrente. A S0-037F não pode ser promovida automaticamente a gateway Meta.

## 5. Antirreplay e commit [P, dependente da S0]

- **Antes do commit:** autenticar principal e prova, validar janela temporal, conferir ACL e todas as posições `entry/change/messages|statuses/item`; `nonce_ref` por principal+época deve ser registrado sob unicidade protegida **na mesma transação** de payload, batch, cada `occurrence_ref` gerada pela S0 e tarefas. Vincular ao fingerprint completo; `request_ref` colidente e conteúdo diferente é conflito fechado.
- **Replay fiel após commit:** consultar fonte durável autenticada por `request_ref`/escopo/fingerprint e retornar apenas o **mesmo resultado autoritativo**, sem recriar trabalho. Nova tentativa assinada para o **mesmo POST** pode usar novo nonce, mas a idempotência do batch/payload impede efeito interno duplo.
- **Replay antes ou durante o commit:** transação concorrente, nonce repetido com payload diferente, autorização revogada ou lease incerto não pode produzir aceite falso; usar conflito/erro transitório auditável, sem dar acesso a detalhes entre concessionárias.
- **`COMMIT_UNKNOWN`:** consulta restrita a recibo durável; enquanto indeterminado, não converter incerteza em HTTP 200. Política final de 200/4xx/503/quarentena/reentrega é **DEC-WA-06 [R]**; evitar tormenta de retry.
- **Revogação/rotação:** verificar vigência do serviço, chave/época e vínculo de App/rota/canal sob trava ou controle serializável **dentro da mesma transação da gravação**. Uma verificação JS final, fora da transação, não é suficiente. Definir grace period e aceitação apenas para consulta histórica na revisão de segurança.
- **Ocorrências:** `statuses[].id` é ID da mensagem referenciada, **não** um ID universal de callback. Criar `occurrence_ref` próprio para cada item; não colapsar status legítimos repetidos pelo `wamid/status/timestamp`.
- **Persistência do corpo:** avaliar como primeira opção guardar bytes protegidos em tabela privada transacional no PostgreSQL, para evitar afirmar atomicidade de SQL com um objeto externo. Criptografia, acesso a chave, quotas do Free, backup/restore, retenção e descarte seguem DEC-WA-06; **nenhum modelo físico foi aprovado**. Se storage externo for escolhido, exigir protocolo explícito de staged/confirmed/recovery, sem alegar transação distribuída que não existe.

## 6. Contratos de C02/C07 e saída preservados

Após **aceite durável**, a S0 aplica C02 com resolvedor central e evidência de telefone 8↔9, ou C07 como ocorrência técnica de callback preservada e reconciliável. Ingresso não altera os **oito estados comerciais** por inferência. C03 (IA), C06 (template/recontato) e C12 (humano) partem de **autorização comercial atual, distinta**, antes de reservar/despachar na outbox; uma prova válida de ingresso Meta nunca concede saída.

## 7. Testes executáveis exigidos para próximo gate, ainda não executados

| Gate proposto | Negativa/positiva necessária |
| --- | --- |
| SVC-01 | Principal autenticado de fora do body; `service_ref` forjado ou token de audiência errada negado |
| SVC-02 | Serviço ativo de App/loja A sem acesso a rota ou canal B, inclusive lote A+B |
| SVC-03 | `purpose`, `audience`, `canonicalization_version` e campos extras alterados não passam |
| SVC-04 | MAC inválida, chave errada, assinatura sobre corpo anterior, timestamps fora de janela negados |
| SVC-05 | Nonce concorrente igual: só um commit; nonce igual com fingerprint diferente: conflito |
| SVC-06 | Revogação de serviço/chave/rota/loja **concorrente** à gravação impede novo commit |
| SVC-07 | Falha após persistir payload mas antes da tarefa reverte payload, batch, nonce e ocorrências |
| SVC-08 | `COMMIT_UNKNOWN` resolve em consulta autenticada; recibo sem fonte S0 não gera ACK |
| SVC-09 | POST com dois canais da mesma App e vários status, preservando todas as posições e callbacks iguais |
| SVC-10 | Reentrega íntegra não produz segundo efeito C02/C07; falha Graph incerta não implica retry |
| SVC-11 | Papéis anon/authenticated/worker cruzado e `service_role` genérico sem poder de escrita comercial |
| SVC-12 | Logs, erros e auditoria não vazam payload, telefone, token, chave ou identidade de cliente |

**Aceite do incremento WA-06A:** documento proposto versionado, leitura de retorno e revisão solicitada à S0. **Não alegar SVC-01..12 PASS:** só se tornarão testes reais após interface e implementação controlada. O histórico WA-05D-AUD1 permanece em **358/358 testes locais de laboratório**; este documento não aumenta esse número.

## 8. Dependências e sequência objetiva [R]

**S0 (PR #1):** responder ao contrato de identidade do workload, ACL/owner mínimo, atomicidade payload+nonce+inbox+tarefa, revalidação de vínculos, recibo por `request_ref` e recuperação de commit incerto. Compatibilizar com S0-029/033/034B e 037D/F **sem** tratar fixtures como produção nem modificar migrations históricas.

**Meta (PR #2):** após revisão cruzada, publicar serialização canônica e interface tipada para emissor autenticado, mantendo o adaptador da Graph separado; preparar testes de contrato que possam rodar em Postgres/Supabase **local**, não outra família de simuladores `Map`.

**Responsável:** DEC-WA-04 (Supabase definitivo), DEC-WA-06 (mecanismo de identidade, segredos, retenção, backup, ACK/continuidade), verificação externa do token definitivo e autorização de homologação real seguem abertos. Nada de alterações na POC `whatsapp-webhook-sandbox` do projeto `projeto-supabase-omitido`, numbers, banco hospedado, Graph API, merge, deploy ou recurso pago sem autorização específica. PRs continuam **Draft**.
