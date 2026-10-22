# E01-KH v0.3 — Contrato lógico de conhecimento, habilidades e MCP do Diretor

**Data:** 22/10/2026. **Classe:** [DN] regras funcionais AL-IA-02/03; [P/R] campos, operações e arquitetura a pactuar. **Candidato documental, não tabela SQL, endpoint MCP, tool executável ou homologação.** Complementa E01/OAI-01 v0.3, AL-IA-02, AL-IA-03 e E02 v0.3. Não altera S0, S1, Meta ou Frontend.

## 1. Fronteiras de confiança e níveis

1. **Política estrutural S0**: fonte da verdade de autenticação, ACL/tenant, ações, catálogo de campos, versionamento, estado comercial, escopo de mídia e auditoria. Nunca inserida na base de fatos como se fosse uma instrução alterável.
2. **Quatro parâmetros globais versionados**, sem versões por concessionária: `f01_instrucoes`, `f01_comportamento`, `f02_instrucoes` e `f03_instrucoes` (nomes [P]). F02/F03 não têm campo administrativo de comportamento; guias MCP não integram esses quatro. O conteúdo pode ser gerenciado pela Prumo, mas **não altera ACL nem software**.
3. **Conhecimento empresarial**: institucional compartilhável quando autorizado + bases factuais por concessionária; consulta requer ACL e elegibilidade por IA, fase e data.
4. **Histórico/ficha/casos de cliente**: fonte transacional separada, escopo pessoa/concessionária e cutoff em F03; conversa de cliente não é fato institucional.
5. **Guias MCP**: manuais semânticos para o agente externo do Diretor operar APIs autorizadas, distintos do conhecimento acionado por F01/F02/F03.
6. **Habilidades**: catálogo de invocações de capacidades já implementadas. Descrição pode instruir uso, mas **não cria integração**.

## 2. Registro lógico de fato e base [P/R]

`FatoVersionado` proposto:
- Identidade/versão imutável da revisão; `scope_kind=INSTITUCIONAL|CONCESSIONARIA`; `owner_concessionaria_ref` obrigatório apenas no segundo escopo; `base_ref` pertencente ao mesmo escopo.
- `gatilho_semantico_declarativo`: enunciado que resume o assunto, **não** frase conversacional fingindo ser cliente.
- `fato_canonico`: afirmação aprovada, com condições, limites, exceções e unidade exata; **não** uma ordem para editar dados ou ignorar S0.
- `proveniencia`/responsável/estado de aprovação/versão; `eligible_ai_kinds`; datas de vigência (por fato/campanha), idioma, política de visibilidade e vínculo de fonte quando autorizado.
- `knowledge_id`/`base_id` não deduzidos por similaridade; recuperação e resposta citam versão real. Formato físico, revisão de conteúdo bancário e política de proveniência são [R/V].

`BaseVersionada` proposta:
- `base_ref`, proprietário imutável (institucional ou concessionária), `contexto_semantico` de escopo, `estado`, `pausar_em` opcional, timezone explícito, versão, aprovação e trilha de alterações.
- Bases adicionais podem existir **somente dentro da concessionária proprietária**, sem migração por nome. Contexto escrito no presente ou passado continua histórico; pausá-la não exige reescrever seu texto.
- `pausar_em` pode faltar. Quando presente e vencido, consultas **não** usam fatos como oferta atual mesmo com job de mudança de `estado` atrasado. Reativação legítima não prorroga vigência de fatos automaticamente.
- A data do **fato/campanha** é avaliada independentemente da data de pausa da base; descrição com término "previsto" não prova término efetivo nem prorrogação. Na incerteza, não ofertar como condição vigente; sinalizar revisão.

## 3. Recuperação e composição autorizada [P]

Pipeline candidato antes de qualquer modelo:
(1) S0 resolve operação, função, ator, concessionária, permissões e instante; (2) filtra no banco/API **antes** de busca semântica por escopo e função; (3) obtém candidatos por busca textual/vetorial/opção equivalente sem cross-tenant, **sem pressupor vetor ou produto específico**; (4) revalida ACL, status de base, `pausar_em`, vigência de fato/campanha e versão das fontes **após** a busca; (5) distingue `modo=oferta_atual` de `modo=interpretacao_historica`; (6) retorna conteúdo mínimo com fonte/versão, ou “não comprovado”; (7) S0 valida saída antes de enviar/responder.

No **modo histórico**, base pausada pode fornecer **contexto da campanha e fatos históricos identificados como não vigentes** para compreender o que cliente mencionou; jamais elevar esse contexto a oferta atual. No **modo de oferta**, somente fatos comprovadamente vigentes. F03 lê evidências históricas de casos anteriores da mesma concessionária até cutoff por caminho transacional autorizado, nunca por mistura informal com FAQ.

