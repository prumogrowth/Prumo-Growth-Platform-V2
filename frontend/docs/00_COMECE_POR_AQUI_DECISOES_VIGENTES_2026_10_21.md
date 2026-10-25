# COMECE AQUI — fontes vigentes do Frontend da plataforma Prumo
**Corte inicial:** 21/10/2026. **Última precedência:** 22/10/2026. **Função:** índice de consulta com **precedência**, não autorização para executar operações. Esta frente documenta produto e interface; a implementação real depende de S0/S1/Meta/OpenAI/Banco e aceite próprio.

## Precedência mais recente — plataforma sem nome e contrato visual (22/10/2026)

**[FV-DOC-03 — Contrato funcional vigente do Frontend](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md)**: fonte prioritária atual para **plataforma sem nome ≠ LiberaCred (produto da instituição financeira)**, ficha sem edição manual pelo Consultor, F01/F02/F03, handoff, autoria no WhatsApp, mensagens, fila e dependências de outras frentes. **[FV-DOC-04 — auditoria documental de 22/10](./39_FV_DOC_04_AUDITORIA_DOCUMENTAL_FRONTEND_2026_10_22.md)** registra o que foi verificado e o que ainda está pendente. Documentos anteriores continuam disponíveis para histórico, **não competem com a decisão posterior**.

## Alteração posterior de nomenclatura [D-NOM-01]

**[Papéis vigentes: Diretor / Gestor / Consultor](./37_D_NOM_01_NOMENCLATURA_DIRETOR_GESTOR_CONSULTOR_2026_10_21.md)** (21/10/2026) deve ser consultado **antes das demais referências**: **responsável da plataforma → Diretor**, **gestor → Gestor**, **operador → Consultor**, com as mesmas atribuições. O conteúdo anterior não é substituído quanto à lógica de negócios. Nomes técnicos legados permanecem até etapa específica de integração.

## Ordem recomendada de consulta
1. **[FV-DOC-01 — Decisões vigentes D-AL-01..10](./35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md)**: fonte prioritária para pausa, atendimento existente, transferência excepcional, contato humano comprovado, leads novos entre equipes, fila compartilhada de gestores, retomada, limites da IA Vendedora, badge único e Supabase.
2. **[FV-DOC-02 — Ambiguidades e precedência](./36_FV_DOC_02_AUDITORIA_AMBIGUIDADES_E_PRECEDENCIA_2026_10_21.md)**: riscos DOC-01..13, pontos históricos e escopos das frentes.
3. **[Escopo e fronteiras da frente visual](./01_ESCOPO_E_FRONTEIRAS.md)** + [Mapa de telas](./02_MAPA_DE_TELAS_E_JORNADAS.md): uso do frontend, somente após aplicar as decisões recentes.
4. **Contratos candidatos UI/Backend:** [FV-01](./04_CONTRATO_FV01_UI_BACKEND_v0_1.md), [FV-02](./05_CONTRATO_FV02_CONCLUSAO_EXTRAÇÃO_POS_HUMANA_v0_1.md), [leitura UQ](./30_FV_S0_UQ_CONTRATO_LEITURA_CANDIDATO_2026_10_20.md) e [resultado de comandos](./31_FV_S0_RESULTADO_COMANDOS_E_DIVERGENCIA_S1_2026_10_20.md). **Propostas**, não APIs reais confirmadas.
5. **Histórico das decisões e entregas visuais:** [FV-G2-01/21](./21_FV_G2_01_GESTAO_POR_OPERADORES_E_PAUSA_GLOBAL_2026_10_19.md), [FV-UI-014/32](./32_FV_UI_014_INDICADOR_UNICO_E_PAUSA_SELETIVA_2026_10_20.md), [FV-UI-015/33](./33_FV_UI_015_INDICADOR_OPERACIONAL_E_CONFIRMACAO_2026_10_20.md) e [FV-UI-016/34](./34_FV_UI_016_MARCO_PREVIA_G2_2026_10_20.md). Não extrair decisões atuais de descrições antigas sem o índice 1.
6. **Fundação S0:** [S0-043](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-fundacao-prumo/docs/S0_043_PAUSA_SELETIVA_E_INDICADOR_CONVERSA_2026_10_20.md) e [decisões/gates S0](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-fundacao-prumo/docs/DECISOES_E_GATES.md); documentação da própria branch é referência para **capacidade operacional real** somente quando existir implementação e validação. A S1 é proprietária dos comandos transacionais e exceptions por caso.
7. **Projeto original:** pacote documental de **17/10/2026** com índice mestre 00A; decisões D41 e 13A, normas de cadastro/banco/Meta, contratos LGPD e testes. **Fonte histórica e complementar**; pontos expressamente retificados (ex.: Meta DEC-WA-05) não devem ser revividos pelo texto antigo.

