# AL-IA-04 — Matriz de decisões, deltas históricos, pendências e revisão cruzada

**Data:** 22/10/2026 | **Natureza:** reconciliação DOCUMENTAL da frente OpenAI, **sem edição de normas pertencentes a S0/S1/Meta, sem aceite físico e sem merge**.  
**Legendas:** [DN] manifestação recente expressa; [DA] decisão anterior ainda compatível; [HS] histórico/superado; [P] proposta; [R] pendência técnica/normativa interna; [V] validação externa.

## 1. De onde vêm estas informações

### 1.1. Fontes inspecionadas

[TRECHO COMERCIAL INTERNO EXCLUÍDO DA VERSÃO PÚBLICA]
- Pacote do Drive com **55 arquivos, cópia 17/10/2026**: 00A/05/06/08B/08C/09/10/11/13A/21/22/23/24/25/26/31/33/35/36/40/41, entre outros. Não se assume que estejam todos versionados no GitHub ou que seu conteúdo tenha sido inteiramente migrado.
- Frente OpenAI **PR #3 Draft**, arquivos OAI-05/06/07/08, E01, mapa de capacidades e planos E02/E03; trabalho documental mais recente **não** prova ativação de integração real.
- Frentes S0 **PR #1, #8 e #12 Draft**, em suas respectivas branches, para localizar contratos candidatos, gates de status, versão/snapshot e mecanismos locais de segurança. Esta revisão não as modifica.
- **Alinhamento verbal/textual da presente conversa de 21–22/10/2026**, cujas manifestações posteriores do responsável são marcadas **[DN]**.

[TRECHO COMERCIAL INTERNO EXCLUÍDO DA VERSÃO PÚBLICA]

### 1.2. Invariantes preservadas

- Oito status comerciais canônicos e distinção de eventos técnicos, salvas mudanças futuras expressas.
- Isolamento por concessionária, fonte/proveniência, autoria, auditoria, prevenção de duplicidade, minimização legalmente exigida e autorização externa.
- Marca `vendido` **manual do Consultor** com prova de venda do Banco; negativa definitiva do Banco **humana** com evidência; preparação da ficha ≠ remessa efetiva.
- F01 após handoff no caso silenciada; cliente com venda anterior na própria loja retorna para humano.
- IA não executa chamada bancária, Meta ou SQL privilegiado por simples vontade do modelo.
- Não houve nesta entrega implantação, teste remoto, gasto OpenAI, configuração Meta ou autorização do Banco.

## 2. Matriz dos principais deltas entre histórico e decisões mais recentes

