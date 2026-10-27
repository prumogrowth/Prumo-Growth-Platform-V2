# UI ↔ S0 / CFI-01 — contrato mínimo 0.1-candidate

26/10/2026. **CANDIDATO NÃO RATIFICADO.** S0: continuidade do PR #9, checkpoint executável preservado `1b4f2841d513fb971c93379636414bf686784beb`, HEAD documental `ff623482`. Branch desta proposta: `exp/s0-ui-cfi01-contrato-candidato-20261026`.

Esta proposta tem validadores executáveis e testes, sem endpoint, autenticação nova, dispatch, SQL, lookup de recibo ou ativação de botão. Não é aceite de produto nem integração operacional com Frontend. É uma proposta concreta para revisão conjunta; a existência de código não ratifica nenhuma convenção candidata.

## Fontes atuais recuperadas

| Frente | Checkpoint consultado | Evidência pertinente |
|---|---|---|
| S0 / PR #9 | `ff623482fca0eb1857a64b51959e3716bc0216d7` | Runtime atômico `1b4f284`, contrato estrutural anterior, fachada/ponte CFI e metadados privados |
| Frontend | `456bee6355bcf3c99b94754809f5a93a23b25004` | Docs 07/08 com emenda funcional vigente; FVA-02/doc 92; `s0-command-result.mjs`, blob `044cfb95fee6eb8916dadf7de6f77aecdd3d2471` |
| S1 | `e868b5dbd98b107f4ebd3f9f7087e24ec8518dbe` | Gate de equipe/concessão existente; I75C/G3 continua parcial; export parser blob `cb9fb9cf541308fdec1c5c21f6ee02a7a6675145` |

Os módulos Frontend/S1 exercitados são byte a byte os mesmos blobs nas fontes já fixadas em `backend/tests/compat_sources/`. `integration/ui_cfi01/source_manifest.json` registra a conferência desses caminhos nos HEADs atuais; o CI verifica os hashes das fontes testadas. FVA-02 ainda descreve uma demonstração sem Auth/API e não é evidência de integração. Nenhuma branch alheia foi alterada.

**Incompatibilidades confirmadas:** a UI propõe `expected_case_version`; o executor exige `expected_cycle_version`. O classificador UI aceita C11/C12/C15–18, não CFI-01. O recheck SQL precisa do evento, chave lógica e binding S0, que não estão na projeção pública atual. Não converter versões, reutilizar C13 ou aceitar binding deserializado do browser.

## Escopo e versões do protocolo

- Comando: `prumo.s0.cfi01.command/0.1-candidate`.
- Resposta: `prumo.s0.cfi01.result/0.1-candidate`.
- Identificadores candidatos reutilizam os nomes físicos existentes: `capture_human_closure` e `recheck_human_closure`. Nenhum alias C10/C13/C15 é criado.
- A versão deve coincidir exatamente; versões futuras/produção não são aceitas por esse parser. Mudança incompatível de nomes, significado ou campos exige versão distinta e revisão dos consumidores.
- JSON UTF-8; objetos de chaves exatas, sem campos extras. O decoder candidato S0 recusa nomes repetidos, inclusive depois de escapes, NaN/Infinity, UTF-8 inválido, BOM e corpo maior que 4096 bytes. Esse limite é uma proposta de envelope pequeno, não SLO produtivo. A referência JS valida objetos já decodificados; **não** afirma detectar duplicatas perdidas por JSON.parse.

## Comando mínimo

| Campo | Tipo/perfil candidato | Significado |
|---|---|---|
| `schema_version` | Literal acima | Versão deste envelope, não versão do caso ou banco |
| `command` | Dois nomes acima | Captura técnica ou recheck; sem conclusão comercial |
| `request_id` | UUID canônico minúsculo | Uma tentativa de comunicação; gerar outro em nova tentativa. UUIDv4 é recomendação de geração, não autorização |
| `correlation_id` | UUID canônico minúsculo | Correlação do fluxo captura/recheck; pode permanecer nas tentativas. Não vira evento nem chave idempotente |
| `case_ref` | UUID canônico no perfil candidato | Referência solicitada; S0 resolve a concessionária e confere permissão. Caso opaco não UUID exigiria outro perfil/binding aprovado |
| `idempotency_key` | Regra existente: 8–128, `[A-Za-z0-9._:-]` | Identidade lógica do pedido; preservada no retry do mesmo intento. Não é nonce, request_id ou credencial |
| `expected_version` | Exatamente `{kind,value}` | Discriminador explícito para impedir confusão entre caso e ciclo |
| `capture_request_id` | UUID, **somente recheck** | Referência candidata à tentativa de captura; não é recibo, evento, bearer ou binding validado |

