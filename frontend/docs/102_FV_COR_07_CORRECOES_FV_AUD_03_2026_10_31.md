# FV-COR-07 — correções dos nove achados da FV-AUD-03

31/10/2026. Repositório exclusivo `prumogrowth/Prumo-Growth-Platform-V2`. Branch corretiva `codex/fv-cor-07-pos-auditoria-20261031`, descendente da base auditada `2efa2d5c3df0df05bd0193a715e2e958b71cd816`. A Etapa 1 aprovada permanece ancestral em `17336799ddf4c8575c790f09eb64570d6460733c`.

HEAD remoto e checkout da base foram conferidos antes de alterar arquivos; a branch corretiva não existia. O checkout original e os dois checkouts da auditoria foram preservados. A primeira consulta Git falhou por conectividade com o proxy no sandbox; a permissão oficial de rede foi solicitada, concedida e a consulta repetida com sucesso. Nenhum desvio da política de rede.

## Fonte recuperada e limites

Foram recuperados o relatório integral A–H FV-AUD-03, `achados.json`, reproduções Node/Chromium, matriz dos 63 itens, screenshots e logs. O pacote de auditoria original possui SHA-256 `bbb079c9e27342825f9ccb24b15663f4c40c9080eee38cd270db664824be95c7`. Os identificadores abaixo são os mesmos do relatório; nenhum achado ausente foi presumido.

A [fonte integral FV-REV-01 v0.4](FV_REV_01_v0_4_FONTE_2026_10_29.md), o [mapa de realocação](100_FV_REV_01_ETAPA_2_MAPA_2026_10_30.md), a [entrega anterior](101_FV_REV_01_ETAPA_2_ENTREGA_2026_10_30.md) e as [COR-01 a COR-06](99_FV_REV_01_CORRECOES_POS_AUDITORIA_2026_10_30.md) foram confrontados. O cabeçalho histórico da fonte não substitui esta autorização nem altera o repositório oficial.

A missão corrige somente o frontend sintético. Não cria API/contrato real, autenticação, upload, transporte Meta, execução F03/F02, remessa bancária, reabertura ou resultado comercial. N04/N05 eram implementações parciais, não regressões comprovadas; sua correção demonstrativa não ratifica contratos externos.

## Matriz de correções

| ID / classificação original | Correção delimitada | Evidência e critério de aceite |
| --- | --- | --- |
| R01 / REGRESSION, alta | Banco suspende captura oculta sem descartar prévia pronta ou anexos locais do mesmo contexto. Microfone ainda pendente é cancelado; gravação em curso é parada para produzir prévia. Consulta móvel de detalhes conserva a prévia. | `browser.corrections`: R01, R01-recording e R01-requesting. URLs/texto mantidos ao consultar; tracks encerradas; callback tardio não ressuscita captura; troca real de caso continua revogando URLs. |
| N02 / REQUIREMENT_MISMATCH, alta | O esclarecimento demonstrativo de Banco B não chama a limpeza global do composer de Conversas A. Revalida ator/loja/caso da ficha antes da ação; o retrato alternativo pertence apenas a B. | `modules.dom` e `browser.corrections`: A-102 com texto/emoji/áudio + Banco A-108 + esclarecimento; A-102 continua selecionado e os rascunhos sobrevivem. |
| N03 / REQUIREMENT_MISMATCH, média | A fixture A-111 declara sequência sintética explícita entre fontes: template final confirmado precede a perda. IDs únicos, vínculo/versão e origem da projeção são validados. Registros sem ordem global confirmada ficam em grupo separado, sem linha contínua. Não interpreta rótulos como datas. | `relationship-view` e navegador: envio precede perda; sequência duplicada/inválida não confirma ordem; planejados continuam separados; estados incertos/falhos/cancelados preservados. |
| N04 / PARTIAL_IMPLEMENTATION, média | A cena A-114 inclui acontecimento sintético explícito de atualização cadastral F03, ligado à versão da ficha. Acontecimento é restrito ao titular autorizado e à mesma versão persistida; não é derivado automaticamente do status. | `relationship-view`, `modules.dom` e navegador: Histórico apresenta atualização `live-form-v2-demo`; versão divergente e supervisão não recebem esse detalhe. |
| N05 / PARTIAL_IMPLEMENTATION, média | Persistência cadastral isolada deixa de produzir autoria F03. Publicação F03 adicional exige autoria explícita, publicação/confirmação, público titular e versão correspondente à ficha autorizada. Resultados dos ciclos F03 já autorizados continuam acumulativos. | Teste red/green com ficha F01 persistida sem publicação F03; negativas de versão, confirmação, publicação e público; F01/F02 e ciclos anteriores preservados. |
| I01 / INHERITED_DEFECT, média | Card, leitura e conversa compartilham o critério de corpo legível suportado pelo runtime. Entradas vazias/nulas/ausentes não geram leitura nem pendência. A leitura fictícia referencia o último inbound legível mostrado. A projeção de quantidade é preservada quando existe inbound representável; contador obsoleto sem inbound não cria mensagem. | Casos vazios, whitespace/null/ausente, sistema/IA, local/incerto, nova mensagem após leitura e supervisor. Lista literalmente vazia nunca foi reproduzida como amarelo na auditoria; agora tem estado vazio explícito. Registros sem corpo são sinalizados, não apagados da fixture. |
| I02 / INHERITED_DEFECT + REQUIREMENT_MISMATCH, média | A projeção operacional de transporte continua exigindo titular. Um observador já autorizado à mensagem recebe somente aviso de transporte não confirmado quando não dispõe dessa projeção. Nenhum ACK/proofRef/versão privada é exposto ou consultado como titular. | Negativas de escopo e mensagem, ausência de referências privadas, mesmo guard operacional e aviso visível para Marina; supervisão não marca leitura nem ganha composer. |
| I03 / INHERITED_DEFECT + REQUIREMENT_MISMATCH, baixa | Removido o botão i redundante. Nome do cliente é o controle acessível de abertura; X/Escape/Voltar e resize devolvem foco a controles visíveis. | Jornadas antigas redirecionadas do ID removido para o nome, preservando asserções de foco/aria/teclado e reabertura. Novo navegador exige ausência do i, além do funcionamento do nome. |
| OBS01 / PARTIAL_IMPLEMENTATION, baixa | Rótulo `Total de ativos` e nome acessível `Indicadores fictícios dos atendimentos ativos autorizados` identificam o escopo dos tiles. Filtro e permissões não mudam para fazer números coincidirem. | Todas/Ativos/Históricos continuam 11/8/3 para Rafael/Aurora; resumo permanece de ativos com legenda inequívoca nos dois temas. |

