# S1-002 — preparação do marco de pausa: alinhamento, auditoria e higiene documental (20/10/2026)

> **[D] Atualização de nomenclatura (21/10/2026):** **diretor** substitui o nome de papel **responsável (da plataforma)**; **gestor** permanece **gestor**; **consultor** substitui **operador**. As competências permanecem iguais, e a estrutura técnica/identificadores ainda **não** foram renomeados. A terminologia antiga neste documento deve ser interpretada por esta equivalência. [Decisão normativa de nomenclatura](S1_002_DECISAO_NOMENCLATURA_PAPEIS_2026_10_21.md).


**Documento preparatório, não realização das três etapas.** A frente continua trabalhando na issue #10 em sandbox; quando o marco descrito abaixo estiver satisfeito, interromper novos incrementos S1 antes de iniciar a rodada de perguntas, a auditoria e o fechamento documental.

## Condição objetiva para a pausa

A pausa passa a fazer sentido após:
1. Pausa/retomada **somente do ingresso** com versionamento e conta/grants preservados — **aprovado exclusivamente no sandbox** [ISSUE10-01..11].
2. Prova sintética S0 de início humano, redistribuição S1 seletiva e concorrência de primeira resposta — **aprovado no sandbox** [ISSUE10-12..23 e ISSUE10R-01..04].
3. Transferência manual excepcional a membro da mesma equipe **sem grant geral**, com entitlement temporal e revogável **por caso** e RLS negativa sobre outras lojas/casos/mensagens/anexos — **pendente**, não habilitar sem provas.
4. Projeções S0 de indicador único: número de não lidas quando houver não lidas, bolinha sem número após leitura sem resposta; leitura do gestor separada da leitura do operador; controle de reassignment e dedupe — **pendente**.
5. Novo caminho gerencial autenticado de pausa/retomada no gateway GoTrue/HMAC, sem motivo e com versão/ACK; atualização/negação de funções legadas e regressão — **pendente**.
6. Contratos e evidências acima com CI e status restrito revisados, sem acesso à Meta ou Supabase hospedado — **pendente da conclusão dos itens 3–5**.

**Quando 1–6 estiverem concluídos em sandbox, congelar novos incrementos e realizar as três etapas**, sem proclamar produção GO.

## Etapa A — perguntas de alinhamento (não perguntar tudo agora)

Itens que **merecem confirmação expressa do responsável** depois do marco; não presumir respostas:

- Qual evento torna “atendimento humano iniciado” irrefutável: primeiro envio confirmado no WhatsApp, registro de ligação telefônica, atendimento presencial ou combinação? Qual fonte e prioridade em caso de latência da Meta?
- O gestor pode transferir manualmente para um operador **também pausado**? A pausa bloqueia apenas leads novos automáticos ou também o recebimento manual de casos já existentes?
- A permissão excepcional por caso expira ao fechar o atendimento, quando o destinatário sair da equipe, quando outro receber o caso ou por prazo específico? Quem pode revogá-la e qual efeito sobre leitura de histórico?
- Ao assumir caso de outro operador, o novo titular herda não lidas anteriores ou inicia com contador próprio? Supervisores possuem leitura independente e visualizam quais detalhes?
- Uma notificação visual pendente após leitura sem resposta deve cessar com qualquer resposta humana, com resposta **confirmada pelo provedor**, ou com sinal de resolução validado pelo núcleo?
- Quando a pausa é aplicada e existem casos sem substituto, o produto deve exibir aviso, fila de atenção gerencial ou apenas manter a titularidade sem sinalização adicional?
- A chefia única ativa por operador, introduzida como hipótese técnica de I11, é requisito de negócio ou podem coexistir múltiplos gestores com poderes sobre o mesmo operador?

Todas essas perguntas devem apresentar opções, consequências e recomendação técnica na futura rodada, sem confundir decisão do usuário com hipótese.

## Etapa B — auditoria geral da frente

Checagem de requisitos vigentes contra migrations **históricas** I1–I31, novas fixtures ISSUE10, políticas RLS públicas e SECURITY DEFINER/INVOKER, autenticação GoTrue, custódia HMAC, retries/nonce, isolamento de concedentes, unicidade de titular, lock ordering, efeitos dos gatilhos I2/I6, dados cross-store, revogação, erro sem vazamento, concorrência e casos terminais. Incluir dependências S0 (lead, ciclo, mensagem, conversa, evento humano, leitura/estado de resposta), APIs e frontend. Destacar **testes antigos aprovados mas semanticamente superados**.

Não afirmar auditoria geral aprovada sem executar inventário de migrações, revisão de código e regressão representativa. Registrar classificação de risco: bloqueante, importante e futuro, sempre com proprietários e critérios de aceite.

## Etapa C — documentação e saúde técnica

Criar mapa de decisões [D], hipóteses [P], requisitos não resolvidos [R], riscos e dependências; remover contradições de **status atual**, sem apagar documentação histórica/evidências; estabelecer qual arquivo é o contrato vigente por domínio, cross-links issue/PR/CI/SHA; consolidar inventário de comandos e fontes de autoridade; revisar nomes de I31/I32 e numeração de fixtures 053/054; separar claramente **sandbox comprovado** de **produção não homologada**.

Ao final, entregar um sumário executivo de riscos bloqueantes, decisões pendentes e próximo incremento recomendado. Não atualizar porcentagem global sem métrica de projeto validada.

## Situação atual e segurança

