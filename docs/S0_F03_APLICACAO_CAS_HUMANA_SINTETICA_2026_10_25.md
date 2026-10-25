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

## Certificação PG17 concluída — 375 testes

**GitHub Actions SUCCESS:** https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40178595768

**Código certificado:** `13ab8f7f5870efa1f4a389bc2ffe9b1819c299a1`. PostgreSQL **17.11** descartável, sem recursos hospedados.

- **84/84** testes S0 CFI-01: `Ran 84 tests ... OK`.
- **291/291** testes F03: `Ran 291 tests ... OK`, dos quais **187** físicos PG17.
- **375/375** no total, 24 novos sobre o baseline anterior (14 físicos iniciais + 8 unitários + 2 físicos adversariais posteriores).
- Cenário **186** passou: atualiza campo existente somente com SHA do valor anterior correto; o recibo por campo registra SHA antigo e novo.
- Cenário **187** passou: uma falha SQL proposital *após as duas escritas* provoca rollback da ficha, da versão e do recibo de aplicação no mesmo commit.
- Primeira tentativa desses dois cenários [Actions #40178480555](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40178480555) falhou por problemas do **teste** (SQL delimitador `$` e consulta de auditoria sem filtro de concessionária). Corrigidos sem alterar a lógica CAS; última execução SUCCESS.
- Os testes desta etapa usam atores/sessões S0 de fixture; não homologam assinatura humana real. Nenhuma mudança de produção ou `main`.

**Próximas lacunas:** autorização humana real e contratada, cadastro/catálogo operacionais, rechecagens de todas as fontes externas e mídia, controles LGPD, integração de aplicação real campo a campo com CAS e gate separado; este laboratório não promove HOLD nem concede grants à F03.
