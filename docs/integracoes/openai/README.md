# Frente OpenAI — Prumo Growth | índice inicial

## E04 — conflitos históricos F03 corrigidos (23/10/2026)

[Correção no pré-validador F03](./e04_offline_lab/f03-commit-gate.mjs), [15 cenários adversariais novos](./e04_offline_lab/tests/f03-commit-gate.test.mjs) e [relatório de investigação e execução](./E04_F03_CONFLITOS_HISTORICOS_TESTES_2026_10_23_v0_1.md). A F03 não pode mais ocultar divergência explícita de valores do mesmo campo entre atendimentos autorizados: o laboratório compara as evidências **independentemente do que o modelo declare em `conflicts`** e encaminha a revisão humana, sem sobrescrever ficha. Não escolhe o valor mais recente automaticamente.

**Provas distintas:** **110/110** aprovados no Node 22.16.0 local (57 F03 + 53 ciclo F02); **269/269** aprovados em V8 isolado sobre os 6 arquivos de teste recuperados do GitHub (imports nativos adaptados), **não** `npm test` completo no Node/CI. Os 70 SYN originais E02 continuam sem homologação de execução; E04 offline autorizada, E05 não autorizada.

## E04 — proteção F03 contra sobrescrita, replay e fonte inválida (23/10/2026)

Implementados [pré-validador puro F03](./e04_offline_lab/f03-commit-gate.mjs), [42 casos de teste](./e04_offline_lab/tests/f03-commit-gate.test.mjs) e [relatório de evidência](./E04_F03_PRECHECK_CONCORRENCIA_NODE_2026_10_23_v0_1.md). **Node.js 22.16.0:** 42/42 novos casos F03 aprovados e 95/95 com os 53 F02 presentes no diretório local. **Regressão de 6 suítes completas, sobre fontes reobtidas do GitHub:** 254/254 aprovados em **V8 isolado com adaptação de imports Node** — não é `npm test` completo no Node/CI. Nenhum resultado concede mutação, envio, prova do Banco ou homologação S0.

As guardas mantêm cutoff histórico imutável, validam seis versões distintas, exigem evidência explicitamente atestada na **fixture confiável da S0**, bloqueiam fontes de outra pessoa/concessionária, versões alteradas e replays conflitantes. Permissão real, assinatura e veracidade do histórico dependem de ratificação S0/CFI-01. **70 SYN documentais da E02 continuam sem execução de sua suíte original; E05 não autorizada.**

## E04 — jornada integrada offline F01 → humano → F03 → F02 (23/10/2026)

[Código de orquestração pura](./e04_offline_lab/journey.mjs), [43 testes de integração sintética](./e04_offline_lab/tests/journey.test.mjs) e [relatório de fronteiras/evidências](./E04_FLUXO_INTEGRADO_F01_HUMANO_F03_F02_2026_10_23_v0_1.md) publicados somente nesta branch. A jornada exige handoff e conclusão humana expressos, F03 por histórico autorizado da mesma pessoa/loja, nova autorização **separada** da S0 para F02 e rechecagem final de categorias/limite local/recibos. Não envia, não grava, não devolve F01 ao caso humano.

**Regressão conjunta realizada em runtime V8 isolado com arquivos da branch:** **212/212 PASS** (50 guardas, 33 transporte, 33 frequência, 53 ciclo F02, 43 jornada); **não** é execução integral `npm test` no Node/CI, que permanece como verificação separada. Os **70 oráculos originais SYN da E02** continuam sem execução/homologação por seu protocolo. E04 offline autorizada; E05/chaves/custo/Meta real não.

## E04 — ciclo de vida F02 e concorrência (23/10/2026)

Implementado o [avaliador offline de ciclo de plano F02](./e04_offline_lab/plan-lifecycle.mjs), acompanhado de [53 testes `node:test`](./e04_offline_lab/tests/plan-lifecycle.test.mjs) e [evidência técnica de execução](./E04_F02_LIFECYCLE_CONCORRENCIA_EVIDENCIAS_2026_10_23_v0_1.md). **53/53 PASS em Node.js 22.16.0**, arquivos publicados com os mesmos hashes dos executados. Valida versões de caso/catálogo/cadeia, limites de posse/handoff e opt-out, eventos repetidos/contraditórios, `sent` terminal, `unknown/queued/api_accepted` e hold 131049. Qualquer indicação de próxima tentativa significa apenas **pedido de rechecagem S0**, nunca autorização de envio, confirmação Meta ou alteração comercial.

**Medição:** estes são **53 novos testes isolados**, além dos 66 testes de frequência/recibos medidos em Node na rodada anterior. Os 50 testes F01/F02/F03 foram executados anteriormente em V8; não houve execução completa do comando `npm test` nesta rodada. Os 70 oráculos SYN da E02 seguem sem execução integral própria. E04 offline continua liberada, E05 não.

