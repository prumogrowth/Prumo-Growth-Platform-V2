# WA-46 — HMAC Meta sobre bytes brutos antes da fronteira WA45 (somente laboratório)

**24/10/2026 · Branch de integração S0/Meta · PR #2 Draft · PostgreSQL 17/Node offline.**

## Incremento executável

A nova porta \`s0_wa_050_meta_raw_hmac_gate.mjs\` verifica HMAC-SHA256 de **um snapshot dos bytes brutos** de um POST sintético Meta, usando App Secret **fictícia** selecionada por porta interna vinculada à rota fixa do construtor. Antes e depois da busca da chave, verifica App, WABA, phone ID, tenant, canal, revisão e segredo contra um registro interno simulado. Após MAC válido, só aceita **um status** num envelope Meta estrito (\`object/entry/changes/value/metadata/statuses\`), rejeita múltiplos, mensagens e payload WA34/35.

Em seguida, entrega apenas \`eventRef/kind/bodySha256/wamid/recipient\` à WA45, que relê sua própria registry/binding e emite a tupla S0/044. O adaptador confere que os quatro campos técnicos de App/WABA/phone/canal e os campos do evento retornados pela WA45 continuam iguais aos da rota assinada. Por fim, reconfere o registro interno e prazo monotônico.

**Contrato explícito:** a assinatura Meta, quando calculada sobre fixtures, é um **teste criptográfico**, não comprovação de origem real da rede. A autenticação de máquina, a autoridade dos ports, o binding persistido, a identidade do emissor e o consumo transacional S0 ainda **não** existem como serviço produtivo. \`WA34\` JSON-HMAC continua **incompatível** com a tupla \`S0/044\`: não há aceitação de \`mac_sha256\` WA34 nem conversão tácita para a MAC interna S0. O gate processa um formato sintético mínimo de callback; não implementa todas as variantes oficiais Meta, inclusive callbacks com campos opcionais adicionais.

O \`eventRef\` WA46 é derivado dos campos sintéticos de status por SHA-256, **não** representa ID único garantido pela Meta e não determina política definitiva de deduplicação. O \`bodySha256\` corresponde aos mesmos bytes que foram verificados por HMAC. O gate não retém bytes brutos nem expõe segredos na resposta.

## Provas e execução

- \`supabase/tests/s0_wa_050_meta_raw_hmac_gate.mjs\`: fronteira adicional, totalmente offline, com negação fechada.
- \`supabase/tests/s0_wa_050_meta_raw_hmac_gate.test.mjs\`: **28 provas Node**, incluindo HMAC positivo/negativo, segredo/App errado, rota revogada, revisão obsoleta, mutação assíncrona do corpo, cross-WABA/Phone, destinatário/WAMID inconsistentes, lote, inbound misto, UTF-8/JSON inválidos, payload WA34 e falta de porta/chave.
- \`scripts/run-s0-local.sh\` e \`.github/workflows/wa39-s0-meta-offline.yml\` executam e exigem marcadores WA46-01–28 juntamente com regressões S0 e WA39–45. A evidência só é verde após execução no **HEAD exato**.

## Impedimentos de produção e dependências

- Sem HTTP ou ACK: \`ack_allowed\`, \`send_authorized\`, \`retry_external\`, \`production_authorized\`, \`service_authenticated\`, \`meta_provenance_production_proven\`, \`delivery_confirmed\` e \`case_transition_authorized\` permanecem **false**.
- Sem principal de máquina, chave externa em KMS, chaveamento de audience/issuer/nonce no transporte WA34→S0, registros autoritativos remotos ou rechecagem transacional após a última operação assíncrona.
- A WA45 e a WA46 possuem registros *injetados* potencialmente falsificáveis por quem construir o processo. O novo código não é endpoint e não deve ser publicado. A S0/044 mantém wrapper de escrita privilegiado de laboratório. Sem migration, deploy Supabase, Meta Graph, número real ou token da concessionária.
- S1 não foi alterada nem é necessária para este ensaio; para atendimento comercial deverá decidir revogação e transferência de Consultores, estados de atendimento e ordem de locks S0↔S1 antes da integração.

**Próximo incremento sugerido:** contrato versionado e autenticado de origem/audiência da máquina + harmonização explícita WA34/35→S0/044/045 em uma porta confiável, com replay em transação e privilégio mínimo. Submeter o contrato ao aceite das frentes S0/Meta/Infra; manter S1 pendente para semântica comercial.
