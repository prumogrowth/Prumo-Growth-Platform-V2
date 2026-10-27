# Auditoria técnica pós-C05/C08 — Prumo

**Data:** 17/10/2026. **Escopo:** código versionado da branch `feat/s0-fundacao-prumo`; migrações candidatas 001–006, 008–015, suítes SQL de PostgreSQL 17 e GoTrue/PostgREST locais. Não é auditoria de uma plataforma já operando com clientes reais.

**Parecer:** **GO somente para continuar desenvolvimento com dados sintéticos e testes controlados. NO-GO para merge/deploy de produção e WhatsApp real.**

## Fontes normativas
- `00A` (precedência), `13A` (oito estados comerciais), `21–23` (resultado bancário humano, pós-venda e cadastro), `41` (permissões).
- `09` (catálogo, agenda e registros técnicos), `26` (C02/C04/C05/C06/C08/C09; critérios CT-08/13/15), `38` (S0-A1–A5 e S2-A3–A9), `39` (IDM-05, RET-06, REC-04/05).
- Decisão confirmada posteriormente pelo responsável: **o mesmo telefone do cliente pode estar em A/B/C, mas cada número emissor de atendimento Prumo é exclusivo de uma concessionária**. O banco usa lead por `(loja,telefone)`.

## Falhas concretas encontradas e corrigidas

| Código | Falha verificada na revisão de código | Reparo versionado | Prova executada |
|---|---|---|---|
| AUD-REC-01a | Chave idempotente C05 considerava apenas a lista de tentativas e podia devolver plano de **outro ciclo ou canal da mesma loja**, silenciosamente | Migração **015** inclui `ciclo_id`, `canal_id` e `tentativas` no fingerprint | SQL rejeita reutilização da chave para outro ciclo/canal |
| AUD-REC-01b | Planejamento permitia duas tentativas numa ordem cronológica invertida | Migração **015** exige que cada horário seja posterior ao anterior | SQL rejeita sequência inválida e prova rollback sem plano parcial |
| AUD-REC-01c | Reserva C06 sintética consultava o plano, mas não revalidava a **aprovação atual** do template | Migração **015** revalida `aprovado_simulacao` e o canal simulado | SQL desautoriza template antes da reserva, sem alterar tentativa nem criar evento |
| AUD-AUTH-08/09 | Suíte Auth/REST não incluía as quatro tabelas novas de recontatos | Suíte Python ampliada para consulta por gestor A/B, operador, usuário sem vínculo, anônimo, POST indevido e revogação com JWT antigo | Execução local integrada GoTrue/PostgREST: PASS |

Os reparos são SQL/provas locais e não dependem de alterações no Supabase hospedado.

## Evidência de execução

- [PostgreSQL 17 — #39071156341, PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39071156341): inclui `PASS AUD-REC-01`, `PASS REC-RACE` e regressões C01/C02/C05/C08. A execução pós-suíte Auth `#39071193556` também concluiu com sucesso.
- [Supabase Auth + REST local — #39071193575, PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39071193575): `PASS AUTH-01` a `PASS AUTH-09` (rótulos 07–09 aparecem numa ordem técnica própria). Inclui leitura RLS de catálogos, planos, tentativas e eventos A/B, negação de POST e revogação sob JWT ainda válido.
- Banco PostgreSQL descartável e Supabase local via Docker. Usados apenas usuários, números e mensagens fictícios; nenhuma mensagem Meta foi transmitida.
- Testes da concorrência (reserva→resposta e resposta→reserva) continuam PASS no mesmo commit de código.

## Requisitos vigentes preservados

1. Telefone de cliente aparece em lojas diferentes com histórico independente; cada canal emissor Prumo é único de uma loja e não se mistura com outro.
2. Oito status comerciais canônicos continuam distintos dos estados técnicos `programado/reservado/cancelado`.
3. Handoff humano não devolve caso à IA. Recebimento pós-remessa/pós-venda mantém atendimento humano sem inventar status bancário.
4. C02 cancela **apenas envios locais ainda não transmitidos**, guarda eventos e preserva as tentativas. A simulação não permite saída real.
5. Planejadora não escreve templates novos; agenda apenas IDs previamente sinalizados como aprovados **na simulação**. Aprovação simulada não equivale a aprovação Meta.
6. Gestor lê a loja vinculada; operador somente o caso atribuído no domínio D2; não há regra de exposição de D3/D4 implementada.

## Pendências importantes, que NÃO autorizam produção

- **C04, consentimento e opt-out:** falta registro/verificação de base legal, finalidade, supressão por emissor, política de escopo interlojas e decisões pendentes. Não usar o simulador como autorização para contato proativo.
- **C06/C07/C09 reais:** não existe transmissor Meta, assinatura de webhook, estados `sent/delivered/read/uncertain`, callbacks tardios, prova do template final, janela, relógio das 24h, nem regra aprovada para duas falhas qualificadas. Não marcar perdido por silêncio no ensaio.
- **Governança do catálogo:** esquema contém ID/código/versão e flag `aprovado_simulacao`, mas não há processo de publicação Meta/imutabilidade de snapshots de texto/variáveis nem aprovador humano operacional integrado.
- **Backend confiável:** funções privadas aceitam identidade de ator para simulações por `postgres`. Falta camada que derive o ator de autenticação confiável e não de parâmetro do navegador; não expor service role em clientes.
- **Validação integrada pendente:** Storage D3/D4, documentos financeiros, LGPD, retenção, backups e restauração, observabilidade de falhas, recuperação de filas e testes C05/C08 completos em ambiente de homologação remoto exclusivo.
- **Operações humanas S1 e MCP S3:** fluxo bancário com prova humana, ficha versionada e confirmação MCP não estão homologados. Nenhum bug deve disparar suspensão/auto-reparo autonomamente.

## Ação recomendada

**Prosseguir com C04/opt-out e modelo de falhas C06/C07/C09, ainda exclusivamente em sandbox**, mantendo gates por capacidade. Antes de habilitar WhatsApp real, comprovar elegibilidade, política Meta para o produto financeiro, aprovação de templates, controle da janela, callbacks e retenção LGPD. Não criar conta, integração, merge nem deploy automaticamente com base neste parecer.

**Observação metodológica:** PASS significa sucesso dos cenários expressamente executados, não ausência demonstrada de todos os defeitos possíveis. O percentual histórico 19F mede prontidão do planejamento, não percentagem de software construído.