## E04/F02 — frequency capping Meta e erro 131049 (22/10/2026)

O responsável levantou a hipótese de **“dois templates por pessoa a cada dia sem resposta”**. A pesquisa confirmou limitações Meta adaptativas de **MARKETING** e rejeição **131049**, mas **não** confirmou limite numérico universal de dois templates diários. Ver [análise e conciliação CF-OP-02/FREQ v0.1](./CF_OP_02_META_FREQUENCY_CAPPING_F02_2026_10_22_v0_1.md).

**E04 entregou código offline:** [pré-verificação de frequência local configurável](./e04_offline_lab/template-frequency.mjs), [33 casos de frequência](./e04_offline_lab/tests/template-frequency.test.mjs), além de **5 regressões novas** na [suíte de recibos Meta](./e04_offline_lab/tests/transport-evidence.test.mjs), agora com **33 casos**. As duas suítes totalizam **66/66 PASS reais no Node 22.16.0**, com hashes dos quatro arquivos idênticos aos blobs testados no GitHub; nenhuma API real. Os 50 testes anteriores seguem medidos separadamente em V8. **Os 70 SYN E02 não foram executados como oráculos originais.** 131049 causa revisão, não perda comercial automática; definição física pertence S0/Meta [R].

## E04 — redutor de recibos Meta implementado offline (22/10/2026)

A suíte E04 ganhou [normalizador determinístico de recibos de transporte](./e04_offline_lab/transport-evidence.mjs) e [28 testes `node:test`](./e04_offline_lab/tests/transport-evidence.test.mjs). **28/28 passaram em Node.js 22.16.0 com os mesmos blobs publicados no GitHub.** Esse incremento não executa webhook real, envio, C09, mudança de status, banco ou chamada OpenAI. `sent` requer prova no modelo sintético; `queued/accepted/unknown` não contam como envio; duas falhas definitivas são **apenas sinalização de revisão S0**, sem concluir perda comercial.

**Métricas não intercambiáveis:** os 50 testes anteriores de guardas F01/F02/F03 passaram em V8 isolado (runner Node ainda não comprovado); os 28 testes novos passaram em Node real; os **70 SYN originais** continuam oráculos documentais, não resultados homologados. A autorização específica E04 offline permanece vigente, E05 e efeitos externos seguem bloqueados.

## E04 AUTORIZADA E INICIADA — implementação offline isolada (22/10/2026)

**Autorização expressa do responsável, nesta conversa:** iniciar desenvolvimento de código e testes **offline** com dados 100% fictícios, apenas na frente OpenAI/PR #3. A trava `G-FASE-DO-PROJETO` de **implementação E04** fica liberada **somente para este escopo**; não implica ratificação S0/Meta, E05, API pagas, credenciais, dados reais, deploy, migração, outros PRs ou merge.

**Primeira entrega de código:** [laboratório executável E04 — Node.js, sem dependências](./e04_offline_lab/README.md), [validador offline `core.mjs`](./e04_offline_lab/core.mjs) e [50 testes sintéticos `node:test`](./e04_offline_lab/tests/offline.test.mjs). A lógica e as mesmas 50 funções de teste foram executadas em V8 isolado **50/50 PASS** nesta sessão; **execução nativa `node --test` ainda não verificada**. Evidência limitada a validadores puros sem integração física/modelo.

**Métricas distintas:** 70 cenários SYN documentais da E02 **continuam sem execução/homologação como suíte original**; os 50 casos E04 são **testes unitários sintéticos novos sobre subconjunto de guardas**, não equivalentes a 50/70 SYN aprovados. E02-REV física permanece [R], E03-A..H adiadas, E05 bloqueada.

## Governança de conhecimento e MCP — pacote adversarial (22/10/2026)

- [E01-KH/MCP v0.4 — matriz de autoridade da Prumo, fontes, operações e oito gates pendentes](./E01_GOVERNANCA_CONHECIMENTO_MCP_PORTOES_v0_4.md).
- [E02-KH/MCP-AX v0.1 — 24 variações adversariais documentais](./E02_MATRIZ_ADVERSARIAL_CONHECIMENTO_MCP_v0_1.md): confirmações independentes, replay, auditoria protegida, privacidade e isolamento de conhecimento entre concessionárias.

**Precedência:** AL-IA-02/03 decidem que só a Prumo administra conhecimento, não há pesquisas abertas da F01/F02/F03 por padrão e nenhuma ferramenta pode nascer de um guia MCP. O corpus principal **continua SYN-01..70, 65 P0/5 P1 e 0 executados**; AX-01..24 **não** são 24 novos SYN, fixtures executáveis nem PASS. Contrato físico e aceite KH-R01..R08 dependem da S0/Prumo/segurança. E02-REV/FIX, E04 e E05 não foram liberados.

