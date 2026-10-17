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

## Auditoria e reparos de exclusividade (17/10/2026)

**Evidência atual:** [GitHub Actions #39064447771](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39064447771) — PostgreSQL 17 descartável, suíte concluída com sucesso.

| Regressão | Resultado |
|---|---|
| Global UNIQUE cliente E.164: segunda concessionária não grava telefone existente | PASS |
| Emissor exclusivo por loja: número idêntico em dois canais é negado | PASS |
| C01: segunda loja recebe item recusado genérico sem histórico alheio | PASS |
| Corrida entre duas concessionárias distintas pelo mesmo telefone | PASS; 1 lead, 1 ciclo, 1 aceite, 1 rejeição |
| Reatribuição: operador perde leitura do lead e da conversa antiga | PASS |
| Operador designado recebe apenas lead do seu caso | PASS |
| RLS A/B, importação, eventos, handoff humano e simultaneidade por mesma chave | PASS |

**Supersessão:** os relatórios de CI anteriores que davam PASS para *mesmo cliente telefônico em lojas A/B* documentam testes antigos — esse resultado **não é mais um critério válido** e foi substituído pela exclusividade global conforme orientação posterior. Preservar os links históricos apenas como trilha de auditoria.

**Pendente:** validação de privacidade do índice global e inferência de recusas; procedimento de número reciclado/troca de concessionária; provas Supabase Auth/REST; autorização documental consolidada; recuperação/backup e retenção. Nenhuma migration comercial no remoto, nem produção ativada.
