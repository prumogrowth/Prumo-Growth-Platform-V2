# S0–Meta–Ingress–01 — contrato operacional candidato v1

28/10/2026, America/Sao_Paulo. Aprovado para desenvolvimento laboratorial pela instrução desta execução. Não ratificado para operação, Meta real, deploy, migrations oficiais ou composição com I86. Base imutável `3cab3d57619cc1157698a08ac26f34e0c363f6dd`, código I85 histórico `062c90ffbe2b223c1d6bb08f614e7a1b6a898201` / CI40680048140. Nenhuma autoridade humana é criada ou utilizada.

## Identidades e provas

Duas provas independentes são exigidas. Meta/Infra valida `X-Hub-Signature-256`, HMAC-SHA256 sobre os bytes originais e App Secret escolhido por configuração confiável. Neste laboratório a S0 também refaz essa verificação, com segredo aleatório sintético por App, antes da aceitação. Isso prova a App física sem deduzi-la de WABA/phone do corpo. Nunca chamar Graph.

A segunda prova é Ed25519 do ingressor técnico sobre `PRUMO/S0-META-INGRESS/M2M/LAB/v1\x00 || canonical(envelope)`. JSON UTF-8 canônico: chaves ordenadas, separadores `,`/`:`, Unicode literal, sem NaN, duplicatas, BOM, extras ou coerções. O wire precisa coincidir byte a byte com a serialização Python definida em `protocol.py`. Esse formato interno estreito requer homologação de interoperabilidade; não é canonicalização genérica de JSON externo.

Envelope `prumo.s0-meta-ingress.lab/1-candidate`: `issuer`, `key_id`, `key_revision`, `audience=LAB_S0_META_INGRESS`, `scope=append|recover`, `app`, `route`, `route_revision`, `batch_ref`, `nonce`, `issued_ms`, `expires_ms`, `raw_base64`, `meta_signature`, `version`. O MAC externo e todos os bytes Base64 originais ficam vinculados à prova M2M. Não se aceita `meta_verified`, identidade humana, Bearer GoTrue, service_role ou operação de envio. IDs ASCII 1–128; revisões decimais positivas até 18 dígitos; tempos inteiros em ms. Janela máxima 30 s, sem tolerância futura: `issued <= clock_timestamp() < expires`, rechecado depois das esperas. Raw até 256 KiB, envelope até 360000 bytes, até 100 ocorrências. Sem compressão ou streaming no perfil.

A fonte confiável local é o registro técnico instalado pelo controlador exclusivo: chave pública, emissor, revisão, validade, escopos, lista explícita de canais, App, rota e concessionária. App/rota são comparadas ao registro, nunca autorizadas pelo corpo. O runtime tem login SQL próprio restrito; a prova M2M permanece obrigatória na API interna. Login SQL não é principal ingressor e não é fornecido ao chamador. Nenhum segredo real é usado.

## Decisão multicanal

Uma requisição física pode conter várias WABAs/números da mesma App **e concessionária**, com canais distintos explicitamente cadastrados. A ratificação laboratorial não permite misturar concessionárias. Cada par `(route,waba,phone)` possui uma única linha, canal e revisão, e deve estar ativo e corresponder à App e à concessionária autorizadas ao ingressor; o canal deve também constar na lista explícita da chave técnica. Um canal válido na mesma App/loja sem grant explícito não recebe permissão por proximidade. A PK impede ambiguidade no par; a unicidade `(route,channel)` impede alias de canal na mesma rota. Identificadores no payload são candidatos de lookup, não prova de autorização.

Todos os vínculos são lidos sob locks em ordem determinística e incluídos no snapshot e digest do recibo. Nenhum canal herda direitos de outro. Um item de outra App, outra concessionária, desconhecido ou inválido recusa o lote inteiro. Não se reduz a um canal válido. Uma App compartilhada não transfere propriedade comercial.

`entry`, `changes`, arrays e seus índices são preservados. Entre `messages` e `statuses`, o ordinal acompanha a ordem de encontro das propriedades no JSON físico. Essa escolha explícita estende o parser original, que enumera mensagens antes de status. A proveniência inclui entry/change/array/item e o JSON integral do item e do contexto da mudança; os bytes originais continuam a fonte íntegra. Duplicatas são ocorrências distintas. Campos desconhecidos dentro de itens/contextos permitidos são preservados; campo de assinatura de evento desconhecido ou coleção nova em `value` recusa todo o lote, nunca é ignorado. Mensagens e status ficam em tipos diferentes e `ARCHIVED_UNRESOLVED`, sem lead, caso, atendimento, destinatário comercial ou dispatch inferido.

