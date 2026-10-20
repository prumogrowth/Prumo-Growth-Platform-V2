# Prumo — decisões e portões S0 (17/10/2026)

| Recurso | Situação |
|---|---|
| GitHub | Free privado, sem previsão de upgrade |
| Supabase | Free em ambiente exclusivo, projeto `projeto-supabase-omitido`; Pro ~US$25/mês planejado quando exigido |
| n8n | não contratado; avaliar em S2 |
| OpenAI API | pendente; simulações primeiro |
| WhatsApp Meta | pendente de canal, políticas, opt-in/out e homologação |
| instituição financeira | integração/autorizações reais pendentes; remessas humanas comprovadas |

## Decisão posterior de 17/10/2026
**Regra esclarecida:** mesmo cliente pode contatar A, B e C, com registros independentes e RLS por loja. O número **emissor da Prumo** não pode ser compartilhado por concessionárias; já possui índice UNIQUE global. Migração 007 errada foi excluída antes de qualquer deploy. Consulte `docs/REGRA_NUMEROS_ATENDIMENTO_CLIENTE_2026_10_17.md`. O documento da interpretação global do cliente está retratado.

## Portões
1. Fonte vigente: 00A, 13A, 21–23, 41. Documento 01 é histórico e não determina implementação.
2. Ensaiar esquema/RLS/grants com dados A/B em Postgres **descartável** antes de qualquer deploy.
3. Gestor lê conversas D2 próprias; não recebe D3/D4 brutos por supervisão. A escrita de operador exige caso atribuído, ainda não implementado em S0.
4. SQL/migrações requerem revisão em branch e aceite técnico; **NÃO implantar remotamente automaticamente**.
5. Supabase Free remoto é desenvolvimento, nunca produção sem os portões aplicáveis.
6. Operação real depende de GO/NO-GO humano por capacidade e validação Meta/Banco/LGPD. Nenhuma assinatura é feita automaticamente.

**Estado:** branch S0 publicada em PR draft #1. Testes limitados de isolamento A/B aprovados em PostgreSQL 17 descartável ([CI PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39059980947)). Transações sintéticas, casos e testes de isolamento foram ampliados, mas Auth/REST real, recuperabilidade, integrações e revisão humana permanecem pendentes. Nenhuma migration foi aplicada ao Supabase remoto.


## Atualização de precedência Meta / S0-030 — 18/10/2026

**DEC-WA-05 — APROVADA quanto à titularidade por concessionária:** cada concessionária é proprietária de sua própria conta empresarial Meta, App Meta, WABA, números e autorizações; a Prumo opera somente como integradora autorizada. Esta regra posterior **substitui as afirmações históricas sobre Apps/WABAs/números da gestora**, sem mudar a exclusividade global do número emissor nem o isolamento do telefone do cliente por loja. Referência: PR #2, `docs/integracoes/whatsapp-meta/decisao-titularidade-meta-por-concessionaria-v1_0.md`. **Onboarding/permissões/canais reais ainda não aprovados.**

DEC-WA-01/02/03: diretrizes aprovadas, protótipos sintéticos 028/029 e correção aditiva 030 versionados no PR #1; detalhes operacionais e contrato de API ainda não homologados. DEC-WA-04 (ambiente definitivo) e DEC-WA-06 (segredos, privacidade, retenção, continuidade) permanecem **pendentes**. Não promover POC Supabase existente a ambiente definitivo por inferência. Nenhuma migração comercial hospedada, conexão Meta real, merge ou canal real autorizado. Ver `docs/AUDITORIA_CORRECOES_WA_S0_030_2026_10_18.md`.


## D-ORG-01 — Equipe da Prumo, não da concessionária (18/10/2026)

