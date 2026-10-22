# AL-IA-06 — Auditoria de fidelidade e completude do alinhamento funcional

**Data da auditoria:** 22/10/2026  
**Escopo auditado:** pacote AL-IA-00/01/02/03/04/05, incorporado à branch `feat/s2-openai-adapter-sintetico` (PR #3 Draft), e índice `README.md`.  
**Objetivo:** impedir que manifestações do responsável sejam omitidas, invertidas, generalizadas ou confundidas com propostas de engenharia.  
**Veredito:** **APTO COMO REGISTRO DOCUMENTAL DE ALINHAMENTO, COM RESSALVAS NORMATIVAS/EXTERNAS EXPLICITADAS**. **NÃO significa implementação, teste, homologação de S0/Meta/Banco ou conciliação plena de 55 fontes.**

## 1. Metodologia e limites

1. Conferência das decisões expressas na conversa de alinhamento encerrada em 22/10/2026, com atenção a retificações posteriores (a última decisão expressa prevalece sobre hipóteses iniciais).
2. Revisão dos seis documentos AL-IA e de seus rótulos **[DN] decisão nova**, **[DA] anterior compatível**, **[HS] histórico**, **[P] proposta**, **[R] pendência**, **[V] validação externa**.
3. Cruzamento com o consolidado auditado de **10/10**, os contratos OAI-05/OAI-07/E01 na frente OpenAI, as decisões Q do pacote do Drive **17/10** (em especial 06/08A/08B/08C/13A/21/22/23/41) e com o contexto recente dos PRs S0 #8/#12.
4. Busca de **omissões concretas**, frases que sugiram autorização operacional não dada e conflitos documentais não sinalizados. Os contratos anteriores em outras branches **não foram alterados**.
5. Aplicação de correções **na própria branch OpenAI** nos arquivos identificados, sem merge, código ou chamadas a serviços reais.

**Limitação honesta:** esta auditoria verifica o pacote consolidado contra as regras relevantes **recuperadas e disponíveis** do diálogo e das fontes acima. **Não substitui auditoria jurídica de todo o acervo de 55 documentos, revisão física de endpoints/SQL/UX nem acesso às conversas integrais de outras frentes que não estejam neste alinhamento.** Portanto, não afirmar garantia matemática de “nenhuma frase jamais omitida”. A decisão do responsável prevalece sobre extrapolação do assistente; se surgir uma fonte conflitante, deve-se registrar nova revisão.

## 2. Achados efetivos e reparos feitos

| ID | Severidade | Achado da primeira versão | Correção documental |
|---|---|---|---|
| AUD-01 | **Alta** | Faltava a regra explícita de **duas falhas consecutivas comprovadas** de template que cancelam a sequência F02; uma falha isolada não cancela a próxima. | Inserida em **AL-IA-01 §3** e reforçada em **AL-IA-04 DEL-21** / **AL-IA-05 §4A**. |
| AUD-02 | **Alta** | O retorno de cliente em `cadastro enviado ao banco` havia ficado implícito; a regra antiga obriga **retorno direto ao humano** sem retomar F01, preservando o resultado bancário anterior. | Inserida em **AL-IA-01 §6**, **AL-IA-04 DEL-20** e **AL-IA-05 §4A**. |
| AUD-03 | **Alta** | Múltiplos telefones na ficha foram registrados sem explicitar conflito com o **telefone como ID comercial** aprovado anteriormente nos docs 08A/08C. | Separados desejo novo (IA verifica identidade; substituição ou vários telefones) e **questão técnica/normativa não conciliada** em **AL-IA-01** e **AL-IA-04 DEL-18**. |
| AUD-04 | **Alta** | Disponibilidade de foto, vídeo, áudio e documentos à F03 podia ser lida como ordem de armazenar mídia bruta permanentemente, contrariando diretriz antiga de transcrições/extrações. | **AL-IA-01 §4, AL-IA-04 DEL-19 e AL-IA-05 §4A** passaram a distinguir **acesso lógico multimodal** de **retenção física** ainda [R/V]. |
| AUD-05 | Média | A relação entre o template final e o marco de inatividade estava sintetizada demais e podia confundir **24h para planejar o template** com **24h após o envio efetivo** para marcar `perdido`. | Ambos os intervalos foram explicitados em **AL-IA-01 §3**, **AL-IA-04/05**. |
| AUD-06 | Média | A entrada de lead por telefone apto, lotes independentes e o fato de `primeiro disparo enviado` **não iniciar atendimento ativo** estavam pouco visíveis. | Ingressos/estados foram incluídos em **AL-IA-01 §2A**, **AL-IA-04 DEL-22** e **AL-IA-05 §4A**. |
| AUD-07 | Média | Não estavam reiterados o papel do número WhatsApp da Prumo **dedicado a uma concessionária**, os horários receptivo/humano e o cenário de cliente que **declara** compra anterior mesmo sem prova naquela loja. | Incluídos em **AL-IA-01 §2A**, **AL-IA-05 §4A**, sem vazamento entre lojas nem confirmação bancária presumida. |
| AUD-08 | Média | Falta de distinção explícita entre uma **confirmação final por e-mail apenas cogitada** e um requisito efetivo da F01. | Classificada como **histórica/pendente, não aprovada**, em **AL-IA-05 §4A**. |
| AUD-09 | Média | A continuidade com o Consultor após novas mensagens poderia ser lida como liberação automática do caso na janela de 24h. | **AL-IA-01 §6** explicita preferência pelo mesmo Consultor enquanto elegível, janela Meta desde último inbound, **sem conclusão automática por prazo**; atribuição após clique e fora da janela permanece [R]. |
| AUD-10 | Baixa | Retorno após `perdido` com histórico próprio não estava em destaque. | Reforçado em **AL-IA-01 §6** e **AL-IA-05 §4A**, sem recuperar histórico legalmente eliminado. |

Estas correções são **precisão/recuperação de regras já existentes ou confirmação posterior**. **Não autorizam código novo nem mudam status físico.** O pacote original tinha boa cobertura das decisões recentes; as lacunas encontradas estavam predominantemente nas regras antigas resumidas e nas interfaces entre uma decisão nova e um contrato anterior.

## 3. Checklist explícito de decisões recentes — resultado da auditoria

| ID | Requisito/decisão do responsável | Onde está registrado | Resultado |
|---|---|---|---|
| C01 | Isolamento absoluto A/B/C, incluindo conteúdo semântico, históricos, clientes e respostas | AL-IA-01 §1; 02 §3/4; 04 | **Coberto** |
| C02 | Papéis Diretor/Gestor/Consultor; consultor sem edição cadastral | AL-IA-01 §1/4; 04 DEL-01 | **Coberto** |
| C03 | Consultor provavelmente visualiza ficha inteira **sem editar**; UI final não homologada | AL-IA-01 §4; 04 §5 | **Coberto, com incerteza preservada** |
| C04 | F03 apenas após clique humano, inclusive em qualquer handoff; Meta 24h não dispara F03 | AL-IA-01 §4/6 | **Coberto** |
| C05 | Cada encerramento tem cutoff incluindo última mensagem naquele momento; novos encerramentos permitem novas execuções | AL-IA-01 §4 | **Coberto** |
| C06 | Histórico lógico integral do cliente na concessionária desde primeiro atendimento, inclusive diferentes humanos, IAs, mídias e templates | AL-IA-01 §4; 04 DEL-02/19 | **Coberto; forma física [R/V]** |
| C07 | Interpretação temporal e correções; S0 aplica campos permitidos; F03 não inventa fatos | AL-IA-01 §4; 02 §3 | **Coberto** |
| C08 | Ficha viva única por cliente/concessionária; histórico de negociações/remessas preservado em eventos próprios | AL-IA-01 §4/5; 04 DEL-06/07 | **Coberto** |
| C09 | F03 atualiza ficha mesmo que antes enviada ao Banco, sem aviso de rotina | AL-IA-01 §4; 04 DEL-07 | **Coberto** |
| C10 | F03 sinaliza contradição não resolvida e lacunas essenciais; opcional não impede seguimento | AL-IA-01 §4 | **Coberto** |
| C11 | Defeito recorrente F03 é incidente crítico, não editar manualmente ficha pelo Consultor | AL-IA-01 §4; 04 DEL-08 | **Coberto** |
| C12 | Pendência ao Consultor original; indisponível → Gestor que decide solução/redistribuição | AL-IA-01 §3/4; 04 DEL-09 | **Coberto** |
| C13 | F03 pode provocar transições automáticas S0, inclusive `perdido` por desistência e razão | AL-IA-01 §5; 04 DEL-05 | **Coberto, catálogo [R]** |
| C14 | `vendido` é exclusivamente manual do Consultor, com confirmação real Banco | AL-IA-01 §5; 04 | **Coberto** |
| C15 | Remessa efetiva ≠ ficha pronta; `cadastro enviado ao banco` requer evidência; negativa definitiva humana ≠ desistência | AL-IA-01 §5; 04 | **Coberto** |
| C16 | Preferência por envio direto futuro via serviço S0, acionado por F01/F03; humano como alternativa; Banco não investigar agora | AL-IA-01 §2/5; 04 §6 | **Coberto, [V] em aberto** |
| C17 | Retorno após `vendido` na mesma loja sempre humano; depois F03 ainda atualiza cadastro vivo | AL-IA-01 §2/6; 04 DEL-17 | **Coberto** |
| C18 | Múltiplos números cliente mediante verificações conduzidas por IA, nunca misturar lojas | AL-IA-01 §6A; 04 DEL-18 | **Coberto, modelo físico [R]** |
| C19 | Gatilho semântico declarativo + fato canônico direto + metadados de controle | AL-IA-02 §2 | **Coberto** |
| C20 | Bases institucionais e bases isoladas por concessionária; só Prumo cadastra | AL-IA-02 §3/4; 03 §6 | **Coberto** |
| C21 | Bases extras por concessionária, ativas, pausadas, reativáveis | AL-IA-02 §4 | **Coberto** |
| C22 | Contexto de base é criado possivelmente na origem, pode estar no presente e permanece visível na pausa | AL-IA-02 §4 | **Coberto** |
| C23 | Campanha com validade expirada não pode ser ofertada só porque base está ativa; data prevista ≠ data real | AL-IA-02 §4 | **Coberto** |
| C24 | Pausa automática **opcional** por data e hora, e também manual | AL-IA-02 §4 | **Coberto** |
| C25 | F01 tem instruções globais + comportamento global; F02 e F03 têm cada uma apenas instruções globais; nenhum prompt por concessionária | AL-IA-02 §5 | **Coberto** |
| C26 | Campos operacionais das IAs não se confundem com guias semânticos para ChatGPT do MCP | AL-IA-02 §5; 03 §4 | **Coberto** |
| C27 | Cache OpenAI opcional, decisões por eficiência; atendimentos simultâneos isolados; cache não é memória/autorização | AL-IA-02 §6 | **Coberto** |
| C28 | Sem consulta aberta à internet por padrão, controle por fontes autorizadas | AL-IA-02 §1 | **Coberto** |
| C29 | Habilidades futuras com conhecimento associado; F01/F02/F03 não criam por si | AL-IA-02 §7; 03 §5 | **Coberto** |
| C30 | Diretor via MCP configura habilidades existentes; novas integrações executáveis exigem desenvolvimento fora do MCP | AL-IA-02 §7; 03 §5 | **Coberto** |
| C31 | MCP Diretor amplia administração de dados operacionais, mas não edita código/regras estruturais; confirmação específica antes de executar | AL-IA-03 §1/2; 04 DEL-11 | **Coberto, ACL/retenção [R/V]** |
| C32 | Registros do próprio MCP consultáveis porém **não editáveis/excluíveis pelo mesmo MCP**, nem com confirmação; proteção extensível | AL-IA-03 §3 | **Coberto** |
| C33 | Guias semânticos tipo skills do MCP orientam criação de bases, contextos, conhecimentos e capacidades administrativas | AL-IA-03 §4 | **Coberto** |
[TRECHO COMERCIAL INTERNO EXCLUÍDO DA VERSÃO PÚBLICA]
| C35 | Regras F02 históricas ainda compatíveis (templates, faixas, intervalos de 24h, falha/cancelamento) | AL-IA-01 §3; 05 §4/4A | **Coberto após reparo** |

## 4. Riscos não resolvidos — não imputar nova regra ao responsável

**R1 — Normas antigas ainda conflitantes em outras frentes.** Docs 23/24/40/41 e OAI-05 ainda autorizam excepcionalmente edição cadastral pelo Consultor; OAI-05/OAI-07/PR #8 bloqueiam transições comerciais que o responsável agora deseja viabilizar pela F03; parte do PR #12 pode invalidar snapshots de modo excessivo. **Ainda não houve emenda ou aceite físico nesses arquivos.**

**R2 — Identidade por múltiplos telefones.** A diretriz nova altera hipótese anterior de telefone como chave de negócio. Não adivinhar como indexar, confirmar nova titularidade ou como lidar com reciclagem do número.

**R3 — Mídias da F03.** Acesso lógico amplo ao histórico autorizado precisa ser compatibilizado com retenção, transcrição, disponibilização técnica de mídias e privacidade. Não sacrificar nem a nova abrangência nem os limites existentes.

**R4 — instituição financeira.** Não há confirmação de acesso a API, remessa direta ou prova oficial; decidiu-se **deixar em aberto**. Nenhuma simulação de `cadastro enviado ao banco` só com saída de IA.

**R5 — Governança MCP.** Amplitude de exclusão operacional do Diretor, registros protegidos, retenção legal/backups, identidade forte, dupla confirmação e exportações exigem arquitetura de segurança; não escrever concessões físicas por simples descrição em Markdown.

**R6 — Estado, F03 e relógios.** Cutoff imutável ≠ elegibilidade de commit; última inbound Meta 24h ≠ encerramento do Consultor ≠ 24h após template final. Regras de retorno ao mesmo Consultor e eventual realocação após clique/expiração exigem contratos S0/S1, não inventar uma liberação automática por tempo.

**R7 — Catálogo/terceiros.** Campos essenciais do Banco, lista de motivos `perdido`, templates aprovados, consentimento e limites comerciais ainda têm dependências [R/V]. Habilidades novas, caching e mecanismo de vector search continuam como propostas [P], não implementados.

## 5. Critérios de não regressão para leitura futura

- Não tratar **AL-IA-05 histórico** como autorização para reinstalar IA Analista autônoma ou transformar proposta de comissão/taxa em fato.
- Não tratar **[DN] registradas** como migração/contrato aprovado fora da frente OpenAI; requerer revisão cruzada dos donos S0/Meta/frontend/MCP.
- Não reabrir decisões expressamente concluídas (isolamento, não edição da ficha pelo Consultor, gatilho/cutoff F03, quatro campos globais, Prumo administradora única das bases, pausa/contexto, proteção da auditoria MCP).
- Não alterar visibilidade de clientes, status ou regras via instruções textuais; somente S0 pode efetivar comandos autorizados.
- Não confundir consulta/uso de contexto de uma **base pausada** com permissão para divulgar **oferta vencida**.
- Não afirmar que os 55 documentos do Drive estão íntegros no GitHub nem que foram eliminados/conciliados.
- Não mexer em outras frentes, produzir chamadas pagas, implantar serviço ou fazer merge por esta auditoria.

## 6. Evidência e resultado

Esta auditoria produziu **correções documentais efetivamente publicadas na mesma branch do PR #3** nos arquivos **AL-IA-01, AL-IA-04, AL-IA-05**. O pacote continua com **decisões novas + regras antigas compatíveis + divergências + pendências** claramente demarcadas. A auditoria não exige que o responsável repita o que já decidiu; a equipe implementadora deverá citar esses identificadores e resolver apenas lacunas verdadeiramente técnicas ou validações de terceiros.

**Índice:** [AL-IA-00](./ALINHAMENTO_2026_10_22_00_INDICE_E_PRECEDENCIA_v0_1.md). [AL-IA-01](./ALINHAMENTO_2026_10_22_01_JORNADA_F01_F02_F03_v0_1.md). [AL-IA-02](./ALINHAMENTO_2026_10_22_02_CONHECIMENTO_CACHE_HABILIDADES_v0_1.md). [AL-IA-03](./ALINHAMENTO_2026_10_22_03_MCP_DIRETOR_GUIAS_AUDITORIA_v0_1.md). [AL-IA-04](./ALINHAMENTO_2026_10_22_04_RASTREABILIDADE_DELTAS_PENDENCIAS_v0_1.md). [AL-IA-05](./ALINHAMENTO_2026_10_22_05_HISTORICO_IDEIAS_E_LINHAS_NAO_ATIVAS_v0_1.md).
