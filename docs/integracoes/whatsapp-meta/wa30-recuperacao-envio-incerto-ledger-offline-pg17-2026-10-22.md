# WA-30 — Recuperação de envio incerto: evidência durável sem reenvio (PG17 + TypeScript)

**22/10/2026 · [PR #2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2) · Escopo exclusivo WhatsApp/Meta, laboratório isolado.** Continua [WA-29](./wa29-claim-unico-pre-despacho-revogacao-concorrente-pg17-2026-10-22.md) e a semântica [WA-16](./wa16-commit-incerto-e-recuperacao-laboratorio-2026-10-20.md) de falha de confirmação transacional, sem convertê-las em integração Meta real.

## Evidência executada

**[GitHub Actions #39869583349](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39869583349)** — commit de código e workflow `a6da27885e233cf065af8ded13abb76c0a5f6b68`: **3/3 jobs SUCCESS**, **585/585 testes Node 22 PASS** (18 novos WA30), **27/27 verificações WA30 PG17 PASS** e **11/11 snapshots lidos do banco e interpretados pelo módulo TypeScript**, além de toda regressão WA06D/WA15C/WA16/WA27/WA28/WA29 existente.

## Desenvolvimento concluído

1. **Classificador puro e defensivo**, `integrations/whatsapp-meta/wa30-uncertain-dispatch-recovery.ts`, acompanhado de `wa30-uncertain-dispatch-recovery.test.ts`. Lê apenas o envelope mínimo do laboratório, rejeita alterações de estrutura, propriedades extras, getters, proxies, valores que autorizam operação, categorias de evento inventadas e objetos desconhecidos. Resultados diferenciados:
   - `LAB_HOLD_UNRESOLVED`: reivindicação persistida, nenhum resultado conclusivo;
   - `LAB_ABSENT_STILL_UNCERTAIN`: falta de registro local **não prova** que uma requisição Graph não saiu;
   - `LAB_ACCEPTED_NOT_SENT`: registro de aceitação não representa `sent`, entrega ou sucesso;
   - `LAB_SENT_REPORTED_UNVERIFIED` e `LAB_FAILURE_REPORTED_UNVERIFIED`: sinal **somente de fixture**, sem autoridade de webhook, sem comprovação de envio/falha definitiva;
   - `LAB_INVALIDATED_HOLD`: reivindicação invalidada por revogação;
   - `LAB_CONFLICT_QUARANTINE`: sinais contraditórios ou recibo vinculado a naturezas distintas;
   - `LAB_UNTRUSTED_SNAPSHOT`: envelope inválido/não reconhecido, bloqueio preventivo.
2. **Persistência ficcional independente**, `integrations/whatsapp-meta/lab/wa30_pg17_unknown_outcome.sql`: adiciona somente o schema `wa30_lab` no PG17 descartável após o laboratório WA29, com `evidence` (chave exata loja/caso/tentativa/identificador de evento e constraint sem autorização), `quarantine`, função `record_fixture` e consulta `read_fixture`. A gravação revalida o estado de `wa29_lab.authority` e de `wa29_lab.claims` sob bloqueio da mesma linha usada pela revogação; recusa evidência de outra concessionária, tentativa inexistente, claim invalidada ou entrada malformada. Reapresentação exata do mesmo identificador e categoria devolve `LAB_REPLAY_NO_RESEND` sem duplicar; reuso contraditório do mesmo identificador coloca a tentativa em quarentena.
3. **Validação física**, `wa30-assert-uncertain-pg17.py` e `wa30-assert-db-recovery.ts`: verifica aceitação não convertida em envio, sinal enviado/fracassado **não autenticado**, coexistência contraditória → quarentena, retenção de evidências mesmo após opt-out, bloqueio de novos eventos após revogação, ausência de autorização em todas as linhas, separação A/B e transação de gravação revertida por `ROLLBACK`. Testa conflito efetivo de lock **evidência antes → revogação depois**, observando `pg_blocking_pids`; depois do COMMIT da revogação, a recuperação aponta **invalidação**. Os 11 snapshots PostgreSQL alimentam o mesmo classificador TypeScript testado em Node.
4. **Integração de testes**, na workflow `.github/workflows/whatsapp-meta-offline.yml`: gate WA30 após WA29 com verificação individual de 27 marcadores; se falhar qualquer etapa, o job fica vermelho.

## Invariantes de segurança

Para **todos os resultados**: `retry_external=false`, `send_authorized=false`, `ack_allowed=false`, `production_authorized=false`, `delivery_confirmed=false`, `definitive_failure_count_increment=false`, `case_transition_authorized=false`. Nenhum evento sintético é `sent` verificado pela Meta, e nenhum `FAILED_REPORTED` aciona a regra de **duas falhas definitivas consecutivas** da cadência WDC-13. A transição comercial de caso segue exclusiva da S0. **Nunca reconstruir um POST Graph a partir do ledger ou da ausência de uma claim**.

## Limites de homologação e dependências

Este trabalho **não** autentica uma sessão GoTrue/JWT, não certifica identidade S1, titularidade do caso, fonte do webhook Meta, `wamid`, horário da janela de 24h nem campanhas/ofertas reais. O ledger contém **sinais simulados de teste**. Uma prova do banco local não equivale a prova de transporte Graph ou entrega WhatsApp. Não há ACK, envio, consulta à Meta, segredo, cobrança, atualização comercial, produção, migração S0 ou merge. A fila de outbox, lease/claim, verificação imediatamente antes de POST, resultado HTTP perdido, webhook tardio e as políticas de reenfileiramento ainda exigem contrato ratificado.

**Fronteira interfrentes:** S0/S1 devem autenticar principal, delegação por loja/caso e ordem de locks real (S1 equipe → S0 caso); serviço Meta deve receber autorização limitada e versionada e não confiar nos JSONs simulados de WA30. Sem acordo sobre idempotência do transporte e resultado externo incerto, o sistema permanece em HOLD/QUARANTINE e **não tenta reenvio por conta própria**.

**Estado:** PR #2 permanece Draft, sem merge, deploy, chamadas reais Graph ou alterações nas branches S0/S1/OpenAI/frontend.
