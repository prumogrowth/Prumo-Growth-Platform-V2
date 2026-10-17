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
