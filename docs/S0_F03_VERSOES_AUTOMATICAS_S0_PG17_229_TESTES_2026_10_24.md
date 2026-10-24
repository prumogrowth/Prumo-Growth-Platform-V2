# E04/S0-F03 — Versões acionadas por alterações S0 e 229 testes em PG17

**Data:** 24/10/2026. **Único repositório oficial:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`.
**Branch exclusiva:** `feat/oai-s0-f03-history-port-20261023`; revisão no [PR #1](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/1), Draft contra `feat/s0-cfi01-f03-auth-preflight-20261020`, **não contra main**.
Esta entrega é fixture/integração de **E04 local e sintética**; não é migração hospedada nem abertura da F03 para dados reais.

## Prova física executada

[**GitHub Actions #40061833588**](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40061833588), commit `5d7db52f8e51e1d3106144e02775fccf01d2c7ea`, job `f03-pg17-disposable`, **conclusão SUCCESS** em PostgreSQL **17.11**:
- **84/84** testes físicos S0 CFI-01 da base: `Ran 84 tests … OK`.
- **145/145** testes F03: `Ran 145 tests … OK` — 24 do leitor multi-casos, 31 do manifesto/selo, 15 da autorização HMAC, 18 de reserva CAS (unitários), **57 testes físicos PG17**.
- **229/229 PASS**. Os testes físicos 42–57 são **16 novos cenários** de atualização automática de versões; não se confundem com falhas anteriores de inicialização de runner no repositório antigo.

## Adaptação S0 implementada

[SQL local apenas](../supabase/tests/s0_f03_version_source_triggers_local_only.sql), carregado pelo [executor PG17](../scripts/run-s0-f03-pg17-local.sh) **depois** das fixtures de manifestação/HMAC/vetores independentes.

**Gatilhos em tabelas S0 já existentes:**
- Alteração efetiva do `public.leads_loja.telefone_cliente_normalizado` incrementa `versao_identidade` do lead naquela loja.
- Alteração efetiva de `public.casos_humanos` incrementa `versao_caso` da combinação loja/caso.
- Inserção, encerramento, alteração ou exclusão efetiva de `public.atribuicoes_humanas` incrementa `versao_atribuicao` no caso associado. Atualizações que não mudam valores não incrementam essas versões.
- Se ainda não existe fonte de versão F03 para um lead/caso, os fluxos preexistentes da S0 **continuam funcionando**; nesse caso, a reserva CAS F03 segue negada pela falta das versões exigidas, em vez de inventá-las.

**Fontes exclusivamente sintéticas acrescentadas nesta fixture:**
- `prumo_private.cfi01_f03_form_fields_local`: valores fictícios de campos da ficha geram atualização de `versao_ficha`.
- `prumo_private.cfi01_f03_catalog_entries_local`: itens inventados geram atualização de `versao_catalogo`.
- Operações dessas fontes sem vetor inicializado são **recusadas**; reatribuição dos IDs de campo ou produto é recusada. RLS e revogações impedem leitura direta por `authenticated`, `anon` e `service_role`.

## Evidência nova: 16 cenários físicos

Na [suíte de integração PG17](../backend/tests/test_s0_f03_pg17_integration.py), os testes 42–57 verificaram alteração real do telefone e do caso, fechamento e no-op de atribuição, alteração e no-op de ficha sintética, alteração/remoção de catálogo sintético, bloqueio de transferência de chave/escopo, recusa de fonte não inicializada, continuidade de S0 sem vetor F03, e isolamento entre concessionárias. Em especial, uma edição S0 significativa **invalida a versão capturada** e a reserva F03 retorna `STALE_REVIEW_REQUIRED`.

## Limites e próxima etapa de segurança

1. **Não há ainda ficha operacional nem catálogo comercial de produção integrados ao CAS**. As respectivas fontes são fixtures com dados fictícios; a prova física NÃO homologa a atualização final de dados bancários/cadastro.
2. A identidade sintética multitelefone/aliases `prumo_private.aliases_identidade_s0` não faz parte deste executor mínimo CFI-01. O gatilho de telefone do lead **não cobre, por si só, inclusão ou revisão de aliases**, que exigirão integração isolada futura. Alteração de fonte fora destes gatilhos também requer proteção.
3. Os cinco vetores independentes são úteis apenas quando **todos os escritores relevantes** atualizam a sua versão. A reserva é consultiva (`*_REVIEW_ONLY`), não um CAS de escrita em ficha com auditabilidade campo a campo ou revalidação global de mídias.
4. Ainda faltam identidade/aliases reconciliados, prova de integridade de mídia/áudio, chave HMAC/rotação real, contrato LGPD de leitura mínima, autorização F03 e atualização real de ficha num único commit transacional ratificado pela S0.
5. Não houve alteração de `main`, merge, deploy, uso de Meta real, API OpenAI paga, dados pessoais ou Supabase hospedado. Nenhum segredo de produção foi solicitado.

**Responsabilidade:** a frente OpenAI continua implementando as adaptações estritamente necessárias na S0 compartilhada, sem aguardar equipe S0 separada, mantendo a branch base da S0 e as outras frentes intactas.
