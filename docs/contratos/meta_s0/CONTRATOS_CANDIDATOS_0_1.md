# Meta/S0 — quatro contratos candidatos 0.1

26/10/2026. **NÃO RATIFICADOS. LABORATÓRIO ISOLADO. SEM INTEGRAÇÃO FINAL.**

Branch auxiliar exclusiva: **aux/meta-s0-contracts-20261026**, baseada no PR #8 em **cb7fc3e2eacdaad9b8d47ffca1284759ca3357a3**. Só acrescenta arquivos em integration/meta_s0_candidate/, neste diretório documental e um workflow auxiliar. Não modifica código Meta importado, backend S0, S1, Frontend, migrations, IAM ou caminhos de deploy.

O ambiente cloud ficou indisponível durante a inspeção. Arquivos e commits são preparados pelo conector GitHub; a execução será verificada pelo CI da branch, sem afirmar execução local. Os protótipos não chamam Graph, Supabase, GoTrue ou qualquer serviço externo. Não há endpoint HTTP nem credencial produtiva. A existência de código não ratifica regra comercial.

## Checkpoints recuperados e precedência

| Fonte | HEAD consultado | Código certificado anterior | CI histórico confirmado por GET |
|---|---|---|---|
| PR #7, composição S0/Meta | 450dcd645f35d4c8bf93e974e75d3b09467965a7 | dbcca8b8583e4d31640f765232fb6708260ea36b | 40311987315, success |
| PR #8, Meta Cloud | cb7fc3e2eacdaad9b8d47ffca1284759ca3357a3 | mesmo SHA | 40356607954, success |
| PR #9, S0 restrito | ff623482fca0eb1857a64b51959e3716bc0216d7 | 1b4f2841d513fb971c93379636414bf686784beb | 40323084692, success |
| PR #11, UI/S0 | ddec1b80444bfde871d43a02d0ee94b9ed7cde11 | 99238f8a3304b8cc70ef14421b74842b0740b016 | 40358081309, success |

Todos estavam Draft, abertos e sem merge na leitura. As timelines retornaram vazias pelo conector; checkpoints vieram dos corpos dos PRs, documentos nos SHAs e metadata de Actions. Não se afirma recuperar discussão ausente. Os números históricos de testes pertencem àquelas entregas; não são novas execuções desta tarefa.

Fontes: documentos de decisão do PR #7 e contratos Cloud do PR #8; relatório/backend atômico e ponte S0/S1 do PR #9; contrato UI do PR #11. O manifesto fixa paths e blobs dos sete componentes Meta reaproveitados. CFI valida resultado antes do commit e mantém equipe antes de caso/atribuição; aproveitamos esses princípios, sem copiar autenticação humana.

**Fronteiras:** a recomendação GoTrue de D4 no PR #11 vale para UI humana. Não autentica ingresso Meta nem worker. Case version, cycle version, intent revision, catalog revision e binding revision são domínios distintos; nenhuma conversão é feita. Status delivered não vira inbound, venda, fechamento, recibo CFI, F03, falha definitiva de cadência ou permissão.

## Modelo comum e responsabilidade

S0 é titular de intenção, destinatário validado, escopo, finalidade e elegibilidade. Meta fornece observações técnicas e um futuro transporte. S1 continua titular de direitos, equipe e concessões. O worker não pode fornecer booleans de autoridade ou selecionar tenant pelo telefone.

Identidades distintas: principal humano; principal de dispatch; ingressor M2M; conciliador técnico. O perfil de laboratório distingue operações por ACL de chave, tenant, canal, rota e revisão. O registro de chave vincula issuer e audience; não aceita JWT, actor_id, sessão GoTrue ou afirmações de papel do corpo. A autoridade de enviar continua pendente mesmo com HMAC válido.

Cada transação candidata deve: descobrir candidatos sem conceder autoridade; adquirir locks na ordem ratificada; reler registro/revisões/chave/direitos vivos; verificar prova; consumir nonce; executar CAS/inserções; validar resultado completo; persistir auditoria e recibo; confirmar commit durável; só então responder. Nonce, chave lógica, correlatores, digest bruto, observação candidata e wamid têm finalidades diferentes.

