# S1-002/I31 — testemunha de revisão monotônica independente da autoridade (20/10/2026)

**Estado:** implementação de pesquisa apenas em CI; PR #5 Draft, `feat/s1-002-equipe-prumo`, sem merge, deploy, banco hospedado ou chaves reais. Provas E2E e aceite precisam ser vinculados ao SHA final testado.

## Motivação

I30 aprovou 108/108 testes unitários e 120/120 E2E com a integridade criptográfica HMAC do ledger de certificados, mantendo o `watermark` em memória da autoridade durante reinícios do assinador. A restauração simultânea de SQLite e checkpoint assinados de versão antiga **após reiniciar também a autoridade** não podia ser identificada: a autoridade esquecia seu marco de revisão.

## Contrato I31 (laboratório local)

`backend/s1_i31_monotonic_witness_local.py` contém uma **testemunha em processo Python distinto**, com outro segredo HMAC-SHA256 de 32 bytes sintéticos e outro arquivo persistente `0600`, separados do SQLite I29 e do checkpoint HMAC I30. Seu registro possui apenas revisão, digest HMAC do estado I30 e MAC próprio da testemunha; não contém certificado em claro, token, chave privada TLS ou conteúdo comercial. O bootstrap cria arquivo apenas uma vez (`O_EXCL`). Atualizações usam arquivo temporário exclusivo, `fsync`, substituição atômica e sincronização de diretório.

O protocolo de consulta `CHECK(revision, digest)` exige **igualdade exata** com a revisão e digest assinados no witness; nenhuma leitura do signer fornece o segredo. O protocolo de avanço `ADVANCE(expected, next_revision, digest)` exige CAS da revisão existente e incremento de exatamente um, sem downgrade. O witness recusa arquivo ausente, alterado, MAC incorreto, formato desconhecido ou permissões inseguras. O canal de escrita/avanço é entregue somente à autoridade I31; o assinador não o recebe. Um canal separado permite ao runner ler **somente a revisão**.

`backend/s1_i31_witness_authority_local.py` reaproveita o cliente `CHECK(fingerprint)` já aceito no I30 para o assinador mTLS. Antes de autorizar assinatura, a autoridade verifica (a) integridade e consistência do SQLite, (b) HMAC do checkpoint I30, (c) `watermark` próprio do processo e (d) igualdade da revisão e digest com o witness. Somente depois das quatro provas autoriza a identidade mTLS; o assinador então revalida GoTrue e assina HMAC da operação, e o PostgreSQL mantém validação de nonce/sessão e RBAC. A alteração de certificado continua sob `BEGIN IMMEDIATE` do I29, CAS, escrita atômica do checkpoint I30 e `ADVANCE` da testemunha. Uma falha entre qualquer etapa causa divergência e **bloqueio**, não fallback.

A testemunha pode sobreviver ao reinício da autoridade e do assinador. Se alguém restaurar **SQLite+checkpoint I30** para uma cópia antiga ainda autenticada, mas a testemunha conservar sua revisão atual, a nova autoridade recusa o boot/assinatura. Uma restauração honesta para a revisão contemporânea volta a operar. Se todos os arquivos, inclusive o da testemunha, forem restaurados juntos a uma versão antiga enquanto a testemunha também estiver desligada, **a prova perde seu ponto de comparação**.

## Testes planejados

`tests/test_s1_002_i31_monotonic_witness.py`: 15 casos novos, além dos 108 testes I23–I30, exercendo certificado válido, não autorizado, rotação, revogação, reinício do assinador, MAC/SQLite alterado, MAC da testemunha alterado, rollback SQLite+checkpoint depois de reiniciar a autoridade (witness continua), falha do witness, CAS obsoleto, bloqueio de reautorização, outra identidade da mesma CA, ausência da administração no signer, emergência e reinício honesto da autoridade e testemunha com o estado atual. Total esperado: **123 unitários**.

