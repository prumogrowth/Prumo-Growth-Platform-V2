# E04 — pré-validação S0 do recontato pós-humano F02 com S1 e política de templates

**Data:** 25/10/2026. **Frente:** S0/F02/F03, branch própria `feat/oai-s0-f03-history-port-20261023`, PR #1 Draft. **Não integrado à main.**

## Orientação recebida do responsável

- Manter as frentes independentes e continuar nas respectivas branches.
- Integração futura ocorrerá numa branch específica com validação e autorização antes de incorporação à main.
- Priorizar eficiência de testes sem reduzir cobertura, mas **não** alterar workflows de outras frentes sem coordenação.
- A [Issue #3](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/issues/3) é uma auditoria inicial sobre duplicação de workflows da S1; segue aberta e **não autoriza alterações**. Nenhum workflow S1 foi modificado nesta rodada.
- Banco remoto Supabase continuará intocado até a integração geral futura definida pelo responsável. Somente PostgreSQL 17 descartável no CI.

## Entregas efetivas da frente

1. `supabase/tests/s0_f02_posthuman_template_policy_local_only.sql`: tabela local de *fixture* S0 com template aprovado no catálogo simulado, finalidade `post_human`, categoria `MARKETING`/`UTILITY`/`AUTHENTICATION` e versão de política; RLS restritiva; inserção somente no banco de teste pela administração S0, classificação imutável. Não é um registro de aprovação real da Meta nem autorização de envio.
2. `backend/s0_f02_posthuman_preview_local.py`: pré-validação S0 de um resultado F02 vindo do JS S2 em commit fixado. Exige anteriormente o estado de compatibilidade física `LEGACY_C04_HUMAN_CASE_INCOMPATIBLE` (inclui F03 com fonte textual, corte, HMAC, identidade, versões, opt-out e plano legado); requer identidade independente de um gestor reconhecida pelo `IdentityProvider` injetado, sessão em `auth.sessions`, papel `gestor` da mesma loja e vínculo ativo na S1. Rechecagem privada do template e política da S0, com nome, versão e categoria contra a saída F02. Reexecuta a porta C04/F03 ao final.
3. O único estado positivo é `PREVIEW_ONLY_LEGACY_C04_BLOCKED`: **nunca** efetua envio, gravação de plano, aplicação de campo, decisão comercial nem autoriza recontato pós-humano. A função antiga de agendamento C04 continua proibindo ciclos com casos humanos. A autorização humana real e a eventual nova capacidade operacional ainda precisarão ser desenvolvidas/ratificadas pela S0, sem contornar o agendador anterior.
4. `backend/tests/test_s0_f02_posthuman_preview_local.py`: seis testes unitários da forma estrita e do retorno mínimo. `backend/tests/test_s0_f03_pg17_integration.py`: doze cenários físicos #250–261, incluindo papel, S1, sessão, categoria não registrada, política stale, categoria adulterada pelo JS, opt-out posterior, template estrangeiro, RLS, imutabilidade e versão atualizada; caso de base positiva comprovou zero planos e envios.
5. `scripts/run-s0-f03-pg17-local.sh` carrega apenas a fixture S0/F02 da própria frente, no PG17 descartável, e inclui os seis testes. Nenhum arquivo `.github/workflows/` foi editado; nenhuma alteração à Issue #3 ou à branch S1.

## Evidência de testes

- **[GitHub Actions #40198258805 — SUCCESS](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40198258805)** no código `0a29003fd73eb94d7065e4286e01ebb81683663e`.
- **84/84** testes S0 Python preexistentes aprovados.
- **408/408** testes Python F03/F02, incluindo **261 físicos PG17** da mesma suíte, aprovados.
- Total **492/492 Python**, mais **269/269 Node** da S2 fixada. São 761 verificações de suítes diferentes no mesmo CI, não 761 fluxos de negócio de ponta a ponta, nem os 70 oráculos E02 homologados.
- A primeira rodada identificou incompatibilidade entre `FOR SHARE` e uma transação PostgreSQL `READ ONLY`; corrigimos a consulta consultiva **sem torná-la gravável** e a rodada integral posterior passou. Registros de falha permanecem no Actions para auditoria, sem encobrir o resultado inicial.

## Limites explícitos e próximo gate

- A identidade nos testes físicos continua usando `LocalIdentity` sintética, não uma sessão GoTrue real fim a fim. O papel S1 e a sessão são consultados fisicamente em PG17, mas isso não homologa o runtime real.
- O catálogo S0 desta etapa é sintético e **não** deriva categoria nem aprovação da Meta. Consentimento C04 também é um artefato simulado: não autoriza contato real, WhatsApp nem marketing.
- Esta etapa verifica uma intenção consultiva; ainda não existe registro de aprovação humana independente de plano pós-humano, cancelamento atestado e vínculo idempotente com um novo executor separado da função C04 pré-humano. A funcionalidade operacional permanece bloqueada.
- Gate seguinte na branch da própria frente: desenhar e testar (sem ativar) o contrato S0 de intenção pós-humana ratificada, idempotência e trilha de auditoria, políticas opt-out/finalidade, além da matriz original de aceitação E02; integrar em branch própria no futuro, com aprovação prévia, sem mudar workflows S1.
