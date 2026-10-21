# WA-16 — classificação segura de COMMIT incerto e prova de transações em laboratório

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Estado em 20/10/2026:** código e suíte publicados no PR #2 (Draft); **CI da revisão WA-16 ainda não confirmado**. Não declarar PASS PostgreSQL/TypeScript sem job concluído e logs. Os gates WA-15C (12/12), WA-06D (20/20) e Meta (479/479) já aprovados se referem a **commits anteriores**, não demonstram a WA-16.

## Objetivo

Quando a Meta aceita uma tentativa e o sistema deixa de receber confirmação da gravação do vínculo na S0, **a resposta perdida não autoriza reenviar Graph**. A leitura posterior de uma gravação exata prova persistência S0; a ausência de vínculo NÃO prova ausência da mensagem na Meta. Ainda não há ACK durável nem autenticação de serviço.

## Implementado em TypeScript

- `s0-unknown-commit-recovery.ts`: função pura `classifyUnknownCommitRecovery`, que aceita **somente** um objeto data-only com os quatro campos esperados da consulta S0-041/042: `outcome`, `ack_allowed:false`, `retry_external:false` e `production_authorized:false`.
- `LAB_FOUND_EXACT` vira `LAB_CONFIRMED_DURABLE`; `LAB_ABSENT` vira `LAB_ABSENT_STILL_UNCERTAIN`; `LAB_CONFLICT` vira `LAB_CONFLICT_QUARANTINE`; qualquer falha, campo extra, privilégio, retorno de escrita ou objeto hostil vira `LAB_UNTRUSTED_RECOVERY`.
- **Todas** as decisões explicitam `retry_external:false`, `ack_allowed:false`, `delivery_confirmed:false`, `production_authorized:false`.
- `s0-unknown-commit-recovery.test.ts`: **10 testes WA16-01..10 preparados**, para resolver a ambiguidade sem associação a entrega ou venda.

A função **não autentica** a consulta; exige que uma fronteira interna confiável a execute. Seu JSON, se falsificado fora dessa fronteira, é apenas um valor sem autoridade.

## Preparado em PostgreSQL 17, com a porta WA-15B real

- `lab/wa16-produce-unknown-commit-commands.ts`: gera oito argumentos sintéticos via a porta WA-15B realmente importada do PR #2.
- `wa16_pg17_setup.sql`: insere duas intenções bloqueadas na S0, em transação própria, usando o cadastro Meta↔S0 da WA-15C.
- `wa16_pg17_before_rollback.sql`: registra tentativa de fixture mas faz `ROLLBACK`, sem criar vínculo durável.
- `wa16_pg17_after_commit.sql`: confirma outra tentativa com `COMMIT`; o workflow esconde a saída do `psql`, simulando perda da **resposta ao cliente**, não falha física de rede/servidor.
- `wa16_pg17_recover_unknown.sql`: em **nova conexão**, verifica persistência exata após `COMMIT`, ausência após `ROLLBACK`, classificação de conflito, replay somente em banco (sem reenviar Graph), unicidade bidirecional e bloqueio de outbox.
- `wa16_pg17_read_recovery_json.sql` e `wa16-assert-db-recovery.ts`: buscam resultados JSONB das funções S0-042 reais e os passam à classificação TypeScript verdadeira.
- O job `wa15c-cross-branch-pg17` do workflow Meta foi ampliado com etapa WA-16, depois de todas as migrations e 12 testes WA-15C; há **11 marcadores WA16P-01..11**, pré-verificação de oito comandos e uma verificação adicional TypeScript↔PostgreSQL.

**Auditoria estática executada** sobre os arquivos publicados: 10 casos unitários identificados, 11 IDs WA16P distintos, presença de rollback, COMMIT, consulta em sessão separada, verificação de único vínculo, importação real do classificador e chamadas explícitas aos quatro arquivos SQL no workflow.

**Limitação da prova:** ocultar a resposta confirmada ou executar `ROLLBACK` testa dois resultados conhecidos do laboratório; **não demonstra resultado verdadeiramente desconhecido sob falha de conexão durante COMMIT**. Esse cenário requer outro gate e observabilidade de transação. Também não demonstra HMAC, JWT/IAM, API de serviço, ACK após gravação, Graph ou autorização comercial.

## Gates seguintes (não realizados)

1. Confirmar o GitHub Actions WA-16 e analisar logs individuais; reparar eventuais falhas antes de aprovar.
2. Projetar/implementar autoridade mínima de um **serviço interno autenticado**, sem `postgres` como usuário de runtime e sem conceder execução pública a funções privadas. Desenhar privilégios por operação e escopo sob revisão específica.
3. Provar suspensão de Graph retry durante resultado de escrita desconhecido em executor/transport real, com telemetria sem informações pessoais, sem usar serviços reais até autorização separada.

Todos os PRs permanecem Draft. Sem merge, deploy, Supabase hospedado, tokens Meta, banco financiador ou disparos externos.
