# S1-002/I7 — Drenagem limitada e justa do backlog | 18/10/2026

**Somente frente S1-002**, branch Draft PR #5. [D-negócio] fila protegida não pode ser esquecida; [P] política de lotes e equidade no PG17; [R/V] agenda e execução de worker em ambiente real. Não há alteração de S0, Meta, OpenAI ou interface visual.

## Solução sintética candidata

Após a migration 042 (recuperação após ativação/grant, até 25 pendências por evento), 043 acrescenta `ultima_inspecao_em` à fila privada e **rotaciona pendências sem substituto**. A recuperação anterior selecionava sempre os 25 mais antigos; 25 atendimentos sem candidato poderiam impedir a análise dos que tinham um operador elegível. O novo ordenamento prioriza pendências ainda não examinadas, depois as mais antigas inspecionadas. Não abandona nem retira caso sem operador da fila; não reabre `vendido` ou `perdido`.

A nova função privada `prumo_private.s1_drenar_backlog_protegido(loja, max_lotes)` executa entre 1 e 10 lotes de **até 25 pendências por lote** (máximo 250 casos examinados), reporta antes/depois, reatribuições, terminais, duplicados evitados e itens que permanecem protegidos. Só `postgres` autorizado internamente pode executar; `anon/authenticated/service_role` continuam sem acesso. **Não** contém `cron`, filas externas, autorização RH, API REST pública nem comando de envio.

A varredura é a operação que um futuro worker interno poderá usar mediante contrato/autorização específicos. Até isso, a recuperação automática de até 25 casos por evento de ativação/concessão permanece como antes. Não afirmar que grandes filas se esvaziam sozinhas sem esse futuro executor.

## Testes PG17 candidatos [P até prova]

`S1B-01..10`: 100 pendências em duas lojas, um caso terminal vendido, gatilho de ativação só drena 25 da própria loja, uma chamada do backlog drena 25 adicionais, segunda encerra lote com status terminal preservado, rerun idempotente, 30 pendências sem receptor no início não bloqueiam 10 posteriores elegíveis (evita starvation), novo profissional em B recupera 25 e a chamada privada termina os 5 restantes, leitura autenticada multiloja isolada, execução negada a authenticated e limites rejeitados. **Todas fixtures sintéticas em transação com ROLLBACK.** Não homologar sem execução no workflow PG17 e checagem de regressão I1-I6.

## Pendências reais

Tempo/escala/plantão, política do gestor para casos presos, idempotência do agendador real, custo e taxa da fila grande, autenticação GoTrue/REST e interface de alerta não foram implementados. RLS role fake PG não substitui token Supabase validado. Não rodar em Supabase hospedado, nem merge/deploy; percentual global não deve ser inflado.


## Evidência I7 — 100 casos sintéticos, 18/10/2026

[**GitHub Actions PostgreSQL 17 #39168767820 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39168767820), SHA testado `a3313e1de6b72a1284f37b481dcba294c8037a37`, job `117797244695`. Logs conferidos: **S1B-01..10 (10/10 PASS)** em 100 pendências fictícias e duas concessionárias; baseline no mesmo job: S1E 7/7, S1R 9/9 duas vezes, S1X 7/7 duas vezes, S1C 5/5, S1D 5/5, S1Q 10/10, S1QC 4/4. A hipótese de bloqueio das primeiras 30 pendências foi mitigada: 10 posteriores recuperáveis foram processadas. Vendas mantidas como terminais e nenhuma atribuição a operador inválido.

A execução inicial [#39168641246](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39168641246) falhou somente na expectativa do teste sobre **número de inspeções**: uma mesma pendência sem destinatário pode ser inspecionada mais de uma vez em lotes distintos, sem duplicar casos ou histórico. O teste foi corrigido para distinguir total de tentativas de inspeção de casos exclusivos, e toda a suíte passou em #39168767820.

**Limites persistentes:** rotinas de ativação/concessão ainda processam até 25 registros por evento; o saldo maior requer **chamada interna explícita à função de drenagem**, não há scheduler nem automação contínua implantada. Não é prova de serviço REST/GoTrue hospedado, regra de escala/plantão, performance com dados reais ou autorização RH. Sem merge/deploy/progresso global.
