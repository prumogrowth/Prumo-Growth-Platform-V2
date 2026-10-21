# S0 ↔ F03 CFI-01 — recibo atômico interno e gate de contrato | 21/10/2026

**Estado:** incremento de laboratório, PR #12 Draft; **não homologado**, sem merge/deploy/OpenAI paga/Supabase hospedado, sem clientes reais. Não confundir com Marco A/B integralmente concluídos.

## Mudança efetiva

O backend `S0CFI01AtomicCommandsLocal` da S0 mantém `execute()` público estrito: somente estado técnico e referência do encerramento. Os métodos **internos** `capture_internal_receipt` e `recheck_internal_receipt` reutilizam autenticação GoTrue, assinatura HMAC-SHA256 com nonce e a **mesma transação PostgreSQL** da função `prumo_private.cfi01_atomic_signed_closure_local`. Não existe conexão privilegiada suplementar para obter metadados.

Quando a autorização e os locks S0/S1 passam, a função retorna ao backend S0 (não ao modelo): `store_ref`, `case_ref`, `closure_event_ref`, `assignment_ref`, `expected_cycle_version` (= `public.ciclos_comerciais.versao_registro`), `snapshot_sha256`, `message_watermark` (= UUID da última mensagem da ordenação assinada) e `message_count`. O evento e o hash correspondem ao recibo persistido no mesmo caminho de captura; rechecagem relê equipe, sessão, concessão, atribuição, versão comercial, mensagens e recibo com locks e retorna metadados somente se ainda válidos.

Não se fornece transcrição, conteúdo pessoal, `form_version`, versão de catálogo, token de acesso, dado bancário ou ferramenta de escrita. O recibo não é um bearer token, não autoriza envio ao provedor e não permite `APPLIED`. Nem `message_watermark` nem hash isolados asseguram minimização/LGPD; serão apenas fatos verificáveis da S0.

## Provas e limites

