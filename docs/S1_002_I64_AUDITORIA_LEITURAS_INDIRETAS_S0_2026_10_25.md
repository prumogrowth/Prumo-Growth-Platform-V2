# I64 — auditoria de leituras indiretas da S0 (D2) e quarentena candidata

25/10/2026, **laboratório PG17/GoTrue exclusivamente**. Nenhum artefato de migração para o Supabase hospedado foi criado.

## Achado reproduzível

A S0 emite SELECT autorizado por grant de `gestor` à concessionária em `leads_loja`, `ciclos_comerciais`, `canais_loja`, `lotes_importacao`, `itens_lote`, `reencontros_lote` e `eventos_status_comercial`. O I63 restringe apenas casos, atribuições, conversas e mensagens. Portanto um Gestor de outra equipe, mas com grant geral à loja, continua enxergando dados indiretos até aplicar uma regra adicional. Isso é demonstrado antes do patch experimental, não é apenas hipótese.

## Candidato I64

`supabase/tests/s1_089_s0_indirect_read_boundary_local_only.sql` adiciona **7 policies SELECT RESTRICTIVE** sem novas permissivas, tabelas, grants ou RPCs.

- `leads_loja`: somente contato que tenha algum caso efetivamente legível pelo ator segundo o I63, e cuja política permissiva S0 já permita SELECT. Um Consultor com exceção sem grant de loja **não** recebe leitura bruta.
- `ciclos_comerciais`: mesmo par exato (concessionária, contato), condicionado a caso real autorizado e à permissão S0 preexistente. Outros ciclos desse mesmo contato permanecem legíveis ao Gestor autorizado, como histórico contextual.
- `canais_loja`, `lotes_importacao`, `itens_lote`, `reencontros_lote` e `eventos_status_comercial`: quarentena **`USING(false)`** para `authenticated`. As tabelas são administrativas ou por lote; ainda não existe contrato que transforme a permissão por caso em leitura segura desse universo. A quarentena também restringe Gestores legítimos — escolha conservadora apenas no candidato, que **não deve ser promovido** sem análise de produto/operacional.
- As políticas I63 de casos/conversas/mensagens seguem separadas e intactas, e não surge uma view que contorne RLS. A regra de envio de mensagens simuladas também não é ampliada.

A fronteira de dados do S0 aqui auditada é D2 sintético. Não existe inferência de permissões para D3/D4, que não são dados de cliente armazenados nesse recorte. A verificação de RPCs/SECURITY DEFINER históricos e outras tabelas auxiliares fora das sete superfícies demandará inventário posterior, e o certificado I64 não equivalerá a revisão total de todos os caminhos da aplicação.

## Evidências

`supabase/tests/s1_090_s0_indirect_read_boundary_aceite.sql` mostra a leitura indevida pré-candidato do Gestor de outra equipe e verifica após a quarentena a visibilidade para Gestor correto, a não elevação de privilégios do Consultor excepcional, a perda de acesso à revogação e o isolamento das cinco tabelas em lote, em transação `BEGIN/ROLLBACK`.

A prova PostgREST usa GoTrue real e o gateway I62 assinado, na mesma stack local do I63. Evidências finais devem citar os workflows e logs após aprovação.

## Verificação GoTrue adicionada

O arquivo `scripts/test_s1_002_i64_indirect_read_e2e.py` é executado depois de I63 e antes da revogação da chave assinadora, com banco local e tokens reais. Ele cria um vínculo de Gestor na loja que **não** o torna supervisor do caso, documenta a leitura real pré-patch de sete superfícies, aplica a quarentena candidata e verifica que o mesmo token deixa de acessar tais dados. Também exige que o Gestor efetivamente responsável retenha apenas contatos/ciclos autorizados, que o Consultor com exceção revogada não recupere o histórico e que a revogação/restauração do grant de loja produza resultado imediato no mesmo JWT. Certificação depende dos logs de CI.

## Certificação — 25/10/2026

**PG17 transacional: SUCCESS.** [Workflow #40186805770](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40186805770), job `121149227492`; commit candidato `0cd0b0f943bbb0595f8be62bd7b29970aa4527d9`. Conferidos logs `PASS I64-01` a `PASS I64-08`, total **8/8**, mais `I64 S0 indirect exposure PG17 8/8; all synthetic objects and policies rolled back` e `PASS S0+S1 I52-I64 canonical and candidate stages after legacy regression`.

**GoTrue/PostgREST com JWT real: SUCCESS.** [Workflow #40186925810](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40186925810), jobs `121149594126` (E2E) e `121149593985` (unitários), commit de integração `421105e8031a6f115364d95a7c828ae82c22d830`. Conferidos `PASS I64-E2E-01` a `PASS I64-E2E-06`, total **6/6**, com regressões `I63-E2E-01..06` e anteriores preservadas na mesma execução.

**Achado comprovado:** em autenticação real, o gestor com grant de loja mas sem relação com o caso podia ler `leads_loja`, `ciclos_comerciais` e as cinco superfícies administrativas mesmo com os casos ocultos pelo I63. A quarentena I64 fechou todas essas leituras, mas conservou acesso exato para gestor supervisor com concessão S0 válida nos dois objetos de histórico de contato. Revogação de grant sob o mesmo JWT produz corte imediato e restauração controlada.

**Limitação expressa:** 7 policies são candidatas *somente nos testes* e não uma recomendação de implantação incondicional. O bloqueio total de 5 tabelas administrativas é um *trade-off de segurança* que precisa de contrato de produto específico antes de adoção. Não foi auditada toda superfície futura de RPC, views, funções SECURITY DEFINER, exportação agregada ou demais objetos auxiliares. Dados D3/D4 operacionais não foram expostos, criados nem considerados cobertos por esta prova. Nenhuma alteração ao hosted Supabase ou `main`.
