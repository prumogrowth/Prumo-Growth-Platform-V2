# S1-002/I27 — autenticação mútua TLS do gateway e do assinador (20/10/2026)

**Escopo isolado:** apenas `feat/s1-002-equipe-prumo` e PR #5 Draft. Todas as chaves e certificados são sintéticos e temporários. Não há migration operacional, alteração do Supabase hospedado, merge, deploy nem acesso à Meta ou a clientes reais.

## Problema e decisão

I26 validou 50/50 testes unitários e 70/70 E2E com **GoTrue consultado pelo processo assinador**, vinculando a prova HMAC ao usuário e à sessão. Mas o canal de assinatura ainda dependia da posse de um descritor IPC dentro da mesma conta de sistema: o assinador não tinha uma identidade de serviço autenticada independentemente do bearer do usuário.

O I27 testa **mTLS real entre dois processos locais**, com identidades criptográficas diferentes: o assinador requer um certificado de cliente emitido pela CA efêmera e também verifica **fingerprint exato do certificado gateway autorizado**; o cliente gateway exige certificado de servidor assinado pela CA, nome DNS `localhost` e **fingerprint exato do assinador esperado**. TLS não substitui a verificação GoTrue nem as regras S1 de autorização de equipe.

## Implementação do experimento

`backend/s1_i27_ephemeral_certificates.py` cria, somente em `TemporaryDirectory`, uma CA de 1 dia e três certificados de finalidade distinta usando OpenSSL local: `signer` (SAN DNS:localhost e IP 127.0.0.1, EKU serverAuth), `gateway` (EKU clientAuth) e `intruder` (outro clientAuth válido, emitido pela mesma CA). Não há repositório de certificados, chaves permanentes ou compartilhamento com browsers.

`backend/s1_signer_mtls_local.py` inicia outro processo `spawn` com listener **127.0.0.1:porta efêmera**, `SSLContext(PROTOCOL_TLS_SERVER)`, TLS mínimo 1.2, `CERT_REQUIRED`, CA confiável e verificação do fingerprint do cliente após o handshake. Uma requisição de assinatura somente chega ao GoTrue quando a identidade mTLS do cliente foi aceita. Ela contém material canônico, key ID e Bearer; o assinador faz `GET /auth/v1/user` diretamente, compara ator e session ID, checa comando, formato e janela temporal, assina com chave HMAC privada do filho e não retorna segredo. O cliente valida hostname e pin do certificado de servidor antes de enviar a requisição. Frames JSON têm tamanho limitado, campos duplicados rejeitados e nenhum payload de cliente é gravado nos logs.

O supervisor administrativo do runner mantém um **segundo canal de controle (pipe)** para `LOAD/REVOKE/STOP`, fora do socket TLS de assinatura; um endpoint TLS autenticado não recebe autorização para provisionar/revogar chaves. O gateway usa `LocalIndependentlyAuthenticatedGateway` do I26, passando a ter um cliente mTLS que implementa a mesma interface `sign(key, material, bearer)`. No banco, a custódia I22, nonce transacional I20, revogação CAS I24 e revalidação de `auth.sessions` I15 continuam intactas.

## Critérios de teste

O job unitário repete os 30 cenários HTTP I23 + 10 testes de processo I25 + 10 de autenticador I26 e acrescenta **13 provas mTLS I27** de: conexão válida, falta de certificado de cliente, outro certificado válido emitido pela mesma CA, pin de servidor incorreto, CA de confiança incorreta, bearer inválido, ator forjado, sessão forjada, assinatura expirada, chave revogada, processo encerrado, ausência de bearer e rejeição de configuração insegura.

O E2E `scripts/test_s1_002_i27_mtls_local.py` mantém 70 cenários anteriores sobre 50 migrations reais S0/S1 e acrescenta **S1MTLS-71..80**, exercendo autenticação mútua, operador gerenciado sob GoTrue real, cliente certificado incorreto, ausência de certificado, pin de servidor incorreto, ator/sessão falsos, RBAC interequipe, revogação do assinador e pane fail-closed sem escrita comercial.

## Limites e NO-GO para produção

Este ensaio estabelece autenticação mútua criptográfica no **transporte local**, mas **não** garante identidade operacional independente: ambas as chaves TLS, CA, segredos HMAC, pipe administrativa e credenciais de conexão continuam controladas pela mesma conta do runner de CI. Um atacante que comprometa essa conta poderá copiar certificados/chaves e assumir o serviço. Falta custódia separada das chaves TLS e HMAC, identidades de workloads/contêiner distintas, certificados emitidos e rotacionados por PKI de produção, políticas de revogação, attestation, proteção da pipe administrativa, proteção contra acesso ao token legítimo de gerente, auditoria WORM externa e autenticação HTTP real. O serviço de assinatura continua serial e `socket` padrão, não representa servidor resiliente ou endurecido contra esgotamento de conexões.

**NO-GO para merge, deploy ou produção.** A interface de gerência e a conclusão humana S0 continuam pendentes. Os testes não constituem auditoria externa ou comprovação de infraestrutura independente.

**Evidência CI:** a preencher exclusivamente depois de conferir os dois jobs, commits e logs.