`expected_version.kind='case'` carrega token opaco de 1–128 caracteres `[A-Za-z0-9._:-]` neste perfil; **permanece CASE_VERSION_BINDING_REQUIRED**, sem payload físico. O tipo/gramática definitivo e a fonte desse token precisam de aprovação.

`kind='cycle'` carrega decimal **string** canônico 1..9223372036854775807, sem sinal, zeros à esquerda, expoente ou coerção. O perfil permite testar roundtrip explícito para o payload físico existente, preservando int64 além de Number.MAX_SAFE_INTEGER. **Não significa que a UI já receba ou possa usar versão de ciclo**; isso depende de uma leitura autorizada e do contrato D2. Número JSON, mesmo pequeno, não é aceito nesse campo candidato.

Não há versão inventada de atribuição, ficha, catálogo ou identidade. O backend atual revalida atribuição e snapshot, mas isso não produz versões desses outros agregados por derivação.

Campos de identidade/permissão/loja, JWT, nonce, assinatura, hash, transcript, watermark, flags de envio/aplicação e `closure_event_ref` são recusados no envelope. Autenticação pertencerá ao transporte aprovado e será validada pelo backend, não por um booleano no corpo.

### Exemplos verificáveis

`EXEMPLOS_0_1_CANDIDATE.json` contém comandos completos de captura/recheck e respostas com fingerprint calculado. Todos os identificadores são sintéticos. A captura usa `kind=case`, portanto sua resposta ilustrativa é **CONTRACT_PENDING**; não houve gravação. A resposta de recheck é apenas exemplo de forma candidata, não prova de lookup ou execução. Os quatro comandos válidos e 30 negativos em `integration/ui_cfi01/golden_vectors.json` fixam o perfil entre Python e JS.

## Resposta mínima e exibição

Chaves exatas: `schema_version`, `command`, `request_id`, `correlation_id`, `case_ref`, `request_fingerprint`, `outcome`.

`outcome` contém somente:

```json
{"state":"CONTRACT_PENDING","commercial_effect_confirmed":false}
```

Estados técnicos candidatos, reaproveitando a projeção existente:

| Origem física ou situação | `outcome.state` |
|---|---|
| Captura `CAPTURED_LOCAL_ONLY` ou `ALREADY_CAPTURED` | `RECORDED_REVIEW_ONLY` |
| Recheck `VERIFIED_REVIEW_ONLY_LOCAL` | `RECHECKED_REVIEW_ONLY` |
| Binding caso/ciclo ou contrato ainda pendente | `CONTRACT_PENDING` |
| Sem conversa/snapshot duplicado para revisão | `REVIEW_REQUIRED` |
| Recusa, versão obsoleta, indisponibilidade ou entrada inválida | `DENIED`, `STALE`, `UNAVAILABLE`, `INPUT_REJECTED` |

Captura não aceita resultado RECHECKED; recheck não aceita RECORDED. APPLIED, ALREADY_APPLIED e alegações de persistência comercial são recusadas. O campo false não nega que possa existir recibo técnico no banco: significa que **não há confirmação de aplicação em ficha, venda, banco ou envio**. Não incluir effect_id, versão de ficha, credencial ou metadados internos do recibo.

`candidate_response` é um construtor puro de forma, usando `completion_review_projection` existente. Seu chamador deve fornecer estado vindo do backend confiável quando a integração for aprovada; fabricar um dicionário não prova que ocorreu commit. A referência visual devolve sempre `has_verified_effect=false` e `may_execute=false`, inclusive quando a forma é aceita para exibição candidata.

## Correlação, fingerprint e contexto obsoleto

`request_fingerprint` é SHA-256 UTF-8/ASCII de JSON compacto da tupla ordenada:

```text
[schema_version,command,request_id,correlation_id,case_ref,idempotency_key,
 expected_version.kind,expected_version.value,capture_request_id ou "-"]
```

