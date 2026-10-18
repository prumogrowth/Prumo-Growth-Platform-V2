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
