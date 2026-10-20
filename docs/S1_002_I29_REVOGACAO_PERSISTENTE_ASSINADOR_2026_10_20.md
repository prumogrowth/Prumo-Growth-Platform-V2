# S1-002/I29 — ledger durável de certificados e recuperação após reinício (20/10/2026)

**ESCOPO RESTRITO A CI DESCARTÁVEL.** Branch `feat/s1-002-equipe-prumo`, PR #5 Draft; sem merge, deploy, nova migration operacional, Supabase hospedado, clientes ou chaves reais.

## Origem da lacuna

I28 comprovou **78/78 testes unitários e 93/93 E2E** de rotação mTLS de identidade de serviço, com revisão CAS e lista de revogados. Seu assinador, entretanto, guardava revisão, allowlist, tombstones e eventos **somente em memória**. Quando reiniciado, podia reautorizar o fingerprint inicial sem consultar a revogação anterior.

I29 ensaia um registro **persistente em arquivo SQLite fora da memória/processo do assinador**, separado de um canal de administração. Não se trata de banco hospedado nem armazenamento imutável. O uso de SQLite é apropriado **apenas para provas em runner efêmero**.

## Contrato

`backend/s1_i29_persistent_certificate_store.py` contém `LocalCertificateState`:

- Bootstrap administrativo `initialize(initial_fp)` por criação atômica `O_EXCL` e modo `0600`. **Não** recria nem sobrescreve um ledger existente; reinício usa unicamente `snapshot()`/conexão existente. Somente fingerprint SHA-256, estado `ACTIVE|REVOKED`, revisão CAS e código de evento são armazenados. Não há certificados PEM, chaves TLS, bytes HMAC, JWT, ator ou dado comercial.
- Schema SQLite separado `meta`, `certificates`, `events`, `PRAGMA synchronous=FULL`; mudanças `STAGE_CERT/REVOKE_CERT` sob `BEGIN IMMEDIATE`, expectativa de revisão, índice único e histórico mínimo de eventos. As transições de `REVOKED` são terminais pelas APIs. Máximo duas identidades `ACTIVE` durante overlap; remoção da última aceita para fail closed emergencial.
- Leitura `mode=ro` e `PRAGMA query_only=ON`, valida `PRAGMA integrity_check`, schema, revisão, sequência de eventos, contagens, fingerprints e estados; arquivo ausente, permissões inseguras, corrupção ou estados inconsistentes geram `RevocationStateUnavailable` e nunca autorizam uma assinatura.
- Essa validação cobre **corrupção/erros estruturais**, não adulteração maliciosa por quem controla o arquivo e SQLite. Um DBA/operador OS com acesso pode reescrever dados e histórico consistentes; **não há prova de autenticidade nem armazenamento WORM.**

`backend/s1_signer_mtls_persistent_local.py` mantém TLS mútuo real, pin de certificado servidor e autenticação GoTrue independente do filho. Em **toda nova conexão TLS**, abre o arquivo separado em modo leitura, exige que fingerprint do cliente esteja ativo e nega acesso se ledger indisponível/adulterado. Um watermark em memória rejeita **revisão mais antiga do que a já observada por aquele processo**. Isso **não protege contra restauração de um snapshot antigo antes de reiniciar o processo**: faltaria contador monotônico externo, ledger assinado ou autoridade independente.

O `LocalPersistentTlsSignerSupervisor` é o único objeto que recebe métodos administrativos `stage_certificate`, `revoke_certificate` e `rotation_status`; alterações persistem com CAS antes de novas decisões TLS. O gateway mTLS recebe apenas o cliente `sign(key, material, bearer)`. Chaves HMAC permanecem em memória do processo assinador e **precisam ser provisionadas novamente por um controlador sintético após a reinicialização**; o ledger **não** faz backup/recuperação de chaves HMAC.

## Critérios de teste

O CI repete 78 provas unitárias I23/I25/I26/I27/I28 e acrescenta **15 testes I29**: bootstrap único, sucessor pré-stage recusado, overlap persistente, revogação antiga com sucessor funcional, reinício com tombstone presente, proibição de reautorizar antigo após reinício, arquivo removido, corrupção, permissão insegura, revisão CAS obsoleta, concorrência com apenas um vencedor, certificado de outra identidade da mesma CA, histórico mínimo após reinício, rollback detectado pelo processo **após observar** revisão mais nova, emergência revogando todos e reinício fail closed. Total planejado **93 unitários**.