## Regras rápidas para evitar interpretações erradas
- **Novo lead sem operador:** fila sem titular acessível aos gestores autorizados à loja; a IA comercial continua atendendo sua etapa; gestores não recebem automaticamente.
- **Caso atribuído a operador pausado:** se não existir substituto na **mesma equipe** com grant, continua atribuído ao operador. Não enviar esse caso à fila de novos leads.
- **Novo lead com operadores em equipes diversas:** distribuição regular pode cruzar equipes, respeitando concessão à loja.
- **Volta de operador:** distribui pendentes SEM titular automaticamente; não retira caso já assumido.
- **Gestor:** gerencia sua equipe; só visualiza fila compartilhada de concessionária autorizada; pode operar um caso se titular; não administra grants ou contas.
- **IA:** atende o cliente e não recebe conhecimento da disponibilidade ou identidade de operadores. Roteamento pertence ao núcleo.
- **Meta:** titularidade por concessionária conforme DEC-WA-05 registrada na S0, ainda dependente de homologação externa.
- **Tecnologia:** Supabase; Firebase foi erro de transcrição.

## Auditoria da implementação (22/10/2026)

**[FV-AUD-01 — auditoria estática da implementação](./40_FV_AUD_01_AUDITORIA_ESTATICA_IMPLEMENTACAO_2026_10_22.md)**: leitura do código atual, fixtures, testes e lacunas perante FV-22-01..16, com gravidade, evidências, prioridades e bloqueios. **Não substitui** FV-DOC-03 nem equivale a testes Node/Chromium executados, integração ou homologação. Consultar após o contrato funcional para orientar os reparos sem promover hipóteses históricas a regras vigentes.

## Primeiro reparo visual (22/10/2026)

**[FV-UI-017 — integridade de contexto e mensagens](./41_FV_UI_017_INTEGRIDADE_CONTEXTO_MENSAGENS_2026_10_22.md)**: rótulos humanos vigentes, descarte de rascunhos em trocas de contexto, prévia sintética de autoria, confirmação **apenas local** sem falso envio WhatsApp e regressões V8. **Não** é integração/aceite Node/Chromium; os demais achados da FV-AUD-01 continuam registrados.

## Reparação de distribuição e permissões (22/10/2026)

**[FV-UI-018 — fila compartilhada e acesso por caso](./42_FV_UI_018_PERMISSOES_DISTRIBUICAO_2026_10_22.md)**: demonstração visual de fila nova sem titular por concessionária, intents de assunção/atribuição sem efeito e caso excepcional sem grant geral. Inclui testes sintéticos e explicita dependências atômicas S0/S1. **Não** é autorização produtiva nem homologação de integração.

## Conclusões sucessivas, F03 e ficha viva (22/10/2026)

**[FV-UI-019 — eventos de conclusão, esclarecimento e versões da ficha](./43_FV_UI_019_CONCLUSOES_F03_FICHA_VIVA_2026_10_22.md)**: duas conclusões históricas F03 projetadas em fixture, nova conclusão somente candidata em cenário alternativo, dossiê vivo por cliente/loja e snapshot bancário antigo preservado. **Sem** execução real F03, S0, remessa, gravação ou homologação Node/Chromium.

