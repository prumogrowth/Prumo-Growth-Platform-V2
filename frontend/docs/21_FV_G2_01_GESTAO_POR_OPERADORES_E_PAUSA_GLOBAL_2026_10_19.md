# FV-G2-01 — Gestão por equipes de operadores, pausa de distribuição e concessões

Data: 19/10/2026. **Fonte de decisão [D]: orientação direta do responsável nesta conversa**. Este documento prepara as telas G1/G2/G3, **não é contrato físico S0/S1, não implementa autorização**. Divergência interfrentes registrada na [issue #9](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/9).

## Diretrizes de negócio comunicadas

1. **Gestor supervisiona operadores da Prumo, não concessionárias.** G1 pode gerir cinco pessoas; G2, outras três. Uma pessoa pode atender A+B ou também C segundo as concessões aprovadas pelo responsável.
2. O gestor pode **pausar temporariamente a entrada de novos leads PARA UM OPERADOR de sua equipe**. Se a pessoa atende A+B, a pausa alcança ambas; o gestor NÃO escolhe pausar só A ou só B. Enquanto pausada, novas atribuições à pessoa devem cessar, cabendo ao backend redistribuir a carteira operacional elegível aos demais destinatários autorizados. Os casos históricos permanecem íntegros.
3. **Somente o responsável define quais concessionárias cada operador/equipe pode receber.** Ele pode habilitar C para operadores selecionados que já atendem A+B. O gestor não adiciona/retira essas concessões, não amplia sua própria equipe e não cria profissionais.
4. **Pausa de recebimento não é revogação de concessão nem desligamento de conta.** A experiência visual deve separar disponibilidade para novos leads, acesso de login e elegibilidade A/B/C; não esconder/retirar todos os casos sem projeção S0 autorizada.
5. A distribuição e eventual redistribuição são competências do S0/S1-002. O browser somente exibe quem está sob gestão, as concessões de leitura permitidas, os pedidos, conflitos e confirmações do backend.

## Matriz visual candidata

| Ação | Responsável | Gestor de operadores | Operador |
| --- | --- | --- | --- |
| Criar/remover definitivamente gestor ou operador | Permitido conforme alçada | Não | Não |
| Definir gestores e membros da equipe | Autoriza | Sem autoconcessão | Não |
| Conceder/retirar elegibilidade de loja A/B/C | Autoriza | **Não** | Não |
| Pausar novos leads de operador sob sua equipe | Pode solicitar conforme alçada | **Sim, sobre a pessoa em todas as lojas concedidas** | Não |
| Remanejar carteira operacional decorrente da pausa | Núcleo S0/S1 processa | Solicita/acompanha, sem decidir lojas destino | Não |
| Ver monitoramento operacional | Conforme concessões | Somente projeções autorizadas da própria equipe e restrições de lojas/tenant | Própria carteira |

O gestor continua impedido de operar como atendente sem atribuição explícita; D2 por **equipe** não concede D3/D4 bruto. A política exata de intersecção entre equipe e concessões de loja ainda é [R] da S0/S1.

## Implicações para telas futuras

**G1 — Equipe e fila:** entrada principal por gestores → operadores sob gestão, com cartão individual (ativos, temporariamente indisponíveis, novos leads pausados, casos a redistribuir). Concessionárias são metadados/escopo, não carteira de gestão do gestor. Somente exibir casos efetivamente permitidos pela S0.

**G2 — Distribuição:** ação **“Pausar recebimento de novos leads”** no operador inteiro, não por concessionária. Exibir lojas elegíveis da pessoa **somente leitura**, motivo operacional mínimo, período solicitado (sem documentos ou diagnósticos médicos) e feedback `REQUESTED / APPLIED / CONFLICT / FORBIDDEN` derivado da S0. Redistribuição mostra andamento e fila protegida. Reativar somente por regra definida e confirmada pelo S0; data prevista não significa comando automático aprovado.

**G3 — Monitoramento:** carteira da equipe, operadores com pausa, redistribuições aguardando elegibilidade, atrasos e histórico de decisões. Não inventar status comerciais adicionais. Sem gráficos de produtividade que comparem pessoas não concedidas ao gestor.

**G4 — Lotes:** lotes por origem/loja autorizada, mas distribuição limitada às elegibilidades **fixadas pelo responsável**. Gestor nunca seleciona “de qual concessionária o operador passa a receber” por edição local.

## Divergências conhecidas e bloqueios de implementação

O contrato [S1-002/I10](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s1-002-equipe-prumo/docs/S1_002_I10_AUTORIDADES_RESPONSAVEL_GESTOR_2026_10_19.md) dizia gestor sob concessão de **concessionária**, podendo pausar A sem pausar B; havia leitura D2 de toda a loja. Isso entra em conflito com a orientação mais recente. FV-01, mapa visual e as fixtures atuais também exibem supervisão por concessionária. **Não homologar o modelo antigo como a regra nova.**

Devem ser revisados por S1-002/S0 antes de criar fluxo real: entidade de equipe, regra de leitura D2 por operador, operador novo com A+B+C, política de indisponibilidade global, remanejamento dos casos ativos por loja sem perda histórica, destinatários em outras equipes, política de encerramento da pausa, Auth/RLS e comandos C11. Filtros visuais não são autorização.

## Testes de aceite candidatos para a frente visual

- Gestor G1 vê seus cinco operadores; G2 vê seus três, sem cruzar carteiras, mesmo quando as equipes compartilham concessionária.
- G1 pausa operador que atende A+B: a UI não oferece seletor A/B, reflete solicitação e só declara pausa após retorno S0.
- A lista de lojas do operador é somente leitura para G1/G2. Só a concessão aprovada pelo responsável habilita C.
- Pausa não altera status comercial, matrícula, login ou histórico por inferência. Redistribuição preserva a concessionária do caso; nenhum elegível → fila protegida.
- Gestor não faz inclusão/desligamento definitivo nem habilitação unilateral de C, e não ganha permissão D3/D4 por gerenciar a pessoa.
- Duas gestões concorrentes sobre a mesma pessoa, revogação de gerente, fim de ausência e mudança A/B/C exigem controle de versão e resposta explícita da S0.

**Estado:** preparação documental da experiência. Nenhum endpoint, SQL, schema, RLS, comando de pausa, concessão ou interface funcional de gestão foi aprovado/implantado por este arquivo. A issue #9 acompanha a conciliação, sem suspender o desenvolvimento das demais partes independentes.
