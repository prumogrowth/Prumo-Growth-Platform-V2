# AL-IA-07 — Revisão cruzada de outras frentes: só dependências úteis à IA

**Data:** 22/10/2026 | **Modalidade:** leitura temática das **branches GitHub independentes**; atualização apenas da **documentação de nossa frente OpenAI**. As fontes externas não foram editadas, fundidas ou copiadas em bloco.  
**Terminologia oficial do produto:** **plataforma** = sistema comercial desenvolvido pela Prumo, **ainda sem nome próprio definitivo**; **LiberaCred** = produto de crédito da instituição financeira. Não chamar a plataforma de LiberaCred, salvo ao citar fielmente nome histórico de arquivo.

## 1. Fontes efetivamente consultadas

| Frente | Branch/PR | Documentos-fonte prioritários lidos |
|---|---|---|
| Núcleo S0 | `feat/s0-fundacao-prumo` / PR #1 Draft | `docs/S0_043_PAUSA_SELETIVA_E_INDICADOR_CONVERSA_2026_10_20.md`, `S0_044_ALINHAMENTO_FILA_GESTORES_IA_2026_10_21.md`, `S0_045_NOMENCLATURA_DIRETOR_GESTOR_CONSULTOR_2026_10_21.md`, `D_ORG_01_EQUIPE_PRUMO_2026_10_18.md`, `REGRA_NUMEROS_ATENDIMENTO_CLIENTE_2026_10_17.md`, `CF_OP_02_CONTRATO_NUCLEO_RECONTATO_HUMANO_v0_1.md` |
| WhatsApp/Meta | `docs/whatsapp-meta-concessionária de demonstração-poc-20261017` / PR #2 Draft | `00-decisoes-vigentes-precedencia-documental-2026-10-21.md`, `01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md`, `decisao-titularidade-meta-por-concessionaria-v1_0.md`, WA-17B, WA-18B/18C, WA-20/21 |
| Gestão/equipe S1 | `feat/s1-002-equipe-prumo` / PR #5 Draft | I11 (com retificação), I12, I13, `S1_002_ISSUE10_EXCECAO_POR_CASO_RLS_2026_10_20.md`, `S1_002_MARCO_PAUSA_ALINHAMENTO_AUDITORIA_DOCUMENTOS_2026_10_20.md` |
| Interface visual | `feat/frontend-plataforma-visual` (branch independente) | `frontend/docs/00_COMECE_POR_AQUI_DECISOES_VIGENTES_2026_10_21.md`, FV-DOC-01/35, FV-DOC-02/36, FV-02/05, FV-03/09 |
| Coordenação CFI/F03 | `coord/s0-openai-cfi01-c09-20261019` / PR #8 Draft e `feat/s0-cfi01-f03-auth-preflight-20261020` / PR #12 Draft | `OPENAI_F01_F02_F03_RESPONSABILIDADES_V0_1.md`, `CFI01_NOTA_ARQUITETURA_OPENAI_S0_SUPABASE_N8N_2026_10_21.md`, `S0_CFI01_F03_SNAPSHOT_METADATA_RATIFICATION_GATE_2026_10_21.md`, `S0_CFI01_RECHECK_POST_F03_PG17_2026_10_21.md` |
| Contrato interfrentes CF-OP-02 | `docs/cf-op-02-cadeias-contextuais-20261018` / PR #7 Draft | Diretriz e matriz CF-OP-02, complementadas pela versão S0/Frontend |

**Limite da leitura:** inspeção das decisões e contratos transversais pertinentes ao trabalho OpenAI; não equivalem a auditoria integral de código, revisão linha a linha de todos os arquivos, homologação técnica ou autorização para incorporar a totalidade dos documentos.

## 2. Descobertas que **corrigem** nosso registro

### XFR-01 [ALTA] — Canal da concessionária, e não propriedade da Prumo
Meta **DEC-WA-05/WDC-02** aprovou **conta empresarial/App/WABA/número de WhatsApp/catálogo de templates pertencentes à concessionária**. Prumo opera com delegação. Corrigimos AL-IA-01/04/05: a hipótese “número da própria Prumo dedicado à loja” é **histórica e superada como propriedade**, enquanto a exclusividade do número emissor por loja e o isolamento continuam. Posse técnica efetiva e onboarding seguem [V]. **Implicação IA:** F01 representa contexto/canal da loja autorizada; não assume recursos Meta globais.

### XFR-02 [ALTA] — Duas falhas consecutivas geram também perda técnica
Meta **WA-18C/WDC-13** acrescenta ao cancelamento da cadência a transição comercial **`perdido` com motivo técnico**, executada pelas regras backend/S0, não pela IA F02. Somente falhas **definitivas e correlacionadas** da mesma cadeia contam; **um envio `sent` comprovado entre falhas zera o contador** mesmo sem resposta, e um timeout/API_ACCEPTED/UNKNOWN não é prova. Corrigimos AL-IA-01/04/05. Isso é **outra origem de `perdido`**, distinta de desistência reconhecida na F03, silêncio após template final e negativa bancária formal.

