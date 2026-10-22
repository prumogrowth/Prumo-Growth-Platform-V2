# WA-31 — Evidências tardias após revogação: preservação forense sem reautorizar

**22/10/2026 · [PR #2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2) · Frente WhatsApp/Meta, exclusivamente laboratório offline PostgreSQL 17.**

## Contexto e decisão técnica do laboratório

[WA-30](./wa30-recuperacao-envio-incerto-ledger-offline-pg17-2026-10-22.md) recusa novos eventos de **operação** quando a reivindicação, opt-out ou grant do caso foram revogados. Isso protege os gates de envio; mas **uma confirmação de transporte pode chegar tardiamente** depois da revogação. Descartá-la do registro forense perderia a capacidade de investigar se houve uma tentativa antiga. WA-31 separa dois caminhos:

- **Porta operacional** WA-30: segue negando evidência em claim invalidada; não cria permissões nem estados comerciais.
- **Porta forense** WA-31: arquiva somente um sinal **sintético e não autenticado**, vinculado a uma tentativa que já existia, mesmo após revogação; não muda `wa29_lab.claims`, não reabre uma reserva, não envia nem autoriza Graph, não incrementa a cadência e não concede ACK.

Essa separação é um **experimento**, não uma decisão de arquitetura operacional ratificada por S0/S1 nem integração verdadeira com webhooks Meta.

## Implementação e provas

**[GitHub Actions #39870801973](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39870801973)** no commit de código `3a57015f99ba680ab7a2a38b644298916b96d3d0`: **3/3 jobs PASS**, regressão **603/603 testes Node** (18 testes novos) e **31/31 verificações físicas WA31 PG17**, com **12 snapshots PG17 → TypeScript** e **dois bloqueios concorrentes observados via `pg_blocking_pids`**. Regressões WA06D/15C/16/27/28/29/30 continuam verdes.

Arquivos criados apenas na frente Meta:

1. `integrations/whatsapp-meta/wa31-late-evidence-classifier.ts` e `.test.ts` (18 testes). Classificador de envelope mínimo, sem identificadores ou conteúdo. Distingue claim sem observações, evidência ainda ativa mas não verificada, revogação sem evidências, evidência histórica antes da revogação, observação tardia depois da revogação, conflito em quarentena, ausência/escopo incorreto e snapshot não confiável. Nega campos extras, tipos frouxos, getters, proxies, sinais de transporte como prova de entrega e qualquer flag afirmativa de autorização.
2. `integrations/whatsapp-meta/lab/wa31_pg17_late_evidence.sql`: schema de fixture **`wa31_lab` independente**, tabelas `observations` e `quarantines`. As flags `send_authorized`, `production_authorized`, `ack_allowed` e `definitive_failure_count_increment` possuem `CHECK(NOT ...)`. Um registro só é aceito com relação exata a uma claim previamente existente para loja/caso/tentativa; a porta trava primeiro a linha da autoridade fictícia e depois a claim. Eventos repetidos com mesmo identificador sintético e tipo retornam `LAB_REPLAY_NO_RESEND` sem duplicar; identificador reapresentado com natureza diferente coloca a tentativa em quarentena sem sobrescrever o histórico.
3. `integrations/whatsapp-meta/lab/wa31-assert-late-evidence-pg17.py` e `wa31-assert-db-late-evidence.ts`: verifica datas relativas de gravação em relação ao estado invalidado, replay, colisão, revogação de opt-out e grant, escopo B, attempt inexistente, entrada inválida, rollback, invariantes `send_authorized=false`, preservação das claims revogadas e inalterabilidade do ledger **WA-30**. Doze respostas do banco são classificadas pela implementação TypeScript real.
4. `.github/workflows/whatsapp-meta-offline.yml` adiciona o gate WA31 após WA30 e exige 31 marcadores distintos no job PG17.

### Concorrência provada

- **Revogação primeiro:** transação de revogação trava a autoridade; uma escrita forense espera e, após COMMIT, arquiva como `LAB_ARCHIVED_AFTER_REVOCATION`, **sem revalidar a claim para envio**.
- **Evidência primeiro:** gravação arquiva o sinal como não verificado; uma revogação espera e, após COMMIT, invalida a claim. O registro anterior permanece para auditoria, mas a rechecagem do caso retorna `LAB_INVALIDATED_HISTORICAL`.

## Contratos pendentes e restrições

- **Não existe conexão real com webhooks Meta, Graph ou verificação de assinatura.** Os identificadores `event_ref` são **eventos sintéticos do laboratório**, não prova de `wamid`, recibo Meta ou entrega. O runner fornece valores arbitrários como administrador local do PG17. Isso não representa acesso legítimo do serviço S0/S1 nem autenticação JWT/GoTrue.
- A gravação tardia é **forense, não operacional**. Ela não pode emitir ACK para a Meta, responder ao cliente, reabrir uma janela de atendimento, reativar consentimento, atualizar histórico comercial nem contar falha definitiva de template para WDC-13.
- Se um envio saiu **antes** da revogação, nenhuma transação local consegue desfazer esse fato externo. Se o envio é incerto, a classificação permanece **HOLD/QUARANTINE**, não *retry* por ausência de linha. Nenhuma consulta a Graph foi realizada para conciliar o estado externo.
- A prova usa somente uma linha fictícia de autoridade em `wa29_lab`, sem locks reais S1→S0, RLS de autenticação produtiva, privilégios mínimos, serviço de recebimento de webhook, retenção LGPD, observabilidade multi-WABA, cadência comercial ou idempotência do transporte.
- O plano de integração com as frentes donas precisa definir: porta forense autenticada com identidade de mensagem e tenant/WABA verificados, política de retenção e minimização, assinatura e replay idempotente, correlação com tentativas S0, reconciliação do transporte e ordem de locks interfrentes. Só então cabe propor migrações e rotas reais, sujeitas à revisão de segurança.

**Estado:** PR #2 continua **Draft**, sem merge, deploy, migrações em produção, segredos, contato com Meta ou alteração do código de S0/S1/OpenAI/frontend.