| Identificador | Escopo e regra candidata |
|---|---|
| request_id / correlation_id | Comunicação e correlação, sem autoridade; podem mudar entre repetições |
| nonce | Uma prova M2M, único por issuer/chave; consumo junto com efeito e auditoria |
| idempotency_key | Intento lógico de reserva por tenant/canal; mesmo intento preserva chave |
| attempt_ref | Gerado no backend, vinculado à intenção e snapshot; não é bearer |
| observation_ref / decision_ref | Idempotência de evidência/revisão; divergência não substitui histórico |
| batch_ref | Chave do lote por tenant/canal/rota/revisão; mesmo ID e digest diferente é conflito |
| raw_sha256 | Bytes exatos Meta; identifica variante física, não conteúdo comercial |
| candidate_key / wamid | Chave sintética de observação / ID de mensagem; não callback ID ou autorização |

### Envelope executável de laboratório

Versão literal prumo.meta-s0.lab/0.1-candidate. Objeto com chaves exatas:
version, operation, request_id, correlation_id, nonce, issued_at_ms, expires_at_ms, body.
IDs: ASCII [A-Za-z0-9_.:-], 1–128 caracteres. Revisões: decimal string positiva canônica até int64, sem coerção. O binding legado do parser Meta ainda exige Number seguro; valores fora dele falham fechados, não são arredondados para concessão.

Prova separada: {kind:"LAB_M2M_HMAC", key_id, mac_sha256}. Material autenticado:
JSON.stringify(["PRUMO_META_S0_CANDIDATE_LAB_ONLY", key_id, SHA256(bytes_do_envelope)]), HMAC-SHA256 com chave sintética de 32 bytes e comparação constante. TTL até 30 s, sem tolerância de relógio neste perfil; validade da chave, ACL, rota e revisão são rechecadas dentro da transação modelada. Sem compatibilidade com WA34, wire SQL WA44, assinatura externa Meta ou HMAC humano CFI.

O envelope interno aceita somente bytes que fazem roundtrip exato por JSON.stringify: recusa duplicatas, aliases escapados, BOM, extras e UTF-8 inválido. É perfil estreito interno, **não substitui parser público Meta nem aprova WA68**. Limites de fixture: envelope 512 KiB; Meta raw 256 KiB/100 itens; resposta Graph 64 KiB pelo classificador existente. Limites operacionais, parser público e clock produtivo continuam pendentes.

Prova inválida/revogada não consome nonce. Recusas semânticas autenticadas podem consumir nonce e gerar auditoria, evitando reexecução da mesma prova. Erro de entrada que aborta callback desfaz estado/nonce/auditoria; falha genérica de persistência/resposta retorna COMMIT_OR_RESULT_UNKNOWN. Recuperação usa **nova prova/nonce** e a mesma identidade lógica. Nonce repetido nunca restitui execução ou ACK. Retenção/expurgo ainda não definidos.

Todos os resultados mantêm send_authorized, production_authorized, ack_allowed, retry_automatically, delivery_confirmed, case_transition_authorized e definitive_failure_count_increment falsos. lab_ack_ready é indicador exclusivamente de teste; nenhum servidor o converte em HTTP.

## META-S0-DISPATCH-01 — autorização e reserva transacional

**Objetivo:** uma única tentativa registrada, com elegibilidade revalidada pelo S0. Reserva e início são fases distintas para poder cancelar trabalho ainda não iniciado.

Entrada reserve: {intent_ref,idempotency_key,expected_revision}. Não contém tenant, telefone, texto, versão de ciclo ou ACL. S0 deve resolver o snapshot autoritativo: concessionária/canal/app/WABA/número/remetente/destinatário, conteúdo, finalidade, atribuição, direitos S0/S1, consentimento/opt-out, janela, template/catálogo e revisões pertinentes. As fontes comerciais definitivas de cada gate precisam de ratificação. As fixtures booleanas não simulam concessão produtiva.

Na mesma transação: revalidar escopo/snapshot; conferir chave lógica/fingerprint; exigir CAS; inserir tentativa server-owned, ocupação da intenção e idempotência; nonce e auditoria. Mesma chave com outro intento/snapshot retorna conflito. Outra chave não contorna intenção ocupada. Falta de fonte, versão, concessão ou decisão deve negar/bloquear, nunca adotar default permissivo.

