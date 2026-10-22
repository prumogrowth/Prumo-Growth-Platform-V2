# FV-DOC-04 — Auditoria documental de alinhamento e integridade do Frontend
**Data:** 22/10/2026. **Escopo:** documentação própria da branch `feat/frontend-plataforma-visual`, com leitura de fontes **externas sem modificá-las**. **Tipo:** auditoria de conteúdo/precedência e verificação de referências Markdown; **NÃO** é auditoria de implementação, aprovação cruzada de contratos, execução de testes UI/CI, revisão jurídica ou homologação.
**Veredito:** **APTO PARA CONTINUAR O DESENVOLVIMENTO DA FRENTE VISUAL COMO REFERÊNCIA DOCUMENTAL, COM RESSALVAS TÉCNICAS EXPLICITADAS.** Não significa que todas as funções estejam prontas ou que os documentos normativos de outras frentes tenham sido corrigidos.

## 1. O que foi feito nesta rodada
- Consolidação funcional [FV-DOC-03](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md) criada com fronteiras de produto, papéis, O3 sem edição cadastral, F01/F02/F03, fluxo de conclusão, estados Meta, assinatura de autoria, filas, indicadores, dependências e cenários futuros de aceite FV-22-01..16.
- Índice [00 — COMEÇAR AQUI](./00_COMECE_POR_AQUI_DECISOES_VIGENTES_2026_10_21.md) atualizado para colocar a nova referência **antes** da leitura das decisões de 21/10, identificar plataforma sem nome e separar produto bancário LiberaCred.
- [D-NOM-01](./37_D_NOM_01_NOMENCLATURA_DIRETOR_GESTOR_CONSULTOR_2026_10_21.md) atualizado para nomear os papéis **da plataforma**, não “papéis da LiberaCred”.
- [D-AL-01..10](./35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md) mantido para distribuição/pausa; remarcado como histórico 21/10 e com exclusão explícita da IA de melhoria da primeira versão. Prova de contato humano reforçada: ACK de solicitação não é envio efetivamente confirmado.
- [FV-DOC-02](./36_FV_DOC_02_AUDITORIA_AMBIGUIDADES_E_PRECEDENCIA_2026_10_21.md) preserva o diagnóstico antigo e aponta para a auditoria atual.
- Emendas de precedência em [escopo 01](./01_ESCOPO_E_FRONTEIRAS.md), [mapa 02](./02_MAPA_DE_TELAS_E_JORNADAS.md), [materiais 03](./03_MATERIAIS_E_PREPARACAO.md), [FV-01/04](./04_CONTRATO_FV01_UI_BACKEND_v0_1.md), [FV-02/05](./05_CONTRATO_FV02_CONCLUSAO_EXTRAÇÃO_POS_HUMANA_v0_1.md), [CFI-01/07](./07_CONCILIACAO_INTERFRENTES_FV_S0_OAI_v0_1.md), [matriz CFI/08](./08_MATRIZ_ACEITE_CONTRATUAL_FV_S0_OAI_v0_1.md), [FV-03/09](./09_CF_OP_02_CONTRATO_VISUAL_JANELA_CADEIAS_v0_1.md), [auditoria O3/16](./16_AUDITORIA_FV_UI_007_FICHA_PROVENIENCIA_2026_10_18.md), [gestão 21](./21_FV_G2_01_GESTAO_POR_OPERADORES_E_PAUSA_GLOBAL_2026_10_19.md), [leitura UQ/30](./30_FV_S0_UQ_CONTRATO_LEITURA_CANDIDATO_2026_10_20.md), [indicador/32](./32_FV_UI_014_INDICADOR_UNICO_E_PAUSA_SELETIVA_2026_10_20.md) e [prévia/34](./34_FV_UI_016_MARCO_PREVIA_G2_2026_10_20.md).
- **Regras antigas que prometiam C13 ao Consultor foram corrigidas nos pontos de maior risco:** linha O3 do mapa 02, tabela e §5 FV-01, passo 7 e casos FV02-T01/T12 da FV-02, matriz CF-01 da CFI-01 e cenários CFI-T22/T29 da matriz 08. Referências históricas documentais permanecem identificadas como **superadas para a UI**; não há remoção destrutiva de evidência de datas anteriores.

