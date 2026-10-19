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

## 4. Máquina técnica S0 candidata e prova necessária

`ACCEPTED_FOR_PROCESSING` (pedido idempotente e evento humano S0 registrado) → `EXTRACTION_PENDING` → `VALIDATING_RESULT` → `APPLIED | PARTIAL_REVIEW | FAILED_SAFE | STALE_RESULT`.

Esses são **rótulos técnicos candidatos**, não oitavo/nono status comercial, nem garantia de igualdade com rótulos FV-02. `ACCEPTED` ≠ `APPLIED`. Expor à UI somente projeção minimizada e autorizada, com causalidade e versões; não exibir texto bruto da IA nem conteúdo de outra loja. O evento de conclusão não expira por si só o prazo Meta; o caso pode permanecer visível enquanto janela ativa, e inbound futuro continua com humano atribuído.

**Falhas obrigatórias (negação por padrão):** evento inexistente/replay errado, `case_version`/`form_version` divergente, watermark desatualizado, tenant trocado, fonte do operador apresentada como do cliente, campo desconhecido/não elegível, retorno sem fonte, resultado de modelo truncado/recusado, permissão/atribuição revogada, opt-out/privacidade aplicável, concorrência de correção humana ou nova mensagem, timeout/429/401. Nenhum desses efeitos pode marcar vendido/perdido, enviar Meta, apagar versão atual nem transferir operador.

## 5. Homologação e escopo da autorização recebida

- **S0 / OpenAI / Frontend**: revisão do mapa acima e dos estados/projeções na issue #4; aceitar/rejeitar explicitamente a assinatura proposta antes de afirmar que é contrato canônico.
- **S0 vs. Meta (sem editar trabalho da outra frente):** o fechamento F03 não precisa de prova `sent` nem transporta webhook. Toda deduplicação de transporte/ACK/canal pertence ao desenho independente Meta e a seus contratos S0 pertinentes; esta branch não toca migrations 040 nem adaptador WA.
- **S1-002/I11:** estado global de disponibilidade, equipe gestor→operador e atribuição vigente pertencem S1; **grants operador→lojas são atribuídos pelos responsáveis** e não pelo gestor. Uma pausa global invalida a elegibilidade operacional nas lojas A+B simultaneamente, preservando grants para retorno, mas não recuperando casos já redistribuídos. S0 deve conferir o operador efetivamente autorizado. Não criar segundo redistribuidor ou presumir gestor da concessionária.
- **Não fazer agora:** chave OpenAI/billing (adiados por decisão de 19/10), execução F03 real, migrations SQL, alteração de enum/8 estados, API Meta, deploy, merge. O trabalho nesta branch é **desbloqueio contratual específico**, autorizado pelo responsável, sem equivaler a liberação de implementação global.
