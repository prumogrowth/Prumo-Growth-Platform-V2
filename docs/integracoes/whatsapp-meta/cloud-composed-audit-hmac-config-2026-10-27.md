# Auditoria técnica — composição de webhook Meta (isolamento e custo)

**Data:** 27/10/2026. **Base preservada:** PR #34, commit `c1143ec62160d47ba0177e28187fad1433bb403f`. **Branch isolada:** `audit/meta-cloud-composed-cost-snapshot-20261027`.

## Escopo e metodologia

Auditoria do `inspectSignedMetaComposedWebhook()`, com foco em robustez de configuração assíncrona, composição sem perdas, custo de HMAC por lote e preservação das barreiras existentes. Inspeção do código remoto e prova adversarial na própria GitHub Actions, em ambiente Node 22 e fixtures fictícias.

A versão de base executava **seis verificações HMAC WebCrypto por webhook** (verificador de ingresso e cinco leitores especializados) independentemente do conteúdo do lote. Além disso, reutilizava `trustedRoute` e `limits` por referência ao longo de múltiplos `await`: um chamador que alterasse tais objetos depois da invocação poderia modificar a proveniência ou causar recusas inconsistentes.

## Falhas demonstradas antes do reparo

Executados os primeiros 16 testes adversariais **antes de alterar o módulo**, na branch auditora:

- GitHub Actions **run 40585679496**, commit `2b07d25c564d4160b95c50590e8d570e65e6fd48`: **2 passaram, 14 falharam**.
- Os testes demonstraram desperdício de HMAC para tipos ausentes e a dependência de objetos mutáveis fornecidos pelo chamador, incluindo WABA/phone, `route.revision` e `maxEvents`/`maxBodyBytes`.
- O resultado negativo foi intencional na fase de reprodução, não estado final do PR. Não foram utilizados dados reais.

## Reparos

**1. Snapshot confiável:** no início da chamada, antes do primeiro `await`, copiar `waba_id`, `phone_number_id`, `revision`, `maxBodyBytes` e `maxEvents` para objetos independentes congelados. A base e cada leitor especializado recebem **a mesma cópia**. Erros de acesso à configuração negam o lote.

**2. Composição seletiva sem bypass:** primeiro autenticar a totalidade do corpo e o scope pelo `inspectCloudWebhookForHandoff()`. Usar **somente os tipos de eventos já autenticados** para escolher quais leitores executar:
- `button`/`interactive` → leitor de seleções;
- `reaction` → reações;
- `image`/`audio`/`video`/`document`/`sticker` → mídia;
- `unsupported` → códigos de mensagens recebidas;
- **qualquer status, inclusive `sent`/`delivered`/`read`** → leitor de códigos de status, pois este também detecta `errors[]` inconsistente em estados que não são `failed`.

Cada leitor executado **continua fazendo sua própria verificação HMAC**, escopo e parsing do mesmo corpo imutável. A composição mantém conferência do `raw_sha256`, da identidade, do endereço de ocorrência, de colisões e lacunas, e negação integral para qualquer incompatibilidade. Não houve relaxamento de validação de respostas, envio, tentativa ou armazenamento.

## Custo criptográfico aferido

Contagem **real de chamadas** a `crypto.subtle.verify()` nos testes Node, sem inferência de tempo de execução:

| Lote assinado | Antes | Depois | Redução de verificações |
|---|---:|---:|---:|
[TRECHO COMERCIAL INTERNO EXCLUÍDO DA VERSÃO PÚBLICA]
| Um tipo especializado (ou apenas status) | 6 | 2 | 66,7% |
| Reação + status de entrega, sem outras especializações | 6 | 3 | 50% |
| Todos os cinco grupos especializados | 6 | 6 | 0% |

Esses números são quantidade de verificações, **não benchmark de latência**, FPS, consumo de memória ou economia monetária. Lotes de até 100 eventos foram testados sem criar uma verificação HMAC por evento. Um lote com 101 eventos falha pela proteção pré-existente de capacidade.

## Testes e integração

`integrations/whatsapp-meta/cloud-composed-observation-audit.test.ts`: **20 provas novas**, incluindo contagem WebCrypto por tipo, todas as categorias, falhas de status mesmo sem `failed`, variantes interativas desconhecidas, alterações simultâneas de rota/revisão/limites, mutação dos bytes e lotes no limite de 100 eventos.

`.github/workflows/meta-cloud-composed-audit-offline.yml`: 20 novos + **174 regressões focadas** herdadas (composição, seleções, reação, mídia, status, `unsupported`, HMAC e roteamento). Total esperado: **194**. O SHA final, o resultado e os logs devem ser conferidos na GitHub Actions para certificação. Não executa toda a bateria WA39–68.

## Decisões e pendências

A otimização não cria interface de snapshot autenticado para terceiros, não remove a validação dos leitores necessários e não afirma `exactly_once`/dedupe. Como todo o código da frente Meta, permanece **somente offline**, sem network Graph, segredos reais, clientes, HTTP 200/ACK, migrações, Supabase, S0/S1, merge ou deploy.

Nenhum novo pedido à S0 é necessário para esta auditoria. A operação produtiva, persistência durável e futura composição compartilhando um artefato de HMAC validado devem ser objeto de contrato/autorização específicos; PRs candidatos #14/#19 seguem sem ratificação.
