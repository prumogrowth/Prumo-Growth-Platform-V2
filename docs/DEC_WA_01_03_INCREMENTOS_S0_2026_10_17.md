# Prumo S0 — DEC-WA-01/02/03: identidade BR e inbox/outbox sintéticos

**Status:** incrementos candidatos 028 e 029 na branch privada do PR #1. As diretrizes DEC-WA-01/02/03 estão aprovadas; **DEC-WA-04/05/06 continuam pendentes**. Nenhuma implantação comercial, conexão Meta, alteração de canal real, merge ou credencial operacional foi autorizada/executada.

## Origem normativa e versionamento

- PR #2, branch `docs/whatsapp-meta-concessionária de demonstração-poc-20261017`, HEAD consultado `1b6d99eb41e3853253d72a669e8850a5177db0e2`.
- `docs/integracoes/whatsapp-meta/interface-compartilhada-s0-meta-v0_1.md` — envelope, ACK, identidade, C02/C07 e intenções C03/C06/C12; **campos e rotas ainda [P]**.
- `docs/integracoes/whatsapp-meta/conciliacao-pr1-pr2-s0-whatsapp-v0_1.md` e documentos canônicos 00A, 13A, 21–23, 25, 26, 30, 40, 41.
- Regra irrevogável vigente: número **do cliente** pode repetir em lojas A/B/C com histórico separado; **emissor** da Prumo mantém UNIQUE global. Migração antiga 007 permanece excluída.

## Implementação 028 (S0 somente)

`202610180028_s0_identidade_aliases_sinteticos.sql` cria exclusivamente em `prumo_private`:
- `aliases_identidade_s0` com vínculo composto à loja e lead e unicidade **por loja + número exato**, não global.
- `eventos_identidade_s0` para decisões de vínculo; `pendencias_identidade_s0` para preservar entrada ambígua sem atribuição arbitrária.
- `chave_variante_br_s0`: chave candidata `+55+DDD+8 últimos dígitos` somente para representação BR sintética elegível, quando comprovada por sinal de teste. **Não é endereço de envio nem prova de titularidade civil.**
- `resolver_contato_s0`: correspondência exata, alias confirmado, prevenção de colisão entre leads legados, `NEEDS_REVIEW` quando apenas dado legado não confirmado coincide, travamento transacional da chave candidata por loja, criação local idempotente.
- `receber_mensagem_identidade_s0`: ponte privada **sintética** com C02 existente; chama C02 com o telefone principal do lead, para não duplicar mensagens por 8↔9 e preservar handoff/versões. Em conflito grava pendência e NÃO aciona IA.

O sinal `p_mobile_confirmado` é **assertiva de fixture controlada exclusivamente pelo operador SQL de teste `postgres`**, não evidência da Meta real nem dado permitido do cliente. Portanto, as rotinas não são API externa, não substituem C01/C02 atuais e **não autorizam normalização automática em produção**. Versões antigas de leads sem evidência móvel não são fundidas por fórmula numérica.

## Implementação 029 (S0 somente)

`202610180029_s0_inbox_outbox_sinteticos.sql` cria:
- `inbox_eventos_s0` (idempotência por `concessionaria_id,canal_id,tipo,chave_evento`, fingerprint sintético e FKs compostas).
- `tarefas_ingresso_s0` com vínculo 1:1 com evento, READY/LEASED e reserva privada `FOR UPDATE SKIP LOCKED`, versão e expiração de lease.
- `outbox_intencoes_s0` com contratos C03/C06/C12 **somente em `BLOQUEADA_GATES` ou `CANCELADA`**. Não há função de publicação, destinatários, credenciais ou chamadas Graph.
- `aceitar_lote_ingresso_s0` cria evento e tarefa na **mesma transação**; duplicata compatível não cria segundo efeito; erro em qualquer item invalida todo o lote. O retorno `ACCEPTED_DURABLE` declara só persistência no PG sintético, não HTTP ACK Meta real.
- `reservar_ingresso_s0` reserva dentro da concessionária/canal; `registrar_intencao_bloqueada_s0` registra intenção, não valida direitos comerciais nem faz envio.

Tabelas privadas com RLS ativada e EXECUTE/GRANT negados a `anon`, `authenticated`, `service_role`, `prumo_s0_gateway` e `prumo_s0_signer`. Nenhum papel de serviço permanente foi criado; operação interna de fixture requer `current_user='postgres'`. Isso é protótipo seguro de transação, **não** plano de privilégio mínimo final.

## Limites importantes

