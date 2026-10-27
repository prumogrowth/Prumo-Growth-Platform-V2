# Evidências e lacunas verificadas

27/10/2026. Prefixo dos links abaixo: repositório oficial do pedido. SHAs completos, blobs, URLs de cada fonte, metadados/jobs e trechos de logs estão em [EVIDENCIAS.json](EVIDENCIAS.json). Um CI SUCCESS certifica a execução descrita em seu SHA, não a operação comercial nem um HEAD posterior.

## Checkpoints recuperados e atualização

| Fonte | HEAD documental verificado | Executável certificado | CI SUCCESS |
|---|---|---|---|
| E01 F02 / PR #1 Draft | `dc18e41034329647f38737a8d8b87befcdd94eb6` | mesmo SHA | [40480580349](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40480580349) |
| E03 S0 histórico / PR #16 Draft | `b298252c26c69f668b3c3fdb86e9252faff9e44b` | `8be6e194bfb5b8694c1010ff8560c8ec19ed4fd8` | [40405271785](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40405271785) |
| E02 S0/F02 / PR #18 Draft | `88af4aea3aeb2c403bab4c078fdc04d560f2cba0` | `4a3d248d46fad5c195398324b3ee98ae6236365f` | [40414847271](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40414847271) |
| E04 S0 G1 / PR #20 Draft | `4775091ac6207e1593daf1d8fb3b3b3f414224de` | `d53c40a6ef55e82d2282c482b299cff1dbf990bd` | [40434954253](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40434954253) |
| E07 S1 I78 | `8780b576aa18bd3983c063339e2e42d2452af22c` | `f8268bc35c4701a8b522a66504e080628673b11d` | [40475205913](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40475205913) |
| E06 S0/S1 I79 / PR #26 Draft | `8068db1c42216fb1da6855401146eab257f3eff1` | `ab96b5d2d2aae293e239b38bccec82c29dd72a15` | [40484344324](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40484344324) |

As comparações executável→HEAD retornaram apenas documentos. Em PR #18, **o schema result JSON também foi adicionado depois do CI do executável**. O pin final é exercitado pela CI F02 e pelos testes locais; não atribuir ao CI S0 a execução de um arquivo que ainda não existia. No PR #26, contrato/checkpoint/evidências são posteriores ao executável, sem mudança de runtime.

A coleção de branches foi consultada antes e depois da leitura. F02 e S0/F02 permaneceram nos SHAs fornecidos. S1 original está em I78; I79 integrada está em branch própria do principal, não na antiga branch S1. Nenhum contrato F02 posterior que ratificasse a interface foi identificado nessas árvores. Aprovações externas não registradas nessas fontes não foram presumidas.

## E01, E02, E03 e E04 — o que os CIs realmente provam

E01, job `122109964189`: **269 Node/S2**, **84 S0 Python**, **718 F02/F03 Python**, com sucesso. São suítes distintas, com fixtures e regressões de natureza diferente; não somar como jornadas únicas ou chamar todos os 718 de testes físicos. Fontes: `scripts/run-s0-f03-pg17-local.sh`, testes F02 e contrato de coordenação no SHA F02 acima. O run é `pull_request`, com `head_sha=dc18e410…` conferido pela API.

E02, job `121894443928`: 264 unitários; 18 famílias Auth/REST e dez cenários CFI originais; **56 CFI/F02 = 32 CFI + 24 F02**, **19 histórico S0 + 19 com I63**. GoTrue/PostgREST/PG17 reais em stack descartável, atores/dados fictícios. Logs mostram sucesso e remoção da stack. Fontes no PR #18: `backend/s0_f02_review_registry_local.py`, `supabase/tests/s0_f02_review_registry_local_only.sql`, `integration/f02/test_authoritative_review.py`, `docs/contratos/f02_s0_review/CONTRATO_CANDIDATO_0_1.md` e `ENCAMINHAMENTO_F02.md`.

E03: barreira SELECT de sessão em onze objetos, `supabase/tests/s0_history_session_gate_local_only.sql`. A próxima instrução READ COMMITTED depois de revogação confirmada é negada. A leitura é READ ONLY e usa snapshot; não promete interromper query já em execução nem recolher bytes/cache. Não equivale à política de download/mídia/D3/D4.

E04: G1 manual tem 36 cenários GoTrue/PG/PostgREST, mesma fila e exceção I61 por caso/atribuição. Fontes: `backend/s0_g1_manual_queue_local.py`, `supabase/tests/s0_g1_manual_queue_local_only.sql` e `docs/contratos/g1_issue17/CONTRATO_G1_MANUAL_V1.md` no PR #20. Encaminhamento G1 não é ato de ratificação F02. A ponte owned por postgres é restrição explícita de laboratório, não owner hospedado aprovado.