| ID | Tema | Texto/premissa anterior (fonte) | Decisão mais recente [DN] | Consequência / responsável por reconciliar |
|---|---|---|---|---|
| DEL-01 | Correção cadastral humana | Docs 23, 24, 40, 41 D41-04 e OAI-05 permitem correção pontual pelo operador designado | **Consultor NÃO edita ficha**; apenas conversa, lê quando interface existir e conclui; F03/S0 atualizam | S0/S1/frontend/contratos OAI precisam revisar UI, C13, ACL e testes; não retirar silenciosamente escrita de banco/remessa humana |
| DEL-02 | Histórico F03 | OAI-05 limitava snapshot preferencialmente à conversa/caso corrente e minimização, sem histórico integral padrão | F03 deve poder consultar **todo histórico do mesmo cliente na mesma concessionária** até cutoff, inclusive outros consultores e mídias | S0/OAI/privacidade: consulta lógica completa autorizada, preservando cutoff, segmentação segura, proveniência, retorno e custo |
| DEL-03 | Mensagens após fechamento | Contratos OAI e rechecks S0 tratam inbound posterior como invalidação indistinta de snapshot | Evento anterior permanece **historicamente imutável**; inbound novo pertence somente a futura execução após nova conclusão; não permitir commit antigo sobre atualização nova | S0 PR #12 e OAI: separar validade histórica do cutoff vs elegibilidade contemporânea de escrita |
| DEL-04 | Gatilho F03 | Contratos antigos ainda têm ambiguidades sobre “final do atendimento” | **Somente clique/ato expresso do Consultor** dispara F03, independentemente de janela Meta fechada | S0/frontend: evento técnico, autorização, precisão temporal, repetição |
| DEL-05 | Status via F03 | OAI-05/OAI-07 e PR #8 conservadores vedam mudança automática `perdido`/outros por conclusão humana | **F03 pode desencadear transições comerciais permitidas via S0**, inclusive `perdido` e motivo em desistência clara; `vendido` exclusivamente humano | S0/contratos de domínio: reconciliar eventos, catálogo, evidência, origem da mudança e provas; não inferir aprovação para negativa bancária |
| DEL-06 | Novas fichas por negociação | Algumas propostas anteriores separam versão/ficha por ciclo | **Ficha do cliente é contínua e única na loja**; histórico de negociações/remessas fica em registros próprios | S0: preservar snapshots históricos e evitar duplicação de ficha viva |
| DEL-07 | Atualização após remessa | Dúvida se remessa congela formulário | F03 segue atualizando silenciosamente ficha atual a cada nova conclusão humana, **mesmo após envio ao Banco**, sem aviso de rotina | S0: snapshot de remessa não muda retroativamente; status de enviado exige evidência |
| DEL-08 | Falha repetida F03 | Doc 23 tolerava correção pontual humana | Defeito F03 é **incidente crítico a diagnosticar e corrigir**, não política de preenchimento manual pelo Consultor | S0/S1 manutenção; possível administração Diretores via MCP em outra trilha, não fallback automático |
| DEL-09 | Pendência após F03 | OAI-08 pode considerar fluxo posterior F02 para esclarecer | Preferir devolver ao **Consultor original**; se indisponível, **Gestor do Consultor**, que decide atribuição/resolução | S0/S1 dono da fila; F02 não recebe automaticamente a pendência para template |
| DEL-10 | Janela 24 horas | Poderia ser confundida com tempo após encerramento humano | 24h Meta desde última mensagem inbound; janela expirada **não conclui** humano nem dispara F03; caso continua administrável | Meta/S0: preservar três relógios independentes: janela Meta, eventos humanos, 24h após template final de perda |
| DEL-11 | MCP do Diretor | D41-03: apenas importar lotes e remanejar via MCP; C13/41 operadores corrigem dados | MCP Diretor administra amplamente **dados operacionais**, inclusive exclusão em massa, sob confirmação; **não edita plataforma** e **jamais edita base protegida de auditoria MCP** | S0/MCP: **conflito normativo pendente** e grandes exigências de segurança/retenção; não ampliar grants físicos silenciosamente |
| DEL-12 | Bases de conhecimento | Consolidado 10/10 tratava duas camadas genéricas e “aprendizado automático”; ainda sem organização de base por loja | Conteúdo institucional e por loja, bases extras só na loja, Prumo cadastra tudo, contexto visível na pausa, vigência e pausa automática opcional | Nova proposta OpenAI/S0; sem criar IA Analista automática revogada |
| DEL-13 | Instruções por concessionária | Hipótese levantada durante o próprio alinhamento “global + por loja” | **Retirada expressamente**; F01 instruções + comportamento globais; F02 e F03 somente instruções globais exclusivas | OpenAI/frontend/MCP: quatro campos conceituais; lojas diferenciadas por fatos, não prompts de estilo |
| DEL-14 | Habilidades | Inicialmente nenhuma taxonomia/guia semântico | Habilidade com conhecimento associado; nenhuma F01/F02/F03 pode criá-la; Diretor pode cadastrar via MCP apenas sobre capacidade já existente, nova integração exige software separado | OpenAI/MCP/S0: catálogo e mecanismo sob desenho futuro |
| DEL-15 | Envio ao Banco | Docs 06/13A/21 e OAI preveem remessa humana atual; integração direta apenas cenário condicionado | Preferência de **envio direto no futuro se viável** por ação S0 desencadeada pela F01 ou F03; alternativa humana permanece | Banco [V] e S0 [R]; responsável expressamente **adiou verificação externa**, não fazer investigação agora |
| DEL-16 | IA Analista | Consolidado v0.2 desenha IA separada que otimizaria F01 | Doc 06 v4.6 posterior **excluiu IA Analista autônoma**; conversa atual **não a restabeleceu** | Não criar módulo/treinamento autônomo a partir da visão histórica |
| DEL-17 | Retorno após `vendido` | Doc 22 prevê novo caso humano sem alterar venda passada | **Confirmado**; ficha viva continua a ser atualizada após novo encerramento humano | S0/S1 mantém histórico de venda e roteamento somente humano |
| DEL-18 | Mudança de número | Modelos antigos enfatizam telefone como identificação dentro da loja | Mesmo cliente poderá ter **múltiplos telefones** ou substituir antigo após identificação verificada; IA pode conduzir verificações, porém critérios seguros/execução S0 [R] | S0/identidade/privacidade: impedir fusão fraudulenta; não vincular só por alegação |

