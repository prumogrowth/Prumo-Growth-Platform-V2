# S0/CFI-01 — Ponte contratual para conclusão humana e extração F03 | v0.1

**19/10/2026 — [P/R] candidata de engenharia S0/OpenAI, NÃO endpoint homologado nem migração.**
**Mandato limitado:** autorização do responsável para corrigir/desenvolver SOMENTE trechos S0 que bloqueiam a frente OpenAI; a frente WhatsApp/Meta recebeu autorização paralela e **mantém propriedade de transporte/prova do provedor**. Este adendo está em **branch S0 isolada baseada no HEAD do PR #1**, sem editar PR #1, PR #2 ou PR #3, e sem merge.

**Referências existentes:** issue [CFI-01 #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4), E01/OAI-05/OAI-07/OAI-08 e [CFI-01 proposta OpenAI](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s2-openai-adapter-sintetico/docs/integracoes/openai/CFI_01_PROPOSTA_CONCILIACAO_ENVELOPE_F03_v0_1.md); FV-02/FV-03 da frente visual; S0 `docs/CF_OP_02_CONTRATO_NUCLEO_RECONTATO_HUMANO_v0_1.md` e docs 21–23/26. Os nomes de campo abaixo são **proposta de conciliação para revisão conjunta**, não assinatura aprovada por silêncio.

## 1. Atribuições e pré-condições invariáveis

1. **Frontend → S0:** pede conclusão com `case_ref`, versão visualizada e chave idempotente opaca. **Não** fornece autoridade `operator_id`, `tenant_id`, relógio, status, consentimento, snapshot, catálogo, `closure_event_id` nem destino OpenAI.
2. **S0 antes do aceite:** autentica sessão Prumo, concessão válida na mesma concessionária, operador *atual* ativo/atribuído (S1), caso existente, finalidade permitida, ausência de bloqueios normativos, versão CAS e idempotência. Uma conclusão é **evento técnico do caso humano**, não C10, C13 ou novo status comercial. A janela operacional Meta e a da UI continuam distintas.
3. **S0 forma F03:** gera `closure_event_id`, `request_id`, `conversation_snapshot_ref/hash`, corte de mensagens (watermark + event seq autorizado), `case_version`, `form_version`, `allowed_fields_catalog_version` e `policy_versions`; filtra somente mensagens autorizadas do **mesmo caso/loja** e retém minimização. O hash não é autenticação isolada.
4. **Adaptador OpenAI:** recebe operação `human_close_extract` para propor valores **com fontes**, lacunas/conflitos, desfecho conversacional e eventual `followup_need_advisory`. NÃO grava ficha, chama Meta, cria plano ou toma decisão sobre Banco. A IA Vendedora continua definitivamente suspensa para aquele caso depois de handoff.
5. **S0 após F03:** valida *individualmente* cada campo contra catálogo/tipo/classificação/proveniência/autoria, snapshot/versões não obsoletos, autorização atual, política de dados e conflito. Aplica automaticamente apenas elegíveis com **autoria técnica identificável**, em transação/idempotência próprias, e preserva correções humanas. Campo essencial faltante causa pendência explícita; opcional ausente NÃO força devolução. Remessa bancária/venda/negativa nunca se seguem automaticamente da resposta.
6. **F02 separada:** `followup_need_advisory` é mero parecer. Para nova cadeia pós-humana, S0 precisa de decisão independente, nova identidade de plano, allowlist/template versionada, consentimento/opt-out/capacidade, atribuição atual e validação contra template manual concorrente. Jamais ressuscitar plano C08/C10 cancelado.
7. **Novo caso humano pós-`vendido`:** S0/S1 preservam ciclo histórico vendido. F03 exige snapshot/finalidade do **novo** atendimento; não reaproveita ficha do ciclo vendido. F02 comercial fica bloqueada sem novo ciclo e autorização explícita, mesmo que o cliente tenha voltado.
8. **Atualização S1-002/I11 [D] (19/10):** gerente/gestor Prumo coordena sua **equipe de operadores**, não possui necessariamente concessão da concessionária. Os **responsáveis da plataforma** configuram grants individuais operador→loja e fazem desligamento definitivo. O gestor pode pausar/reativar o operador INTEIRO por ausência, afetando todas as lojas atendidas sem revogar grants; S0 valida simultaneamente identidade/sessão, estado global ativo, grant ao caso/loja e atribuição atual antes de qualquer F03/F02. Gestão por equipe não é permissão implícita sobre cadastro da concessionária. Política de novo receptor dentro ou fora da equipe ainda [R].

## 2. Mapa de compatibilidade para decisão [R]

| Designação E01 antiga | Candidata de fronteira S0 ↔ OpenAI | Regra de migração |
|---|---|---|
| `trigger_ref` | `closure_event_id` | S0 cria e valida após conclusão humana; aliases antigos apenas no **mapeamento interno** versionado, não comandos mistos da UI |
| `scope.concessionaria_ref/caso_ref/conversa_ref/ciclo_ref` | `concessionaria_id/caso_id/conversa_id/ciclo_id` | IDs resolvidos pela S0, nunca aceitos como prova do browser/modelo |
| `expected_case_version` | `expected_version` | Versão CAS de caso distinta de `current_form_version` |
| `authorized_context_ref/context_version` | `conversation_snapshot_ref`, `conversation_snapshot_hash`, `message_watermark` | Cut confiável; verificar mensagens novas e mudanças de atribuição antes da aplicação |
| `fields_policy_version` | `allowed_fields_catalog_version` | Catálogo autorizado S0; classes D3 somente após gate de privacidade/Banco |
| `extraction.field_suggestions[]` | `fields_proposed[]` | Itens de proposta, sem comandos de persistência |
| `field_key/value/evidence_refs[]` | `field_code/proposed_value/source_message_refs[]` | Fonte deve ser fala/transcrição do cliente autenticada daquele mesmo caso |
| `missing_field_keys[]` | `missing_fields[]` | Obrigatoriedade vem S0, não a IA |
| `needs_human_clarification` | derivado pelo S0 | Nunca ordem unilateral do modelo |
| OAI-07 e OAI-08 | `conversational_assessment`, `followup_need_advisory` | Evidência e recomendação silenciosas, sem status/banco/envio |

**Ainda a ratificar:** nome do evento técnico e payload UI↔S0; assinatura final S0↔OpenAI e versão; tratamento de ausência/erros; deadline/retry/idempotência; critérios de reencerramento após novas mensagens; política D3; autorização de suporte pós-venda. Preferir versão explícita do envelope a aceitação permissiva de aliases.

## 3. Exemplo fictício SOMENTE para inspeção contratual

Pedido **construído internamente** pela S0 (nenhum navegador envia essa estrutura diretamente):

```json
{
  "operation_kind":"human_close_extract",
  "contract_version":"s0-openai.v0.2-candidate",
  "request_id":"req_fake_001",
  "closure_event_id":"close_fake_001",
  "concessionaria_id":"loja_fake_A",
  "caso_id":"caso_fake_A01",
  "conversa_id":"conversa_fake_A01",
  "ciclo_id":"ciclo_fake_A01",
  "expected_version":12,
  "current_form_version":3,
  "conversation_snapshot_ref":"snapshot_fake_A01",
  "conversation_snapshot_hash":"hash_fake_opaque",
  "message_watermark":"m_fake_009",
  "allowed_fields_catalog_version":"CAT_FAKE_01",
  "policy_versions":{"privacy":"fake_v1","extraction":"fake_v1"}
}
```

Resposta **candidata**, que S0 nunca aplica cegamente:

```json
{
  "operation_kind":"human_close_extract",
  "contract_version":"s0-openai.v0.2-candidate",
  "request_id":"req_fake_001",
  "closure_event_id":"close_fake_001",
  "snapshot_hash":"hash_fake_opaque",
  "form_version_observed":3,
  "fields_proposed":[
    {"field_code":"campo_demo_modelo","proposed_value":"MODELO FICTICIO A","source_message_refs":["m_fake_003"],"source_kind":"client_statement","certainty":"explicit"}
  ],
  "missing_fields":[],
  "conflicts":[],
  "conversational_assessment":{"conversation_outcome":"INCONCLUSIVE","evidence_message_refs":["m_fake_008"]},
  "followup_need_advisory":{"suggested":"UNCERTAIN","evidence_message_refs":["m_fake_008"]}
}
```

**Nomes/valores de enum ilustrativos.** Nem schema físico nem campos reais do Banco aprovados; o exemplo não prova validação algorítmica ou integração.

### Ensaios offline de fronteira F03 — 19/10/2026 (execução efetiva, escopo restrito)

Foi implementado um **avaliador de proposta sintética SEM efeitos comerciais**, [`backend/s0_openai_bridge/f03_offline_gate.py`](../backend/s0_openai_bridge/f03_offline_gate.py), com a suíte [`backend/tests/test_s0_openai_f03_offline.py`](../backend/tests/test_s0_openai_f03_offline.py). Em ambiente descartável isolado, **30/30 testes unitários PASS**, compilação Python sem erro, e hashes do conteúdo Python conferidos com a publicação na branch.

**Prova somente de laboratório:** catálogo fictício A/C obrigatórios e B opcional (somente no stub); mensagens do cliente têm `asserted_fields` anotados previamente no gabarito fictício, usados para conferir igualdade de valores e origem. **Em produção, citar uma mensagem não comprova a verdade de uma extração.** A anotação sintética não é algoritmo de NLP nem substitui checagem S0/operador sobre texto real ou homologação de dados do Banco. `PROPOSAL_ONLY` e `PARTIAL_REVIEW` não executam `UPDATE`, não remetem cadastro, não registram ato bancário, não acionam F02 nem significam autorização para autoaplicar. O próprio código não possui caminho para SQL, rede ou WhatsApp.

**Grupos testados:** separação obrigatório/opcional; campos explicitamente presentes; negação de campo fora do catálogo; isolamento A/B e caso diferente; fontes de operador/untrusted; valor inventado mesmo com referência; duplo campo/fonte; corte e versão obsoletos; ausência de conclusão autenticada; revogação/pausa do operador (representada por booleano S0 fictício); finalidade pós-venda não comercial; no-op de persistência. O retorno F03 real, assinatura física, modelos, sessão real e autorização de responsável/gestor S1 **não foram testados**.

Reproduzir localmente, sem bibliotecas extras, no diretório raiz do repo: `python -m unittest discover -s backend/tests -p 'test_s0_openai_f03_offline.py' -v`. O repositório PR #8 ainda não tem **CI da branch** confirmada para este incremento; não atribuir PASS de CI.

**I12 da S1-002 (19/10):** movimentação manual entre operadores da equipe exige origem/destino autorizados, grant da mesma loja no destino e `atribuicao_esperada` para recusar replay; pausa global pode concorrer com transferências. F03 precisa comparar a **atribuição ATUAL verificada por S0/S1 no instante de aplicar**, não confiar só no ator que iniciou conclusão. Política entre equipes ainda [R]. A flag fictícia `actor_authorized_now` NÃO implementa esse contrato nem autoriza exposição de SQL/REST.

### Regressão F03 — ambiguidade e aplicação tardia (19/10/2026)

**Achado corrigido no avaliador sintético:** anteriormente uma proposta podia citar uma declaração verdadeira e ignorar outra declaração incompatível do **mesmo cliente** presente no mesmo snapshot. Como a política de precedência/correção ainda não foi aprovada pelo S0, o avaliador agora detecta valores distintos em falas **autorizadas do cliente** para o mesmo campo e **rejeita somente o campo conflitante**. Preserva outros campos provados e não transforma nota especulativa do operador ou fonte não autorizada em contradição. Recusa estruturas malformadas de catálogo/proposta/refs sem lançar erro não tratado. A detecção opera sobre `asserted_fields` **anotados em fixtures fictícias**, não interpreta linguagem real nem resolve retificações semanticamente.

- [F03 avaliador](../backend/s0_openai_bridge/f03_offline_gate.py) e [40 testes de extração](../backend/tests/test_s0_openai_f03_offline.py): **40/40 PASS local**, incluindo dez novas regressões 31–40; nenhuma chamada à API, banco ou Meta.
- [Guarda separada de revalidação de atribuição](../backend/s0_openai_bridge/f03_assignment_recheck.py) e [21 testes de corrida](../backend/tests/test_s0_openai_f03_assignment_recheck.py): **21/21 PASS local**. A função compara evento de fechamento, loja/caso, operador e ID de atribuição, versões de ficha/caso, watermark, hash, catálogo, sessão simulada, estado global ativo, grant da loja e finalidade. Pausa, remanejamento ou nova atribuição ao mesmo operador invalidam resultados antigos. O retorno máximo é `REVIEW_ONLY`, **NUNCA `APPLIED`**.
- **Execução verificável nesta entrega:** `python -m unittest discover -s backend/tests -p 'test_s0_openai_f03*.py' -q` em ambiente temporário isolado: **61 testes executados, 61 PASS**, e `python -m compileall -q backend` sem erro. Arquivos publicados foram comparados por comprimento e checksum FNV-1a com os locais; checksums não substituem revisão formal.
- **Não coberto:** não há credenciais, Auth real, provas bancárias, NLP de modelo, catálogo real de dados, integração S1 I12, transação/lock real ou código de aplicação no banco. A revalidação por flags fictícias NÃO pode ser exposta como endpoint ou tornar-se fonte de autoridade. Assinatura F03 e política de correção seguem [R].
- **Concorrência real:** no futuro S0 deve refazer a verificação na MESMA transação que aplicar campos, sob bloqueio/versionamento efetivo, obtendo identidade e atribuição da S1 e não de payload cliente/modelo. `REVIEW_ONLY` é somente sinal para essa etapa, não permissão de escrita.

### Saneamento adicional de tipos — 19/10/2026

**Problema identificado:** a versão anterior dos stubs Python aceitava potencialmente uma string como `"false"` nos indicadores de autorização F03, por usar truthiness; em Python `bool` também é subclass de `int`, podendo contaminar comparações de versão. No laboratório isso poderia apresentar `PROPOSAL_ONLY` ou `REVIEW_ONLY` com evidência malformada.

**Correção executada nos módulos isolados:** `f03_offline_gate.py` agora exige dataclasses corretas, **booleanos reais** para autorização/snapshot/closure e evidência, **versões inteiras positivas não booleanas**, IDs string não vazios e valores anotados no gabarito como texto. `f03_assignment_recheck.py` valida estritamente sessão, operador ativo, grant, finalidade e indicadores de revisão. Dados malformados retornam `BLOCKED`/`DENY`, sem SQL, Meta, modelo ou exceção de autorização.

**Prova local após a correção:** `python -m unittest discover -s backend/tests -p 'test_s0_openai_f03*.py' -q` → **78/78 PASS** (**50** validação de campos, **28** atribuição); `python -m compileall -q backend` → PASS. Códigos/testes nesta branch foram confrontados por conteúdo e checksum FNV-1a com o laboratório local. **Sem CI de GitHub verificado; não é validação do modelo ou de integração S1/S0.**

**Compatibilidade verificada:** S0 PR #1 evoluiu 7 commits desde o ponto de origem desta branch, alterando docs S0-040/runner, sem modificar os 9 caminhos originais deste PR; Meta PR #2 alterou somente `integrations/whatsapp-meta/` e docs próprias nesse intervalo. **Sem colisão de caminhos**, mas PR #8 permanece atrás do HEAD S0 e precisa revisão de base antes de merge; especialmente a prova técnica Meta `API_ACCEPTED` não equivale a callback autenticado `sent`. Sem adotar arquivos ou resultados Meta como autorização comercial.

### F03-COMP — composição de revisão e titularidade, sem escrita (19/10/2026)

Novo módulo [`f03_review_pipeline.py`](../backend/s0_openai_bridge/f03_review_pipeline.py) na branch isolada do PR #8 **une a revisão de campos do F03 sintético e a revalidação S0/S1 do operador**. A decisão fica sempre em `DENIED | STALE | NOT_READY | REVIEW_REQUIRED | REVIEW_ONLY`; jamais concede `APPLIED`, envio Meta, cadastro bancário ou efeito de persistência.

**Regra adicional de segurança:** os contratos de ambas as revisões têm de corresponder ao MESMO `store`, `case`, `closure_event`, `snapshot_hash`, versões de caso/ficha e catálogo. O resumo da composição inclui somente códigos de campos (nunca valores), preserva indicação de ausência essencial para o humano autorizado e recusa campos/atribuição obsoletos. Se não existem campos válidos mas há campo essencial pendente, a resposta candidata é `REVIEW_REQUIRED`, não mero `NOT_READY`. Nenhum detalhe de pendências é divulgado se o segundo gate devolver `DENY`.

**Prova local verificável e delimitação:** [22 testes novos](../backend/tests/test_s0_openai_f03_review_pipeline.py) executados por `unittest` local: **22/22 PASS**, e compilação Python PASS. A suíte isola a orquestração com **mocks dos dois validadores dependentes**; portanto comprova fluxo, correspondência de envelopes, precedência de resultados e ausência de valores no resumo, **mas NÃO é teste ponta a ponta do F03 real, Auth, S1 I13, banco, Meta ou API OpenAI**. A fonte `asserted_fields` continua ficcional. Comandos locais: `python -m unittest discover -s backend/tests -p 'test_s0_openai_f03_review_pipeline.py' -v`. O código publicado foi comparado ao executado por tamanho e hash de conteúdo, não substitui CI.

**I13 S1-002:** gerente/coordenador ativo e vínculos gestor→operadores são validados sob trava na transação pela S1 na migração sintética 050; nenhum desses locks foi implementado neste módulo. A S0 real deve obter a autorização S1, revalidá-la **dentro da mesma transação** do futuro preenchimento e rejeitar mudanças de supervisão/atribuição após o snapshot. A composição `REVIEW_ONLY` é um **parecer não executivo**, nunca substitui essa barreira.

## 4. Máquina técnica S0 candidata e prova necessária

`ACCEPTED_FOR_PROCESSING` (pedido idempotente e evento humano S0 registrado) → `EXTRACTION_PENDING` → `VALIDATING_RESULT` → `APPLIED | PARTIAL_REVIEW | FAILED_SAFE | STALE_RESULT`.

Esses são **rótulos técnicos candidatos**, não oitavo/nono status comercial, nem garantia de igualdade com rótulos FV-02. `ACCEPTED` ≠ `APPLIED`. Expor à UI somente projeção minimizada e autorizada, com causalidade e versões; não exibir texto bruto da IA nem conteúdo de outra loja. O evento de conclusão não expira por si só o prazo Meta; o caso pode permanecer visível enquanto janela ativa, e inbound futuro continua com humano atribuído.

**Falhas obrigatórias (negação por padrão):** evento inexistente/replay errado, `case_version`/`form_version` divergente, watermark desatualizado, tenant trocado, fonte do operador apresentada como do cliente, campo desconhecido/não elegível, retorno sem fonte, resultado de modelo truncado/recusado, permissão/atribuição revogada, opt-out/privacidade aplicável, concorrência de correção humana ou nova mensagem, timeout/429/401. Nenhum desses efeitos pode marcar vendido/perdido, enviar Meta, apagar versão atual nem transferir operador.

## 5. Homologação e escopo da autorização recebida

- **S0 / OpenAI / Frontend**: revisão do mapa acima e dos estados/projeções na issue #4; aceitar/rejeitar explicitamente a assinatura proposta antes de afirmar que é contrato canônico.
- **S0 vs. Meta (sem editar trabalho da outra frente):** o fechamento F03 não precisa de prova `sent` nem transporta webhook. Toda deduplicação de transporte/ACK/canal pertence ao desenho independente Meta e a seus contratos S0 pertinentes; esta branch não toca migrations 040 nem adaptador WA.
- **S1-002/I11:** estado global de disponibilidade, equipe gestor→operador e atribuição vigente pertencem S1; **grants operador→lojas são atribuídos pelos responsáveis** e não pelo gestor. Uma pausa global invalida a elegibilidade operacional nas lojas A+B simultaneamente, preservando grants para retorno, mas não recuperando casos já redistribuídos. S0 deve conferir o operador efetivamente autorizado. Não criar segundo redistribuidor ou presumir gestor da concessionária.
- **Não fazer agora:** chave OpenAI/billing (adiados por decisão de 19/10), execução F03 real, migrations SQL, alteração de enum/8 estados, API Meta, deploy, merge. O trabalho nesta branch é **desbloqueio contratual específico**, autorizado pelo responsável, sem equivaler a liberação de implementação global.


### F03-COMP — integração offline dos validadores reais (19/10/2026)

**Defeito reproduzido e corrigido no PR #8, sem mudar autoridade comercial:** a composição antiga retornava `NOT_READY` quando `result_has_validated_fields` era inconsistente **antes de consultar** `recheck_before_apply`, mascarando revogação de grant/sessão ou atribuição obsoleta. O pipeline agora realiza a revalidação de autoridade **primeiro**; `DENY` precede `STALE` e ambos precedem disponibilidade/prontidão e análise da proposta. Para casos autorizados, os retornos de campos continuam limitados a revisão, sem `APPLIED`.

**Evidência local verificada:** os três módulos originais foram reproduzidos com blobs Git exatamente iguais aos da branch anterior (`8978538`, `d2e7f6a`, `e393e58`). A suíte nova `backend/tests/test_s0_openai_f03_real_integration.py` **não usa mocks** e atravessa os dois validadores reais com gabaritos inteiramente fictícios. Execução anterior à correção: **40 executados, 37 PASS e 3 FAIL** (precedência indevida). Após a correção e acréscimo de quatro regressões: **44/44 PASS**. A suíte existente de composição foi readequada à nova precedência (apenas expectativas de ordem/chamada) e reexecutada: **22/22 PASS**. Execução conjunta efetiva: **66/66 PASS** com `python -m unittest discover -s backend/tests -p 'test_s0_openai_f03*.py' -v`; `python -m compileall -q backend` também concluiu sem erro. Os três arquivos publicados no novo incremento foram confrontados com o laboratório pelos blobs `529fe893`, `1865e953`, `d13b7271`.

**Limite da prova:** execução local offline do subconjunto de composição, não da suíte integral do repositório nem CI. Não há validação de NLP real, autenticação/S1 ou transação PostgreSQL, integração Meta, API OpenAI, Banco ou catálogo final. `REVIEW_ONLY` segue sendo parecer técnico e não autoriza gravação; contrato físico CFI-01, revisão conjunta e gates [R/V] permanecem pendentes.

### F03-COMP — conservação de opcionais informados (19/10/2026)

**Lacuna de cobertura corrigida no laboratório isolado:** a composição anterior podia retornar `REVIEW_ONLY` mesmo quando a proposta do modelo omitia campo **opcional efetivamente informado** pelo cliente. A composição agora devolve `REVIEW_REQUIRED` e somente os códigos `omitted_informed_optional_codes`, separados de `missing_required_codes` e `rejected_field_codes`. Não inventa valores, não preenche campos por inferência nem amplia autoaplicação; fala de operador, mensagem não autorizada e outro caso/loja não constituem evidência. Sem autorização atual, o detalhe não é exposto. Esta é extensão aditiva de **parecer offline**, não assinatura física ratificada com S0/FV.

**Execução local comprovada:** 16 novos testes com os dois validadores reais + 44 cenários de integração F03 reproduzidos localmente = **60/60 PASS** (`python -m unittest discover -s backend/tests -p 'test_s0_openai_f03*.py' -v`, no diretório do laboratório contendo esse subconjunto); `python -m compileall -q backend` PASS. Os hashes Git dos três módulos de origem coincidiram com o PR #8 antes da modificação; o hash do pipeline corrigido (`11e39080`) e do novo teste (`3969aa5c`) coincidiram com os publicados. Os 44 cenários antigos foram **reconstituídos** para a execução local e não representam comparação byte a byte do respectivo arquivo de teste no repositório. As suítes antigas F03 de 50 casos, atribuição de 28 e composição mockada de 22 **não foram reexecutadas nesta rodada**; o número 60 não deve ser apresentado como suíte integral/CI. Não houve API, SQL, Meta, deploy ou merge. A verificação ainda depende de snapshot e `asserted_fields` fictícios.

### F03 — reexecução conjunta verificável de 160 testes (19/10/2026)

**Rodada efetivamente realizada após o reparo de opcionais omitidos:** `python -m unittest discover -s backend/tests -p 'test_s0_openai_f03*.py' -v` (laboratório local, Python 3.13.5) → **160/160 PASS**, e `python -m compileall -q backend` → PASS. Composição detalhada, sem somar rodadas antigas: **50** casos do validador de campos + **28** de atribuição + **22** da composição mockada + **44** de integração entre validadores reais + **16** de cobertura de opcionais. Todos os **oito arquivos Python envolvidos** (três módulos e cinco suítes) tiveram seus hashes Git verificados contra os conteúdos publicados no PR #8, incluindo a suíte de 44 anteriormente reconstituída; portanto, esta é uma execução conjunta sobre os arquivos exatos da branch.

**Compatibilidade de superfície:** comparação atual de refs mostra a S0 sete commits à frente do ancestral comum; seus cinco caminhos diferenciados nesta comparação são documentação/runner S0 e não os arquivos `backend/s0_openai_bridge` nem as suítes F03. Listagens atuais de arquivos alterados nos PRs Meta #2 e S1 #5 não apontam colisão nesses caminhos. Isso NÃO prova compatibilidade transacional S0/S1 nem substitui rebase/revisão futura. O runner PostgreSQL da S0 exige banco local descartável e NÃO foi executado nesta rodada. Sem CI, sem SQL, sem Auth/S1 real, sem modelo OpenAI, Meta, Banco, merge ou deploy. O resultado máximo continua `REVIEW_ONLY`.


### F03 — matriz offline de corridas e escopo (28 casos, 19/10/2026)

**Incremento executado e publicado no PR #8:** [`backend/tests/test_s0_openai_f03_race_matrix.py`](../backend/tests/test_s0_openai_f03_race_matrix.py) contém **28 casos novos, com os três validadores reais, sem mocks**. Cobertura: resposta atrasada após inbound, edição da ficha/caso, recorte de snapshot, catálogo, mudança/reatribuição do operador, pausa global, perda de sessão e de concessão de loja, opt-out, conflitos de fontes, prioridades de negação, replay de evento de conclusão, escopo entre concessionárias e ausência de exposição de códigos de campo após revogação. O cenário de loja A revogada e loja B válida usa permissões **fictícias independentes**; não implementa ou comprova S1 real.

**Evidência restrita desta rodada:** no laboratório offline descartável, `python -m unittest discover -s backend/tests -p 'test_s0_openai_f03_race_matrix.py' -v` → **28 executados/28 PASS**, `python -m compileall -q backend` → PASS. Hashes Git locais iguais aos blobs publicados: `f03_offline_gate.py` `8978538`, `f03_assignment_recheck.py` `d2e7f6a`, `f03_review_pipeline.py` `11e3908` e matriz de testes `4366848`. **Não somar esta rodada aos 160 testes de execução anterior como se fosse a mesma execução; nenhuma CI confirmada.**

**Risco estrutural explicitamente não resolvido (TOCTOU):** a comparação de um `CurrentAuthority` antigo pode retornar `REVIEW_ONLY` mesmo após uma alteração que tenha ocorrido em outro instante; o teste 26 demonstra justamente que um objeto fictício obsoleto não é prova de concessão vigente. Somente S0/S1, com leitura autorizada atual e bloqueios/versionamento **na mesma transação** de eventual persistência, pode impedir esse reaproveitamento. Isto **não** é implementação de lock PostgreSQL, fluxo físico `human_close_extract`, autorização financeira, F01/F02 ou integração produtiva. Pendências CFI-01 [R] e escopo da S0 permanecem intactos.

**Compatibilidade de caminhos:** a S0 passou a oito commits à frente do ponto comum desta branch; entre os arquivos novos do delta estava uma migration S0-041 de vínculo Meta/tentativa, fora da titularidade da F03. Não foi incorporada nem executada neste incremento. Sem API, SQL, banco real, merge, deploy ou custos.

### F03 — captura sintética imutável das evidências (19/10/2026)

**Falha reproduzida e corrigida no laboratório:** `Evidence` usava `@dataclass(frozen=True)`, mas o `dict` interno `asserted_fields` ainda era mutável, inclusive através de alias detido por outro objeto. Modificar esse mapa após criar o snapshot fazia uma proposta inicialmente rejeitada passar a `PROPOSAL_ONLY` sem alteração de `case_version`/`snapshot_hash`. A evidência sintética agora é copiada na captura e exposta somente para leitura por `_FrozenFields`. `dataclasses.asdict` e cópia isolada de dados continuam suportados, sem mutar o registro; `deepcopy` de `Evidence` ou do `Snapshot` também preserva a proteção. O código não gera hash do snapshot nem prova proveniência real; metadados `asserted_fields` ainda são um **gabarito FICTÍCIO**, não NLP confiável.

**Evidência desta rodada, sem contagem acumulada:** `python -m unittest discover -s backend/tests -p 'test_s0_openai_f03*.py' -v` (subset do laboratório) → **50/50 PASS**, sendo 28 testes de corridas já publicados e **22 novos testes de imutabilidade** em `backend/tests/test_s0_openai_f03_snapshot_immutability.py`. `python -m compileall -q backend` PASS. Códigos e testes dos cinco arquivos locais tiveram SHA de blob Git coincidente com os publicados no PR #8: `f03_offline_gate.py` `01dfce7`, `f03_assignment_recheck.py` `d2e7f6a`, `f03_review_pipeline.py` `11e3908`, matriz race `4366848`, novos testes `5ccc160`. Os 160 testes do incremento anterior **não foram reexecutados contra esta alteração**; não declarar 210 testes numa execução ou aprovação CI.

**Fronteira não resolvida:** `asdict` explicitamente produz uma representação mutável **separada**, não uma credencial S0. Imutabilidade dos registros Python sintéticos não substitui a S0 autenticar evento, construir snapshot físico mínimo com assinatura/corte e consultar permissões e versões atuais sob trava transacional antes de gravar. CFI-01 permanece [P/R], persistência real e API permanecem não implementadas, sem merge, SQL, Meta, custo ou deploy.

### F03 — preparação do gate de regressão integral e critérios transacionais [P/R] (19/10/2026)

**Executor offline publicado (sem banco):** `python3 scripts/run_f03_offline_regression.py` executa exclusivamente as sete suítes F03 conhecidas, com contagem individual fechada (**50 + 28 + 22 + 44 + 16 + 28 + 22 = 210**), hash Git de cada arquivo e recusa `exit 2` quando uma suíte está ausente ou tem número inesperado de casos. Os nomes e totais são *expectativas para futura execução integral*, NÃO aprovação de 210 cenários. `--allow-subset` existe somente para laboratório incompleto, rotula a execução como `SUBSET` e não deve aparecer como aceite integral. O script retira variáveis comuns de segredo da execução, mas isso não isola rede no nível do sistema operacional.

**Evidência realmente executada nesta rodada:** no laboratório local que contém **apenas** a matriz de 28 corridas e a matriz de 22 testes de imutabilidade, a execução `--allow-subset` completou **50/50 PASS**; modo estrito sem flags **bloqueou (código 2)** pela ausência de outras cinco suítes; `python -m compileall -q scripts backend` PASS. Hash do executor local e GitHub = `b2f4a5978f5bfda7887abebe1ddfc919b3efcd93`. Ainda **não** houve execução conjunta 210/210 após a alteração de imutabilidade; os 160 anteriormente verificados eram de versão anterior e não devem ser somados como execução única. Sem CI.

**Checklist [P/R] que a futura transação física S0/F03 deverá demonstrar antes de qualquer `APPLIED`** (sem declarar nomes de RPC/tabela/endpoint homologados):

| Etapa / prova necessária | Pertence a | Falha esperada |
|---|---|---|
| Fechamento humano legítimo, autoria, sessão e concessão Prumo/loja ativas | S0 + S1 | `DENY`; modelo não autentica fechamento |
| Atribuição atual e eventual redistribuição para mesmo operador com ID novo | S0 + S1 | `STALE`, sem reutilizar autorização antiga |
| Mesmo caso, loja, ciclo e evento de conclusão, com finalidade apropriada | S0 | `DENY`, inclusive para casos pós-venda sem autorização específica |
| Hash/corte imutável, último inbound, versão de caso e versão de ficha dentro do lock | S0 + domínio de mensagens | `STALE`, sem aceitar resposta tardia ou correção concorrente |
| Catálogo/versão/classificação D3 aprovada, fontes por mensagem e conflitos | S0 + política de privacidade | Campo excluído/pendência humana; nunca valor inventado |
| Opt-out, permissão de tratamento e estado humano atual, sem acionar IA Vendedora | S0 + S1 | Bloquear/no-op, sem mensagem à pessoa |
| Idempotência de execução e CAS/locks junto com escrita e trilha de auditoria | S0 transacional | Zero gravações duplicadas; versão auditável somente no commit |
| Retorno técnico separado entre sugestão, revisão, recusa, desatualização e `APPLIED` | S0 → FV | `REVIEW_ONLY` nunca equivale a `APPLIED` nem a remessa ao Banco |

**Provas futuras obrigatórias, ainda NÃO executadas:** T-S0F03-01 concorrência de novo inbound versus commit; T-S0F03-02 revogação de concessão depois da extração; T-S0F03-03 reatribuição para mesmo operador com novo ID; T-S0F03-04 duas propostas idênticas concorrentes/idempotência; T-S0F03-05 duas lojas com identificadores semelhantes; T-S0F03-06 correção humana C13 versus sugestão antiga; T-S0F03-07 falha transacional/rollback sem `APPLIED`; T-S0F03-08 retorno pós-venda sem finalidade bancária e sem plano automático. Os IDs são **rótulos de planejamento desta ponte**, não casos canônicos ratificados nem resultados de teste.

**Dependências para retirar [R]:** issue #4 CFI-01 (comando/contrato físico + aprovação S0/OpenAI/FV), issue #6 CF-OP-02 (atribuição/roteamento pós-conclusão, opção de plano sem retomada IA e limites) e validações externas [V]. O documento candidato OAI-05/E01 da frente OpenAI não deve ser apresentado como autorização unilateral para alterar a S0. Nenhum SQL, API Meta/OpenAI, envio, merge ou deploy nesta atividade.
