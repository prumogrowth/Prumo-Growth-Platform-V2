# S0 → F02 — registro autenticado de pedidos de revisão, 0.1-candidate

26/10/2026, America/Sao_Paulo. **Contrato candidato não ratificado; implementação somente em PG17/GoTrue descartáveis.** Base S0 PR #16 `b298252c26c69f668b3c3fdb86e9252faff9e44b`; código CFI certificado anterior preservado. Fonte F02 PR #1 `a7ba0136ae7c7907cc5b7f9ad0ee6b6ae499125e`, CI própria [40362538933](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40362538933) SUCCESS. Não modifica a branch da F02, não incorpora seus 15 adaptadores S0/F03 nem suas fixtures de ficha/C04/C08.

## Fronteira de autoridade e avanço concreto

A F02 prepara uma **solicitação não autenticada** com `prepare_handoff`. O SHA-256 identifica o conteúdo alegado, sem autenticar testemunhas, consentimento, pessoa ou autorização. Seus módulos lifecycle/preflight/recovery continuam úteis como verificações formais. Timeline, revogações e relógio recebidos da F02 nunca são fonte da S0.

A S0 agora pode **registrar, consultar e retirar um pedido de revisão**, duravelmente e na mesma transação do recheck CFI-01. O principal GoTrue e a sessão/S1/grant/atribuição são verificados pelos mecanismos existentes. Loja, caso, encerramento e recibo CFI completo são conferidos; lead e canal são comparados ao caso/conversa físicos sob os locks já adquiridos pelo CFI. O resultado permanece PENDING_EVIDENCE: **não atesta F03 completo, C08, ledger de origem, intenção humana, política/template nem disposição Meta**. Esses campos são armazenados como alegações tipadas.

Registrar um pedido de revisão não é ratificar seu conteúdo. Retirar o próprio pedido técnico não cancela plano, tentativa ou mensagem externa. Nenhum método de aprovação, agendamento, dispatch, aplicação de ficha ou conclusão comercial é implementado.

## Operação interna, sem endpoint público

`S0F02ReviewRegistryLocal` recebe o **objeto CFI real já configurado**, sem DSN privilegiado/identidade substituta. Entrada de `execute`:

| Campo | Origem e regra |
|---|---|
| `authorization` | Bearer humano verificado pelo GoTrue existente; fora do envelope F02 |
| `operation` | `record`, `read` ou `withdraw`; nenhuma operação comercial |
| `binding` | `S0F03BoundReceiptLocal` mantido no servidor, nunca desserializado do browser/F02 |
| `evidence`, `proposal` | Dataclasses originais F02; `prepare_handoff` reaproveitado sem alteração; alegações continuam não verificadas |
| `window` | `ReviewWindow` com datas UTC conscientes de fuso; prazo voluntário máximo deste pedido, nunca duração de uma autorização |
| `expected_revision` | Inteiro técnico CAS; obrigatório na retirada; read pode recuperar revisão mais recente, mas recusa cursor maior que o servidor |

O binding CFI existente é ligado a ator/sessão/caso/ciclo/atribuição. A interface **não permite** ao gestor usar o recibo de outro operador, trocar sessão após novo login ou transformar versão de caso em ciclo. Continuidade entre sessões e revisão independente de gestor dependem de contrato aprovado. Não se escolhe uma permissão nova para viabilizar esses casos.

A consulta ainda exige esse binding mantido no servidor. O teste de retomada cria outro objeto broker, conservando o binding fora dele; não simula perda completa de processo, HA/failover ou recuperação de binding perdido. O lookup durável para reconstruí-lo continua dependente de UI D3. O ledger de pedidos resolve a perda da timeline alegada, não toda a integração de recuperação.

O documento interno `prumo.s0.f02.review.request/0.1-candidate` contém `schema`, `request_sha256`, `evidence`, `proposal`, `requested_at`, `expires_at`. Apenas o backend constrói JSON canônico dessas dataclasses. Não é uma nova API JSON pública. Contexto de sessão, papel e segredos não são aceitos dentro dele.