## 3. Referências normativas e documentos impactados fora desta frente

| Fonte/arquivo | Tensão/ação futura indicada — **não executada agora** |
|---|---|
| Drive docs 23, 24, 40, 41 | Eliminar permissão excepcional de editar ficha pelo Consultor; rever formulários e eventos de correção preservando autoria e prova de banco |
| Drive docs 05, 06, 08B, 09, 11, 13A, 21, 22 | Reconciliar classificação `perdido` pela F03, provada negativa do Banco, cadências, retorno pós-venda e mudança de nomenclatura |
| OAI-05 | Cutoff com acesso a histórico integral da própria loja, multimodal autorizado, regras novas de F03 e sem edição manual do Consultor |
| OAI-07 | F03 classificador pode resultar em status comerciais validados, sem criar venda/negativa/remessa fictícia |
| OAI-08 / PR #8 | F03 pendência prioritariamente ao Consultor/Gestor em vez de recontato F02; nova semântica de perdas |
| PR #12 S0 CFI-01 | Snapshot histórico versus commit, reentradas, versões, autorização de fila e antirressurreição de valores antigos |
| Docs S0/S1/front | Interface de visualização não editável; roteamento de pendência ao Gestor; troca telefone; nomenclatura Diretor/Gestor/Consultor; modo F01 silenciada |
| Guia/MCP/ACL admin | Escritas amplas x D41-03, confirmação por operação, auditoria MCP inviolável pelo próprio MCP; guias de criação de bases |
| Docs Banco/Meta/LGPD | Homologação de remessas e templates, documentação multimodal, retenção e exportação massiva |

**Não copiar/reescrever estes arquivos normativos nas branches alheias**: a mudança nesta frente é somente o registro fiel das decisões para revisão cruzada. Não confundir “registrado como [DN]” com “ratificado/homologado em toda a matriz física”.

## 4. Decisões encerradas e não reabrir sem mudança expressa

1. Isolamento real entre concessionárias, inclusive recuperação semântica e ficha/histórico.
2. F03 sob clique humano com cutoff; novo encerramento gera nova execução, sem mirar mensagens posteriores.
3. Consultor não edita ficha; F03/S0 atualizam dentro do catálogo.
4. Ficha evolutiva por cliente/loja, não uma ficha completa por negociação.
5. Remessa não bloqueia atualização cadastral, mas snapshot de remessa é histórico.
6. F03 pode gerar mudança automática de status permitida e registrar motivo; `vendido` continua humano/manual/com prova; negativa bancária humana não se confunde com desistência.
7. Pendência F03 ao consultor original e, se indisponível, gestor.
8. Janela Meta e conclusão humana independentes; 24h final-template perdida é outra regra.
9. Prumo é administradora única de conhecimento; bases de campanha por loja isoladas; contexto preservado na pausa; pausa automática opcional data/hora.
10. Quatro campos globais por IA e **nenhum campo de instrução/comportamento por loja**.
11. Habilidades futuras com conhecimento associado; MCP Diretor configura somente capacidades técnicas existentes; IA operacional não cria habilidades.
12. Auditoria protegida do MCP jamais editável pelo próprio MCP; outras operações autorizadas exigem confirmação específica.

## 5. Pendências de especificação [R] — não impedem encerrar alinhamento conceitual

