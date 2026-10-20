# S1-002/I24 — ciclo transacional de chaves HMAC com auditoria mínima (19/10/2026)

**Situação:** trabalho de pesquisa e teste estritamente local. `feat/s1-002-equipe-prumo`, PR #5 Draft; não migrar para Supabase hospedado, nem executar em produção. Não há contas, chaves, credenciais ou dados reais.

## Base verificada e objetivo

I23 passou em 30 testes unitários HTTP e 40 E2E GoTrue/HMAC sobre 50 migrations reais S0/S1. I22 já separou o custódio criptográfico (`prumo_s1_i22_custodio`) do executor do comando (`prumo_s1_i21_executor`), ambos `NOLOGIN`. No entanto, a fixture I22 ainda dependia de UPDATE/INSERT administrativos diretos na tabela de chaves para revogar e trocar chaves.

O I24 cria **somente no banco descartável** `supabase/tests/s1_024_ciclo_chaves_auditoria_local_only.sql`: versionamento CAS, revogação terminal no contrato administrativo, provisionamento prévio de uma chave sucessora, auditoria mínima e rejeição de ações fora de ordem. O lock transacional usa a mesma chave de `pg_advisory_xact_lock(hashtextextended('prumo-s1-key-v1:' || chave_id))` que a função `verificar_hmac` já usa, impedindo que revogação e validação do mesmo identificador avancem sem serialização.

## Contrato do laboratório

- `chaves` recebe `versao bigint` e `revogado_em timestamptz`, consistentes com o campo `ativo` por constraint. A nova chave nasce ativa com `versao=1`; a revogação grava `versao=2`, `revogado_em` e `ativo=false`. API administrativa **não permite reativação** de chave revogada. Isso não significa que um proprietário privilegiado do banco seja tecnicamente incapaz de modificar a tabela: a irreversibilidade é assegurada no contrato da operação e no fluxo de autorização, não por HSM/WORM.
- `provisionar_chave_i24(uuid,bytea,timestamptz,timestamptz,text)` exige exatamente 32 bytes sintéticos, janela de validade delimitada e motivo enum; retorna somente identificador, versão e status. **Não retorna segredo HMAC.**
- `revogar_chave_i24(uuid,bigint,text)` exige versão esperada, transição ativa → revogada, motivo enum e lock; versão obsoleta retorna SQLSTATE `40001`. As transições geram histórico dentro da **mesma transação**. Não há exclusão de chave nem reciclagem de mesmo identificador.
- `auditoria_chaves_i24` contém apenas `id, chave_id, evento, versao, motivo_codigo, ocorrido_em`; nenhum segredo, HMAC, JWT, identificador de cliente, texto livre ou payload. A trilha é auditável, porém **não é inviolável contra o DBA/custódio que controla a tabela**. Em produção exigiria armazenamento de auditoria independente, imutável e com política de retenção.
- Ambas as funções são `SECURITY DEFINER SET search_path=''` de propriedade do custódio `NOLOGIN` e aceitam exclusivamente conexões cujo `session_user` seja `postgres` no ambiente de CI. Não recebem `EXECUTE` do login SQL, executor, `anon`, `authenticated` ou `service_role`; também não há novas RPCs públicas. **`postgres` não é uma credencial aceitável para um serviço administrativo externo:** esse gate é só da fixture de CI.
- Para rotação segura, primeiro provisionar a sucessora no banco, verificar sua validade, alternar o assinador para essa chave, executar uma operação sintética de teste, revogar a anterior sob lock e auditar o resultado. Durante a sobreposição, ambas podem validar HMAC. Se a nova chave falhar, retornar ao assinador anterior **apenas enquanto ela estiver ativa**; após revogação, a restauração consiste em provisionar novo identificador, nunca reativar a antiga.
- O script de CI continua usando `http.server` SOMENTE em loopback; não existe automação de gestão de segredos em produção, nem canal real para comunicar a nova chave ao assinador. Nos testes, os segredos são bytes aleatórios temporários criados no runner.

## Evidência a verificar

`scripts/test_s1_002_i24_key_lifecycle_local.py` repete os **40 cenários I23** (GoTrue, gerência, HMAC, nonce, custódia segregada, política HTTP). Adiciona:
41. trilha sintética de bootstrap, revogação e provisionamento;
42. versão de revogação obsoleta (`40001`);
43. revogação repetida proibida (`22023`);
44. motivo livre negado sem histórico novo;
45. chave curta/janela inválida negadas sem persistência;
46. sobreposição e troca de assinador com duas chaves válidas;
47. revogação da antiga sem interrupção da sucessora;
48. conexão SQL da aplicação sem `EXECUTE` administrativo e sem SELECT de auditoria;
49. duas revogações concorrentes com apenas uma vencedora e um evento;
50. minimização de colunas e owner/ACL da auditoria.

Além disso, o job de 30 testes unitários I23 também é repetido, sem dependência da stack GoTrue.

## Riscos e critérios de NO-GO operacional

A custódia permanece numa role/tabela PostgreSQL temporária e tem poder de alteração sobre seu próprio histórico. Não foram criados Vault/KMS/HSM, credenciais com rotação externa, assinatura fora do banco, trilha WORM, política de backup/restauração, playbook de indisponibilidade, TLS/proxy confiável, gestão centralizada de rate limits, análise de abuso/observabilidade ou integração da interface gerencial e do S0 humano.

**Gate de produção:** homologar provedor de segredos e identidade operacional, separar chaves e login SQL em domínios de risco independentes, fazer rotação coordenada com confirmação/rollback e teste de chave comprometida, exigir auditoria inviolável fora do banco e revisão de `SECURITY DEFINER` e da infraestrutura de rede. Nunca compartilhar chaves do CI ou copiar as fixtures para migrations. I24 **não** altera o progresso global do projeto.

**CI:** inserir status e links somente após conferir os logs de ambos os jobs; até lá, aceite pendente.