## Transação, locks e durabilidade

Ordem efetiva: rota `FOR SHARE` → principal técnico `FOR SHARE` → bindings `FOR SHARE` ordenados `(waba,phone)` → advisory transacional exclusivo por rota, namespace `s0_meta_ingress_lab`/seed731001 → recheck dos recursos já bloqueados/tempo → nonce → lote/idempotência/itens/aliases/auditoria. Todos os objetos pertencem ao schema novo `s0_meta_lab` no banco descartável exclusivo. Não há locks, FKs ou chamadas a recursos I79–I86, CFI, outbox Meta ou S1. Colisão do hash advisory só serializa rotas, sem ampliar escopo.

O controle técnico toma rota `FOR UPDATE` antes da chave/binding e exige CAS de revisão. Revogação de chave incrementa apenas a revisão da chave; desativação de binding incrementa binding e rota. A interface de controle não possui reativação. Nova chave é um ID/material novos; revogado não volta a ativo pelo controle suportado. Alterações diretas pelo instalador são privilegiadas e pertencem à fronteira de confiança, não a uma proteção contra superusuário. Mudanças de binding não podem transferir concessionária: novo vínculo/rota exige revisão e homologação próprias.

Se a revogação vence o fence, ingresso é recusado. Se o ingresso vence, a revogação espera seu commit. O readback revalida autorização atual e pode recusar a entrega do recibo se a revogação já venceu nesse intervalo. Um recibo anteriormente emitido continua prova histórica de armazenamento, sem conferir autorização futura. A validade técnica é linearizada na checagem sob locks; não promete cancelar bytes já emitidos ou autorização indefinidamente viva após o retorno.

Uma transação grava: rota/revisão/snapshot, raw/digest, lote UUID, todas as ocorrências UUID com ordinais, digest normalizado, alias/idempotência, emissor/chave/revisão M2M, nonce/digest do envelope, auditoria e material reconstruível do recibo. O runtime valida integralidade antes do commit e novamente por conexão nova após commit. Erros tardios revertem todo o lote. Resultado SQL incompleto não passa por readback.

Requisitos verificados: PG17, `fsync=on`, `full_page_writes=on`, `SET LOCAL synchronous_commit=on`. Foram exercitados SIGKILL de cliente em oito janelas e SIGKILL do container PostgreSQL com WAL/volume persistido e transação aberta. Commit local sobrevivente e transação não confirmada desfeita não certificam réplica, quorum, failover, perda de host/volume, controlador de disco ou HA. O recibo declara exatamente `PG17_LOCAL_WAL_FSYNC_ON_SYNC_COMMIT_ON`.

## Idempotência e conflitos

Chave lógica: `(route,batch_ref)`; unicidade física: `(route,raw_sha256)`. A rota pertence a uma App autenticada. Mesmo identificador e bytes/revisões iguais recuperam o mesmo lote. Mesmo raw com novo ID apenas acrescenta alias, sem repetir ocorrências. Byte físico diferente e ID novo é outro lote, mesmo que mensagens normalizadas coincidam. Não existe dedupe comercial por wamid. Alterar revisão de rota/binding não permite regravar ou promover recibo antigo; a colisão exige reconciliação técnica independente.

Mesmo ID com raw distinto, ou raw já registrado sob snapshot/revisão diferente, gera `CONFLICT` auditado na mesma transação do nonce, mantendo o original imutável. O conflito não é ACK daquele pedido. Nonce único por key_id; mesma prova assinada é `REJECTED/NONCE_REPLAY`, inclusive depois de commit. Recuperação exige prova e nonce novos, autorização técnica vigente e mesmos bytes/contexto. Recuperação ausente registra consulta e devolve incerteza, sem inserir lote ou alias.

Não há retry automático, efeitos comerciais ou segundo registro lógico após crash. Timeout/erro de commit não permite concluir rollback. Não apagar nonces/aliases/tombstones nesta entrega. Retenção e expurgo produtivos dependem de política própria.

## Recibo autenticado e verificação pelo consumidor