Todos os valores desse perfil são ASCII, e Python/JS geram os mesmos bytes. A ordem das chaves do objeto não altera o fingerprint; nenhum valor é normalizado ou arredondado. O hash não é assinatura, autenticação, prova de execução ou autorização. Não é `snapshot_sha256`, digest F03 nem HMAC SQL, e não os substitui.

Antes de exibir, conferir comando, ambos os correlatores, caso, fingerprint completo e o esquema/estado. Isso também vincula a resposta à precondição, chave lógica e referência de captura originais. Resposta de tentativa anterior não é aceita contra a tentativa atual, mesmo com a mesma chave lógica.

A UI deverá manter **geração de contexto local**, nunca enviada como fato de autorização: trocar ator, loja, caso, versão observada, tentativa ativa ou sair/retornar à mesma tela invalida a geração anterior. Use novo UUID por geração, sem restaurar o antigo ao voltar. Não use actor_id real ou concessão como token de contexto.

`stage_response` recebe gerações locais de envio/atual. A referência Web Crypto recebe `getCurrentContext` e relê a geração **depois do await**, pois o contexto pode mudar durante o hash. Isso trata a lacuna de resposta tardia coerente com FVA-02; não modifica nem testa um botão conectado no app atual. O callsite Frontend ainda precisa adotar a invalidação; o validator não consegue observar sozinho a troca de tela/ator.

A detecção de versão obsoleta em dados do domínio continua no recheck/CAS atômico já certificado no PR #9. Aqui se prova consistência de forma/correlação e recusa de resposta antiga; não se afirma ter consultado a versão viva do banco.

## Idempotência e recheck: o que já foi resolvido

- `compare_retry` compara somente tentativas do **mesmo comando**: mesmo intento e mesma chave → `SAME_INTENT_STRUCTURE_ONLY`; mesma chave com alteração de caso/precondição/referência → `IDEMPOTENCY_CONFLICT_REVIEW_REQUIRED`; chave diferente → `NEW_INTENT_REVIEW_REQUIRED`.
- Mudar request_id/correlation_id não cria outro intento. O fingerprint de transporte muda, mas a comparação lógica continua igual. Isso não é cache, ledger persistente, detector global de chaves ou garantia de exactly-once.
- **Recheck não é retry de captura.** O SQL existente exige a chave original da captura. O comparador retorna `DIFFERENT_COMMAND_NOT_A_RETRY` entre as duas operações; não transforma essa reutilização legítima em conflito. Cada invocação física continua usando nonce novo no backend.
- O escopo e a semântica efetivos de repetição permanecem os do executor S0 por caso/concessionária, usuário/sessão e snapshot; a chave isolada não atravessa identidade nem concessão. Este módulo não altera constraints ou regras transacionais.
- Timeout/UNAVAILABLE não prova rollback nem commit ao chamador remoto. Não há retry automático nesta proposta. O futuro transporte deve manter a chave lógica para uma repetição explicitamente segura e reautenticar/revalidar no servidor.
- `prepare_physical_capture` só prepara um DTO estrutural para captura explicitamente `kind=cycle`. Caso fica pendente; **todo recheck fica RECHECK_SERVER_BINDING_REQUIRED**. Não resolve UUID de request para evento, não aceita recibo JSON e não chama o gateway.

O banco atual não armazena request_id/correlation_id da UI na auditoria CFI. A correlação proposta existe no envelope/fingerprint, não foi falsamente declarada durável. Aprovar D3 antes de adicionar o binding/correlação ao modelo S0 existente; não criar um registry paralelo por suposição.

## Quatro decisões para aprovação conjunta