## 3. Novas informações relevantes, sem reabrir decisões do responsável

### XFR-03 [ALTA] — F02 não recebe todo o catálogo; finalidades internas são independentes da categoria Meta
Meta **WDC-08–12/WA-18B/18C**: `MARKETING`/`UTILITY` são **categorias da Meta**, enquanto **FINALIDADES internas** (abertura, recontato, campanha, operação humana etc.) admitem vários vínculos num template, cada uso com elegibilidade/autorização independente. F02 recebe **somente** modelos de sua loja/WABA, ativos, aprovados, versão correta e **permitidos para aquele fluxo/público/finalidade**. Se Meta invalidar um template, S0 pode chamar F02 com contexto e alternativas aprovadas; ela pode retirar, substituir, reordenar/ajustar plano autorizado, **não criar template**. Erro comum de envio **não** dispara F02.

### XFR-04 [ALTA] — Variáveis de templates são calculadas pelo backend, não pela IA
Meta **WDC-09/WA-18B**: o vínculo `{{slot}}`→fonte permitida permanece **congelado por versão aprovada**. Valor de nome, campo de cadastro, URL dinâmica autorizada etc. só é resolvido **na hora do disparo pelo backend**, com escopo, finalidade, versão e fontes aprovadas. F01 e F02 não inventam nem injetam valores. Template aprovado pode admitir edição **quando Meta permitir**, mantendo snapshot histórico e nova revisão, nunca supondo “HTTP 2xx = aprovado”.

### XFR-05 [ALTA] — Opt-out é independente em cada concessionária
Meta **WDC-14–16/WA-18**: opt-out solicitado à concessionária A **bloqueia proatividade de A**, sem alterar registro de B; B precisa elegibilidade própria. Cliente enviar mensagem espontânea após opt-out **não restaura automaticamente opt-in**. F01/F02 devem receber bloqueio/elegibilidade efetivos da S0, nunca decidir reconsentimento a partir de conversa isolada. Botões de “não quero” podem trazer interpretação comercial contextual, mas pedido inequívoco de parar comunicação prevalece na proatividade.

### XFR-06 [ALTA] — F01 não conhece disponibilidade de Consultores
S0-044 e FV-DOC-01/D-AL-08 fixam que F01 **não conhece quantidade, nomes, equipes, escalas, concessões ou disponibilidade dos Consultores/Gestores**. A F01 continua seu trabalho mesmo sem humano elegível e apenas solicita handoff; S0/S1 resolve atribuição/fila. O prompt e a recuperação de dados devem **excluir** essas informações, não apenas dizer que F01 não as utilize. **F03 é outra tarefa**: ao devolver pendência do atendimento humano, precisa de endereçamento autorizado pelo S0 ao Consultor original/Gestor, sem receber listagem irrestrita de pessoal.

### XFR-07 [ALTA] — “Pausado para novos leads” não é “indisponível para o caso”
S0-043/044, S1 ISSUE10 e FV-DOC-01: o Gestor pode **pausar apenas o recebimento de novos leads**, com confirmação simples e sem motivo/duração, preservando conta, grants e **acesso aos casos ainda atribuídos**. Casos iniciados por contato humano comprovado permanecem com o Consultor. Só casos **sem contato comprovado** podem ser redistribuídos automaticamente **dentro da mesma equipe** e com concessão à loja; sem elegível, permanecem com titular pausado. Novos leads normalmente podem ser distribuídos **entre equipes**; se ninguém elegível, ficam **sem titular** em fila dos gestores autorizados. **Implicação F03:** não acionar automaticamente Gestor só porque o Consultor original tem `intake_paused`; S0/S1 avalia indisponibilidade real, atribuição e autoridade.

### XFR-08 [MÉDIA] — Gestor e exceção por caso
S0 D-ORG-01, S1 I11/I12 e ISSUE10: equipe de Consultores/Gestores é **da Prumo**, ainda que dedicada a lojas específicas. Diretor gere contas e grants gerais; Gestor administra equipe e pode assumir caso autorizado. Transferência manual é restrita **à própria equipe**, podendo criar **autorização estritamente por caso** para destinatário sem grant geral de concessionária, sob RLS/escopo/revogação. Isso afeta F03 quando devolve pendência ao Gestor, pois **notificar** não equivale a dar leitura sem autorização D2/D3/D4. A F03 não atribui diretamente nem alarga ACL.

### XFR-09 [MÉDIA] — Identificação humana visível, distinta da F01
Meta **WA-21**: mensagem **textual livre escrita por Consultor/Gestor/Diretor** recebe prefixo automático do backend `Cargo Nome:\nMensagem`, com cargo/nome reais autenticados; não faz parte do campo de comportamento da F01 nem concede identidade humana à IA. Templates requerem conteúdo/variável Meta aprovados; não concatenar prefixo livre a template. Histórico guarda autoria e texto realmente transmitido. **Não implementado ainda**.

