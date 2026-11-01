# OAI-OFF-02 — Fronteira tipada offline (contrato candidato v0.1)

**Status:** CANDIDATO OFFLINE; não é interface S0 ratificada, cliente OpenAI, homologação E02 nem autoridade de negócio.
**Origem:** OFF-01 `394512327cd3756dfbe61ff970a6279c354b6565` sobre S2 `1747cb0fee2a95322dc768044bafe9817d8cc540`.
**Arquivos novos:** `e04_offline_lab/typed-boundary.mjs`, `e04_offline_lab/s2-guard-links.mjs` e teste próprio.

## API pública

`validatePrivateEnvelope(e)` retorna `{status:'READY',privateContext}` ou `{status,stage}` sanitizados. O contexto validado é uma **cópia imutável** com token de procedência interno ao módulo; não deve ser serializado ou exposto ao fornecedor. `buildProviderPayload(ready)` devolve **somente** o objeto serializável elegível ao fornecedor. `validateProviderCandidate(ready,output)` recebe objeto ou string JSON estrita e devolve `{status:'PROPOSED',stage:'S0_RECHECK_PENDING',operation,privateReceipt,proposal,assurance}` ou falha tipada. `simulateOfflineExchange(envelope,event,options)` executa a mesma lógica com relógio, recheck e replay **sintéticos**. `safeAuditEvent(outcome,operation)` reduz campos a status/etapa/operação/versão sem conteúdo ou IDs. `parseStrictJSON(text)` rejeita duplicatas de chaves, inclusive equivalências escapadas.

`runSyntheticGuard(name,fixture)` faz ligação, **somente offline**, com os seis módulos S2 preservados. `name` é `journey | f03-commit | f02-lifecycle | f02-frequency | meta-131049 | transport-evidence`; seu retorno `S2_SYNTHETIC_GUARD_ONLY` mais veredicto não comprova autorização S0, assinatura de transporte ou envio.

## Entrada privada v0.1

```js
{
 schemaVersion:'prumo.openai.private-exchange/0.1-candidate',
 operation:'F01'|'F02'|'F03',requestId:'private_request',attemptId:'private_attempt',
 providerTag:'opaque_nonsecret_exchanged_alias',nowMs:1793448000000,deadlineMs:1793448060000,
 scope:{authenticated:true,authorized:true,tenantAllowed:true,
   storeId:'private_store',caseId:'private_case',personId:'private_person',
   expected:{case:1,cycle:1,form:1,catalog:1,assignment:1,policy:1},
   current:{case:1,cycle:1,form:1,catalog:1,assignment:1,policy:1}},
 privacy:{modelContentAuthorized:true,dataMinimized:true},
 instructions:{version:'v1',text:'instrucao global',behavior:'somente F01'},
 task:{/* ver abaixo */}
}
```

Todos os objetos usam chaves exatas; IDs curtos com caracteres seguros; 48 fontes/itens por lista, 3 mil caracteres por trecho e limite de profundidade 12. Rejeita protótipos não comuns, acessores, chaves mágicas, números não finitos, listas esparsas e dados contraditórios. `scope` é **fixture fornecida**, não evidência de autenticação/consentimento; `providerTag` é um marcador sintético opaco, **não segredo nem identificador real**. Um backend real teria de gerar e controlar esse marcador. A versão `policy` não é confundida com a versão de `form`, `case` ou `cycle`.

**F01 task**: `owner:'ai',handoff:false,humanized:false,modality:'text'|'audio',recentContext:[{role:'customer'|'ai',text}],sources:[{id,storeId,approved:true,active:boolean,mode:'current'|'historical',content,modelAllowed:true,validUntil?:ISO}]`. Instrução global e comportamento global são permitidos, nunca escala/nomes de consultores. Citação comercial histórica/pausada/vencida é rejeitada pelo `validateF01` antes de aceitar a proposta. A existência de referência ainda não comprova oferta financeiramente válida.

**F02 task**: `explicitS0Request:true,optOut:false,handoffPlanReuse:false,ownerRoute:'human'|'seller_ai',purpose,maxAttempts,windowStart:ISO,windowEnd:ISO,allowedTemplates:[{id,version,storeId,purpose,active:true,eligible:true}]`. Não conhece slots nem cria templates; a finalidade não determina categoria Meta. Os clocks, o envio, a consentência e C09 são externos.

