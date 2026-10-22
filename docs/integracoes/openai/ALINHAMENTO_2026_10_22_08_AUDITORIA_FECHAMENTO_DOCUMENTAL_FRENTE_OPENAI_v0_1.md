# AL-IA-08 — Auditoria de fechamento documental da frente OpenAI

**Data:** 22/10/2026  
**Escopo autorizado:** SOMENTE `docs/integracoes/openai/**` na branch `feat/s2-openai-adapter-sintetico` / PR #3 Draft.  
**Veredito:** **CONSOLIDAÇÃO DOCUMENTAL INTERNA ADEQUADA, COM PENDÊNCIAS TÉCNICAS E INTERFRENTES EXPLICITADAS**. Não equivale a contrato físico ratificado, testes integrados, merge, produção, autorização de API paga, licença Meta/Banco ou auditoria completa das outras frentes.

## 1. Motivo, terminologia e método

A auditoria foi solicitada para assegurar que a **nossa frente OpenAI** conserva tudo o que é necessário para trabalhar em um objetivo compartilhado com S0, S1, frontend, Meta e MCP, **sem assumir a documentação nem alterar arquivos desses outros donos**. Foram conferidos:

- Registro recente de decisões `AL-IA-00..07` produzido a partir do alinhamento funcional do responsável;
- Contratos/planos legados próprios da OpenAI (notadamente OAI-01/05/07/08, E01, E02, CFI-01, mapa de capacidades e roteiro E00–E08);
- Dependências relevantes já lidas das branches PRs #1, #2, #5, #7, #8, #12 e da frente visual, citadas no `AL-IA-07`, **sem copiar todo seu conteúdo**;
- Complemento mais recente do responsável sobre a **Prumo providenciar e operar os números no ambiente Meta de cada concessionária**.

**Terminologia mandatória:** a solução em desenvolvimento chama-se **plataforma** (sem nome definitivo); **LiberaCred** é o produto da instituição financeira. Nomes de arquivos históricos podem conservar grafia antiga para rastreabilidade.

**Legendas:** [DN] decisão recente do responsável; [DA] decisão de outra frente/época compatível e relevante; [HS] histórico/superado; [P] proposta técnica; [R] detalhe/integração não ratificado; [V] homologação/condição externa. **Não equiparar** registro [DN] a endpoint funcional ou permissão implantada.

## 2. Achados desta auditoria e ações efetivas

| ID | Grau | Achado concreto | Tratamento na nossa branch |
|---|---|---|---|
| AF-01 | **Alto** | Contratos anteriores OAI-05, OAI-07 e OAI-01 ainda permitiam correção da ficha por Consultor, embora a regra recente a proíba. | **Aviso de precedência** em OAI-05, OAI-07 e OAI-01; AL-IA-01/04 continuam fonte funcional. Preservado corpo histórico para evitar falsificar aprovação retroativa. |
| AF-02 | **Alto** | OAI-05/OAI-07/E01/planos E02 ainda vedavam genericamente mudança comercial decorrente de F03, enquanto a diretriz nova permite transições **executadas pela S0**, com exceções. | Cabeçalhos de precedência adicionados e regra precisa corrigida no README. **F03 nunca grava diretamente; `vendido` segue exclusivamente humano com prova; negativa bancária formal também é ato humano comprovado.** |
| AF-03 | **Alto** | Versões anteriores do envelope F03 limitam snapshot ao caso; intenção nova é **histórico lógico integral do mesmo cliente na concessionária** até corte de cada conclusão humana, inclusive mídias permitidas. | Avisos de precedência em OAI-05, CFI-01, E01/E02; AL-IA-01/02/04/07 detalham finalidade, cutoff, proveniência e conflito de retenção. Requer contrato S0 novo [R]. |
| AF-04 | **Alto** | Metadados de conclusão S0 CFI-01 não equivalem à integração F03 pronta: `expected_cycle_version` não é automaticamente `expected_case_version`; catálogo/ficha/histórico/mídia não estão ratificados. | AL-IA-07 conserva distinção e exige ratificação entre frentes; não inferir contrato físico de laboratório. |
| AF-05 | **Alto** | Uma interpretação recente da DEC-WA-05 poderia esconder quem efetivamente **providencia/implanta/opera** canais Meta. | AL-IA-01/04/05/07 e README/índice já corrigidos: **Prumo configura e opera, com autorização, os números na estrutura Meta da concessionária**, isolados por App/WABA/emissor/credenciais/catálogo. Propriedade contratual/portabilidade [R/V]. |
| AF-06 | **Alto** | F02 estava descrita genericamente com “templates aprovados”, sem regras completas de finalidades internas, variáveis e invalidade Meta. | AL-IA-01 incorpora finalidades por uso, filtros da concessionária, mapeamento de variáveis congelado, preenchimento pela S0 no envio, replanejamento somente quando S0 chamar; AL-IA-07 guarda fontes e contexto. |
| AF-07 | **Alto** | Duas falhas Meta consecutivas apareciam inicialmente apenas como cancelamento; decisão da outra frente também exige **`perdido` técnico**. | Corrigido AL-IA-01/04/05/07: duas falhas definitivas da mesma cadeia, envio efetivamente comprovado zera contagem, resultado incerto não conta; o motor S0, **não a F02**, altera comercialmente. |
| AF-08 | **Médio** | A orientação “F03 devolve ao Gestor se Consultor indisponível” podia confundir `intake_paused` com indisponibilidade para casos já atribuídos. | AL-IA-01/07 distinguem pausa para novos leads da titularidade atual, acesso e distribuição S0/S1; F01 não recebe roster de equipe. |
| AF-09 | **Médio** | O README antigo ainda começava uma seção de normas de 18/10 como “vigentes” e dizia que “nenhuma saída da OpenAI modifica estado automaticamente” sem ressalva. | README atualizado com **contexto histórico**, precedência nova e diferença entre **saída do modelo** e **transição automática guardada pela S0**. |
| AF-10 | **Médio** | OAI-05/07/08, E01, E02 e outros contratos poderiam ser acessados por link direto, ignorando o índice novo. | Avisos visíveis no **topo** de dez contratos/planos legados da própria frente, todos apontando aos alinhamentos AL-IA e a este relatório. Não reescrever a norma histórica como se tivesse sido originada em 22/10. |
| AF-11 | **Médio** | O índice mestre encerrava sua ordem de leitura em AL-IA-06; AL-IA-07 e a auditoria atual poderiam ficar invisíveis. | AL-IA-00/README passam a indexar **AL-IA-00..08**, com ordem e papel de cada arquivo. |
| AF-12 | **Médio** | A diferença entre opt-out por concessionária e reentrada espontânea poderia ser interpretada como autorização de disparo. | Incluída em AL-IA-01 e mantida em AL-IA-07; reentrada inbound não reativa opt-in sem base válida. Autoria humana visível não é “comportamento F01”. |

