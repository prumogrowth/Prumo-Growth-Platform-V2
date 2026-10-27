# S0-035 — Compatibilidade acumulada Supabase Auth/REST local (18/10/2026)

## Escopo e precedência

Este marco documenta a execução deliberada do **workflow GoTrue/PostgREST com Supabase local gerenciado e efêmero** após as migrations S0/028–034. **Não há migração nova** nem alteração comercial, conexão Meta real, serviço externo, custo pago, API privilegiada pública ou instalação no Supabase hospedado.

Normas preservadas: DEC-WA-01/02/03 [D] como diretrizes; DEC-WA-05 [D] define propriedade dos Apps/WABAs/emissores por concessionária, com operação Prumo apenas sob autorização; DEC-WA-04/06 pendentes. O mesmo telefone de cliente pode existir em concessionárias distintas, cada emissor da plataforma continua exclusivo de uma loja. WA-01C e WA-02D da frente Meta seguem candidatos/protótipos isolados, sem dedupe ou ACK real.

## Código efetivamente testado

O commit `fc1c7d2a7a76c9eb7c6dc35c38f4f19f07a3a655` adicionou **somente assertions de teste** ao `scripts/test_s0_auth_rest_local.py`:

- **AUTH-15:** migrações 028–034 carregadas no Supabase local; inspeção SQL de objetos privados, RLS habilitada nas tabelas relevantes, nenhuma permissão de SELECT/INSERT/UPDATE/DELETE aos papéis `anon`, `authenticated`, `service_role`, `prumo_s0_gateway` ou `prumo_s0_signer` sobre as novas tabelas; ausência de EXECUTE das funções C01/C02/inbox/lease pelos mesmos papéis; verificação das FKs compostas `inbox_c02_evento_canal_s0`, `aplicacao_c02_evento_canal_s0`, `aplicacao_c02_mensagem_canal_s0` e presença de triggers de prova.
- **AUTH-16:** cliente anônimo e gestor autenticado com JWT GoTrue recebem erro de indisponibilidade/negativa ao tentar acessar pelo REST comum tabelas privadas da ponte C02 ou RPCs privilegiadas `aplicar_inbox_c02_s0` e `registrar_resultado_ingresso_s0`.
- Os testes antigos **AUTH-01..14** continuam no mesmo roteiro: login GoTrue real (local), leitura do domínio via PostgREST/RLS, gestor A/B, operador atribuído, usuário sem vínculo, escrita permitida de mensagem fictícia, negativas de escrita interloja, recontatos, opt-out, C07 e revogação sem refrescar JWT, sessão viva e gateway HMAC de papel SQL restrito.

## Evidências GitHub Actions

| Execução | Resultado verificado | Observações |
| --- | --- | --- |
| [PostgreSQL 17 #39120145381](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39120145381) | **SUCCESS** | Regressão S0 PG17 para o commit `fc1c7d2`; não é ambiente Supabase |
| [Supabase GoTrue/PostgREST local #39120161917](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39120161917) | **SUCCESS** | Todas as etapas do job, inclusive teardown do sandbox. Nos logs: `AUTH-01..14`, `AUTH-13-REVOKE`, `AUTH-15`, `AUTH-16` **PASS**; nenhum traceback ou erro. CLI Supabase 2.84.2 e driver psycopg 3.2.9 fixados; ambiente não vinculado ao projeto hospedado |

Foi aplicada temporariamente a label `run-auth-integration` no PR #1 para acionar o fluxo caro uma vez e **removida após sucesso**. O workflow mantém `timeout-minutes: 12`, `cancel-in-progress: true` e o Supabase local é encerrado por `supabase stop --no-backup`.

## O que foi realmente comprovado

1. As migrations 028–034 foram aceitas pelo inicializador do Supabase local gerenciado com a configuração versionada, sem repetir os erros históricos de owner/ACL anteriores ao aceite S0-027.
2. O GoTrue local emite tokens de teste; a Data API/PostgREST respeita as permissões e o isolamento testado. O acesso público à ponte C02 e à inbox restrita continua negado; `service_role` não ganhou grants sobre as tabelas e funções privadas listadas.
3. FKs compostas e triggers de prova da S0-034A existem e estão habilitados nesse ambiente. A regressão de regras e concorrência **funcional** C02/identidade foi feita no PostgreSQL descartável separado e não deve ser confundida com tráfego via PostgREST.

## Limitações / NO-GO

- **Sem teste de worker autenticado de privilégio mínimo para aplicar C02/C07 via Supabase local.** O teste assegura principalmente instalação, isolamento da Data API e ausência de exposição das funções; não prova que um eventual futuro worker possa executar essas operações com sessão e privilégio adequados.
- Rotinas comerciais `SECURITY DEFINER` pertencentes a `postgres` ainda aguardam auditoria/redução de privilégios. O verificador HMAC da S0/027 está isolado, as wrappers comerciais **não**.
- Sem segredo Meta por App, autenticidade do POST, aceite durável de payload Meta original, cofre, retenção LGPD, restore, monitoramento de negativas, revalidação de envio ou ACK HTTP real. `APPLIED_ATOMIC` sintético não equivale a `COMMITTED` de um ingressor Meta real.
- WA-01C informa que `statuses[].id` não é ID único de callback; WA-02D continua simulador offline/in-memory. **Não** conectar callbacks à inbox usando o hash de status como dedupe definitiva.
- Os resultados não provam deploy/compatibilidade no **Supabase hospedado**. O projeto hospedado permanece sem migrações e tabelas comerciais. Não executar SQL comercial nele sem autorização específica.
- Nenhum PR foi mesclado. PR #1 e PR #2 permanecem Draft.

**Gate: GO** para continuar desenvolvimento e testes sintéticos usando o baseline 028–034 no Supabase local gerenciado. **NO-GO** para API privilegiada pública, operação real Meta/instituição financeira, número comercial, compra de recursos, migração hospedada ou produção.

## Próximo incremento recomendado

Auditar a cadeia de privilégios das wrappers comerciais `SECURITY DEFINER postgres` e projetar uma redução compatível com PostgreSQL de testes e Supabase local gerenciado, preservando Auth, sessão, loja, HMAC, nonce, versão e idempotência. Em paralelo, receber da frente Meta o contrato final de ocorrência durável C07; não conectar o simulador de status antes de contrato aprovado.
