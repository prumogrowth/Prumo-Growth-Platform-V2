# I63 — RLS de histórico com exceção canônica I61

**25/10/2026, exclusivamente candidatos de homologação. Nenhum deploy.**

## Decisão técnica

O candidato `supabase/tests/s1_087_rls_excecao_canonica_local_only.sql` substitui, somente em banco descartável, a dependência de `prumo_private.s1_excecoes_55` pela estrutura persistente da migração I61 (`prumo_private.s1_excecoes_caso_i61`). Em vez de copiar políticas restritivas I41/I42/I60 separadamente e provocar `AND` indevido ou `OR` amplo, instala exatamente uma permissão adicional e uma restrição por cada superfície S0: `casos_humanos`, `atribuicoes_humanas`, `conversas` e `mensagens` (8 policies). As funções de autorização retornam booleanos, são de um schema não exposto ao PostgREST e verificam o `auth.uid()` derivado de JWT.

O Consultor somente herda leitura de casos/conversas/mensagens do mesmo contato e concessionária se tiver uma atribuição **atual** com grant operacional da loja OU exceção canônica I61 ainda válida, contendo `atribuicao_id`, caso, loja, operador, Gestor ativo e vínculo de supervisão atual. Um Gestor ativo lê os casos em que um Consultor atualmente supervisionado participou, sem acesso irrestrito à loja. Histórico anterior ao caso (conversa e mensagem com `caso_id NULL`) somente é legível se existe algum caso real para o mesmo par `(loja,lead)` acessível ao ator. O canal e o case ID da mensagem devem coincidir com sua conversa. Revogar ou encerrar a exceção elimina as leituras dependentes na próxima consulta do mesmo JWT. Pausar intake A2 não revoga os casos anteriores.

Não publica nova view, não amplia `INSERT` em mensagens e não libera tabelas privadas ou dados de D2/D3/D4 (lotes, ciclos, leads, outros objetos indiretos). Esses limites continuam exigindo revisão antes de qualquer promoção conjunta de RLS.

## Aceite e riscos

O teste `supabase/tests/s1_088_rls_excecao_canonica_aceite.sql` usa dados sintéticos e BEGIN/ROLLBACK no PG17, inclui o manager com grant amplo para demonstrar que esse grant não supera a restrição de equipe, reuso de mesmo contato, pré-caso, pausa, revogação e escrita bloqueada. O próximo passo, após PG17, é complementar a prova com GoTrue real e a transferência assinada I62; não confundir cobertura de laboratório com autorização para implantar em produção.

## Prova de sessão real adicionada

A `scripts/test_s1_002_i63_canonical_rls_e2e.py` é executada depois do I62, com GoTrue/PostgREST descartáveis, token real do destinatário e gestor, transferência/revogação pelo gateway HMAC já certificado, e as políticas I63 carregadas no banco efêmero. Verifica antes/apos: ausência de entitlement, histórico corrente e pré-caso de contato/loja exatos, negativa de gestor alheio, pausa A2 preservando leitura, revogação assinada cortando tudo no mesmo JWT e RPC privada inacessível. Evidências serão registradas após executar CI.

## Certificação final de 25/10/2026

**PG17 descartável: SUCCESS**, [workflow #40180680687](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40180680687), job `121130901757`, versão de código `c077e16788370968db3a8681739bf488db805280`. Logs conferidos: `PASS I63-01` até `PASS I63-09`, **9/9**; `I63 canonical history RLS PG17 9/9; all rolled back`; e `PASS S0+S1 I52-I63 canonical and candidate stages after legacy regression`. Candidato instalado dentro da transação teste; policies e dados sintetizados são revertidos.

**GoTrue real + gateway assinado I62: SUCCESS**, [workflow #40180783080](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40180783080), jobs `121131205582` (GoTrue E2E) e `121131206150` (unitários). Logs conferidos `PASS I63-E2E-01` até `PASS I63-E2E-06` — **6/6**, incluindo identidade de JWT real, transferência assinada, pré-caso, segregação por equipe, pausa A2, revogação assinada cortando leitura no mesmo token e função não publicada via RPC. I62-E2E-01..07 também permaneceram aprovados.

**Falhas iniciais diagnosticadas e reparadas, não escondidas:** o primeiro PG17 parou na fixture por misturar ciclo da loja A com lead da loja B; a FK composta S0 rejeitou corretamente. Corrigido em `c077e16788370968db3a8681739bf488db805280`. A primeira execução GoTrue parou porque a fixture nova dependia de um canal simulado pré-existente; foi ajustada para criar seu próprio canal explicitamente em `4c193d2a63516aa2c683d8bef2a2c2e1ae307ce6`. Nenhuma flexibilização de FK ou política de segurança foi usada.

### Delimitação do aceite

Este resultado **não** certifica o mecanismo de histórico como deploy operacional: as oito políticas foram mantidas em `supabase/tests` e só são carregadas no PG17 transacional ou no Supabase CLI efêmero. O banco hospedado permanece inalterado. Ainda é necessário integrar as fronteiras de D2/D3/D4 e checar a composição com toda a superfície legada S0 (consultas indiretas e objeto a objeto), revisar autorização de Gestores e preparar migrações somente após auditoria conjunta. O endpoint HTTP assinador continua estritamente local/test-only, sem infraestrutura/KMS de produção.