## Estados técnicos e gates de aceitação (22/10/2026)

**[FV-UI-020 — erros, transporte de mensagens e matriz FV-22](./44_FV_UI_020_ERROS_TRANSPORTE_E_MATRIZ_ACEITACAO_2026_10_22.md)**: estados técnicos explicitamente **sintéticos**, rejeição de C13 na camada visual, 16 critérios rastreados a 24 suítes e bloqueios de integração. Não constitui homologação Node/Chromium, Meta ou S0/S1.

## Preparação de contratos e acessibilidade (22/10/2026)

**[FV-UI-021 — gate candidato S0/S1 e navegação acessível](./45_FV_UI_021_PREPARACAO_S0_S1_ACESSIBILIDADE_2026_10_22.md)**: classificação conservadora de envelopes sem liberar dados ou efeitos; anúncios de contexto, foco móvel, teclado Home/End e testes sintéticos. Não é conexão S0, prova de acesso nem homologação em Chromium.

## Robustez de Escape, rascunho e smoke Chromium (22/10/2026)

**[FV-UI-022 — navegação móvel e atualização do smoke](./46_FV_UI_022_ESCAPE_RASCUNHO_SMOKE_REGRESSAO_2026_10_22.md)**: foco devolvido ao painel visível no Escape, rascunho cancelado mantido somente no contexto original, mock de input corrigido e expectativa de supervisão atualizada para incluir A-117. Execuções V8 concluídas; **Chromium/Node nativos continuam não homologados**.

## Preparação de execução nativa sem clone (22/10/2026)

**[FV-UI-023 — verificação de ZIP da branch](./47_FV_UI_023_MANIFESTO_ZIP_OFFLINE_NATIVO_2026_10_22.md)**: inventário de fontes do Frontend pinado por hashes Git, verificador Python fail-closed e teste Node de integridade do manifesto. Permite executar **diagnóstico** nativo sobre ZIP exportado do GitHub, após conferência integral dos bytes; **não representa** homologação FV-UI-013, CI de produção ou conexão de sistemas.

## Regressão adversarial do ZIP privado (22/10/2026)

**[FV-UI-024 — testes Python e gates nativos obrigatórios](./48_FV_UI_024_TESTES_ADVERSARIAIS_ZIP_E_GATE_NATIVO_2026_10_22.md)**: 15 cenários sintéticos para ataques/alterações de ZIP, limite agregado de descompressão e exigência da suíte de segurança tanto no checkout Git quanto no diagnóstico offline, além de Node e Chromium. Não é prova de execução nativa nem homologação.

## Gates sequenciais da validação nativa (22/10/2026)

**[FV-UI-025 — segurança Python → Node → Chromium](./49_FV_UI_025_GATES_SEQUENCIAIS_VALIDACAO_2026_10_22.md)**: corrige execução de testes posteriores após falha do verificador, impede Chromium com Node reprovado e inibe arquivos `__pycache__` no checkout, com regressões específicas. Execução integral real **permanece pendente** de ZIP/checkout autorizado.

## Execução nativa do Frontend em ZIP verificado (22/10/2026)

**[FV-UI-026 — Python, Node e Chromium em ambiente nativo](./50_FV_UI_026_EXECUCAO_NATIVA_DIAGNOSTICO_2026_10_22.md)**: ZIP do commit `83d5f4df` com 54/54 hashes corretos; Python 20/20; Node 316/317 identificou regex defeituosa da matriz; smoke Chromium após correção local revelou teste de foco prematuro. Após corrigir os dois testes e repinar o manifesto em **ZIP derivado local**, diagnóstico nativo 20/20 Python, 317/317 Node e smoke Chromium completo. Continua **sem homologação de checkout Git, serviços externos ou produção**.

## Reflow de interface e movimento reduzido (23/10/2026)

