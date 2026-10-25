# I69 — exportação paginada de resumos administrativos com RLS do invocador

**25/10/2026 — laboratório somente**. A orientação da Issue #3 (auditoria de otimização de 13 workflows) foi lida; **não autoriza alterações**. Esta frente mantém sua branch `feat/s1-002-equipe-prumo`, sem tocar em workflows de outros módulos, integração ou `main`.

## Contrato candidato

O I68 demonstrou a segurança de duas views `security_invoker=true` para contagens por lote/canal. Essas views ainda permitiam `GET ...?select=*` e paginação arbitrária, potencialmente criando um canal de coleta ilimitada de *resumos* da própria equipe. O I69 **revoga SELECT de cliente diretamente nas duas views I68** e disponibiliza duas RPCs PostgreSQL **SECURITY INVOKER**, com SQL estático, `SET search_path=''` e `EXECUTE` exclusivo a `authenticated`:

- `public.s1_69_exportar_lotes(p_loja uuid,p_apos uuid,p_limite integer)`: devolve `concessionaria_id,lote_ref,itens_autorizados` (contagem apenas de linhas aceitas, autorizadas por RLS I67 e ACL I68).
- `public.s1_69_exportar_canais(p_loja uuid,p_apos uuid,p_limite integer)`: devolve `concessionaria_id,canal_ref,conversas_autorizadas` (apenas conversas RLS I63 e grant ativo de Gestor na concessionária).

O cliente deve informar a loja; `p_apos` é o UUID da última referência retornada, ou `null` para primeira página. `p_limite` precisa ser inteiro de 1 a 20. Ordenação crescente estável por referência; páginas sem `OFFSET`. Não aceita coluna, tabela, filtro ou ordenação arbitrários e não usa SQL dinâmico. Nenhum `SECURITY DEFINER`, grant de lote/canal bruto ou endpoint para `anon` foi criado.

A verificação PostgreSQL usa dois gestores, dois lotes/canais da mesma loja e um contato de outra equipe, testa paginação 1+1 sem duplicidade, limites inválidos, leitura direta de views negada, outra loja, revogação de grant e regressões I63–I68. A prova GoTrue/PostgREST faz as mesmas chamadas com JWT real após I68. **Apenas testes; não promover ao banco hospedado.**

## Limitações que impedem promoção

**Limite de até 20 linhas por requisição não limita quantidade total de páginas ou taxa**, nem substitui rate-limit/quotas no gateway e trilha auditável de exportação. Um cliente ainda pode ler tabelas brutas legitimamente permitidas pelo I63/I67 e recompor contagens de suas **próprias** linhas; esse desenho não afirma eliminar exportações alternativas. A consistência entre páginas sob alterações concorrentes não é um snapshot. UUIDs de referências continuam expostos (sem descrição de lote/canal). Integração de autenticação de sessão para exportações sensíveis, retenção, limites globais, logs sem PII e mascaramento precisam de gate próprio antes de produção.

## Prova HTTP adicional

`scripts/test_s1_002_i69_bounded_export_e2e.py` reaproveita a stack e os dois Gestores reais do I68, adiciona segundo lote/canal do Gestor A e exige páginas ordenadas 1+1+vazio, sem repetição; Gestor B só vê lote/canal de sua equipe mesmo pedindo 20 linhas, e a loja B permanece vazia. Comprova que `GET` das duas views I68 falha, `anon` não executa RPC, parâmetros inválidos são negados, Consultor excepcional não vê exportações e o mesmo JWT do Gestor perde imediatamente o acesso após revogação. Nenhum workflow de outra frente foi alterado. Registros de aprovação só serão acrescentados após observar CI.

## Certificação de laboratório — 25/10/2026

**PostgreSQL 17: SUCCESS.** [Workflow #40199097174](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40199097174), job `121186225587`, código inicial `2d3de8c02e0af1ac444f63d807f69201b07a4075`. Logs confirmados `PASS I69-01` a `PASS I69-09` (**9/9**): cursor determinístico e limite por consulta, páginas vazias sem repetição, nenhuma soma de outra equipe nem outra concessionária, parâmetros inválidos rejeitados, views I68 inacessíveis diretamente, usuário sem gestão negado, revogação imediata e ausência de exposição `SECURITY DEFINER`. Regressão S0+S1 I52–I69 passou, rollback de todos os dados/policies sintéticos confirmado.

**GoTrue real + PostgREST: SUCCESS.** [Workflow #40199271891](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40199271891), jobs `121186764077` (E2E real) e `121186764310` (unitários), ambos SUCCESS, código da integração `f94dc4e0e918b4b691031390d117cdfa5c8eb592`. Logs `PASS I69-E2E-01` a `PASS I69-E2E-09` (**9/9**): pré-candidato diretório de views livre; pós-candidato somente duas RPCs paginadas, página 1 + 2 + vazia no mesmo lote/canal, esquema de retorno fixo, nenhuma leitura entre equipes/lojas, `anon` negado, limites inválidos negados pelo HTTP, Consultor excepcional sem leitura, mesmo JWT revogado sem permissão, retorno limitado após restauração e scanner I65 sem exposições.

**Execução eficiente:** o I69 reutilizou a mesma stack GoTrue dos testes assinados I62–I68 em vez de criar um 14º workflow. Alterou apenas o workflow local da **própria frente S1-002** para registrar os arquivos novos como gatilhos, sem modificar workflows de outras frentes e sem executar a otimização ainda não autorizada da Issue #3.

**Gate de promoção: bloqueado.** O limite de 20 itens é **por requisição**, não quota total; a paginação permite coletar repetidamente dados que o ator já pode ver. Outras leituras autorizadas de S0/ I63/ I67 permanecem fora desse controle. Ainda precisam ser definidos limites cumulativos e temporais, rate-limiting externo, trilha auditável, proteção contra scraping por repetição de cursor, mascaramento/necessidade dos UUIDs, consistência entre páginas e validação de consumidores que dependem de acesso direto às views I68. Não houve deploy, merge `main`, alteração hospedada ou integração sem autorização.