**Catálogo e dados:**
- Definir catálogo final de campos, tipos e obrigatórios para remessa; tratamentos especiais de documentos e mídias, dados sensíveis, consentimento, proveniência e validade.
- Como autenticar/verificar troca de número e vinculação de telefones na mesma loja, sem criar risco de tomada de ficha por impostor.
- Interface exata de visualização da ficha pelo Consultor; a intenção é ficha inteira, read-only, campos presentes/faltantes, mas desenho visual não foi aprovado.
- Precisar concorrência/versionamento F01/F03/MCP, aplicação de dados incompletos, conflitos e fontes (inclusive declarações históricas).

**Estados/operação:**
- Catálogo de motivos `perdido`, quais transições automáticas da F03 são admissíveis e como registrá-las com evidência.
- Tratamento bancário de pedido de correção/complemento, retificação de remessa/status errôneos e efeitos de segundo financiamento; sem consulta externa nesta etapa.
- Política técnica de indisponibilidade do Consultor e roteamento ao Gestor quando equipes/vínculos mudarem.
- Tratamento de falhas Meta/template e provas de envio para `cadastro enviado ao banco`; sincronização de clocks distintos.
- Compatibilidade entre regra documental anterior de `perdido` por 24h após template final e outras origens de `perdido`.

**Conhecimento/configuração:**
- Tabelas/coleções físicas, índices por loja, recuperação híbrida/vetorial, filtros e credenciais; ferramentas File Search/Function Calling/MCP opcionais.
- Estados/versões de base e significado de pausa/arquivamento, fuso/precisão da data e hora, possibilidade de reativação e revisão de vigências.
- Atualização atômica de instruções globais, validação de prompts editáveis, versões e rollback.
- Modelo/custo/cache, qualidade de transcrição/visão, estratégia de janela de contexto e benchmark por tarefa; **sem consumo API real autorizado aqui**.
- Configuração de catálogo de habilidades e guias semânticos MCP versus criação de nova integração codificada.

**Governança jurídica/técnica:**
- Escopo de exclusão/exportação de dados pelo MCP do Diretor frente a retenção, auditoria legal e backups; proteção física dos registros MCP e verificação da segunda confirmação.
- Consentimentos, segregação por concessionária, minimização/uso de histórico multimodal por fornecedor externo, opt-out e regras Meta/Banco.
- Conciliação documental entre GitHub, Drive e arquivos locais antes de excluir fontes. **Não foi confirmado que GitHub contém tudo do pacote de 55 documentos.**

## 6. Validações externas deliberadamente abertas [V]

- **instituição financeira:** API, possibilidade de remessa direta, prova/autorização, credenciais, estados e remessas; **não investigar nem decidir agora por instrução expressa**.
- **Meta/WhatsApp:** contratos/categorias/status reais dos templates, mídia, tratamento de janela de atendimento e uso permitido de dados/mensagens.
- **Privacidade/LGPD e fornecedor IA:** base legal, finalidade, período de retenção, tratamento/transcrição de áudio e demais mídias, transferência a prestador e direitos.
- **Custos e viabilidade API:** requerem documentação técnica atual e testes autorizados; não presumir orçamento, capacidade, modelo ou preço imutável.

## 7. Critérios de revisão documental

Uma frente responsável que for integrar estas decisões deverá: (i) identificar decisão [DN] e premissa [HS] afetada; (ii) emendar documentação aprovada com registro de precedência, sem apagar origem; (iii) validar assinatura/titularidade S0/S1/Meta; (iv) preparar contrato de teste com dados sintéticos isolados A/B; (v) pedir homologação externa onde necessário; (vi) só depois implementar os gates liberados. Não atribuir a estes arquivos pontos de progresso ou status de `APROVADO EM PRODUÇÃO`.

**Ligação interna:** [AL-IA-01](./ALINHAMENTO_2026_10_22_01_JORNADA_F01_F02_F03_v0_1.md), [AL-IA-02](./ALINHAMENTO_2026_10_22_02_CONHECIMENTO_CACHE_HABILIDADES_v0_1.md), [AL-IA-03](./ALINHAMENTO_2026_10_22_03_MCP_DIRETOR_GUIAS_AUDITORIA_v0_1.md), [AL-IA-00](./ALINHAMENTO_2026_10_22_00_INDICE_E_PRECEDENCIA_v0_1.md).
