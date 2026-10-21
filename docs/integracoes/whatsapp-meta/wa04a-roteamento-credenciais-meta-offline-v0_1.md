# WA-04A — Seleção de credenciais Meta por concessionária (offline) | 18/10/2026

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Estado:** proposta técnica [P] isolada no PR #2. **Não é integração operacional de segredos, Supabase ou WhatsApp.** O usuário está providenciando as credenciais definitivas e informou que as cadastrará pessoalmente no Supabase; a frente Meta aguardará a sua confirmação para qualquer avaliação das configurações reais. Não solicitar valores secretos no chat, Issues, PRs ou arquivos de repositório.

## 1. Diretriz respeitada

DEC-WA-05 [D] estabelece que **cada concessionária é titular do próprio Meta App, WABA, número e credenciais**. A Prumo age sob autorização revogável. A relação App/WABA/Phone Number ID ↔ canal/concessionária deve ser comprovada no **núcleo S0**; não é derivada de JSON, query string ou telefone do cliente.

A interface candidata distingue três credenciais **com propósitos diferentes**:

| Propósito | Descrição | Fonte futura |
| --- | --- | --- |
| `GET_VERIFY_TOKEN` | Token de desafio/verificação de propriedade do endpoint GET | Configuração protegida do App selecionado pelo roteamento |
| `POST_APP_SECRET` | App Secret usado para autenticar a assinatura HMAC do POST | Configuração protegida do App selecionado pelo roteamento |
| `GRAPH_ACCESS_TOKEN` | Token de acesso usado por serviço autorizado para chamadas Graph de saída | Contexto autenticado de concessionária/canal e autorização de envio S0 |

**Não confundir** o token de GET, o App Secret de POST e o token Bearer da Graph API. Não reutilizar um slot para dois propósitos ou duas concessionárias. Os nomes fictícios `WA_META_A_VERIFY`, `WA_META_A_HMAC` e `WA_META_A_GRAPH` nos testes não são segredos reais nem nomes definitivos que precisam ser criados agora.

## 2. Código implementado

`integrations/whatsapp-meta/credential-routing.ts` exporta:

- `selectMetaCredential(reg, command)` — retorna **somente o nome de referência (`secret_slot`)**, finalidade, `app_ref` e versão; nunca o valor do segredo. GET e POST só procuram App a partir de `trusted_route_ref` fornecida por roteamento protegido da aplicação, não de argumento do webhook; GRAPH exige um escopo completo emitido pelo serviço S0, com concessionária, canal, App, WABA e emissor exatamente vinculados.
- `resolveSignedMetaChannel(reg, query)` — resolve WABA + Phone Number ID em canal/concessionária, **apenas como função que deverá ser chamada depois de autenticação HMAC externa**. Seu campo `authenticated_app_ref` não é uma prova criptográfica; nunca expor esta função diretamente a solicitações públicas.

O registro candidato é `TrustedMetaRegistry` com `app_ref`, `route_ref`, `concessionaria_id`, `revision`, intervalo de vigência, status ativo, três referências de segredo e canais vinculados. Recusa duplicidades de app/rota/emissor/slot, escopo divergente, App ou canal revogado, revisão desatualizada e intervalos de vigência vencidos. A versão deve vir de uma **fonte de verdade atual** e evitar corrida entre checagem e uso real.

**Toda saída traz `production_authorized: false`**. Mesmo `ok: true` só significa que a configuração **fictícia** é coerente, não que o backend autorizou Graph, que o usuário tem opt-in, que o canal existe na Meta, que o secret está no Supabase ou que a transmissão pode ocorrer.

Não há `Deno.env`, `fetch`, URL de Graph, Supabase Client, token, HTTP endpoint, worker, política de refresh, armazenamento persistente, mutação de credenciais nem leitura de ambiente hospedado. O objeto de retorno `secret_slot` é **metadado interno**, não deve ser exposto ao cliente nem incluído em logs públicos.

## 3. Supabase — preparo, não configuração

A [documentação atual de Edge Function Secrets](https://supabase.com/docs/guides/functions/secrets) recomenda cadastrar segredos pelo painel do projeto e acessá-los **somente pelo runtime servidor**; os valores não devem entrar em Git, testes, mensagens ou frontend. Variáveis com prefixo `SUPABASE_` são reservadas.

- **O usuário realizará o cadastro manualmente.** Este PR não define, cria, busca nem altera segredos, e não verifica se foram cadastrados.
- **DEC-WA-04 está pendente:** não assumir que o Supabase da POC isolada concessionária de demonstração (`whatsapp-webhook-sandbox`) é o ambiente definitivo. Identificar explicitamente projeto/ambiente correto **antes de qualquer conexão ou teste real**, sem tocar na POC.
- **DEC-WA-06 está pendente:** confirmar cofre/isolamento, política de rotação e revogação, retenção, backup/restore, monitoramento e privilégio mínimo.
- Uma variável por propósito por App é adequada às *fixtures*, não necessariamente à escala. Segundo os [limites atuais de Edge Functions](https://supabase.com/docs/guides/functions/limits), há limite de **100 segredos por projeto**; para muitas concessionárias, escolher antes um esquema de armazenamento protegido e seleção de segredos que escale, sem utilizar nomes ou valores expostos.
- A versão/revisão e revogação são apenas comparações locais. A future função operacional precisará obter o *binding* ativo e resolver o segredo com **escopo autenticado, menor privilégio e verificações contra trocas concorrentes**.

**Quando o usuário avisar que terminou o cadastro:** solicitar/confirmar somente **nome do projeto e ambiente escolhido, identificação dos Apps/canais e nomes das chaves (sem valores)**; iniciar com verificação segura de presença/referência e teste isolado, após autorização específica e conforme gates DEC-WA-04/06. Uma mensagem de confirmação **não libera automaticamente** Graph de saída, substituição do webhook ou mudança de número comercial.

## 4. Provas da entrega

Node.js `22.16.0`: `node --experimental-strip-types --test credential-routing.test.ts` → **WA-CRED-01..19: 19/19 PASS**. Cobertos App A/B, três propósitos independentes, vigência/revogação/revisão, divergência loja/canal/WABA/número, duplicidade entre Apps, nomes de segredo inválidos, prefixo reservado, ausência de token/PII no resultado e impossibilidade de atribuir permissão operacional.

TypeScript `5.8.3`: `tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck credential-routing.ts` → **PASS**.

Blobs Git dos arquivos publicados idênticos aos testes executados localmente:

- `credential-routing.ts`: `c14a28d25a47a9b52f97f391fb19d0faaa6f8531`
- `credential-routing.test.ts`: `30722e314555be523b89205b5e8dee0776969371`

**Limites:** testes do módulo isolado, sem HTTP/Graph, sem valores de segredo, sem integração com Supabase e sem CI GitHub Actions; o arquivo `*.test.ts` foi executado, não submetido a typecheck integral com `@types/node`. Os testes WA-01/02/03 anteriores não foram reexecutados nesta entrega.

## 5. Gate

**GO** para evolução de código/testes sintéticos e revisão do contrato App↔canal pela S0. **NO-GO** para uso dos segredos reais, webhook Meta real, disparo, conexão com o Supabase hospedado, RLS/RPC privilegiada, migrações, merge, deploy, mudanças de números ou substituição da POC. PRs #1 e #2 Draft.
