# WA-02A/02B — reparos pós-auditoria | 18/10/2026

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Status:** código sintético reparado no PR #2, aguardando revisão cruzada; **sem integração/implantação**. Corrige o parecer de auditoria registrado no PR #2, comentário `6248555958`. A implementação permanece uma preparação **inerte** de mensagens; não prova autorização comercial nem faz chamadas Graph.

## Achados e medidas aplicadas

| Achado da auditoria | Correção aplicada | Prova de regressão |
| --- | --- | --- |
| HTTP `408` classificado como rejeição definitiva | `graph-outbound.ts`: `408` e `425` passam a `UNCERTAIN_EXTERNAL`, sem retry automático; `429`/5xx preservados | `WA-OUT-15` |
| Regex de `wamid` restritiva rejeitava padding `=` | Conserva prefixo `wamid.`, aceita alfanuméricos e caracteres seguros encontrados em formatos opacos (`+`, `/`, `=`, etc.), com limite; nunca transforma aceite em entrega | `WA-OUT-16` |
| Possível terminador de linha aceito devido à semântica de `$` em regex JS | Rejeita whitespace e controles explicitamente antes de validar a forma `wamid` | `WA-OUT-17`, incluindo LF/CR reais |
| Catálogo `APPROVED` não possuía escopo de App/loja/emissor | `graph-template.ts`: contexto confiável `TrustedTemplateScope` deve coincidir com escopo da intenção E do catálogo para concessionária, canal, App, WABA e Phone Number ID | `WA-TPL-19` |
| Contagens não comprovavam ausência de botões/mídia obrigatórios | Agora exige `schema_complete=true`, manifesto explícito de componentes; aceita apenas `HEADER/BODY/FOOTER` em texto, formato posicional, no máximo um de cada; recusa campos de catálogo inesperados e requisitos não suportados | `WA-TPL-20..23` |
| Texto Unicode malformado poderia ser serializado com substituição silenciosa | Recusa UTF-16 com surrogate isolado em parâmetros C06 | `WA-TPL-24` |

## Alteração de assinatura candidata [P]

`prepareGraphTemplateRequest(intent, trustedSnapshot, trustedScope, apiVersion)` **agora recebe quatro parâmetros**, incluindo `trustedScope` obtido de serviço interno autenticado, e requer `schema_complete` e `components` no `trustedSnapshot`. Não há invocadores operacionais a migrar neste PR. O contexto `trustedScope` **não é autenticado pelo módulo puro**: o contrato exige que o backend S0 o forneça após resolução do canal e que revalide opt-in/out, template, janela, estado/handoff e permissões na hora de transmitir. Forjar três objetos coincidentes em um teste **não** concede autorização de negócio.

O modelo de manifesto limita deliberadamente a superfície suportada; catálogo sem esquema completo ou contendo botões, mídia, parâmetros nomeados e formatos especiais é **incompatível**, sem geração parcial de payload. Templates com footer textual estático são compatíveis; não interpolamos o footer.

## Evidência real local e integridade GitHub

- Node.js `v22.16.0`: `node --experimental-strip-types --test graph-outbound.test.ts graph-template.test.ts` → **41/41 testes PASS**, incluindo 17 WA-OUT e 24 WA-TPL.
- TypeScript `v5.8.3`: `tsc --noEmit --strict --target es2022 --module nodenext --moduleResolution nodenext --allowImportingTsExtensions --skipLibCheck graph-outbound.ts graph-template.ts` → **PASS**.
- SHA de blob Git dos arquivos locais efetivamente executados/compilados, conferidos no GitHub:
  - `graph-outbound.ts`: `7870a499007ae2ff8c6a5558086554916b092aa7`.
  - `graph-outbound.test.ts`: `970adf27788819ae54aad77249ed689355e34862`.
  - `graph-template.ts`: `bcb0a1422f3526624cfbfac43bfb9ad79c496518`.
  - `graph-template.test.ts`: `3644a0d285ae6b6076101846d927333416dee72f`.
- **Limite da evidência:** não houve teste de rede Meta, Supabase hospedado, autorização C06 real, CI GitHub Actions ou typecheck completo dos arquivos de teste (o ambiente local não inclui `@types/node`). O resultado PASS não é homologação de produção.

## Gate para WA-02C e operação

Com os defeitos unitários corrigidos, **GO para preparar WA-02C com fake transport + fake backend e sem saída para rede**, em etapa específica. **NO-GO** para autorização ou envio reais: dependem da frente S0 e de DEC-WA-04 (ambiente), DEC-WA-06 (segredos, retenção, auditoria, continuidade), além da validação operacional dos canais/mandatos sob DEC-WA-05. O backend precisa entregar escopo autenticado, catálogo completo e atual, checagem final de elegibilidade, reserva de tentativa, persistência do resultado e reconciliação.

**Restrições respeitadas:** nenhum webhook existente substituído, nenhuma migration em Supabase remoto, nenhuma alteração de Meta/App/WABA/números comerciais concessionária de demonstração, nenhuma Graph API chamada, nenhum custo, merge ou deploy. PR #1 e PR #2 permanecem Draft.
