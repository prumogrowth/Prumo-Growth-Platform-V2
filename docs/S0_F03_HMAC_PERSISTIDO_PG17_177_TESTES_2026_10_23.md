# E04/S0 — HMAC de conteúdo persistido e vinculado ao manifesto F03 (23/10/2026)

**Estado: implementado e testado em PostgreSQL 17.11 descartável no GitHub Actions.** A frente OpenAI implementou a adaptação diretamente na S0 compartilhada, exclusivamente offline. PR #16 permanece Draft, empilhado sobre PR #12 sem alteração de sua branch; sem API OpenAI/Meta, dado real, deploy, migração hospedada ou merge.

## Evidência física — fonte de verdade dos resultados

| Run do GitHub Actions | Resultado | Composição exata |
|---|---|---|
| [#40032573748](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40032573748) | **162/162 PASS** | 84 S0 CFI-01 + 78 F03 (24 leitor, 31 manifesto, 23 PG17 físico) |
| [#40032787969](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40032787969) | **177/177 PASS** | 84 S0 CFI-01 + 93 F03 (24 leitor, 31 manifesto, **15 testes de autorização** e **23 testes físicos PG17**) |

**Logs da segunda execução:** `Ran 84 tests ... OK` e `Ran 93 tests ... OK`, job `f03-pg17-disposable` concluído `success`; imagem de banco `PostgreSQL 17.11`. Os nove novos testes físicos F03 (15–23) comprovaram prova HMAC persistida, consulta repetida, detecção de mudança de texto e mensagem retrodatada, negação de mudança de versão de chave, impossibilidade de criar prova sem manifesto, triggers de imutabilidade, ACL negativa e **dois escritores simultâneos gerando apenas um registro**. Os 15 testes adicionais confirmaram duplo recheck autorizado, falta/revogação de autorização, chave inválida, leitura sem gravar, isolamento do DSN e resposta sem segredo.

## Entregas versionadas

- [`backend/s0_f03_bound_content_seal_local.py`](../backend/s0_f03_bound_content_seal_local.py), blob Git `c475de723507c3c439c8e3955c15e4bb550ca730`: nova porta interna S0. Exige recibo CFI-01 com tipo S0 e chave de prova com versão explícita. `S0F03LocalBoundContentBridge` exige **`history.verify` antes e depois**, e `S0F03LocalBoundContentStore` bloqueia a linha da pessoa (lead) e suas conversas, lê as mensagens em uma transação e guarda o **HMAC-SHA256** e hash de metadados na mesma transação. A verificação compara valor e versão de chave com o conteúdo vivo. Retorno positivo **somente `*_REVIEW_ONLY`**.
- [Fixture SQL local](../supabase/tests/s0_f03_history_seal_local_only.sql), blob `5bc526ccad9ee770fa49b032786075a018bfc3d5`: tabela adicional `prumo_private.cfi01_f03_content_proofs_local`, FK composta para evento+loja de manifesto pré-existente, um recibo por evento, comparação de hash/contagens por gatilho, `UPDATE/DELETE` proibidos, RLS e nenhuma permissão direta para usuário `authenticated`. Armazena **identificador da versão de chave**, HMAC e contagens; **não** chave nem texto.
- [23 testes físicos](../backend/tests/test_s0_f03_pg17_integration.py), blob `11f18d4c0c301cf935418e200c8d7238c6414ada`.
- [15 testes de pré/pós autorização](../backend/tests/test_s0_f03_bound_content_seal_local.py), blob `86ebfff80447aee0d1fc5c36605881ae7b75e070`.
- [Executor PG17 descartável](../scripts/run-s0-f03-pg17-local.sh), blob `b9c4eae87d356e27b44a45580667a569c3f1ff8d`, agora invoca as quatro suítes F03 (24+31+15+23) além das 84 S0.

## Limites técnicos e segurança — não promover a produção

**O escopo de atomicidade demonstrado é limitado:** o HMAC e o registro são criados em uma única transação, com locks nas linhas de lead/conversas selecionadas e mensagens lidas. Isso **não é** uma garantia de imutabilidade global do passado: fluxos de escrita não cooperantes, atualização de identidade/alias, concorrência fora do escopo e novas mensagens com outros vínculos exigem prova própria. Uma verificação atual não equivale a autorização permanente. Não publicar nem transmitir material ao modelo por estes estados.

**Chaves:** os testes utilizaram chaves sintéticas passadas em memória à S0. Há identificador de versão gravado, mas **nenhum cofre, rotação/autorização de chave ou distribuição em produção**. Um reprocessamento com outra versão é deliberadamente recusado. A política física de rotação e retenção permanece pendente.

**Histórico:** HMAC protege o texto sintético das mensagens contempladas, não áudios, imagens, anexos, transcrições nem validação semântica das declarações. Ainda faltam (a) fechamento integral ratificado de histórico multi-casos e identidade multi-telefone, (b) controle de versões independentes de ficha, caso, catálogo e atribuição, (c) concessão autenticada/minimizada de leitura por finalidade LGPD, (d) compare-and-swap e auditoria de aplicação F03 no cadastro e (e) ligação consistente com fechamento S0, F02 independente e S1. Nenhum destes itens foi declarado pronto.

**Próximo avanço da própria frente OpenAI:** desenhar porta S0 local de versões/catálogo e ledger de decisão pós-F03, preservando o escopo read-only dos módulos presentes, e ampliar testes adversariais. E05, deploy, merge e dados reais continuam não autorizados.
