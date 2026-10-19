# Auditoria transversal dos últimos incrementos S1-002 (I2–I7) | 18/10/2026

**Escopo auditado:** gestão Prumo I1–I7 nas migrations 038–044, contratos S1-002 e CF-OP-02, e prova de compatibilidade com S0 C02, em branch Draft PR #5. Fonte do objetivo: pacote documental auditado 17/10, especialmente decisão D41 (gestor/operador), registro 22 (retorno pós-venda), registro 21 (recusa bancária), doc.26 C02/C11 e contrato CF-OP-02 entre frentes. **Não valida integração real com Meta, instituição financeira ou Supabase hospedado.**

## Matriz de coerência e propriedade

| Tema / invariante | Resultado de auditoria |
| --- | --- |
| Profissional pertence à Prumo, não à loja; grants A/B independentes | Alinhado nos testes I1/I2/I3. |
| Suspensão e revogação cortam atribuições futuras; ex-operator não reassume carteira automaticamente | Alinhado nas rotinas I2/I6 e testes. |
| Redistribuir somente a operador Prumo ativo com grant de operador na MESMA loja; gestor só executa após autoatribuição humana | Alinhado na seleção automática. O fluxo administrativo de autoatribuição é propriedade S0/gestor, não executado nesta frente. |
| Duas suspensões, duas reconciliações ou dois recuperadores não dão duplicidade | Testes intersessões locais I4–I6 passaram, sem afirmar tráfego distribuído/REST real. |
| Fila sem elegível fica protegida e com história; recuperação em ativação/grant | Alinhado na migração 042 e testes S1Q/S1QC. |
| Backlog 100 casos, gatilho 25 e drenagem manual limitada, com inspeção justa | Alinhado na migração 043 e S1B. **Não** equivale a cron automático. |
| Ciclo vendido/perdido histórico e nova solicitação humana são entidades diferentes | **ERRO REAL ENCONTRADO E CORRIGIDO** na migration 044. Antes disso 039–043 descartavam/fechavam atribuições de novos casos porque só examinavam o status histórico. |
| Retorno pós-venda não muda `vendido`, mantém somente humano; pós-remessa não altera `cadastro enviado ao banco` | Marcadores S0 `retorno_pos_venda`, `retorno_pos_remessa` e `revisao_humana` preservados; ensaios AUD1 e AUD2 aprovados. |
| IA/Meta não atribuem operador; S1 não manda template nem decide status | Nenhuma alteração externa nem chamada real. Somente equipe, atribuições, fila e auditoria S1. |
| Nenhum nono status, nem mudança automática em venda/recusa bancária | Nenhum novo status comercial introduzido; controles positivos e negativos AUD1/AUD2. |

## Diagnóstico e reparação comprovada

**Risco F-01 [alto, corrigido em sandbox]:** doc.22 [D] exige que contato espontâneo após `vendido` abra caso humano, preservando ciclo antigo. S0 C02 simulado já cria `casos_humanos.motivo_simulado='retorno_pos_venda'` e, após `perdido`, `revisao_humana`. I2 encerrava a atribuição como `ENCERRADO_HISTORICO` por olhar somente `ciclos_comerciais.status_comercial`; I6 fechava a pendência da fila como `TERMINAL`. Isso impedia remanejamento/recuperação do novo atendimento. **Migration 044** condiciona o encerramento ao **par status histórico + motivo S0**: `vendido/retorno_pos_venda` e `perdido/revisao_humana` são novas solicitações humanas operacionais, mantendo o ciclo vendido/perdido intacto. `cadastro enviado ao banco/retorno_pos_remessa` já permanecia humano. Bloqueia caso/ciclo em decisões transacionais, ainda exigindo matriz final de locks entre frentes.

**Evidências físicas:**
- [PG17 #39192614838 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39192614838), SHA `74d03faee0c4a0bc04877c9be8cbb7b83b73da61`: **AUD1 7/7** e regressões I2/I6/I7 após 044.
- [PG17 #39192862292 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39192862292), SHA `38bc2223d49f0b556f0f859a8c8ee744ed37409b`: **AUD2 5/5** usando a função existente S0 para criar novo CASO_HUMANO de inbound fictício, depois redistribuição S1, idempotência e status histórico preservado. Suites S1E/S1R/S1X/S1C/S1D/S1Q/S1QC/S1B também executadas no mesmo job.
- Falha antiga de teste sobre contagens de inspeções I7 foi corrigida no commit `a3313e1de6b72a1284f37b481dcba294c8037a37`, com 10/10 S1B em [#39168767820](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39168767820).

## Limites que permanecem e NÃO autorizam produção

1. **Conceito físico incompleto S0 [R]:** `motivo_simulado` é um marcador sintético; o atributo definitivo de pedido humano ativo, conclusão e janela visual requer contrato entre S0/FV. Não inferir por CPF, horas ou status isolado. Casos legados sem motivo exigem revisão, sem encerramento por extrapolação.
2. **Carga/escala [R]:** balanceamento por menor carteira, sem turno/capacidade/plantão homologado. Doc.26 C11 prevê manter em fila fora do expediente.
3. **Autorização humana [R]:** ações reais de suspensão/ativação, gerente e exceções exigem aprovador RH/Prumo identificado; testes de role `authenticated` no PostgreSQL não provam JWT ou sessões GoTrue.
4. **Backlog [R]:** 043 oferece entrada interna limitada, mas nenhum scheduler/worker real, alerta ao gestor e autorização de execução recorrente. Excesso de 25 casos por gatilho ainda depende de chamada interna explícita.
5. **Concorrência interfrentes [R]:** S1 passa a travar casos/ciclos também, porém a compatibilidade de ordem dos locks com todas operações de status S0/Meta não foi demonstrada. Testes S0 C02 → S1 foram sintéticos, não cobrindo venda/negação bancária simultânea com transferência.
6. **Integração e segurança [R/V]:** Supabase Auth/REST real, wrappers e RLS de serviços, política LGPD, Meta e instituição financeira não foram homologados. PR #5 permanece Draft sem merge; CI roda em PG17 descartável.
7. **Perímetro:** apenas migrations, testes, runner e documentos S1 foram escritos nesta auditoria. Nada em infraestrutura hospedada, branches de outras frentes, cron ou dados reais. Percentual do planejamento permanece inalterado.

**Veredito:** I2–I7 alinham-se ao objetivo de distribuir e recuperar atendimentos da Prumo por loja **dentro do escopo sintético testado após reparação F-01**. Não existe aceite integral de produção ou interface completa. O próximo gate útil é fechar com S0 a tipificação física dos novos casos pós-ciclo, a ordem dos locks e a projeção segura da fila ao gestor; depois testar Auth/REST real em ambiente separado, com autorização.
