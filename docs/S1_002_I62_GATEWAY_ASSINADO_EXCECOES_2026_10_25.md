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

## Evidência CI inicial — 25/10/2026

- [Workflow real GoTrue I37 #40178448376](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40178448376), jobs `121124233933` e `121124234090`: **SUCCESS** após correção da allowlist HMAC em `69b9f1005ccf9dd016eedac28587149a09f9af1c`. Logs conferidos `PASS I62-E2E-01..06` (**6/6**) e **10/10 testes unitários**; regressões I53/I55 e assinatura anterior mantidas.
- Falha da primeira execução [#40178384922](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40178384922): o signer tinha uma allowlist estrutural além do verificador por operação, logo rejeitou legitimamente o novo domínio `EXC62M`; corrigido adicionando apenas os dois domínios explicitamente válidos `EXC62M` e `EXC62R`.
- O teste E2E ampliado também exercita a **rota HTTP de revogação** em retry legítimo e bloqueia outro Gestor, sem duplicar evento. Sua certificação é separada e depende de novo workflow.

I62 **não** está no Supabase hospedado, no ambiente de clientes ou em endpoint de produção. A RLS definitiva de histórico permanece outra etapa.

## Certificação final — 25/10/2026

**Workflow [#40178720872](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40178720872) — SUCCESS**, commit de código/testes `d2671ba4eca4c5a8fb4fd224b0c368cd286943f1`. Logs conferidos dos jobs `121124961226` (unittest **10/10**, job SUCCESS) e `121124961282` (E2E **7/7**, job SUCCESS).

Casos I62-E2E-01..07: GoTrue identifica Gestor sem permitir identidade fornecida no JSON; pessoa de outra equipe/Consultor não transfere; transferência excepcional cria atribuição S0 válida e nenhum grant de loja; HMAC impede trocar operação; revogação com nonce não repetível; rota HTTP retorna idempotência para Gestor autorizado, nega outro Gestor e mantém um único evento; leitura privada SQL e REST recusada. Regressões de intake I53 e fila I55 persistem verdes na mesma execução.

Os testes não constituem auditoria de implantação, não exercitam gestão real de segredo/KMS, TLS de borda ou dados de clientes. Permanecem pendentes a integração operacional do executor e composição das RLS I41–I60 com as tabelas I61 no ambiente de homologação.