Há três hashes de domínios diferentes: snapshot CFI; SHA F02 não assinado da proposta/evidência; SHA S0 do documento integral, que inclui a janela. **O hash F02 não inclui a janela**, por isso sozinho não pode identificar um replay temporal. O HMAC interno S0 inclui o SHA do documento integral, operação, ator/sessão, caso/ciclo/encerramento, chave da captura, versão de chave técnica, instante/nonce e CAS. Seu domínio `s0-f02-review-local-v1` é distinto do HMAC CFI, Meta e de qualquer assinatura F02 alegada.

## Saída S0 → F02

`ReviewResult.projection()` usa `prumo.s0.f02.review.result/0.1-candidate`, com estado, `review_ref` UUID criado no banco, revisão como decimal string, horário observado pelo servidor, hash F02 e prazo original. Referência e cursor são correlação, **não bearer**. O transporte definitivo continua pendente; esta versão é um resultado interno autenticado, não recibo público assinado.

Todas as saídas, inclusive negativas, têm:

- `evidence_scope = CFI_CONTEXT_ONLY_F02_EVIDENCE_PENDING`;
- `human_ratification = NOT_IMPLEMENTED_CONTRACT_PENDING`;
- `send_authorized = false`, `scheduling_authorized = false`, `commercial_transition_authorized = false`.

| Estado | Significado |
|---|---|
| `RECORDED_REVIEW_ONLY` | Um pedido com alegações foi registrado sob contexto CFI/S0 verificado; provas F02 continuam pendentes |
| `REPLAY_REVIEW_ONLY` | Mesma chave, escopo e documento integral; mesmo registro e mesmo prazo, nova checagem viva |
| `CURRENT_REVIEW_ONLY` | Estado corrente recuperado do servidor; não depende da timeline apresentada pela F02 |
| `WITHDRAWN_REVIEW_ONLY` | Pedido retirado; tombstone persistente, sem reabertura por replay ou omissão do cliente |
| `EXPIRED_REVIEW_ONLY` | Prazo do pedido atingido e estado terminal persistido; não constitui falha comercial |
| `INPUT_REJECTED` | Tipos, comando, janela, vínculo ou CAS inválidos |
| `DENIED` / `STALE` | Identidade, sessão, privilégio, vínculo ou fonte CFI recusados/alterados; nenhuma nova alteração aceita |
| `IDEMPOTENCY_CONFLICT` | Mesma chave do ator/loja com outro documento, encerramento ou janela; não sobrescreve original |
| `REQUEST_EXPIRED` | Primeiro registro solicitado depois do prazo; nada registrado |
| `REVIEW_REQUEST_NOT_FOUND` | Consulta/retirada sem registro na chave e escopo autenticados |
| `CLOCK_RECHECK_REQUIRED` | Relógio do servidor anterior ao último horário persistido; não reabre estado nem inventa monotonicidade física |
| `UNAVAILABLE` | Falha/resultado ou commit indeterminado; não afirma rollback. Recuperar pela mesma chave com prova nova, sem criar novo envio |

## Persistência, concorrência, relógio e segurança

A fixture `supabase/tests/s0_f02_review_registry_local_only.sql` exige opt-in e PG17/postgres descartável. Não é migration de implantação. Reaproveita tabelas/chaves/nonces/auditoria CFI, GoTrue e S1 existentes. Dois novos objetos privados: pedido com conteúdo/escopo imutáveis e audit append-only ligado ao nonce CFI. Estado, revisão e último horário só avançam de forma monotônica; WITHDRAWN/EXPIRED não voltam a PENDING_EVIDENCE. Não há armazenamento de JWT, senha, MAC, texto da conversa ou dados reais.

A unicidade técnica implementada é **(loja, ator, chave do pedido)**. Chave nova pode representar outro pedido de revisão sem autoridade; isso **não** aprova cardinalidade por encerramento, plano substituto ou nova tentativa comercial. A exclusividade por encerramento adotada pela timeline sintética F02 não é promovida silenciosamente a regra S0; permanece decisão de protocolo. Não se declara toda a F02-A10 resolvida.