- [PG17 #39640696965 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39640696965): 133 unitários e 76 físicos após correção do desempacotamento do retorno; os três testes novos conferem metadados com recibo persistido, rechecagem sob mensagem nova e bloqueio de sessão revogada/flag injetada.
- [PG17 #39640805731 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39640805731): mesmos testes físicos e unitários, branch com extensão da suíte de autenticação.
- [GoTrue/REST #39640459204 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39640459204): oito cenários originais passaram com o SQL estendido; **não** era ainda o novo teste do recibo interno.
- [GoTrue/REST #39640821139 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39640821139): 9/9 cenários CFI01-AUTH com GoTrue verdadeiro, incluindo metadados internos consistentes com snapshot S0, autenticação/recheck, sessões negadas e estado comercial preservado; commit de código `72d9e81daee44f392a00feb5b1be067f0dd68611`. Instância efêmera encerrada.
- Falha intermediária [PG17 #39640383420](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39640383420) por tentativa de desempacotar 8 colunas como 2, corrigida no commit `f46955bdfd0104643827209da2eeef4e30dbca69` e validada no sucesso acima.

## Contrato: colisões reais, NÃO mapear silenciosamente

| Dimensão | S0 física hoje | FV/OpenAI candidata | Decisão pendente |
|---|---|---|---|
| Versão comercial | `expected_cycle_version` = `ciclos_comerciais.versao_registro` | `expected_case_version` / `expected_version` | Campo distinto; nenhum mapeamento físico foi aprovado. `casos_humanos` na migration S0/003 não declara `versao_registro`. |
| Conclusão | Recibo de closure com UUID, ator/sessão/atribuição/chave/hash/última mensagem | `closure_event_id` / `trigger_ref` | Convenção canônica, versão da assinatura e política de reprocessamento. |
| Snapshot | SHA-256 sobre sequência S0 de mensagens com watermark UUID e contagem | `conversation_snapshot_hash`, `message_watermark` e referência autorizada | Semântica final de corte, edição, múltiplas conversas e payload minimizado. |
| Atribuição | ID físico de `atribuicoes_humanas`; S1 conferida a cada operação | `assignment_ref` e `assignment_version` candidatos | Identidade válida e versão distinta, inclusive regra de exceção individual S1 (não importada de fixture). |
| Formulário e catálogo | **Não são emitidos por este recibo** | `form_version_observed`, `current_form_version`, `allowed_fields_catalog_version` | Fonte autorizada S0, campos/tipos, LGPD e regras por classe; sem catálogo fictício em produção. |
| Resposta F03 | Nenhuma aplicação/exceção comercial | `fields_proposed`, `missing_fields`, `conflicts`, OAI-07 conversacional | Schema OAI-05/07, evidências e códigos homologados; F02 separado, nunca consequência automática da IA. |

## Incremento seguinte — ponte tipada S0→F03 com bloqueio contratual

Em `backend/s0_cfi01_f03_receipt_bridge_local.py`, `S0CFI01F03ReceiptBridgeLocal` aceita **somente** o serviço `S0CFI01AtomicCommandsLocal` e reaproveita `capture_internal_receipt`/`recheck_internal_receipt`; portanto, cada chamada volta à autenticação GoTrue e à transação HMAC/nonce/SQL S0. O único resultado afirmativo é `VERIFIED_CONTRACT_PENDING`: a S0 confirmou o recibo e sua atualidade, **não** autorizou envio ao modelo nem a escrita. Rechecagem exige ID do fechamento, chave original, versão de ciclo, caso, atribuição, hash, watermark e contagem inalterados; bytes do modelo não entram em nenhuma dessas comparações. Alterações geram `DENIED`, `STALE` ou `UNAVAILABLE` **sem retornar binding**.

A ponte não infere `expected_case_version` a partir de `expected_cycle_version`; rejeita atributos da UI que tentem fornecer `form_version`, `catalogue_version`, `assignment_ref`, `actor_id` ou `fields_proposed`. Há uma lista explícita `UNRATIFIED_F03_INPUTS` com os atributos ausentes. O binding é objeto **somente de backend S0**, não objeto HTTP, token delegável, prompt, garantia de minimização ou permissão de persistência. Mesmo o recheck positivo mantém contrato pendente.

**Evidência de autenticação real:** [GoTrue/REST #39681504462 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39681504462), 10/10 cenários CFI01-AUTH em Supabase local efêmero, incluindo CFI01-AUTH-10: a ponte consome recibo da S0 com token GoTrue verdadeiro, revalida e mantém `VERIFIED_CONTRACT_PENDING`, sem modelo ou escrita. Execução no commit `c3aa553173d464e04bd48bf59c367c8061661304`.

**Evidência física:** [PG17 #39681391275 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39681391275), 133/133 unitários + 84/84 testes físicos. Os oito novos casos (#77–#84) exercitam captura/recheck do recibo, mensagem nova, troca de UUID de atribuição com histórico preservado, injeção de contexto pelo navegador, alteração de versão de ciclo, sessão revogada, adulteração do evento e tipagem/objeto falso. A primeira tentativa [#39681279134 — FAILURE](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39681279134) encontrou erro **na montagem do teste de reatribuição**, que excluía atribuição referenciada pelo recibo histórico; corrigido em `c3aa553173d464e04bd48bf59c367c8061661304` pelo encerramento da atribuição antiga, sem exclusão. Nenhuma migration, API de produção, OpenAI paga, mensagem real ou atualização comercial foi introduzida.

## Próximos gates não delegáveis ao modelo

1. **Marco A:** ratificar versão de contrato e semântica de versão do caso/ciclo, atribuição, `form_version`, catálogo, corte/mensagens e schema completo OAI-05/07. A comparação foi feita, mas não há aprovação física.
2. **Marco B:** em sandbox S0, após finalidade LGPD e catálogo ratificados, disponibilizar recorte efetivamente minimizado para F03; receber proposta estruturada; checar tipos/fontes/escopo, revalidar na mesma transação de gravação e auditar campos elegíveis. Não transformar o recibo de metadados em autorização de escrita; não aceitar resultado comercial/bancário por texto.
3. **Produção:** revisão do helper de sessão `postgres` estritamente limitado, RLS, migrations revisadas, segredos, observabilidade e autorização expressa de implantação; toda fixture atual é de laboratório.
4. A decisão sobre backend/n8n/combinação segue em aberto e **não é tomada nesta implementação**.

**Critério de parada:** quando não houver alteração técnica segura sem ratificação das escolhas acima, levar decisões compactas à conversa com o responsável, sem antecipar auditoria geral e sem elevar os PRs de Draft.