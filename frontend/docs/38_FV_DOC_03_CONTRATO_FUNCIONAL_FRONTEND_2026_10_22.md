# FV-DOC-03 — Contrato funcional vigente da frente Frontend: plataforma Prumo
**Data de revisão:** 22/10/2026. **Natureza:** consolidação [D] de decisões expressas do responsável e leitura controlada das frentes OpenAI, WhatsApp/Meta, S1 e coordenação S0; **não** aprovação de APIs/SQL/RLS, implementação, design definitivo, teste ou operação real. **Escopo de escrita:** exclusivamente `frontend/docs/` na branch `feat/frontend-plataforma-visual`.

## 0. Glossário, autoridades e fontes de verdade
- **Plataforma**: sistema operacional da Prumo em desenvolvimento, **sem nome próprio definido**. Nunca tratá-lo como se seu nome fosse LiberaCred.
- **LiberaCred**: **produto financeiro da instituição financeira**, apresentado/comercializado por intermédio da operação e das concessionárias; não é o nome da plataforma.
- **Prumo**: operação que desenvolve/administra a plataforma para uso autorizado por concessionárias. O vínculo organizacional dos profissionais humanos é com a Prumo.
- **Diretor** = papel anteriormente chamado responsável da plataforma; **Gestor** permanece; **Consultor** = operador humano anterior. Não renomear literalmente nomes SQL/APIs/status/títulos históricos sem migração.
- **F01**: IA de atendimento/vendedora; **F02**: IA planejadora de recontatos e templates; **F03**: IA extratora/classificadora silenciosa **após conclusão expressa** do atendimento humano. Os nomes técnicos F01/02/03 pertencem à frente OpenAI.
- **[D]** decisão expressa do responsável; **[E]** fonte externa à nossa frente cuja regra funcional foi documentada, a integrar sem alegar homologação; **[R]** diferença ou contrato não ratificado; **[P]** apresentação/contrato candidato; **[V]** dependência externa; **[H]** histórico superado quanto à matéria identificada.
- Nas operações e na UI, **S0/S1** autenticam, autorizam e persistem; **Meta** transporta/prova mensagens; **OpenAI** propõe conteúdo/extrai dados; o **Frontend** exibe projeções autorizadas e solicita operações. **Um texto de interface, prompt, cache ou modelo nunca concede acesso**.
- Precedência **restrita ao Frontend**: este documento prevalece para os tópicos de identidade da plataforma, ficha sem edição, apresentação da conclusão, autoria WhatsApp e dependências atualizadas sobre FV-01/02, o mapa O1–O5, relatórios históricos e quaisquer descrições anteriores incompatíveis. D-AL-01..10 e D-NOM-01 continuam fontes para equipes/distribuição/papéis, exceto se aqui houver refinamento expresso. **Não se declara alteração de contrato de outra branch.**

## 1. Identidade da plataforma e representação de concessionárias [D/E]
1. Usar “**plataforma**” ou “**plataforma da Prumo**” em documentos novos e textos de contexto. Usar **LiberaCred somente ao se referir ao produto da instituição financeira**. Nome comercial da plataforma: **em aberto**. Títulos de arquivos históricos e URLs existentes não precisam ser renomeados.
2. **Isolamento absoluto por concessionária**: cliente com mesmo telefone/CPF em duas lojas não dá visibilidade cruzada de ficha, chat, histórico, conhecimento, existência de outro registro, campanha ou mídia. O Frontend nunca amplia dados recebidos pela projeção S0.
3. **Meta externo x operação interna**: contas/BM, App, WABA e número vinculados **formalmente à estrutura da concessionária** no arranjo Meta previsto; a **Prumo providencia/configura/administra a operação por autorização/delegação** e utiliza o canal na plataforma. “Número nosso” descreve gestão/uso operacional da Prumo, **não transferência de titularidade formal** sem contrato/prova. Exibir a concessionária, canal correto e autores efetivos; não inferir propriedade legal, concessão global ou canal de outra loja.
4. Autorizações, opt-in/out e elegibilidade independentes por concessionária. Um opt-out em A não contamina B, nem inbound espontâneo significa novo opt-in. Sem homologação Meta/LGPD real [V].