`prumo.s0-meta-ingress.receipt.lab/1-candidate`, Ed25519 sobre `PRUMO/S0-META-INGRESS/RECEIPT/LAB/v1\x00 || canonical(body)`, chave distinta do M2M e do HMAC Meta. O corpo vem apenas do readback SQL e contém: instância S0, App/rota/revisão, UUID do lote, raw_sha256, quantidade efetiva/UUIDs de ocorrências, digest normalizado, snapshot/digest de bindings, emissor/chave/revisão M2M da gravação inicial, identidade/revisão/chave pública do recibo, audit_id inicial, timestamp registrado e estado `DURABLY_COMMITTED`. Não usa contagem alegada pelo ingressor. Chave pública não é segredo e não é âncora autoconcedida.

Consumidor deve fixar chave pública S0 confiável por canal administrativo, verificar assinatura/domínio/versão e comparar pelo menos App, rota, revisão e digest dos bytes que recebeu. `verify_receipt` recusa contexto esperado incompleto. Deve conferir snapshot/revisões, quantidade e referências conforme o perfil homologado. O recibo não contém JWT, senha, chave privada, App Secret, raw, telefone de participante ou texto de mensagem. IDs técnicos de canal permanecem dados a proteger operacionalmente.

Material durável permite regenerar o mesmo corpo/assinatura determinística após reinício do broker, conservando chave de recibo e identidade da instância em custódia confiável. A chave pública fica persistida no lote; chave privada incompatível, mesmo sob mesmo ID, resulta em incerteza. Ausência de chave histórica também resulta em incerteza. Perfil simples de laboratório carrega uma chave por instância; rotação exige conservar a instância/chave antiga para recuperação, nunca assinar silenciosamente corpo antigo com outra identidade. Distribuição de trust anchors, KMS/HSM e continuidade HA ficam pendentes.

## Estados e transições

| Decisão | Condição e transição permitida |
|---|---|
| `ACK_ELIGIBLE` | Somente lote completo, commit e readback comprovados, autorização técnica revalidada e recibo autenticado reconstruível. Pode fundamentar decisão externa do Meta/Infra após homologação; não emite ACK Meta nesta entrega. |
| `PENDING_RECONCILIATION` | Falha após início de escrita, resultado/commit/recibo incerto, readback incompleto ou recuperação sem registro. Nunca presumir sucesso/rollback. Nova prova pode recuperar `ACK_ELIGIBLE`, conflito ou recusa. |
| `REJECTED` | Entrada, autenticidade, escopo, tempo, vínculo ou nonce inválidos. Nenhum recibo de sucesso. Registro previamente confirmado pode continuar existindo; recusa atual não o apaga. |
| `CONFLICT` | Colisão de identidade/conteúdo/revisão, auditada e confirmada. Original preservado. Não muda automaticamente para sucesso daquela variante; resolver fora desta API. |
| `UNAVAILABLE` | Dependência/configuração indisponível antes de qualquer escrita observada. Não fundamenta ACK. Se houve escrita ou resultado de commit incerto, usar `PENDING_RECONCILIATION`. |

Estados descrevem uma tentativa técnica, não um lifecycle comercial ou fila de processamento. Nova tentativa autenticada reavalia tudo. Negativas pré-autorização não recebem auditoria SQL durável neste perfil; auditoria de rejeições de perímetro, rate limit e coletor seguro são dependências operacionais explícitas. Falha ao armazenar conflito também retorna incerteza, não conflito presumido confirmado.

## Interface HTTP e fronteiras

API principal é chamada interna `Ingress.call(bytes, signature)`. Harness separado escuta somente loopback/porta efêmera em `/lab/ingress`; retorna projeção técnica 207/422/409/503 e marcador laboratorial, sem URL pública ou endpoint Meta GET/POST. O teste de perda de resposta HTTP fecha o socket após commit e recupera o mesmo recibo. 207 é convenção do harness, sem significado de ACK do provedor.

Meta/Infra é responsável pelo código HTTP externo, assinatura no ponto correto antes de transformação, challenge/subscription, limite de corpo, TLS, backpressure e retry do provedor. Payload permanentemente inválido exige política de quarentena/dead letter e encaminhamento operacional, sem inventar processamento completo. Indisponibilidade/incerteza exige conservar bytes/correlação e recuperar com nova prova; não responder sucesso fictício nem repetir efeitos comerciais. Não se implementa listener produtivo, resposta HTTP200, dispatch, catálogo PR19 ou governação I86.
