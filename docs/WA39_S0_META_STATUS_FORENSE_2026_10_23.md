# WA-39 — Integração aditiva S0 ↔ WhatsApp/Meta (forense, offline)

**23/10/2026 · Incremento independente construído sobre o HEAD do [PR S0 #1](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/1), commit `75095fe9b6050c704df37c663bb92595bc6513b6`. Não modifica a branch da S0, a S1, nem o [PR Meta #2](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2).**

## Motivo e separação de trabalho

O responsável pelo projeto autorizou a **frente WhatsApp a desenvolver as interfaces necessárias na S0**, desde que não quebre contratos e mudanças de outras frentes. S1 continua com uma equipe responsável; esta proposta não modifica RLS, concessões, papéis, atribuição ou suas migrations.

O PR #2 da frente Meta executa testes WA32–38 com um binding S0 injetado em mock/SQL separado. A S0 REAL já tem estruturas 029 (inbox/outbox técnico, sem emissão), 040 (unicidade de remetente), 041 (binding `wamid` → tentativa de mensagem, por loja e App) e 042 (IDs Meta App/WABA/phone associados ao registro S0). O incremento 043 utiliza essas tabelas existentes **sem criar segundo cadastro de concessionária ou duplicar registro de canais**.

## O que foi acrescentado

- `supabase/migrations/202610230043_s0_meta_status_forense_fixture.sql`:
  - `prumo_private.meta_status_forense_fixture_s0`: observação técnica vinculada ao ID imutável de `meta_vinculos_tentativa_fixture_s0`, tipo `sent/delivered/read/failed`, chave de evento provisória e SHA-256 do corpo. Unicidade `(vinculo_id,event_ref,body_sha256)` evita duplicata exata; um corpo diferente para o mesmo evento gera observação separada para triagem.
  - `prumo_private.meta_status_conflitos_fixture_s0`: conflito de tipo com a mesma chave de evento e o mesmo hash, sem alterar a observação inicial.
  - Ambas com FK para vínculo S0 existente, RLS habilitada, revogação de ACLs de `anon`, `authenticated`, `service_role` e papéis sintéticos. Trigger herdado da S0-041 impede UPDATE/DELETE da evidência.
  - `prumo_private.archivar_status_meta_tecnico_fixture_s0`: **somente `postgres` no PG17 descartável**, `SECURITY INVOKER`; busca a combinação exata de IDs Meta técnicos + canal + intenção + tentativa/correlação + destinatário + `wamid` em registros S0 confiados, usa bloqueio transacional por vínculo/evento, arquiva replay, variantes e conflito, inclusive após cancelamento. Nunca escreve estado comercial nem outbox; retorna `LAB_*` + flags de autoridade sempre falsas.
- `supabase/tests/s0_wa_043_status_forense_fixture.sql`: **18 cenários SQL sob ROLLBACK**, inclusive replay idempotente, variante divergente em quarentena, conflito de tipo, isolamento de concessionárias com `wamid` e destinatário iguais, rejeição de escopo/recipient/attempt inválidos, arquivo técnico tardio após CANCELADA, hash e categoria inválidos, trilha append-only, ACL/RLS e ausência de efeitos sobre inbox/status comercial.
- `scripts/run-s0-local.sh`: inclui nova migration e novo teste sem mudar a ordem anterior.
- `.github/workflows/wa39-s0-meta-offline.yml`: nova execução completa S0 em PostgreSQL 17 **descartável**, além de 18 marcadores WA39. Somente PR contra branch S0, sem deploy.

## Limites e próximas etapas

**Este não é um serviço S0 autenticado de produção.** A nova função depende do superusuário de teste; `p_body_sha256` e `p_event_ref` são entradas da fixture, não prova HMAC Meta. A validação do App Secret e a identidade máquina→máquina **não foram vinculadas de forma confiável a esta função**. Os callbacks Meta podem não fornecer ID único por notificação, logo corpo divergente é evidência técnica, não necessariamente fraude nem dois envios comerciais.

É preciso, em incrementos posteriores e coordenados, definir identidade/autorização interna de serviço com menor privilégio; verificar origem da assinatura antes de entrar no processo S0 e manter trilha da decisão; correlacionar HMAC, nonce e persistência transacional; ratificar políticas de ACK/redelivery, retenção LGPD e comportamento de lote com a frente Meta. S1 deve ratificar apenas interfaces/ordem de locks que dependam de concessões, não as tabelas técnicas aqui propostas.

**Sem chamada à API Meta real, envio, webhook hospedado, Supabase hospedado, Graph retry, ACK HTTP, IA, templates reais, migração de números comerciais, merge ou alteração das outras frentes.** A decisão de titularidade de conta/App/WABA por concessionária (DEC-WA-05) permanece vigente; o próximo piloto será somente com destinatários controlados após autorização e obtenção segura de credenciais.

A migration 043 é **arquivo candidato para desenvolvimento local**, NÃO está aprovada para aplicar no Supabase real. A frente de Supabase deverá incorporar somente uma versão revisada no seu próprio fluxo de implantação.
