# WA-35 — Ponte offline: HMAC Meta → vínculo de tentativa → MAC interno → nonce PG17

**23/10/2026 · [PR #2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2) · Escopo exclusivo da frente WhatsApp/Meta.** Integra os **componentes de laboratório**, sem criar identidade de serviço, API S0, migração de produção, webhook hospedado ou comunicação Meta real.

## Qual lacuna está sendo atacada?

- [WA-32](./wa32-webhook-assinado-escopo-s0-forense-offline-2026-10-22.md) provou verificação HMAC de bytes de um callback Meta **fictício** e correspondência exata a uma porta S0 **simulada**.
- [WA-33](./wa33-handoff-forense-atomico-pg17-2026-10-22.md) provou gravação forense sob locks PostgreSQL, porém recebia os dados como argumentos SQL sem identidade do chamador.
- [WA-34](./wa34-contrato-handoff-servico-nonce-laboratorio-2026-10-22.md) provou envelope interno MAC + consumo transacional de nonce, **separadamente**, sem vínculo autenticado entre emissor e invocador do SQL.
- **WA-35** executa a cadeia, do callback sintético à gravação física, **num runner privilegiado de testes**. Isso reduz a lacuna de montagem do contrato, mas **não substitui** autenticação/autorização da porta de escrita S0. Não alegar E2E produtivo.

## Artefatos

1. `integrations/whatsapp-meta/wa35-signed-ingress-handoff-fixture.ts`: usa o `inspectRoutedMetaPost` real da integração Meta sobre um snapshot dos **mesmos bytes** usados para o SHA-256 assinado internamente. Admite **exatamente um** status por POST; rejeita inbound, lote misto, status não suportado e escopo incompatível. Compara App/concessionária/canal/WABA/número Meta/`wamid`/destinatário, caso/tentativa, revisão e estado da claim por leituras `LOOKUP` + `RECHECK` da porta fictícia S0. Reconsulta esse vínculo e o registro de canais após as operações assíncronas de nonce e chave. Emite pacote WA34 com `FORENSIC_APPEND_ONLY` e sinal técnico **`LAB_TICKET_FOR_S0_RECHECK_ONLY`**, nunca autorização.
2. `wa35-signed-ingress-handoff-fixture.test.ts`: **26 cenários adversariais Node**. Cobre HMAC inválido, canal de outra loja, lote de status, mistura inbound, vínculo inexistente/ambíguo, escopos e destinatário trocados, rechecagem obsoleta, revogação do App/rotação de canal, chave/nonce inválido, objetos S0 hostis, mutação do corpo do webhook durante uma espera assíncrona e SHA calculado dos bytes efetivamente validados.
3. `integrations/whatsapp-meta/lab/wa35_pg17_read_forensic_binding.sql`: leitura privilegiada e **somente de laboratório** do vínculo já criado em `wa33_lab` para uma tentativa fictícia cuja claim fora invalidada. **Não é consulta S0 autenticada**, não representa ligação de mensagem real.
4. `wa35-assert-signed-nonce-pg17.ts`: runner de **16 verificações cruzadas**. Gera callback HMAC assinado com App Secret fictícia, correlaciona-o ao binding obtido do PG17, gera MAC interna com outra chave fictícia e verifica o envelope WA34. Só então **o próprio runner** chama, via `psql` privilegiado, o consumo de nonce `wa34_lab.consume_fixture`. Testa arquivo forense de claim revogada, duplicidade exata, replay do mesmo nonce, novo nonce para o mesmo evento, adulteração MAC, HMAC Meta errado, tempo expirado, tenant trocado e revisão/destinatário alterados entre emissão e uso. Recusa DSN diverso de `127.0.0.1:5432/prumo_s0_test_ci` e variáveis `PG*` capazes de redirecionar conexão.
5. `.github/workflows/whatsapp-meta-offline.yml`: novo gate WA35 depois de WA34, exigindo **WA35-01 a WA35-16** uma vez cada no PG17 descartável.

## Evidência

- **[GitHub Actions #39931145380](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39931145380)**, commit `7b7c365bff11a178197e94242ac77a3902dd04e3`: **3/3 jobs aprovados**, regressão Node **683/683 PASS**, incluindo os 26 testes WA35.
- **[GitHub Actions #39931542959](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39931542959)**, commit `23ea13c564f87dc1a6905c464260dd9109e98dcc`: **3/3 jobs aprovados** com gate PostgreSQL exigindo 16 marcadores WA35, além das regressões anteriores.
- Observação: passes físicos são de um PostgreSQL 17 descartável, em fixture sob superusuário. Não constituem prova de produção S0, verificação GoTrue, Meta Graph, consentimento real, entrega, ACK ou segurança de credenciais produtivas.

## Segurança e pontos de atenção

- O ticket contém internamente referências de loja, destinatário e tentativa; é **objeto de backend fictício**, não resposta HTTP, ferramenta MCP, prompt de IA, log ou token delegável. O retorno deve ser recusado a cliente/IA.
- O `event_ref` é calculado de forma determinística por SHA-256 de App, WABA, telefone Meta, `wamid`, destinatário, tipo de status e timestamp. **Meta não garante que essa composição identifica um callback único**. Dois callbacks distintos podem ter os mesmos atributos; a identidade e política de deduplicação definitivas dependem de ratificação S0/Meta. A assinatura interna do **corpo inteiro** não substitui a identidade do evento.
- S0 precisa validar a assinatura interna por seu **próprio componente confiável**, provar a identidade do serviço chamador, usar chave com rotação/isolamento de segredos, escolher o *clock* no receptor, vincular hash e tentativa persistida, consumir nonce e anexar evidência na **mesma transação**, sob privilégio mínimo, RLS e ordem de locks compatível com S1.
- As rechecagens do TypeScript **não** fecham a corrida entre o último read e o COMMIT, e o próprio banco fictício aceita argumentos sem MAC. Esse risco permanece impeditivo. Um cliente com acesso à função `consume_fixture` poderia simular uma gravação sem conhecer a chave interna.
- A regra comercial não muda: status `sent`, `read` ou `failed` no laboratório não prova entrega nem falha definitiva WDC-13, não fecha caso F03 e não autoriza Graph. Todos os resultados deixam `ack_allowed`, `send_authorized`, `retry_external`, `production_authorized`, `delivery_confirmed`, `case_transition_authorized` e `definitive_failure_count_increment` em `false`.
- Não há webhook HTTP real, Meta Graph, key vault, autorização de serviço, migração S0/S1, merge, deploy, dados de cliente, ferramentas OpenAI/MCP ou operação bancária. O PR #2 permanece **Draft**.

## Próxima decisão necessária

Ratificar com donos S0/S1 e infraestrutura: **(1)** identidade de máquina e autoridade de gravar `FORENSIC_APPEND_ONLY`; **(2)** origem confiável do binding App→loja→caso/tentativa e sua revisão; **(3)** deduplicação de status sem ID único fornecido por Meta; **(4)** protocolo de verificação MAC + consumo de nonce + evento atômico, com RLS e locks reais; **(5)** regra HTTP ACK/retentativas do webhook e retenção LGPD. Até isso, não migrar esse laboratório para produção.
