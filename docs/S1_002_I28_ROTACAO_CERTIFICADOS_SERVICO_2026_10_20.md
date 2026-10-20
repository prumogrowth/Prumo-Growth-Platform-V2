# S1-002/I28 — Rotação e revogação de identidade TLS do gateway (20/10/2026)

**Situação:** exclusivamente sandbox/CI; PR #5 Draft, branch `feat/s1-002-equipe-prumo`, base `feat/s0-fundacao-prumo`. Não houve novas migrations operacionais, deploy, merge, Supabase hospedado, chaves reais ou usuários comerciais.

## Base e lacuna

O I27 comprovou **63/63 testes unitários e 80/80 E2E** em CI com TLS mútuo real no loopback, pin explícito do certificado servidor e do certificado gateway, GoTrue revalidado dentro do assinador, HMAC verificado no PostgreSQL e RBAC de equipe. O par de certificados era fixo para a vida inteira do processo: não havia introdução coordenada de identidade sucessora nem desativação de um certificado comprometido sem encerrar o serviço.

## Escopo da implementação I28

A fixture `backend/s1_i28_rotating_certificates.py` usa OpenSSL local para gerar duas identidades adicionais sob **a mesma CA efêmera do I27**: `gateway_next` e `gateway_rogue`, com EKU de clientAuth. Todos os materiais ficam em diretório temporário criado durante testes, descartado ao final. Não há CA de produção, KMS/Vault nem certificados armazenados no Git.

`backend/s1_signer_mtls_rotation_local.py` implementa um assinador local que continua exigindo certificado de cliente assinado pela CA e **fingerprint SHA-256 exato presente na lista autorizada**. A lista nasce contendo somente o gateway original; para trocar o cliente são exigidas operações administrativas transmitidas pela pipe separada do supervisor (jamais pelo transporte mTLS de assinatura):

- `STAGE_CERT(fingerprint, expected_version)`: inclui certificado sucessor somente quando a revisão esperada corresponde à vigente; até **duas identidades simultâneas** para sobreposição operacional. A revisão avança.
- `REVOKE_CERT(fingerprint, expected_version)`: remove a identidade da allowlist, mantém o fingerprint em conjunto de revogados **enquanto o processo existir** e incrementa a revisão. Nunca cria chave nova nem altera grants de banco. Permite remover a última identidade em emergência, encerrando imediatamente *novas* autorizações.
- `STATUS`: informa ao runner administrativo apenas `version`, número de certificados ativos/revogados e eventos classificados com sua revisão (`CERT_STAGED`, `CERT_REVOKED`); **não expõe bytes de certificado, pins, tokens, segredos HMAC, ator, cliente ou conteúdo da operação**.
- Requisição administrativa com revisão obsoleta devolve `STALE`; fingerprint inválido, identidade repetida, limite ativo excedido e tentativa de reutilizar fingerprint revogado devolvem `DENIED`. O socket TLS aceita somente a operação de assinatura allowlisted e GoTrue independente: não há `LOAD`, `STAGE_CERT` ou `REVOKE_CERT` no protocolo de rede.

### Operação segura simulada

Provisionar certificado sucessor fora do assinador usando CA de CI; verificar fingerprint, estágio sob revisão conhecida, experimentar nova conexão mTLS com cliente novo, alternar o gateway, confirmar transações gerenciais autorizadas e, finalmente, revogar o certificado antigo. Depois da confirmação de revogação, a conexão antiga não consegue solicitar assinatura nova. Em incidente, revogar todas as identidades ativas implica **fail closed e indisponibilidade planejada** até uma substituição com governança. O banco permanece autoridade final de sessão, HMAC/nonce e equipe.

As decisões de certificado são verificadas em **cada nova conexão**. O protótipo trata conexões sequencialmente; a revogação é reconhecida ao processar o comando administrativo e **não é alegada como cancelamento retroativo de uma operação já assinada**. Uma assinatura emitida pouco antes da revogação do certificado pode continuar válida pelo curto prazo do HMAC, enquanto a chave HMAC e sessão estiverem válidas; revogação emergencial total também exige avaliar revogar chave HMAC e sessão.

## Verificações previstas

