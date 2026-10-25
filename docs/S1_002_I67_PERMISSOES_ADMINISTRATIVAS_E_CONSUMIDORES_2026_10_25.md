# I67 — consumidores da interface legada e autorização administrativa por caso

Data: 25/10/2026. Somente branch experimental, PG17 e Supabase CLI efêmeros. Nenhuma alteração no Supabase hospedado.

## Decisão operacional

A quarentena I64 permanece como baseline. O I67 **substitui apenas três políticas de leitura globalmente bloqueadas**, por predicados `AS RESTRICTIVE` filtrados pela mesma prova de contato e equipe I63:

- `itens_lote`: permite ao Gestor da loja apenas linha **aceita**, com `lead_id` não nulo, de cliente cujo caso seja acessível por participação real de sua equipe. Linhas rejeitadas (sem caso/cliente) permanecem bloqueadas.
- `reencontros_lote`: permite somente linhas ligadas a `lead_id` autorizado na concessionária correspondente.
- `eventos_status_comercial`: permite apenas evento cujo ciclo pertença ao contato com caso autorizado, na mesma concessionária.

**Não amplia permissões `GRANT` ou políticas `PERMISSIVE` preexistentes.** O Gestor ainda precisa possuir concessão S0 ativa à loja. Um Consultor com acesso excepcional I61/I62, mas sem concessão de Gestor, não recebe leitura bruta administrativa. Revogar concessão da loja retira imediatamente a leitura.

`lotes_importacao` e `canais_loja` **permanecem bloqueados**: os recursos de cabeçalho abrangem múltiplas equipes. Mesmo que uma linha de um lote seja autorizada, nenhuma linha de outra equipe, linha rejeitada ou cabeçalho compartilhado é exposto.

É um **contrato candidato parcial para três das cinco tabelas**; não justifica desbloquear indiscriminadamente os demais objetos D2/D3/D4 nem tratar todas as colunas do cliente como aprovadas para publicação. A autorização de colunas/projeção de UI, mascaramento, relatórios e canais deve ser especificada antes do deploy.

## Auditoria de consumidores legados

O script `scripts/test_s1_002_i67_legacy_consumer_inventory.py` pesquisa arquivos SQL, Python, JS/TS e Shell do checkout buscando os três nomes de fachadas I51 e `prumo_s1_interface`. Registros históricos e testes são apresentados separadamente; **referências em runtime fora da lista aprovada falham CI**. A checagem não descobre SQL dinâmico, sistemas externos ou consumidores fora do repositório.

A fronteira SQL I66 foi preservada: os wrappers legados ainda existem, mas não possuem `USAGE/EXECUTE` cliente; chamadas operacionais atuais utilizam autenticação GoTrue e fluxo HMAC do I62.

## Aceite

`supabase/tests/s1_095_admin_row_scoped_aceite.sql` reproduz um lote sintético contendo um contato de cada equipe e linha rejeitada sem caso. Compara as leituras antes/depois do candidato, prova que cada Gestor com vínculo e concessão só vê as próprias linhas de itens/reencontros/eventos e que nenhum deles lê lote/canal completos. Valida Consultor excepcional negado, concessão expirada, ACL privada e regressões I63–I66. O teste ocorre dentro do `BEGIN/ROLLBACK` já estabelecido no I64.

O cenário GoTrue real testará a mesma autorização via PostgREST e JWT reais. Evidências de CI serão registradas após serem observadas.

## Teste de sessão real

`scripts/test_s1_002_i67_admin_row_scope_e2e.py` cria um segundo Consultor legítimo, atribuído a outro Gestor, e registra itens aceitos de duas equipes no mesmo lote, além de uma linha rejeitada sem caso. Prova a quarentena I64 original, aplica I67 apenas no stack efêmero e verifica via JWT real a separação nas três tabelas. Revoga e restaura concessão do segundo Gestor usando o mesmo token; valida que lote/canal permanecem fechados, bem como ACL I66 e scanner I65. O runner PG17 também executa o inventário estático de consumidores. Evidências somente após resultados.
