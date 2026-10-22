# WA-29 — Reivindicação única pré-despacho e revogação concorrente (PG17)

**22/10/2026 · PR [#2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2) · WhatsApp/Meta · Prova física somente em PostgreSQL 17 descartável.** Estende o ensaio [WA-28](./wa28-reserva-transacional-revogacao-concorrente-pg17-2026-10-22.md); respeita [WA-25/26](./wa26-ponte-s0-catalogo-politicas-fases-offline-2026-10-22.md). Não substitui decisões WDC-10/11 nem ratifica contratos interfrentes S0/S1.

## Resultado físico

[GitHub Actions #39867666346](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39867666346), código no commit `564fd392070519601b247511c9559103e89672e0`: **três jobs SUCCESS**, inclusive **23/23 marcadores WA29** no PG17, com **três conflitos de bloqueio observados** pelo PostgreSQL; WA28 (21), WA27 (14), WA15C/WA16 e WA06D preservados. A regressão Node 22 permanece **567/567 PASS**.

## O que foi construído

- [`wa29_pg17_dispatch_claim.sql`](../../../integrations/whatsapp-meta/lab/wa29_pg17_dispatch_claim.sql): um **schema independente `wa29_lab`**, somente para teste. Modela autoridade de caso, reserva prévia e `claims` por `(loja,caso)`, com referência à tentativa original. A função fictícia `claim_fixture` exige escopo/ator/versões, reserva já existente, consentimento, ausência de opt-out, elegibilidade do caso/campanha, grant e status do template. Todas as consultas capazes de alterar o estado travam primeiro a mesma linha de autoridade (`FOR UPDATE`) e depois a reserva. O resultado `LAB_CLAIMED_NO_SEND_RIGHTS` representa **apenas um marcador interno**, nunca um token ou permissão Graph.
- `revoke_fixture`: simula revogação de opt-out, grant, template, campanha ou caso, incrementa a versão e marca a reserva e claim pendentes como cancelados/invalidados. Nenhum privilégio real do serviço S0/S1 é implementado.
- [`wa29-assert-claim-races-pg17.py`](../../../integrations/whatsapp-meta/lab/wa29-assert-claim-races-pg17.py): duas sessões reais independentes e `pg_blocking_pids` para demonstrar a ordem de execução; testa ROLLBACK, tentativa repetida, duas tentativas distintas, versões/ator/loja errados, consentimento/campanha/grant inválidos, ação NULL e isolação de B. Restringe a conexão ao banco temporário específico e descarta variáveis PG* herdadas.
- O [workflow offline](../../../.github/workflows/whatsapp-meta-offline.yml) executa a prova após WA-28 e confere cada um dos 23 marcadores, falhando se algum faltar ou duplicar.

**Três conflitos físicos reproduzidos:**

1. A **claim** recebe o bloqueio primeiro. A revogação espera; após `COMMIT`, invalida a claim ainda não consumida e cancela a reserva. Tentativa posterior fica negada.
2. A **revogação** recebe o bloqueio primeiro. A tentativa de claim espera; após `COMMIT`, é recusada sem gravar claim.
3. **Duas tentativas de claim** disputam o mesmo caso. A segunda aguarda e perde após a primeira gravar. Repetição **da mesma tentativa** retorna `LAB_ALREADY_CLAIMED_NO_RETRY`, nunca um novo direito de transmitir.

## Limites que NÃO podem ser ultrapassados

- **Não existe transporte Meta acoplado à transação.** Uma claim persistida não transmite WhatsApp, não representa `API_ACCEPTED`, `sent`, autorização C06 ou êxito bancário. `send_authorized=false` e `production_authorized=false` estão protegidos por constraints de laboratório.
- **A janela entre `COMMIT` da claim e um eventual POST Graph real continua sendo um risco**: se uma requisição externa já tiver saído, a invalidação do registro **não desfaz** o envio. Para um adaptador operacional, será necessário protocolo ratificado S0/outbox/transport, recheck final e conciliação de resultado incerto, sem repetição automática que gere mensagem dupla.
- Não existe GoTrue/JWT, papel S1 real, RLS de aplicação, autenticação de `actor_ref`, prova consentimento/opt-out/campanha legítima, serviço Meta, controle de janela 24h, vigência real nem fluxo de cadência F02/F03. Todos os dados, ids, papéis e permissões são **fixtures não confiáveis**. `claim_fixture` jamais deve ser reutilizada como serviço produtivo.
- **A ordenação S1 → S0** documentada no [PR #12](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-cfi01-f03-auth-preflight-20261020/docs/S0_CFI01_S1_TRANSACAO_ORDEM_LOCKS_2026_10_21.md) não foi testada aqui; o ensaio trava apenas uma linha de autoridade fictícia. Isso não é prova de ausência de deadlock transfrentes.
- O índice único por caso é uma restrição **de ensaio para reivindicação pendente**, não a decisão sobre múltiplas tentativas/cadências reais. Expiração, recuperação após queda, estados de observação do Graph, liberação segura e transições comerciais continuam sem contrato operacional.

**Próximo gate:** ratificar com os donos S0/S1 identidade/locks e o envelope de reserva→claim→envio→conciliação antes de construir uma implementação autenticada. Não tocar em outras branches nem mudar migrações, RLS, segredo, Meta Graph ou produção.

**Escopo preservado:** somente `integrations/whatsapp-meta/lab/`, workflow da própria frente e documentação WhatsApp/Meta. PR #2 segue Draft, sem merge ou deploy.