## 2. Matriz de cobertura dos achados relevantes à nossa frente
| ID | Tema | Decisão/fonte e tratamento Frontend | Estado documental |
|---|---|---|---|
| A-01 | Nome da aplicação e produto financeiro | Plataforma Prumo **sem nome definido** ≠ LiberaCred, **produto da instituição financeira**; atualização no índice, D-NOM e FV-DOC-03 §1 | **[D] Registrado** |
| A-02 | Papéis | Diretor / Gestor / Consultor; não renomear status/roles do banco sem contrato; D-NOM + FV-DOC-03 §§0/2 | **[D] Registrado** |
| A-03 | Ficha O3 | **Consultor não altera NENHUM campo manualmente**, nem por exceção antiga C13. O3 leitura/proveniência/lacunas, sem editor; FV-DOC-03 §3, 01/02/04/05/07/08 | **[D] Registrado / referências conflitantes emendadas** |
| A-04 | F01/F02/F03 e conclusão | F01 atende; F02 planeja; F03 extrai após clique humano e validação S0. Divergência pontual de sigla na fala registrada [R-SIGLA-01], sem inventar decisão. | **[D/E] Fluxo de UI registrado; nomenclatura pontual [R]** |
| A-05 | Ficha viva, cutoff e mídias | Ficha evolutiva por loja, histórico lógico sem vazar lojas, encerramentos rastreáveis, snapshots bancários preservados; armazenamento multimodal e múltiplos números [R/V] | **[E] Registrado, técnica pendente** |
| A-06 | Pendência de extração | Consultor original esclarece ao cliente; Gestor autorizado assume encaminhamento quando indisponível, não edita campo cadastral; FV-DOC-03 §3 | **[E] Registrado** |
| A-07 | Assinatura humana | Texto livre `Cargo Nome:\nMensagem` para Diretor/Gestor/Consultor; autoria real S0, prévia, retry seguro; templates não recebem prefixo arbitrário; FV-DOC-03 §5 | **[D/E] Registrado; integração [T]** |
| A-08 | Janela Meta x conclusão | Último inbound +24h != clique humano != 24h pós-template final. Composer livre bloqueado fora da janela, histórico retido; FV-DOC-03 §4 | **[D/E] Registrado; política de lista ativa [R]** |
| A-09 | Templates, entrega e falhas | ACK != SENT, status técnicos distintos de comerciais, finalidades de templates distintas de categorias Meta e consentimento, falhas correlacionadas e confirmadas | **[E] Registrado; integração [T/V]** |
| A-10 | Pausa e distribuição | Caso existente do pausado só redistribui mesma equipe; lead novo pode cruzar equipes. Fila sem titular dos Gestores autorizados; FV-DOC-03 §6 remete D-AL | **[D] Registrado** |
| A-11 | Indicador único | COUNT/DOT/NONE e supervisor não marca leitura; herança após transferência permanece hipótese S1 | **[D/R] Registrado** |
| A-12 | IA Vendedora e outras IAs | F01 não conhece quadro de Consultores; **IA de melhoria excluída da primeira versão**; F02/F03 continuam diferenciadas | **[D] Registrado** |
| A-13 | Administração Diretor e conhecimento | MCP via própria frente com segunda confirmação e audit log protegido; quatro configurações globais de IA e bases por loja sem menus inventados no Frontend | **[E] Contexto registrado, sem tela contratada** |
| A-14 | Meta: titularidade x operação | Ativos Meta ligados à concessionária, configuração/uso operacional via Prumo autorizada; não transformar em propriedade jurídica presumida nem credencial do browser | **[D/E/V] Distinção registrada** |
| A-15 | Transições e remessa | Ato de clicar Concluir não vende/remete. F03 pode produzir avaliação que somente S0 pode autorizar para estado permitido; venda e remessa exigem prova própria | **[E] Registrado; catálogo S0 [R]** |
| A-16 | Capacidade efetivamente entregue | Protótipos sintéticos não são Meta/Supabase operacional; FV-UI-013 não homologada e 19F 69/100 último marco conhecido | **[T] Limitação registrada** |