- [Issue #10](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/10)
- [CI da seleção e corridas #39506166135](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39506166135), **ISSUE10-01..23 e ISSUE10R-01..04 PASS** em PostgreSQL 17 descartável.
- [Documento S0/S1 e fronteira](S1_002_ISSUE10_MARCO_S0_PROVA_REDIS_E_REVISAO_2026_10_20.md)

**NO-GO produção / merge / deploy**, PR #5 Draft. Nenhuma intervenção na branch S0 base nem no Supabase hospedado. Hardening do witness I31 permanece em backlog até fechar o pacote de negócio e executar a pausa de revisão.

## Atualização do marco — avanço de 20/10/2026, sem antecipar a pausa

Os itens **3 (transferência excepcional por caso)** e **4 (projeções de leitura/resposta e supervisão)** foram concluídos **como contratos de sandbox**, com regressões negativas, sem promover migrations operacionais, Meta ou UI:

- [Exceção manual I35](S1_002_ISSUE10_EXCECAO_POR_CASO_RLS_2026_10_20.md): [CI #39516209628 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39516209628), EX55-01..20 PASS, isolamento RLS por caso/conversa/mensagem, ausência de grant geral, revogação e proteção conservadora do reconciliador I3.
- [Projeção de mensagens S0 I36](S1_002_ISSUE10_INDICADOR_MENSAGENS_S0_2026_10_20.md): [CI #39517258320 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39517258320), MSG56-01..18 PASS, estados COUNT/DOT/NONE e visitas de gestor independentes do operador. Nesse mesmo CI rodaram EX55-20/20, ISSUE10-23/23 e ISSUE10R-4/4.

**Falta o item 5: novo contrato do gateway gerencial assinado, sem motivo e com revisão CAS, atendendo GoTrue/HMAC e negando rotas legadas.** Depois de testá-lo, verificar o item 6 e preparar o relatório de congelamento. Na etapa A da pausa, pedir confirmação das ambiguidades de negócio (destino pausado, herança de leitura e validade/expiração da exceção). A integração real Meta, confirmação de entrega e S0 ao vivo não são pré-requisito para o **marco de auditoria de sandbox**, mas permanecem gates de produção.

**Aviso:** as seções anteriores deste documento eram o planejamento de 20/10 e registravam 3–5 pendentes. Este adendo atualiza o estado auditável sem sobrescrever a fotografia histórica.

## Duas definições confirmadas antes da rodada futura de perguntas

- **Decisão fechada:** pausar a distribuição não suspende a conta nem o acesso à plataforma. Operador pausado segue podendo consultar e responder seus casos não redistribuídos. A ausência de substituto mantém a atribuição. Esta pergunta **não deve ser repetida** na futura reunião de alinhamento.
- **Decisão de UI ainda aberta, sem necessidade de pergunta imediata:** `COUNT` (não lidas) e `DOT` (lidas sem resposta) não precisam de cores diferentes. Mesmo esquema de cores ou cores distintas são opções válidas; a semântica e ausência de número na bolinha são o contrato funcional, não a paleta.

## Marco formal atingido — congelamento funcional de S1-002 em sandbox

Em 20/10/2026 (execuções CI registradas em 21/10 UTC), o último pré-requisito de laboratório, **I37 gateway GoTrue/HMAC de intake-only**, foi comprovado por [CI #39526190841 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39526190841), código SHA `bb1e61bb4bd9c0d65f1cc33d17530fe689a6c57c`, 138 unitários e 148 marcadores E2E (132 históricos e 16 do intake).

**Os seis itens de laboratório acima têm agora contrato, testes e evidências rastreáveis.** Itens 3 e 4 já haviam sido aceitos nos ensaios PG17 ISSUE10 (EX55 20/20 e MSG56 18/18). Em I37, o gateway usa GoTrue real **descartável** e não rota antiga de suspensão; identifica `INTAKE_PAUSED`, `INTAKE_RESUMED`, `ALREADY_APPLIED`, `CONFLICT` e `DEFERRED_S0_PROOF`. A identidade do operador, sua conta e concessões permanecem ativas durante pausa do intake, e o frontend não deve sinalizar redistribuição concluída antes de prova e confirmação S0.

**A partir deste marco, interromper novos incrementos funcionais S1** e executar o processo combinado, nesta ordem:

1. **Alinhamento com o responsável:** pedir somente respostas ainda não definidas (destino já pausado em transferência manual, herança de leitura após mudança de titular, natureza da confirmação de contato humano, revogação excepcional e chefia múltipla), apresentando alternativas e trade-offs; não reabrir decisão fechada sobre acesso do pausado ou obrigatoriedade de cores diferentes.
2. **Auditoria geral técnica S1/S0:** inventariar migrations históricas, funções/fachadas, teste RLS cross-store, anti-concorrência, autenticação GoTrue, HMAC, signer/witness, contratos S0, regressões semânticas e caminhos legados. Não presumir que resultados E2E do sandbox implicam segurança em produção.
3. **Higiene e consolidação:** reconciliar contratos vigentes vs histórico I11/I12, revisar divergências, fontes de verdade, requisitos abertos, issues/PR/CI/SHA e classificação de risco, consolidando documentação recuperável.

**Gates de produção ainda BLOQUEADOS:** Meta/WhatsApp e contato humano confirmado realmente, governança de anexos/documentos, UI e leitura real, migrations operacionais, isolamento de domínios de segurança/KMS/testemunha I31, DR, homologação de operações humanas, revisões de Security Definer, execução distribuída, usuários/clientes e autorização de deploy. O reconhecimento do marco significa **pausa para revisão**, jamais merge ou GO de produção.

**PR #5 permanece Draft, base S0 não modificada, banco Supabase hospedado intocado.** Não registrar percentual global de conclusão.