1. C01/importação continua no caminho sintético antigo e só resolve telefone textual; integração geral do resolvedor no C01/C02 requer trabalho adicional e contrato de evidência. A ponte privada 028 é **incremento aditivo**.
2. Sem persistência criptografada de telefone de cliente real, hash de lookup com segredo de produção, rotatividade de alias por telefone reciclado, LGPD/retention, sistema de identidade civil ou regras externas Meta. Dados testados exclusivamente fictícios.
3. A migração 029 não implementa consumidor que chame C02/C07, finalização de tarefa, backoff/DLQ operacional, retentativa externa nem auditoria durável de negativas. Workers reais dependem de autorização e identidade técnica específicas.
4. Não foi feita alteração de `canais_loja.modo='simulado'` ou vínculo Meta/WABA, enquanto posse/mandato DEC-WA-05 e ambiente DEC-WA-04 não forem deliberados.
5. `SECURITY DEFINER` comercial ainda usa proprietário `postgres` nas wrappers da 027. A redução de privilégios não é presumida resolvida pelo incremento WA.
6. Callback Meta sem event ID estável, revalidação no instante de publicação e estados `UNCERTAIN_EXTERNAL` são especificações para os próximos marcos, não código vigente.
7. Os testes PostgreSQL da S0 não certificam Supabase Auth/REST gerenciado. Uma execução integrada pesada fica sujeita a gate explícito; não disparar automaticamente por commit.

## Testes e aceitação

`supabase/tests/s0_identidade_aliases.sql`: WA-ID-01..05 — 9↔8, 8↔9, repetição de ID de mensagem, lojas distintas, telefone ambíguo/fixo, colisão e ACL privada.

`supabase/tests/s0_inbox_outbox.sql`: WA-IN-01..03, WA-OUT-01, WA-SEC-01 — lote 2 mensagens+2 callbacks, replay, rollback integral, lease, escopo de loja, outbox sem estado executável, isolamento de papéis.

Os dois arquivos foram incluídos em `scripts/run-s0-local.sh`, cuja proteção restringe URL a banco PostgreSQL local descartável. **Registrar resultado de CI pelo link de execução específico no arquivo `tests/S0_ACEITE.md` após confirmação de PASS.** Não declarar Auth/REST/Meta testados.

## Retorno necessário à frente WhatsApp/Meta (PR #2)

- Preservar envelope `meta-s0.v0.1-proposed` como candidato; o código não expõe endpoint, não aceita HMAC real e não altera a função sandbox concessionária de demonstração.
- Para adaptação do ingressor, fornecer semântica validada do identificador de cada evento de status (não assumir que `statuses[].id` seja ID único), critérios de fingerprint, regra de ACK/quarentena e tratamento de posts com múltiplos itens.
- Definir **prova móvel segura** separada da flag sintética do resolvedor 028; `wa_id` sozinho não prova titularidade civil. Não implementar conversão cega nem enviar a 8/9 como tentativa.
- Não introduzir tabela comercial própria de canais, leads, ciclos ou mensagens; na integração real, chamar interface aprovada pelo núcleo e preservar dados de canal/loja por vínculo confiável.
- Conservar a POC `whatsapp-webhook-sandbox` intacta e PR #2 Draft; nenhuma conexão direta a 028/029 é operável ainda.

**Gate:** GO exclusivamente para iterar sobre PostgreSQL sintético e CI de baixo custo. **NO-GO** para deploy no Supabase hospedado, Meta/Banco/Marca A, canais comerciais, plano pago ou merge.


## Adendo de auditoria 030 — 18/10/2026 (sem alterar evidência anterior)

O documento `docs/AUDITORIA_CORRECOES_WA_S0_030_2026_10_18.md` registra a correção aditiva 030: replay de pendência com comparação de conteúdo, FK composta de alias/lead/loja, ensaio atômico de múltiplos canais e `payload_fixture_s0` fictício recuperável no Postgres descartável. **As migrations 028 e 029 não foram reescritas.** O resultado 030 é `FIXTURE_BATCH_STORED`, **não** recibo `COMMITTED` e **não** autorização para ACK HTTP.

**DEC-WA-05 agora tem decisão posterior aprovada apenas para titularidade por concessionária** (PR #2, documento `decisao-titularidade-meta-por-concessionaria-v1_0.md`); eventual afirmação anterior de pendência integral ou propriedade dos emissores Meta pela gestora está superada. Onboarding, credenciais, plano de mudança de canais e permissões reais seguem sem autorização. DEC-WA-04/06 continuam pendentes. Regras antigas de exclusividade do canal emissor e separação de clientes entre lojas permanecem.
