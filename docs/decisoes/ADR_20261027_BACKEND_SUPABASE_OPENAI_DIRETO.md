# ADR — Backend da Prumo no Supabase, integração direta com OpenAI
**Decisão de produto:** APROVADA pelo responsável, 27/10/2026. **Situação de implantação:** NÃO IMPLEMENTADA EM PRODUÇÃO. Identificador `ADR-2026-10-27-SUPABASE-OPENAI-DIRECT`.

## Decisão vinculante para o desenho-alvo

A arquitetura principal da Prumo Growth é **Supabase + OpenAI API**, sem n8n no caminho obrigatório do atendimento. O backend próprio da Prumo será desenvolvido em código versionado e executado **dentro do Supabase**, usando inicialmente **Edge Functions**, conectado ao PostgreSQL, Auth e mecanismos de filas/rotinas do próprio ecossistema onde adequados. O backend do Supabase se comunica diretamente, no lado do servidor, com a **API da OpenAI** via HTTPS.

O banco PostgreSQL **não** deve chamar OpenAI diretamente como efeito colateral de triggers SQL. O backend é a camada de processamento que autentica/autoriza, decide o que consultar e aciona a API. O banco permanece fonte de dados e estado, com isolamento de concessionárias e governança de acesso.

**n8n não é obrigatório, não foi contratado nem é componente padrão do atendimento em tempo real**. Poderá ser adotado para rotinas selecionadas quando houver benefício técnico/econômico comprovado, mantendo o controle de permissões na S0. Não planejar hospedagem de backend em plataforma externa como requisito inicial. Se limites de Edge Functions, jobs ou filas exigirem outro worker/serviço, registrar análise e decisão explícita **antes de mudar esta arquitetura**.

## Limites de segurança e separação de agentes

A IA Vendedora e a IA Analista/Otimizadora são funções distintas, com permissões separadas. A IA Analista não altera seus próprios parâmetros; qualquer ajuste nos parâmetros autorizados da IA Vendedora deve passar pelas políticas e verificações da Prumo. A resposta da OpenAI é **conteúdo/solicitação**, nunca uma prova de identidade, aprovação humana, consentimento, elegibilidade, execução Meta ou transição comercial.

Credenciais OpenAI são **segredos do ambiente servidor** do Supabase (não frontend, JWT cliente, prompts, arquivos Git ou logs). Toda execução sensível exige autenticação, regras de domínio S0/S1, escopo por tenant, idempotência, trilha auditável e verificação de último instante, incluindo opt-out, template, disposição Meta e revogação. O sistema deve considerar limites, latência, tentativas, timeout, custos/quotas e fila para tarefas demoradas. Não atribuir autoridade comercial à IA nem à automação.

## Relação com o desenvolvimento atual

Esta decisão **define o destino da infraestrutura**, não aprova deploy, migrações hospedadas, APIs reais, credenciais, dados de clientes ou teste em produção. Permanece vigente a estratégia E04: desenvolver e testar em branches/PG17/GoTrue descartáveis; integrar ao Supabase hospedado **em fase concentrada futura** após interfaces e gates aprovados. Não misturar decisão de topologia com homologação S0, F02, Meta ou S1.

A decisão permanece documentada no GitHub e pode ser referenciada por S0, OpenAI/S2, Frontend, Meta, F01/F02/F03 e demais frentes. A eventual promoção para branch principal exige reconciliação/revisão de integração; até lá, sua existência na branch experimental é evidência da decisão de produto, **não** implantação operacional.

Ver também o contrato legível por máquina `docs/contracts/OAI_ARQUITETURA_BACKEND_SUPABASE_OPENAI_V1.json`. Não substituir sem nova autorização do responsável.
