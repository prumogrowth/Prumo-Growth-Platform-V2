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