## 3. Riscos residuais que NÃO são dúvidas da frente sobre a decisão principal
**R-01 — Sigla pós-humana:** fala recente cita F03 e F02, enquanto documentação vigente OpenAI fixa F03 como extratora e F02 como planejadora. Sem inventar mudança de arquitetura; a UX exige apenas **clique explícito → S0 → resultado autorizado da extração**, sem edição manual. Requer esclarecimento apenas se o nome/capacidade física for assunto de integração [R-SIGLA-01].

**R-02 — Versões e contrato S0/CFI-01:** `expected_case_version` conceitual FV e `expected_cycle_version` do S0 laboratorial não são equivalentes comprovados; ausência de assinatura/endpoint final bloqueia botão real. UI não fabrica cutoff, catálogo ou prova de persistência [R-CFI-01].

**R-03 — Transferência/leituras/filas S1:** elegibilidade de Consultor pausado para transferência manual, herança de não lidas quando muda titular, fila de Gestores entre equipes e APIs reais continuam pendentes de contratos/aceites. S1 contém testes em sandbox, **não implementação aprovada em produção** [R-S1-01/R-LEITURA-01].

**R-04 — Histórico pós-conclusão e janela Meta:** distinção entre **tirar da lista ativa** e **manter titularidade/histórico** necessita projeção S0; não desligar consultor por relógio ou apagar chat [R-RETENCAO-01].

**R-05 — F03, `perdido` e Banco:** possibilidade recente de classificar desistência pelo extrator entra em atrito com documentação anterior; apenas S0 poderá autorizar/aplicar transições válidas. Banco exige evidência real, não simulação; fiscalização externa fora desta frente [R-STATUS-01/V].

**R-06 — Mídias, identidade multi-telefone e LGPD:** permitir consulta lógica F03 a mídias autorizadas não significa retenção física universal; múltiplos telefones por ficha exigem controle de identidade S0, não campo editável no Frontend [R/V].

**R-07 — Legado histórico:** muitos relatórios de ensaio visual 18–20/10 permanecem fiéis ao seu momento e contêm rótulos e hipóteses agora superados; a **ordem canônica de consulta** e as emendas impedem que sejam tratados como normas atuais. Não reescrever retroativamente relatórios de testes como se o teste antigo houvesse sido reexecutado.

## 4. Verificações de integridade documental
- **Leitura:** documentos atuais da nossa branch e fontes relevantes publicadas nas frentes Meta (WA-21, especificação 01), OpenAI (AL-IA-01/02/03), S1 (I37, ISSUE10 indicadores) e coordenação S0/CFI-01. O uso externo é **somente contextual**, nunca modificação.
- **Links Markdown relativos — CHECK FINAL REALIZADO:** consulta à árvore GitHub desta branch depois da criação desta auditoria, seguida de inspeção dos **19 arquivos criados/alterados**: **114 referências Markdown relativas**, **0 caminhos locais inexistentes**. Foram conferidas também as referências ao próprio FV-DOC-04. **Não** foram validados conteúdo/resposta de URLs externos, direitos de acesso do leitor ou todos os 55 documentos históricos.
- **Higiene de escopo — CHECK FINAL REALIZADO:** comparação GitHub desde o SHA inicial `4fc3f5861595204f42b94a8fb99f2d031f21aa01`: **19 arquivos alterados (17 editados + 2 novos)**, **100% `.md` em `frontend/docs/`**, **0 outros caminhos no diff**. Nenhum código, arquivo de teste, S0, S1, Meta, OpenAI, banco real ou main foi editado por esta frente.
- **Não houve testes de código**, screenshots de UI, Chromium, SQL ou conexão com OpenAI/Meta/Supabase nesta rodada, portanto **não declarar a UI homologada**, nem aumentar o índice 19F.
- **Certeza:** a fonte recuperável da regra atual é o índice 00 → FV-DOC-03 → D-AL/D-NOM → contratos visuais antigos como complemento histórico. Conflitos mais amplos de contrato físico permanecem responsabilidade das frentes proprietárias.

## 5. Próximo uso recomendado
Antes de implementar ou revisar cada tela, vincular o incremento aos cenários **FV-22-01..16** no [FV-DOC-03](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md), exigir projeção/status autêntico da frente proprietária quando houver efeito real e rejeitar qualquer inferência de autorização pelo navegador. **A documentação é suficiente para prosseguir no desenho/contratos do Frontend dentro dessas ressalvas; não equivale a liberar integração produtiva.**
