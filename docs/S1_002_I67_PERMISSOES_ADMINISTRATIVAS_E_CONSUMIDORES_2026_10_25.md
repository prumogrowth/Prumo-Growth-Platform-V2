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

O script `scripts/test_s1_002_i67_legacy_consumer_inventory.py` pesquisa arquivos SQL, Python, JS/TS e Shell do checkout buscando os três nomes de fachadas I51 e `prumo_s1_interface`. Registros históricos e testes são apresentados separadamente; **referências em runtime não revisadas falham CI**. A checagem não descobre SQL dinâmico, sistemas externos ou consumidores fora do repositório.

A fronteira SQL I66 foi preservada: os wrappers legados ainda existem, mas não possuem `USAGE/EXECUTE` cliente; chamadas operacionais atuais utilizam autenticação GoTrue e fluxo HMAC do I62.

## Aceite

`supabase/tests/s1_095_admin_row_scoped_aceite.sql` reproduz um lote sintético contendo um contato de cada equipe e linha rejeitada sem caso. Compara as leituras antes/depois do candidato, prova que cada Gestor com vínculo e concessão só vê as próprias linhas de itens/reencontros/eventos e que nenhum deles lê lote/canal completos. Valida Consultor excepcional negado, concessão expirada, ACL privada e regressões I63–I66. O teste ocorre dentro do `BEGIN/ROLLBACK` já estabelecido no I64.

O cenário GoTrue real testará a mesma autorização via PostgREST e JWT reais. Evidências de CI serão registradas após serem observadas.

## Teste de sessão real

`scripts/test_s1_002_i67_admin_row_scope_e2e.py` cria um segundo Consultor legítimo, atribuído a outro Gestor, e registra itens aceitos de duas equipes no mesmo lote, além de uma linha rejeitada sem caso. Prova a quarentena I64 original, aplica I67 apenas no stack efêmero e verifica via JWT real a separação nas três tabelas. Revoga e restaura concessão do segundo Gestor usando o mesmo token; valida que lote/canal permanecem fechados, bem como ACL I66 e scanner I65. O runner PG17 também executa o inventário estático de consumidores. Evidências somente após resultados.

### Achado do inventário e limite

A primeira CI I67 identificou **um consumidor legado real no código-fonte**, `backend/s1_gateway_local.py` (adaptador demonstrativo I19 local). Não é um módulo de produção autorizado: usa o login SQL local `prumo_s1_gateway_ci` e é limitado a `127.0.0.1`. Após aplicar a quarentena I66, sua rota SQL é negada no banco. **Isso não prova ausência de consumidores externos**, portanto o adaptador não é considerado limpo ou preparado para produção. A auditoria estática foi fortalecida para registrar expressamente esse único módulo sob estado `I67-RETIRED_LOCAL_ADAPTER`, checar os limites de loopback e de login restrito, e falhar caso apareçam outros consumidores de funções I51 ou do adaptador fora de teste. Qualquer ativação real do I19 requer substituição completa pelo gateway assinado, nunca reversão de ACL I66.

O ensaio SQL de I67 passou 8/8 na execução anterior; a mesma execução foi reprovada **corretamente** pelo detector estático desse consumidor, o que motivou este tratamento explícito.

### Desacoplamento adicional do gateway assinado (I67)

O inventário ampliado comprovou quatro imports do adaptador I19 para uso de parser e lista de comandos, **não do executor SQL antigo**. Em vez de abrir exceções para esses imports, o I67 extraiu um módulo de validação sintática `backend/s1_command_validation_local.py`, sem SQL ou credenciais, e atualizou `s1_gateway_http_policy_local.py`, `s1_gateway_signed_local.py`, `s1_signer_independent_gotrue_local.py` e `s1_signer_process_local.py` para consumi-lo. A implementação I19 continua inteiramente independente como adaptador de testes históricos. O teste unitário `tests/test_s1_002_i67_command_parser.py` compara os contratos do novo parser e do antigo, inclusive erros e enumeração de motivos. A arquitetura do HMAC e do gateway assinado **não** recebeu acesso à interface I51; o objetivo é eliminar a dependência por importação. O scanner I67 bloqueia a volta de tal dependência fora do conjunto de testes.

## Certificação final — 25/10/2026

**PostgreSQL 17 descartável: SUCCESS.** [Workflow #40193261944](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40193261944), job `121168609527`. Logs conferidos `PASS I67-01` a `PASS I67-08`: **8/8**; `PASS I67-SCAN-01`: inventário estático aprovado, **zero consumidores de runtime não revisados**, um adaptador I19 local explicitamente aposentado, **31 referências históricas/de teste**. As 8 provas anteriores I64/I65/I66 foram preservadas no mesmo runner, e `PASS S0+S1 I52-I67 ...` foi confirmado. Políticas e dados sintéticos foram descartados por `ROLLBACK`.

**GoTrue real + PostgREST: SUCCESS.** [Workflow #40193208274](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40193208274), jobs `121168445306` (E2E) e `121168445467` (unitários), ambos SUCCESS. Logs `PASS I67-E2E-01` a `PASS I67-E2E-07`: **7/7** em JWT real, incluindo lote compartilhado de duas equipes e linha rejeitada, escopo exato dos itens/reencontros/eventos, manutenção de lote/canal fechados, Consultor sem concessão administrativa e revogação/restauração imediata do grant no mesmo token. I66 HMAC e I63/I64 continuam funcionando. O teste de paridade entre parsers antigo e novo passou.

**Regressões de componentes assinados:** os outros 12 workflows I20–I31 disparados pela extração do parser também terminaram em SUCCESS na revisão de código `c50af9de93f4b5382974e82787ca1c4672fd1128`, sem regressões observadas.

### Intercorrências e resolução

1. A primeira CI PostgreSQL falhou pela grafia inválida `pg_catalog.current_user`, ajustada para `current_user` sem alterar a autorização.
2. A segunda execução aprovou **8/8** no SQL, mas o inventário detectou o código de `backend/s1_gateway_local.py`, um adaptador I19 antigo; não foi mascarado. O scanner foi reforçado para documentar e exigir seu contrato de uso exclusivo em loopback.
3. A auditoria mais ampla detectou também **quatro imports de validação de entrada** desse módulo antigo a partir dos componentes de gateway assinado. O parser foi extraído a `backend/s1_command_validation_local.py`, e os quatro componentes passaram a consumi-lo. O módulo SQL aposentado continua para regressões legadas, mas o gateway assinado não o importa mais. A CI só foi considerada aprovada **após** essa refatoração e os testes de paridade.

### Limites e próxima frente

O I67 é **um contrato candidato**, não uma migration para o banco hospedado. `canais_loja` e `lotes_importacao` continuam em quarentena; nenhuma regra de RLS para cabeçalhos coletivos foi liberada. O inventário estático não demonstra ausência de consumidores externos ao repositório, código gerado, SQL dinâmico, produção, relatórios exportados ou clientes desconhecidos. Para a próxima etapa I68, revisar projeções/colunas acessíveis e metadados de filas ou cabeçalhos sem liberar dados comerciais alheios à equipe; definir um caminho de exportação administrativa minimamente privilegiado e testar com autenticação real.

Sem deploy, sem alteração no Supabase hospedado, sem `main` e sem desativar a trilha assinada I62.
