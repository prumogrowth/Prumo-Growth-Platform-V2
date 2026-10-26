# I73 — executor SQL exclusivo para exportações (laboratório)

Data: 25/10/2026. Branch: `feat/s1-002-equipe-prumo`. Base: I72 `f9ce4d1`. Apenas fixtures e adaptador local; sem migrations de produção, deploy, `main`, merges ou Issue #3.

## Vulnerabilidade e correção

A I72 removeu o endpoint REST da tabela de reservas, mas usuários `authenticated` com acesso SQL ainda podiam gastar a própria quota, porque possuíam `INSERT` na tabela interna e `EXECUTE` na RPC I71.

A I73 revoga esses grants de `authenticated` e seu `USAGE` no schema do ledger. O novo `prumo_s1_export_executor` é `NOLOGIN` e não é alcançável por `SET ROLE` do usuário final. Ele recebe somente os grants por coluna necessários à reserva e execução da RPC I71. Herda permissões comerciais do papel `authenticated`, sem contornar RLS, gestão da equipe ou revogação. A RPC permanece `SECURITY INVOKER`.

Um verificador de sessão em `prumo_export_auth.sessao_ativa(uuid,uuid)` consulta `auth.sessions`, sob `SECURITY DEFINER` **não publicado no PostgREST** e executável somente pelo papel de exportação. O adaptador `backend/s1_gateway_export_local.py` valida estritamente tipo, loja, cursor e página, deriva ator/sessão do bearer GoTrue real, verifica a sessão no banco e usa parâmetros SQL fixos. O login SQL efêmero tem `SET ROLE` apenas para o executor.

## Provas e limites

- PostgreSQL 17: seis verificações de cortes SQL, manutenção de grants mínimos, RLS da S0, quota e ausência de RPC/helper privilegiado público. Executa depois da I72 sob `ROLLBACK` do ensaio I64.
- Testes unitários: entrada sem identidade arbitrária, tamanho de páginas, tipo fechado e projeção fixa.
- GoTrue real + PostgREST: oito provas, inclusive JWT adulterado, sessão encerrada, SQL `authenticated` arbitrário negado, Gestor revogado e reserva legítima auditada. Reutiliza a stack descartável do I72.

**Risco restante:** comprometimento do próprio login SQL do gateway ainda permite tentar falsificar contexto. A etapa seguinte deve empregar prova assinada independente, nonce e verificação fora da posse do executor; não usar este adaptador como servidor de produção. Quotas globais por loja, rate limit, LGPD e exportações S0 alternativas continuam em análise.

## Certificação

Pendente de logs de CI. Commit persistido não equivale a sucesso. Nenhuma implantação hospedada autorizada.
