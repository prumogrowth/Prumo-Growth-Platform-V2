# S0 — contrato de comunicação: perfis de compatibilidade candidatos

26/10/2026 — PR #4, branch `feat/s0-auditoria-nucleo-operacional-20261025`.
**Proposta técnica executável, não contrato comercial/operacional aprovado.**
Identificador interno: `s0.communication.compatibility/0.1-candidate`.

## Entrega e reaproveitamento

`backend/s0_communication_contract.py` prepara payloads estritos para a captura
CFI-01 já existente, valida metadados de recibo sem lhes atribuir autoridade,
correlaciona saída de revisão S2/F03 e produz projeção técnica mínima candidata.
Nenhum HTTP, SQL, modelo, credencial, escrita de domínio ou serviço é criado.
Os adaptadores existentes das outras frentes permanecem intactos e continuam
responsáveis por autenticação, autorização, HMAC, nonce, locks, CAS e auditoria.

Os testes executam os módulos reais da UI/S2 e validadores S0/S1/PR #1, fixados
por commit e hash. As cópias em `backend/tests/compat_sources/` são somente
fontes imutáveis de teste, não fork de runtime nem importação das branches.
O manifesto registra caminhos, SHA Git de blob e SHA-256 de cada arquivo.

## Fontes recuperadas

| Frente/fonte | Commit fixado | Contrato ou implementação usado |
| --- | --- | --- |
| S0 CFI-01 | `948891714f632adb6179cf3a11f362a6eb914f91` | Captura/recheck atômico, DTO `S0InternalReceiptLocal`, allowlist `_CAPTURE_FIELDS` e validador `ClosureRequest` |
| S1 | `84c8eba8c92054458ff224cc781a2e368710319c` | `backend/s1_gateway_export_local.py`; parser separado, ator/sessão de GoTrue, sem aceitar payload CFI como exportação |
| Frontend | `6d245d11e23bb3b0918d8594e87d242f2fbad815` | `s0-command-result.mjs`, contrato documental 07/08 e UQ/read; resultado candidato, sem transporte/autorização |
| S2 | `ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c` | `f03-commit-gate.mjs`: saída `S0_RECHECK_ONLY` com `fieldCodes/snapshotRef` |
| PR #1 OpenAI/F03 | `631d8eca3a5ba93c1d7ce40f1a9eb555071b7104` | `_candidate`, `ProposedField/proposal_digest`, vetor de versões e ponte física; revisão local, não executor |
| PR #2 Meta | `54d790dc7eb2cf73c564ad0cfea0496554bf9287` | Interface forense WA39–66, bytes/HMAC/event_ref/body_sha256, sem ACK/envio/permissão comercial |

PR #1 continua Draft contra a pré-validação S0; PR #2 continua Draft contra a
fundação. Recuperados também os contratos da coordenação CFI-01/CF-OP-02,
conciliação FV/E01/OAI-05/07 e a atualização de responsabilidade do núcleo S0
na descrição do PR #2. Não foram incorporados commits de nenhuma dessas branches.

## Vocabulário e quem pode fornecer os fatos

| Informação | Fonte/consumidor | Semântica e validação compartilhável |
| --- | --- | --- |
| `case_ref` | UI solicita; S0 resolve e S1 autoriza | UUID canônico no perfil físico local; não implica permissão |
| `expected_cycle_version` | Captura S0 | Inteiro PostgreSQL 1..2^63−1; versão de `ciclos_comerciais`, não versão de caso |
| `expected_case_version` | Intenção FV candidata | Sem binding físico aprovado; não converter para versão de ciclo |
| `idempotency_key` | Solicitante/S0 | Chave de 8–128 caracteres do alfabeto já aceito pelo gateway atômico; não é `request_id`, nonce ou autorização |
| `request_id`, `correlation_id` | Correlação UI/S0 | Ficam separados de idempotência e evento; não são autoridade nem são reenviados ao gateway físico sem contrato |
| `actor_id`, `session_id`, papel | Identidade autenticada S0/S1 | Nunca recebidos como fatos confiáveis do browser/IA; credencial não passa por este módulo |
| `store_ref`/`scope_ref` | S0 resolve tenant, S1 confere | Não mapear alegação de escopo do browser para concessão; loja não é equipe |
| `assignment_ref` | UUID físico S0/S1 | Identifica atribuição; não substitui versão de atribuição nem escopo excepcional por caso |
| `closure_event_ref` | Recibo interno S0 | Evento durável, não token; não mapear automaticamente `trigger_ref`/`closure_event_id` de exemplos OAI |
| `snapshot_sha256` | Recibo S0 | Digest do snapshot de mensagens do caso; não é HMAC, autenticação nem digest de metadados selados |
| `message_watermark` | Recibo S0 | UUID da última mensagem na ordenação S0; não é sequência numérica S2 |
| `message_count` | Recibo S0 | Contagem 1..2500 do binding existente; não permite obter conteúdo |
| `snapshotRef` S2/PR #1 | S2 devolve; S0 revalida | PR #1 compara com `metadados_sha256` de conteúdo selado, não com `receipt.snapshot_sha256` |
| Vetor de versões | S0-owned fixtures/validadores | PR #1: ficha, catálogo, caso, atribuição, identidade; S2 inclui ciclo separadamente. Nenhum valor é fabricado a partir de outro |
| `fieldCodes` | S2 propõe; S0 confere | Códigos únicos ordenados; interseção com S0 atual: 1..12 códigos `[a-z_]{2,48}`. Valores/fontes continuam no validador existente de `ProposedField` |
| Estados técnicos | S0/Frontend/F03 | Captura/recheck/revisão são distintos de aplicação em ficha, venda, banco ou envio |
| Meta `event_ref`, `body_sha256` | Fronteira Meta e S0 forense | Identidade do evento e hash dos bytes são distintos. Status/timestamp participam da identidade; variante JSON não deve ser apagada por canonização |