## Segurança, preservação e arquivos

`app.mjs` concentra os reparos de navegação, contexto, renderer e foco. `communication-composer.mjs` separa consulta de descarte; `local-audio.mjs` mantém seu motor e as garantias de generation/contexto, tracks e URLs. `conversation-attention.mjs` valida representação e corte de leitura. `transport-state-view.mjs` acrescenta aviso minimizado, preservando a função estrita anterior. `relationship-view.mjs` e `revision-fixtures.mjs` corrigem ordem/autoria e o exemplo cadastral. `index.html` remove o i e explicita o resumo de ativos; CSS separa visualmente registros sem cronologia global.

Sem alteração em `fixtures.mjs`, `cf-op-02.mjs`, ficha/banco/human-cycle, estados canônicos ou módulos de gestão. Filtros, cards, atenção verde/amarela, conclusão verde autorizada, 0/1/2 ações do composer expirado e faixa terminal substitutiva permanecem. Ficha continua somente leitura e a supervisão continua sem D3/D4.

A allowlist recebe apenas a nova branch exata. Segurança ZIP, inventário, hashes Git e ancestralidade permanecem obrigatórios. O manifesto é repinado após o commit de conteúdo; o commit final certificado contém esse pin e aponta para um ancestral de conteúdo verificável. Não se declara que o manifesto contém o próprio hash nem que o código foi validado sem commit.

## Validação e evidências

Os testes novos foram executados inicialmente contra o runtime auditado, antes da correção. O lote Node inicial teve 10 FAIL / 1 PASS; o PASS é o controle sem pendência em lista vazia/sistema/IA. Falha de placeholder vazio no ensaio Chromium anterior não é prova de amarelo em lista vazia. A primeira execução Node ampla de desenvolvimento teve 441/444 PASS: dois FAIL de manifesto ainda não repinado e um contrato de fonte que passou a exigir a nova função de apresentação minimizada. Não se classificam esses resultados de desenvolvimento como gate certificado ou falhas ambientais.

`browser.corrections.py` executa as reproduções em ESM e HTML integral, nos dois temas, em 1440/900/390px, com teclado, toque emulado quando aplicável, verificação de visibilidade, seleção e efeitos posteriores. O áudio é MediaRecorder com dispositivo sintético; requisições externas são bloqueadas e verificadas. A saída opcional `FV_COR07_OUTPUT` deve ficar fora do checkout e contém resultados, capturas e proveniência. Não representa dispositivo físico ou tecnologia assistiva real.

O gate completo continua exigindo Python, todas as suítes Node e Chromium anteriores; as reproduções FV-COR-07 também são obrigatórias, em etapa adicional limitada a 360s. O orçamento original do Chromium (600s) e as etapas anteriores não foram relaxados ou substituídos. O runner de camadas continua sendo diagnóstico parcial, conforme sua declaração anterior. Os registros locais e a CI no SHA final devem ser consultados para os resultados efetivamente executados. As capturas e o HTML entregues são gerados do checkout validado, identificados pelo SHA e hashes em `PROVENIENCIA.json`. Não há publicação de site.

As alterações de expectativas antigas se limitam a: abertura/foco pelo nome em lugar do i removido; referência explícita da mensagem na leitura local; checagem da função de apresentação minimizada de transporte em lugar da função operacional no renderer. Permanecem as asserções de elegibilidade, descarte em troca real de contexto, envio não comprovado, supervisão e isolamento.

## Dependências e próxima verificação

Continuam pendentes as projeções/contratos reais de leitura, mensagens/mídia, ordem entre fontes, publicação F01/F02/F03, consulta cadastral histórica e capacidades/provas bancárias. A representação textual existente não autoriza interpretar payload desconhecido de mídia como leitura confirmada; áudio local legítimo conserva seu rótulo e seu player. Nenhum contrato externo foi inventado para encerrar um achado.

Abertura direta `file://` foi bloqueada pelo navegador na auditoria e não é certificada por estes testes sob HTTP local. Host/iframe real do proprietário, dispositivos físicos, leitores de tela e integrações reais permanecem fora da evidência executada.

Esta entrega fica pronta para **nova auditoria independente**. Não concede aceite automático, não inicia merge/deploy e não autoriza operações reais. A orquestração deve repetir as reproduções com o novo SHA e verificar a preservação da Etapa 1/COR-01..06, além dos nove achados.