**[FV-UI-027 — janelas baixas, rolagem e Chromium](./51_FV_UI_027_REFLOW_REDUCED_MOTION_CROMIUM_2026_10_23.md)**: correção de lista inacessível a 360×500 CSS px; teste de reflow em 720/360/320 px, foco após navegação e preferência por movimento reduzido. **Cópia local derivada:** 20/20 Python, 318/318 Node e Chromium PASS, com ZIP íntegro. **Sem homologação Git ou de integrações reais.**

## Semântica móvel e foco por teclado (23/10/2026)

**[FV-UI-028 — aria-expanded e foco visível](./52_FV_UI_028_ARIA_EXPANDED_FOCO_TECLADO_2026_10_23.md)**: corrigido `aria-expanded` incorreto ao abrir detalhes na viewport móvel e reforçado o contraste do foco nas superfícies claras. Em cópia local derivada: **20/20 Python, 320/320 Node, Chromium PASS** (390 e 320 px, Escape e Tab). Sem homologação de checkout Git ou de integrações produtivas.

## Foco e anúncio em confirmações fictícias de equipe (23/10/2026)

**[FV-UI-029 — retorno do foco em modais aninhados](./53_FV_UI_029_RETORNO_FOCO_MODAIS_ANINHADOS_2026_10_23.md)**: corrigido o foco perdido após confirmar pausa de novos leads e intenção na fila compartilhada, sem alterar permissões. Diagnóstico de **cópia ZIP derivada**: **20/20 Python, 323/323 Node e Chromium PASS** (390px e 1366px). Ainda sem homologação de checkout Git ou de integrações reais.

## Preparação para o redesign (23/10/2026)

**[FV-UI-030 — testes por camadas para não repetir validações desnecessárias](./54_FV_UI_030_TESTES_POR_CAMADA_PREPARACAO_REDESIGN_2026_10_23.md)**: inventário separado em **19 suítes de regras, 3 de interação, 5 de contratos/integridade** e roteiro Chromium isolado. Novo executor diagnóstico `run_validation_layers.mjs` facilita evoluir o layout sem confundir testes funcionais com visuais. Sem revisão do visual escolhido, homologação ou integrações reais.

## Foco após notas fictícias (23/10/2026)

**[FV-UI-031 — retorno ao editor de nota recriado](./55_FV_UI_031_FOCO_APOS_NOTA_LOCAL_2026_10_23.md)**: mantém navegação por teclado depois de registro local de nota, com regressões em DOM sintético, smoke Chromium e inspeção estrutural registrados para futura execução. Sem execução nativa/homologação desta revisão; manifesto repinado após arquivos visuais.

## Restauração de foco em extração e O5 (23/10/2026)

**[FV-UI-032 — foco após re-render na extração e transição O5](./56_FV_UI_032_FOCO_EXTRACAO_NAVEGACAO_O5_2026_10_23.md)**: ancora foco na aba Extração após resultado fictício e esclarecimento e conduz o teclado à conversa vinculada em desktop/celular. Cobertura sintética e verificações Chromium adicionadas, ainda sem homologação de checkout ou sistemas reais.

## Execução nativa sobre ZIP integral do FV-UI-032 (23/10/2026)

**[FV-UI-032 — evidência de Python, Node e Chromium em ZIP verificado](./57_FV_UI_032_VALIDACAO_NATIVA_ZIP_2026_10_23.md)**: 57/57 hashes, **20/20 Python**, **334/334 Node** e **Chromium PASS** no snapshot do commit `138bf641`. **Não** é homologação de checkout Git, de sistemas externos ou produto.

## FV-UI-033 — foco preservado sob reflow (23/10/2026)

**[FV-UI-033 — transição de breakpoint com foco e painel consistentes](./58_FV_UI_033_REFLOW_FOCO_BREAKPOINT_2026_10_23.md)**: corrige a perda de foco reproduzida ao encolher desktop→móvel com aba Detalhes selecionada e evita que ela desapareça no caminho inverso. Roteiro Chromium inclui 1440→360→1440, 320→1440 e navegação Home/End. Escopo visual fictício, sem homologação S0/S1, redes ou checkout.