## E01/E03 — prontidão do fornecedor e aviso de descontinuação (22/10/2026)

- [E01-AUDIO v0.4 — modelos de voz, descontinuações previstas para 2027 e implicações F04/F05](./E01_ATUALIZACAO_MODELOS_AUDIO_DEPRECACOES_2026_10_22_v0_4.md): a shortlist antiga foi atualizada **documentalmente**, sem decidir endpoint ou modelo de produção.
- [E03-PRE v0.2 — conta API, controle de gastos, retenção, cache, segredos e checklist sem execução](./E03_PRONTIDAO_PRE_OPERACIONAL_SEM_CREDENCIAIS_v0_2.md): E03-A..H **permanecem adiadas**, sem criar projeto OpenAI, billing, credencial, sessão ou chamada paga.

**Regra vigente:** 70 SYN apenas documentados, 0 executados; revisão interfrentes E02 pendente; E04 exige autorização **expressa de implementação**; E05 requer liberação de custo/segredo/ambiente separada. Os achados da documentação oficial da OpenAI exigem revalidação no momento do laboratório.

## Auditoria editorial do gabarito E02 (22/10/2026)

[AUDITORIA E02-QA v0.1 — revisão dos 70 cenários](./E02_AUDITORIA_QA_GABARITOS_70_v0_1.md): foram corrigidos, nos [oráculos documentais v0.4](./E02_CADERNO_70_ORACULOS_E_OBSERVAVEIS_v0_4.md), os SYN-02/03/08/09 e SYN-27..32. Distribuição conferida: **70 IDs contínuos; 65 P0 e 5 P1**; **0 testes executados, 0 PASS medidos**. SYN-27/28 são testes transversais de protocolo, não apenas F01. SYN-31 (n8n) é **condicional**: rota não escolhida pede `NÃO_APLICÁVEL/JUSTIFICADO`, não PASS fictício.

**Alcance:** QA editorial desta rodada, **não** aceitação E02-REV/FIX, schema S0 ratificado ou permissão para E04/E05. As decisões dos donos nas issues #4/#6/#15 seguem abertas.

## Contrato tipado e erros da integração — E01-INT v0.4 (22/10/2026)

A frente OpenAI publicou o [**E01-INT v0.4 — contrato lógico F01/F02/F03, saída tipada e falha fechada**](./E01_CONTRATO_TIPADO_ADAPTADOR_FALHAS_v0_4.md). Ele descreve o que é **entrada autorizada da S0**, o que pode ser **proposta do modelo**, o que exige **revalidação e efeito exclusivo S0**, tratamento de `DENIED` antes de divulgar `STALE` e distinção entre resultado técnico, `sent` Meta e estado comercial. **[P/R]: não é schema físico, código, teste executado nem interface aprovada.** Issues de ratificação #4/#6/#15 seguem sem resposta nova; E02-REV/FIX permanecem abertas; E04 ainda depende de autorização expressa de implementação.

## Coordenação interfrentes: solicitações enviadas em 22/10/2026

