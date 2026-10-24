# WA-45 — Fronteira de emissão controlada entre evento e assinatura interna S0 (somente laboratório)

**24/10/2026 · Repositório oficial [Plataforma-de-Vendas-por-IA](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA) · branch `feat/wa39-s0-meta-forensic-bridge-20261023` · nenhuma alteração na S1 ou na `main`.**

## Problema técnico

WA-44 demonstrou os bytes canônicos do material HMAC JavaScript ↔ PG17 S0/044 com fixtures. Ainda assim, `makeWa44CandidateFixture` aceita registros denominados `registry` e `binding` diretamente como argumentos, adequados **apenas para testes**. Uma aplicação real não pode confiar em concessão, concessionária, tentativa ou chave fornecidas no mesmo evento HTTP.

**WA-45 modela a separação**: `s0_wa_049_meta_trusted_boundary.mjs` expõe um gerador de laboratório cujas portas internas simuladas `getRegistry`, `lookupBinding`, `getInternalKey`, `newNonce` e `nowSeconds` são recebidas no construtor. A chamada `issue(event)` recebe **somente** `eventRef`, `kind`, `bodySha256`, `wamid` e `recipient`; qualquer `concessionaria`, token, canal ou campo extra é recusado. O registro interno é conferido **duas vezes**, inclusive após obtenção da chave e do nonce; alterações de loja, App, canal, tentativa, revisão do vínculo ou relógio provocam bloqueio. O candidato continua usando exatamente a canonicalização e HMAC da WA-44, que por sua vez concorda com o receptor S0/044.

**Isto não comprova a confiança das portas simuladas.** Uma chamada de código que consiga construir o gerador com dados/segredo forjados ainda pode gerar um pacote de laboratório. O construtor deve existir somente atrás da futura identidade de máquina autenticada, com registry e binding obtidos da própria S0 em canal confiável. Nunca usar estes arquivos `supabase/tests` como endpoint HTTP ou rota da IA.

## Provas adicionadas

- `supabase/tests/s0_wa_049_meta_trusted_boundary.mjs`: fronteira que devolve `LAB_CANDIDATE_ONLY` ou falha fechada, sempre com flags de envio, ACK, produção e autenticação **falsas**.
- `supabase/tests/s0_wa_049_meta_trusted_boundary.test.mjs`: **22 testes negativos/contratuais Node**: falsificação de tenant, canal, destinatário, revisão e mensagem; getters/proxy/campos extras; chave, nonce e relógio inválidos; mudança de vínculo durante operações assíncronas; indisponibilidade; repetição e isolamento da assinatura.
- Ainda no mesmo teste, **5 comprovações físicas PG17**: material canônico, assinatura HMAC, gravação técnica sob a função S0/044, repetição negada e alteração do evento rejeitada, sem registrar envio/ACK ou transição comercial.
- `scripts/run-s0-local.sh` e `.github/workflows/wa39-s0-meta-offline.yml`: incorporam os 27 cenários e preservam regressões S0, WA39–44 no mesmo PostgreSQL 17 descartável. A validação só será reconhecida como concluída quando CI do HEAD estiver verde.

## Limitações e próximos bloqueios

- A assinatura HMAC **interna** WA44/45 não é a assinatura do webhook da Meta nem prova quem originou a mensagem.
- A implementação de S0/043-046 permanece em banco de teste e ainda contém wrapper de domínio proprietário `postgres`. Não foi eliminado o executor privilegiado nem estabelecido principal real com menor privilégio.
- WA34/35 continuam com envelope próprio; a WA-45 **não aceita nem converte uma assinatura JSON WA34**. A harmonização do contrato e uma prova da origem Meta permanecem necessárias.
- A proteção de nonce exige persistência transacional no receptor; a geração JavaScript não substitui a verificação em PostgreSQL.
- Não se acessou o Supabase hospedado, nenhuma conta, número, token ou API real da primeira concessionária foi usada. **Sem merge, deploy, Graph, ACK ou IA de atendimento.**

## Comunicação entre frentes

A WA-45 não modifica S1, nem exige decisões dela nesta etapa. Antes da ativação de ações comerciais, continua necessário encaminhar à equipe S1 as decisões sobre **revogação/reatribuição de atendimentos**, estados em que callbacks forenses tardios podem ser mantidos sem reabrir envio, e a **ordem conjunta de locks S0↔S1**. Até esse aceite, qualquer assinatura e evidência aqui é **forense, não autorização comercial**.