## FV-UI-033 — diagnóstico nativo concluído em snapshot derivado (23/10/2026)

**[Resultado nativo FV-UI-033](./59_FV_UI_033_GATE_NATIVO_SNAPSHOT_2026_10_23.md)**: 57/57 hashes, Python **20/20**, Node **335/335** e Chromium **PASS** após correções de reflow; commit técnico `ebd7f60`. **Sem** checkout Git autenticado, zoom manual, leitores de tela reais ou homologação S0/S1.

## FV-UI-034 — foco no fechamento do painel tablet (23/10/2026)

**[FV-UI-034 — Escape e Fechar devolvem foco à abertura de Detalhes](./60_FV_UI_034_FOCO_FECHAR_DETALHES_TABLET_2026_10_23.md)**: corrige controles ocultos ainda focados ao fechar a lateral de 761–1040px; teste de Escape em painel versus campo de nota, proteção a diálogos, mock tablet e Chromium nas larguras 900/1024px. Sem comunicação S0/S1, merge ou deploy.

## FV-UI-034 — execução nativa integral em snapshot verificado (23/10/2026)

**[FV-UI-034 — relatório do gate sequencial](./61_FV_UI_034_GATE_NATIVO_SNAPSHOT_2026_10_23.md)**: 58/58 blobs Git, Python **20/20**, Node **340/340** e Chromium/Playwright **PASS** em ZIP derivado do código publicado no commit `0deae33`. Apenas diagnóstico visual fictício: sem checkout Git autenticado, sistemas S0/S1 ou homologação.

## FV-UI-035 — foco na ampliação de viewport móvel (23/10/2026)

**[FV-UI-035 — correção de foco mobile→desktop/tablet](./62_FV_UI_035_FOCO_MOBILE_PARA_DESKTOP_2026_10_23.md)**: o botão Voltar, oculto ao cruzar 760px, deixa de provocar perda de foco. O teclado recebe a região de conversa ou a aba ativa de Detalhes, conforme o estado do atendimento fictício.

**[FV-UI-035 — diagnóstico nativo do snapshot](./63_FV_UI_035_GATE_NATIVO_SNAPSHOT_2026_10_23.md)**: **58/58** blobs, **20/20 Python**, **341/341 Node** e **Chromium PASS** em ZIP visual derivado com hashes conferidos no GitHub. Não comprova checkout Git autenticado nem homologação.

## FV-UI-036 — tema claro e escuro, base visual neutra (23/10/2026)

**[FV-UI-036 — design e implementação](./64_FV_UI_036_BASE_VISUAL_TEMA_CLARO_ESCURO_2026_10_23.md)**: visual de mensageria próprio, paleta neutra e escolha Claro/Escuro, incluindo modais, sem integrações ou persistência externa.

**[FV-UI-036 — testes nativos](./65_FV_UI_036_GATE_NATIVO_LOCAL_2026_10_23.md)**: provas sobre snapshot derivado; checkout autenticado e aceite FV-22 continuam pendentes.

## FV-UI-037 — tema dinâmico do sistema até escolha manual (24/10/2026)

**[FV-UI-037 — preferência claro/escuro dinâmica](./66_FV_UI_037_TEMA_SISTEMA_ESCOLHA_MANUAL_2026_10_24.md)**: mudanças de tema no sistema atualizam a interface até a seleção explícita de Claro ou Escuro. A preferência manual prevalece durante a sessão, sem armazenamento ou mudanças comerciais. Somente protótipo fictício.

## FV-UI-038 — contraste dos módulos gerenciais em escuro (24/10/2026)

**[FV-UI-038 — legibilidade no diálogo da equipe](./67_FV_UI_038_CONTRASTE_MODAL_GERENCIAL_DARK_2026_10_24.md)**: uniformiza superfícies e textos auxiliares dos módulos de Lotes, Monitoramento, Fila e ajuda no modo escuro. Inclui testes de contraste em Chromium para desktop/celular; sem dados reais, autorização ou operação de negócio.

