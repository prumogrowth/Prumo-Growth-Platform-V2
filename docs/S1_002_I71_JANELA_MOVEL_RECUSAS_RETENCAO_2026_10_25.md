# I71 — quota móvel, registro de recusas e retenção explícita

Data de desenvolvimento: 25/10/2026. Apenas branch independente `feat/s1-002-equipe-prumo`. Nenhuma implantação, integração com outras frentes, alteração na `main` ou execução de otimização da Issue #3.

## Risco e correção experimental

O I70 usava janelas fixas de hora e exceções SQL em recusas. O primeiro modelo permitia concentração de até oito requisições na passagem de uma hora; o segundo impedia o registro da recusa porque a transação do banco era desfeita. O I71 mantém o máximo de **4 requisições aceitas e 30 unidades solicitadas nos últimos 60 minutos**, por ator, loja e tipo (lotes/canais), sem arredondamento de janela. A verificação usa as reservas efetivamente aceitas e a exclusão mútua `pg_advisory_xact_lock` na chave de escopo, não o antigo contador por hora, removido para evitar métricas conflitantes.

Recusas são agregadas em `prumo_private.s1_71_export_recusas`, por minuto, identidade técnica, loja, tipo e motivo fixo `QUOTA_60_MINUTOS`, sem telefone, nomes, leads, casos, conteúdo de mensagens, IP ou parâmetros de cursor. A agregação limita o crescimento em caso de ataques repetidos do mesmo ator. A reserva recusada **não lança uma exceção SQL de quota**, porque ela reverteria também a auditoria; o trigger registra a recusa e suprime apenas a inserção da reserva aceita. A RPC devolve `{"estado":"LIMITE_ATINGIDO","linhas":[]}`, distinto de `OK` e `VAZIO`. Outros erros de permissão ou infraestrutura continuam falhando.

As antigas RPCs I69, agora incompatíveis com a semântica nova de quota, deixam de ser executáveis por `authenticated`. Em seu lugar, `public.s1_71_exportar_resumo(p_tipo,p_loja,p_apos,p_limite)` é `VOLATILE SECURITY INVOKER`, com SQL estático, validação estrita de parâmetros, autorização de equipe/Gestor, RLS I63/I67 para leitura e lista fechada de retorno, sem nomes nem identificadores de clientes. Retém limite de página de 1 a 20.

A rotina `prumo_private.s1_71_purgar_registros(referencia)` exige execução administrativa `postgres`, não oferece grants clientes e apaga **registros aceitos e recusados com mais de 30 dias**. A limpeza é explícita e testada, mas não agendada para produção. IDs de atores ainda podem ser dados pessoais indiretos e exigem controle de retenção/legalidade.

## Limitações que impedem deploy

O log privado armazena recusas **de quota**; não registra todos os tipos de tentativas inválidas, falhas de autenticação, negações RLS ou erro de infraestrutura. A auditoria abrange reservas aceitas, não comprova envio HTTP ao cliente. Uma chamada direta de INSERT autorizada para o próprio ator ainda pode consumir quota, e recusas por INSERT também contam como tentativa; não há rate limit de borda. A janela de 60 minutos impede burst exatamente no limite da hora, mas não impede múltiplas contas legítimas coordenadas nem substitui quota global da loja. Consultas diretas a tabelas autorizadas continuam fora desse mecanismo.

**Teste PG17:** prova consumo histórico migrado do I70, bloqueio após virada de hora, liberação quando expirados 60 minutos, auditoria da recusa sem exceção/rollback, isolamento dos escopos, proteção das RPCs antigas, ausência de dados de clientes, retenção administrativa e I63–I70 intactos. **Teste GoTrue real:** mesma lógica via JWT/PostgREST, seis chamadas concorrentes, recusa auditada e regressões. Resultados só serão considerados certificados após workflows concluídos.

**Nenhum arquivo é migration de produção; todos os objetos I71 aparecem apenas em `supabase/tests/` e na stack descartável.**

## Validação real

O E2E I71 reutiliza a stack efêmera GoTrue/PostgREST do I70, sem iniciar novo workflow. Testa o histórico I70 existente, seis chamadas HTTP concorrentes para um novo escopo com exatamente quatro autorizações e duas recusas registradas, simulação de 59/61 minutos, revogação das RPCs antigas, acesso de `anon`, usuário sem gestão, revogação no mesmo JWT, proteção da auditoria privada e limpeza administrativa de registros vencidos. Logs e porcentagens serão registrados somente após CI.