Fingerprint candidato: intenção, revisão esperada, binding/revisão, destinatário opaco, finalidade, hash de conteúdo, revisões catálogo/template. Campos humanos/comerciais adicionais dependem de bindings aprovados. O perfil ocupa intenção indefinidamente: **não inventa regra de nova tentativa/cadência/expiração**.

Entrada begin: {attempt_ref,expected_revision}. Sob os mesmos fences/direitos vivos, CAS RESERVED → EXTERNAL_POSSIBLE uma única vez, com commit durável anterior a qualquer futuro I/O. Repetição retorna BEGIN_ALREADY_CONSUMED_NO_RETRY; re-reserva devolve referência sem execução. Não há lease reemitível após timeout.

**Limite técnico:** banco e Graph não compartilham transação. Commit de begin perdido, ou queda após begin e antes de saber se houve POST, torna efeito externo desconhecido. Não existe garantia exactly-once externa nesta proposta. O caminho futuro deve favorecer at-most-one begin e aceitar possível não envio; nunca despachar ao recuperar ocupação antiga. Autorização produtiva e eventual handle de uso único exigem desenho/custódia/transporte separado; o protótipo não produz esse handle.

Critérios: 20 reservas concorrentes → uma tentativa; dez begins → um vencedor; chave alterada/conflitante; escopo cruzado; todos os gates negativos; CAS; rollback; resultado perdido; cancelamento/revogação antes/depois de begin. Concorrências do modelo serial, não prova de constraints PostgreSQL reais.

## META-S0-DISPATCH-02 — observação, incerteza e reconciliação

Entrada observe: {attempt_ref,observation_ref,wire}. Transporte futuro deve autenticar identidade técnica e vincular observação à tentativa/correlação iniciada. wire é snapshot inerte transport_error, not_attempted, ou HTTP com status, headers e response_base64. Reutiliza **sem alterar** classifyCloudWireObservation e classifyGraphSendResult.

A tentativa possui correlation_ref gerado no servidor, independente de correlation_id de transporte. A evidência conserva esse vínculo; auditoria persiste digest do envelope, escopo técnico, referências solicitadas (identificadas como tal) e recibo efetivo.

A transação registra digest e campos sanitizados: estado técnico, wamid validado se houver, status HTTP e códigos numéricos. Não persiste body Graph, token, mensagem textual de erro ou segredo. Repetição exata não duplica evidência. Mesmo observation_ref com digest diferente mantém original, registra fingerprints do conflito e põe tentativa em quarentena; aceitação/rejeição incompatíveis ou wamids divergentes exigem revisão.

| Observação | Resultado candidato |
|---|---|
| 2xx com wamid válido | API_ACCEPTED_NOT_DELIVERED; não comprova entrega |
| 4xx explicitamente rejeitado, salvo exceções do classificador | PROVIDER_REJECTED_NO_RETRY; intenção continua ocupada |
| Timeout, 408/425/429/5xx, malformado, ausência de resposta ou queda após begin | EXTERNAL_UNCERTAIN; intenção continua ocupada |
| not_attempted depois de begin | Continua incerto: não prova ausência de efeito |
| Evidência tardia coerente | Acrescenta/refina leitura técnica; não abre begin/reserva |
| Conflito | QUARANTINED_REVIEW; sem novo envio |

Retry-After permanece dica, sem scheduler/reenvio. Ausência de registro não prova rollback ou recusa Graph. read é consulta técnica autenticada; não autoriza POST. Evidência tardia sob ACL técnica atual pode ser arquivada após cancelamento/opt-out/revogação **humana** S0/S1, conservando cancelamento e sem uso comercial; chave/registry técnico revogado bloqueiam. Esse particionamento é candidato a ratificação, não exceção já aprovada.

Entrada review, por ACL técnica distinta: {attempt_ref,decision_ref,evidence_refs}. Anexa decisão referenciada/idempotente; não altera evidência original, retira quarentena, desfaz cancelamento ou libera slot. Mesmo decision_ref divergente também põe em quarentena. Resolução comercial, contato humano, eventual novo intento e autoridade do conciliador precisam de decisão. Sem painel, lookup Graph ou integração operacional.

## META-S0-ACK-03 — M2M e lote durável

Entrada append_batch: {batch_ref,route_revision,raw_base64,meta_signature}. Duas provas independentes: assinatura externa Meta nos bytes exatos e prova M2M do ingressor no envelope interno. App Secret e rota vêm de configuração confiada do servidor; WABA/phone do corpo só confirmam essa rota. Não aceitar serviço como usuário GoTrue.