`tests/test_s1_002_i28_cert_lifecycle.py`: 15 provas novas usando servidor GoTrue sintético (sem verificação criptográfica JWT), além dos 63 testes de unidade I23/I25/I26/I27: cliente original, sucessor não provisionado, estágio CAS, overlap, revogação anterior, bloqueio de reautorização, revisão obsoleta, identidade não autorizada, fingerprint inválido, limite 2, GoTrue ator divergente, cliente sem comando administrativo, auditoria mínima, emergência sem identidades e pane do assinador. **Total esperado 78 unitários**.

`scripts/test_s1_002_i28_service_rotation_local.py`: repete **80 provas E2E I27** com 50 migrations S0/S1 reais em banco GoTrue descartável, HMAC/nonce, RBAC e certificados I27; mais 13 casos S1ROT-81..93 de PKI/segredo, operação legítima inicial, recusa pré-stage, stage CAS, overlap real, versão obsoleta, revogação do antigo com sucessora ativa, não reativação, certificado alheio negado, auditoria mínima, Bearer inválido, RBAC interequipe e revogação emergencial fail-closed sem alterar equipe. **Total esperado 93 verificações E2E**.

## Limitações e gates de produção

A lista de revogados e a auditoria do I28 são **voláteis** e **não sobrevivem à reinicialização do processo**; a reconfiguração/recriação do serviço não consulta uma base independente de certificados revogados. O runner possui CA privada, chaves TLS dos dois serviços, pipe administrativa, segredos HMAC sintéticos e conexão privilegiada local. A autenticação mTLS é real no TLS loopback, mas **não equivale a workloads isolados, PKI gerenciada, governança de certificados com CRL/OCSP, política de validade/rotação operacional, auditoria WORM, Vault/KMS/HSM ou atendimento de infraestrutura externa**.

Riscos restantes: roubo de Bearer válido e/ou certificados TLS/OS, comprometimento da CA, endpoints de controle por mesmo usuário de sistema, falta de proteção contra indisponibilidade de rede, ausência de telemetria/alerta durável, rollback seguro de certificados e recovery de assinador após reinício. Produção também exige identidade distinta de serviço, controle independente de emissão de certificados e processo formal de revogação/recuperação e integração gerencial com conclusão humana S0.

**Parecer:** GO para continuar desenvolvimento isolado somente se CI comprovar a suíte; **NO-GO produção, merge, deploy e Supabase hospedado**. Nenhuma porcentagem global do projeto decorre deste teste.

## Resultado verificado em CI — aprovado apenas para sandbox

**[GitHub Actions #39401134475 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39401134475)**. Código testado no SHA `eda5d84efac3cd14040d1ac1cb32f7229a82e977`; os dois jobs terminaram em `success`.

- Job `118555841880` (`http-policy-unit`): **78/78 unittest PASS**, conforme cinco relatórios `Ran 30 tests ... OK` (I23), `Ran 10 tests ... OK` (I25), `Ran 10 tests ... OK` (I26), `Ran 13 tests ... OK` (I27) e `Ran 15 tests ... OK` (I28). Inclui certificado sucessor não autorizado, CAS de revisão, overlap controlado, identidade revogada, cliente não confiável, GoTrue, auditoria mínima e emergência.
- Job `118555841207` (`e2e-gerencia-local`): **S1ROT-01..93 = 93/93 identificadores únicos PASS**, logs examinados. A execução repetiu a cadeia das 50 migrations S0/S1 reais em GoTrue/PostgreSQL efêmeros, fixtures exclusivamente locais I20/I21/I22/I24 e os 80 gates anteriores. S1ROT-81..93 foram confirmados: CA temporária, gestão autorizada, sucessor pré-stage negado, stage CAS, overlap operativo, versão stale recusada, revogação antiga com sucessora ativa, proibição de reautorização do antigo, outro certificado válido mas não allowlisted negado, histórico sem dados secretos, bearer falso recusado, RBAC interequipe e emergência sem alteração do estado da equipe.

**Parecer técnico:** GO exclusivamente para prosseguir em sandbox. **NO-GO para produção, merge, deploy e Supabase hospedado.** Os eventos e revogações de identidade são **voláteis**, controlados pela mesma conta OS que possui certificados/CA e segredos sintéticos. Nenhuma PKI, CRL/OCSP, rotação de workload real ou auditoria imutável externa foi homologada. A evidência acima corresponde ao SHA de código testado; commits subsequentes de documentação não alteram esse resultado.
