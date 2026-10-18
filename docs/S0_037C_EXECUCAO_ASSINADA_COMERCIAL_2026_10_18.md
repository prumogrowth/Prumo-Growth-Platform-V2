# S0-037C — autorização assinada e transação C08/C07 (ensaio PG17, sem novos owners)

**Data:** 18/10/2026. PR #1, branch `feat/s0-fundacao-prumo`. **Status final: regressão sintética aprovada em PostgreSQL 17**. S0-037A comprovou que alterar owner comercial isoladamente falha; S0-037B comprovou DML sob RLS literal em lojas fictícias, mas **sem autenticação nem HMAC**. Esta etapa fecha esse hiato apenas como **regressão da cadeia assinada existente**, não como solução de privilégio mínimo integral.

## Objetivo

Com fixtures descartáveis e assinatura HMAC produzida apenas pela sessão de teste privilegiada, verificar operações comerciais reais **do simulador S0** atravessando:

`prumo_s0_gateway (NOLOGIN; apenas 2 EXECUTEs)` → `gateway_*_assinado_s0 (owner prumo_s0_signed_executor)` → `gateway_validar_prova_s0 (owner prumo_s0_signer; HMAC + nonce único)` → `gateway_*_s0 (SECURITY DEFINER postgres; auth.sessions FOR KEY SHARE)` → `cancelar_plano_gestor_sintetico / conciliar_pendencia_c07_sintetica (SECURITY INVOKER postgres)` → `auditoria_gateway_s0`.

É a arquitetura **atual**, ainda dependente de `postgres` para as duas wrappers comerciais. Esse encadeamento não representa nova concessão e não elimina `SECURITY DEFINER postgres`.

## Evidência executável S0-037C

`supabase/tests/s0_037c_execucao_assinada_c07_c08.sql`, incluído no runner PostgreSQL descartável `scripts/run-s0-local.sh`, usa `BEGIN;...ROLLBACK;` e verifica:

- **OWNER37C-01:** nenhuma leitura direta de `auth.sessions`, DML comercial ou auditoria privada pelo gateway; HMAC falsificado falha com `PROVA_INVALIDA`.
- **OWNER37C-02:** gestor A com sessão fictícia ativa e assinatura correta cancela C08 de A; nonce reutilizado é rejeitado; novo nonce sobre os mesmos parâmetros resulta em `ALREADY_APPLIED` sem nova transição.
- **OWNER37C-03:** duas decisões humanas C07, `ENCERRAR_SEM_PROVA` e `VINCULAR_SINTETICAMENTE`, aplicadas apenas a pendências e envio fictícios da loja A; A não consegue conciliar pendência da loja B, mesmo com HMAC formalmente válido para a tentativa — `FORBIDDEN_SCOPE`.
- **OWNER37C-04:** contagem íntegra de quatro aplicações/provas HMAC aceitas, incluindo replay idempotente com novo nonce; evento de envio cancelado, vínculo C07, duas auditorias de reconciliação, duas lojas independentes, nenhum avanço dos oito estados comerciais.
- **OWNER37C-05:** após revogar a sessão GoTrue **fictícia** A, uma assinatura nova e válida falha com `SESSAO_INATIVA`; nonce, auditoria e comércio permanecem inalterados.

A fixture cria `auth.sessions` somente se ausente no **PG17 descartável**; nunca executá-la no Supabase hospedado ou como migration. Chave HMAC de teste literal injetada sob `BEGIN/ROLLBACK`, nunca real. Nenhum envio, callback Meta, autorização bancária, dado de cliente ou configuração de produção. Sinais simulados de status não promovem `vendido`.

## O que continua **NÃO comprovado**

Esta prova de execução assinada **não** substitui a S0-037B: o algoritmo continua dependendo do proprietário comercial `postgres` e de acesso privilegiado a `auth.sessions`. **Não há prova de owner rebaixado concluindo operações C08/C07 sob RLS**; não se deve trocar proprietários, permitir DML direto, criar worker com senha ou liberar uma API pública. A concorrência e o isolamento são cobertos por regressões prévias, não por novas corridas deste arquivo. Também não há testes de `VINCULAR` com integração Meta nem deduplicação real de `statuses[].id`.

Futuros gates: projeto de sessão com leitura mínima e revogação/lock, autorização resistente a GUC controlada pelo cliente, domínio sem guard `current_user='postgres'` mas não público, gravação de auditoria sem privilégios excessivos, políticas RLS por escopo autenticado e testes no GoTrue/PostgREST **local** após qualquer alteração persistente.

## Coordenação documental

- `docs/MAPA_MENTAL.md` deve refletir a evolução S0-028..037C, os contratos e os **gates [D]/[P]**; o n8n é opcional e fica fora do caminho crítico Meta→Supabase, como decisão arquitetural aprovada.
- DEC-WA-01/02/03 aprovadas, DEC-WA-05 titularidade Meta por concessionária; DEC-WA-04/06 pendentes.
- PR #1 e #2 Draft sem merge. Não executar migrations no Supabase hospedado, deploy, Meta Graph, operaçãa instituição financeira ou tráfego real.

## Aceite efetivo — 18/10/2026

[**PostgreSQL 17 #39127146330 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39127146330), código testado `219240503ea966e7a392aef6d2342872bb6929bb`. Logs: `OWNER37C-01..05 PASS`, regressões SQL e concorrência anteriores e **24 testes Python OK**.

Histórico transparente de três falhas de **fixture/teste**, corrigidas sem alterar funções comerciais, owners, ACL permanentes ou migrations: [#39126937486](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39126937486) (GUC com segmento numérico inválido); [#39127006581](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39127006581) (`id` ambíguo nas três consultas de pendência); [#39127073850](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39127073850) (introspecção de `auth.sessions` por papel sem USAGE do esquema substituída por SELECT real negado). O último CI comprovou o caminho completo.

**Limite do aceite:** a cadeia atual assinada C08/C07 funciona nos cenários sintéticos, **mas ainda chama wrappers comerciais `SECURITY DEFINER postgres`**. Não comprova nem autoriza redução efetiva dos seus owners, migração hospedada, operação Meta, serviço real ou produção. A última rodada Auth/REST local acumulada continua [#39122948236 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122948236), não repetida sem alteração de runtime.
