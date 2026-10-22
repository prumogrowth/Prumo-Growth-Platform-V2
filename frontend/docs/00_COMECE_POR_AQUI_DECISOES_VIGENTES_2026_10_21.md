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

## Estado do trabalho
FV-UI-015/016: demonstrações com dados sintéticos. **NÃO** declarar integração real, Auth/RLS/GoTrue, comunicações Meta ou remessas confirmadas. FV-UI-013 não homologada formalmente; **19F 69/100** como último marco. Esta consolidação é **documentação somente**. Nenhum código, migration, branch S1, dado real ou deploy foi tocado.

**Critério de mudança futura:** nova decisão expressa do responsável recebe identificador, data, arquivo de precedência e referência ao documento que substitui. Não apagar registros antigos nem deixar texto histórico competir com regra atual.