Reutiliza inspectCloudWebhookForHandoff e inbound.ts: snapshot antes de await, HMAC externo, lote de mensagens/status e posições, SHA bruto, recusa de escopo misto/item inválido. Não elimina item repetido dentro do lote nem usa chave sintética como ID oficial de callback.

**Unidade atômica proposta:** todos os itens normalizados, recibo do lote/digest/revisão, idempotência, nonce M2M e auditoria. Ou tudo está durável ou nenhum sucesso é informado. Cada item tem índice e ARCHIVED_UNVERIFIED; não há aceite parcial silencioso. Status e mensagem inbound continuam distintos; status não ingressa como conversa/fechamento. Caso/tentativa sem vínculo autoritativo permanece sem resolução comercial; arquivamento não inventa vínculo por telefone.

Mesmos raw bytes e rota/revisão, com nova prova, recuperam mesmo recibo completo; alias de batch_ref não duplica itens. Variantes físicas com novo batch_ref preservam recibos separados. Mesmo batch_ref com SHA distinto registra conflito durável de fingerprints, sem ACK daquele pedido e sem substituir recibo original.

Adapter de persistência deve devolver sucesso **somente após commit durável de todos os itens**. Perda de resposta, commit incerto, armazenamento parcial, falha de sync ou assinatura inválida não permitem ACK. Nova prova pode obter readback/replay do recibo. Se storage não é durável, lab_ack_ready fica falso, mesmo com resultado em memória.

FileStore prova ordem local write → fsync(file) → rename → fsync(directory) → retorno. Há falhas antes/depois de rename e **dois processos filhos que terminam abruptamente**, antes de rename e após commit/antes da resposta. Restart relê snapshot; temporário não promovido é ignorado. Isso prova comportamento no filesystem do runner desse adapter descartável, não durabilidade PostgreSQL, failover ou homologação Meta.

ACK HTTP produtivo, código/status, política de payload irrecuperavelmente inválido, retries Meta, retenção/disponibilidade são **pendentes**. Não existe listener, ACK externo ou HTTP 200/202 de ingresso.

## META-S0-LOCK-04 — locks, revogação e concorrência

Fonte preservada: caminho final WA55→WA52 faz outbox FOR SHARE → evento → chave técnica → nonce/histórico. Reparos 52/53 removem inversões key/event. PR #7 restringe grants UPDATE(id) necessários ao lock com WITH CHECK false; não reabrir wrappers selados/guards com DML.

Fonte S0/S1: S0S1LocalTeamAuthority.lock_team exige equipe antes de caso/atribuição. Sessão GoTrue bloqueada do PR #9 pertence ao caminho **humano**; não substitui principal M2M.

Proposta de ordem total para discussão, ainda sem mapeamento DDL aprovado:

| Rank | Recurso candidato |
|---|---|
| 10 | Fence autoridade S1/equipe/concessão, se operação depende de direitos humanos |
| 20 | Fence escopo S0/caso/atribuição/opt-out |
| 30 | Registry técnico/rota/binding/revisão |
| 40 | Intenção |
| 50 | Outbox/tentativa |
| 60 | Identidades de eventos, ordenadas por chave |
| 70 | Chaves técnicas, ordenadas por ID |
| 80 | Nonces |
| 90 | Recibo/histórico/auditoria |

Dentro do rank, ordenar chaves ASCII por bytes; adquirir conjunto inteiro em ordem, nunca descobrir lock de rank inferior já na seção crítica. Seleção preliminar de chave/rota não concede autorização: validação decisiva após aquisição ordenada/recheck. Para batch, descobrir todo conjunto de eventos/ordenar antes de adquirir; conflito de conjunto aborta e planeja novamente, sem Graph no retry.

Todos os writers de revogação/cancelamento devem adquirir mesmos fences. Se revogação vencer, begin/reserva falham. Se begin vencer, revogação posterior invalida trabalho futuro; bytes externos podem ter saído e ficam incertos. Nunca prometer recolher mensagem externa com lock SQL. Preservar tombstones contra reabertura por timeout. Revogar key/registry não é revogar equipe/concessão; cada operação declara suas dependências.

