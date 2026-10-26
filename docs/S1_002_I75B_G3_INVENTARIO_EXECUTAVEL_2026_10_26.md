# S1-002 / I75B — Inventário G3 executável e lacunas de autorização

**26/10/2026.** Branch `feat/s1-002-equipe-prumo`. Escopo: somente código S1, analisador estático de fonte rastreada e CI PostgreSQL 17 descartável. **Nenhuma alteração à S0 oficial, migrations ou deploy.**

## Implementação real

- `scripts/test_s1_002_i75_g3_surface_inventory.py`: varre as migrations SQL, fixtures SQL e arquivos Python/JS/TS de runtime rastreados pelo checkout; extrai declarações de tabelas com separação de colunas que respeita parênteses; indexa policies e referências lexicais a tabelas e mídias; gera JSON em `RUNNER_TEMP/s1_002_i75b_g3_inventory.json`.
- `tests/test_s1_002_i75_g3_inventory.py`: seis testes para parser, negação a objeto obrigatório ausente, quebra das chaves de isolamento, deriva nas 8 policies candidatas I63, ausência de falsas declarações em comentários e proibição de converter menções a mídia em uma suposta autorização.
- `.github/workflows/s1-002-postgres.yml`: adiciona execução e arquivamento do JSON como `s1-002-i75b-g3-inventory` **dentro do workflow existente**. Não cria outro workflow, não altera a Issue #3.

## Objetos efetivamente identificados nos contratos do repositório

| Grupo | Tabelas canônicas | Fonte |
| --- | --- | --- |
| Identidade/contato e ciclo | `public.leads_loja`, `public.ciclos_comerciais` | `supabase/migrations/202610170001_s0_foundation.sql` |
| Casos e atribuições | `public.casos_humanos`, `public.atribuicoes_humanas` | `supabase/migrations/202610170003_s0_domain.sql` |
| Histórico de conversas | `public.conversas`, `public.mensagens` | `supabase/migrations/202610170003_s0_domain.sql` |
| Administrativo endereçável por linha | `public.itens_lote`, `public.reencontros_lote`, `public.eventos_status_comercial` | `supabase/migrations/202610170003_s0_domain.sql` |
| Cabeçalhos compartilhados | `public.lotes_importacao`, `public.canais_loja` | `supabase/migrations/202610170003_s0_domain.sql` |

O analisador exige `concessionaria_id` e chaves adequadas de lead, caso, conversa e canal conforme a tabela. São **11 objetos com verificação de contrato estrutural**, não 11 permissões operacionalmente aprovadas. A coluna `leads_loja.telefone_cliente_normalizado` e `mensagens.conteudo_sintetico` são exemplos de dados cuja finalidade e projeção precisam ser revisadas. A existência de `mensagens.conteudo_sintetico` demonstra modelagem de conversa **sintética**, não uma biblioteca real de mídias do WhatsApp.

A fixture `supabase/tests/s1_087_rls_excecao_canonica_local_only.sql` contém as **8 policies I63** de histórico para casos, atribuições, conversas e mensagens, preservadas como candidatas de teste. I67–I74 já possuem regressões positivas e negativas independentes; a I75B não reinventa essas políticas.

## Certificação de execução I75B

- **Código verificado:** `40336b7b3ff7de2d7d864333ffad4135c480f2c1`.
- [Workflow oficial S1 PG17 #40312496327](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40312496327), job `121536871573`: **SUCCESS**. Logs confirmados:
  - `6 tests ... OK` (seis testes unitários da I75B);
  - `PASS I75B-01`, `PASS I75B-02`, `PASS I75B-03` (**3/3 verificações**);
  - inventário de **57 migrations**, **45 outras tabelas declaradas** e **25 arquivos runtime**;
  - regressão SQL I74 **6/6**, regressões I63–I73, e rollback final de fixtures conforme marcador `all synthetic objects and policies rolled back`.
- Artefato de auditoria **`s1-002-i75b-g3-inventory`** publicado no mesmo run (ID `12644938398`), contendo o inventário JSON; é resultado de scan e não evidência de leitura/download de dados reais.

## Limites da prova e prioridades que realmente faltam

**Acesso a mídia/anexo e D3/D4 NÃO CERTIFICADO.** Candidatos lexicais de mídia e 45 outras tabelas declaradas são pontos de inspeção, não rotas de download/autorização. Não foi demonstrado catálogo físico S0 de mídia e retenção, endpoint de download, proteção de URL, ACL de objeto nem revogação de arquivos já entregues. Também não está provada a completude de consumidores fora do checkout, SQL dinâmico ou integrações Meta/Banco.

**Próxima tarefa I75C (sem reabrir I61–I74):** conciliar as entradas do JSON com proprietários de dados da S0, classificar superfícies D2/D3/D4 por objeto/coluna, mapear consumidores externos relevantes e selecionar **testes negativos efetivos** de download, atribuição revogada e isolamento loja/contato. Se não houver mecanismo implantado de mídia/anexo, documentar o bloqueio e o contrato necessário, **sem inventar uma tabela ou endpoint** para exibir aprovação.

O aceite G3 continua parcial; G1–G6 e homologação permanecem pendentes. A2 não está em discussão, pois foi fechada na I51. O checkpoint I74 permanece válido e a I75B acrescenta evidências estáticas, sem promover migrações ou mexer na produção.