## 3. Checklist de cobertura funcional após o saneamento

| Domínio | Decisão relevante | Fonte atual nesta frente |
|---|---|---|
| Papéis e isolamento | Diretor/Gestor/Consultor; sem cruzar cliente, canal, ficha, vetor ou histórico entre lojas | AL-IA-01, 03, 04, 07 |
| F01 — missão e estilo | Instruções globais F01 + comportamento global F01; nenhum perfil específico por loja | AL-IA-01, 02 |
| F02 — função | Somente instruções globais F02, sem comportamento; elegibilidade de templates e planos sob S0/Meta | AL-IA-01, 02, 07 |
| F03 — função | Somente instruções globais F03, sem comportamento; silêncio diante do cliente e análise após clique humano | AL-IA-01, 02 |
| Entrada e handoff | Não iniciar atendimento ativo por envio inicial sem resposta; F01 silenciada após handoff; retorno pós-venda/remessa sempre humano na mesma loja | AL-IA-01, 05 |
| Equipe humana | F01 sem acesso a equipe/disponibilidade; S0/S1 gerencia casos e filas; pausa de intake não é indisponibilidade total | AL-IA-01, 07 |
| Histórico F03 | Histórico lógico integral da mesma pessoa **naquela loja**, todas as conversas autorizadas, cutoff de cada conclusão e tratamento multimodal sujeito a políticas | AL-IA-01, 02, 04, 07 |
| Ficha | Ficha cadastral evolutiva única por cliente/loja, snapshots históricos comerciais preservados; Consultor não edita; F03 propõe/aplica via S0 permitida | AL-IA-01, 04 |
| Desfecho | F03 interpreta desistência e pode ensejar `perdido` guardado; `vendido` é humano/prova; banco enviado é real/provado | AL-IA-01, 04 |
| F02 — cadência | Templates finalidades/versões elegíveis, horários/intervalos, regras do template final, prova de envio e dois relógios distintos | AL-IA-01, 05, 07 |
| F02 — erro | Duas falhas definitivas consecutivas de envio → S0 cancela plano e marca perda técnica; status incerto não conta | AL-IA-01, 04, 05, 07 |
| Canal Meta | Prumo fornece/configura/opera com autorização na BM/App/WABA/número da concessionária; credenciais separadas por loja | AL-IA-01, 04, 05, 07 |
| Conhecimento | Gatilho semântico + fato canônico + metadados; instituição/lojas separadas; cadastro apenas Prumo | AL-IA-02 |
| Bases extras e vigência | Criar bases adicionais isoladas por loja, pausar/reativar, contexto original consultável na pausa, agendamento opcional de data/hora e cautela com oferta vencida | AL-IA-02 |
| Histórico, cache, internet | Histórico consultável como contexto; prompt caching opcional, sem compartilhar clientes; internet aberta não é padrão | AL-IA-02 |
| Habilidades | Conhecimento vinculado; F01/F02/F03 não criam; Diretor/MCP só configura capacidade executável preexistente | AL-IA-02, 03 |
| MCP Diretor | Guias internos semânticos separados dos prompts das IAs; operações administrativas confirmadas e auditadas; registros próprios do MCP não editáveis/excluíveis por MCP | AL-IA-03 |
| instituição financeira | LiberaCred é produto bancário; envio direto futuro condicionado, fallback humano; não investigar agora | AL-IA-00, 01, 04 |
| Arquitetura técnica | S0 autoriza e persiste, OpenAI propõe, Meta transporta, S1 atribui; n8n opcional/indefinido | AL-IA-01, 02, 03, 07 |
| Histórico de decisões | Não reativar IA Analista antiga nem concessões históricas substituídas | AL-IA-04, 05, 06 |

