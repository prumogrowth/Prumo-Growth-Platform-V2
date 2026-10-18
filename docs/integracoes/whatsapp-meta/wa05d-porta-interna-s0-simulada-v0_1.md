# WA-05D — fronteira interna S0 privilegiada (simulador) e verificação cruzada

**Data:** 18/10/2026. **Status:** [P/V local], branch Draft do PR #2; não há implementação de ingresso operacional, RLS ou transação Supabase. **Token Meta definitivo ainda depende de verificação por terceiro.**

## 1. Verificação cruzada da frente S0

Foram revisados os contratos reais versionados nas duas branches:

- PR #2: \`interface-compartilhada-s0-meta-v0_1.md\` e a WA-05C \`s0-handoff-contract.ts\`, que autenticam HMAC da Meta **só com portas fictícias** e geram candidatos de handoff sem qualquer recibo confiável.
- PR #1: \`S0_034B_AUDITORIA_CONTRATO_C07_WA01C_2026_10_18.md\`: \`statuses[].id\` identifica a **mensagem**, não um evento único; a chave \`wamid/status/timestamp\` da migration S0/030 **não deve servir como dedupe real**. A S0 precisa emitir seu \`occurrence_ref\` na transação de ingresso.
- PR #1: \`S0_037D_CAPACIDADE_TRANSACIONAL_2026_10_18.md\` e \`S0_037F_EMISSOR_ASSINADO_MOCK_2026_10_18.md\`: capacidades e emissores assinados foram demonstrados em **SQL/PG17 descartável**, mas a 037D depende de emissor de fixture \`postgres\` e a 037F de \`sessoes_mock/vinculos_mock\`, sem auth GoTrue ou owner comercial operacional. **Não** reutilizar indiscriminadamente a prova de C07/C08 como autenticação do ingresso Meta.

**Decisão de engenharia:** a porta futura deverá ser propriedade da S0, consumir um principal de serviço autenticado **fora do payload**, limitar suas permissões por rota/loja/canal, manter as credenciais de transporte Meta separadas da autorização interna e acoplar escopo/versão/payload/batch/ocorrências/tarefas a uma transação durável única. Nenhuma nova tabela, role, migration ou API interna foi criada nesta etapa.

## 2. Código implementado na frente WhatsApp