## FV-UI-039 — alvos de toque do seletor Claro/Escuro (24/10/2026)

**[FV-UI-039 — controle de tema e reflow](./68_FV_UI_039_ALVOS_TOQUE_TEMAS_2026_10_24.md)**: os botões de tema passam a ter pelo menos 44×44 CSS pixels, com quebra de cabeçalho até 400px e regressão Chromium em 320/390/900/1440px. Apenas aparência e acessibilidade; nenhum efeito comercial.

## FV-UI-040 — Hierarquia visual legível da lista de conversas (24/10/2026)

**[FV-UI-040 — hierarquia da lista em ambos os temas](./69_FV_UI_040_HIERARQUIA_LISTA_2026_10_24.md)**: títulos e metadados com fontes legíveis, contraste reforçado e uma seleção mais perceptível, sem mudar contexto, mensagens ou escopos. Ensaios locais de Chromium (oito cenários) e Node, mais manifesto de 58 blobs conferido no GitHub. Ainda sem gate de checkout autenticado.

## FV-UI-041 — legibilidade de detalhes (24/10/2026)

**[FV-UI-041 — painel Detalhes em claro e escuro](./70_FV_UI_041_LEGIBILIDADE_DETALHES_2026_10_24.md)**: abas e propriedades com fontes mais legíveis, aviso com contraste ajustado e regras de dark mode sem alterar escopo ou ações. Teste local em oito cenários; hashes finais verificados no GitHub.

## FV-UI-042 — cabeçalho e mensagens mais legíveis (24/10/2026)

**[FV-UI-042 — conversa nos dois temas](./71_FV_UI_042_LEGIBILIDADE_CONVERSA_2026_10_24.md)**: melhora fontes e contraste de identidade, prévia contextual, mensagens e horários; preserva envio e sinalização técnica. Ensaio Chromium direcionado em oito cenários, com gate integral do checkout ainda pendente.

## FV-UI-043 — compositor e estados operacionais legíveis (24/10/2026)

**[FV-UI-043 — organização da barra inferior](./72_FV_UI_043_BARRA_OPERACIONAL_COMPOSITOR_2026_10_24.md)**: indicadores contrastantes, ação de trabalho com alvo de 44px, campo e botão de composição com 48px. Corrigida colisão de cores de status no tema claro. Sem mexer no estado comercial, permissões, simulações ou envios.

## FV-UI-044 — foco teclado na conversa (24/10/2026)

**[FV-UI-044 — contorno visível e sequência Tab/Shift+Tab](./73_FV_UI_044_FOCO_TECLADO_CONVERSA_2026_10_24.md)**: margem de 6px na barra operacional rolável para proteger o anel de foco, indicação consistente em cabeçalho, ação, campo e prévia nos dois temas. Chromium direcionado 8/8 local; sem alterar o fluxo de prévia ou autorização.

## FV-UI-045 — auditoria integrada e bloqueio de snapshots antigos (25/10/2026)

**[FV-UI-045 — preflight nativo do checkout e dos blobs](./74_FV_UI_045_PREFLIGHT_NATIVO_HEAD_2026_10_25.md)**: reforça a validação de revisão/branch, ancestral do manifesto, inventário exato e SHA Git/tamanho de cada arquivo antes de executar testes funcionais. Quatro cenários de regressão em Git sintético; checkout autenticado completo e homologação seguem pendentes.

## FV-UI-046 — GitHub Actions para validação integrada (25/10/2026)

**[FV-UI-046 — workflow de validação de interface](./75_FV_UI_046_GITHUB_ACTIONS_VALIDACAO_2026_10_25.md)**: workflow sem deploy restrito à branch experimental, com gatilho por mudança em `frontend/visual`, timeout de 15 minutos, cancelamento de runs repetidas e gate nativo de Git/ZIP/Node/Chromium. Execução real aprovada no commit `f6f10b53329fecfa000699df37bdb1b509626714`: **25/25 testes Python, 352/352 Node e Chromium integrado PASS**, com logs no [run 40180965490](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40180965490). Não constitui homologação de produção.

