# WA-05D-AUD1 — Auditoria independente da origem do handoff Meta → S0

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Data:** 18/10/2026. **Status:** [P/V local] — vulnerabilidade de laboratório reproduzida e corrigida. A entrega permanece em **Draft**, sem CI remoto, Supabase hospedado, token Meta, banco real, secrets reais, Graph, Webhook comercial, merge ou deploy.

## 1. Contexto e defeito reproduzido

O contrato WA-05C gera um candidato de lote após uma inspeção HMAC fictícia da Meta. A WA-05D confere vínculo App/rota/loja/canal em uma fonte de configuração simulada e digest SHA-256 do corpo e escopo antes de inserir um marcador no próprio Map.

**AUD-INT-01 — ausência de autenticação criptográfica do envelope interno:** um invasor capaz de substituir os metadados do candidato poderia também recalcular o **SHA-256 não autenticado**. Reproduzimos com um callback \`delivered\` cujo \`provider_kind\` foi trocado por \`read\` mantendo os bytes brutos, o App e o canal. O atacante recalculou \`scope_sha256\` para o conteúdo adulterado e a WA-05D antiga respondeu **\`LAB_ACCEPTED\`**.

O ensaio exploratório **falhou antes do reparo**, confirmando a brecha no contrato de laboratório; após a correção, negou a tentativa. Isso **não demonstra comprometimento operacional**, pois a porta de produção não existe.

O problema não era a implementação SHA-256: **hash sem chave não identifica o emissor**. A autenticação HMAC recebida da Meta e a autenticação de transporte entre serviços S0 são garantias diferentes.

## 2. Reparos implementados

Em \`integrations/whatsapp-meta/s0-ingress-gateway.ts\`, a WA-05D agora exige **\`FakeInternalServiceProof\`** no argumento \`admit\` e uma porta privilegiada, fictícia, \`trustedInternalSigningKey(service_ref)\`, distinta do App Secret Meta e do token Bearer da Graph API.

- \`createFakeS0ServiceProof\` (somente laboratório) produz HMAC-SHA256 sobre **todo o \`S0HandoffCandidate\`**, a identidade \`service_ref\` e os instantes \`issued_at_ms\`/\`expires_at_ms\`.
- \`validProof\` compara a assinatura usando WebCrypto, a chave de uma **fonte S0 independente**, o principal selecionado por \`trustedCaller()\`, e limita a validade máxima sintética a **cinco minutos**. Ausência de prova, chave desconhecida, assinatura adulterada, prazo expirado, emissão futura e troca de identidade são recusados.
- A prova é verificada **antes e depois** da região de falha/concorrência simulada \`beforeCommit\`. Uma **rotação ou revogação da chave durante a operação** bloqueia a admissão em memória.
- A revalidação App/loja/canal/revisão e bytes protegidos da WA-05D permanece. Todos os retornos, inclusive o aceito, seguem com \`ack_allowed:false\` e \`production_authorized:false\`. Nenhum \`DurableBatchReceipt\` ou HTTP 200 é gerado.

**Ponto indispensável:** a função de assinatura de fixture **não pode assinar candidatos arbitrários no backend real**. Em produção, somente o adaptador Meta autenticado e autorizado poderá solicitar um atestado, e a S0 deverá verificar a **identidade efetiva do serviço, a finalidade do atestado, permissões por rota/loja, origem da chave e proteção contra replay** com política aprovada. Se o emissor interno for comprometido, HMAC não comprova a verdade do conteúdo. Nem a MAC nem a simulação provam que o payload foi persistido.

O protótipo mantém janelas de replay de provas válidas até seu vencimento e deduplicação **somente em Map**. Antes da produção, requer controle de nonce/identificador protegido, ACL, rotação coordenada, transação SQL e journal durável.

## 3. Evidências executadas

Usado o código publicado no PR #2 como base, com verificação dos blobs da branch; a exploração anterior ao reparo reproduziu **\`LAB_ACCEPTED\` indevido**. Depois:

- Node.js **v22.16.0**: **358/358 testes sintéticos PASS** em **22 suítes**, incluindo 352 regressões originais e **GATE-23..28** (seis casos permanentes).
- TypeScript **v5.8.3**: \`tsc --noEmit --strict\` **PASS** sobre **16 módulos e 22 suítes** com tipos Node disponíveis localmente.
- Novo teste GATE-23: adultera \`provider_kind\` e recalcula o digest de escopo com bytes do Meta inalterados. Sem a assinatura interna legítima da nova versão, o resultado é \`SERVICE_ATTESTATION_DENIED\`, com zero inserções.
- GATE-24..28: prova ausente/alterada, serviço diferente, validade temporal, rotação da chave antes do commit, chave errada e resultado aceito ainda sem ACK.
- Blobs Git publicados **idênticos** aos arquivos locais executados: \`s0-ingress-gateway.ts\` = \`9f54c91c0c59dec24660b4711df61603305b7f59\`; \`s0-ingress-gateway.test.ts\` = \`1f44fe6eed8ef199b8077bcfcb90a7e266be451c\`. O módulo de handoff WA-05C não precisou de nova alteração (\`a9ae647a6cc5e99f79c3fa8a0c0bed21eeac6327\`).

O teste exploratório que revelou o defeito foi executado **apenas localmente**, fora da suíte permanente. Os seis testes GATE-23..28 **foram publicados**. Não houve CI remoto, teste PostgreSQL, tráfego Meta ou inspeção de segredo hospedado.

## 4. Requisitos da S0 não atendidos pelo laboratório [R]

1. **Principal autenticado e autorizado** para cada chamada interna, com escopo explícito de origem, rota, App/concessionária/canal e revogação. Não aceitar \`trustedCaller()\` injetado como prova; é apenas fixture.
2. **Material criptográfico protegido e purpose-scoped**, diferente do App Secret Meta, Graph token e verify token GET. Definir escolha entre mTLS, token de identidade de workload, HMAC com cofre protegido etc. sob DEC-WA-06; não criar segredo real nesta fase.
3. **Replay control** com identificador de operação, validade, escopo e transação durável; uma prova interna HMAC válida não pode ser interpretada como autorização permanente.
4. **Transação ACID** entre confirmação do vínculo vigente, corpo bruto protegido, batch, occurrence_ref por item e tarefas, com recuperação de \`COMMIT_UNKNOWN\` e política de ACK somente após commit.
5. **Segregação de decisões comerciais**: autenticidade do ingresso não autoriza C03/C06/C12 nem envio de WhatsApp. Timeouts Graph incertos continuam sem retry cego.

**GO:** especificar interfaces autenticadas e testar localmente mecanismos de principal e revogação de menor privilégio. **NO-GO:** tratar a MAC de laboratório como segurança implementada, emitir HTTP 200, migrar hosted Supabase, conectar a POC concessionária de demonstração, usar token Meta ainda pendente de verificação por terceiro, merge ou deploy.

## 5. Mapa mental

Atualizar \`docs/MAPA_MENTAL.md\` da branch \`feat/s0-fundacao-prumo\` com a auditoria e os 358 testes locais. **Não criar novo nó no primeiro diagrama:** o serviço interno S0 é detalhe de proteção da ligação já existente Meta → inbox durável. O próximo crescimento visual só ocorre quando houver subsistema ou relação arquitetural realmente nova.
