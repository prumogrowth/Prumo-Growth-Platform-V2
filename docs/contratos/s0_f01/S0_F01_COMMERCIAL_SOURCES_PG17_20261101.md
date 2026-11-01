# S0/S1 F01 — fontes comerciais, seleção opaca e recheck em laboratório PG17

**01/11/2026 | Issue [#12](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/12) | Estado: ENTREGUE_PARA_REVISAO_OPENAI / LAB_ONLY; NÃO É ACEITE OPERACIONAL.**

## Base e fontes congeladas

A responsabilidade pela fonte comercial, autoria, curadoria, concessão por loja/finalidade e verificação semântica pertence à S0/Comercial; OpenAI OFF-14 valida **somente metadados sintéticos**. A decisão do proprietário autoriza desenvolvimento integrado **em isolamento**, não preços reais, segredos, dados de clientes, modelo real, mensagens, migrações hospedadas, merge ou deploy.

- Base S0 F01 de posse/handoff: commit `caf58eac889481bb96354bdcdaa740c8e48d9755`, branch candidata `exp/s0s1-f01-commercial-pg17-20261101`.
- Ingresso S0 PG17 original pinado: `01ffdb093013664b73b18d23f92aac2202578210`.
- OFF-14 original e imutável: `df5a2ecafbd468cc0f45a83a2a21826ad4d96c75`, módulo `docs/integracoes/openai/e04_offline_lab/f01-commercial-source-review-lab.mjs`, blob `3cf4edef458ec12fd11647b1896df040f076da19`. Executa 45 testes da própria frente sem alterações.

## Contrato candidato: `prumo.s0.f01-commercial-sources/0.1-lab`

O PostgreSQL 17 descartável `s0_meta_ingress_lab` recebe um novo schema `s0_f01_sources_lab` **sem privilégios de runtime** e sob as mesmas travas/flags de instalador descartável. São apenas metadados falsos: `contexts` por caso/loja/pessoa/finalidade e revisões de catálogo/conhecimento/política/consentimento/grant; `sources` com `current` versus `historical`, estado de aprovação, validade, correção, versão, códigos de alegação e flags explicitamente fictícias de grant/proveniência/minimização; `selections` com fingerprint; `aliases` `src_###`; `reviews` em estado `LAB_REVIEW_ONLY_NO_PUBLISH`.

**Não há textos de fontes, preço, taxa, oferta, mídia, transcrição, identidade real, PII, nome de Consultor, roster, segredo, token, Graph ou publicação.** Um código como `PRODUCT_FEATURE` é uma etiqueta sintética, **não prova semântica**.

**Seleção de entrada:** `prepare` exige `turn_ref` S0/F01 previamente persistido, escopo idêntico de loja/caso/pessoa/serviço, owner IA, prazo vigente e oito revisões F01 `case/cycle/assignment/catalog/knowledge/policy/route/consent`; requer ainda revisão separada de grant de conteúdo e estado `LAB_ALLOWED` por contexto. Com lock no registro F01, contexto e fontes, confronta fonte por finalidade e loja, código permitido, alegações de proveniência/grant/minimização, corrigida/revogada/pausada, vencida ou sem prazo. **Uma fonte histórica só pode participar como `interpretive`**; nunca sustentar oferta comercial corrente. Registra fingerprint do **catálogo completo**, inclusive itens não selecionados, e mapeamento persistente de referências internas para aliases `src_001` etc. O retorno de laboratório contém somente alias, claim code e modo; não revela `source_ref` interno, conteúdo ou condição comercial.

**Recheck de retorno:** `review` valida a seleção/aliases imutáveis, o catálogo inteiro, todos os grants/revisões e o escopo; exige lista **exatamente igual** aos aliases/códigos/modos originalmente selecionados, não aceita nova alegação nem remapeamento. Em **uma transação** reusa `recheck_proposal` do F01 de posse e grava dois fatos **NO_PUBLISH** sujeitos a rollback e dedupe; se humano assumiu ou fonte mudou durante a geração, nega. Não reserva envio e não concede acesso a modelo, publicação ou fato comercial. O check antigo não serve como direito futuro após revogação.

Toda saída mantém `source_authenticated=false`, `content_grant_verified=false`, `semantic_support_verified=false`, `commercial_offer_authorized=false`, `model_content_authorized=false`, `publish_authorized=false`, `send_authorized=false`, `production_authorized=false`.

## Provas e contagem

[CI funcional `41318170109`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41318170109) no SHA `dfdc2934cd627c0a49162b7cfc01d45d9c8b8337`: `completed/success`, 2/2 jobs. **20/20 novos testes físicos PG17**, **8/8 de compatibilidade com OFF-14** (7 offline + 1 obtido de observações persistidas em PG17), **45/45 testes originais OFF-14** e **25/25 regressões físicas F01 posse/handoff** = **98 casos distintos**, não somando os mesmos 7 testes de interoperabilidade duas vezes.

Os 20 casos físicos cobrem seleção/replay de alias, fonte de outra concessionária, histórico como oferta negada, histórico interpretativo, fonte pausada/revogada/draft/expirada, prazo indefinido, correção, claim não declarado, ausência de grant/proveniência/minimização, política/consentimento deny/unknown, cinco revisões, recheck positivo somente lab, replay, alias forjado, edição sem incremento de revisão (incluindo fonte não selecionada), adição de fonte, remapeamento persistido, handoff no meio do fluxo, rollback e negação ACL runtime.

Houve duas rodadas negativas por defeito na montagem da suíte (helpers de turno/handoff ausentes) e no alias de importação da função de recheck F01; ambas foram corrigidas com novas execuções completas. **O commit definitivo com este relatório exige uma CI própria**, que deve ser comprovada antes do aceite da entrega.

## Lacunas explícitas e handoff entre frentes

1. **Comercial/Proprietário/Infra:** identificar fonte oficial de preços, campanhas, condições, aprovação humana, revogação, histórico/correção e política de retenção; atribuir curadoria, assinatura, integridade, vigência e privilégios por concessionária. Não publicar dados reais ou credenciais nesta Issue.
2. **S0/S1:** adquirir fonte autenticada e escopo de conhecimento de cada loja, assegurar revisões/locks também para escritores e provas de origem; desenhar leitura minimizada/consentida e verificador **semântico** do texto/citação/claim no momento de publicar. O snapshot sintético OFF14 não é atestado. O lock de contexto só serializa mutações que respeitam a disciplina de acesso; uma escrita direta que o ignore pode correr depois do commit. O fingerprint detecta alterações no **próximo** recheck, não torna remotos atômicos.
3. **OpenAI:** revisar compatibilidade com OFF-14 e contrato de aliases; o envelope com `source_ref` do teste é **apenas interno à S0** e não deve ser enviado ao provedor. A saída OFF-14 `LAB_ELIGIBLE_UNVERIFIED` continua sem autoridade. Nunca inferir oferta, taxa, contrato, preço ou publicação a partir de `claimCodes`.
4. **Meta:** #8 cadastro de canais, #10 PRE_DISPATCH e #9 comprovante outbound permanecem gates separados; #11 posse IA/handoff anterior não autentica base comercial e #7 F02 não autoriza envio.
5. **Próxima integração real:** especificar fonte/endpoint autenticado S0 e material comercial aprovado, prova semântica e recheck de publicação unificado; somente então discutir E2E sob autorização específica. Não houve merge, deploy, alteração hospedada, consulta de dados de cliente nem chamada à OpenAI/Meta.

**Evidência deste relatório é laboratório, não aceite da OpenAI, do Comercial ou de produção.**
