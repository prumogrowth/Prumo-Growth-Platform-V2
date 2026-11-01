# Auditoria M13 — catálogo de templates (31/10/2026)

**Escopo:** exclusivamente Meta offline, módulo `wa13-template-catalog-reconciliation.ts`, suíte `wa13-template-catalog-reconciliation.test.ts`, inspeção legada `graph-template-provider-observation.ts`, contratos e checklist correlatos. Nenhuma alteração S0/S1, Infra, F02 ou produção. **A M13 principal permanece aberta** enquanto não existir contrato ratificado de sincronização S0↔Meta e autorização de origem.

## Parecer

O validador não executa Graph nem SQL e nunca concede autorização de aprovação, envio ou efeito comercial. Foram identificados e corrigidos três defeitos de consistência/robustez e criado recheck adicional, todos confinados à própria frente:

**AUD-M13-01 — vínculo de versão incompleto (relevante):** o lote podia resultar `LAB_CATALOG_RECONCILED_UNVERIFIED` com template `APPROVED` de mesmo ID, nome e categoria, mas **BODY/BUTTONS diferentes** do conteúdo associado à versão local. O registro `version_ref` não estava vinculado aos componentes alegados. Correção: `provider_components_sha256` torna-se campo obrigatório da entrada S0 **de laboratório** e também do candidato. É comparado a SHA-256 do JSON canônico dos componentes normalizados pelo inspetor `inspectMetaTemplateProviderRecord` (ordem HEADER/BODY/FOOTER/BUTTONS e componentes suportados). Divergência recusa o lote inteiro com `COMPONENT_VERSION_MISMATCH`. O hash é de valores **alegados**, não prova que a Meta aprovou esse conteúdo nem que S0 o armazenou imutavelmente. O contrato lab ainda não é wire-format ratificado pela S0.

**AUD-M13-02 — rejeição indevida de metadados opcionais legítimos (compatibilidade):** a M13 exigia seis campos exatos em cada detalhe; o inspetor Meta existente aceita também `parameter_format`, `quality_score` e `rejected_reason`. Correção: permissão explícita somente desses três campos opcionais como dados ignorados para decisão de aprovação. Getters, campos desconhecidos e símbolos continuam negados. `quality_score` ou metadado livre não comprovam autorização.

**AUD-M13-03 — coerção de hash malformado (robustez):** a expressão regular do digest do catálogo poderia invocar `toString` de objeto em campo não textual. Correção: verificar `typeof === 'string'` antes de aplicar regex. Regressão exige nenhum acesso ao método adversarial.

**AUD-M13-04 — ausência de recheck explícito de candidato offline (barreira adicional):** criada `recheckWa13CandidateOffline(candidate,freshHost,freshS0,freshProvider)`. Reexecuta a conciliação sobre **novos argumentos injetados no laboratório** e exige correspondência exata de App, concessionária, WABA, template/versão/revisão, digest de componentes, categoria e flags não autorizantes. Recusa pausa/opt-out não afirmado aqui, versão trocada, expiração, catálogo negado e reutilização cross-tenant. Mesmo o resultado `LAB_RECHECKED_UNVERIFIED` mantém todas as flags produtivas falsas. Esta rechecagem não é uma reserva, lock, transação S0, garantia de observação independente nem substitui `PRE_DISPATCH` da #10.

## Regressões

- 43 testes anteriores `M13-01..43`, preservados.
- 19 testes novos `AUD-M13-44..62`: BODY alterado; botões alterados; metadados opcionais reconhecidos e desconhecidos; hash inválido; recheck estável sem autoridade; PAUSED, mudança de versão, cross-shop, cross-WABA, conteúdo/validade, revogação, catálogo negado; getters em candidaturas/metadata e hash objeto com `toString` hostil.
- Meta offline esperado: **1.447 testes**, sendo **62 próprios M13** e 1.385 anteriores. As **18 provas físicas PG17** pertencem ao laboratório de ingresso S0 histórico, **não** autenticam a conciliação M13. Testes de recebimento e scanner ACK são subconjuntos ou verificações separadas; não somar para inflar cobertura.
- **CI funcional:** [41262001974](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41262001974), SHA `745f54acd8255bea728c5ab7c87848d5018ad66b`: **1.447/1.447 Meta offline, 18/18 PG17**, dois jobs `success`, scanner ACK lexical aprovado. O run intermediário `ec39afd5bc16cb5ecd1a27c12ae42a303c6d9acf` aconteceu antes da atualização das fixtures e falhou, não servindo de homologação.

## Dependências não resolvidas

- [ ] **Fonte de verdade S0/S1** com revisões independentes de App/grant/binding/catálogo/versão e vínculo autenticado de tenant↔concessionária, CAS ou transação e readback; [Issue #8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8). M09-01/M09-02 são entregas laboratoriais, não fonte Meta real.
- [ ] **Proveniência do Graph Meta e identidade da WABA**: detalhe por template e eventual paginação/cursor sob um mesmo contexto autenticado, prova real de titularidade, delegação, aprovação, vigência e sincronização de mutações. Não confiar em `observed_at_ms` de fixture ou alegação `APPROVED` sem recibo fonte.
- [ ] **F02 e PRE_DISPATCH**: nenhum candidato M13 é permissão de campanha, consentimento, opt-out, versão elegível, posse IA ou envio. Direitos efetivos reservados à S0, nas [#7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7) e [#10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10).
- [ ] **Concorrência/ABA:** duas comparações locais são insuficientes para detectar uma mutação que ocorre entre leituras e retorna ao mesmo estado ou uma alteração após o último snapshot; exigir trava/revisão transacional e recheck no commit real. O digest normalizado não constitui assinatura ou recebimento autenticado.

**Status:** M13-A/B/C concluídos apenas para laboratório, com auditoria corretiva; M13-D e o marco principal continuam `[ ]`. Sem merge, deploy, Graph, SQL, HTTP ACK, token real ou efeito comercial.