## 2. Pessoas, papéis e direitos na experiência [D/E]
- Rótulos de UI futuros: **Diretor / Gestor / Consultor**; não criar novos papéis ao ler `operador`/`responsavel` antigos. Os oito status comerciais persistidos mantêm sua grafia canônica, inclusive `em atendimento pelo operador` e `cadastro enviado ao operador`; a tradução visível a “consultor” é camada de apresentação e requer acordo de contrato [R], **não migration**.
- **Diretor** pode realizar as ações da alçada administrativa previamente aprovada; MCP administrativo, quando implementado pela frente responsável, possui autorização, prévia, confirmação específica e trilha; o Frontend não imita nem executa operações administrativas apenas porque possui botões.
- **Gestor** supervisiona sua equipe, atua como atendente somente com atribuição válida, pode pausar a entrada de novos leads de Consultor **sem bloquear conta** e pode assumir a fila compartilhada das concessionárias às quais esteja autorizado.
- **Consultor** atua somente nos seus casos e escopos concedidos. Em caso de concessão excepcional por caso, a UI deve restringir todo conteúdo àquele caso; não mostrar ficha, conversas ou arquivos de outros casos da mesma concessionária.
- A matriz D2/D3/D4/arquivos não pode ser substituída por filtros visuais; a autorização é responsabilidade S0/S1.

## 3. Ficha cadastral: visualização e nenhuma edição pelo Consultor [D]
**Regra posterior expressa: o Consultor NÃO modifica manualmente NENHUM campo cadastral, nem em fluxo habitual nem como “correção excepcional”.** Qualquer texto antigo em FV-01/FV-02/CFI-01 e docs.23/C13/D41-04 que permita um botão/formulário de correção individual pelo Consultor é **histórico/superado para esta interface**, aguardando conciliação pela frente normativa sem que a UI exponha a ação.

**Percurso atual para UI:**
1. Durante o atendimento automatizado, **F01** pode captar/propor atualização de dados conforme as permissões e validações técnicas do S0. A interface não pressupõe escrita direta pela IA no banco.
2. Após o atendimento humano, o **Consultor autenticado e atribuído pressiona explicitamente “Concluir atendimento”**. O S0 confirma o evento e o recorte da conversa; somente então desencadeia processamento de **F03**, segundo o contrato de integração a ratificar. **F02 é Planejadora, não extratora** nos contratos vigentes OpenAI. A fala recente do responsável citou “F02” após o encerramento embora também tenha nomeado “F03”; por fidelidade, **registrar a divergência de sigla [R-SIGLA-01]**, **não** renomear a F02 nem executar nova atribuição. O comportamento seguro e já consolidado para o Frontend é **clique explícito → solicitação S0 → resultado validado de extração**, sem escolher implementação por si.
3. **Somente S0** valida/aplica campos propostos pelo serviço autorizado e apresenta ficha persistida com proveniência/versão; o Frontend mostra informação efetivamente confirmada, nunca valor provisório como definitivo.
4. A ficha é **contínua por cliente e por concessionária** ao longo das conversas/negociações; resultados, remessas bancárias e documentos históricos preservam snapshots próprios. Nova análise pode atualizar ficha viva sem reescrever remessa antiga.
5. Tela O3: **somente leitura** para o Consultor, com dados confirmados, lacunas essenciais/opcionais, conflitos, origem/versão e estados técnicos de processamento. **Não apresentar** lápis, campos editáveis, “corrigir dado”, formulário C13, permissão oculta ou resposta de gravação humana.
6. Lacunas/contradições são comunicadas ao **Consultor original**, para esclarecimento com o cliente; se indisponível, ao **Gestor** autorizado para decisão. Não corrigir manualmente nem iniciar recontato F02 automaticamente só porque falta um campo.
7. Capacidade administrativa excepcional **separada** pelo MCP do Diretor poderá alterar dados operacionais nos limites que forem implementados/autorizados. Isso **não** cria edição pelo Consultor, não equivale ao fluxo da tela O3 e não modifica registros protegidos do próprio MCP.
8. Novo encerramento humano pode gerar nova execução da extração, com **cutoff** imutável por evento, incluindo última mensagem existente naquele instante e nunca mensagens futuras. A F03 consulta o **histórico lógico autorizado da mesma loja**, inclusive outras conversas/autores e mídias quando viabilizado; **não** presumir retenção permanente de mídia bruta ou autorização de leitura fora do escopo [R/V].
9. A intenção de vários telefones por ficha na **mesma loja** depende de reconciliação de identidade com chave comercial anterior e verificação contra fraude [R]; **não fixar UI com suposição eterna de único número nem criar edição/vinculação livre pelo Consultor**.
10. **Falha F03 recorrente** é incidente técnico, não justificativa para implantar campo manual improvisado. UI mostra indisponibilidade/reprocessamento somente conforme S0; não declara gravação sem confirmação.

