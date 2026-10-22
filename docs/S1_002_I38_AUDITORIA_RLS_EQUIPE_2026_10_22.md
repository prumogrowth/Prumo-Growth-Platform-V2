# S1-002/I38 — auditoria RLS interequipes em laboratório
**Corte:** 22/10/2026. **Escopo:** S1-002; contrato vigente S1-D05 e S1-D19. **Estado:** prova de regressão e política candidata em fixture transacional, não migration de produto.

## Problema confirmado por inspeção
A policy S0 `casos_select_escopo`, mais as de `atribuicoes_humanas` e `conversas`, concede leitura a Gestor por vínculo de concessionária, sem verificar que o caso é da sua equipe. Um Gestor sem grant geral de loja, embora chefe do Consultor titular, não recebe o acesso de supervisão que o contrato prevê. A S1 038 exige estado Prumo ativo, mas não resolve a distinção de equipes. Mensagens dependem da visibilidade da conversa.

## Incremento implementado
- `supabase/tests/s1_058_supervisao_equipes_rls_local_only.sql`: cria seis atores fictícios, três equipes e uma loja compartilhada, demonstra as duas falhas do baseline e ensaia políticas candidatas para casos, atribuições, conversas e mensagens.
- `scripts/run-s1-002-i12-local.sh`: executa a auditoria após o baseline S0/S1 em PG17 descartável.
- Testa Gestor 1 e 2 com grant na mesma loja, Gestor 3 sem grant mas com equipe e Consultor titular. Todas as políticas/funções/fixtures do candidato são encerradas por `ROLLBACK`, sem escrita persistente.

## Limites e bloqueios
**Não promover a política candidata sem contrato e revisão técnica S0.** Ela demonstra apenas isolamento de casos atribuídos nos objetos cobertos. Não resolve fila de lead novo sem titular, acesso a histórico completo do mesmo contato, D3/D4, relatórios por loja, diretor, grants excepcionais, anexos, RLS em funções `SECURITY DEFINER` existentes ou permissões de recursos futuros. A leitura de supervisão vigente deve preservar todos esses limites.

Nenhuma branch S0 foi alterada; o SQL S0 continua histórico. O teste usa `auth.uid()` fake do PG17 e `SECURITY DEFINER` em schema temporário dedicado, sem ser um modelo de autenticação homologado. A2 permanece [R].

## Critério para próxima etapa
Comprovar execução física PG17 do arquivo I38 e investigar falhas. Em seguida, pactuar uma política de autorização de leitura que alcance S0 por integração regular, com testes negativos e positivos sobre **todos** os objetos relevantes. Até isso ocorrer, **RLS da supervisão permanece bloqueadora (P0)**. Sem merge, deploy ou Supabase hospedado.
