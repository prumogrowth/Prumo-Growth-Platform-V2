# E04 — S0/F03: novo repositório oficial e teste físico do CAS de versões

> **ATUALIZAÇÃO POSTERIOR — versão das fontes de escrita S0 implementada e validada:** [relatório de 229/229 testes PG17](./S0_F03_VERSOES_AUTOMATICAS_S0_PG17_229_TESTES_2026_10_24.md). A [execução #40061833588](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40061833588) passou com 84 S0 + 145 F03, dos quais **57 físicos F03 PG17.11**. A nova fixture contém gatilhos nas tabelas S0 existentes de lead, caso e atribuição humana, além de fontes **somente sintéticas** de ficha e catálogo. A afirmação anterior de 213 testes permanece como histórico da etapa pré-gatilhos; não implica que a F03 já pode aplicar campos reais.

**Data:** 24/10/2026. **Repositório único autorizado:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`. **Branch da adaptação S0/F03:** `feat/oai-s0-f03-history-port-20261023`; base `feat/s0-cfi01-f03-auth-preflight-20261020`. **PR Draft #1**, nenhum merge/deploy e nenhuma alteração no repositório anterior.

## Prova de preservação do espelho

Antes de escrever, foi confirmado pela API GitHub, no repositório novo, que as branches correspondem aos commits anteriores:
- OpenAI F01/F02/F03: `feat/s2-openai-adapter-sintetico` em `ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c`.
- S0/F03: `feat/oai-s0-f03-history-port-20261023` em `b4d9f91d930b94ce0cd0f424dd3c5c723d4e7f1e`.
- Base S0: `feat/s0-cfi01-f03-auth-preflight-20261020` em `948891714f632adb6179cf3a11f362a6eb914f91`.
Arquivos essenciais do leitor CAS, fixture SQL e workflow também foram comparados por SHA blob. A cópia preservou o código e histórico relevante. A partir desta mudança, apenas o novo repositório é alvo de operações de escrita.

## A execução que estava pendente agora passou

**[GitHub Actions #40061037165](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40061037165)**, PR #1, commit espelhado `b4d9f91d930b94ce0cd0f424dd3c5c723d4e7f1e`:

- Job `f03-pg17-disposable` concluído `success`, contêiner **PostgreSQL 17.11**.
- Suíte S0 CFI-01: **84 testes, OK**.
- Suítes F03: **129 testes, OK**, compostos de 24 do leitor multi-casos, 31 do selo de metadados, 15 da barreira de autorização HMAC, 18 do CAS unitário e **41 físicos PG17**.
- **TOTAL 213/213 PASS**. Os 18 casos físicos novos incluem divergência das cinco versões, replay, duas propostas concorrentes, ausência de fonte/HMAC, bloqueio de atualização, isolamento ACL, atribuição encerrada, alteração da versão do ciclo e imutabilidade do recibo.

O bloqueio anterior de GitHub Actions (`runner_id=0`, `steps=[]` no repositório espelhado de origem) **não se reproduziu aqui**: o workflow desta branch foi inicializado, executou o banco e finalizou. Não era correto interpretar as falhas de inicialização anteriores como falha do código.

## O que está pronto e o que continua limitado

**Pronto e testado em ambiente sintético:** persistência append-only de manifesto multi-casos, prova HMAC para texto histórico da fixture, rechecagens de S0 e **reserva CAS consultiva de cinco versões independentes** (ficha, catálogo, caso, atribuição e identidade). A reserva recusa alterações entre leitura e decisão e limita o mesmo encerramento a um único recibo. **Ela não altera os campos da ficha nem o status do cliente.**

**Não está pronto:** ligação das versões de laboratório aos escritores S0 de produção; garantia global de completude histórica inclusive outras mídias, identidade multi-telefone, política/rotação de chaves HMAC reais, concessão limitada de dados à F03, mapeamento seguro de evidência campo a campo e aplicação final com CAS na ficha real. Nenhuma dessas operações é autorizada pelo estado `REVIEW_ONLY`.

**Governança:** S0 é componente compartilhado e adaptável pela nossa frente OpenAI, que mantém responsabilidade integral por F01, F02 e F03. O PR da adaptação fica **Draft** e não pode ser mesclado à base ou à `main` sem autorização. Nenhum serviço OpenAI pago, Meta/WhatsApp real, Supabase hospedado ou dado pessoal foi usado nesta rodada.
