# Encaminhamento S0 → F02

26/10/2026. Contrato `prumo.s0.f02.review.* / 0.1-candidate`, sujeito à avaliação conjunta.

**Entrega efetiva:** pedido de revisão passa a poder ser registrado e recuperado no PostgreSQL, sob GoTrue/CFI/S1 vivos, com idempotência, CAS, retirada, prazo imutável, auditoria e rollback. A S0 usa o estado persistido; omitir uma revogação na timeline F02 não o apaga.

**F02 deve:** preservar proposta/evidência originais; tratar `RECORDED_REVIEW_ONLY`, `REPLAY_REVIEW_ONLY` e `CURRENT_REVIEW_ONLY` somente como status de um pedido com provas pendentes. Não converter digest, referência, cursor ou qualquer estado em autorização. Retomar por nova consulta S0; resposta perdida pede recuperação pela mesma chave/documento, sem novo envio.

**Diferenças para negociar:** chave técnica é única por loja+ator+chave, sem impor unicidade comercial por encerramento. Janela é limite voluntário do pedido, não TTL homologado. O CFI exige capturador/sessão originais: não há transferência automática para novo login ou gestor independente. O contrato UI/S0 continua candidato; a recuperação continua exigindo binding no servidor, cujo lookup durável depende de D3. Não se declara recuperação completa após perda de processo/HA.

**Falta aprovar:** mapeamento e validação das quatro provas F03/C08/origem/intenção; versões e cutoff; permissão do gestor ratificador e continuidade entre sessões; TTL/retenção/minimização; transporte UI; fonte Meta/opt-out/template e eventual política pós-humana. A S0 coordena com F02/F03, S1, Frontend, Meta e Produto/Privacidade.

**C04/C08:** cancelamento local não comprova cancelamento externo. Tentativa antes reservada permanece incerta; esta entrega não libera novo slot, agendador ou envio. Não incorporar automaticamente as fixtures de outra frente.

Código, contrato detalhado, schema de resposta, manifesto de proveniência e evidências acompanham o PR S0 desta branch. Nenhuma alteração na branch F02, merge, deploy, migration hospedada ou chamada comercial real.