## FV-UI-047 — filtros da lista mais legíveis (25/10/2026)

**[FV-UI-047 — busca, abas e filtros](./76_FV_UI_047_FILTROS_DA_FILA_2026_10_25.md)**: ajustes somente visuais de áreas de toque (≥44px), fontes, contraste e foco em claro/escuro. Validação oficial **APROVADA** no [GitHub Actions run 40188680770](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40188680770): **25/25 Python, 353/353 Node, Chromium PASS**, com 8 novos cenários de filtros (320/390/900/1440 px × claro/escuro).

## FV-UI-048 — espaço da lista no celular (25/10/2026)

**[FV-UI-048 — fila compacta sem ocultar conteúdo](./77_FV_UI_048_ESPACO_LISTA_MOVEL_2026_10_25.md)**: reduz espaços verticais no cabeçalho móvel, mantém os controles do FV-UI-047, resumo, conversas e rodapé com rolagem na tela baixa. GitHub Actions **APROVADO** no [run 40189686784](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40189686784): **25/25 Python, 354/354 Node e Chromium integrado PASS**, incluindo oito novos cenários de reflow e acesso a conteúdo.

## FV-UI-049 — estados vazios claros (25/10/2026)

**[FV-UI-049 — busca e filtros sem resultados](./78_FV_UI_049_ESTADOS_VAZIOS_DA_FILA_2026_10_25.md)**: diferencia busca vazia, filtros, ausência real na aba e suspensão. Contador visível/total e botão de limpeza estritamente visual; GitHub Actions **APROVADO** no [run 40191190235](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40191190235): **25/25 Python, 355/355 Node e Chromium PASS** em 8 novos cenários (busca, limpeza de filtros e suspensão).

## FV-UI-050 — avisos orientativos e estados (25/10/2026)

**[FV-UI-050 — notificações legíveis](./79_FV_UI_050_AVISOS_ESTADO_2026_10_25.md)**: melhora tempo de leitura, posição do toast e rodapé informativo, mantendo a mensagem e semântica de demonstração. GitHub Actions **APROVADO** no [run 40192925946](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40192925946): **25/25 Python, 356/356 Node e Chromium PASS**, após correção de expectativa de CSS calculado no teste inicial.

## FV-UI-051 — orientações entre lista, conversa e detalhes (25/10/2026)

**[FV-UI-051 — escopo demonstrativo acessível](./80_FV_UI_051_ORIENTACOES_TRES_PAINEIS_2026_10_25.md)**: associa as orientações da busca e composição aos campos correspondentes e explica no Resumo do caso que os dados são fictícios e nenhuma operação externa é realizada. Gate do GitHub Actions **APROVADO** no [run 40196488010](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40196488010): **25/25 Python, 357/357 Node, Chromium PASS** e oito cenários de descrição acessível.

## FV-UI-052 — contagem acessível da lista (25/10/2026)

**[FV-UI-052 — anúncio não duplicado dos resultados](./81_FV_UI_052_CONTAGEM_ACESSIVEL_FILA_2026_10_25.md)**: anuncia a contagem quando há conversas e preserva a orientação própria do estado vazio; sem mudar filtros, permissões ou a automação de outras frentes. Validação GitHub Actions obrigatória.

## Estado do trabalho
FV-UI-015/016: demonstrações com dados sintéticos. **NÃO** declarar integração real, Auth/RLS/GoTrue, comunicações Meta ou remessas confirmadas. FV-UI-013 não homologada formalmente; **19F 69/100** como último marco. Esta consolidação é **documentação somente**. Nenhum código, migration, branch S1, dado real ou deploy foi tocado.

**Critério de mudança futura:** nova decisão expressa do responsável recebe identificador, data, arquivo de precedência e referência ao documento que substitui. Não apagar registros antigos nem deixar texto histórico competir com regra atual.