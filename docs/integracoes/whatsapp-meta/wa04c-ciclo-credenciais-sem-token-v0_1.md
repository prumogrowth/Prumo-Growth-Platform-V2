# WA-04C — Ciclo de credenciais Meta sem token real (proposta offline)

**Data:** 18/10/2026. **Estado:** [P] candidato sintético no PR #2. O responsável informou que a liberação do token definitivo depende de **verificação por terceiro**. A integração continuará sem credenciais e **sem testes reais** até nova comunicação. Os testes abaixo são puramente locais, com nomes e dados fictícios.

## 1. Implementação

`integrations/whatsapp-meta/credential-lifecycle.ts` acrescenta a função pura `planMetaLifecycleTransition(registry, request)`:

- `REVOKE_APP`: produz um **novo registro candidato** com o App desativado e a revisão incrementada.
- `REVOKE_CHANNEL`: desativa **somente no registro candidato** o canal da loja correta, exigindo canal ativo, contexto exato e revisão atual.
- `STAGE_ROTATION`: prepara três **nomes novos e distintos** de referência dos segredos GET/POST/Graph, não os valores, e **desativa o App candidato**. **Não há caminho de reativação**: isso dependerá da verificação externa, desenho seguro da S0 e aprovação operacional posterior.

A função recusa loja errada, App ausente/inativo, versão antiga, vigência encerrada, slots malformados/reservados/reutilizados e alteração de outro canal. Nunca altera o objeto de entrada. As saídas contêm `proposal_only: true` e `production_authorized: false`.

**Atenção:** mesmo um resultado `ok: true` significa somente **consistência de uma proposta no laboratório**. Nem o registro de entrada nem quem pediu a transição são autenticados por este módulo puro. Ele **não grava revogações**, não lê Vault, não consulta Supabase, não renova segredo, não configura Graph, não recebe POST e não garante atomicidade em ambiente distribuído. Revogações operacionais, inclusive de emergência, exigem mecanismo privilegiado e independente desta simulação.

## 2. Evidência executada

- Node.js 22.16.0: **LIFE-01..13, 13/13 PASS** em `node --experimental-strip-types --test credential-lifecycle.test.ts`.
- TypeScript 5.8.3 `--noEmit --strict`: **PASS** do módulo e teste nesta sessão.
- Blobs conferidos contra os arquivos efetivamente executados: `credential-lifecycle.ts` = `14adeaebb778085d528cc182e923740ad1a6ebd0`; `credential-lifecycle.test.ts` = `c59b549e7d2e5ffe5f64f7caee3c5f25b8533a0e`.
- **Sem** CI remoto, Supabase hospedado, credenciais reais, callbacks da Meta ou envio WhatsApp. Os 13 testes são unitários sintéticos da etapa, não homologação integrada.

## 3. Bloqueios e continuidade

**[R] Dependência externa:** verificação por outra pessoa para liberar o token Meta definitivo. Não solicitar credenciais em texto, Issues, arquivos ou logs; não pressupor que o token já está no Supabase. A ausência do token não impede desenvolvimento documental, unitário e simulado.

**[R] Gates de arquitetura:** DEC-WA-04 ambiente definitivo; DEC-WA-06 segredos/rotação, retenção, recuperação, ACK; origem autenticada dos vínculos App/WABA/Phone/canal/loja pela S0; privilégio mínimo; autorização de negócio antes de qualquer transmissão; escopo e ocorrências C07.

**Próximo desenvolvimento independente:** exercitar, em fluxo sintético, o efeito das propostas de rotação e revogação sobre a WA-04B, sem implementar uma porta real de secrets. Nenhum merge, deploy, migration hospedada, troca do webhook da concessionária de demonstração ou recurso pago autorizado.

## 4. Mapa mental de acompanhamento

O `docs/MAPA_MENTAL.md` da branch `feat/s0-fundacao-prumo` será atualizado juntamente com incrementos relevantes, separando **[P] proposta implementada em Draft**, **[V] teste efetivamente executado**, **[R] dependência/gate** e **[D] decisão aprovada**. Esse compromisso vale quando estivermos realizando novas etapas; não representa monitoramento autônomo em segundo plano.