## 4. Conclusão humana, janela WhatsApp e status [D/E]
- **Clique explícito de conclusão** é diferente de janela Meta vencida, silêncio, pausa, leitura, transferência de titular, envio de template, remessa e venda. Nada disso substitui o clique nem dispara F03 por inferência. “Conclusão solicitada” ≠ “extração concluída” ≠ “ficha persistida”.
- Janela WhatsApp de mensagens livres: **24h desde a última mensagem recebida do cliente**, projeção S0; mensagem outbound/template não reabre janela livre. Fora dela, o Consultor ainda conserva o caso não concluído conforme atribuição, porém o composer livre deve ficar indisponível e opções elegíveis de **template aprovado** podem aparecer.
- Após concluir, conservar histórico; não inventar que 24h encerra automaticamente titularidade, apaga conversa ou libera outro Consultor. A permanência exata em “janela ativa” após conclusão e expiração exige conciliação entre CF-OP-02 histórico e orientação OpenAI mais recente [R-RETENCAO-01].
- Se após análise F03 o S0 **autorizar uma transição comercial** prevista (ex.: `perdido` por desistência com razão e evidência), o Frontend pode **exibir apenas estado confirmado pelo S0**. A autorização de transições automáticas F03 ainda [R] perante contratos antigos; **clique isolado não muda status**.
- `vendido` continua ato humano autorizado com evidência real do Banco; `cadastro enviado ao banco` somente após **remessa real confirmada**. Negativa bancária comprovada não equivale à desistência; F03 não inventa ato bancário.
- Retorno após `vendido` ou `cadastro enviado ao banco` é **humano**, sem reativar F01, preservando histórico. Em `perdido`, eventual novo ciclo depende de elegibilidade S0, não de clique da UI.
- Identificadores candidatos de contrato FV/S0 (versão de **caso** vs versão física do **ciclo**, hashes/watermark/catálogo) **não são intercambiáveis**. A UI só envia campos e versões aceitos por contrato final; S0 define ator, escopo, cutoff e prova; sem afirmar que PR #12 seja integração operacional já pronta.