As dúvidas da [E02-REV — sete decisões](./E02_RESUMO_DECISOES_PARA_RATIFICACAO_v0_4.md) foram encaminhadas aos donos por comentários rastreáveis em [CFI-01 issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4#issuecomment-6352881916), [CF-OP-02 issue #6](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6#issuecomment-6352882384) e [WA-22 issue #15](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/15#issuecomment-6352882892). **Comentário enviado ≠ aceite recebido.** Manter E02-REV aberta até manifestação formal dos respectivos donos; nenhuma mudança em contratos/branches alheias.

## E02: avanço documental de oráculos e evidências (22/10/2026)

**Novas referências da frente OpenAI:** [CFI-01E — manifesto lógico de histórico F03](./CFI_01_MANIFESTO_HISTORICO_F03_CANDIDATO_v0_1.md), [E02-FIX v0.4 — 70 oráculos com observáveis e negativos](./E02_CADERNO_70_ORACULOS_E_OBSERVAVEIS_v0_4.md), [E02-REV v0.4 — sete decisões objetivas a ratificar](./E02_RESUMO_DECISOES_PARA_RATIFICACAO_v0_4.md).

**Status:** 70 casos com EXPECTED textual e exigência de observabilidade, **0 testes executados**, nenhuma nova decisão interfrentes ratificada, nenhum schema físico implantado. Questões #4/#6/#15 permanecem abertas. A verificação documental **não** autoriza E04/E05 nem garante que a S0 já disponibiliza o histórico multimodal.

## Revisão cruzada E02-REV — 22/10/2026

A frente OpenAI consolidou **três pacotes candidatos de revisão entre frentes**, **sem ratificação pelos proprietários**:

- [CFI-01 v0.3 — F03: mapa S0/FV/S1/Meta e versões físicas pendentes](./CFI_01_CONCILIACAO_PONTE_F03_INTERFRENTES_v0_3.md).
- [CF-OP-02/C09 v0.3 — F02: planos, três relógios, Meta e perda técnica](./CF_OP_02_C09_CONCILIACAO_F02_INTERFRENTES_v0_3.md).
- [E02-REV v0.3 — critérios de aceite, owners, decisões abertas e gates](./E02_PACOTE_REVISAO_CRUZADA_E_GATES_v0_3.md).

**Estado:** pactuação S0/S1/FV/Meta/Prumo **PENDENTE**; E02-REV não aprovado, E02-FIX não fechado; 70 SYN documentados, 0 executados. PR #12 S0 tem apenas recibo/ponte local `VERIFIED_CONTRACT_PENDING`, sem payload histórico F03 ou aplicação; **não** contar prova PG17/GoTrue S0 como integração OpenAI. Gate G-FASE-DO-PROJETO continua bloqueando implementação E04 com “prossiga” genérico.

## E02 operacional v0.3 — segurança, conhecimento e testes documentais (22/10/2026)

Esta rodada avança **E01/E02 documental**, sem iniciar implementação. Fontes [DN]: AL-IA-02/03; regras candidatas [P/R] separam o que a frente OpenAI propõe do que depende de S0/S1/Meta/Prumo.

- [E01-KH v0.3 — Contrato lógico de conhecimento, bases, habilidades e MCP](./E01_CONHECIMENTO_HABILIDADES_E_MCP_OPERACIONAL_v0_3.md)
- [E02 v0.3 — Segurança, privacidade e gates operacionais](./E02_SEGURANCA_E_GATES_OPERACIONAIS_v0_3.md)
- [E02-MT v0.3 — Matriz SYN-01..70, correções SYN-08/SYN-09 e novos cenários](./E02_MATRIZ_REGRESSAO_OPERACIONAL_v0_3.md)
- [E02-FIX v0.3 — Dez exemplos de fixtures narrativas para posterior concretização](./E02_CADERNO_FIXTURES_DOCUMENTAIS_v0_3.md)

**Situação verificável:** 70 cenários **documentados** (32 históricos + 38 novos), 10 exemplificados, **0 executados**. Não confundir testes textuais com PASS; E02-REV/FIX não estão aprovados, E04 permanece condicionado à liberação **expressa de implementação** (G-FASE-DO-PROJETO). E05 ainda requer autorização de chave, orçamento e ambiente. Os arquivos antigos permanecem rastreáveis, mas discrepâncias funcionais seguem v0.3 e AL-IA.

## Contratos operacionais v0.3 — atualização iniciada em 22/10/2026 [P/R]

Foram publicadas **novas versões candidatas de implementação**, alinhadas às decisões mais recentes AL-IA. **Precedência de consulta:** AL-IA-00..08 (decisões [DN], limitações [R/V]) → versões operacionais v0.3 abaixo → versões v0.1/v0.2 históricas para rastreabilidade.

- [OAI-01 v0.3 — Porta S0↔OpenAI](./OAI_01_CONTRATO_OPERACIONAL_S0_OPENAI_v0_3.md)
- [OAI-05 v0.3 — F03, histórico e ficha](./OAI_05_F03_CONTRATO_OPERACIONAL_v0_3.md)
- [OAI-07 v0.3 — Desfechos, status e roteamento](./OAI_07_DESFECHO_ROTEAMENTO_CONTRATO_OPERACIONAL_v0_3.md)
- [OAI-08 v0.3 — F02 e cadeia pós-humana](./OAI_08_F02_POS_HUMANO_CONTRATO_OPERACIONAL_v0_3.md)
- [E01 v0.3 — Contrato funcional integrado](./E01_CONTRATO_FUNCIONAL_OPERACIONAL_v0_3.md)

**Situação real:** v0.3 atualiza contratos **da frente OpenAI**, mas **não é assinatura canônica S0**, código, teste executado, gasto autorizado ou alteração de outras frentes. Ainda requer ratificação CFI-01 (issue #4), CF-OP-02/C09 (issue #6), catálogo e versões S0, mídia/Meta e privacidade. OAI-06 áudio ainda segue como proposta anterior compatível sujeita a revisão. **E01/E02 não estão encerrados; E04/E05 não iniciados.** Não abrir credenciais ou API paga. Preservar documentos antigos, sem interpretar seus trechos superados como autorização.

## Atualização documental de alinhamento [DN] — 22/10/2026

O responsável pelo produto concluiu uma nova rodada de alinhamento sobre F01/F02/F03, ficha e histórico, status comerciais, MCP de Diretores, bases de conhecimento, instruções globais, comportamento F01, cache opcional, habilidades e vigência/pausa de campanhas. Esse alinhamento foi **registrado na própria frente OpenAI**, em documentação aditiva, com precedência explícita e diferenças para contratos anteriores; não altera contratos físicos nem concede autorização de deploy.

**Comece pelo [AL-IA-00 — Índice, precedência e escopo](./ALINHAMENTO_2026_10_22_00_INDICE_E_PRECEDENCIA_v0_1.md)**, que referencia:
- [AL-IA-01 — Jornada F01/F02/F03, conclusão humana, ficha e estados](./ALINHAMENTO_2026_10_22_01_JORNADA_F01_F02_F03_v0_1.md)
- [AL-IA-02 — Conhecimento, bases, pausa, cache, instruções e habilidades](./ALINHAMENTO_2026_10_22_02_CONHECIMENTO_CACHE_HABILIDADES_v0_1.md)
- [AL-IA-03 — MCP Diretor, guias semânticos e auditoria protegida](./ALINHAMENTO_2026_10_22_03_MCP_DIRETOR_GUIAS_AUDITORIA_v0_1.md)
- [AL-IA-04 — Matriz de deltas, conflitos, pendências e revisões cruzadas](./ALINHAMENTO_2026_10_22_04_RASTREABILIDADE_DELTAS_PENDENCIAS_v0_1.md)
- [AL-IA-05 — Histórico de ideias, hipóteses e frentes não ativas](./ALINHAMENTO_2026_10_22_05_HISTORICO_IDEIAS_E_LINHAS_NAO_ATIVAS_v0_1.md)
- [AL-IA-06 — Auditoria de fidelidade e completude (22/10/2026)](./ALINHAMENTO_2026_10_22_06_AUDITORIA_FIDELIDADE_E_COMPLETUDE_v0_1.md) — **ver achados corrigidos e pendências reais antes de implementar**
- [AL-IA-07 — Revisão cruzada: dependências de S0, Meta, S1, frontend e F03](./ALINHAMENTO_2026_10_22_07_DEPENDENCIAS_RELEVANTES_OUTRAS_FRENTES_v0_1.md) — **refina estrutura Meta da concessionária versus operação conduzida pela Prumo**
- [AL-IA-08 — Auditoria final da documentação da frente OpenAI](./ALINHAMENTO_2026_10_22_08_AUDITORIA_FECHAMENTO_DOCUMENTAL_FRENTE_OPENAI_v0_1.md) — **validar precedência, decisões, lacunas e limites antes da implementação**

**NOMENCLATURA E CANAIS:** **plataforma** = sistema ainda sem nome; **LiberaCred** = produto de crédito da instituição financeira. A Prumo, com autorização, **providencia e opera os canais na estrutura Meta de cada concessionária**, isolados por App/WABA/número/credenciais/catálogo; não deduzir propriedade jurídica ou portabilidade sem contrato. Ver AL-IA-01/07.

**ATENÇÃO À PRECEDÊNCIA:** em especial, as novas decisões **retiram edição de ficha pelo Consultor**, exigem acesso lógico F03 ao histórico completo da própria concessionária até o cutoff, permitem transições comerciais F03 **mediante S0** (exceto `vendido`), ampliam a intenção administrativa do MCP sem liberar alteração de sua auditoria e adotam **somente quatro campos globais para IA**. As seções e contratos datados de 18/10 abaixo continuam como registros históricos/candidatos quando divergirem; qualquer mudança nas frentes S0/Meta/Frontend exige conciliação do respectivo dono. Envio direto ao Banco segue **[V] expressamente adiado**. PR #3 permanece Draft e E04/E05 não foram abertos.


**Data:** 18/10/2026. **Branch:** feat/s2-openai-adapter-sintetico. **Estado:** planejamento contratual [P], sem integração operacional. Branch derivada de main; não contém código das branches S0 ou Meta.
**Regra de convivência:** NÃO transferir, cancelar, bloquear, reescrever ou assumir demandas dos PRs #1 (S0) e #2 (WhatsApp/Meta). Se uma dessas frentes já implementa algo relacionado a IA, a titularidade permanece com ela até decisão expressa posterior.

**Atualização de testes S0 isolados (19/10/2026):** o [PR #8 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/8) contém agora validador F03 de proveniência e versões com **30 testes sintéticos locais aprovados**, além do avaliador C09 conservador anterior. Os campos A/B/C e a anotação `asserted_fields` são SOMENTE gabarito fictício; nenhuma IA real, prova do Banco, persistência ou CI confirmada. **Esses testes pertencem ao laboratório S0 de ponte e NÃO concluem E04 ou E05 da frente OpenAI.** A assinatura CFI-01 #4 e extensão C09 #6 seguem pendentes, sem API OpenAI.

**Exceção de escopo concedida pelo responsável em 19/10/2026:** as frentes OpenAI e WhatsApp/Meta receberam autorização para propor/ajustar **partes específicas** da S0 que bloqueiem suas integrações, sem tomar posse do backend inteiro ou invadir arquivos da outra frente. A frente OpenAI abriu [PR S0 #8 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/8) numa branch **separada**, com base na branch S0 e somente dois adendos documentais para F03/CFI-01 e C09. **PRs #1/#2 não foram editados**, sem SQL, APIs, deploy ou merge. A cláusula anterior de não interferência continua válida para mudanças não autorizadas ou para a propriedade Meta de canais/callbacks. O contrato canônico ainda espera ratificação #4/#6.

## Objetivo particular desta frente

Preparar o acesso da plataforma técnica Prumo à API da OpenAI: entendimento de projetos e credenciais, contrato de chamada/retorno do provedor, configuração de segredo via ação MANUAL do responsável, limites, evidências e integração futura com o núcleo S0.

**Fora desta etapa:** gerar ou divulgar chave por automação, escrever segredos no GitHub, consumir API paga, ativar IA real, **programar fixtures/adaptador antes de gate expresso de implementação e fechamento do planejamento aplicável**, abrir conta/projeto/chave/faturamento API agora (adiado por decisão do responsável em 19/10/2026), implantar Edge Functions, modificar esquema, efetuar merges ou mudanças nas outras duas frentes. Qualquer operação futura no Supabase exige verificar o projeto exclusivo da Prumo, permissões da conta executora e autorização da mudança; não inferir indisponibilidade geral de ferramentas a partir de uma sessão de trabalho.

## Documentos nesta branch

1. **contrato-s0-openai-v0_1.md** — porta e fronteiras entre S0, OpenAI e Meta; v0.1 candidata, atualizada com as operações novas.
2. **OAI_05_CONTRATO_EXTRAÇÃO_PÓS_ATENDIMENTO_HUMANO_v0_1.md** — contrato específico `human_close_extract`, campos com evidência e persistência automática sob validação S0 [P/R].
3. **OAI_06_VOZ_AUDIO_E_MODELOS_v0_1.md** — contrato específico `speech_transcribe` / `speech_synthesize`, texto aprovado, voz e limites Meta [P/R/V].
4. **E01_CONTRATO_FUNCIONAL_MULTI_CAPACIDADE_v0_2.md** — visão integrada de F01–F05, segurança e autoria, com exemplos e semântica harmonizados com OAI-05/06.
5. **E01_PLANO_DE_AVALIACAO_MODELOS_E_VOZ_v0_1.md** — plano de benchmark dos modelos de texto, extração, transcrição e TTS sem escolha antecipada [P].
6. **provisionamento-credenciais-manual-v0_1.md** — emissão e armazenamento MANUAL da chave pelo responsável, destino seguro conforme runtime.
7. **matriz-dependencias-e-testes-v0_1.md** — titularidade preservada e cenários de teste.
8. **avaliacao-transporte-openai-direto-ou-n8n-v0_1.md** — conexão direta versus n8n ainda em aberto [R].
9. **AUDITORIA_CONTRATO_OAI_2026_10_18.md** — auditoria da fase de abertura e seus gates.
10. **MAPA_CAPACIDADES_E_PENDENCIAS_OPENAI_v0_1.md** — inventário que preserva também mídia visual/documentos como pesquisa futura sujeita a autorizações, governança de conhecimento, modelos e dependências, sem ampliar o escopo sem decisão.
11. **E02_POLITICAS_SEGURANCA_CRITERIOS_ACEITE_v0_1.md** — E02: segurança, privacidade, autoaplicação de campos com fonte, limites e gates propostos [P/R/V].
12. **E02_MATRIZ_CASOS_SINTETICOS_E_METRICAS_v0_1.md** — E02: 32 cenários de teste a implementar em E04, métricas, bloqueios críticos e comparação futura [P].
13. **OAI_07_DESFECHO_ENCAMINHAMENTO_PREFERENCIA_CANAL_v0_1.md** — esclarecimentos [D-NEGÓCIO] do responsável em 18/10 sobre fechamento humano, motivo/desfecho da conversa, todos os campos disponíveis, essenciais × opcionais, roteamento e avisos IA → humano, voz adaptativa e orçamento por lote; limites bancários [R/V].
14. **E03_PREPARACAO_CONTA_CREDENCIAL_GATES_v0_1.md** — checklist [P/R] de projeto API OpenAI, billing, credencial e armazenamento MANUAL no runtime homologado; E03 ainda pendente.
15. **OAI_08_CONTRATO_PLANEJADORA_POS_HUMANA_CF_OP_02_v0_1.md** — atualização CF-OP-02 [D-negócio/P/R/V]: recomendação de nova cadeia pós-humana, pedidos humanos, templates aprovados, rota de retorno e três relógios; sem executar envio nem C09.
16. **CFI_01_PROPOSTA_CONCILIACAO_ENVELOPE_F03_v0_1.md** — equivalência E01/OAI-05/OAI-08 e versão **candidata** do envelope F03 para revisão S0/OpenAI na issue #4; não homologado.
17. **E02_RASTREABILIDADE_CF_OP_02_v0_1.md** — ligação entre casos OAI, NC, SYN e CF2, com áreas proprietárias e limites de execução.
18. **AUDITORIA_POS_SANEAMENTO_CF_OP_02_2026_10_18.md** — controle dos 8 achados, correções documentais verificáveis e pendências de aceite S0/Meta.
19. **E02_PACOTE_REVISAO_CASOS_FICTICIOS_CFI_CF02_v0_1.md** — 16 exemplos sintéticos de entrada/saída F03, F02 pós-humana, três relógios e C09, aguardando homologação da assinatura e elegibilidade; zero testes implementados.
20. **E02_RUBRICA_DE_ACEITE_PRE_E04_CF_OP_02_v0_1.md** — rubrica candidata de avaliação pré-E04, separando revisão textual, ensaio stub e API real, com P0/P1, métricas, fonte e bloqueios [P/R]. Nenhum teste executado.
21. **E02_GABARITO_DOCUMENTAL_SYN_01_32_v0_1.md** — desenvolvimento documental dos 32 casos SYN com estímulos e expectativas fictícias, sem schema/fixture física ou teste executado [P/R].
22. **PLANO_EXECUCAO_E_CRITERIOS_DE_CONCLUSAO_v0_1.md** — roteiro E00–E08: somente E00 concluído; E01/E02 em revisão, E03 preparado documentalmente, E04–E08 não iniciados.

## Princípios de precedência

- A plataforma ainda NÃO tem marca comercial aprovada; LiberaCred é o produta instituição financeira.
- **Registro histórico de 18/10:** docs 00A, 13A, 21–23 e 41, com apoio dos docs 06/26/33/38/40, eram fontes anteriores. **Trechos dessas fontes foram superados por decisões funcionais posteriores**; consultar AL-IA-00/01/02/03/04/07/08 antes de tratar uma cláusula como vigente. Propostas [P], pendências [R] e validações [V] não são decisões [D].
- Exatamente oito estados comerciais; **nenhuma saída da OpenAI grava um estado diretamente**. A F03 pode, após conclusão humana, fundamentar transição automática **executada e validada pela S0** quando permitida, inclusive `perdido` por desistência explícita; **nunca `vendido`**, que é registro humano com prova. Envio bancário exige remessa real; negativa definitiva do Banco exige prova e ato humano. Vedações antigas genéricas estão superadas como intenção funcional, não como autorização física implantada.
- IA Vendedora e IA Planejadora estão no escopo; há ainda extrator pós-atendimento humano SILENCIOSO (nova orientação funcional, interface P/R) e capacidade futura de áudio/voz; **IA Analista autônoma está EXCLUÍDA**; ChatGPT/MCP administrativo é fluxo independente sob normas próprias.
- Concessionárias não compartilham contexto de cliente, histórico ou resultado. Handoff humano encerra definitivamente a IA Vendedora do caso.
- Somente o núcleo decide elegibilidade, permissões, persistência, status, handoff e intenção de envio; somente a frente Meta responde por transporte/callbacks WhatsApp.
- E02 reforça que JSON estruturado não prova veracidade: autoaplicação exige evidência explícita rastreável, campo permitido, versão atual e autorização S0. Dados reais e campos D3 permanecem dependentes de decisão e validação externa; requisitos de privacidade/retenção seguem sem homologação.

**Compatibilização com retorno pós-venda (19/10/2026):** doc.22 e novidades S1-002 exigem novo caso humano próprio quando cliente com venda histórica retorna, mantendo `vendido` e IA Vendedora bloqueada. OAI-08/E01 e matriz E02 agora incluem essa fronteira e fila protegida: F03 somente com conclusão válida do novo caso, F02 sem cadeia por inferência de venda passada. Regras físicas e testes permanecem [R/V], não implementados nesta branch. API OpenAI continua intencionalmente adiada.

## Referências

Projeto: pacote documental auditado em 17/10/2026 (00A, 06, 13A, 26, 33, 38, 40, 41) e branches PR #1 / PR #2 consultadas em 18/10/2026.
OpenAI projetos/chaves: https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform
OpenAI segurança de chaves: https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety
Supabase secrets para funções autorizadas: https://supabase.com/docs/guides/functions/secrets

**Nova orientação F03 [D-direção/R-interface, 18/10/2026]:** ao encerrar o atendimento humano, uma rotina OpenAI separada da IA Vendedora extrai informações declaradas e propõe preenchimento automático dos campos elegíveis; S0 valida/persiste sem exigir digitação rotineira do operador. A falta de informação permanece pendente, sem preenchimento fictício. Nenhuma tela/SQL/ação Meta foi assumida pela frente OpenAI. Também entram no contrato TTS (áudio de saída), STT (áudio de entrada) e avaliação por tarefa/modelo, sujeitos a provas e autorizações próprias.

**Emenda OAI-07 [D-NEGÓCIO; implementação P/R]:** quando operador clicar encerrar, analisar evidências e desfecho conversacional, preencher automaticamente TODOS os campos elegíveis que foram explicitamente informados, voltar ao humano apenas se faltar dado realmente essencial ou houver outra necessidade legítima de revisão e exibir motivo curto para CADA handoff IA → humano; somente campos exigidos e legalmente autorizados seguem para remessa. A modalidade áudio/texto adapta-se ao padrão reiterado e pedido explícito, sem inferir preferência por um único áudio. Venda/recusa bancária oficiais permanecem atos humanos com prova conforme 13A/21/41; classificação IA é hipótese, não mudança de status. Não há teto global de gasto em testes: exigir autorização de estimativa por lote. Ver OAI-07.

**Esclarecimento de resultado comercial [D-NEGÓCIO, 18/10/2026]:** atendimento “fechado” significa interesse confirmado e dados preparados para remessa, NÃO `vendido`. A OpenAI poderá sugerir `NEGOTIATION_READY_FOR_BANK_HANDOFF` com fonte, e S0 encaminha para operador de remessa conforme regras. Status `cadastro enviado ao operador` após fechamento HUMANO requer validação da transição pela frente S0, e `cadastro enviado ao banco` exige envio real com prova. `vendido` continua condicionado à confirmação bancária efetiva de venda/pagamento e marcação humana com evidência. Ver OAI-07 atualizado.

**E03 [P/R, adiamento deliberado 19/10/2026]:** o responsável decidiu manter a API OpenAI para a fase posterior de testes reais, quando a estrutura e os testes offline estiverem prontos. O checklist de conta, credencial e custos continua documentado, mas **não acionar agora** projeto/chave/billing/secret; não há obrigação de abrir conta para consolidar E01/E02. Não armazenar chave no Supabase por inferência enquanto n8n versus direto estiver pendente. Cada chamada paga futura ainda exige estimativa e aprovação específica.

**Registro histórico CF-OP-02 / OAI-08 (18/10/2026):** antes da decisão posterior de devolver a pendência primeiro ao Consultor/Gestor, F03 podia sugerir, com evidências, acompanhamento após conclusão humana ambígua; F02 só prepara NOVA cadeia de templates pré-aprovados quando S0 solicitar/autorizar, inclusive por pedido do operador. Caso humanizado permanece humano e planos incompatíveis pré-handoff NÃO são retomados. Três eventos independentes: conclusão humana, janela Meta +24h desde último inbound e C09 +24h desde template final efetivamente enviado. S0 deve homologar extensão C09 para fase humana elegível [R]; banco enviado/vendido não sofrem perda por silêncio. Contratos de coordenação: [PR #7](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/7), [issue #6](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6); assinatura F03 [issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4).

**Ponto de controle pós-auditoria (18/10/2026):** os 32 SYN e 16 EX são exemplos/GABARITOS TEXTUAIS, não fixtures executáveis. Duas descrições SYN de preferência/contradição e o exemplo F02 foram refinados para não inventar conflito nem permitir menos de 2 tentativas no caso de cliente já atendido. O roteiro E00–E08 é candidato e ajustável, subordinado à conclusão do planejamento global; E04/E05 não estão autorizados por publicação documental ou “prossiga” genérico. Ver auditoria pós-saneamento e gates do plano.

**Topologia OpenAI ↔ backend [R]:** chamada direta autenticada pelo runtime servidor/Edge Functions OU orquestração via n8n; nenhum caminho foi testado/selecionado para esta frente. O contrato de domínio deve ser independente da topologia. **Sem GO para operação real.** Mudanças em outra frente dependem da frente proprietária e de revisão cruzada.
