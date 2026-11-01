# Recebimento controlado — OpenAI OFF-02 a OFF-08

Este diretório **não** contém dados de produção. Recebe uma única distribuição auditada da frente OpenAI, para publicação em branch isolada após validação automática.

**Arquivo esperado:** `OAI_OFF_02_A_08_PATCH_AUDITADO_2026_10_31.zip`

**SHA-256 exato do ZIP:** `9116f713198d9c8b3061874d9c6c2dcb2a4045c384b02feaad4ca334b39b0feb`

**Fonte de autoridade de integridade:** [cópia byte-idêntica do manifesto](../OAI_OFF10_COPIA_MANIFESTO_SHA256_STAGING.json), 27 digests; 28 arquivos totais contando o manifesto.

## Procedimento de entrada

1. Na branch `test/oai-off08-payload-staging-20261031`, abra **este diretório** no GitHub.
2. Use **Add file → Upload files** e selecione apenas o ZIP indicado acima, preservando o nome.
3. Faça commit **somente na branch de staging**, não em `main`.
4. O workflow [`oai-off08-verified-intake.yml`](../../../../.github/workflows/oai-off08-verified-intake.yml) executará os controles em GitHub Actions e criará `feat/oai-off02-off08-offline-20261031` **somente se** ambos os gates de 678 testes PASS (0 falhas/skips).

O workflow **não** aceita ZIP diferente, não substitui arquivos OFF-01, não cria código S0/Meta, não faz merge/deploy ou operação produtiva. Em caso de falha, consulte o log do run: **não** force push nem ajuste expectativas de testes.

Este processo é candidato/offline e não representa ratificação, homologação ou autorização de comunicação. O resumo curto F01/F02/F03 continua somente planejado na Issue #13, fora desta remessa.

## Arquivos do chat

- **Essenciais de código/testes e documentação corrente:** os 28 arquivos do ZIP indicado.
- **Fonte herdada OFF-01:** já versionada no commit `394512327cd3756dfbe61ff970a6279c354b6565`; não duplicar nem substituir.
- **Relatórios locais antigos e ZIPs anteriores:** evidência histórica, alguns superados; arquivar seletivamente como documentação, **não** sobrescrever o candidato auditado.
- **Pacote de documentação geral da plataforma e ideias LiberaCred:** contexto de projeto, não incorporar automaticamente a esta branch técnica nem misturar conceitos sem reconciliação com decisões vigentes.

**Estado de entrada ao criar este README:** ZIP ainda **não** foi transferido para GitHub.