## E05 — compatibilidade real e discrepâncias documentais

O pin F02 `docs/contracts/upstream/OAI_S0_F02_REVIEW_RESULT_SCHEMA_0_1_PINNED.json`, o schema S0 `docs/contratos/f02_s0_review/result.schema.json` e a cópia herdada por I79 têm o mesmo blob **`61598ba702dc03f9f715673118c88f9359e64113`**. O resultado tem 13 estados, `revision` como string decimal e flags operacionais sempre falsas. O adapter F02 também limita revisão a int32; a regex isolada do schema não substitui esse limite.

Três módulos são byte a byte iguais em F02/S0/I79:

| Arquivo em backend/ | Blob Git |
|---|---|
| `f02_reconciled_human_authorization_handoff.py` | `ef6803df9d97b3fe3ad804669fc5be17555fbdbe` |
| `f02_reconciled_review_lifecycle.py` | `11a9e71eabefdf63195fd01a431d1bf19c603ee3` |
| `f02_reconciled_review_recovery.py` | `b049b9765e9126ad4230ece85009689f2d49473b` |

`backend/s0_f02_review_registry_local.py` também permanece igual entre PR #18 e I79: blob `b288db3c8d1160d6c38ca35508726028ea156644`. A I79 não acrescentou ratificação F02 silenciosamente.

O handoff F02 cita `84d76c…` como fonte anterior; o manifest de gates cita `dcac0d…` como baseline, e o contrato S0 descreve corte F02 `a7ba0136…`. São proveniências históricas, não incompatibilidade automática. Para coordenação nova, usar o snapshot atual sem reescrever essas fontes históricas. O contrato de coordenação anterior menciona 1.056 verificações em CI anterior; o run atual tem os grupos acima.

Os três hashes permanecem distintos: snapshot CFI, hash F02 não assinado e hash do documento integral S0. O hash F02 não inclui a janela; a S0 vincula o documento integral com janela no HMAC/idempotência. A S0 usa loja+ator+chave, não exclusividade por encerramento. Referência e cursor não são bearer.

## E06 e E07 — I79 substitui a lacuna técnica antiga, não G04

Fontes I79: `backend/s1_professionals_local.py`, `supabase/tests/s1_i79_profissionais_local_only.sql`, `integration/i79/test_professionals.py`, `.github/workflows/exp-s0-s1-i79-professionals.yml` e `docs/contratos/i79_g2/CONTRATO_E_CHECKPOINT.md`. O job `122122262229` confirma 280 unitários, 56 CFI/F02, 19+19 histórico, 36 G1 antes e **62 = 36 G1 + 26 I79** depois do delta. Job `122122262376` confirma regressões S1/PG17 separadas. Os números herdados/repetidos não são testes novos.

**Lacuna de composição:** no workflow e nos logs, os 56 CFI/F02 e o histórico rodam antes de `Install I79 authoritative professional foundation atomically`; depois rodam os 62 G1/I79. Não há prova nesse run de registro/revisão F02 executados após instalação I79 ou concorrendo com transferência de chefia. Esse teste adicional deve compor a suíte existente, não reconstruir a I79.

I78 tinha oito verificações SQL de bancada e helper temporário, documentados em `docs/S1_002_I78_G2_CHEFIA_DIRETOR_2026_10_27.md`. A I79 posterior fornece administração autenticada/cargo explícito e invariantes adiadas. Não pedir novamente à antiga frente S1 que implemente esses componentes. O checkpoint integrado mantém legado, desligamento, borda/UI e homologação abertos; D1/A2 funcionais já aprovados não precisam ser reabertos. D1–D4 **UI CFI** são outro conjunto de decisões.

## E08 — mapa das quatro provas, sem promover digests

| Campo alegado | Código existente F02/F03 a mapear | Lacuna na recepção S0 |
|---|---|---|
| `f03_receipt_sha256` | Recibo/contexto CFI; `s0_f03_history_manifest_local.py`, `s0_f03_crossfront_evidence_local.py` e cadeia de resultado F03 do laboratório | Identificar qual recibo F03 final é o objeto canônico, seu ID, versão, canonicalização, cutoff e verificador; recibo CFI sozinho não é F03 completo |
| `c08_local_witness_sha256` | `S0F02LocalLegacyCancellationWitness.inspect_and_seal` em `s0_f02_legacy_cancellation_witness_local.py` | Resolver e revalidar testemunha local na fonte atual; não tratar como cancelamento Meta |
| `origin_ledger_sha256` | `S0F02LegacyObservedOriginBridge.inspect`, `s0_f02_legacy_observed_origin_local.py`, ledger AFTER do laboratório | Provar completude/corte e origem observada; não aceitar data retroativa alegada |
| `human_intent_sha256` | `S0F02LocalPostHumanIntentStore.record`, `s0_f02_posthuman_intent_local.py` | Intenção sintética auditada não é decisão operacional do Gestor; ligar ao futuro ato aprovado sem confundir provas |