**F03 task**: `humanClosed:true,closureAuthenticated:true,closureId,personId,cutoffSequence,catalog:[{code,essential}],verifiedWithdrawalSourceIds:[],records:[{id,storeId,personId,caseId,sequence,author,kind:'text'|'media',available,contentAuthorized,content,claims:[{code,value,explicit}]}]`. Históricos de vários casos da mesma pessoa/loja até cutoff; mídia indisponível fica sem conteúdo. `claims` são **atribuições sintéticas** para negativos de conflito; não comprovam que a fonte real é verdadeira. Conteúdo fornecido por modelo só se torna proposta com referência de claims explícitas coincidentes e permanece pendente de análise semântica S0. Divergências de claims independentes resultam em revisão, mesmo se o modelo omitir conflito. Não interpreta depois do cutoff.

## Payload externo e resposta sintética

Payload gerado:
`{schemaVersion:'prumo.openai.provider-input/0.1-candidate', operation, providerTag, instructions, material}`.
F01 `material` possui `modality,context,sources:[{alias,mode,content}]`;
F02 possui `purpose,windowStart,windowEnd,maxAttempts,templates:[{alias,version}]`;
F03 possui `evidence:[{alias,kind,content}],catalog:[{code,essential}]`.
O mapeamento de `src_001`/`tpl_001` para IDs, recibos/versões/autorização/HMAC/nonce/sessões e identidades originais **fica exclusivamente na memória privada**. Aliases e regex não tornam textos livres anônimos: apenas dados previamente selecionados/minimizados por uma futura S0 podem ser entregues.

Resposta sintética obrigatória:
`{schemaVersion:'prumo.openai.provider-result/0.1-candidate',operation,providerTag,state:'completed'|'refused',output}`.
`refused` exige `output:null`. `completed` exige uma destas formas:

- F01: `{text,sourceAliases:[],commercial:boolean,modality:'text'|'audio',handoffAdvisory?:boolean}`.
- F02: `{attempts:[{templateAlias,version,purpose,at:ISO}],finalTemplate:null|{templateAlias,version,purpose,at:ISO}}`.
- F03: `{fields:[{code,value,sourceAlias}],conflicts:[{code,sourceAliases:[...]}],commercialAdvisory:null|{kind:'perdido',sourceAliases:[...]}}`.

Propriedades extras em qualquer nível ou outra operação/tag/versão falham. `tool_calls`, `sent`, `applied`, `vendido`, autorização, credenciais e SQL jamais podem virar efeitos. A resposta `PROPOSED` só devolve os IDs internos à **S0 para revalidação futura**, com `assurance` explicitamente falso. Não há envio, alteração de ficha ou comprovante Meta/bancário.

## Falhas, observabilidade e riscos

Falhas tipadas: `DENIED`, `STALE`, `INVALID_INPUT`, `SCHEMA_INVALID`, `SOURCE_INVALID`, `REVIEW_REQUIRED`, `MODEL_REFUSAL`, `MODEL_FAILURE`, `TIMEOUT`, `QUOTA_EXCEEDED`, `ALREADY_HANDLED`, `REPLAY_CONFLICT`. Negação vence stale; recheck de escopo/versionamento sintético ocorre antes da análise de retorno. Timeout/refusal/quota não fazem retry automático. Exceções não carregam stack, segredos, corpo de resposta, pathname nem campo financeiro. O hash SHA-256 de replay é **detector sintético de igualdade de bytes**, sem assinatura, idempotência transacional ou durabilidade; o `prior` é externo e mutável fora do laboratório.

Limites remanescentes: fixture autenticação/opt-in e `verified` não são provas físicas; texto pode conter PII mesmo depois de projeção; nenhuma moderação/validade semântica foi comprovada; ausência de prova de completude do histórico; nenhum assinador, modelo real, API, telefone, consentimento persistido ou relógio Meta; política de retenção ainda externa. Contratos CFI/F02 e sessão continuam dependências da S0. `evaluateF03CommitCandidate` é guarda separada e seu `S0_RECHECK_ONLY` não faz COMMIT nem prova a integridade do recibo. A38 histórica permanece bloqueada. E02 mantém 70 expectativas documentais sem execução integral.
