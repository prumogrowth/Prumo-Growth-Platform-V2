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
