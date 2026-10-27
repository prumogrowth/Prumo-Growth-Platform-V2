# Prumo — Gate do backend autenticado S0 (17/10/2026)

## Resultado

**GO para continuar desenvolvimento somente sintético. NO-GO para expor backend na internet, conectar Meta/Banco ou implantar no Supabase hospedado.**

A implementação `backend/identity_boundary.py` constitui um **adaptador interno/testável**, não um endpoint web implantado. Para duas operações sintéticas, a identidade do gestor provém do **GoTrue** e a sessão é conferida na tabela `auth.sessions` da instalação **local**. O corpo enviado pelo navegador não pode escolher ator, role ou SQL.

## Provas executadas
- **PostgreSQL 17 / unidade:** [GitHub Actions #39080561907 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39080561907), regressão de migrações + doze testes unitários de contrato. [Regressão final #39080940371 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39080940371): também cobre filtro estrito de DSN após o teste integrado.
- **Supabase Auth + REST integrado:** [GitHub Actions #39080757870 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39080757870), `AUTH-01..12` PASS. `AUTH-12` foi executado com GoTrue real do sandbox, conexão local `psycopg`, validação de sessão, cancelamento por gestor autorizado da loja B, negativa a gestor revogado/operador/sem vínculo, proibição de ator arbitrário, idempotência e teste de sessão excluída.
- A primeira tentativa do novo teste [#39080593068](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39080593068) falhou por `ModuleNotFoundError: backend` (problema de PYTHONPATH do runner), reparado no workflow e comprovado pela execução de sucesso. Não ocorreu falha de autorização nas assertions anteriores.
- Etiqueta de opt-in `run-auth-integration` retirada após a execução; o trabalho Auth pesado não está programado para disparar em cada commit.

## Limitações
- Ainda não há servidor HTTP, DTOs públicos versionados, observabilidade, rate limit, auditoria de negativas, proxies ou gestão de segredos em produção.
- O adapter SQL usa **postgres** somente no PostgreSQL local autorizado para S0. Credenciais privilegiadas devem ser substituídas por serviço restrito/escopado antes de qualquer operação real. A lista de funções é fechada: `cancelar_plano` e `conciliar_c07`. Nenhuma é função MCP; escritas MCP continuam exigindo preparação e dupla confirmação.
- A validação de uma sessão ativa na transação reduz o risco de usar tokens persistentes após revogação. Para produção será necessário definir política de invalidação, logout, concorrência e falhas de autenticação conforme Auth/LGPD.
- O teste Auth/REST usa identidades e dados inteiramente sintéticos e não homologa autenticação Meta/WhatsApp, dados bancários, mídia D3/D4, backup, retenção, webhook nem ativação comercial.
- Nenhuma migration comercial foi aplicada ao Supabase hospedado e PR #1 permanece DRAFT.

## Fontes normativas

Documentos 26, 40 e 41: identidade individual autenticada no backend; validação de loja/papel/versão a cada comando; operador apenas sobre caso atribuído; gestor não é administrador global; MCP inicial só pode preparar/confirmar operações especificamente autorizadas. Documento `docs/BACKEND_IDENTIDADE_AUTENTICADA_S0_2026_10_17.md` contém contrato detalhado.

**Próxima engenharia:** definir credencial do serviço e política de autorização fim a fim antes de construir uma rota pública; fazer revisão de segurança de interface operacional, erros, rate limiting, logs e recuperação. Não avançar automaticamente para deploy.
