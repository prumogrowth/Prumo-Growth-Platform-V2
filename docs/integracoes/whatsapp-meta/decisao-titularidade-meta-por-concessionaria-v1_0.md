# DEC-WA-05 — titularidade dos canais Meta por concessionária | v1.0

> **[LEITURA_ORIENTADA_2026_10_21] Documento de referência histórica ou de engenharia, NÃO substitui decisões funcionais recentes.** Consulte o [LEIA PRIMEIRO](./README.md), a [especificação vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e o [mapa de conflitos por origem](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Apenas trechos expressamente substituídos perdem vigência; evidências offline não significam serviços reais homologados.

**Status:** **DECISÃO DE NEGÓCIO APROVADA PELO RESPONSÁVEL** quanto à **titularidade e padrão de implantação por concessionária**. A verificação documental das contas Meta, os requisitos de provisionamento, a ativação real, as permissões e a operação permanecem **PENDENTES DE VALIDAÇÃO**. Este documento substitui a hipótese anterior de números/WABAs pertencentes à gestora e dedicados a lojas.

**Declaração do responsável:** “Cada concessionária vai ser proprietária do canal de WhatsApp usando a sua própria conta empresarial, ou seja, esse App criado para a concessionária de demonstração e API vai pertencer à concessionária de demonstração; outra concessionária vai ser outro App e outra API.”

## 1. Modelo de titularidade aprovado [D]

1. **Cada concessionária** controla sua própria conta empresarial Meta, seu aplicativo Meta próprio, suas WABAs e seus números de WhatsApp, conforme os recursos e permissões efetivamente confirmados no painel Meta. A Prumo atua como prestadora/integradora **por autorização**, nunca como proprietária presumida dos ativos dos clientes.
2. **Um aplicativo Meta distinto por concessionária** é a decisão de arquitetura deste projeto. A **Graph API / WhatsApp Cloud API** é o mesmo serviço oficial da Meta utilizado por todos; o que muda por concessionária são o aplicativo, os recursos atribuídos (WABA, Phone Number ID), credenciais, autorizações e contextos de cobrança/conta. Não inventar endpoint/API de tecnologia diferente para cada loja.
3. O núcleo comercial continua **multi-tenant**, com `concessionaria_id` e `canal_id` escopados. A existência de aplicativos separados **não substitui** verificação de tenant, FKs compostas, políticas RLS e autorização de backend.
4. **Exclusividade do emissor:** o mesmo número de atendimento da empresa não deve pertencer simultaneamente a duas concessionárias no cadastro Liberacred. `canais_loja.identificador_emissor UNIQUE` continua como regra vigente. Um **número de cliente** pode aparecer em várias concessionárias com históricos separados.
5. **Titularidade e onboarding** são distintos: ser responsável por um App Meta não prova que o App/WABA/número comercial já esteja registrado, com permissões, webhook correto ou apto a produção. Necessária conferência explícita do vínculo real no Business Manager/Meta for Developers, sem mudanças operacionais nesta etapa.

## 2. concessionária de demonstração — estado conhecido versus pendente

**Evidências do projeto:** aplicativo Meta Developer denominado **“concessionária de demonstração - Atendimento”** já criado em contexto empresarial de teste; Meta Test Messaging Account/WABA e Phone Number ID de **teste** foram utilizados em webhook funcional via Supabase Edge Function `whatsapp-webhook-sandbox`. Houve comunicação bidirecional no **sandbox** com resposta automática ao comando `TESTE PRUMO`. O usuário informa que a conta empresarial e o aplicativo estão prontos e que **um número real está disponível para cadastramento**.

**Não foi verificado nesta decisão:** propriedade administrativa efetiva do App/WABA na conta correta, estado de publicação/permissões/negócio, status de onboarding de número real, inscrição webhook da WABA de produção, segurança de permissões de usuário de sistema ou habilitação de envio real. Acessar painel autorizado e validar antes de afirmar produção liberada.

**Limite inegociável:** números comerciais atualmente ativos, inclusive os já usados por outras plataformas da concessionária de demonstração/concessionária de demonstração, não podem ser migrados, desinscritos, reconfigurados, conectados ou afetados sem autorização **específica e plano de alteração**. Ter número disponível **não equivale** a autorização para cadastrá-lo agora.

## 3. Modelo lógico replicável de credenciais e segredos [D/P]

- **[D]** Credenciais, HMAC de assinatura, tokens de sistema, referências de WABA e sender são **por concessionária/app**, com acesso concedido à Prumo de forma revogável.
- **[P]** Usar chaves lógicas estáveis em um registro de integração escopado, **não** IDs da Meta em nomes de colunas e não uma nova tabela de domínio concorrente: `concessionaria_id`, `canal_id`, `meta_app_id`, `meta_business_id` (se aplicável/validado), `meta_waba_id`, `meta_phone_number_id`, `credential_set_ref`, `app_secret_ref`, `access_token_ref`, `verify_token_ref`, `token_expires_at` (se aplicável), `permission_scope`, `integration_status`, `valid_from`, `valid_to`. DDL/semântica dependem da frente principal (DEC-WA-02) e revisão de segurança (DEC-WA-06).
- **[P]** Padrão de rotulagem humana para ambiente/gestor de segredos: `meta/<ambiente>/<slug_concessionaria>/<app_ref>/<tipo_segredo>`. Tipos: `app_secret`, `system_user_access_token`, `webhook_verify_token`. Usar referências opacas e segredos criptografados; **não incluir tokens, app secrets, telefones pessoais, credenciais ou URLs sensíveis no GitHub**. Para múltiplos tenants preferir registro/secret manager com acessos por tenant; evitar depender de uma variável de ambiente por cliente indefinidamente.
- **[P]** Cada aplicativo pode receber URL de webhook que permite identificar **candidato** ao app antes de verificar a assinatura, por exemplo rota parametrizada/identificador opaco, mas **o roteamento comercial só ocorre após validar HMAC com o segredo exato daquele App e resolver WABA+Phone Number ID**. Não aceitar tenant arbitrário do corpo não autenticado.
- **[P]** Para testes, manter convenções já usadas no piloto `META_APP_SECRET`, `META_WHATSAPP_TEST_ACCESS_TOKEN`, `META_WHATSAPP_TEST_RECIPIENT` **sem renomear segredos em produção por conta desta decisão**. Só migrar para estrutura escalável mediante controle de alterações.
- **[D]** A experiência de onboarding deve ser **repetível**: uma concessionária adicionada terá sua conta/App/WABA/número próprios, permissões de usuário de sistema e webhooks validados de forma isolada, sem copiar tokens de outra empresa.

## 4. Organização das responsabilidades

| Tarefa | Responsável proposto |
| --- | --- |
| Propriedade/controle de Business Manager, App/WABA, números e revogação de acessos | **Concessionária** |
| Consentir vinculação, permissões Meta, operação de templates e faturamento | **Concessionária**, com apoio da Prumo, observadas regras Meta/negócio |
| Integração HMAC, parsing Meta, Graph API, testes sandbox e nomenclatura de integração | **Frente WhatsApp/Meta** |
| Registry de canais por loja, chaves externas, autorização backend/RLS/GRANT | **Frente principal**, mediante contrato conjunto |
| Plano de segredos, retenção/rotação, backups, eventual uso em produção | **DEC-WA-06 pendente** e aprovação explícita operacional |
| Enquadramento em políticas financeiras Meta/Banco, LGPD e opt-in/out | **Validação externa pendente** |

## 5. Próxima verificação pontual — sem tocar números comerciais

Identificar **qual é a natureza do número real disponível**: novo/dedicado e sem WhatsApp comercial ativo, ou já em uso no WhatsApp Business/fornecedor/BSP. Isso determina o procedimento de cadastro e evita interromper um canal existente. Em seguida, fazer **auditoria somente de leitura** do vínculo da conta da concessionária de demonstração ao App/WABA e da elegibilidade de cadastro, com autorização do proprietário.

**Nenhuma migração, inscrição, desinscrição, publicação, token ou função Supabase foi alterada neste registro.** A própria plataforma/integração técnica ainda precisa atender os gates DEC-WA-04 e DEC-WA-06 antes de produção.

## 6. Precedência documental

Esta decisão expressa é **posterior** a trechos dos documentos 11, 25, 30 e ao planejamento Meta anterior que assumiam “números da gestora dedicados à loja”. **A titularidade foi alterada por decisão de negócio**; ajustes físicos/políticas jurídicas devem ser conciliados pela frente principal, não alterados silenciosamente. Contratos [conciliacao PR1/PR2](conciliacao-pr1-pr2-s0-whatsapp-v0_1.md) e [interface compartilhada](interface-compartilhada-s0-meta-v0_1.md) adotam esta nova precedência.
