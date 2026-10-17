# Prumo — evidências de aceite PARCIAL S0 (17/10/2026)

Última suíte de regressão: [GitHub Actions #39062435159](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39062435159).
Banco: PostgreSQL 17 efêmero; identidade Supabase simulada exclusivamente para os testes. Nenhuma operação Meta, OpenAI, Banco ou MCP real. Não é aceite de produção.

## PASS apenas no escopo explicitamente testado

| Critério | Evidência |
|---|---|
| S0-A1 | FK cruzada A/B bloqueada; também FK lead-ciclo-caso na mesma loja |
| S0-A2 | Lote novo preserva novo item/reencontro e o histórico anterior, mesma chave não duplica (simulação SQL) |
| S0-A3 | Nono status comercial rejeitado |
| S0-A4 | Gestão e operações confinadas à loja/caso: SQL/RLS, gestores A/B e operadores |
| S0-A5 | Repetição de inbound com mesmo canal/ID não duplica; ID distinto preservado (simulação SQL) |
| D41 AP41-01/02/03 | Gestor A lê conversas D2 completas da sua loja, inclusive IA; B não |
| D41 AP41-05/06/09 | Autoatribuição, resposta simulada, remanejamento e revogação |
| Segurança da concessão | Usuário sem vínculo, anon, operador sem designação e vínculo expirar negam leitura/escrita indevida |
| Eventos | UNIQUE(ciclo,versão) para histórico impede duplicação, ainda sem serviço de transições completo |

**Logs e consultas realmente executados, não só expectativa do roteiro.** As migrations 001–005 estão apenas no GitHub e no PostgreSQL efêmero; projeto Supabase remoto continua SEM tabelas comerciais/migrations.

## Ainda NÃO VALIDADO

- Contrato real C01/C02 (API transacional e ingestão de provedores), concorrência multiworker, consulta ao id Meta real.
- Supabase Auth/Data API/Storage com identidades reais de teste, sem usar dados pessoais verdadeiros.
- Projeção D3/D4 e controles de acesso de cadastro/banco (sem tabela sensível implementada).
- AP41-07/08: correção versionada e remessa/resultado bancários simulados; AP41-10/11/12: MCP com confirmação e auditoria.
- Garantia atômica de mudança de estado + evento; contratação/uso dos provedores; painéis e fluxos reais.
- Retenção/LGPD, backup/restauração e estratégia operacional aprovada; não há testes RET/RES/REC integrais.
- Revisão humana final de migrações, configuração de grants/toggles API e procedimento de recuperação antes de deploy.

**Portão: PR continua DRAFT. Não fazer merge ou deploy remoto somente com os PASS desta página. A régua documental histórica 19F não é modificada automaticamente.**

## Incremento C01 e eventos atômicos — evidência em 17/10/2026

Evidência: [CI #39063441684](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39063441684), PostgreSQL 17 descartável.

| Teste da nova implementação | Resultado |
|---|---|
| TX-C01: função transacional de importação, linhas rejeitadas e reentrega com mesma chave | PASS (CI) |
| TX-AUTH: esquema interno não acessível a `anon` / `authenticated` | PASS (CI) |
| TX-STATUS: versão esperada, prova de inbound sintética, evento e idempotência | PASS (CI) |
| TX-HANDOFF: ciclo com caso humano não volta para atendimento pela IA | PASS (CI) |
| TX-CONC: duas conexões simultâneas, sem duplicar lote/lead/ciclo/item | PASS (CI) |

A função do lote **não é endpoint público**: exige execução interna com papel SQL `postgres` e verifica o ator gestor/loja. Ela ainda carece de um adaptador de identidade real, de política de retenção e de auditoria operacional. O controle de concorrência foi comprovado especificamente para duas chamadas concorrentes com a **mesma chave de lote**; lotes distintos, filas e concorrência de atribuições permanecem pendentes.

**S0 não homologado:** C02 real, Auth real, APIs Meta/Banco, acesso fino D3/D4, reações externas, backup/restauração e portões LGPD permanecem bloqueados. Nenhuma migração comercial foi aplicada ao Supabase remoto. Não alterar a porcentagem histórica de planejamento (19F) por esses testes.

## Auditoria corretiva — regra esclarecida de cliente x emissor (17/10/2026)

**Correção do registro anterior:** o requisito que impunha UNIQUE global no telefone de cliente foi **retratado**. O número do cliente pode existir em concessionárias diferentes; apenas o número de **atendimento emissor da Prumo** é exclusivo. A migração 007 foi excluída antes de implantar e a importação 006 voltou a deduplicar por `(concessionaria_id,telefone_cliente_normalizado)`. A migração 008 (leitura do lead por operador designado) permanece.

O link do CI antigo #39064447771 refere-se a implementação retirada e não serve como aceite vigente.

**Evidência corrigida e efetivamente executada:** [GitHub Actions #39065589861](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39065589861) — PostgreSQL 17 efêmero, resultado **PASS** com conferência dos logs. Critérios aprovados nesta simulação:
- Mesmo telefone em lojas A/B: 2 leads/ciclos independentes, RLS gestor A/B e nenhuma conversa cruzada.
- Mesmo telefone reimportado na MESMA loja: sem duplicação, com reencontro.
- Emissor Prumo repetido para duas lojas: rejeição por constraint única.
- Dois lotes concorrentes entre A/B para o mesmo cliente: dois leads/ciclos isolados, 0 itens rejeitados por compartilhamento.
- Operador não designado ou desatribuído não lê lead/conversa de outro caso.
- Demais testes C01, eventos, handoff e idempotência continuam obrigatórios.

**Portões permanecem:** Auth/REST em ambiente Supabase integrado, revisão de grants, backup/restauração, LGPD, aprovação humana, nenhuma migração no remoto.

**Evidência específica:** log `PASS TX-CROSS-SHOP: mesmo cliente em A e B sob concorrencia; historicos isolados`; `PASS TX-C01`, `PASS TX-STATUS`, `PASS TX-HANDOFF`, `PASS TX-CONC` e RLS A/B confirmados. Esses testes não substituem Supabase Auth real nem homologação operacional.

## Incremento C02 simulado — evidência de execução (17/10/2026)

CI [#39066422146](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39066422146) — `success`; conferidos os logs. PostgreSQL 17 descartável, sem canal Meta conectado.

| Caso | Evidência |
|---|---|
| C02-01 | mesmo telefone em A/B com canais diferentes, lead/ciclo independente; mesmo ID externo em A e B permitido |
| C02-02 | canal emissor exclusivo, canal desconhecido recusado, função interna sem acesso dos papéis API |
| C02-03 | segunda mensagem da mesma conversa não duplica status/evento |
| C02-04 | primeira resposta simulada depois de primeiro disparo enviado gera transição com evento |
| C02-05 | retorno após cadastro enviado ao banco cria caso humano; ciclo histórico intacto |
| C02-06 | retorno após vendido cria ocorrência humana distinta; sem retorno à IA |
| C02-07 | mais de um ciclo do mesmo lead não é associado arbitrariamente |
| C02-08 | gestores A/B só veem suas próprias mensagens mesmo com telefone de cliente igual |
| C02-CONC | webhook repetido concorrente cria uma só mensagem; dois eventos distintos em paralelo criam duas mensagens, apenas um lead/ciclo/conversa/evento |

**Limites:** este teste **não** autentica Meta, WhatsApp, IA, opt-in/out ou transporte HTTP; não cancela ENVIOS_TEMPLATE porque o planejador ainda não foi implementado; retorna `CANCELAMENTO_PENDENTE`. Roteamento `IA_PENDENTE`/`HUMANO_PENDENTE` não significa atendimento efetuado. Não libera S0/S2, merge nem implantação remota.

## Auditoria S0/C01/C02 — reparos executados e regressão

**CI validado:** [PostgreSQL 17 #39067051654](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39067051654) — `success`, logs C01/C02/concorrência/RLS conferidos. Dados e Auth exclusivamente sintéticos.

- PASS: C02-02 — rejeição de canal com identificador vazio ou espaços indevidos (migração 010).
- PASS: C02-07 — mensagem com vários ciclos possíveis é armazenada em `mensagens` e `pendencias_inbound_simulado`, sem atribuir ciclo/caso arbitrário, sem acionar IA, com reentrega idempotente (migração 011).
- PASS: C02-08 — gestor de A consegue consultar a pendência A; gestor de B não consegue consultar pendência A.
- PASS: demais C01/C02, mesmo cliente em A/B e emissores únicos, controle de status, handoff e múltiplas conexões concorrentes.

**Classificação: GO apenas para próxima engenharia sintética; NO-GO para uso real.** Documento completo: `docs/AUDITORIA_TECNICA_S0_C01_C02_2026_10_17.md`. Auth real, cancelamento de recontatos, prova bancária, integração Meta, tratamento humano de pendências, LGPD e backup/restauração continuam PENDENTES.

## Recontatos C05/C08 — entrega sintética, validação técnica 17/10/2026

[CI PostgreSQL 17 #39069478063 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39069478063), logs REC-01..06, C05-APPROVAL, C08-GESTOR, C08-PRIVATE e REC-RACE verificados.

| Teste | Resultado |
|---|---|
| REC-01/02 | PASS — plano idempotente e reserva sem transmissão externa |
| REC-03/04 | PASS — resposta C02 cancela programados/reservados da loja A sem afetar B; envio cancelado não volta à reserva |
| REC-05/06 | PASS — cancelamento não altera estado comercial; trilha de eventos e RLS A/B preservados |
| C05-APPROVAL | PASS — template sintético não aprovado recusado sem registro parcial |
| C08-GESTOR / C08-PRIVATE | PASS — gestor autorizado, expected_version, reexecução idempotente, sem execução da função via API |
| REC-RACE | PASS — duas conexões PostgreSQL; reserva→inbound e inbound→reserva não deixam envio obsoleto elegível |

Fonte de escopo: `docs/RECONTATOS_C05_C08_SIMULACAO_2026_10_17.md`.

O texto anterior que indicava **cancelamento de recontatos pendente** refere-se à versão anterior à migração 013; a pendência atual é **cancelamento operacional de envios reais e homologação Meta**, não a gravação sintética de cancelamento. Ainda não existe emissor real nem confirmação de entrega; não computar o aviso final como enviado nem 24 horas de silêncio.
