> **NOMENCLATURA VIGENTE [D-NOM-01] — 21/10/2026:** o papel anteriormente chamado **responsável** passa a chamar-se **Diretor**; **gestor** permanece **Gestor**; **operador** passa a chamar-se **Consultor**. A mudança é somente de nomes, sem alteração de alçadas, código ou permissões. Palavras genéricas como “responsável pelo caso” não mudam automaticamente. Ver [decisão de nomenclatura](./37_D_NOM_01_NOMENCLATURA_DIRETOR_GESTOR_CONSULTOR_2026_10_21.md); terminologia abaixo pode refletir a data original do texto.

# FV-DOC-01 — Decisões vigentes de operação: gestores, operadores, leads, fila e IA
**Corte:** 21/10/2026. **Natureza:** consolidação documental [D], aprovada pelo responsável nesta conversa, **não** contrato físico nem declaração de funcionalidade implantada. **Escopo:** frente visual; referências para pactuação S0/S1. Não altera Supabase, migrations, permissões, código ou integrações.

## Legenda e precedência
- **[D]** decisão expressa de produto; **[T]** integração/contrato técnico ainda pendente; **[V]** capacidade externa não verificada; **[H]** redação histórica substituída, preservada para auditoria.
- Este documento prevalece **somente nos temas D-AL-01 a D-AL-10** sobre redações anteriores incompatíveis do frontend (especialmente FV-G2-01/21, FV-UI-014/32), S0-043 e contratos S1 I11/I12 históricos. Outros assuntos continuam regidos por D41, 13A, 21–23, 00A, DEC-WA-05 e documentação específica. Um documento novo não reescreve nem homologa código de outra frente.
- **Não misturar**: um *lead novo sem titular*, um *caso já atribuído retido durante pausa*, uma *transferência manual* e o *handoff da IA para humano* são situações distintas.

## D-AL-01 [D] — Pausa de novos leads não suspende conta
O gestor pode pausar ou retomar somente o **recebimento de novos leads de operador de sua equipe**, em todas as concessionárias concedidas à pessoa, com **confirmação simples, sem motivo/atestado/data/duração**. A conta permanece ativa; o operador pode consultar, responder e conduzir **todos os casos ainda atribuídos a ele**, respeitando direitos operacionais e comerciais normais. Pausa não revoga concessionárias, acesso de login, histórico ou atribuições. Criar, bloquear ou revogar contas e configurar grants gerais é responsabilidade dos **responsáveis** da plataforma, não do gestor.

## D-AL-02 [D] — Redistribuição automática de caso EXISTENTE durante pausa
Apenas casos ativos **sem primeiro contato humano efetivamente comprovado** são candidatos à movimentação automática. O destinatário deve ser **outro operador da MESMA equipe do pausado**, com conta ativa, disponível para entrada de novos leads e com concessão geral à concessionária do caso. Caso com contato humano comprovado **permanece com o titular** até decisão manual individual. Se não houver destinatário, o caso **CONTINUA ATRIBUÍDO ao pausado**; não cai em fila sem titular e não cruza equipe. Evidência ausente/desconhecida implica **manter**, não presumir autorização. Retomada não recolhe automaticamente casos transferidos.

## D-AL-03 [D] — Transferência manual para membro da própria equipe sem grant geral
Gestor pode transferir **caso individual** a outro membro de sua equipe mesmo sem concessão geral à loja. Com a transferência **validada pelo backend**, o novo titular obtém **somente os acessos operacionais necessários àquele caso**, sujeitos aos limites já aprovados de D2, D3, D4, anexos e etapas financeiras. Não recebe livre acesso aos demais casos nem grant da concessionária. Quando deixa de ser titular, a exceção de operação é encerrada; histórico/auditoria continuam preservados. Garantia de escopo, revogação, expiração/revalidação e RLS são [T] da S0/S1, jamais um privilégio criado pela UI. Transferência manual permanece dentro da equipe, sem autorização de atravessar equipes.