### XFR-10 [ALTA] — F03: contrato CFI-01 físico é menor que a intenção recém-aprovada
PR #12 **CFI-01** provou em PG17 e GoTrue efêmeros a captura/rechecagem de **recibo de encerramento**, autenticação, atribuição, `expected_cycle_version`, hash e watermark de mensagens. **NÃO** entregou conteúdo da conversa, `form_version`, versão autorizada do catálogo, nem contrato de extração histórico/multimodal de F03. `expected_cycle_version` ≠ `expected_case_version` por suposição. O alinhamento novo exige acesso lógico ao histórico **do mesmo cliente em toda a concessionária**, até o corte, mesmo quando múltiplas conversas/consultores. **Necessária revisão cruzada técnica**, não reduzir F03 ao caso físico atual nem tratar laboratório como execução OpenAI.

### XFR-11 [MÉDIA] — Janela humana e C09 pertencem a contratos distintos
S0 CF-OP-02, FV-03 e PR #7 preservam: última mensagem **inbound cliente** inicia/reabre janela Meta de 24h; clique explícito de conclusão humana dispara F03; 24h depois do template final **comprovadamente enviado**, com silêncio e elegibilidade, é relógio de possível `perdido` por inatividade. Mensagem de template outbound não reabre conversa livre. **Regras visuais de tirar da lista ativa após conclusão+janela encerrada não equivalem a apagar conversa nem a concluir automaticamente o humano.** Qualquer detalhe de fila/retorno deve manter precedência do novo alinhamento AL-IA-01 e revisão S0/S1.

### XFR-12 [MÉDIA] — n8n não é obrigação arquitetural
Nota CFI-01 da coordenação: **Supabase/Auth/PostgreSQL** é núcleo decidido; **n8n versus ligação direta/combinação com backend S0 permanece [R]**. O modelo não ganha SQL nem credenciais; backend S0 mantém autorização, validação e persistência. Não transformar preferência técnica do assistente em decisão final.

## 4. Pendências e fontes de verdade

1. **Atualizações desta nossa frente:** AL-IA-01/02/03/04/05/06 e índice AL-IA-00 foram corrigidos em pontos de terminologia/titularidade; AL-IA-01/04/05 também ajustaram perda técnica e indisponibilidade do Consultor. **Outras branches não foram editadas.**
2. **[R]** Cabe à coordenação OpenAI↔S0 firmar envelope F03 em conformidade com histórico integral por cliente/concessionária, cutoff, identidade/campo/versão, e efeitos idempotentes atuais.
3. **[R]** Cabe a S0/Meta rever planos F02 com finalidade por template, falhas definitivas, pausa/suspensão de template, snapshots e autorização comercial distinta.
4. **[R]** Cabe a S0/S1/frontend ratificar o caminho F03→Consultor/Gestor e semântica da indisponibilidade, distinta da simples pausa de intake.
5. **[V]** Banco, Meta em produção e LGPD continuam pendentes de homologação; nenhum documento daqui inventa acesso real, aprovação bancária, ferramenta MCP ativa nem implantação de IA.
6. **Regra de classificação:** fatos decididos noutras frentes são fontes válidas quando afetam nosso contrato; modelos técnicos ainda [P/R] não viram decisão nova do responsável. Se há choque real, sinalizar e conciliar com a frente titular antes de codificar.

## 5. Links de consulta

- [Meta — índice vigente WDC-01..22](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/docs/integracoes/whatsapp-meta/00-decisoes-vigentes-precedencia-documental-2026-10-21.md)
- [Meta — decisão de titularidade DEC-WA-05](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/docs/whatsapp-meta-concessionária de demonstração-poc-20261017/docs/integracoes/whatsapp-meta/decisao-titularidade-meta-por-concessionaria-v1_0.md)
- [S0 — distribuição e fronteira da IA S0-044](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-fundacao-prumo/docs/S0_044_ALINHAMENTO_FILA_GESTORES_IA_2026_10_21.md)
- [S1 — pausa de intake, correção issue #10](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s1-002-equipe-prumo/docs/S1_002_I11_GESTAO_POR_EQUIPE_PAUSA_GLOBAL_2026_10_19.md)
- [FV — decisões D-AL-01..10](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/frontend-plataforma-visual/frontend/docs/35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md)
- [CFI-01 — gate de metadados F03](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-cfi01-f03-auth-preflight-20261020/docs/S0_CFI01_F03_SNAPSHOT_METADATA_RATIFICATION_GATE_2026_10_21.md)
- [CF-OP-02 — contrato S0](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-fundacao-prumo/docs/CF_OP_02_CONTRATO_NUCLEO_RECONTATO_HUMANO_v0_1.md)

**Resumo:** a revisão NÃO importa toda a documentação alheia; captura as diferenças que mudam filtros, memória/contexto, decisões F01/F02/F03, permissões e fluxos da nossa integração. O restante pertence a suas respectivas frentes e só será incorporado quando se tornar dependência direta.
