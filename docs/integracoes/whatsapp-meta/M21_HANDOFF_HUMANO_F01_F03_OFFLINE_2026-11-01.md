# M21 — Handoff humano e fronteira F01/F03 (LAB offline)

**Data:** 01/11/2026. **Escopo:** somente Meta/WhatsApp, sem webhook/Graph real, sem acesso à S0 hospedada e sem chamada a F01/F03. **M21-A/B/C LAB**; **M21-D e marco principal pendentes**.

## Regra e precedência

A especificação vigente [01](01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) preserva: o handoff humano definitivo impede F01 de **retomar o mesmo caso**. O inbound posterior pertence à rota humana autenticada/autorizada pela S0. **F03 não conversa com o cliente**; somente a **conclusão humana explícita** autorizada pela S0 pode acioná-la, após manifesto histórico, cutoff e fontes/capacidades ratificados. **Três relógios/atos independentes:** janela Meta de texto livre após inbound; evento de conclusão humana e cutoff F03; janela comercial C09 após `sent` verificado do template final e regras S0. Nada é inferido a partir de mero timeout, template, leitura ou `human_message_sent`.

A [WA-21](wa21-papeis-diretor-gestor-consultor-assinatura-2026-10-21.md) define **Consultor/Gestor/Diretor**. A [M17](M17_ASSINATURA_HUMANA_PREVIEW_OFFLINE_2026-11-01.md) é somente assinatura textual, não identidade autenticada nem prova de contato. Fonte da identidade real é S0/S1. O histórico multimodal/cutoff F03 pertence à [Issue #5](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/5); aplicação de ficha, recheck e competências exclusivamente S0 à [Issue #6](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/6). Não duplicar demandas existentes.

## M21-A — fronteira Meta pura e não autoritativa

`integrations/whatsapp-meta/wa21-human-handoff-f01-f03-offline.ts` expõe `inspectWa21HandoffOffline(caseClaim,eventClaim)` e `recheckWa21HandoffOffline(previousSnapshot,freshCaseClaim,freshEventClaim)`.

- `wa21-s0-case-state.lab.v0.1` é **alegação** de caso, loja/App/WABA/número/lead, revisões do caso/atribuição/handoff/cutoff, estado `LAB_F01_ACTIVE`, `LAB_HUMAN_HANDOFF_DEFINITIVE` ou `LAB_HUMAN_CLOSED`, bit de handoff irreversível alegado, atribuição humana, instante de handoff, janela Meta separada, opt-out alegado, freshness e flags S0 falsas.
- `wa21-case-event.lab.v0.1` é **evento injetado** de `LAB_INBOUND_MESSAGE`, `LAB_HUMAN_CLOSURE_EXPLICIT`, `LAB_META_WINDOW_TIMEOUT`, `LAB_TEMPLATE_SENT_CLAIM` ou `LAB_HUMAN_MESSAGE_SENT_CLAIM`, vinculado ao mesmo escopo e timestamp. Somente a forma `LAB_HUMAN_CLOSURE_EXPLICIT` pode carregar `closure_ref`, `actor_ref`, `actor_role` e `closure_cutoff_ms` alegados. O evento não autentica o autor, o histórico nem o comando.
- Caso F01 ainda ativo e **nunca** transferido definitivamente, com inbound -> `LAB_F01_ACTIVE_UNVERIFIED` (**não** autorização de invocar modelo). Estado F01 aparentemente reaberto após handoff definitivo -> **DENIED**. Inbound no caso humano -> `LAB_HUMAN_ROUTE_ONLY_UNVERIFIED`, **sem** permissão de atendimento ou envio. Evento anterior ao horário de handoff -> `LAB_PRE_HANDOFF_EVENT_HOLD`, nunca reclassificado como novo contato humano.
- Somente estado humano já fechado + evento **explícito** de conclusão, cutoff coerente ao evento/apos handoff -> `LAB_F03_CUTOFF_CANDIDATE_UNVERIFIED`. Inbound após fechamento -> `LAB_POST_CLOSURE_HOLD`; timeout, template ou `human_message_sent` **não** disparam F03. Janela Meta aberta, fechada ou desconhecida não muda o cutoff.
- (Re)check exige o MESMO snapshot/versionamento `wa21-human-handoff-snapshot.lab.v0.1`, com hash de **todos os campos de contexto e evento** (apenas consistência sem chave, nunca HMAC nem identidade). Alteração de revisão, cutoff, evento, tempo, autor, janela ou loja -> negativa. Entradas com getter/campos extra/fonte que alegue autenticação verdadeira -> negativa.

**Saídas:** `source_authenticated=false`, `case_verified=false`, `closure_verified=false`, `f01_invocation_authorized=false`, `f03_invocation_authorized=false`, `human_dispatch_authorized=false`, `graph_dispatch_authorized=false`, `human_closure_apply_authorized=false`, `commercial_transition_authorized=false`, `c09_window_authorized=false`, `ack_allowed=false`, `production_authorized=false` **em todos os caminhos**. Não retorna nome, texto, telefone de cliente ou dados financeiros.

## M21-B — regressões

`integrations/whatsapp-meta/wa21-human-handoff-f01-f03-offline.test.ts`: **60 casos M21** cobrindo handoff irreversível, F01 sem retorno, ingressos e eventos históricos, fechamento humano explícito, janela Meta diferente de cutoff, `opt_out` sem opt-in inferido, C09 independente, fronteira do ator humano, isolamento por loja/App/WABA/número/caso/lead, leitura stale/future, getters, permissão falsificada, revisões, recheck e proteção de conteúdo em saída.

**CI funcional:** commit `bc63bd4ed2e340c0b623c35b0cac91e94ce8bd3b`, [GitHub Actions 41363919177](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41363919177): **60/60 M21**, **2.072/2.072 Meta offline** (2.012 baseline + 60), **377/377 testes de interface**, dois jobs `success`, scanner ACK estático aprovado e **18/18 PG17 históricos** em escopo separado de **ingresso S0/Meta**. Não significa que F01/F03 ou Graph foram integrados. Revalidar CI do último HEAD documental em execução específica.

## M21-C — fronteiras, aceites e bloqueios

- **S0/S1:** fonte hospedada/assinada de `handoff_ever_definitive` ou condição equivalente **não reversível** no mesmo caso, identidade/cargo/atribuição humana, pausa de F01/F02, roteamento de inbound, autorização de livre mensagem Meta e trilha durável. S0 precisa definir resolução pós-fechamento e replay, sem reinventar F01 no Meta.
- **F01/OpenAI:** consumidor de handoff autenticado; ao transferir definitivamente não reabrir o mesmo caso por inbound, relógio de Meta ou prompt; usar contratos da frente OpenAI, sem Meta invocar a API.
- **F03/OpenAI/S0:** conclusão humana **expressa e autorizada**, `closure_ref`, `cutoff_ref` imutável com identidade pessoa/loja/casos e manifesto de histórico/mídias, revisão do cutoff e recheck de catálogo/permissões. As [Issues #5](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/5) e [#6](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/6) já contêm solicitações; manifestos/catálogo existentes continuam `REVIEW_ONLY_NOT_FROZEN`/`APPLIED_SYNTHETIC_ONLY`, **não** dados F03 completos nem autorização real.
- **Meta/Infra:** transporte/ingresso e observação técnica autenticada dependem de S0/Infra; HMAC/recibo/ACK da [#2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) não prova conclusão humana. Autoria humana e templates em M17/M18 permanecem pendentes em [#10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10).
- **Homologação:** testes cruzados com caso transferido, inbound tardio, retry/replay/concorrência, casos distintos da mesma pessoa, cutoff E1/E2, mídia ausente, opt-out e revogação antes de promover `F03` ou operação real. Sem migração, nova Issue, conta real, credencial, Graph, envio, merge, deploy, HTTP ACK ou efeito comercial.

**Checklist M21:** [x] A módulo LAB, [x] B testes LAB, [x] C limites/contratos, [ ] D integração autenticada/autorização S0/OpenAI/Infra, [ ] marco principal M21 operacional.


## Adendo da auditoria M21 — 01/11/2026

A [auditoria corretiva](AUDITORIA_M21_HANDOFF_F01_F03_2026-11-01.md) detectou que um evento de fechamento F03 podia se declarar explícito em caso aparentemente fechado sem comprovar **coincidência com uma ocorrência de fechamento na própria alegação S0 do caso**. Em LAB, isso permitia `LAB_F03_CUTOFF_CANDIDATE_UNVERIFIED` para autor, referência ou horário não correlacionado. O resultado nunca autorizava F03, mas sua semântica era permissiva demais.

Corrigido: entrada de caso **`wa21-s0-case-state.lab.v0.2`** com `closure_revision`, `closure_ref`, `closure_actor_ref`, `closure_at_ms`, `closure_cutoff_ms`. Em caso `LAB_HUMAN_CLOSED`, todos precisam estar presentes/coerentes e corresponder ao evento explícito. Caso não fechado com campos de fechamento é recusado. O cutoff pode preceder o instante da conclusão, mas não o handoff; deve coincidir nos dois objetos e não pode ser posterior à conclusão. A entrada de evento continua `wa21-case-event.lab.v0.1`. Saída passa a **`wa21-human-handoff-snapshot.lab.v0.2`**, com domínio de hash próprio e rejeição de v0.1 no recheck.

**20 regressões adicionais AUD-M21-61..80**: divergência de fechamento por referência, autor, horário e cutoff; ausência de registro; causalidade; recheck de revisões; versões antigas; getter hostil; permissões sempre falsas. **Evidência funcional:** commit `b84c5972a2705901433b91e885a01a28c5e3485f`, [CI 41370100369](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41370100369), **80 M21, 2.092/2.092 testes Meta offline**, **377/377 de interface**, **18/18 PG17 históricos independentes de ingresso**, dois jobs `success`, scanner ACK estático aprovado.

Os novos campos são **alegações de laboratório**, não fonte S0 autenticada nem autorização de fechamento. A titularidade do manifesto/cutoff F03, competência humana, identidade multicases e aplicação de campos continuam nas [#5](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/5) e [#6](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/6). **M21-D e marco operacional permanecem [ ]**. Os 60/2.072 resultados anteriores acima eram anteriores à auditoria.