## 4. Conflitos intencionalmente NÃO “resolvidos” por esta frente

**[R/V] Nenhum exige repetição das regras já decididas pelo responsável.** São gates das frentes técnicas/provedores:

1. **S0↔OpenAI F03:** contrato de seleção de histórico por pessoa/loja, cutoffs múltiplos, versão do caso/ciclo/ficha, catálogo de campos, autorização de classes D2–D4, aplicação idempotente concorrente, histórico multimodal e retenção de mídia bruta versus recuperação autorizada.
2. **S0/S1/Frontend:** remessa humana/bancária comprovada, proibição de edição de ficha pelo Consultor nos contratos antigos, retirada de status vetados e atualização segura da ficha viva; retorno F03→Consultor/Gestor sem conceder acesso a equipe à F01.
3. **Meta e núcleo:** situação jurídica de número/portabilidade, processos de onboarding, direitos por App/WABA, status/revisão de template, finalidade elegível, opt-out por loja, fonte de variáveis, perda técnica e assinatura humana.
4. **Identidade cadastral:** vários telefones por cliente versus chave anterior por telefone dentro da concessionária; prova e prevenção contra fraude/reciclagem.
5. **MCP:** autenticação e confirmação vinculada à pessoa, limites reais de escrita, retenção legal, separação da auditoria protegida e catálogo de ferramentas/skills sem criar código.
6. **instituição financeira:** envio direto e eventuais confirmações dependem de prova externa, consulta e homologação **deliberadamente adiadas**.
7. **OpenAI/arquitetura:** escolha de modelo, custo, provedor de embeddings/vector store, cache e retenção, estrutura de habilidades, desenho RAG, endpoint e relação direta/n8n; não foram implantados.
8. **Prova operacional:** PR #3 continua Draft, sem demonstrar chamadas reais pagas, dados de clientes, implantação do adaptador ou testes E04/E05.

## 5. Precedência operacional para quem trabalhar depois

**Sempre iniciar por `README.md` → `AL-IA-00` → `AL-IA-01/02/03` → `AL-IA-04/07` → este `AL-IA-08`.** O `AL-IA-05` guarda hipóteses históricas; `AL-IA-06` guarda a primeira auditoria de 22/10, **anterior aos refinamentos interfrentes e a esta auditoria**. Os contratos OAI-01/05/07/08, E01, E02 e a proposta CFI-01 só podem orientar implementação **depois de corrigidos/ratificados** contra decisões novas. Avisos no topo apontam a esta cadeia.

**Não transferir as decisões da frente OpenAI como alterações automáticas à S0/Meta/S1/Frontend.** As decisões do responsável estão registradas como intenção de produto; os donos dos domínios técnicos ainda decidem, com o responsável quando necessário, como e quando conciliar suas implementações. Apenas nossa documentação foi alterada.

## 6. Limites deste veredito

A auditoria cobre **consistência interna e fidelidade às decisões mais recentes recuperadas**, com contraste temático em documentos das outras frentes. A validação de existência e links dos arquivos deve ser feita no fechamento do PR. Não substitui revisão humana integral das 55 fontes históricas, estudo de legislação Meta/Banco/LGPD, verificação de todos os contratos externos, testes de execução, aprovação do usuário de detalhes técnicos ainda [R/P] ou auditoria de repositório completo.

**Conclusão documental:** nenhum bloqueio conceitual remanescente obriga o responsável a repetir as decisões expressamente registradas. O futuro desenvolvimento da **plataforma** pode prosseguir por frentes, **desde que cada uma preserve sua autoridade e reconcilie as interfaces sinalizadas**. Este documento não anuncia autorização de implementação ou homologação.