**Alinhamento organizacional D-ORG-01 (18/10/2026):** gestores e operadores são profissionais **da Prumo**, inclusive quando dedicados exclusivamente a uma concessionária. Loja é escopo de atendimento, não vínculo empregatício. Uma pessoa pode ter múltiplas lojas por concessão explícita; gestor pode autoatribuir caso segundo D41-04. Ver `docs/D_ORG_01_EQUIPE_PRUMO_2026_10_18.md`. O vínculo organizacional não confere por si só acesso; RLS deve exigir concessão vigente e atribuição do caso quando necessária. Titularidade Meta DEC-WA-05 pertence à concessionária, tema diferente do pessoal da Prumo.


## Atualização de precedência S0 × S1 I11 — 20/10/2026 (aditiva, sem deploy)

**Decisão posterior de produto (19/10) prevalece sobre a descrição histórica D41/D-ORG-01 de supervisão exclusivamente por loja.** A frente S1-002 já versionou `S1_002_I11_GESTAO_POR_EQUIPE_PAUSA_GLOBAL_2026_10_19.md`, com gestão por **operadores da equipe** e concessões A/B/C atribuídas somente pelos responsáveis. O gestor não precisa de grant próprio de concessionária para liderar o operador; o caso conserva a loja de origem e o receptor continua exigindo concessão válida. Os textos S0 antigos por loja devem ser interpretados como **históricos para essa dimensão**, não como autorização para atravessar equipes.

**Atenção a uma divergência ainda não resolvida:** a migration S1 048 materializa pausa de distribuição como `equipe_prumo_s1.estado='suspenso'`, com redistribuição e restrição de leitura. A orientação da frente visual (FV-G2-01, 19/10) determina distinguir pausa de **novos leads** de suspensão da **conta** e de revogação de **lojas**. A questão é de propriedade S1 e está registrada na [issue #10](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/10). **Não promover comando definitivo de pausa no S0 nem ampliar direitos D2 por concessionária até o contrato S0/S1 resolver essa semântica.** Prosseguir em paralelo com interfaces candidatas e testes sintéticos.

A frente visual preparou contratos de **leitura UQ01–UQ09** e de **classificação de resultados de comandos C11–C18** sem conexão com S0. Isso não autentica sessão, não confirma prova bancária e não altera comercial. Códigos APPLIED/ALREADY_APPLIED somente podem ser considerados efetivos por S0 autenticada com auditoria; resultados PENDING/ACCEPTED/UNCERTAIN não autorizam inferência de venda, envio ou remessa. Ver `frontend/docs/30_FV_S0_UQ_CONTRATO_LEITURA_CANDIDATO_2026_10_20.md` e `frontend/docs/31_FV_S0_RESULTADO_COMANDOS_E_DIVERGENCIA_S1_2026_10_20.md` na branch `feat/frontend-plataforma-visual`. Estas fontes **não foram integradas/mescladas** a esta branch.

**Escopo da alteração presente:** esclarecimento documental do gate S0, sem SQL/migration, RLS, Auth, API, Supabase hospedado, produção ou implantação. Exigir revisão técnica coordenada antes de alterar permissões reais.


## Atualização D: pausa seletiva sem bloqueio de conta — 20/10/2026

A decisão de produto foi **refinada e prevalece** sobre a hipótese de I11 de redistribuir toda a carteira na pausa. Consultar [S0-043](./S0_043_PAUSA_SELETIVA_E_INDICADOR_CONVERSA_2026_10_20.md) e, na frente visual, FV-UI-014. Gestor pausa e retoma **apenas o recebimento** com confirmação simples, sem motivo/data. Casos com contato humano iniciado permanecem; os demais somente são candidatos a transferências **para pessoas elegíveis da própria equipe**, e permanecem atribuídos quando não há substituto. Transferência manual sem concessão geral de loja exige autoridade **específica para o caso**, ainda pendente em S1 e sem exceção RLS liberada.

O módulo puro `backend/operator_distribution_policy.py` é um **planejador isolado para testes**: não executa a pausa/transação, não autoriza servidor e não altera triggers, funções SQL ou contas. Não associar este marco a homologação da operação real. A frente S1 receberá o detalhamento diretamente do responsável e fará as adaptações sob sua propriedade.
