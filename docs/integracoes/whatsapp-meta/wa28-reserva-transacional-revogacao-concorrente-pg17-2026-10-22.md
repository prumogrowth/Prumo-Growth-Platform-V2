# WA-28 — Reserva e revogação concorrentes (PostgreSQL 17 descartável)

**22/10/2026 · PR [#2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2) · Integração WhatsApp/Meta, somente laboratório.** Complementa [WA-26](./wa26-ponte-s0-catalogo-politicas-fases-offline-2026-10-22.md) (gates candidatos) e [WA-27](./wa27-pg17-rls-finalidades-revogacao-2026-10-22.md) (RLS e revogação entre sessões). Decisões funcionais continuam em [00/WDC-10/11](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md) e [01](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md).

## Resultado verificado

[GitHub Actions **#39866359225**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39866359225), commit de código/workflow `6f48e919fa45bc5171fbb349b4bb5199d9dc9ede`: **3/3 jobs SUCCESS**. Regressão Node 22 **567/567 PASS**, WA-06D PostgreSQL 17 PASS, WA-15C/WA16/WA27 PASS e **WA-28 21/21 PASS** em PostgreSQL 17 físico descartável. Os 21 marcadores foram conferidos individualmente no log do job, não presumidos.

## Construído nesta etapa

- [`wa28_pg17_atomic_reservation.sql`](../../../integrations/whatsapp-meta/lab/wa28_pg17_atomic_reservation.sql): **schema separado `wa28_lab`**, com tabela `authority`, tabela `reservations` e funções de **ensaio** `attempt_reserve`/`revoke_fixture`. Ambas travam a **mesma linha de autoridade** com `SELECT ... FOR UPDATE`; toda revogação incrementa a versão e cancela reservas da mesma loja/caso. A reserva exige ator, concessionária/caso, versões do caso/catálogo e gates de consentimento, opt-out, atribuição, grant e status de template válidos. Chave composta impede tentativa duplicada. Constraints SQL exigem `send_authorized=false` e `production_authorized=false` sempre.
- [`wa28-assert-concurrent-pg17.py`](../../../integrations/whatsapp-meta/lab/wa28-assert-concurrent-pg17.py): orquestra **duas conexões PostgreSQL independentes**, observando conflitos reais em `pg_blocking_pids` sem depender de `sleep` fixo; valida `COMMIT`, `ROLLBACK`, deduplicação e ausência de contaminação entre lojas. Recusa DSN fora do PostgreSQL local de CI e saneia variáveis PG* herdadas.
- [Workflow CI](../../../.github/workflows/whatsapp-meta-offline.yml): executa e valida os **21 marcadores**. Ações inválidas, incluindo tipo de revogação `NULL`, são negadas sem alterar reservas ou versão.

**Interleavings demonstrados em banco físico:**
1. A reserva da loja A trava o caso **antes** da revogação. A revogação espera; após o COMMIT da reserva, cancela a reserva e faz opt-out. Nova tentativa é negada.
2. A revogação de grant da loja A trava o caso **antes** da reserva. A reserva espera; após COMMIT da revogação, termina negada, sem criar registro.
3. Retentativa idêntica produz `LAB_ALREADY_RESERVED`, sem registro duplo. Uma transação de reserva seguida de ROLLBACK deixa zero registros duráveis; ator errado, versão antiga, outra loja e template pausado não passam.
4. A loja B mantém autoridade própria e não sofre revogação da A.

## Limites e dependências importantes

**O laboratório não autentica usuários nem concede autorização real.** `actor_ref` e `shop_ref` são parâmetros fictícios, não JWT/GoTrue verificado ou grants S1 autenticados; a fixture executa como proprietário em banco temporário. Não há um serviço S0 real, RLS/roles produtivas, assinaturas, catálogo/consentimento/campanha reais nem autorização de C06/Meta Graph. Reservar em PostgreSQL **não** transmite mensagens e não prova `sent`, ACK, benefício comercial ou estado bancário.

Os locks testados cobrem **uma linha fictícia da autoridade dentro do mesmo schema WA28**. Não constituem prova de ausência de deadlock na S0/S1 real, nem da ordenação S1 equipe → S0 caso exigida pelo contrato [PR #12 — ordem dos locks](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/feat/s0-cfi01-f03-auth-preflight-20261020/docs/S0_CFI01_S1_TRANSACAO_ORDEM_LOCKS_2026_10_21.md). Não há lease/claim transacional ratificado entre última verificação e dispatch Graph; revogação **depois** do despacho precisará de conciliação. Sem integração física com autenticação, não declarar fechamento do risco TOCTOU em produção.

**Dependência próxima:** com S0/S1 definir escopo autenticado, ordem de locks, isolamento por caso/loja, contrato da reserva, expiração/cancelamento e gate final de despacho no mesmo protocolo transacional. Implementação só no domínio dono após ratificação e testes interfrentes. Nesta entrega, arquivos foram alterados **apenas** no laboratório WhatsApp/Meta, workflow dedicado e documentação própria. **Sem merge, deploy, Meta Graph, Supabase hospedado ou mudança nas outras branches.**
