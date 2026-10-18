# S1-002/I6 — Recuperação automática da fila protegida | 18/10/2026

**Proprietário exclusivo:** S1-002. **Estado [P]:** migração 042 proposta para teste PostgreSQL 17 descartável; não representa prontidão para produção. Alinhamento de negócio: ao afastar operador, preservar casos da mesma loja e atribuir a novo profissional Prumo ativo; na ausência de elegível, manter fila protegida. Após a volta do próprio profissional, **não restaurar sua carteira automaticamente**.

## Responsabilidade e gatilhos

A rotina interna `prumo_private.s1_recuperar_fila_protegida(loja,limite)` processa lotes de até 50 registros de pendência **de uma loja**. Usa lock `FOR UPDATE SKIP LOCKED` no item da fila; trava o caso para sincronizar FK de possíveis atribuições concorrentes; verifica se já tem titular, se ciclo já é `vendido/perdido`, e se há candidato Prumo **ativo**, com concessão `operador` vigente naquela mesma concessionária (sem autoatribuir gestores supervisores). O destinatário **não pode ser o operador anterior** daquela pendência. A escolha mantém a heurística provisória de menor carteira ativa e `SKIP LOCKED` para destinos sob suspensão/revogação simultânea.

Para pedido elegível sem titular, cria nova atribuição (sujeita ao guard I2), remove pendência e grava histórico de recuperação. Se a pendência já ganhou titular, apenas limpa o registro e audita `JA_ATRIBUIDO`; se o ciclo é terminal, fecha a pendência, audita `TERMINAL` e preserva status/história. Se nenhum candidato está disponível, **permanece na fila protegida**, sem fingir que ocorreu recuperação. Não reativa IA Vendedora, nem altera ficha comercial, mensagens, templates, Meta ou OpenAI.

**Ação sem intervenção manual:** triggers internos reavaliam até 25 pendências da loja após (a) ativação de um profissional Prumo que já tem grant operacional vigente; (b) nova concessão ou renovação válida de operador ativo. **Não há varredura agendada para pendências remanescentes, nem regra de capacidade/escala homologada.** A fila não desaparece sem elegível; a execução de lotes maiores dependerá de mecanismo interno confiável ainda [R]. Executor sem privilégio `postgres` não pode usar a rotina; tabelas privadas com RLS sem acesso Data API.

## Fronteiras e limitações

- S1-002: apenas estados de equipe, atribuição, fila protegida, evidência de recuperação e isolamento por loja.
- S0: segue proprietário de caso/comercial, roteamento da resposta, agendas, status e LGPD. Nem a venda nem a recusa bancária são inferidas deste fluxo.
- FV: deve obter fila e alertas via projeção/serviço S0 autorizado, não ler diretamente `prumo_private`.
- IA/Meta: não determinam elegibilidade de operador nem modificam atribuição.

**Política [R] ainda necessária antes da produção:** gestor responsável por alertas, escala/plantão e disponibilidade, fase bancária elegível para remanejamento, número de tentativas de recuperação/limite por transação, contrato interno de executor de backlog e governança do administrador. Conexões reais Supabase Auth/GoTrue/REST, concorrência do consumidor de fila com criação de nova atribuição, e efeitos dos gatilhos em throughput exigem integração e testes adicionais. Não fazer merge, migrar projeto hospedado ou chamar API real sem revisão e autorização.

## Critérios de testes [P, até ver CI]

`S1Q-01..10`: casos A/B entram na fila ao suspender O1; gestor não ganha caso; reativação do ex-responsável não restaura posse; ativar O2 com escopo A realoca só A; novo grant O4 em B realoca B; `vendido` não reabre; pendência stale com titular é limpa sem duplicação; reexecução idempotente; isolamento RLS B versus A; cliente `authenticated` bloqueado; limites inválidos recusados. A execução deve ocorrer após 038–042 e regressões anteriores. Todos testes até prova do CI **não executados**.

## I6 — Corridas de recuperação [cenários candidatos]

`scripts/test_s1_002_queue_recovery_race.sh` executa com duas conexões PostgreSQL reais e fixtures exclusivamente fictícias. Verifica `S1QC-01..04`: dois consumidores em competição pela mesma pendência; nova atribuição por fluxo concorrente enquanto recuperação aguarda trava do caso; suspensão/RLS; ausência de duplicidade na tabela de auditoria. Critérios de aprovação: PG17 SUCCESS e marcadores PASS. **Nenhum teste S1QC declarado aprovado antes do log.**

## S1-002/I6 — Evidência executada e limites (18/10/2026)

**CI funcional PG17:** [GitHub Actions #39167477859 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39167477859), SHA `a438106ecf9e07eecb45a1c7b568d790638854ef`, log do job `117793341159` verificado: **S1Q-01..10, 10/10 PASS** (recuperação em ativação/concessão, ex-operador não reocupa, gerente não autoatribui, ciclo vendido intocado, stale sem duplicação, RLS e executor privado).

**CI concorrência PG17:** [GitHub Actions #39167842391 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39167842391), SHA `2b50344206fff68b30b2a5afc4e5e13c292fe20f`, job `117794451583`; log verificado: **S1QC-01..04, 4/4 PASS** com duas conexões PostgreSQL; uma única atribuição e trilha com dois recuperadores; concorrência com atribuição externa fecha pendência stale; suspenso sem leitura. O mesmo job executou **S1E 7/7, S1R 9/9 duas vezes, S1X 7/7 duas vezes, S1C 5/5, S1D 5/5, S1Q 10/10, S1QC 4/4**.

O ensaio inicial de S1QC [#39167719374](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39167719374) parou após S1QC-02 por comentário Bash incorreto (`--` em lugar de `#`); falha do script corrigida e toda a bateria retestada em #39167842391. **Não** equivale a prova GoTrue/REST, carga, scheduler, integração S0 de fila gerencial ou produção.

**Gates abertos:** alerta/reapresentação da fila ao gestor via projeção S0, processamento de backlog com lote excedente ao gatilho 25, limites de escala/capacidade, identidade real de aprovador RH, grants expirados sem novo evento exigem executor 040, Auth/REST integrado, encerramento/venda/cadastro bancário interfrentes, custo/concorrência de workers, RLS entre equipe/serviço. Sem merge/deploy/Supabase hospedado e sem incremento de percentual global.
