# S1-002 / I44 — integração de RLS com JWT GoTrue e PostgREST reais

**Data:** 22/10/2026. **Classificação:** prova técnica [T], ainda não contrato operacional homologado. **Referência:** I43, contrato S1-D05/D12/D13/D18/D19.

## Entrega
- `supabase/tests/s1_064_gotrue_rls_setup_local_only.sql` carrega entidades e policies originais S0 001–005, gate S1 038 e uma fixture mínima da exceção I55 em um **Supabase CLI local descartável** com `auth.users` **real**. Os três módulos **idênticos** de policies I41, I42 e I43 são importados diretamente; não cria migration de produto.
- `scripts/test_s1_002_i44_real_auth_rls.py` cria seis contas GoTrue locais por signup/password login, usa seus JWTs efetivamente assinados nas chamadas PostgREST, aplica casos/mensagens fictícios nas duas concessionárias e verifica leitura, envio e revogação após commit.
- `.github/workflows/s1-002-i44-gotrue-rls-local.yml` executa o ensaio em stack efêmera com CLI pinada, restrição de rede loopback, flags explícitas de CI e descarte ao encerrar. Nenhum token, chave ou senha é impresso nos logs.

## Cenários
1. Seis identidades reais GoTrue, vínculo de equipe S1 e dados sintéticos S0, com Consultor excepcional **sem grant geral de concessionária**.
2. Gestor sem grant de concessionária enxerga somente casos atuais e históricos de sua equipe; outro Gestor não vê carteira alheia. Outro Consultor e intruso não herdam esses acessos.
3. Consultor excepcional lê caso corrente e caso histórico do **mesmo contato na mesma loja**, sem ver coleções gerais S0, outro contato ou outra loja.
4. PostgREST rejeita envio histórico e aceita envio sintético da atribuição corrente; `anon` não vê carteira.
5. Revogação confiada a executor `postgres` retira imediatamente as leituras e escritas via **mesmo JWT real não expirado**. A atribuição S0 e a supervisão da equipe permanecem.
6. JWT GoTrue adulterado é rejeitado pelo serviço HTTP.

## Fronteira com S0
Esta prova usa PostgreSQL/S0 001–005 de base, mas **não testa integralmente todas as migrations S0 e S1**. A exceção I55 é representada por dados e predicado fiéis, porém **não** testa o fluxo de transferência operacional com evento externo nem a assinatura de ator em mutação. A revogação aqui é realizada pelo executor SQL do laboratório; a autorização administrativa do solicitante permanece gate independente. Não inclui D3/D4, F03, mensagens sem `caso_id`, relatórios, mudanças concorrentes de chefia ou lifecycle de sessão GoTrue (este último coberto separadamente nos ensaios I16/I17).

A revisão S0 deve aprovar e consolidar todos os predicados, verificar `SECURITY DEFINER` / `search_path` / owners e evitar eventuais exposições em outras tabelas e views antes de qualquer migração operacional. Não mexer em S0, banco hospedado, Meta real ou branches externas. PR #5 permanece Draft.

## Evidência
[GitHub Actions #39872874327 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39872874327), job `120151290596`, código testado no commit `e692cae309961625247d0f1fc8ce11cedc3601bc`. Logs verificados: `PASS I44-01`, `02`, `03`, `04`, `05`, `06` e `6/6`. O token GoTrue real permitiu leitura da própria equipe e histórico contextual, restringiu envio no caso antigo e perdeu imediatamente leitura/envio após revogação do entitlement, sem modificar a titularidade S0. JWT adulterado rejeitado. Uma execução anterior [#39872625205](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39872625205) passou I44-01..03 e falhou por **falso pressuposto do teste**: PostgREST devolveu HTTP `401` à requisição anônima em vez de lista vazia. O assert foi corrigido para reconhecer o bloqueio legítimo; não houve relaxamento de políticas.

A aprovação é estritamente da **stack local efêmera**, com migrations S0 001..005 e gate S1 038 mais fixtures I55 reduzidas, não da operação hospedada. PR #5 segue Draft.