## Perfis implementados e incompatibilidades reconciliadas

### 1. Captura física existente — sem remapear versões

`prepare_request(CAPTURE_PROFILE, raw)` exige exatamente `case_ref`,
`expected_cycle_version`, `idempotency_key`. Em entrada válida retorna
`STRUCTURE_ONLY` e um DTO imutável; `to_physical_payload()` preserva o payload
que o gateway S0 existente já aceita. Campos de ator, sessão, loja, grants,
catálogo, ficha, flags de envio e aliases são recusados. DTOs construídos
manualmente também são revalidados ao serializar.

`prepare_request(FV_INTENT_PROFILE, raw)` reconhece a intenção candidata com
`expected_case_version` e mantém **`CASE_VERSION_BINDING_REQUIRED`**, sem payload
encaminhável. Não traduz `request_id` para idempotência nem inventa versão de
ciclo, ID de atribuição ou autorização. Perfis desconhecidos são recusados.

A incompatibilidade numérica é tratada explicitamente: Python/Postgres preservam
inteiros até 2^63−1, mas JSON em JavaScript não representa exatamente inteiros
maiores que 2^53−1. `to_js_payload()` bloqueia esse intervalo; não arredonda nem
transforma silenciosamente em string. A futura serialização decimal tipada
precisa ser ratificada pelos consumidores antes de entrar no wire contract.

### 2. Metadados e staleness — sem recibo falsamente verificado

`parse_receipt_metadata` aceita somente os oito campos físicos existentes,
sem conteúdo, credencial ou poder adicional. `compare_receipt_metadata` compara
todos eles, incluindo tenant/caso/evento/atribuição/watermark/contagem, e devolve
`UNCHANGED_STRUCTURE_ONLY` ou `STALE_REVIEW_REQUIRED`. Igualdade estrutural **não
substitui** o `capture_internal_receipt/recheck_internal_receipt` autenticado,
a assinatura e a consulta transacional às permissões vivas. Não se entrega esse
DTO como bearer, binding autenticado ou prompt.

### 3. Saída F03 já existente — correlação limitada à revisão

`parse_f03_review_candidate` aceita exatamente
`{status:'S0_RECHECK_ONLY', fieldCodes:[...], snapshotRef:...}` na interseção já
aceita pela S0/PR #1. Rejeita códigos duplicados/fora do perfil, `APPLIED`, valores,
propostas extras ou alegações de envio. `match_f03_review` compara códigos e o
**digest de metadados selados explicitamente nomeado**; resultado positivo é
`MATCHED_STRUCTURE_ONLY`. Não lê ficha, catálogo, mensagens, secrets ou banco.

Os testes executam o gate JS S2 real e passam sua saída ao `_candidate` original
do PR #1 (com `ProposedField/proposal_digest` originais) e ao novo adaptador.
Revogação e versão obsoleta são testadas no gate S2, sem serem convertidas em
sucesso por S0. São fatos sintéticos de teste, não sessões/autorização reais.

### 4. Projeção técnica candidata para UI — sem reutilizar C13

`completion_review_projection` preserva os estados de captura/revisão/negação,
sem IDs internos, snapshot, valores ou dados pessoais. `CAPTURED_LOCAL_ONLY` e
`ALREADY_CAPTURED` viram `RECORDED_REVIEW_ONLY`; recheck vira
`RECHECKED_REVIEW_ONLY`; contrato pendente continua pendente. `confirmed_persisted`
permanece false: não há prova de aplicação de campos de produto nesta camada.

