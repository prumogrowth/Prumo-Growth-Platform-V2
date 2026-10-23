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

## Estado do trabalho
FV-UI-015/016: demonstrações com dados sintéticos. **NÃO** declarar integração real, Auth/RLS/GoTrue, comunicações Meta ou remessas confirmadas. FV-UI-013 não homologada formalmente; **19F 69/100** como último marco. Esta consolidação é **documentação somente**. Nenhum código, migration, branch S1, dado real ou deploy foi tocado.

**Critério de mudança futura:** nova decisão expressa do responsável recebe identificador, data, arquivo de precedência e referência ao documento que substitui. Não apagar registros antigos nem deixar texto histórico competir com regra atual.