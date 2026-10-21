# S1-002 — preparação do marco de pausa: alinhamento, auditoria e higiene documental (20/10/2026)

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
