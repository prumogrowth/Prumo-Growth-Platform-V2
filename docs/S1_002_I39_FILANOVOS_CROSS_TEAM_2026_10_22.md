# S1-002 / I39 — lead novo entre equipes e fila sem titular

**Data:** 22/10/2026. **Classes:** contrato S1-D06..D09, S1-D19 [D/DN]; implementação [T], laboratório PostgreSQL 17, **não produção**.

## Entrega
- `supabase/tests/s1_059_novos_leads_fila_cross_team_local_only.sql`: exercício integral `BEGIN/ROLLBACK` com a disponibilidade I53 também transitória; não grava alterações permanentes.
- `scripts/run-s1-002-i12-local.sh`: inclui I39 na regressão PG17 para a branch S1.
- O simulador usa **as entidades canônicas S0** `casos_humanos` e `atribuicoes_humanas`; a fila `s1_fila_novos_59` existe **apenas dentro da transação de teste**, sem competir com a fila operacional de responsabilidade S0.

## Casos exercitados
1. Um caso atribuído antes da pausa permanece com Consultor, conta ativa e grant preservados.
2. Um novo lead vai a Consultor elegível de outra equipe sem filtro same-team.
3. Sem elegíveis, lead novo recebe fila `PENDENTE` e **nenhuma atribuição humana**.
4. Dois Gestores com autorização explícita à mesma concessionária podem ver essa fila, mas Gestor sem concessão e Consultor não podem; cliente autenticado não faz DML.
5. Gestor autorizado assume lead com CAS versionado. Versão desatualizada é recusada; só pode existir um titular ativo no S0.
6. Ao retomar a elegibilidade, apenas o lead que segue sem titular volta à distribuição; caso já assumido não muda.

## Limites para integração
Não implementar como migration S1. S0 deve ratificar produtor/evento de criação de caso/lead, fila canônica e recibo, autorização comprovada de Gerente/Gestor, ordem de locks, idempotência de evento externo e a prova de concorrência em **sessões independentes**. A rotina atual testa CAS obsoleto sequencial e usa executor `postgres`, não autenticação GoTrue real.

Pendente: caminho de encaminhamento manual por Gestor a membro sem grant de loja depende da exceção de caso I55 e de contrato S0; tratamento explícito A2 de intake pausado continua [R]. Redistribuição de carteira já atribuída necessita confirmação física S0 de ausência de início humano; I39 não a simula, não transforma casos antigos em fila nem move fora da equipe. Deve-se estender matriz RLS/histórico I38 antes de promoção. Nenhum dado bancário, Meta real, deploy ou Supabase hospedado.

**Gate:** obter sucesso de PG17 na branch e registrar logs dos testes `I39-01..08`; depois harmonização com S0, revisão de segurança e corrida multissessão. PR #5 continua Draft.
