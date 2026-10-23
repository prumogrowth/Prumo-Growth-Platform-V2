# S1-002 / I46 — inventário de ACL S0/S1 e teste negativo de dados D2 indiretos
**Corte:** 22/10/2026 | **Estado:** inventário técnico [T], policies de laboratório [P], integração S0 [R]. Sem deploy, merge ou migrations operacionais.

## Escopo e descoberta
O I45 identificou RLS de leads/ciclos que autorizava Gestores apenas por concessionária. O I46 amplia a observação para os demais objetos D2 criados em S0/003 e autorizados em S0/004. As policies históricas lotes_select_gestor, itens_select_gestor, reencontros_select_gestor e eventos_status_select_gestor usam grant de loja, sem vínculo obrigatório com a equipe atual. Mesmo quando casos_humanos não pode ser lido, uma listagem indireta de itens de importação, reencontros ou eventos comerciais pode revelar dados correlatos de outra equipe.

## Entregas S1 (somente laboratório)
1. scripts/test_s1_002_i46_acl_surface.py executa no final do I44/I45, com seis identidades GoTrue já validadas, tokens reais e PostgREST local; fixture SQL de importação **mista** (contato da equipe, de outra equipe, e lead sem caso) reproduz o vazamento antigo antes do candidato.
2. supabase/tests/s1_066_proto_d2_surface_local_only.sql: AND restritivo + política de leitura por lead/ciclo do I45 para itens_lote, reencontros_lote e eventos_status_comercial. Em lotes_importacao, faltando identidade de caso no cabeçalho misto, o candidato bloqueia leitura autenticada até haver projeção mínima S0. Bloqueio não é política operacional ratificada.
3. scripts/test_s1_002_i46_acl_inventory.py examina **todos os arquivos .sql existentes em supabase/migrations** e emite inventário JSON de relações, criação de RLS, policies, GRANTs a papéis de cliente, views e funções (incluindo declaração SECURITY DEFINER). A coleta é **lexical**, não substitui parsing SQL nem privilégios efetivos.
4. supabase/tests/s1_067_catalog_i46_local_only.sql inventaria o estado efetivo do catálogo PG17 **após o runner de regressão**, com tabelas public/prumo_private, policies, views, lacunas de gate S1 038, leitura autenticada e SECURITY DEFINER executáveis. Falha se encontrar tabela public legível por authenticated sem RLS; isso não basta para provar isolamento correto.

## Testes previstos
- I46-01: ambos os Gestores com concessão de loja veem originalmente todos os objetos importação/evento de equipes distintas (reprodução controlada).
- I46-02: policy candidata limita itens/reencontros ao contato autorizado e eventos ao ciclo/caso da equipe; cabeçalho de lote misto negado.
- I46-03: revogar concessão de loja não interrompe leitura permitida da própria equipe.
- I46-04: revogar chefia corta imediatamente as leituras com o mesmo JWT.
- I46-05: não há INSERT via REST autenticado de itens/eventos.
- I46-06: policies de teste presentes, outsider não obtém dados.
- I46-STATIC: auditoria de todos SQL de migrations, sem afirmar cobertura semântica/executável total.
- I46-CATALOG: inspeção efetiva PG17 de ACL/RLS após regressão completa.

## Matriz de riscos e fronteiras
| Área | Estado I46 | Responsável / próximo gate |
| --- | --- | --- |
| Casos, atribuições, conversas, mensagens com caso_id | I43–I45 [T], sem migração operacional | S0 consolidar predicates, writes e eventos |
| Leads/ciclos e eventos status | Candidatos I45/I46 com negação de acesso entre equipes | S0 validar modelo de ciclo, contato compartilhado e histórico |
| Itens/reimportações | I46 restringe ao lead/contexto atual | S0 autorizar projeções adequadas e revisitar concessões de loja |
| Cabeçalho de lote misto | Bloqueado [P], sem UI de substituição | S0 projetar metadados mínimos de importação/fila sem vazamento |
| Fila sem titular | Sem projeção operacional; bloqueio do candidato não significa conformidade [R] | S0/S1 separar fila por loja de casos atribuídos |
| Mensagens sem caso_id | Falha fechada I45, lacuna de contexto [R] | S0 construir vínculo confiável contato+loja |
| Histórico D3/D4, anexos, relatórios, templates, inbox/outbox e funções | Inventário estático/catálogo apenas; sem autorização fina ou teste E2E [R/V] | S0/F03/Meta; revisão manual de SECURITY DEFINER e grants |
| Transferência, revogação administrativa e concorrência | Somente SQL postgres confiado; teste após commit [T] | S1/S0 fechar API, locks e ator autenticado |

A varredura lexical detecta definições SQL presentes no repositório, mas não verifica metadados do banco hospedado, grants default, alterações externas, privilégios de execução indireta, owners, views SECURITY INVOKER nem decisões de finalidade D3/D4. O catálogo PG17 também se restringe ao esquema efetivamente carregado por sua suíte de testes, não equivale a produção.

**Autoridade:** S0 continua dona dos casos, eventos, ciclos, clientes, fila, atribuições e mensagens. S1 gerencia equipe, chefia, disponibilidade e entitlement contextual. A2 permanece [R]; sem nenhuma decisão nova de produto. **PR #5 sempre Draft**.

## Evidências
Resultados e URLs serão registrados após conferência dos jobs e dos logs, sem pressupor PASS.
