> **LEITURA ATUALIZADA — 21/10/2026:** Além da pausa seletiva, novas decisões estabeleceram **novos leads entre equipes**, fila compartilhada de gestores autorizados à loja, distribuição automática na retomada, ausência de registro manual de chamadas e isolamento da IA Vendedora de informações de equipe. O indicador foi conectado **somente ao app sintético** em FV-UI-015; afirmação antiga de 'não conectado' descreve o estágio anterior. Para decisões vigentes de pausa, distribuição, filas, acesso por caso, comprovação humana e IA, consultar **[FV-DOC-01](./35_FV_DOC_01_DECISOES_VIGENTES_ALINHAMENTO_2026_10_21.md)**; divergências descritas em **[FV-DOC-02](./36_FV_DOC_02_AUDITORIA_AMBIGUIDADES_E_PRECEDENCIA_2026_10_21.md)**. Trechos abaixo permanecem como histórico técnico da sua data, sem substituir decisões posteriores.

> **Incremento sintético posterior FV-UI-015 (20/10/2026):** o indicador único e a confirmação G2 estão agora conectados **à interface demonstrativa em memória**, com testes Node/Chromium nativos registrados em [FV-UI-015](./33_FV_UI_015_INDICADOR_OPERACIONAL_E_CONFIRMACAO_2026_10_20.md). Isso **não** implementa leitura confirmada, pausa ou redistribuição operacional no S0/S1. Abaixo permanece o contrato de domínio para integração futura.

# FV-UI-014 — Indicador único e pausa seletiva: decisão funcional (20/10/2026)

**Fonte [D]:** decisão direta do responsável nesta conversa. **Escopo:** somente documentação e contratos candidatos da frente visual. Design/cores finais ficam para uma etapa posterior. Não alterar S1, não criar acesso real à Meta, S0 ou Supabase.

## 1. Um único indicador por conversa

- **Estado A: mensagens do cliente não lidas pelo operador:** exibir **uma bolinha colorida com a quantidade** de mensagens recebidas não lidas. Cores não são definidas neste contrato.
- **Estado B: mensagens visualizadas pelo operador sem resposta humana efetiva:** o **mesmo indicador** muda de cor e **deixa de mostrar o número**. Os estados A/B são mutuamente exclusivos. A leitura pelo **gestor** é passiva, não zera não lidas do operador, não registra leitura em seu nome e não equivale a resposta.
- **Após resposta humana confirmada:** o indicador de pendência desaparece, desde que não exista nova mensagem do cliente não lida. A projeção deve vir de fonte S0 minimizada, individualizada por profissional e caso, sem que o navegador deduza entrega pela API da Meta como resposta efetiva.
- **Não exibir no fluxo operacional** cronômetros, SLA, fila por tempo sem resposta ou métricas extensas; dados de monitoramento poderão existir na fonte e futuramente aparecer num dashboard próprio. Também não declarar mensagem respondida simplesmente porque foi marcada como lida.
- **Contrato candidato offline**: `frontend/visual/conversation-attention.mjs`, sem rede, sem persistência e **ainda não conectado ao app**. `stageConversationAttention` exige contagem inteira e sinalização explícita de leitura/resposta; `canStageReadAcknowledgment` rejeita tentativa de confirmação pelo gestor ou não titular. Em operação real o S0 verificará identidade, versão, atribuição e permissão.
- Casos sintéticos/estado vigente do app continuam sem novos privilégios; o badge final será integrado quando o S0/S1 oferecer uma projeção de leitura/pendência confiável.

## 2. Pausa e retomada dos novos leads

- Somente **responsáveis** criam, removem definitivamente ou bloqueiam contas de operadores/gestores. O **gestor** apenas pausa/retoma **recebimento de novos leads** dos operadores de sua equipe.
- Dois botões: `Pausar novos leads` e `Retomar novos leads`, cada um com confirmação; mudar estado **somente após confirmação do núcleo**. Não solicitar motivo, atestado, justificativa, duração ou data de retorno. Auditoria técnica mínima de autoria é necessária, não motivo pessoal.
- A pausa vale para **todas** as concessionárias concedidas ao operador; não revoga grants, não desativa a conta e não muda os oito estados comerciais.
- Na pausa, **somente casos sem primeiro contato humano efetivamente comprovado** são candidatos à redistribuição automática. Abrir, ler ou receber caso não é atendimento iniciado, assim como conversa anterior com IA não é contato humano. Critério de prova: primeiro evento de contato humano persistido pelo S0 — candidato técnico para validação com os demais canais.
- Destino **exclusivamente outro operador da equipe do gestor**, ativo, disponível para novos leads e com concessão regular à concessionária de origem. Se não existir tal pessoa, o caso **continua atribuído ao operador pausado**, sinalizado ao gestor. Não mover automaticamente para equipe externa nem criar fila que retire a titularidade.
- Caso com contato humano iniciado **permanece atribuído** e só pode ser transferido por decisão individual do gestor. O retorno não restaura casos transferidos automaticamente.
- O gestor pode transferir manualmente para **pessoa da própria equipe sem grant geral da concessionária**. Essa é uma exceção de escopo **somente daquele caso**, dependente de concessão efêmera/restrita, revogável e auditada de S0/S1 antes de qualquer acesso a conteúdo; jamais autoriza livre trânsito pelos outros casos da loja.
- Em todas as redistribuições: preservar a loja de origem, histórico, identidade de contato, versão da atribuição e unicidade de titular, aplicar idempotência e revalidar equipe/loja/autoridade no momento da escrita.

## 3. Contratos e dependências

A S0 foi autorizada a ajustar suas regras sem regressões, de maneira específica, mas **a operação ainda depende da frente proprietária S1**, que mantém locks/RLS/transações. A implementação I11 existente suspende `equipe_prumo_s1.estado` e redistribui toda a carteira; I12 atualmente exige concessão de loja para transferências manuais. **Ambos requerem atualização, não devem ser contornados pelo frontend.**

Mensagem pronta para a S1 deve ser encaminhada pelo responsável; esta rodada não modifica a branch ou os contratos da S1. A issue [#10](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/10) já registra o histórico de divergências, mas este documento atualiza a decisão operacional com a nova semântica de unread/read/respondido e a redistribuição restrita.

**Gates:** nenhum deploy, PR merge, autenticação de produção, provedor externo, atualização de bancos hospedados ou alteração do índice 19F. FV-UI-013 segue **não homologada**, 19F **69/100**.
