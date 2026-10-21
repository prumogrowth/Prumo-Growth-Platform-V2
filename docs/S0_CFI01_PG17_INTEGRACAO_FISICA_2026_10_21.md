# CFI-01 S0/S1 — primeira prova física em PostgreSQL 17 (21/10/2026)

**Status:** testes físicos de PostgreSQL concluídos em runner descartável no GitHub Actions. Integração completa com GoTrue, gateway assinado e F03 **AINDA PENDENTE**. Este documento é evidência de laboratório, não contrato de produção, migration aprovada, homologação do tratamento de dados ou autorização de merge/deploy.

## Execução observável

- **CI final:** [GitHub Actions #39576618344](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39576618344): **SUCCESS**; job `isolated-closure-pg17` na branch S0 de [PR #12 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/12).
- **97/97 PASS** nos testes unitários Python de pré-check S0 (35), captura de evento (42) e autorização S1 local (20).
- **12/12 PASS** nos testes físicos do novo `backend/tests/test_s0_cfi01_pg17_integration.py` com `psycopg`, transações e PostgreSQL **17** isolado. Em particular, testes 08 (duas conexões com mesma chave), 11 (novo inbound com lock em conversa) e 12 (suspensão S1 concorrente).
- O CI anterior [#39576409121](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39576409121) já demonstrara **10/10** físicos; a rodada final ampliou para 12.
- Não somar esta bateria de 109 com os 220 testes de laboratório OpenAI nem os 210 históricos F03: foram executados separadamente.

## Banco descartável, pré-requisitos e isolamento

O workflow `.github/workflows/s0-cfi01-pg17-integration.yml` executa `scripts/run-s0-cfi01-pg17-local.sh` com banco `prumo_s0_test_cfi01` em container PostgreSQL 17 no GitHub Actions. A validação do DSN nega banco remoto/inesperado; cada execução cria o banco temporário; nenhum DSN hospedado nem segredo de cliente participa.

O script aplica somente os componentes S0 necessários: `bootstrap_fake_auth.sql`, migrations S0 `001, 002, 003, 004, 005, 006, 008`, a dependência da S1 038 e a fixture privada CFI-01. A migração S1 038 foi copiada **byte por byte** do PR #5 para `supabase/tests/s0_cfi01_s1_038_reference_local_only.sql`; SHA blob idêntico `7e27a42f19941bf4f1de5e05cc713795d8caf8b7`. É **somente fixture de teste**; não é duplicação de migration de produto nem indicação de que S1 #5 foi mesclado à S0. Em produção, consolidar a integração a partir do contrato verdadeiro da S1, sem duplicar os objetos.

O `auth.sessions` de integração é uma **tabela de teste sintética**, não a sessão gerida pelo GoTrue hospedado. A identidade Python é representada por um `Principal` sintético em vez de token validado pelo servidor de autenticação. O adapter de SQL de teste usa `postgres` local, usuário privilegiado exclusivo do laboratório; não é o executor S0 de produção. O script e a fixture não são migrations de produção.

## Resultados físicos concretos, sem extrapolação

| Cenário | Resultado |
|---|---|
| Mesmo caso, mesma chave e mesmo recorte | `ALREADY_CAPTURED`; um evento privado |
| Novo inbound após captura e replay | `STALE` |
| Suspensão de equipe S1 e tentativa de fechamento | `BLOCKED_S1` |
| Sessão removida no PostgreSQL de testes | `DENIED` |
| Grant da concessionária removido | `DENIED` |
| Atribuição humana encerrada | `DENIED` |
| Segunda chave para o mesmo recorte de mensagens | `DUPLICATE_SNAPSHOT` |
| Duas conexões físicas com a mesma chave | Um `CAPTURED_LOCAL_ONLY` e outro `ALREADY_CAPTURED`, exatamente um evento |
| Versão do ciclo comercial alterada | `STALE`; nenhuma captura |
| Captura técnica comum | Status comercial permanece `em atendimento pelo operador` |
| Novo inbound concorrente com bloqueio da conversa | Nova mensagem aparece na contagem do recorte após commit |
| Suspensão S1 concorrente enquanto `lock_team` aguarda | A solicitação de conclusão é bloqueada; zero eventos |

Os testes de concorrência positivos **não demonstram ausência universal de deadlocks** nem cobrem todas as ordens de bloqueio do produto: exigem testes ampliados de reatribuição/S1, novos canais, outros serviços, erro de commit e failover.

## Bloqueios ainda presentes para fechar os dois marcos combinados

1. **Assinatura técnica CFI-01:** alinhar definitivamente `case_ref`, versão física do ciclo/caso/ficha, evento de conclusão, ID idempotente e recibo `begin/recheck` com os contratos OAI-05, OAI-07, FV e S1. Hoje `expected_cycle_version` é físico; `expected_case_version` FV permanece candidato.
2. **S0 com GoTrue e gateway reais:** implementar autenticação/nonce/HMAC/privilegio mínimo para a operação específica de fechamento; a identidade de CI é sintética. Revalidar equipe/atribuicao normal, e tratar exceção estrita por caso separadamente sem tratar fixture S1-055 como acesso real.
3. **Integração S0→F03:** derivar snapshot minimizado/auditoria do S0 para a porta F03, sem vazar assignment/session/idempotency key ao modelo; implementar rechecagem após resposta e antes de qualquer efeito.
4. **Gravação D3/F03:** contrato canônico de extração, campos/valores/evidências/permissão, aplicação atômica/idempotente e estado técnico somente após commit S0, sem decisões bancárias automáticas.
5. **Expansão de regressão:** integração real com GoTrue/Postgres e testes de dois agentes/lojas/exception por caso e concorrências adicionais; sete suítes históricas F03 de 210 testes ainda não foram rerodadas de forma integrada à base atual.

**Próxima etapa da mesma frente:** integrar o resultado físico a uma operação S0 de `begin/recheck` com contrato assinado e desenho de privilégios, sem aguardar equipe S0 inexistente. A pausa para dúvidas e auditoria geral somente após a conciliação + substituição de concessões fictícias estarem concluídas e comprovadas. PR #12 e #8 permanecem Draft; sem merge/deploy, Meta, Banco ou cliente real.
