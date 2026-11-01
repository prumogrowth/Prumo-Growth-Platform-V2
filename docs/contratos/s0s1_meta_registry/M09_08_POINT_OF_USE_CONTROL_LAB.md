# M09-08 — controle transacional de uso em PG17 descartável

**01/11/2026. Estado:** POINT_OF_USE_CONTROL_LAB_ONLY, sem concessão produtiva. Issue #8. Dependência PRE_DISPATCH real separada: #10.

## Base e escopo
Branch `exp/s0s1-m09-point-of-use-20261101`, base M09-07 `4f6355a9ce70af50adc6b4c7a235bd17966fe097`. Original S0 Meta Ingress PG17 pinado `01ffdb093013664b73b18d23f92aac2202578210`. Somente arquivos novos: SQL `pg17_use_check.sql`, porta `pg17_use_check.py`, testes `test_pg17_use_check.py`, workflow próprio e este relatório. Sem mudança em main, fonte S0 herdada, Meta, Supabase ou produção.

## O que foi executado
- Uma transação de laboratório bloqueia route→principal→binding→App→grant, valida loja, canal, WABA, número, tenant, prazo e cinco revisões antes de registrar `attempt_ref` de uso técnico. A PK impede gravação concorrente duplicada.
- O mutador M09-03 de revogação usa a mesma rota como primeiro lock. Se revogar primeiro, o novo check falha. Se gravar check primeiro, a revogação invalida rechecks seguintes. Registros históricos não são leases.
- A fonte antiga não tem unicidade global forte de WABA/phone; a porta recusa atribuições ambíguas observadas. Isto não substitui constraint global de origem em homologação.
- O instalador SQL exige PG17 e flags exclusivas de laboratório. Runtime não tem acesso ao jornal. Nada concede envios, ACK, Graph, vault, `PRE_DISPATCH`, consentimento, fonte Meta real ou ato comercial. As flags de autorização são sempre falsas.

## Evidências e contagem
- **18 novos casos físicos PG17**, incluindo idempotência, rollback, revogação concorrente, cinco versões, escopo cruzado, principal, ambiguidade e RLS.
- **16 regressões físicas M09-04** e **32 regressões sintéticas M09-01**. Total esperado na CI final: 66 casos distintos, não somar reexecuções.
- Uma CI preliminar executou a classe importada M09-04 duas vezes na etapa física; a importação foi corrigida para referência do módulo, mantendo teste M09-04 em etapa separada. O SHA final requer nova CI.
- Cleanup do banco descartável deve demonstrar catálogo original e repositórios pinados intactos. CI preliminar: https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41296636342 .

## Limites e fronteiras com outras frentes
- Meta #2 ainda exige contrato de ingresso físico POST/recibo, HTTP ACK, M2M/keys, readback/recovery e smoke E2E com Infra. Esta M09 não resolve ACK.
- Meta #8 ainda exige fonte hospedada/autenticada, prova de propriedade/delegação e aceite de projeção scoped; M16 amplia a dependência de templates/mídia.
- Meta #10 exige consentimento por finalidade, opt-out, versão/aprovação de template, campanha, reserva e `PRE_DISPATCH` atômico. Este check técnico **não** satisfaz #10.
- OpenAI #7 precisa pedido F02 autorizado, catálogo filtrado, aliases e retomada segura. M15 Meta é apenas preview offline.
- OpenAI #5/#6: F03 histórico multicases/cutoff e revalidação semântica antes da aplicação atômica pela S0.
- OpenAI #11/#12: F01 posse IA, handoff humano irreversível, fonte comercial vigente e recheck de publicação.
- OpenAI #13: resumos breves F01/F02/F03 na aba Resumo, demanda futura.
- Frontend #14: leitura ao abrir pelo Consultor titular, pendência de resposta, ordenação por timestamp confiável, escopo por loja; supervisão simples de Gestor não marca leitura do titular.
- OpenAI→Meta #9: WA39 e evidência outbound sent/falha precisam ratificação e verificação de origem pela S0.

Sem merge, deploy ou promoção operacional. Próximo passo: revisão Meta/Infra da interface e desenho separado dos gates PRE_DISPATCH e HTTP.