## D-AL-04 [D] — O que prova atendimento humano iniciado
Exigir **evento de interação humana efetiva confirmado tecnicamente pelo sistema**, por exemplo uma mensagem enviada pelo operador e aceita/confirmada pelo núcleo. Não contam: atribuição, leitura, abrir conversa, diálogo apenas da IA ou tentativa de contato. **Não haverá registro manual** de ligação externa, visita presencial ou atividade fora da plataforma como prova de atendimento. Possível chamada pela **integração oficial WhatsApp/Meta** pode futuramente contar **somente** se a capacidade existir [V], estiver implementada e o sistema comprovar ligação **atendida**, não apenas tentada. Essa integração não faz parte da entrega atual. Não inferir prova de mensagens textuais exibidas no navegador, status comercial ou tempo.

## D-AL-05 [D] — Leads NOVOS podem ser distribuídos entre equipes
A alocação regular de **novos leads** deve considerar operadores elegíveis para a concessionária **mesmo que pertençam a equipes distintas**, desde que ativos, recebendo novos leads e com concessão válida para a loja. Se o único elegível da equipe A pausar, outro elegível na equipe B pode receber mais leads daquela loja. **Não aplicar a D-AL-02**, que proíbe cruzar equipe apenas ao redistribuir automaticamente **carteira já atribuída** de pessoa pausada. Equidade, prioridades e algoritmo de balanceamento permanecem [T].

## D-AL-06 [D] — Sem operador elegível: fila compartilhada de gestores autorizados
Lead novo que precise de atribuição humana, sem destinatário elegível, entra em **fila pendente sem titular humano** acessível a **todos os gestores autorizados à concessionária**. Havendo Marina e Daniel autorizados à mesma loja, **ambos** podem visualizar a fila. Um gestor pode assumir o atendimento para si ou atribuir individualmente a integrante de **sua própria equipe**, observando a exceção por caso de D-AL-03 quando cabível. O primeiro gestor cuja assunção for **confirmada atomicamente** fica titular; dois gestores não podem assumir o mesmo atendimento [T]. Nenhum gestor recebe leads automaticamente só por ser gestor. A fila compartilhada não concede acesso global a todas as lojas a gestores não autorizados. **Não confundir** esse lead pendente com caso existente mantido com o pausado pela D-AL-02.

## D-AL-07 [D] — Operador volta: pendentes sem titular são distribuídos automaticamente
Quando surgir novamente operador elegível, os leads ainda na fila compartilhada **sem titular** entram automaticamente na distribuição regular, com grants e disponibilidade revalidados [T]. Caso já assumido por gestor ou operador **não é retirado automaticamente**. Não reverter transferências passadas nem duplicar atribuição em corrida concorrente.

## D-AL-08 [D] — A IA Vendedora NÃO gerencia a plataforma
A IA que fala com o cliente recebe o contexto **necessário apenas ao atendimento**, **não** consulta quantos operadores existem, quem são, equipes, disponibilidade, concessões, gestores ou regras internas de distribuição. Ela atende normalmente **mesmo sem operador disponível**. Quando o fluxo exige humano, o sistema sinaliza handoff; **núcleo operacional Supabase + automações autorizadas**, não a IA, decide atribuir operador ou colocar em fila. Não esperar disponibilidade humana para iniciar a fase que compete à IA. Após handoff, respeitar a regra anterior de interrupção da IA naquele caso. **Fila pendente é sobre alocação humana**, não impedimento à IA de conversar.

## D-AL-09 [D] — Um único indicador de atenção por conversa
Mensagem do cliente não lida pelo operador titular: uma bolinha com **quantidade**. Lida pelo titular e ainda sem resposta humana: **a mesma bolinha muda de cor e perde o número**. Com resposta efetiva e sem nova pendência, desaparece. Gestor lendo como **supervisor** não confirma leitura por conta do operador; gestor **formalmente titular** atua como operador daquele caso. Não colocar SLA/cronômetros/ordenação por atraso na caixa operacional; métricas podem ser usadas futuramente em dashboard próprio. Paleta de cores final continua sem decisão.

## D-AL-10 [D] — Supabase, não Firebase
A palavra **Firebase** mencionada nesta conversa foi erro de transcrição. A tecnologia de núcleo continua **Supabase**. Não inferir mudança de infraestrutura, nem conexão privilegiada Meta via navegador. Integrações Meta/Supabase e automações seguem limites e validação das frentes responsáveis.