O prazo informado é um **limite voluntário imutável do próprio pedido**, conferido por `clock_timestamp()` depois de adquirir os locks. Não se adotam 48h de lifecycle, 24h–7d de contato, prazo produtivo de retenção ou validade de ratificação. Política máxima/default e eventual prazo firmado pelo servidor precisam aprovação. Expiração observada é persistida e não some com reinício ou clock retrocedido; relógio regressivo impede aceitação. Nenhuma garantia NTP/cluster é declarada.

Cada operação verifica duas provas de domínio diferente e usa um nonce: a prova CFI existente e o MAC do documento/operação de revisão. Ambos usam o material de chave S0 já existente no laboratório, com domínios separados: não são duas credenciais independentes nem prova de custódia produtiva. A mesma transação verifica fonte CFI, consome nonce, grava auditoria CFI e pedido/auditoria F02. A comparação completa do recibo esperado e a validação da resposta ocorrem **antes do COMMIT**, preservando o reparo do PR #13. Erro tardio desfaz todos esses efeitos. Nenhum retry automático repete I/O comercial.

Novo definer NOLOGIN/NOSUPERUSER/NOBYPASSRLS tem somente colunas necessárias, acesso de leitura/lock à chave e DML no ledger privado. O login de aplicação não assume esse papel e não recebe SELECT nas tabelas. Os grants do owner CFI anterior não são ampliados: ele continua sem `casos_humanos.lead_id`. A única ampliação deliberada da ACL da função CFI é EXECUTE para o novo owner NOLOGIN, concedida com membership temporária de instalação e imediatamente revogada do instalador. Definição, protocolo e comportamento CFI permanecem intactos. Nada é concedido a anon/authenticated/service_role para chamar a porta nova.

Ordem preservada: chave CFI → recheck CFI (sessão → equipe → recursos/grants/conversas/mensagens/recibo) → ledger de revisão. Nenhum caminho novo toma ledger e depois volta ao CFI. O JOIN de locks CFI preexistente não é promovido a uma prova de ordem global. C1–C7 Meta continuam candidatos; não introduzimos locks em outbox/eventos Meta nem reutilizamos autenticação humana como M2M.

## Reutilização e decisões a encaminhar

| Necessidade F02 | Aproveitamento / entrega S0 | Pendência |
|---|---|---|
| F02-A02/A14: escopo e corte | CFI real, hash/watermark/contagem, mesma transação; lead/canal físicos | Recibo F03 completo, minimização, versões independentes, proveniência das quatro provas F02 |
| A03/A17: humano/S1 | GoTrue vivo, sessão SQL sob lock, equipe/grant/atribuição existentes | Quem ratifica, leitura do gestor sobre recibo alheio, independência, revogação/validade do ato e interface UI D1–D4 |
| A09: tempo | Prazo voluntário imutável e relógio DB; estado terminal | TTL produtivo/max/default, retenção e disponibilidade/clock de infraestrutura |
| A10: idempotência | Chave/ator/loja, conflito de documento/janela, duas conexões e recuperação | Exclusividade por encerramento, geração de novo pedido e dedupe operacional dependem de aprovação |
| A11/A20: revogação/continuidade | Estado no servidor, retirada CAS, tombstones, gates vivos, clock regressivo | API de histórico paginado/cutoff assinado, completude entre sistemas e revogadores além do contexto CFI |
| A04/A05/A07: C04/C08 | Preserva bloqueios; provas recebidas como alegações | Validar ledger/testemunha da frente após mapeamento aprovado; cancelamento local não prova cancelamento Meta |
| A12/A13/A18: consentimento/template/envio | Nenhum resultado libera execução | Fonte real de opt-out/template/Meta, C1–C6, política pós-humana e executor autorizado |
| A16: F01/F03/F02 | Correlação do encerramento físico já existente | Ordem dos eventos/handoff e cenário integrado entre frentes ainda não certificados |

**Próximo encaminhamento F02:** consumir a projeção candidata somente como status do pedido; conservar evidência e proposta originais para apresentação humana; não converter RECORDED/CURRENT/REPLAY em aprovação. Ao retomar, consultar a S0 novamente: timeline omitida nunca remove retirada/expiração persistidas. Em falha de resposta, repetir a mesma chave/documento ou consultar; mudança de janela exige decisão explícita, não extensão de replay.

