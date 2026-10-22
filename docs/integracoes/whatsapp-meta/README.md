# WhatsApp/Meta — Leia primeiro (mapa documental vigente)

**Atualizado:** 22/10/2026. **Destinatário:** Diretor, auditor, equipes S0/S1/OpenAI, frente MCP, Consultores e desenvolvedor da integração Meta. **Ambiente:** PR #2 Draft, documentação sem deploy/merge ou uso de Graph real.

> **COMECE AQUI.** Há relatórios técnicos históricos neste diretório e documentos de 17/10 no pacote de 55 fontes. **Não interprete isoladamente um documento antigo como decisão vigente.** As regras aprovadas mais recentes estão consolidadas nos links abaixo, cada uma com origem e indicação de trechos superados. Nem toda regra aprovada foi implementada.

## Ordem de leitura

| Para descobrir | Arquivo oficial de referência | Função |
|---|---|---|
| O que o sistema **deve fazer** | [01 — Especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) | Regras completas por domínio, exemplos, exceções, papéis das IAs, estados e limitações |
| Qual decisão prevalece e quem decidiu | [00 — 22 regras WDC com precedência](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md) | Índice de decisões com IDs, proveniência, glossário e pendências |
| Por que documento antigo diz outra coisa | [02 — Mapa de conflitos por documento e seção](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md) | Relação da regra substituída com a atual, sem perder histórico |
| O que outras frentes decidiram que impacta nosso contrato | [WA-22 — Revisão documental interfrentes](./wa22-revisao-cruzada-outras-frentes-contratos-2026-10-22.md) | Novos limites F03, S0/S1, evidências de contato, C09, mídias, campanhas e MCP sem presumir implementação |
| Se a documentação da própria frente está pronta para a próxima fase | [WA-23 — Auditoria editorial final (22/10)](./wa23-auditoria-final-documentacao-propria-2026-10-22.md) | Inventário, cobertura, correções, pendências identificadas e fronteira da responsabilidade documental |
| Qual é o estado da auditoria técnica e dos primeiros reparos | [WA-24 — Auditoria técnica inicial e reparos (22/10)](./wa24-auditoria-tecnica-inicial-reparos-2026-10-22.md) | Inventário verificável de código, comparação WDC, evidência CI, fixes WA-17 e riscos ainda não homologados |
| O que a auditoria encontrou e reparou | [WA-19 — Auditoria documental](./wa19-auditoria-documental-reconciliacao-2026-10-21.md) | Achados, limites, reparos e pendências |
| Histórico de decisões recentes | [WA-17B](./wa17b-mcp-templates-multimidia-ia-delegada-2026-10-20.md), [WA-18](./wa18-alinhamento-decisorio-respostas-responsavel-2026-10-20.md), [WA-18B](./wa18b-alinhamento-fechamento-optout-variaveis-falhas-cadencia-2026-10-20.md), [WA-18C](./wa18c-falhas-consecutivas-taxonomia-interna-templates-2026-10-20.md) | Proveniência cronológica; partes superadas identificadas |
| O que foi testado de verdade | [WA-16/17 — fechamento de validação](./wa16-wa17-fechamento-validacao-e-pausa-2026-10-20.md) | Distingue casos escritos, verificações V8 e CI Node/PG17 não comprovado |
| O que falta incorporar ao projeto global | [Issue #13](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/13) | Emendas globais às fontes históricas/versionadas, fora desta frente |
| Contratos operacionais e código do adaptador | [README do código WhatsApp](../../../integrations/whatsapp-meta/README.md) | Fases e candidatos técnicos, NÃO prova de produção |
| Escopo da futura interface MCP | [Issue #11](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/11) | Contratos de templates para outra frente construir servidor MCP real |

## Funcionalidade aprovada — assinatura de Diretor, Gestor e Consultor

[WA-20 — Identificação visível do atendente: o que a Meta oferece e como a plataforma poderá implementar](./wa20-identificacao-visivel-atendente-assinatura-mensagem-2026-10-21.md). A Meta envia pelo número da concessionária; para aparecer no WhatsApp do cliente, o nome poderá ser acrescentado pelo backend ao **texto da mensagem**. Autoria de operador permanece separada e autenticada no S0. O formato/frequência exata ainda não foi fechado; mensagens de template obedecem ao conteúdo/variáveis aprovados. **Não implementado.**

> **DECISÃO DE 21/10 (WA-21):** os papéis visíveis passam a ser **Diretor** (antes responsável), **Gestor** (mantido) e **Consultor** (antes operador). A assinatura automática nas mensagens humanas usará `Consultor Nome:\nMensagem`, `Gestor Nome:\nMensagem` ou `Diretor Nome:\nMensagem`. **Isso substitui o formato provisório da WA-20**; o recurso continua não implementado. [Leia a decisão e os limites técnicos WA-21](./wa21-papeis-diretor-gestor-consultor-assinatura-2026-10-21.md).

## Atualização transversal — outras frentes e nome da plataforma (22/10)

**A plataforma de atendimento comercial permanece sem nome próprio definido.** É desenvolvida pela Prumo para atendimento comercial às concessionárias e à comercialização do **LiberaCred, produto da instituição financeira**. Não usar “LiberaCred” para nomear o software; o documento `17_Identidade_e_Nome_da_Plataforma_v0_1.md` do pacote 17/10 já separava os conceitos.

**[WA-22 — Revisão das outras frentes e contratos de interface](./wa22-revisao-cruzada-outras-frentes-contratos-2026-10-22.md)**: S0 (#1), OpenAI (#3), pessoas/S1 (#5), CF-OP (#7), ponte S0/OpenAI (#8/#12), interface visual e pacote histórico. Identifica fronteiras de prova de envio humano, pausa de novos leads, histórico/cutoff F03, mídia, janela Meta versus conclusão humana/C09, indicador interno de leitura, regras bancárias, ofertas/campanhas e auditoria MCP. **A leitura não transforma documentos Draft em integração implementada.**

## Política editorial

1. **Decisão vigente [D]** é diferente de **documento histórico [H]**, **proposta [P]**, **homologação externa [V]** e **estado técnico [T]**. Em caso de conflito, usar a referência 01 e os IDs WDC de 00; uma nova decisão só altera o tema expressamente revisado.
2. **Nenhuma regra antiga foi apagada.** O mapa 02 registra a origem e a decisão superadora. A titularidade jurídica da Meta, liberação de dados sensíveis e demais dependências externas permanecem explicitamente pendentes.
3. **As palavras importam:** categoria Meta MARKETING/UTILITY ≠ FINALIDADES de template ≠ finalidade do consentimento/opt-out. Um modelo pode ter múltiplas finalidades, com permissão independente por contexto.
4. **Separação de frentes:** Meta responde por contratos, transporte, validações e evidências; S0 por transição comercial, persistência e autorização do envio; equipe MCP futura pelo servidor/ferramentas, identidade e delegação administrativa.
5. **Vigência não é conclusão de código.** Novas regras de finalidades, duas falhas→perdido e MCP estão documentadas, não homologadas como funcionalidades. Não registrar testes simplesmente escritos como “aprovados”.
6. **Novas mudanças:** acrescentar data, fonte, ID, trecho revogado, regra substituta, política externa pendente, efeitos em contratos e vínculo à issue/PR; atualizar índice 00 e especificação 01. Não editar silenciosamente uma fonte histórica como se ela nunca tivesse dito outra coisa.

## Biblioteca de relatórios da frente (referências e registros de engenharia)

Arquivos abaixo permanecem pesquisáveis e preservados por fase. São históricos ou detalhamentos, **não substituem os documentos vigentes 00/01/02**.

### Arquitetura, titularidade, interfaces e provas iniciais

- [adr-001-transporte-webhook-supabase-vs-n8n.md](./adr-001-transporte-webhook-supabase-vs-n8n.md)
- [conciliacao-pr1-pr2-s0-whatsapp-v0_1.md](./conciliacao-pr1-pr2-s0-whatsapp-v0_1.md)
- [contrato-webhook-meta-supabase-v0_1.md](./contrato-webhook-meta-supabase-v0_1.md)
- [decisao-titularidade-meta-por-concessionaria-v1_0.md](./decisao-titularidade-meta-por-concessionaria-v1_0.md)
- [estrategia-apis-sem-credenciais-reais-v0_1.md](./estrategia-apis-sem-credenciais-reais-v0_1.md)
- [interface-compartilhada-s0-meta-v0_1.md](./interface-compartilhada-s0-meta-v0_1.md)
- [modelo-tecnico-ingresso-identidade-idempotencia-v0_1.md](./modelo-tecnico-ingresso-identidade-idempotencia-v0_1.md)
- [revisao-cruzada-wa01b-s0-028-029-v0_1.md](./revisao-cruzada-wa01b-s0-028-029-v0_1.md)
- [poc-meta-sandbox-documentacao-publica-2026-10-17.md](./poc-meta-sandbox-documentacao-publica-2026-10-17.md)

### WA-01 a WA-06 — ingestão, credenciais, transação e laboratório

- [wa01c-ids-eventos-meta-e-correlacao-v0_1.md](./wa01c-ids-eventos-meta-e-correlacao-v0_1.md)
- [wa01d-get-verificacao-meta-v0_1.md](./wa01d-get-verificacao-meta-v0_1.md)
- [wa02-reparos-pos-auditoria-2026-10-18.md](./wa02-reparos-pos-auditoria-2026-10-18.md)
- [wa02a-graph-outbound-texto-v0_1.md](./wa02a-graph-outbound-texto-v0_1.md)
- [wa02b-graph-templates-c06-v0_1.md](./wa02b-graph-templates-c06-v0_1.md)
- [wa02c-simulacao-despacho-s0-meta-v0_1.md](./wa02c-simulacao-despacho-s0-meta-v0_1.md)
- [wa02d-conciliacao-status-meta-sintetica-v0_1.md](./wa02d-conciliacao-status-meta-sintetica-v0_1.md)
- [wa03a-auditoria-integrada-e-ocorrencias-v0_1.md](./wa03a-auditoria-integrada-e-ocorrencias-v0_1.md)
- [wa03b-auditoria-pendencias-e-reparos-v0_1.md](./wa03b-auditoria-pendencias-e-reparos-v0_1.md)
- [wa04a-roteamento-credenciais-meta-offline-v0_1.md](./wa04a-roteamento-credenciais-meta-offline-v0_1.md)
- [wa04aud1-auditoria-integrada-235-testes-v0_1.md](./wa04aud1-auditoria-integrada-235-testes-v0_1.md)
- [wa04b-get-post-roteamento-hmac-v0_1.md](./wa04b-get-post-roteamento-hmac-v0_1.md)
- [wa04c-ciclo-credenciais-sem-token-v0_1.md](./wa04c-ciclo-credenciais-sem-token-v0_1.md)
- [wa04d-ciclo-credenciais-concorrencia-v0_1.md](./wa04d-ciclo-credenciais-concorrencia-v0_1.md)
- [wa05a-ingresso-transacional-simulado-v0_1.md](./wa05a-ingresso-transacional-simulado-v0_1.md)
- [wa05aud1-auditoria-retroativa-ingresso-recuperacao-v0_1.md](./wa05aud1-auditoria-retroativa-ingresso-recuperacao-v0_1.md)
- [wa05b-recuperacao-ingressos-sem-token-v0_1.md](./wa05b-recuperacao-ingressos-sem-token-v0_1.md)
- [wa05c-contrato-handoff-meta-s0-v0_1.md](./wa05c-contrato-handoff-meta-s0-v0_1.md)
- [wa05d-aud1-atestacao-interna-offline-v0_1.md](./wa05d-aud1-atestacao-interna-offline-v0_1.md)
- [wa05d-porta-interna-s0-simulada-v0_1.md](./wa05d-porta-interna-s0-simulada-v0_1.md)
- [wa06-aud1-auditoria-contrato-atualizado-wa07-v0_1.md](./wa06-aud1-auditoria-contrato-atualizado-wa07-v0_1.md)
- [wa06a-contrato-identidade-servico-replay-s0-v0_1.md](./wa06a-contrato-identidade-servico-replay-s0-v0_1.md)
- [wa06b-serializacao-canonica-prova-interna-v0_1.md](./wa06b-serializacao-canonica-prova-interna-v0_1.md)
- [wa06c-verificacao-independente-python-typescript-v0_1.md](./wa06c-verificacao-independente-python-typescript-v0_1.md)
- [wa06d-a-roteiro-postgresql-atomicidade-v0_1.md](./wa06d-a-roteiro-postgresql-atomicidade-v0_1.md)
- [wa06d-aud2-auditoria-aderencia-execucao-v0_1.md](./wa06d-aud2-auditoria-aderencia-execucao-v0_1.md)
- [wa06d-b-cluster-efemero-recuperacao-poscommit-v0_1.md](./wa06d-b-cluster-efemero-recuperacao-poscommit-v0_1.md)
- [wa06d-pg17-ci-prova-e-escopo-s0-2026-10-20.md](./wa06d-pg17-ci-prova-e-escopo-s0-2026-10-20.md)

### WA-07 a WA-16 — janela, conciliação, CI e recuperação

- [wa07-contrato-janela-e-templates-cf-op-02-v0_1.md](./wa07-contrato-janela-e-templates-cf-op-02-v0_1.md)
- [wa08-conciliacao-status-validacao-estrita-offline-v0_1.md](./wa08-conciliacao-status-validacao-estrita-offline-v0_1.md)
- [wa09-evidencia-tecnica-status-validador-testado-offline-v0_1.md](./wa09-evidencia-tecnica-status-validador-testado-offline-v0_1.md)
- [wa10-vinculo-inverso-tentativa-wamid-offline-v0_1.md](./wa10-vinculo-inverso-tentativa-wamid-offline-v0_1.md)
- [wa11-indice-bidirecional-lab-e-regressao-local-v0_1.md](./wa11-indice-bidirecional-lab-e-regressao-local-v0_1.md)
- [wa12-commit-desconhecido-vinculo-tecnico-offline-v0_1.md](./wa12-commit-desconhecido-vinculo-tecnico-offline-v0_1.md)
- [wa13-ponte-conciliacao-commit-confirmado-offline-v0_1.md](./wa13-ponte-conciliacao-commit-confirmado-offline-v0_1.md)
- [wa14-evidencia-ci-offline-integracao-2026-10-20.md](./wa14-evidencia-ci-offline-integracao-2026-10-20.md)
- [wa15b-porta-tipificada-s0-042-offline-ci-2026-10-20.md](./wa15b-porta-tipificada-s0-042-offline-ci-2026-10-20.md)
- [wa15c-primeira-prova-cruzada-typescript-postgresql-2026-10-20.md](./wa15c-primeira-prova-cruzada-typescript-postgresql-2026-10-20.md)
- [wa16-commit-incerto-e-recuperacao-laboratorio-2026-10-20.md](./wa16-commit-incerto-e-recuperacao-laboratorio-2026-10-20.md)
- [wa16-wa17-fechamento-validacao-e-pausa-2026-10-20.md](./wa16-wa17-fechamento-validacao-e-pausa-2026-10-20.md)

### WA-17 em diante — autoria, decisões e auditoria

- [wa17-gestao-manual-templates-variaveis-e-aprovacao-meta-2026-10-20.md](./wa17-gestao-manual-templates-variaveis-e-aprovacao-meta-2026-10-20.md)
- [wa17b-mcp-templates-multimidia-ia-delegada-2026-10-20.md](./wa17b-mcp-templates-multimidia-ia-delegada-2026-10-20.md)
- [wa18-alinhamento-decisorio-respostas-responsavel-2026-10-20.md](./wa18-alinhamento-decisorio-respostas-responsavel-2026-10-20.md)
- [wa18b-alinhamento-fechamento-optout-variaveis-falhas-cadencia-2026-10-20.md](./wa18b-alinhamento-fechamento-optout-variaveis-falhas-cadencia-2026-10-20.md)
- [wa18c-falhas-consecutivas-taxonomia-interna-templates-2026-10-20.md](./wa18c-falhas-consecutivas-taxonomia-interna-templates-2026-10-20.md)
- [wa19-auditoria-documental-reconciliacao-2026-10-21.md](./wa19-auditoria-documental-reconciliacao-2026-10-21.md)
- [wa20-identificacao-visivel-atendente-assinatura-mensagem-2026-10-21.md](./wa20-identificacao-visivel-atendente-assinatura-mensagem-2026-10-21.md)
- [wa21-papeis-diretor-gestor-consultor-assinatura-2026-10-21.md](./wa21-papeis-diretor-gestor-consultor-assinatura-2026-10-21.md)
- [wa22-revisao-cruzada-outras-frentes-contratos-2026-10-22.md](./wa22-revisao-cruzada-outras-frentes-contratos-2026-10-22.md)
- [wa23-auditoria-final-documentacao-propria-2026-10-22.md](./wa23-auditoria-final-documentacao-propria-2026-10-22.md)
- [wa24-auditoria-tecnica-inicial-reparos-2026-10-22.md](./wa24-auditoria-tecnica-inicial-reparos-2026-10-22.md)

### Índices vigentes e matrizes adicionais

- [00-decisoes-vigentes-precedencia-documental-2026-10-21.md](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md)
- [01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md)
- [02-mapa-fontes-conflitos-e-emendas-2026-10-21.md](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md)

**Cobertura documental em 22/10/2026:** a auditoria editorial WA-23 conferiu **63 arquivos Markdown** (README + 62 links). Com a inclusão posterior de **WA-24**, o diretório passa a **64 Markdown** (README + **63 links**), sujeitos a commits futuros. O novo documento inicia auditoria TÉCNICA e reparos, sem significar teste nativo verde ou homologação. Os históricos têm aviso de precedência ou nota contextual, quando necessário. O ZIP de 55 documentos históricos de 17/10 segue preservado fora deste diretório. Essa biblioteca não contém ferramentas MCP executáveis.
