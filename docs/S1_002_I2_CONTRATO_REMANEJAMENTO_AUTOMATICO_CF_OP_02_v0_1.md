> **ATUALIZAÇÃO NORMATIVA 19/10/2026 — I11:** gestor lidera **OPERADORES da sua equipe** (não lojas); os **RESPONSÁVEIS** atribuem/revogam quais concessionárias podem enviar leads a cada operador; o gestor pode **pausar temporariamente o operador inteiro, em todas as suas concessionárias**, e redistribuir sua carteira. O gestor não altera grants por loja. Esta decisão **prevalece** sobre qualquer leitura anterior de "gestor da concessionária" neste texto. Veja [Contrato I11](S1_002_I11_GESTAO_POR_EQUIPE_PAUSA_GLOBAL_2026_10_19.md). 14 cenários S1T aprovados em [PG17 #39242471186](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39242471186); não há Auth real nem deploy.

# S1-002/I2 — Contrato de ciclo da equipe e remanejamento automático | CF-OP-02 v0.1

Data 18/10/2026. **[D-negócio] mudança confirmada, [P/R] implementação e política de equilíbrio.** Proprietária: frente S1-002, com fronteira S0/C11. Referências: D-ORG-01, D41, documento 26 C11, [S0 CF-OP-02](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-fundacao-prumo/docs/CF_OP_02_CONTRATO_NUCLEO_RECONTATO_HUMANO_v0_1.md), PR #7, issue #6. Não é API implantada ou função pronta; migration 038 I1 não resolve redistribuição.

## Semântica e ações do domínio

Um profissional pertence à **Prumo**, nunca à concessionária; pode ter concessões independentes A/B, e um gestor só executa atendimento quando autoatribuído ao caso, conforme D41. **Ativo** e **concessão de loja válida** são condições cumulativas com papel e atribuição, nunca permissão em si.

Ao suspender, desligar, remover profissional ou revogar sua concessão em uma concessionária, o backend S1-002 deve: (a) impedir imediatamente novos casos/ações nesse escopo; (b) isolar e bloquear atribuições afetadas; (c) redistribuir **automaticamente** os casos operacionais para outros profissionais Prumo ativos, com concessão e alçada na **mesma loja**, preservando histórico, operador anterior e motivo; (d) se não houver destinatário elegível, manter **fila protegida e sinalização ao gestor**, jamais atribuir a inativo ou outra loja. Se a pessoa perder somente B, A permanece válida; não apagar histórico em B.

## Definição de caso operacional [P/R]

Candidato para redistribuição: atendimento humano **não concluído**, retorno/pendência de complemento, atendimento **concluído mas ainda na janela visual ativa**, caso com **plano de recontatos pós-humano ativo**, mensagens em processamento e responsabilidades de remessa humana ainda pendentes. Não reatribuir retroativamente autoria de conversa, envio ou venda, nem reabrir automaticamente ciclo comercial perdido/vendido. A matriz final de casos sob banco / remessa requer concordância S0 e processo específico [R].

**Atribuição substituída não revive ao reativar operador antigo**. O caso continua com novo profissional até alteração explícita autorizada. A redistribuição deve ser atômica e auditável: único titular ativo por caso, travamento/versão/idempotência; conciliação de eventos de mensagem, botão Concluir, planejamento em andamento e competição entre gestores. Nunca criar janela Meta nem atribuir poderes por evento WhatsApp.

## Estratégia candidata [P]: equilíbrio com restrições

Para cada loja afetada, selecionar apenas membros Prumo ativos, papel operacional/concessão válida e disponibilidade/escala elegível — critérios concretos de turno, capacidade, prioridade, justa distribuição e indisponibilidade seguem [R]. Não presumir que há sempre dois substitutos ou distribuir igualmente sem limites. Casos com compromisso futuro do cliente e cadeias programadas devem preservar plano vinculado **ao caso**, não ao operador removido; futuras respostas seguem novo destinatário autorizado calculado pelo S0.

Gestor mantém leitura D2 integral da própria loja em supervisão, mas não pode virar executor sem autoatribuição ativa. Remanejamento altera direitos futuros, não abre documentos D3/D4 para supervisores não autoatribuídos.

## Divisão de propriedade

- **S1-002**: equipe Prumo, estado, evento de revogação, seleção de substitutos válidos, operação de atribuição única, versão, locks e auditoria.
- **S0**: caso/comercial, verificação de posse antes de comandos, inbox/inbound, planos C04–C09, mensagem/meta e workflow pós-conclusão. Consome nova atribuição e bloqueia envio obsoleto, mas não modifica o estado da equipe diretamente.
- **Frontend**: fila, pessoa responsável, aviso seguro de redistribuição, retirada imediata de casos da tela do revogado e solicitação ao backend; **não** decide alocação.
- **OpenAI**: não escolhe profissionais, não acessa lista de RH e não redistribui; proposta de planejamento preserva referência opaca do caso.
- **Meta**: não altera vínculos Prumo, papel ou dono do atendimento por callback.

## Testes futuros e portões

I2-T01: suspender O1 com casos A e B e pares O2/O3 elegíveis redistribui A/B por suas próprias lojas; O1 não recebe novos e não lê. I2-T02: revogar somente B preserva A. I2-T03: nenhum elegível implica fila protegida e aviso gestor. I2-T04: duas transações de revogação e novos inbound/conclusão não criam duas atribuições. I2-T05: reativação de O1 não restaura casos antigos. I2-T06: plano de template permanece ligado ao caso após remanejamento e inbound chega ao novo humano. I2-T07: gerente autoatribuído recebe poder só naquele caso. I2-T08: evidências históricas/autoria permanecem. I2-T09: não vazar A/B nem ampliar D3/D4. **Nenhum teste I2 foi executado.**

Gates: quem autoriza desligamento/suspensão [R]; matriz de caso operacional e escala/capacidade [R]; revisão da migration 038/GoTrue/REST e wrappers [R]; S0 C11 e C04–C09 conciliados [R]; cenário integrado com dados sintéticos [R]. Não usar Supabase hospedado, Meta/OpenAI/Banco real, ou merge/produção sem autorização.


## Incremento 039 — Prova sintética, não política de RH pronta

Foi acrescentada a migração `202610180039_s1_remanejamento_transacional.sql` à branch S1-002, seguida do ensaio `s1_002_remanejamento_transacional.sql` (S1R-01..08). Mudanças em `estado` da equipe e no último vínculo operacional vigente de uma loja disparam encerramento das atribuições e seleção transacional de operador Prumo ativo com menor carteira na mesma loja (desempate determinístico). Nenhum gestor recebe autoatribuição de forma automatizada. Se não houver operador elegível, fica registro privado de fila protegida; histórico anterior é preservado. Casos já `vendido`/`perdido` perdem vínculo residual, sem nova ação comercial. Status bancários não mudam. Guarda de linha da equipe/concessão impede atribuição a inativo. **Não editar S0, Meta, OpenAI ou Frontend por este incremento.**

**Limitações:** heurística de carga ainda não substitui política de escala; concessão que expira FUTURAMENTE só pela passagem do tempo requer reconciliação agendada; não há gestão de autoridade RH/autenticada, nem teste intersessões ou GoTrue/REST após 039. Os primeiros testes são sintéticos e sua aprovação só pode ser registrada após CI. Atenção: S0 legado roda ANTES de aplicar 038+039, não após; testes I2 são direcionados.

## I10 — decisão de autoridade por papel e escopo (19/10/2026)

**[D, confirmado pelo usuário]** Apenas `responsavel` pode adicionar gestores/operadores e efetuar remoção definitiva; `gestor` administra operadores existentes (mover caso, redistribuir, suspender e reativar temporariamente e outras rotinas operacionais autorizadas). Nenhum gestor acrescenta profissional nem remove definitivamente. Gestão restrita à loja sob concessão; o profissional Prumo pode ter A/B independentes. `gestor` não modifica pares, responsáveis nem estado comercial. Predicado interno e testes S1P-01..10 em migrations 047, sem RPC/REST, definem a matriz, **não implementam o comando administrativo**. I9 continua negando DML direto; comandos de gestão precisam do gateway Auth validado e do modelo de suspensão **por loja** para não interromper outra concessionária. [Contrato I10](S1_002_I10_AUTORIDADES_RESPONSAVEL_GESTOR_2026_10_19.md).