\`integrations/whatsapp-meta/s0-ingress-gateway.ts\` apresenta o \`FakePrivilegedS0Ingress\`, um exercício **exclusivamente em memória** para a futura interface interna:

1. Recebe a proposta \`S0HandoffCandidate\` da WA-05C (fora desse módulo, HMAC de fixture já verificado) e os bytes de payload simulado. Rejeita campos extras, getters, versões ou posições inválidas, callbacks sem \`array_kind\` e metadados de cliente fora do contrato. Cópias são capturadas antes de \`await\`, evitando diferenças entre conteúdo conferido e usado.
2. Obtém \`trustedCaller()\` através de uma **porta confiável de laboratório**. Compara \`service_ref\` ativo e lista de \`route_ref\` permitidas, sem ler \`service_ref\` do lote. **Essa porta é simulável por quem constrói o teste**, e não comprova autenticação real ou resistência a um atacante que controle os ports.
3. Consulta seu \`trustedRegistry()\`, distinto do mapeamento que gerou o candidato Meta, verificando revisão, vigência e todos os vínculos **App/concessionária/canal/WABA/phone** de cada item.
4. Exige que o \`FakeProtectedPayloads\` já contenha uma cópia **idêntica** dos bytes; calcula independentemente SHA-256 do corpo e o \`scope_sha256\` no formato canônico WA-05C. **SHA-256 não é autenticação**, e a fixture não equivale a cofre, storage durável ou prova ACID.
5. Imediatamente antes da inserção em um \`Map\`, relê **principal, registro, relógio e referência do corpo**, bloqueando desativação/revogação/reassociação concorrente ocorridas até esse ponto do ensaio.
6. Simula \`LAB_ACCEPTED\`, \`LAB_REPLAY\`, \`LAB_CONFLICT\` ou \`DENIED\`, com contagens. O mesmo batch e fingerprint não cria item novo; outro batch pode conservar callback com \`wamid\` igual. **Todas** as respostas: \`ack_allowed:false\`, \`production_authorized:false\`, **sem** \`commit_state\`, sem HTTP 200 e sem campo de token.

\`FakePrivilegedS0Ingress\` **não** armazena eventos individuais, não disponibiliza payload recuperável, não implementa transação ACID ou journal durável, não autentica o serviço com JWT/HMAC/mTLS, não consome token Graph nem fornece recibo confiável. Instanciar outro objeto de \`Map\` perde tudo. Mesmo o retorno \`LAB_ACCEPTED\` não autoriza criar \`DurableBatchReceipt\` ou chamar \`decideBatchAck\`.

**Limitação de corrida:** não há \`await\` entre a última verificação e a inserção em memória, mas não há lock do estado do registro em banco, nem garantia serializável ou revogação sincronizada com outros processos. A S0 real deve proteger o vínculo na **mesma transação** do commit.

## 3. Segurança e invariantes para o contrato operacional S0 [R]

- Principal de serviço autenticado e verificável por role/mTLS/JWT interno *ou* outro mecanismo aprovado; não aceitar campos \`transport_signature_validated=true\`, \`service_ref\`, \`concessionaria_id\` ou \`scope_sha256\` de um cliente como autoridade.
- Privilégio mínimo: porta pública Meta valida assinatura por App, chama função interna autenticada; gateway não recebe SELECT indiscriminado em \`auth.sessions\`, secrets ou dados comerciais; diferenciar o HMAC da Meta do HMAC/identidade S0.
- Origem independente e vigente da relação \`route_ref/revision → Meta app → WABA/phone → loja/canal\`, com revalidação sob lock/versão estável na transação S0 e controle de rotação/revogação.
- Persistir **bytes originais protegidos e íntegros**, batch id gerado internamente, um \`occurrence_ref\` para cada posição \`entry/change/messages|statuses/item\`, tarefa de processamento e registro privado de auditoria, com rollback integral em erro.
- Em \`COMMIT_UNKNOWN\` consultar a fonte durável e aplicar política de replay; \`statuses[].id\` ou \`status+timestamp\` jamais são identificador universal da ocorrência nem prova de dedupe. Idempotência de efeitos externos é outro contrato.
- Só uma porta realmente autenticada que prove commit durável, sob DEC-WA-06, poderia futuramente permitir ACK. Não existe essa porta neste PR nem autorização para GET/POST hospedado, Graph ou envio comercial.

## 4. Execução e evidência

Teste local Node.js **v22.16.0**, TypeScript **5.8.3**:

- \`node --experimental-strip-types --test *.test.ts\` → **352/352 PASS** em **22 arquivos de teste**: 330 testes anteriores da frente Meta e **22 novos GATE-01..22**.
- \`tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck --esModuleInterop --types node *.ts\` → **PASS** nos 16 módulos e 22 arquivos de testes, utilizando definições Node locais.
- Hashes confirmados como idênticos entre GitHub e arquivos executados: \`s0-ingress-gateway.ts\` \`df8382ff49a4fbc61355e64a41f71d6d2b093d93\`; \`s0-ingress-gateway.test.ts\` \`a5c2c21cbf8bb0db7a35e169bee93a4dca589464\`.
- Cenários: caller revogado/não autorizado, App vencido, troca de loja ou canal mantendo revisão, revogação antes do commit fake, lote multicanal, bytes divergentes, digest falso, propriedades getter, campos extras sensíveis, replay, duplicação de eventos entre batches e falha de escrita fake.
- **Nenhum** GitHub Actions remoto, HMAC externo Meta, Supabase hosted/local real, Postgres, deploy, mudança de números, migração ou contato com Graph API foi realizado nesta etapa.

## 5. Gate e mapa mental

**GO** para documentação e próxima auditoria sintética do contrato; **NO-GO** operacional enquanto token Meta, DEC-WA-04/06, principal de serviço verificável, privilégio mínimo, proteção/restore de payload, transação ACID e política de ACK não forem resolvidos.

Atualizar a linha do tempo da frente Meta em \`docs/MAPA_MENTAL.md\` da branch S0. O **primeiro Mermaid já possui a ligação da Meta à inbox durável antes do ACK**, portanto esta etapa apenas detalha a fronteira existente; não acrescentar nó de simulação que poderia sugerir backend S0 já implantado.

## Revisão adversarial final WA-05D

Foi reproduzido um defeito **antes do reparo**: em GATE-21, modificar `provider_kind` e `provider_timestamp` de uma observação mantinha o antigo `scope_sha256` válido e o simulador retornava `LAB_ACCEPTED`. O cálculo canônico da WA-05C **e a verificação independente da WA-05D** agora incluem esses campos; GATE-21 nega com `SCOPE_DIGEST_MISMATCH`. GATE-22 confirma que o mesmo batch com referência de payload diferente produz `LAB_CONFLICT`, não replay. **Resultado final: 352/352 testes PASS**, TypeScript estrito PASS, hashes atuais: WA-05C `a9ae647a6cc5e99f79c3fa8a0c0bed21eeac6327`; WA-05D `df8382ff49a4fbc61355e64a41f71d6d2b093d93`; teste WA-05D `a5c2c21cbf8bb0db7a35e169bee93a4dca589464`. A serialização canônica continua **proposta**, ainda não é um contrato versionado de API operacional.

## Complemento de auditoria WA-05D-AUD1 (18/10/2026)

Uma revisão adversarial adicional demonstrou que `scope_sha256`, mesmo completo, podia ser **recalculado por um agente que alterasse o envelope**, preservando uma alteração de callback `delivered → read` nos metadados fictícios. A implementação posterior agora exige atestação HMAC interna, com chave distinta da Meta e verificação ligada ao principal do serviço, em duas etapas antes do commit em memória. **358/358 testes sintéticos PASS** (seis novos), TypeScript estrito PASS; nenhum ACK real ou segredo. Veja [auditoria WA-05D-AUD1](wa05d-aud1-atestacao-interna-offline-v0_1.md). O relato histórico dos 352 testes anteriores permanece válido como marco anterior, não representa o gate atual.
