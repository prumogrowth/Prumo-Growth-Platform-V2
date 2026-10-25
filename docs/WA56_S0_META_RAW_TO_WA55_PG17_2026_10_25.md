# WA-56 — Ponte entre bytes Meta e a entrada WA55

**25/10/2026. Laboratório Node.js + PostgreSQL 17 descartável. Sem deploy, Meta HTTP real, IAM/M2M real ou mudanças comerciais.**

## Implementação

A nova ponte `supabase/tests/s0_wa_060_meta_raw_to_pg17_bridge.mjs` integra o gate de bytes brutos WA46, o ticket HMAC interno WA45/WA44 e a entrada única WA55. Copia o corpo antes de qualquer operação assíncrona, exige assinatura `X-Hub-Signature-256` válida no gate WA46, interpreta e compara independentemente o evento de status, recalcula o SHA256 do corpo e a referência determinística, copia e congela os 15 campos da candidatura, valida seu HMAC interno por comparação temporalmente segura e impede substituição de campos depois da primeira verificação. A porta `appendWa55` recebe apenas o ticket validado e imutável. Respostas comerciais positivas ou formato inesperado são recusados.

`supabase/tests/s0_wa_060_meta_raw_to_pg17_bridge.test.mjs` contém 36 testes: assinatura e bytes alterados, corpo inválido, status e identidade falsificados, chaves e MAC incorretos, tickets falsificados, claims adicionais, relógio, recibos inadequados, cópia antecipada de bytes, além de chamada física PG17 à função WA55 já selada, replay e conferência do ledger original. O runner executa esta suíte somente **depois** das regressões WA39–55 e da selagem das funções antigas.

## Limites

O gate e as chaves são portas de laboratório; o cliente PostgreSQL usa uma senha aleatória gerada durante os testes, não uma autenticação operacional. A WA56 **não prova origem HTTP produtiva da Meta**, não valida cabeçalhos de proxy real nem provê proteção de rede ou credenciais hospedadas. Não realiza Graph/ACK, envio, retry externo, S1, deploy ou merge. O benefício comprovável é a consistência de bytes, escopo e assinatura entre duas interfaces sintéticas com chamada real ao PostgreSQL 17 de CI. A liberação de produção continua expressamente bloqueada.

**S1:** nenhuma solicitação nesta etapa. Avaliação posterior exigirá contrato S0/S1 de cancelamento/autorização previamente acordado.

**Próxima etapa sugerida:** simular transporte HTTP local, com rejeição de cabeçalhos/bytes ambíguos, sem ativar qualquer endpoint real.