## 5. Mensagens: autoria, prévia, sinalização e transporte [D/E]
- Para **cada mensagem textual livre enviada por humano** com cargo Consultor, Gestor ou Diretor, o **texto final visto pelo cliente** deve conter automaticamente o cabeçalho autorizado `Consultor Nome:\nMensagem`, `Gestor Nome:\nMensagem` ou `Diretor Nome:\nMensagem`, com nome do **autor real autenticado**. Não pedir que profissional digite o cabeçalho; nunca usar esse padrão em mensagem originada exclusivamente pela IA.
- A plataforma/S0, não o browser nem o modelo, compõe/valida a autoria e o corpo final de modo idempotente. **Prévia do Frontend** deve refletir o texto final **quando confirmado/projetado pelo serviço**, ou identificar claramente como simulação/candidato [P] na ausência de retorno real; não declarar assinatura enviada antes da confirmação Meta. Manter autoria histórica mesmo quando profissional/cargo mudam.
- **Templates aprovados da Meta** não podem receber prefixo livre arbitrário; somente conteúdo e variáveis previamente aprovados e validados pela integração. Mídia/legendas/áudio exigem política própria [R].
- Emissão WhatsApp com ACK/API aceita não é necessariamente envio efetivo, entregue ou lido. UI distingue `solicitado` / `incerto` / `enviado comprovado` / `entregue` / `lido` / `falhou` conforme projeções confiáveis, **sem criar novos status comerciais**.
- A **bolinha única de atenção da conversa** é distinta dos recibos Meta: `COUNT(n)` para mensagens de cliente não lidas pelo titular; `DOT` sem número para lidas ainda sem resposta humana; `NONE` após resposta humana confirmada sem nova pendência. Gestor como supervisor não zera leitura do Consultor; Gestor titular pode registrar sua própria leitura. Cores ficam para design. Herança de não lidas após troca de titular ainda é [R-LEITURA-01] da S1, **não uma decisão aprovada**.
- Template tem **categoria oficial Meta**, **finalidade interna configurável** e **finalidade/consentimento de contato** separados. S0/Meta fornecem apenas opções elegíveis ao caso/loja/horário/campanha. Editor não improvisa template ou valores faltantes; preenchimento das variáveis é de serviço autorizado, não da IA ou da UI.
- Falhas de template definitivas **consecutivas e comprovadas** podem afetar cadência e status pela regra S0, mas timeout/ACK incerto não são falha definitiva. A UI apenas exibe cancelamento e resultado efetivamente confirmados, inclusive motivo de `perdido` técnico quando autorizado.

## 6. Pausa, distribuição, fila e IA sem contexto operacional [D]
**Conservar [FV-DOC-01 D-AL-01..09](./35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md)**:
- Gestor pausa **apenas entrada de novos leads** de Consultor da sua equipe; conta, casos retidos e grants permanecem.
- Redistribuir automaticamente **caso existente** do pausado, sem prova de primeiro contato e com evidência explícita, **somente para outro Consultor da mesma equipe** com grant à loja; sem receptor ou prova desconhecida, permanece com titular original.
- **Lead novo** pode ir a Consultor elegível de **outra equipe**, desde que tenha grant à concessionária. Sem destinatário: **fila sem titular compartilhada por gestores autorizados àquela concessionária**, com assunção manual atômica. Gestor não recebe automaticamente.
- Retomada/volta de elegível: pendentes **sem titular** retornam à distribuição automática; não retirar atendimentos já assumidos.
- Transferência manual dentro da equipe pode gerar autorização **apenas para o caso**, inclusive quando destinatário não tem grant geral de loja, depois de confirmação S0/S1. Nenhuma tela pode conceder acesso real.
- UI distingue **pausa aplicada** de **redistribuição ainda pendente**; o experimento S1 `DEFERRED_S0_PROOF` não é confirmação de remanejamento. Estado real, versão, conflito e motivo vêm do backend.
- **F01** atende independentemente de haver Consultor disponível; não conhece identidade, quantidade, equipes, grants ou disponibilidade dos humanos. O núcleo operacional encaminha handoff e fila. F01 não retoma depois de handoff humano definitivo no caso.

## 7. Escopo da primeira versão e áreas de administração [D/E]
- **IA de melhoria/otimização do atendimento está FORA do escopo da primeira versão**, por confirmação expressa posterior. Não projetar painel, tarefa, menu, capacidade de alteração de parâmetros ou fluxo de administração desse componente na UI inicial. Não confundir F02 Planejadora, F03 Extratora ou MCP do Diretor com IA de melhoria.
- Bases de conhecimento: frente OpenAI documenta conteúdo institucional e específico por concessionária, bases adicionais com estados ativo/pausado e programação **opcional** de pausa por data/hora; vigência da campanha/conteúdo é independente da pausa da base. **Não criar telas administrativas automaticamente**: MCP do Diretor é o meio de administração documentado, e qualquer UI adicional carece de escopo/contrato próprio.
- Configuração das IAs: quatro campos **globais** identificados na frente OpenAI (F01 instruções/comportamento, F02 instruções, F03 instruções); **não inventar configurações por concessionária na UI**. Não traduzir texto de configuração em acesso estrutural.
- Fronteira MCP do Diretor: prévia e segunda confirmação específica para mutações, sem capacidade de editar código, regras fundamentais ou registros de auditoria protegidos pelo próprio MCP; a UI não deve sugerir que um comando administrativo já foi implementado.
- Evitar telas sobre chamadas WhatsApp como se fossem disponíveis. Ligação atendida via Meta somente é capacidade futura condicional a API/implementação/prova; sem registro manual de ligação como contato iniciado.