`scripts/test_s1_002_i31_witness_local.py`: repete **120 provas integradas I30**, com GoTrue real, 50 migrations S0/S1 e banco efêmero, acrescentando `S1WITNESS-121..132`: bootstrap único, operação legítima, CAS e avanço da testemunha, rotação/identidade revogada, restauração de snapshot antigo após reiniciar a autoridade, recuperação controlada, adulteração de SQLite/MAC da testemunha, RBAC intacto, reinício honesto da testemunha, revogação emergencial e persistência dessa revogação após novo reinício. Total esperado: **132 E2E**.

## Limitações e gates

**Não se trata de autoridade remota ou de proteção completa anti-rollback.** O runner CI possui a chave HMAC do witness, a chave HMAC do checkpoint, os arquivos de ambos, os certificados/CA e as conexões privadas. Não há root/UID/host/contêiner realmente segregados. Um invasor da conta do runner pode recriar/retroceder ambos os arquivos e reiniciar todos os processos; o MAC não substitui um contador monotônico externo, armazenamento append-only/WORM, HSM/KMS, validação de proveniência ou atestação de runtime. `CHECK` e `ADVANCE` são pipes locais, sem autenticação de identidade de workload. A escrita SQLite, checkpoint I30 e witness **não é uma transação distribuída**, logo pane no intervalo pode exigir recuperação administrativa explícita; não se deve reabrir um estado divergente automaticamente. Não existem recursos de HA/backup, segurança operacional de produção, canal TLS público nem integração com a interface gerencial/WhatsApp.

**NO-GO produção/merge/deploy.** Próximos requisitos: testemunha durável **fora do domínio de administração do assinador**, chave não exportável e verificação de monotonicidade entre reinícios completos, auditoria imutável, operação de recuperação e rollback controlados, isolamento real de workload e identidade, e homologação de gestão humana no S0. Não alterar percentuais globais de conclusão.

## Evidências confirmadas — aprovado apenas para continuidade em sandbox

**[GitHub Actions #39456206106 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39456206106)**, código ensaiado SHA `9d8c40d18e9d2ed849651f328b7fc2e91cb753f1`. Dois jobs inspecionados:

- Job `118743867662` (`http-policy-unit`): **123/123 unittest PASS**, os 108 testes legados I23–I30 mais 15 provas I31. Os logs registraram `Ran 30 tests ... OK`, `Ran 10 tests ... OK` duas vezes, `Ran 13 tests ... OK` e `Ran 15 tests ... OK` quatro vezes. Inclui replay de SQLite+checkpoint antigos **após reinício da própria autoridade**, enquanto a testemunha permaneceu ativa.
- Job `118743866960` (`e2e-gerencia-local`): **S1WITNESS-01..132 = 132/132 marcadores PASS distintos**, 50 migrations S0/S1 reais sobre PostgreSQL/GoTrue locais, fixtures somente de CI I20/I21/I22/I24. Os novos casos 121–132 confirmam bootstrap independente, operação GoTrue/HMAC sob witness, avanço CAS, revogação e sucessor, replay da versão antiga após autoridade reiniciar recusado, restauração explícita do estado corrente, adulteração de SQLite/witness negada, RBAC interequipe, reinício honesto de witness+authority, revogação total e persistência da recusa após reiniciar authority/signer.

**Histórico transparente:** [CI #39455942197](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39455942197) encontrou incompatibilidade de classe no cliente `CHECK` do novo módulo e foi cancelado na execução seguinte. Foi corrigido ao reutilizar o tipo `LocalAuthorityCheckClient` já validado do I30. O aceite **não** usa o run anterior, somente o run `39456206106` verde no SHA indicado.

**Parecer:** GO apenas para desenvolver no sandbox; **NO-GO para produção, merge e deploy**. O witness não oferece segurança contra a restauração **de todos os seus próprios arquivos** e do ledger pela mesma conta OS, nem prova de monotonicidade num serviço independente de segurança. Os commits documentais posteriores não modificaram o código testado.
