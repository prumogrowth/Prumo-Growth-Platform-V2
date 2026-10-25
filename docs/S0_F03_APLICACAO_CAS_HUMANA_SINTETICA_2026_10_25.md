# E04 S0/F03 — aplicação CAS sintética por gestor S0 (25/10/2026)

Repositório único `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`; branch `feat/oai-s0-f03-history-port-20261023`; PR #1 Draft contra S0. Não acessar E05/Meta/API OpenAI/Supabase hospedado.

## Alteração entregue
- Porta `backend/s0_f03_field_application_local.py`: somente a S0 valida uma **decisão explícita de gestor** autenticado por `IdentityProvider`, sessão S0, equipe S1 ativa e papel `gestor` vigente naquela concessionária. O F03 e os três atos HOLD não constituem aprovação de alteração.
- Usando a fixture local PG17, exige reserva consultiva F03 previamente criada e igual ao SHA da proposta, cinco versões CAS, caso/atribuição, ausência de pendência S0 de identidade e HMAC de conteúdo recomputado **no interior da mesma transação**; bloqueia loja, catálogo, vetores, lead e conversas antes de aplicar.
- Para cada campo, verifica contrato ativo, tipo, comprimento, item de catálogo existente/ativo e versão **anterior do valor** (`expected_old_sha256`, ou ausência). Verifica todo o lote antes de editar. Escreve apenas em `cfi01_f03_form_fields_local` (tabela fictícia). Gatilhos existentes incrementam a versão da ficha por campo; é verificada a versão resultante.
- Um recibo de aplicação por fechamento humano e até 12 itens de auditoria, com hashes (sem texto de cliente) e gestor/sessão. Audit/itens são append-only, ACL negada para papéis públicos. Repetições idênticas retornam somente estado de auditoria, tentativas diferentes são conflito.
- PostgreSQL commit/rollback de **todo o lote**: alteração parcial não é resultado permitido. Nenhuma alteração em `public.leads_loja`, identidade, catálogo comercial verdadeiro, status, comunicação ou produção.

## Limites (não homologar operação real)
A autorização humana é apenas simulada usando `LocalIdentity` nos testes; **não é comprovante de assinatura real**. A reserva F03 ainda é consultiva; a aplicação não é endpoint público nem integração de ficha operacional verdadeira. O checksum + locks valem para escritores S0 simulados cobertos pela fixture, não garantem mídia/áudio, fontes externas ou intervenções pós-commit. Isto não libera o modelo F03 a acessar/aplicar campos: o chamador é exclusivamente um ator gestor S0 autorizado.

## Próximo gate
Integrar mecanismos reais de aprovação humana e fontes comerciais autenticadas, construir provas de mídia e LGPD, ratificar cobertura de escritores e testar fluxos completos sem transgredir E04. Registrar resultados do GitHub Actions somente após logs.
