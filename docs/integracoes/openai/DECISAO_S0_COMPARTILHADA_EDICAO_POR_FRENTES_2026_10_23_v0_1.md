# Decisão executiva — S0 compartilhada, adaptável por cada frente | 23/10/2026

**Origem:** esclarecimento e autorização expressa do responsável nesta conversa. **Precedência:** substitui qualquer leitura de alinhamentos antigos que coloque a S0 como uma **frente exclusiva ativa** ou como dependência cujo proprietário externo precisa implementar mudanças antes de a frente OpenAI continuar. Modifica também o limite anterior de E04 **quanto à implementação necessária da S0**, sem liberar E05, deploy, migrações reais, merge, segredos ou quebra de outras frentes.

## Responsabilidade correta

A S0 teve uma frente responsável no passado, que implementou o backend inicial. Essa frente **mudou de missão**. **Atualmente não existe frente dedicada exclusivamente à S0.** A S0 é infraestrutura compartilhada em evolução, alterada pelas frentes que precisam de recursos nela.

A frente OpenAI responde integralmente por **F01, F02 e F03**, incluindo contratos, implementação e testes e **as adaptações no lado S0 necessárias a essas IAs**. Não transferir F03 ao backend nem esperar que um inexistente proprietário da S0 edite seu próprio módulo.

**Regra operacional:** ao detectar ausência de interface S0 necessária, a frente OpenAI deve:
1. Examinar o código S0 **atual** e como outras frentes o utilizam (PRs, contratos, schemas e testes).
2. Implementar a alteração mínima e **aditiva** na S0, preservando ACL, isolamento de concessionárias, integridade transacional, auditabilidade, idempotência e contratos existentes.
3. Usar branch independente baseada na versão S0 compatível, especialmente se a S0 ainda estiver em PR Draft não mesclado, para não alterar uma branch ativa de outra frente. Quando necessário, abrir **PR empilhado** sobre a branch S0 existente, com testes e comparação contra base; sem merge automático.
4. Rodar testes compatíveis e registrar limitações reais de CI/PG17; vincular o novo contrato à frente OpenAI e solicitar revisão cruzada quando houver risco de incompatibilidade, **sem paralisar o desenvolvimento por falta de proprietário S0**.
5. Onde provas físicas de autenticação, histórico, versão, catálogo ou consentimento ainda não existirem, implementar **portas que falham em fechado**, sinalizar pendências verdadeiras e continuar E04 com dados falsos; nunca inventar autorização ou promover stubs a produção.

**Separação de papéis:** a S0 continua sendo quem **autoriza e aplica**, e as funções OpenAI **interpretam e propõem**. Mudar código S0 dentro da nossa frente não desloca controle estrutural para a IA F01/F02/F03. F03 permanece nossa função.

## Primeiro exercício comprovável: F03 exige histórico de múltiplos casos

Em 23/10/2026, foi criada branch `feat/oai-s0-f03-history-port-20261023`, baseada em `948891714f632adb6179cf3a11f362a6eb914f91` da S0 PR #12, e aberto [PR #16 — porta S0/F03 histórica local](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/16) contra a branch do PR #12.

Novo código **diretamente no backend S0**: `backend/s0_f03_history_manifest_local.py` e 20 testes. A S0 recupera a identidade e o cutoff **de evento autenticado no banco local**, seleciona **metadados multi-casos** por pessoa e concessionária, faz recheck antes/depois, valida watermark e restringe leitura a PostgreSQL local descartável. **Não fornece conteúdo à F03, não grava ficha e não afirma que o histórico está congelado integralmente**. Resultado elegível = `REVIEW_ONLY_NOT_FROZEN`.

**Evidência:** 24/24 unit tests Python 3.13 locais com fac-símiles dos contratos S0, arquivos publicados com SHA idêntico ao executado; teste no checkout S0 real / PG17 físico **ainda não executado**. PR #16 mantém Draft e não modifica a branch S0 PR #12; nenhum deploy, migração ou merge.

## Portões ainda necessários, sem transformar em bloqueio de autoria

- Imutabilidade integral do manifesto de todos os casos da pessoa/loja no instante de conclusão, inclusive prevenção contra inserções retrodatadas.
- Auditoria/retenção e política legal de mídia/transcrição; identidade de múltiplos telefones validada na S0.
- Versões separadas de ficha, caso, catálogo, atribuição/identidade; recheck transacional no instante da aplicação; conflitos/retificações com evidência.
- Ratificação de interface física S0↔F03, testes PG17 e integração contínua antes de promovê-la de laboratório.

**Sem dependência de uma frente S0 exclusiva.** Implementar essas mudanças de forma segura na própria frente OpenAI quando couber, sem modificar indevidamente trabalho de outras frentes. **E04 de desenvolvimento offline está autorizada.** E05/serviços reais, deploy, merge e alterações destrutivas permanecem sujeitos a portões próprios.
