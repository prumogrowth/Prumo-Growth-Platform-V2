# I62 — Assinatura GoTrue/HMAC para exceções canônicas I61

**25/10/2026 — Testes apenas no Supabase CLI descartável; nenhum deploy.**

A transferência e a revogação por caso passam por três fronteiras separadas: (1) API HTTP local aceita apenas identificadores de loja/caso/atribuição/destino ou ID da exceção, nunca o ID do Gestor; (2) JWT real do GoTrue valida usuário e sessão no assinador independente, que assina domínio `EXC62M` para movimentação e `EXC62R` para revogação, com nonce e janela de expiração; (3) wrapper de SQL em ownership NOLOGIN I21 verifica HMAC custodiado em I22, consome nonce uma vez e delega à bridge `postgres`, que consulta a sessão GoTrue viva antes de chamar a transferência/revogação I61.

O material da assinatura reusa apenas o layout de seis argumentos I20, sem reutilizar domínios das operações `MOVER`, `FILA55C` ou `INTAKE53`. O ID do Gestor deriva exclusivamente de `p_ator` autenticado e assinado, nunca de campo do cliente. Retornos HTTP são filtrados por forma exata e sem PII.

O bridge permanece **fixture em `supabase/tests/`**; depende de HMAC custodiado experimental, certificado mTLS, autoridade de revogação local e PostgreSQL executor separado; o gateway HTTP é `http.server` loopback. Portanto NÃO constitui interface de produção.

A aplicação I61 como migration da branch S0/S1 e a RLS I60 continuam independentes: o incremento prova apenas transferência/revogação assinadas, sem acesso amplo por concessionária ou promoção de políticas de leitura.

## Aceite

- Unitários estritos para campos, signatários, permuta de operação, domínio criptográfico, DSN e filtro de resposta.
- E2E GoTrue real local: outro gestor/consultor proibidos, campos de identidade falsificados, transferência autorizada, adulteração HMAC, revogação+replay, isolamento SQL/REST.
- **Evidência a registrar após CI**, jamais certificar antes.
