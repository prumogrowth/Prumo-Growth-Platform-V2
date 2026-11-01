# M15 — Prévia de planejamento F02 (laboratório offline)

**Data:** 01/11/2026. **Frente:** WhatsApp/Meta. **Estado:** contrato candidato **somente de fixture**, sem autoridade S0, Graph ou aceite OpenAI/F02. M15 principal continua aberto.

## Objetivo e contexto

A M15 exige que a F02 receba somente candidatos de templates vigentes e adequados à finalidade escolhida, com a continuidade de fluxo/campanha, sem inventar modelos ou disparar mensagens. O termo **autorizados** no marco de produção exige decisão ratificada da S0; o laboratório Meta não consegue estabelecer autorização verdadeira, ainda que todos os campos de entrada tenham nomes de "aprovação".

Módulos já existentes, **reutilizados sem alterar as fronteiras**:

- **WA-25** — `template-purpose-eligibility.ts`: seleção de template por propósito, ator, fluxo, campanha e loja/WABA, com versão e flags falsas.
- **WA-26** — `s0-template-purpose-bridge.ts`: planejamento e recheck de política grosseira em portas fake, tickets privados para ensaio, nunca credencial/ordem de envio.
- **M13 / WA13** — `wa13-template-catalog-reconciliation.ts`: coincidência sintética com status/versão/identidade/digest de componentes por App/WABA. Uma resposta `APPROVED` atribuída à Meta não é evidência de aprovação autenticada.
- **M14 / WA14** — `wa14-purpose-consent-preflight.ts`: consentimento por finalidade distinta do propósito de template, opt-out específico/geral, grant de ator/versão/campanha e janela; ledger simulado sem fonte de verdade.

## M15-A — Composição offline sem autoridade

`integrations/whatsapp-meta/wa15-f02-planner-preview.ts` implementa `prepareWa15F02PreviewOffline(request,wa26Ports,m13Host,m13S0,m13Provider,m14Ledger)`.

As entradas são **fixtures não autenticadas**, não chamadas físicas S0/Meta. Contrato `wa15-f02-planning-request.lab.v0.1`: `selection_ref`, `concessionaria_id`, `app_ref`, `waba_id`, `catalog_revision`, `language`, `purpose_ref`, `consent_purpose_ref`, `actor_kind`, `actor_ref`, `flow_ref`, `campaign_ref`, `case_ref`, `lead_ref`, `case_version`, `authorization_revision`, `plan_revision`, `now_ms` e `max_age_ms` (limite laboratorial de cinco minutos).

1. Exige coerência de escopo principal, concessionária, WABA, lead, caso e revisões de solicitação/ledger; WA-26 `resolveSelection` é envelopado para confrontar escopo inteiro (inclusive propósito, ator, fluxo, campanha, case/lead) com o pedido candidato. Não estabelece identidade M2M.
2. Compara a política alegada WA-26 com a política do ledger M14 (revisão, caso, audiência e campanha), exigindo estado coerente `VALID` sem opt-out na declaração de WA-26. Se uma fonte simulada contradiz a outra, recusa.
3. Chama a M13 para conciliação dos detalhes atribuídos à Meta, exige mesma loja/App/WABA/catálogo/relógio e recusa identidade, idioma, categoria ou versão distinta dos candidatos WA-26.
4. Para **cada** candidato WA-26, chama M14 com escopo completo e `consent_purpose_ref` distinto de `purpose_ref`. Não ignora ausência de consentimento nem de grant individual. Se **qualquer** candidato divergir, a prévia inteira é recusada, sem resposta parcialmente verificada.
5. Só retorna `LAB_F02_PREVIEW_UNVERIFIED`, com lista imutável e ordenada, formato `wa15-f02-preview.lab.v0.1`. Um candidato expõe **somente** `template_ref`, `version_ref`, `catalog_revision`, `meta_category`, `purpose_ref`, `requires_s0_recheck:true`, `send_authorized:false`, `production_authorized:false`. A prévia mantém `planning_flow_ref`, `campaign_ref` e `plan_revision` como *pistas sintéticas de continuidade*, não como prova de campanha/ator validado em produção.

A saída não inclui ticket interno WA-26, lead, caso, identificador de concessionária/WABA/App, destinatário, texto/componentes, hash, consentimento nem política interna. `meta_approval_verified`, `consent_verified`, `s0_source_authenticated`, `graph_dispatch_authorized`, `provider_sync_performed`, `send_authorized` e `production_authorized` permanecem `false`.

## M15-B — Testes adversariais

`integrations/whatsapp-meta/wa15-f02-planner-preview.test.ts`: **40 casos M15-01..40** de isolamento entre lojas/WABAs, variante de idioma, template pendente/pausado, digest ou versão divergente, mudança de ator/caso/campanha, consentimento/opt-out, concessão ausente, política WA-26 versus M14, fornecedor alegado M13 desatualizado, dados inválidos/getters, anti-vazamento e múltiplos candidatos ordenados.

**Evidência funcional:** registrar SHA exato e CI completo após confirmação; o teste de Graph PG17 físico histórico é de **outro** escopo e não testa M15. A nova suíte deve totalizar 1.553 Meta offline (base 1.513 + 40 M15), sem somar PG17.

## M15-C — Fronteiras contratuais

O retorno **não** é uma resposta homologada S0→F02. O contrato definitivo exigirá revisão conjunta de S0/S1, OpenAI/F02 e Meta, com:

- Identidade real M2M/tenant/ator, RLS por loja, autorização expressa de caso/campanha, catálogo com aprovação e versão Meta autenticadas e consistentes, snapshot S0 com cursor/revisão/continuidade.
- Política vigente de consentimento e opt-out por finalidade em fonte S0 real, provenance de eventos e readback consistente de revisões de catálogo, consentimento, autorização e campanha.
- A F02 escolhe/planeja **somente dentro da lista autorizada pela S0**, não inventa template/versão, não recebe segredo/PII desnecessária e **não** usa retorno `LAB_F02_PREVIEW_UNVERIFIED` para produção.
- A continuidade de plano/fluxo é uma expectativa documental, sem credencial, token de reserva nem garantia de idempotência. É preciso contrato para plan/flow ref, plan revision, expiração, mudanças de campanha e recheck, e projeção mínima de evidências na [Issue #9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9) quando existir despacho.
- A porta `PRE_DISPATCH` autenticada, com recheck transacional de versão, consentimento, opt-out, template e reserva/idempotência **permanece exclusivamente S0**, [Issue #10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10). O planejamento da [Issue #7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7) não se confunde com esse despacho; #8 é fonte de App/WABA/grants.

## M15-D — Dependência e decisão

- [ ] S0/S1 ratificar fonte + contrato real de catálogo e planejamento F02; OpenAI/F02 revisar formato, campos mínimos e continuidade; Infra/Proprietário ratificar ativos/autoridade.
- [ ] Testar execução física real com principal e scope, snapshot, leitura consistente e aplicação de política nos serviços próprios de S0, sem confundir resultado de `APPROVED` na fixture com Meta real.
- [ ] Estabelecer garantia de concorrência e revogação entre planejamento e envio, através de reserva/recheck **transacional** por S0 na #10; nem M13, M14 nem M15 possuem lock, serialização real, assinatura ou proteção ABA.
- [ ] Aguardar aceite formal interfrentes antes de merge/deploy/produção.

**Estado:** M15-A/B/C avançam apenas offline; M15-D e marco principal abertos. Sem conexão de Graph, credenciais, SQL produtivo, HTTP ACK, envio, merge ou deploy.