## Distinções fundamentais para implementação
| Operação | Destinatário entre equipes? | Grant geral de loja no destinatário? | Titular se não houver elegível? |
|---|---|---|---|
| Distribuir **novo lead** | **Sim**, elegíveis de qualquer equipe autorizados à loja | **Sim** | **Não**: fila de gestores autorizados |
| Redistribuir **caso existente** sem contato, após pausa | **Não**, só mesma equipe | **Sim** | **Sim**, conserva operador pausado |
| Caso existente com contato ou sem prova | **Não automaticamente** | Não aplicável | Mantém titular |
| Transferir **manualmente** para integrante da equipe | **Não**, dentro da equipe do gestor | Pode usar exceção **somente por caso** [T] | Sem movimentação automática |
| Gestor assumir lead da fila | Fila visível a gestores **autorizados à concessionária** | Autoridade gerencial por loja/caso [T] | Não há titular até confirmação |
| Retomar e distribuir pendentes | **Sim**, distribuição regular | **Sim** | Continua na fila se ninguém elegível |

## Regras anteriores que NÃO são revogadas
- Existem **oito status comerciais canônicos**; pausa, fila, leitura, contato confirmado e pendência são dimensões **técnicas distintas**.
- Equipe gestora é formada por profissionais **da Prumo**, não funcionários das lojas. Responsáveis gerenciam contas, papéis e grants; gestor supervisiona sua equipe e pode atuar como operador **quando formalmente titular**.
- Gestor em supervisão pode ver conversas D2 de seu escopo autorizado, mas não recebe D3/D4 brutos por esse motivo. Handoff IA/humano, cadastro, remessa, venda, recusa e retorno pós-marco preservam os contratos financeiros e os limites de prova já definidos.
- **DEC-WA-05**, registrada na S0 em 18/10, determina **titularidade do ambiente Meta/App/WABA/números por concessionária**, com Prumo integradora autorizada; textos de 17/10 sobre canais/Apps da gestora são **históricos** para essa dimensão. A homologação Meta real segue [V]. É decisão documental S0 anterior, não uma autorização nova concedida neste alinhamento.
- A IA Vendedora não se confunde com a IA de melhoria de atendimento; a última não recebe autorização para mudar a própria governança ou direitos do núcleo por inferência.

## Dependências [T] e estado real
Faltam contratos aceitos e testes de **prova do primeiro contato**, comandos de intake, seleção/distribuição, fila compartilhada, assunção única com controle de concorrência, transições automáticas ao recuperar disponibilidade, autorização excepcional por caso com **RLS/GoTrue e anexos D3/D4**, auditoria, versões, idempotência e falha segura. Chamadas Meta [V] ficam para avaliação futura. IA nunca recebe informações de equipe como substituto de autorização S0/S1.

**Estado da frente:** FV-UI-015/016 são **protótipos sintéticos**. S0-043 é política pura preparatória; S1 já registrou retificações na issue #10, sem que isso prove implantação ponta a ponta. FV-UI-013 continua **sem homologação formal**, índice 19F permanece **69/100**. Esta entrega é **documentação somente**, sem merge, deploy, migração, banco remoto ou alteração do código.

## Fontes rastreáveis
- [FV-G2-01 histórico](./21_FV_G2_01_GESTAO_POR_OPERADORES_E_PAUSA_GLOBAL_2026_10_19.md), [FV-UI-014](./32_FV_UI_014_INDICADOR_UNICO_E_PAUSA_SELETIVA_2026_10_20.md), [FV-UI-015](./33_FV_UI_015_INDICADOR_OPERACIONAL_E_CONFIRMACAO_2026_10_20.md), [FV-UI-016](./34_FV_UI_016_MARCO_PREVIA_G2_2026_10_20.md).
- [S0-043](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-fundacao-prumo/docs/S0_043_PAUSA_SELETIVA_E_INDICADOR_CONVERSA_2026_10_20.md), [DECISÕES E GATES S0](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-fundacao-prumo/docs/DECISOES_E_GATES.md), [S1 issue #10](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/10).
- Fontes históricas basais: pacote consolidado de **55 documentos de 17/10**, especialmente **00A**, **13A**, **31**, **41**, e documentação específica de Meta. O histórico permanece intacto; conflitos estão mapeados separadamente na auditoria documental FV-DOC-02.