| ID | Alternativas | Recomendação e justificativa | Aprovação pendente |
|---|---|---|---|
| D1 — comando/resposta | Envelope CFI separado; ou ampliar o classificador conceitual atual da UI | **Separado e versionado**, com os dois nomes técnicos e estados acima. Evita reutilizar C11/C13/C15 e confundir recibo com ficha aplicada. Ratificar nomes, UUIDs, limite e texto visual | S0 + Frontend/produto |
| D2 — precondições | Manter expected_case_version plano; discriminador case/cycle; ou token opaco S0 de um vetor futuro | **Discriminador explícito e int64 decimal string**. UI permanece case até haver fonte/binding autoritativo; ciclo só se uma leitura aprovada o fornecer. Não aprovar alias caso=ciclo. Versões de ficha/atribuição/catálogo separadas | S0 + Frontend, S1 para escopo afetado |
| D3 — recheck/correlação durável | Lookup S0 por capture_request_id; handle opaco devolvido pelo S0; ou expor UUID interno de recibo sob revisão específica | **Binding server-owned com lookup**, reaproveitando recibo/auditoria atuais e autenticação viva. Evita transportar metadados internos ou criar novo bearer. Definir retenção, escopo ator/sessão/caso, associação de retries e persistência dos correlatores; nada disso implementado aqui | S0 + Frontend/S1/privacidade |
| D4 — autenticação/transporte e elegibilidade | Bearer GoTrue por transporte TLS; ou sessão HTTP-only via backend, se essa arquitetura for escolhida | **Reutilizar GoTrue e o executor restrito existentes**; para o desenho atual, Bearer validado pelo servidor é a opção mais direta. Cookies exigiriam avaliação de CSRF/sessão. Concessão, equipe ativa e atribuição continuam gates vivos; supervisor não ganha ação por conseguir ler. Mapear rótulos UI aos gates existentes, sem exceções comerciais novas | S0 + Frontend/S1/segurança |

D1–D4 estão **PENDENTES**. Aprovação desta proposta não aprova F03, catálogo/minimização, mídia G3/Issue #10, Meta, Banco, custódia produtiva ou deploy. Essas dependências continuam separadas.

## Implementação e verificação

- `backend/s0_cfi01_ui_contract.py`: parser estrito, loader candidato, DTO imutável, fingerprint, comparação de retry, preparação estrutural limitada e projeção/correlação.
- `integration/ui_cfi01/reference_contract.mjs`: referência de consumidor com Web Crypto e snapshots imutáveis; fora de `frontend/`, sem transporte ou ativação.
- `golden_vectors.json`: 34 vetores compartilhados, incluindo int64 máximo, caso/ciclo, recheck pendente, extras de autoridade, tipos, aliases, controles/newline e estouro de versão.
- `backend/tests/test_s0_cfi01_ui_contract.py` + `probe.mjs`: 15 testes novos com execução dos módulos reais/candidatos, respostas fora de ordem, contexto que muda durante await, raw JSON duplicado e invariantes não comerciais. Checks de hashes das fontes atuais e rejeição pelo Frontend/S1 existentes.
- Workflow próprio `exp-s0-ui-cfi01-contract.yml`: Node22, 171 testes Python ao todo (156 preservados + 15 novos). Sem banco/rede nesses testes. Não reconta as 28 provas GoTrue/PG17 do PR #9 como execução desta missão.

Commits executáveis: `ca6968a6a9120be94234804396e4a18a5ec84bc3` (envelope/compatibilidade) e `99238f8a3304b8cc70ef14421b74842b0740b016` (distinção explícita recheck/retry preservando a chave existente). **CI final [40358081309](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40358081309): SUCCESS no SHA executável `99238f8a3304b8cc70ef14421b74842b0740b016`, 171/171 testes com Node22; logs conferidos.** A execução inicial `ca6968a6` também passou no run 40357750561; o segundo commit refinou a classificação captura/recheck e reexecutou os checks. Sem retries de falha. Evidências detalhadas no JSON adjacente.

Reprodução: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s backend/tests -v`, com Node22+ disponível, no próprio checkout. `node --check integration/ui_cfi01/reference_contract.mjs` verifica sintaxe. Não é necessário instalar driver, iniciar Supabase, chamar provedor ou usar credenciais para esta alteração pura de contrato.

## Estado de integração

**Pronto para revisão conjunta, não para ativação.** Os checkpoints S0 `1b4f284`/PR #9, Meta/PR #7 e I74/PR #6 foram preservados; nenhum endpoint público, DDL, regra comercial ou branch Frontend foi alterado. O classificador Frontend atual continua recusando esta proposta, corretamente.

Próximo avanço após D1–D4: implementar a resolução de binding/correlação no caminho S0 já existente e ligar uma confirmação de UI em sandbox com sessão real. Exigir a regressão transacional do PR #9 mais os novos vetores e testes de contexto. Até aprovação, manter gate de captura UI/recheck bloqueado e não interpretar STRUCTURE_ONLY como permissão de executar.