Todos os arquivos da tabela estão no SHA F02 `dc18e410…`, com blob/URL no inventário. A CI E01 comprova as suítes desse laboratório, não sua composição com PR #18. Em `integration/f02/test_authoritative_review.py::test_33_intake_is_durable_but_claimed_witnesses_never_gain_authority`, o registro físico S0 aceita e armazena `b*64` como alegação C08 e fica `PENDING_EVIDENCE`. É prova explícita do limite, não uma falha de autenticação do pedido técnico.

Em `test_34_new_broker_recovers_server_withdrawal_without_client_timeline`, só o objeto registry é recriado; binding/gateway externos permanecem. Isso prova durabilidade de retirada, não reconstrução de binding perdido. Os testes 38, 46–48, 50–52 cobrem sessão, prazo, regressão de relógio, lead/canal e corrida retirada/leitura dentro do contexto existente.

## E09 e E10 — Meta posterior foi considerado

PR #14, HEAD `31bb84fa524f4ecfdf02360988471d7f989506d7`, `docs/contratos/meta_s0/CONTRATOS_CANDIDATOS_0_1.md`: DISPATCH-01/02, ACK-03 e LOCK-04 ainda candidatos. CI [40370618576](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40370618576) confirmado SUCCESS no executável `92703c34fd4a2b9bae0d00768969c7c53cc16da3`; 52 modelos novos + 161 regressões são descrição da evidência existente, não reexecução nesta auditoria.

`docs/integracao/S0_META_DECISAO_INTEGRACAO_20261026.md`, SHA `450dcd645f35d4c8bf93e974e75d3b09467965a7`, permite reaproveitamento experimental com adaptações e bloqueia operação. Não confundir composição forense PG com dispatch F02/GoTrue+Meta.

TEMPLATE-CATALOG-05 em `d453a22f7160c4e9ff146d21aebe0c2679c9840a`, `docs/contratos/meta_s0_template_catalog/CONTRATO_CANDIDATO_0_1.md`, mantém T1–T6 pendentes. Avanços posteriores encontrados: PR #21 observação por ID `ec4b9002677f593e09afa84520756e7fbea56304`; #22 páginas de templates `e08a8b3ec216bcb45be0e6dc1514ecb1e4ade943`; #24 botões `008b869e20d71f80be81e55dd31d4342d427219f`; #25 listas `b0ac7959cbe21b8bf1d6d663e7e5a72c7439825b`. Títulos/descrições atuais declaram offline; nenhuma dessas descrições ratifica fonte produtiva, M2M, consentimento ou envio. Não se declara revisão integral do runtime de todos esses PRs.

## E13 — avanço Frontend posterior encontrado na conferência final

A branch `codex/fv-ux-01-comunicacao-20261027`, HEAD `4f03396467a9ce6fc927671a8b4b66a3ea101e79`, apareceu na consulta final de refs às 07:15:45 de 27/10/2026 (America/Sao_Paulo). Foi lido `frontend/docs/97_FV_UX_01_CODEX_IMPLEMENTACAO_E_PREVIA_2026_10_27.md` e comparado o diff com a base `8c9498d…`. O documento mantém D1–D4 candidatos e declara que a entrega de composição/emoji/áudio é local, sem transporte, DTO produtivo ou autenticação. Não resolve lookup F02, ratificação ou retenção produtiva. A prévia e seu CI são trabalhos da frente; não foram reexecutados nem publicados por esta auditoria. Esse avanço não muda os estados G02/G04/G06 nem gera pedido adicional ao Frontend.

## E11 e E12 — verificação desta auditoria e limite de G07

Reexecução local: nove módulos `unittest` puros F02, **197 testes OK**, sem banco, Auth ou rede nos testes. A verificação adicional de fontes confere blobs reais, schema pinado, igualdade dos módulos e rastreabilidade da matriz; reprodução em `verificar_auditoria.py`. Não foi iniciado Docker/Supabase nem aplicado SQL nesta execução.

A16 (jornada), A17 (ratificação real) e A18 (agendamento/última milha) seguem `INTEGRATION_PENDING` em `docs/contracts/OAI_E04_F02_ACCEPTANCE_MATRIX_V1.json`. `OAI_E04_F02_S0_JOINT_GATES_V1.json` conserva sete bloqueios. Suites S2 F01/F02/F03 juntas no job não demonstram handover real→quatro produtores→registro S0→ato gerencial→recuperação sob revogação. Essa ausência mantém G07 pendente; a classificação parcial dos outros gates não edita nem libera os blockers originais.