**Ordem proposta, não integração.** Ranks 10–40 exigem mapear linhas reais, ordem de todos os mutadores S1/S0/Meta, locks implícitos de FK/triggers, modos SHARE/UPDATE, namespaces advisory, expiração pelo clock DB e 40001/40P01. lock-plan.mjs só detecta inversão em lista; não adquire locks SQL. Corridas desta entrega usam mutex/snapshots, não conexões PG concorrentes.

## Aproveitamento e limite da implementação

| Componente | Uso |
|---|---|
| Cloud wire / Graph classifier | Importação direta inalterada |
| Cloud webhook / inbound HMAC | Importação direta inalterada |
| WA29/WA30 | Invariantes claim/uncertainty; não duplicadas/instaladas |
| WA34 | Separação domínio/identidade; wire não reutilizado como autorização |
| PR #7 | Ordem final, guards corrigidos, entrada selada; sem copiar SQL |
| PR #9 | Resultado+nonce+auditoria antes de commit; sem importação GoTrue |
| PR #11 | Distinção case/cycle e pendências UI; sem conectar botão/contrato humano |

CandidateLab é modelo transacionado com adapter durável **de teste**. Não é novo backend, banco paralelo, gateway S0 ou instalador. FileStore é single-process: não usar dois writers, NFS ou produção. Nome de diretório/opt-in não prova segurança do ambiente. Testes usam tmpdir descartável, chaves aleatórias e dados sintéticos, com limpeza.

## Decisões para o Codex principal

| ID | Decisão pendente e responsável | Evidência antes da integração |
|---|---|---|
| C1 | S0/S1: fonte/binding/revisão de cada gate; intenção/slot/fingerprint | Matriz do domínio atual, negativos por escopo, CAS/grants; sem case=cycle |
| C2 | S0/Meta: lifecycle reserva/begin, custo de possível não envio, dedupe/novo intento | Handle/transporte e crash windows; recuperação não POSTa ocupação antiga |
| C3 | Segurança/Infra: M2M, TLS, custódia/rotação, audience/ACL, clock/TTL/nonce | Emissor técnico real/login mínimo, negativas GoTrue/tenant/rota/replay |
| C4 | S0/Meta/Infra: lote/recibo/durabilidade/ACK, inválidos/backpressure | Commit/readback sob falha, lote inteiro, restart/failover; política HTTP formal |
| C5 | S1/S0/Meta: ordem/modos locks, fences concessão/atribuição/opt-out/key/registry | Dois clientes PG17, ambas as ordens das corridas; preservar WA55/WA52/grants PR #7 |
| C6 | S0/comercial/privacidade: conciliação, direitos, retenção/acesso/expurgo/novos intentos | Fluxo auditável aprovado; observação não muda ficha/cadência por inferência |
| C7 | S0/Frontend: preservar D1–D4 PR #11 | Contrato UI humano não vira M2M ou aprovação de dispatch |

Nenhuma decisão está aprovada. Codex principal avalia contratos/testes **antes** de mapear operações ao núcleo oficial. Próxima etapa autorizável: laboratório PG17 separado que reutilize composição guardada do PR #7 e base atual S0/S1, após ratificação. Esta tarefa não executa essa composição nem integra branches.

## Reprodução e revisão

Checkout auxiliar, Node 22 com strip-types e Python 3, sem instalar dependências:

~~~sh
python3 integration/meta_s0_candidate/verify_sources.py
node --experimental-strip-types --test --test-concurrency=1 integration/meta_s0_candidate/candidate.test.mjs integration/meta_s0_candidate/durable.test.mjs
~~~

Workflow executa **161 regressões Meta existentes** selecionadas no PR #8 (12 Cloud webhook + 20 Cloud wire + 129 anteriores), sem copiar/recontar WA39–68. **52 testes novos** cobrem modelo candidato/fixture de filesystem; não substituem certificação PG17/GoTrue dos PRs #7/#9.

Revisor: conferir diff aditivo/manifesto; ler C1–C7; examinar CI no SHA executável; confirmar ausência de direito de envio/produção/ACK externo; exigir corridas físicas/instalação mínima futuras. Resultados desta proposta em EVIDENCIAS.md; até sua verificação, testes estão preparados, não certificados.

Sem merge, deploy, Graph, credenciais reais, migration hospedada ou integração final.
