# Prumo — Auditoria técnica S0/C01/C02 após implementação

Data: 17/10/2026. Estado: **APTO A PROSSEGUIR COM DESENVOLVIMENTO SIMULADO/ISOLADO**; **NÃO HOMOLOGADO PARA OPERAÇÃO REAL NEM PARA DEPLOY REMOTO**.

## Fontes de comparação
- Precedência: documento 00A.
- Decisões vigentes: 13A, 21, 22, 23, 41.
- Especificações candidatas: 25, 26 (especialmente C01/C02/C14), 30, 38 (S0-A1–A5), 39 (IDM/ACC/REC/RES), 40 (contratos e campos).
- Regra confirmada posteriormente pelo responsável: mesmo cliente pode usar A/B/C; **somente número de atendimento da Prumo é exclusivo por concessionária**. Vide `docs/REGRA_NUMEROS_ATENDIMENTO_CLIENTE_2026_10_17.md`.

## Evidência técnica efetiva

[CI PostgreSQL 17 #39067051654 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39067051654), executado em banco descartável local com identidades sintéticas. Testes reexecutados após migrations **010 e 011**; logs conferidos.

| Requisito | Veredito de teste SQL |
|---|---|
| Cliente com mesmo telefone em A e B, leads/ciclos/conversas isolados | PASS |
| Identificador de canal emissor exclusivo, não vazio e sem espaços indevidos | PASS |
| FKs compostas proíbem vínculo de loja cruzada | PASS |
| C01 reimportação idempotente sem sobrescrever conversas | PASS |
| Oito estados comerciais e evento por versão, sem nono status | PASS |
| C02 mensagem duplicada mesma fonte/ID sem duplicação | PASS |
| C02 duas mensagens distintas concorrentes sem perder mensagens ou duplicar ciclo/conversa | PASS |
| C02 retorno pós-remessa e pós-venda somente humano; sem reversão de status | PASS |
| C02 múltiplos ciclos do mesmo lead → persistir entrada para revisão sem atribuir ciclo falso | PASS |
| RLS de gestor por loja, operador por caso/revogação | PASS no PG com Auth simulado |
| Acesso da API às funções internas C01/C02 | DENY em roles PG simulados |

Não extrapolar: `PASS` em PostgreSQL 17 isolado **não prova Supabase Auth/REST, operação Meta ou Banco**, nem cobertura integral de retenção/recuperação.

## Achados e reparos aplicados nesta auditoria

**A-01 (corrigido): canal emissor sem validação mínima.** Existia UNIQUE global, mas `identificador_emissor` aceitava strings vazias ou com espaços externos. Migration `010_s0_channel_validation.sql` exige identificador não vazio e sem espaços extras/caracteres de controle. C02-02 ampliado. **Não substitui normalização e autenticidade do ID oficial Meta.**

**A-02 (corrigido): entrada válida com múltiplos ciclos era descartada por exceção.** O motor recusava escolher ciclo arbitrariamente (correto), mas não persistia a mensagem (risco de perda de entrada). Migration `011_s0_c02_ambiguous_inbox.sql` cria pendência segregada por loja; C02 agora grava mensagem, retorna `HUMANO_PENDENTE` e exige revisão antes de relacionar o ciclo. C02-07/C02-08 ampliados. **A fila de resolução humana efetiva ainda não existe.**

**A-03 (mantido/confirmado): telefones do cliente por loja.** UNIQUE `(concessionaria_id,telefone_cliente_normalizado)`, nunca UNIQUE global; emissor `canais_loja.identificador_emissor` globalmente UNIQUE. A migração 007 errada segue ausente.

## Pendências que impedem homologação operacional

1. **Auth real e exposição Data API:** SQL usa `auth.uid()` simulado no CI; validar `anon`, `authenticated`, papéis, sessões revogadas e grants REST reais em sandbox Supabase. Endpoints internos só via adaptador autenticado. Não expor `postgres` nem segredos no navegador.
2. **C02 externo:** não há webhook Meta autenticado (assinatura, ID real do emissor, `occurred_at`, tipo de conteúdo, validação e replay), mídia/retentativas, autenticação de origem ou autorização para mensagens financeiras reais.
3. **Recontatos:** C02 retorna `CANCELAMENTO_PENDENTE`. C05/C08, agenda de envios, opt-out, cancelamento atômico, corrida com executor e evidência de template ainda não implementados. Nunca declarar que os recontatos foram cancelados.
4. **Pendências humanas:** tabela de mensagens ambíguas foi criada, mas não há UI/fila/atribuição efetiva nem decisão aprovada de desambiguação. Retornos pós-banco/vendido criam mock de caso, não atendimento humano funcional.
5. **Operações humanas D3/D4/C12:** não há cadastro/banco real, prova de venda/recusa, workflow de versões, transporte de mensagens humanas ou checagem de entrega. `INSERT` sintético em `public.mensagens` não pode ser confundido com envio externo. Revisar a superfície de escrita autenticada antes de liberar C12.
6. **Segurança/continuidade:** backups/restauração, retenção e LGPD, opt-in/out, análise de ameaças, testes REC/RES, performance e avaliação de falhas externas ainda pendentes. As provas de CI não cobrem produção.

## Gate

- **GO:** seguir com engenharia do **sandbox de autenticação Supabase** e/ou conclusão de C02/recontatos em modo **100% sintético**, com branch/PR e regressão.
- **NO-GO:** merge automático, deploy de migrations comerciais no Supabase remoto, números WhatsApp reais, integrações OpenAI/Meta/Banco, ativação de clientes e qualquer alegação de S0/S1/S2 homologados.
- Próximo aceite proposto: Auth+REST real escopado, armazenamento de pendência de revisão, cancelamento idempotente de recontatos e trilha de falhas/recuperação. Todas as contratações continuam não realizadas.

Este relatório é auditoria de **código e testes disponíveis**, não garantia absoluta de ausência de falhas.