## 8. Matriz de verificação de Frontend (critérios para futura homologação; NÃO testes executados)
| ID | Cenário de UX / requisito verificável |
|---|---|
| FV-22-01 | Menus e documentação nova usam “plataforma”, não LiberaCred como marca da aplicação; produto bancário LiberaCred é nomeado apenas quando pertinente. |
| FV-22-02 | Rótulos humanos Diretor/Gestor/Consultor; status literais/identificadores antigos mantidos na integração até acordo S0/S1. |
| FV-22-03 | Consultor **não possui** ação/formulário de editar/corrigir ficha, inclusive exceção antiga; O3 só exibe campos autorizados/proveniência/pendências. |
| FV-22-04 | Clique de concluir válido sinaliza pedido/processamento; sem clique, janela vencida, pausa ou silêncio **não** dispara F03. |
| FV-22-05 | Duas conclusões legítimas produzem duas requisições/estados técnicos rastreáveis; cutoff de extração não inclui mensagens posteriores. |
| FV-22-06 | Lacuna da ficha retorna à conversa com Consultor original ou Gestor quando necessário, não habilita editor cadastral nem campanha F02 automática. |
| FV-22-07 | Ficha viva por loja e snapshots bancários/históricos não se confundem; outra concessionária permanece invisível. |
| FV-22-08 | Texto humano livre tem prévia com cargo+nome real; mudanças de titular, retry e template não duplicam/forjam assinatura. |
| FV-22-09 | Janela Meta fechada bloqueia mensagem livre mas conserva caso não concluído; template elegível é operação distinta. |
| FV-22-10 | Estado de envio técnico `API_ACCEPTED`/`UNCERTAIN` não vira `SENT`, resposta humana, venda ou remessa. |
| FV-22-11 | Contador único `COUNT/DOT/NONE`; leitura do gestor supervisor não zera leitura do titular; troca de titular tratada como [R] até aprovação. |
| FV-22-12 | G2 distingue `pausa aplicada` de `redistribuição pendente` e de `caso retido`; lead novo usa distribuição entre equipes. |
| FV-22-13 | Gestores autorizados à mesma loja compartilham fila sem titular com assunção única; retomada distribui pendentes ainda não assumidos. |
| FV-22-14 | Nenhum menu inicial para IA de melhoria; IA Vendedora não recebe informação de quadro de Consultores. |
| FV-22-15 | F03 pode resultar em status permitido apenas com confirmação S0; jamais marcar `vendido` automaticamente nem `cadastro enviado ao banco` sem remessa. |
| FV-22-16 | Sem editor de campanhas/bases/variáveis ou MCP executável por inferência; quando futuramente previsto, exibir permissões/versões/previews autorizados. |

