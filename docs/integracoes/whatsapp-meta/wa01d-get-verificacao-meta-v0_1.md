# WA-01D — desafio GET do webhook Meta por aplicativo | 18/10/2026

**Estado: engenharia sintética; não é endpoint publicado nem homologação de onboarding.**

## Evidência e finalidade

O GET de validação da Meta contém `hub.mode=subscribe`, `hub.verify_token` e `hub.challenge`. O servidor valida o **verify token configurado para aquele App** e devolve o desafio em texto simples com `200`; falha de validação recebe recusa. Isso é separado da assinatura HMAC do corpo bruto de cada POST, que usa o **App Secret**, e separado do token de acesso à Graph API. Referência: documentação de webhook Meta, SDK oficial arquivado e contrato do PR #2. Nenhum desses tokens aparece neste módulo.

Implementação isolada: `integrations/whatsapp-meta/verify-get.ts`, função pura de borda `inspectMetaVerifyGet(rawQuery, trustedVerifyToken)`, com parâmetros estritos, limite de tamanho, detecção de duplicatas, comparação de hashes por varredura de comprimento fixo e resposta sem cache. Recebe `trustedVerifyToken` **escolhido pela configuração protegida do App**. O valor `hub.verify_token` do usuário não escolhe App, loja, WABA, segredo, rota nem permissão. O challenge é devolvido como string decimal intacta, sem conversão numérica e sem interpolar conteúdo arbitrário. Resultados são decisões inertes `{status, body, headers}`: **não existe chamada HTTP, registro de URL ou função Supabase neste código**.

A assinatura HMAC Meta sobre o POST **não** é validação de GET; o GET não demonstra que WABA, telefone ou canal real foi cadastrado. Não registrar URL, query, challenge ou token em log, analytics, tracing ou exceção. A futura definição operacional de segredos/rotação, resposta a erros, rate-limit e retenção pertence à DEC-WA-06.

## Ponto novo da revisão da S0/030

A migration 030 do PR #1 acrescentou fixture multicanal e armazenamento **apenas fictício**. O retorno `FIXTURE_BATCH_STORED` não certifica commit operacional nem payload recuperável, e não pode ser mapeado para ACK real. A seleção do segredo por App e vinculação com vigência histórica ainda não existem.

**Regra de fronteira proposta:** um HTTP POST da Meta apresenta uma assinatura `X-Hub-Signature-256`. O ingressor escolhe o App por roteamento confiável e valida aquela assinatura; não deve interpretar um único POST como eventos autenticados de **vários Apps independentes**, a menos que exista um mecanismo comprovado e aprovado de autenticação de cada App. `entry[]` múltiplos não equivalem a App múltiplo. O fixture cruzando apps/lojas da 030 é teste de atomicidade de banco, **não prova criptográfica de POST real**. Não derivar `app_ref` nem `concessionaria_id` do texto de entrada.

## Testes e gate

`node --experimental-strip-types --test integrations/whatsapp-meta/verify-get.test.ts`: **WA-GET-01..12 PASS** em Node 22.16.0 local; `tsc --noEmit` também aprovado na checagem específica dos arquivos. Arquivos publicados têm SHA Git idêntico aos arquivos ensaiados.

Próximos bloqueios: registry de App/WABA/canal e segredos com vigência (núcleo + DEC-WA-06), política de lote multicanal, payload protegido e recibo durável verificado, ambiente DEC-WA-04 e validação operacional parcial da DEC-WA-05. **Proibidos** deploy, migrations hospedadas, alteração de números comerciais concessionária de demonstração, WABAs/inscrições e merge automático; PRs Draft.