A UI atual permite C11/C12/C15–C18 no seu classificador. **Não existe CFI-01 nesse
conjunto.** Os testes provam que a UI real rejeita esta projeção candidata e que
até um `APPLIED` estruturalmente aceito em C11 continua `hasVerifiedEffect=false`.
Não se usa C13 humano, C10 handoff ou C15 como substituto de conclusão. A decisão
de adicionar comando/projeção CFI à UI permanece aberta; não há botão conectado.

## Autorizações e estados que não podem ser unificados

- S1 equipe/grants/exceção de caso e sessão viva são fatos transacionais. O parser
  S1 de exportação é executado nos testes e não aceita payload CFI ou identidade
  arbitrária. Isso não integra exportação ao fechamento nem certifica sua autenticação.
- Flags JS `authenticated/authorized/tenantAllowed` dos testes S2 não se tornam
  permissão S0. `S0_RECHECK_ONLY`, `VERIFIED_CONTRACT_PENDING`, `CONTRACT_REVIEW_ONLY`
  e `REVIEW_ONLY` permanecem revisão, nunca `APPLIED/ALREADY_APPLIED` comercial.
- Recusa, stale ou indisponibilidade não carregam binding/valores para o browser.
- Principal M2M/nonce/HMAC forense Meta é diferente de sessão GoTrue humana e de
  autorização de escrita de ficha. Todos os flags externos continuam fora desta
  implementação; não há ACK, envio, retry ou alteração comercial.

## Decisões ainda necessárias

1. Aprovar nome/versão do comando e resposta de conclusão CFI-01 na UI/S0; definir
   correlação, idempotência e projeção técnica sem fingir confirmação de ficha.
2. Ratificar fonte e binding das versões de caso, ciclo, atribuição, ficha,
   catálogo e identidade. Definir serialização sem perda para versões int64.
3. Ratificar corte, minimização/LGPD e formato de evidências OAI-05/07, campos
   permitidos e sua proveniência. Não mapear automaticamente E01 versus OAI-05.
4. Aprovar transporte e executor autenticados, prova independente e rechecagem
   S0/S1 na transação de aplicação; não tornar DTO de compatibilidade uma permissão.
5. Negociar interface forense Meta/M2M, ACK e política de dados separadamente;
   snapshots locais e testes de bytes não homologam credenciais/serviço externo.

## Testes e próximo avanço

Testes em `backend/tests/test_s0_communication_contract.py`, probe Node e fontes
fixadas. Cobrem roundtrip para validador S0 real, allowlists, precisão int64/JS,
staleness de cada dimensão do recibo, digest correto, saída real S2→parser PR #1,
revogação/stale JS, recusa de permissões inventadas, fronteiras de UI e S1 e
integridade de todos os blobs. Sem mocks de funções JS/parser que substituam
os consumidores. O banco/autenticação não é exercitado por esses testes.

**Próximo avanço recomendado:** aprovar o binding de versão de caso/ciclo e o
comando/projeção de conclusão; em seguida, ligar o payload físico preparado ao
`S0CFI01AtomicCommandsLocal` e seu recheck existentes em sandbox único, com
sessão S0/S1 real, preservando fila/grants e conferindo revogação/mensagem nova.
Reaproveitar o runtime e fixtures de pré-validação; não reimplementar fechamento.
Só depois conectar F03 pelo contrato aprovado e revalidar campos na transação.

Validação desta entrega e SHAs executados: `S0_COMUNICACAO_EVIDENCIAS_20261026.json`.
Sem merge, deploy, migração, integrações externas ou alterações em branches alheias.

## Resultado de execução — 26/10/2026

- Commit executável: `e18118a2b997e4f61c3e5f931383e13948d2ca75`.
- Local: **58/58 Python**, incluindo **20 métodos novos** de compatibilidade,
  com Node v24.19.0 para os probes. Sem rede ou banco nos adaptadores.
- [GitHub Actions #40296667385](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40296667385):
  **SUCCESS**, job `121484278477`. **58/58 Python** com Node 22 e runner
  PostgreSQL 17 integral, incluindo migrations/isolamento/concorrência existentes.
  Contagem, marcador terminal e passos foram conferidos nos logs. Sem retry.
- O executor SQL/autenticação não foi modificado; o CI de regressão não transforma
  os testes estruturais de comunicação em autenticação ponta a ponta.
- Limite adicional a ratificar no vetor: S2 admite zero e inteiros seguros JS;
  o validador PR #1 exige versões positivas abaixo de 2^63−1. Este módulo não
  converte o vetor nem escolhe valores substitutos. A interseção das regras deve
  acompanhar a fonte física aprovada antes de conectar o gate operacional.
