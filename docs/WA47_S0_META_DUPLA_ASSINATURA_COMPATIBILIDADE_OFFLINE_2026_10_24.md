# WA-47 — Verificação explícita de compatibilidade WA34/35 ↔ S0/044–046 (PG17/Node offline)

**24/10/2026 · Repositório oficial 0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA · PR #2 Draft · sem merge, deploy ou S1.**

## Lacuna e solução executável

WA34/35 emite HMAC-SHA256 de uma representação JSON ordenada de 26 campos, com `issuer=WA34_SYNTHETIC_META_INGRESS` e `audience=WA34_SYNTHETIC_S0_READER`. S0/044–046 emite outra MAC sobre material textual pipe-separated de 15 campos, com audiência `WA44_S0_PG17_FIXTURE_ONLY`. **As MACs não são intercambiáveis.** O novo módulo de teste `supabase/tests/s0_wa_051_dual_wire_agreement.mjs` não as converte; compara **duas assinaturas distintas**, cada qual verificada sob sua chave de fixture, e aplica mapa explícito de escopo, propósito, tempo e identidade do evento.

O mapa associa `app_ref`, concessionária/tenant, canal, WABA/phone, caso↔intent via referências *distintas*, tentativa, correlação, revisão do vínculo, destinatário, `wamid`, tipo de status e hash do corpo Meta. Compara os IDs sintéticos de evento **diferentes**: `EVT_sha256([app,waba,phone,wamid,recipient,kind,ISO])` da WA35 e `WA46_sha256([waba,phone,wamid,recipient,kind,seconds])` da WA46, ambos recalculados de contexto de laboratório. Rejeita diferenças, inclusive se MAC individual estiver válida. Confere timestamps/expiração, finalidade forense, issuer/audience específicos, flags de negação, alterações concorrentes no contexto entre leituras e chaves secretas distintas em portas simuladas.

**Saída positiva:** somente `LAB_DUAL_WIRE_AGREEMENT_ONLY` com `wire_agreement=true` e todos os indicadores de autenticação produtiva, escrita, ACK, envio, reenvio e transição de caso **false**. Nenhuma tupla ou chave é devolvida à chamada pública, não se constrói principal de máquina e não se consome nonce no banco. A identidade de evento continua de fixture, não um ID único provido pela Meta.

## Provas e limite da evidência

- `supabase/tests/s0_wa_051_dual_wire_agreement.test.mjs`: 37 testes Node, com cenários positivos e falsificação de finalidade/issuer/audience, tenant, canal, revisão, assinatura, expiração, alteração de hash, nonce, campos extras/getters e rechecagem de contexto.
- `scripts/run-s0-local.sh` e workflow `wa39-s0-meta-offline.yml`: incluem WA47-01 a WA47-37, além da regressão S0 e WA39–46, em ambiente descartável.
- O teste positivo gera ambos os tickets em JavaScript com chaves totalmente fictícias. É prova de conformidade contratual **em laboratório**, não teste Meta→S0 real nem validação de identidade de serviço contra IAM/KMS.

## Bloqueios preservados

A verificação de duas MACs não comprova a origem real Meta: `WA46` continua consumindo portas de laboratório. O contexto e as chaves da WA47 também são injetados; quem os controlar pode fabricar tickets de laboratório. **Não há replay store transacional**, consumo de nonce, principal M2M autenticado, ligação de sessão ao canal S0, redução do wrapper privilegiado de PostgreSQL, gestão real de segredos, ACK após commit ou política LGPD ratificada. A S0 não recebeu migration; nenhuma estrutura S1 foi alterada. Para comercialização seguem necessárias decisões interfrentes sobre revogação e atribuição de Consultores e ordem de locks S0↔S1.

**Próxima etapa:** evoluir identidade de serviço S0/Infra com audiência e chave gerenciada, impedir uso de papel `postgres` no caminho candidato, e ensaiar consumo de nonce + revisão e append forense na mesma transação sob menor privilégio. Sem habilitar Graph ou HTTP público.