**Coordenação S0/F02/F03/S1:** aprovar mapeamento das quatro provas e das versões, permissão do ratificador distinto do capturador e continuidade entre sessões. S0/Frontend decide transporte, lookup e D1–D4. S0/Meta/S1 decide C1/C3/C5 e disposição de tentativas incertas; Produto/Privacidade define prazos, minimização e retenção. Nenhuma aprovação comercial foi inferida do código ou da matriz de testes.

## C04/C08 e Meta

`CANCELADA` local, testemunho HMAC local ou reconciliação review-only não demonstram que bytes deixaram de chegar ao provedor. Tentativa previamente reservada permanece de disposição externa desconhecida; jamais ganha novo slot de envio por cancelar localmente. API_ACCEPTED/2xx não prova delivered; observação/revisão tardia não cria novo begin. Esse princípio é consistente com DISPATCH-01/02 e ACK/LOCK candidatos do PR #14. O registro S0 desta entrega não consulta Meta e não ratifica tais contratos.

## Fontes lidas e reprodução

**CI [40414847271](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40414847271), job `121894443928`: SUCCESS no SHA executável `4a3d248d46fad5c195398324b3ee98ae6236365f`.** Logs conferidos: 264 unitários (173 S0 + 83 F02 originais + 8 novos); 18 famílias Auth/REST; dez cenários CFI originais; 56 cenários reais GoTrue/PG17 (32 CFI + 24 F02); 19 de histórico S0 e 19 com S1/I63; 22 fontes S1 fixadas conferidas. Nenhum cenário real ignorado; cleanup confirmado. A execução inicial `40414076278` em `3cd7a392` também passou integralmente. O commit final acrescenta somente asserções físicas da ACL da porta e da revogação de CREATE, sem alterar implementação. Os totais não são jornadas comerciais E2E nem recertificação dos 330 físicos F03 históricos.

Contratos F02 no SHA fixado: `docs/OAI_E04_S0_CODEX_ENTREGA_F02_CONTRATOS_2026_10_26.md`, manifesto `OAI_E04_F02_S0_CODEX_HANDOFF_V1.json`, `OAI_E04_F02_RECONCILED_HUMAN_HANDOFF_V1.md`, `OAI_E04_F02_REVIEW_LIFECYCLE_V1.md`, `OAI_E04_F02_BOUND_REVIEW_PREFLIGHT_V1.md`, `OAI_E04_F02_REVIEW_RECOVERY_V1.md` e matriz `OAI_E04_F02_ACCEPTANCE_MATRIX_V1.json`. O MD de consolidação ainda descreve o corte anterior com 18 critérios; o JSON atual contém A01–A20. O manifesto de coordenação marcado `631d8eca` também é histórico: a seleção de código usa a árvore real `a7ba0136`, não esses inventários antigos. Também consultados os adaptadores de conciliação e recibos existentes, PRs #12/#13/#14 e fechamento #16. Não se usa o total histórico de 330 físicos F03 como certificação desta composição.

Três módulos puros F02 e suas quatro suítes originais foram copiados **sem alterar bytes**, com hashes em `integration/f02/f02_source_manifest.json`; 83 testes preservados. Não foi importado o restante da branch nem repetido desenvolvimento de F03/C04/C08/Meta. A CI própria executa os 173 testes S0 anteriores, os 83 puros F02, os oito de compatibilidade novos, Auth/REST/CFI originais, histórico em dois perfis e 32 CFI + 24 novos cenários reais F02. Resultados verificáveis, limites e falhas ficam em `EVIDENCIAS.json` após conferência dos logs.

Usar somente o workflow experimental `exp-s0-f02-revisao.yml`, stack local sem vínculo remoto, CLI 2.84.2 e driver fixado. Após as fixtures CFI/histórico, `PRUMO_F02_DISPOSABLE_TEST=YES PRUMO_CFI01_TRANSACTIONAL_TEST=YES PYTHONPATH=. python3 integration/f02/test_authoritative_review.py`; stop/cleanup obrigatório também em falha. Nenhum endpoint, merge, deploy, hosted Supabase, OpenAI/Meta reais, agendamento ou conclusão de venda foi ativado.