O E2E `scripts/test_s1_002_i29_persistent_revocation_local.py` repete **93 provas I28** em GoTrue/PostgreSQL reais e descartáveis (50 migrations S0/S1 + fixtures locais I20–I24), acrescido de 12 casos `S1PERSIST-94..105`: criação única do ledger, operação legítima, estágio e rotação, revogação inicial, reinício com tombstone, sucessor operacional, arquivo removido e operação negada, novo processo sem ledger negado, corrupção recusada, CAS e revogação mantidos, RBAC intacto e emergência mantendo todos os certificados negados após novo restart. Total planejado **105 E2E**. Logs não contêm bearer, secrets ou fingerprint de certificado.

## Riscos abertos, antes de produção

**A persistência testada não é proteção operacional independente nem rollback-proof.** Os arquivos de certificado e ledger SQLite, CA, credenciais HMAC e canal administrativo ainda são controlados pelo mesmo usuário OS do runner. Acesso com escrita ao banco SQLite permite adulteração e rollback antes do reinício. O arquivo do runner desaparece quando a infraestrutura efêmera termina: isso não equivale a backups, Vault/KMS/HSM, auditoria imutável, replicação, DR, isolamento em workloads distintos ou PKI gerenciada com CRL/OCSP. A leitura de SQLite em toda conexão TLS e o socket serial do laboratório não representam arquitetura de alta disponibilidade.

Para um desenho operacional futuro: criar autoridade de certificado em serviço/identidade separados com ACL, storage imutável ou ledger verificável criptograficamente, contramedida anti-rollback com monotonic counter/serviço externo, revogação de certificado servidor e cliente, processo de renovação controlado e propagação de mudança em múltiplas réplicas; segregar HMAC/CA/DBA/operador de domínio; testar pane e recuperação sem restaurar revogados; auditar cada decisão de rotação e executar revisão de ameaça no canal admin. Interfaces de gestão e conclusão humana S0 ainda pendem.

**NO-GO para merge, produção e deploy.** Nenhuma porcentagem de conclusão global. Aceite de CI somente depois de logs completos dos dois jobs.

## Evidência revisada — CI aprovado exclusivamente no sandbox

**[GitHub Actions #39404883256 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39404883256)**, código ensaiado no SHA `bb86bca7626c4a2abea976bbc30824bb92fd332e`; dois jobs `success`, logs verificados.

- Job `118568281189` (`http-policy-unit`): **93/93 testes unitários PASS**, cinco grupos de regressão (30 HTTP I23; 10 assinador I25; 10 GoTrue I26; 13 mTLS I27; 15 rotação I28), mais **15 novos I29**. Logs com `Ran 30 tests ... OK`, `Ran 10 tests ... OK` duas vezes, `Ran 13 tests ... OK` e `Ran 15 tests ... OK` duas vezes. Confirmados concorrência CAS, tombstone após restart, ausência/corrupção/permissões de arquivo, watermark de versão apenas na vida do processo e emergência.
- Job `118568281629` (`e2e-gerencia-local`): **S1PERSIST-01..105 = 105/105 identificadores distintos PASS**, 50 migrations S0/S1 reais em GoTrue/PostgreSQL descartáveis, fixtures locais I20–I24 e regressão de todos os gates I28. As 12 provas S1PERSIST-94..105 atestaram ledger único, operação e rotação autorizadas, certificado antigo revogado, restart sem reativação, sucessor funcional após restart, arquivo removido/corrompido bloqueando escrita comercial, ausência impedindo restart, restauração sintética explícita, controle CAS e RBAC preservados e emergência sobrevivendo a novo restart.

**Ressalva crítica:** essas evidências demonstram continuidade de revogação com **arquivo SQLite sintético intacto no mesmo filesystem**; não garantem assinatura criptográfica/autenticidade do ledger ou resistência à restauração de um snapshot antigo **antes de reiniciar o assinador**. A exigência de storage/identidade operacional independentes, anticlonagem/anti-rollback e auditoria WORM externa permanece. Sem mudança na base hospedada nem no estado humano de S0. Documentação e aceite posteriores ao SHA não alteram código executado.