## 9. Pendências reais para owner de integração (registrar, NÃO decidir pela UI)
- **[R-SIGLA-01]** O responsável nomeou F03 e F02 na mesma fala ao se referir à atualização pós-humana; contrato OpenAI vigente F01 atendimento/F02 planejamento/F03 extração. A interface fixa só **conclusão→S0→extração**, e o identificador físico será o pactuado; sem abrir edição humana.
- **[R-RETENCAO-01]** CF-OP-02 antigo prevê saída da lista ativa após conclusão e vencimento da janela; OpenAI recente destaca que janela não conclui, não apaga ou transfere caso. Não inferir prazo de desatribuição/histórico.
- **[R-LEITURA-01]** Contador no novo titular após transferência: modelo S1 reinicia não lidas como hipótese sintética, **sem aprovação de produto**.
- **[R-STATUS-01]** Transições `perdido` pela F03 e motivos dependem de contrato S0 ratificado; decisão OpenAI recente não modifica por si migrações anteriores.
- **[R-CFI-01]** Envelopes/versionamentos S0 física `expected_cycle_version` versus frontend `expected_case_version`, catálogo e cutoff. Não mapear por suposição.
- **[R-CAD-01]** Catálogo final de campos e proteção de mídias; ficha read-only visual detalhada não homologada, assim como múltiplos telefones por ficha.
- **[R-META-01]** Prova de propriedade/capacidade Meta e canal real, política de assinatura em mídias/templates, natureza documental vs operacional do controle Prumo.
- **[R-S1-01]** APIs autenticadas de redistribuição/fila/resumo, concessão excepcional por caso e política de herança de leitura; somente sandbox, não disponível para UI real.
- **[V-BANCO-01]** Remessa bancária direta, capacidades oficiais, LGPD e regras de comprovação dependem de verificação externa. A própria frente OpenAI registra que não é prioridade investigar a integração bancária agora.

## Fontes para consulta — **não** transplantar código ou regras por conta própria
**Nesta frente:** [Índice](./00_COMECE_POR_AQUI_DECISOES_VIGENTES_2026_10_21.md), [D-AL-01..10](./35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md), [D-NOM-01](./37_D_NOM_01_NOMENCLATURA_DIRETOR_GESTOR_CONSULTOR_2026_10_21.md), [FV-01](./04_CONTRATO_FV01_UI_BACKEND_v0_1.md), [FV-02](./05_CONTRATO_FV02_CONCLUSAO_EXTRAÇÃO_POS_HUMANA_v0_1.md), [FV-03](./09_CF_OP_02_CONTRATO_VISUAL_JANELA_CADEIAS_v0_1.md).

**Outras frentes, apenas leitura e rastreabilidade:**
- [OpenAI AL-IA-01 jornada F01/F02/F03](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s2-openai-adapter-sintetico/docs/integracoes/openai/ALINHAMENTO_2026_10_22_01_JORNADA_F01_F02_F03_v0_1.md), [AL-IA-02 conhecimento](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s2-openai-adapter-sintetico/docs/integracoes/openai/ALINHAMENTO_2026_10_22_02_CONHECIMENTO_CACHE_HABILIDADES_v0_1.md), [AL-IA-03 MCP Diretor](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s2-openai-adapter-sintetico/docs/integracoes/openai/ALINHAMENTO_2026_10_22_03_MCP_DIRETOR_GUIAS_AUDITORIA_v0_1.md).
- [Meta WA-21 assinatura](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/docs/integracoes/whatsapp-meta/wa21-papeis-diretor-gestor-consultor-assinatura-2026-10-21.md), [Meta 01 especificação](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/docs/integracoes/whatsapp-meta/01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md).
- [S1 I37 intake assinado (sandbox)](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s1-002-equipe-prumo/docs/S1_002_I37_GATEWAY_INTAKE_ASSINADO_2026_10_20.md), [S1 indicador sandbox](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s1-002-equipe-prumo/docs/S1_002_ISSUE10_INDICADOR_MENSAGENS_S0_2026_10_20.md).
- [S0/CFI-01 contrato de snapshots candidato](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-cfi01-f03-auth-preflight-20261020/docs/S0_CFI01_F03_SNAPSHOT_METADATA_RATIFICATION_GATE_2026_10_21.md).
**Nenhum destes links concede autoridade sobre aquela branch ou afirma contrato externo ratificado.**

## Gate e estado
Este documento **não** modifica aplicação, testes, migrações, banco hospedado, Meta, S1/S0, OpenAI ou MCP. Os últimos marcos visuais já conhecidos eram FV-UI-015/016 **sintéticos** e FV-UI-013 **não homologada formalmente**, 19F **69/100**; **não atualizar progresso por criar documentação**. A auditoria exclusivamente documental deste alinhamento está em [FV-DOC-04](./39_FV_DOC_04_AUDITORIA_DOCUMENTAL_FRONTEND_2026_10_22.md).
