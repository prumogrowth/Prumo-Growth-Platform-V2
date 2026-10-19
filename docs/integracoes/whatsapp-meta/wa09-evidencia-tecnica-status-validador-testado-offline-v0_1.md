# WA-09 — evidência Graph e posições de status: biblioteca testada offline

**19/10/2026 | PR #2 Draft | execução local Node sem API, credencial, mensagens, banco ou deploy.**

## Contexto e objetivo

A WA-08 endureceu `technical-reconciliation.ts` com regras dispersas em funções internas, mas deixou **REC-25..35 pendentes de execução** no ambiente da revisão. Nesta continuação, extraímos um subconjunto crítico do contrato para um módulo **puro e executável independentemente**, `integrations/whatsapp-meta/status-evidence.ts`, e o reutilizamos no conciliador já existente.

O componente não decide atendimento comercial, não prova envio, não reconhece uma conexão HTTP autêntica e não autoriza ACK. Apenas verifica consistência de um **resultado técnico previamente observado** e de coordenadas de uma ocorrência de status.

## Implementação publicada

- `isMetaWamid(unknown)`: valida exatamente a gramática já exigida pelo parser/classificador Meta, prefixo `wamid.`, caracteres permitidos e limite, rejeitando IDs genéricos e caracteres de controle.
- `isStatusPosition(unknown)`: exige objeto de dados simples com **somente** `entry_index`, `change_index`, `array_kind='statuses'`, `item_index`; índices inteiros seguros não negativos. Rejeita getters/proxies inválidos, propriedades inesperadas, array `messages` e campos ausentes; exceções são tratadas como rejeição.
- `isAcceptedGraphEvidence(unknown)`: exige objeto de dados simples e nove campos exatos do `GraphSendOutcome`, coerência `send_state='API_ACCEPTED'`, `api_accepted=true`, HTTP 2xx, `wamid` válido, erros Meta nulos, `retry_automatically=false`. Não confere autenticidade de origem, S0, janela de 24h nem evento real `sent`.
- `technical-reconciliation.ts`: importações das três verificações acima substituem validações locais; o resultado `NOT_ACCEPTED` permanece usado para HTTP/estado impossível e `INVALID_REFERENCE` para referências tecnicamente malformadas. A unidade de observação de status continua preservada em memória sem dedupe definitivo. Nenhuma operação de rede foi adicionada.

## Evidência executada nesta sessão

**8/8 testes Node.js PASS** em `status-evidence.test.ts`, Node `v22.16.0` com `--experimental-strip-types --test`, em diretório local isolado. Cenários WA09-01..08: formato de mensagem, índices/posições legítimas e ilegítimas, dados herdados/getters, coerência do HTTP, flags contraditórias, campos extras, retornos booleanos sem PII. Também executado **`tsc --noEmit --strict --skipLibCheck --target ES2022 --module NodeNext --moduleResolution NodeNext` PASS** para `status-evidence.ts`, TypeScript 5.8.3.

As cópias exatas dos **dois arquivos testados** foram publicadas no GitHub e confirmadas com Git blob SHA:
- `status-evidence.ts`: `4ce9bf8319a0dd2ba621643819dd5435833f3a77`
- `status-evidence.test.ts`: `97560d5d2b0c12b8178e8b37841c31d449c4f873`

Fonte do conciliador após integração: blob `c98bb25575c302e659b8a5781e33cacf1fcd16b6`, verificação estática de importações/chamadas. **Não foi executada sua suíte completa REC-01..35 nesta sessão**, nem a compilação do módulo `technical-reconciliation.ts` com todos os imports do repositório. Portanto **não** atribuir PASS da integração inteira por conta dos oito testes do helper; são provas distintas.

## Bloqueios conhecidos, sem dependência de API externa

1. Recuperar a árvore de dependências da branch no ambiente de testes Node/TS e executar `node --experimental-strip-types --test integrations/whatsapp-meta/status-evidence.test.ts integrations/whatsapp-meta/technical-reconciliation.test.ts`, incluindo regressão REC-01..35, registrando commit SHA.
2. Validar S0/Meta em PostgreSQL 17 descartável; os 20 cenários WA-06D SQL permanecem **sem execução comprovada** neste ciclo. Não substituir a transação de ingresso real por fixtures independentes.
3. Só depois construir/admitir porta autenticada e recibo comprovado após COMMIT/COMMIT_UNKNOWN, vínculos App/WABA/número→loja vigentes e proteção integral do payload. API Meta externa, segredos reais, templates aprovados, callbacks reais e prova operacional de `sent` são **etapas posteriores e dependem de autorização específica**.

**GO:** continuar estrutura e testes offline. **NO-GO:** anunciar produção, ACK HTTP, Graph real, regra de negócio S0/C07/C09, custos, Supabase hospedado ou merges. PRs continuam Draft.

## Continuação WA-09B — coerência de correlação e identificação de emissor (19/10/2026)

**Mudança implementada, não limitada a documentação:** `status-evidence.ts` recebeu `isSafeEvidenceRef` para validar a sintaxe e o limite (1–128) dos identificadores internos de `attempt_id` e `correlation_id` em `isAcceptedGraphEvidence`; antes, a função verificava apenas a presença desses campos. Também recebeu `isMetaPhoneNumberId` (somente dígitos, 5–25) e `technical-reconciliation.ts` passou a usar esse validador para o emissor técnico tanto no vínculo `registerAcceptedSend` quanto em `observeAuthenticatedFixture`. **Não se trata da normalização de telefone de destinatário brasileiro, titularidade civil ou validação bancária.**

**Auditoria corretiva:** documentação e nome do caso WA09-10 foram ajustados para deixar claro que formato de referência **não prova ausência de PII**. Não houve coleta de dados reais.

**Teste local efetivamente executado:** `node --experimental-strip-types --test status-evidence.test.ts` em Node v22.16.0 → **11/11 PASS**; `tsc --noEmit --strict --skipLibCheck --target ES2022 --module NodeNext --moduleResolution NodeNext status-evidence.ts` → **PASS**. Verificados Git blob SHA dos arquivos de **código e teste efetivamente executados**: biblioteca `50095d75216f13686782476e8f6143d64933f42d`, testes `bde56f1245b0ee635bc2874950599fc1bd941dd4`. Casos adicionais WA09-09, 10 e 11 validam referências internas malformadas, ausência de caracteres proibidos e o formato técnico do emissor.

**Escopo de evidência:** a alteração em `technical-reconciliation.ts` foi publicada, porém a **regressão integrada REC-01..35 ainda não foi executada** nesta etapa (não havia um checkout completo do repositório privado no ambiente local). Não declarar integração testada end-to-end por causa dos 11 testes do helper. Tampouco foram rodados os cenários PostgreSQL WA-06D (última evidência 0/20) ou S0-040 (0/5). Esses testes internos **não exigem API externa**, mas exigem árvore de código, Node/TS e PG17 adequados. A preferência pelo uso das APIs reais somente na fase final permanece preservada.

**Sem alteração em:** Graph real, Supabase hospedado, S0/S1 SQL, regras comerciais, estado vendido/perdido, opt-out, janela 24h, envio ou recibo HTTP. PRs Draft, sem merge/deploy.
