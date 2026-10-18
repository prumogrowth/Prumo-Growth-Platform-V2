# WA-05C — contrato candidato Meta → persistência S0, sem ACK real

**Data:** 18/10/2026. **Situação: [P/V local]**, exclusivamente em branch Draft PR #2. Revisado com o contrato compartilhado S0 ↔ Meta \`interface-compartilhada-s0-meta-v0_1.md\` e as interfaces WA-01A/B, WA-04A/B, WA-05A/B. **Nenhuma alteração** de função hospedada, secrets, número comercial, Supabase, Meta ou deploy.

## 1. Fronteira arquitetural preservada

**Meta (frente WhatsApp):** valida rota de App confiável (não body/query), usa o App Secret correspondente para HMAC sobre **bytes originais**, interpreta todos os itens \`entry/changes/messages/statuses\` e associa WABA + \`phone_number_id\` ao canal/loja vigente. O resultado do parser **não constitui recibo durável**.

**S0 (frente principal):** será responsável por autenticar a chamada **interna e privilegiada** do adaptador, conferir novamente App/loja/canal e versão contra revogação concorrente, proteger o corpo integral, persistir batch + ocorrência por item + tarefas numa mesma transação ACID, restaurar após falha e emitir recibo confiável **somente após commit**. Os nomes físicos de DDL/RPC e o mecanismo de prova de commit continuam **[P/R]**. Não criar segundo backend concorrente.

**HTTP ACK da Meta:** **não implementado nem permitido por este incremento**. O \`decideBatchAck\` WA-01B é um analisador hipotético de forma e não comprova autenticidade de um recibo. Mesmo que o recibo aparente \`COMMITTED\`, não gerar HTTP 200 só com um objeto recebido. DEC-WA-06 continua pendente para ACK, quarentena e retenção.

## 2. Código publicado

\`integrations/whatsapp-meta/s0-handoff-contract.ts\` é puro nas saídas, sem Supabase, RPC, persistência, HTTP ou liberação comercial:

- \`prepareS0HandoffFixture(input, ports)\` usa internamente \`inspectRoutedMetaPost\` da WA-04B com **portas e segredos fictícios injetados**. Fotografa corpo, batch, referência protegida de payload e rota **antes** da primeira operação assíncrona. Recusa HMAC inválido, rota desconhecida, App revogado, canal de outra concessionária, posições ambíguas e lotes vazios ou acima do limite. Retorna apenas um **\`S0HandoffCandidate\`** com \`contract_version='meta-s0-handoff.v0.1-proposed'\` e \`ack_allowed:false\`.
- O candidato preserva \`batch_ref\`, \`route_ref\`, \`route_revision\`, \`app_ref\`, \`protected_payload_ref\`, \`payload_sha256\`, \`scope_sha256\`, contagem e lista mínima de \`occurrences\` com posição \`entry_index/change_index/array_kind/item_index\`, tipo de evento, App/loja/canal, WABA/emissor, ID/timestamp/tipo técnico do provedor. **Não** contém corpo, identificador de participante, texto de cliente, token, assinatura nem \`occurrence_ref\` definitivo (será criado pelo S0).
- \`scope_sha256\` cria um digest determinístico da referência de lote, rota/revisão e posições/vínculos de App/loja/canal por evento. **É referência de consistência, não uma autenticação/MAC nem prova de origem**. Toda evolução do algoritmo exige versionamento e revisão cruzada; a S0 precisa computar e validar a mesma regra com fonte própria.
- \`reviewS0ReceiptFixture(candidate, allegedReceipt)\` só compara **forma, versão, batch, App, referência/digest de payload, rota/revisão, digest de escopo, contagens e quarentena**. Recusa objeto com getter/protótipo anômalo, campos extras, diferença de escopo, versão ou digest, somas incompletas e recibos inconsistentes. Um recibo perfeitamente compatível retorna **\`STRUCTURE_MATCHES_BUT_UNVERIFIED\`**, \`ack_allowed:false\` e \`reason='NEEDS_AUTHENTICATED_S0_COMMIT_EVIDENCE'\`.
- Não há ponte deste resultado para \`DurableBatchReceipt\`, \`decideBatchAck\`, fetch/Supabase, Graph, outbox, Webhook HTTP ou autorização de negócio C03/C06/C12. Em particular, **nenhum método atual prova ACID**.

**Avisos:** hashes SHA-256 não substituem o armazenamento real dos bytes, autenticação da porta ou controle transacional. A decisão \`ok:true\` da fixture só significa que o parser injetado aceitou o POST; quem recebe a proposta ainda deve conferir autenticação do adaptador e consistência do vínculo S0 atual. Metadados técnicos também são internos, não devem ser logados indiscriminadamente.

## 3. Compatibilidade e riscos não encerrados

- Meta \`statuses[].id\` identifica **mensagem**, não evento único; \`messages[0]\` e \`statuses[0]\` recebem posições distintas pelo campo \`array_kind\`. Um \`occurrence_ref\` é atribuído **pela S0 no commit**, não pela Meta nem pelo arquivo candidato.
- Um POST legítimo pode ter **mais de um canal da mesma App**. O envelope preserva o canal de cada item: não atribuir indiscriminadamente uma loja/canal global ao batch.
- A referência de \`protected_payload_ref\` é só um **nome de fixture** nesta versão; não existe garantia de escrita/recuperação de um corpo protegido.
- Falhas **depois** de aceitar externamente ou **depois** do commit exigem prova de estado, \`COMMIT_UNKNOWN\` e política de redelivery; não reenviar Graph após timeout sem reconciliação, nem deduplicar callbacks por \`wamid/status/timestamp\`.
- O token definitivo depende de verificação de terceira pessoa; o usuário avisará da liberação. **DEC-WA-04/06**, privilégios S0, RLS, persistência durável, gestão de secrets, proteção de payload e operação permanecem pendentes.
- Nenhuma decisão de esquema/RPC, ambiente hospedado, merge, deploy ou custo foi tomada.

## 4. Testes efetivamente executados

Ambiente **Node.js v22.16.0**, **TypeScript v5.8.3**.

\`node --experimental-strip-types --test *.test.ts\` executado localmente no conjunto da frente Meta: **330/330 PASS** (306 regressões anteriores + **24 testes S0C-01..24**). Cobertos HMAC, escopo multicanal, App indevido, corpo mutável, hash bruto, posições de mensagem/status, \`wamid\` com \`=\`, recibo falso \`COMMITTED\`, divergência de lote/payload/App/canal/revisão, counts incoerentes, quarentena e getters hostis.

\`tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck --esModuleInterop --types node *.ts\` → **PASS** para **15 módulos de implementação e 21 arquivos de teste**.

Hashes Git dos arquivos versionados coincidem com o código testado localmente:
- \`s0-handoff-contract.ts\`: \`475f013b06d4b6e0e03f57f019562590488c6a17\`.
- \`s0-handoff-contract.test.ts\`: \`01b4ec2b97e367e3a6f82f4a47755b76f2abf596\`.

**Não foi executado CI remoto**, nem PostgreSQL, integração Supabase, HMAC real Meta, webhook público, número concessionária de demonstração, envio de mensagens, alteração de segredos, migração hospedada ou autorização comercial real.

## 5. Entrega e próxima decisão

**GO:** revisão conjunta da especificação \`meta-s0-handoff.v0.1-proposed\` e desenho do **adaptador interno privilegiado S0** (com evidência de origem, proteção do payload e transação única), mantendo código e testes sintéticos. **NO-GO:** emitir \`200\`/ACK, implantar Edge Function, ativar Graph, conectar dados reais ou alterar a POC concessionária de demonstração. Ambos PRs permanecem Draft.

O \`docs/MAPA_MENTAL.md\` da branch S0 deve registrar a WA-05C na tabela/histórico **sem nó redundante no primeiro diagrama**: o fluxo Meta → inbox durável → ACK já está representado.