Falhas de ACL, versão, horário, fonte ou mídia são **negação segura**; não rebaixar para busca global indiscriminada. Garantir que filtros do índice, resultados, logs, embeddings, resumo, fallback e observabilidade mantenham escopo. Ref. de história de cliente jamais autoriza consultar outra loja.

## 4. Montagem de prompt e cache [P/R]

Ordenação lógica: **barreiras estruturais fora do prompt** → conteúdo global versionado da função → somente comportamento F01 quando F01 → fatos liberados/versionados → contexto transacional mínimo/atribuído, com cutoff para F03 → catálogo de ferramentas autorizadas → resposta tipada e revalidação S0. Conhecimento e mensagem são **dados não confiáveis como instruções**.

Cache de prefixos globais **opcional**. Não utilizar cache como identidade, memória do cliente, autorização, RAG persistente ou argumento de frescor. Alterações de instrução, pausa/vigência, mudança de papel, revogação e handoff surtirão efeito por consulta/guarda atuais, inclusive com cache HIT. Configuração de chaves, TTL, modelo e custo [R], sem premissas de economia.

## 5. Habilidade configurável e guias do MCP [P/R]

`HabilidadeVersionada` candidata: ref, versão, título, descrição semântica, conhecimento de uso e exceções, operação pré-existente/allowlist, esquema de parâmetros, IAs elegíveis, escopo, condições de ativação, `requires_confirmation` conforme operação, custo/risco, ativo/pausado, responsável Prumo. Para registrar e ativar habilidade: operação **já existente e testada**, confirmação administrativa específica quando mutação, ACL atual e escopo da IA compatíveis. Invocação em produção exige S0 autorizar a cada chamada, sem auto-instalar ferramenta.

`GuiaMCPVersionado` candidato: objetivo, como preparar base/fato/campanha/configuração, riscos, ferramentas MCP preexistentes, método de prévia, campos, exigência de confirmação, tratamento de falhas e condições de escalação para humano/técnico. Guia é documento para agente externo do Diretor, **não** um dos quatro prompts e **não** autorização de execução.

**Diretor/MCP:** consultas rotineiras com autorização; para **cada mutação** (criar/alterar/importar/exportar sensível/transferir/excluir, inclusive em massa quando pertinente) o backend prepara prévia com operação/escopo/contagem/irreversibilidade, exige segunda confirmação **autenticada e vinculada àquela operação específica**, revalida ACL/versões e executa idempotente/atomicamente o que S0 permitir. "Faça tudo" não equivale a confirmar operações subsequentes. Uma ferramenta MCP existente é pré-requisito, não permissionamento implícito por ChatGPT.

**Área protegida de auditoria do próprio MCP:** disponível para consulta autorizada; **nenhuma** chamada MCP de Diretor pode reescrever/apagar/forjar registros anteriores, mesmo após confirmação. Novos eventos legítimos vêm do subsistema de auditoria protegido, nunca de método editável pela IA; separação real de credenciais/regras S0 é mandatória. Destruição legal extraordinária [V] é processo fora do MCP.

**Nova integração/código:** o MCP só pode documentar proposta para engenharia; nunca executar deploy, SQL de migração, mudança de guarda, novo SDK, privilégio ampliado nem criação de função externa.

## 6. Casos negativos e decisões abertas

- Duas lojas com bases "Campanha Primavera" iguais e fatos diferentes → nenhuma fonte cruzada por busca/índice/cache.
- Base ativa com fato vencido → não ofertar; base pausada com cliente citando oferta antiga → explicar como histórica sem tratá-la como vigente; `pausar_em` vencido com job atrasado → bloquear oferta.
- Usuário tenta administrar instruções "F02 comportamento por loja" → inexistente; tentar configurar habilidade para API não instalada → somente proposta técnica, sem ativação.
- Diretor tenta excluir própria trilha MCP, ainda que confirme → **negação estrutural**; tentar mutação sem confirmação específica → nenhum efeito.
- Cliente injeta "ignore regras" dentro de fato recuperado → não altera ACL, estado comercial ou ferramenta.
- Multi-F01 cache HIT em lojas distintas → nenhum dado privado entre execuções.

**Dependências pendentes:** catálogo de dados e gates da S0; políticas de conhecimento e aprovação bancária; mecanismo de recuperação e isolamento; contrato MCP de prévia/confirmacão/auditoria; arquitetura de mídia e privacidade; UI administrativa. **Este documento não os implementa.**
