# S1-002 / I41 — contrato técnico candidato de leitura S0 ↔ S1

**22/10/2026.** Escopo S1-002. Fonte normativa: `S1_002_01_CONTRATO_FUNCIONAL_VIGENTE_2026_10_22.md`, S1-D05, D18, D19. **Status:** implementação de teste [T], nenhuma alteração em migrations canônicas da S0/S1.

## Entrega
- `supabase/tests/s1_061_historico_equipe_contato_rls_local_only.sql`: reproduz o excesso de leitura da S0 e exercita políticas candidatas somente numa transação `BEGIN/ROLLBACK`.
- `scripts/run-s1-002-i12-local.sh`: inclui regressão I41, mantendo I38–I40.
- Os predicados de autorização usam `auth.uid()`, existência de equipe ativa, atribuições S0 e liderança `s1_gestor_operadores`, numa função `SECURITY DEFINER` isolada **sem grants de escrita** e políticas adicionais/restritivas temporárias.

## Regras exercitadas
1. **Gestor** enxerga casos, atribuições e mensagens do próprio time, incluindo caso com atribuição histórica já encerrada. Não herda toda a carteira de uma loja por ter grant na concessionária.
2. **Gestor sem grant de loja** ainda vê casos de seus Consultores, inclusive em lojas diferentes, sem inspecionar casos de outras equipes.
3. **Consultor titular atual** acessa a conversa antiga de outro caso do mesmo contato e concessionária, mas não recebe por isso poder de envio no caso antigo nem acesso a atribuições de outras pessoas.
4. Ex-titular sem qualquer atribuição ativa ao contato não mantém acesso por simples participação passada.
5. Mesmo número telefônico em concessionária diferente permanece isolado: identidade lógica de contato é `(concessionaria_id,lead_id)`.
6. Gestor observador não pode enviar mensagem em caso de seu Consultor; o Consultor atual pode enviar somente via validação de atribuição S0 no fixture simulado.

## Evidência de execução
[GitHub Actions PG17 #39865261939 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39865261939); job `120126214863`; executou os arquivos I41 até SHA `a1dcdcdfaff233c042f2a633d8263200b684bb33`. Logs: `OBSERVED I41-RED` (defeitos da S0 atual reproduzidos), `PASS I41-01..07` e `I41-ROLLBACK`. Os testes históricos I38/I39 e as duas corridas I40 permaneceram aprovados. **SUCCESS** significa validação da fixture em PostgreSQL descartável, não homologação de RLS de produção.

## Limites e necessidade de pactuação com a S0
**Não aplicar policies sem revisão conjunta com S0.** A prova tem escopo de SELECT nos objetos S0 `casos_humanos`, `atribuicoes_humanas`, `conversas`, `mensagens`. NÃO fecha segurança de `leads_loja`, `ciclos_comerciais`, relatórios, anexos D3/D4, `canais_loja`, lote/importação, `SECURITY DEFINER` e serviços fora do PG17. Visibilidade do Gestor baseada em atribuições históricas da equipe atual precisa de validação formal do S0 para trocas de chefia e retenção.

O candidato restringe mensagens ao `caso_id` correspondente à conversa. Mensagens de F01/sistema e histórico sem `caso_id` não foram resolvidas. Exceção por caso sem grant (I55), seu histórico do mesmo contato e sua revogação não são integrados aqui; não elevar o sandbox a RLS efetiva do produto. Compatibilizar Diretor, mudança de equipes, read markers, histórico por ciclo/segmento e exceções de caso antes de homologar. A2 continua [R].

**Integração seguinte:** S0 define contrato de leitura e evento/prova canônicos; S1 implementa grants vinculados à própria equipe/caso. Rodar testes de acesso negativos/positivos com GoTrue e PostgREST **descartáveis** e prova de concorrência com revogação. PR #5 permanece Draft, sem deploy/merge/hosted Supabase.
