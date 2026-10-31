# Auditoria M12 — anteparo de ingresso físico (31/10/2026)

**Parecer:** conforme para prosseguir em laboratório offline com ressalvas; **M12 operacional aberta**. Nenhum endpoint, persistência S0, readback autenticado ou ACK HTTP foi implementado.

## Escopo e evidência
- Branch Meta isolada: `feat/meta-s0-physical-interop-ack-guard-20261031`.
- Commit funcional auditado: `6fe99cfeacdc7894002b0f89cc6cd7da403cbca9`.
- [CI 41246615004](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41246615004): **1.385/1.385 testes offline**, zero falhas e skips; **18 verificações físicas PG17/Meta**, dois jobs aprovados. Scanner ACK lexical aprovado, não prova formal de ausência de ACK.
- Fonte S0 PG17 somente leitura pinada em `01ffdb093013664b73b18d23f92aac2202578210`.
- Reutilizados: `wa11-offline-webhook-envelope.ts`, `s0-handoff-contract.ts`, `cloud-batch-scope-preflight.ts`; M12 não chama S0 real.

## Achado AUD-M12-01 e correção

A M12 anterior confrontava entre WA11, handoff e verificação final **apenas** `event_count` e `scope_count`. Em caso de mudança da vinculação `canal_id` ou `concessionaria_id` **depois da primeira validação WA11**, as contagens de eventos/canais poderiam permanecer idênticas; a primeira identidade de escopo seria descartada, e o resultado de laboratório poderia ser classificado como coerente sem detectar o desacordo.

**Correção:** WA11 calcula `channel_distribution_sha256` a partir de tuplas ordenadas de App/concessionária/canal/WABA/número e contagens inbound/status, com digest para escopo técnico apenas (não é assinatura da S0 nem grant). A M12 reconstrói e compara essa impressão digital com a distribuição do candidato de handoff e com o último preflight HMAC. Qualquer divergência recusa o lote inteiro como `SCOPE_CHANGED`, sem saída parcial.

**Novas regressões:** `AUD-M11-45/46` e `AUD-M12-36/37/38/39`. Total atual: **50 testes M11** e **39 testes M12**, subconjuntos dos 1.385 totais. Testam mudança de vínculo após WA11, reassociação de concessionária, vínculo estável e mudança temporária entre passos. A saída permanece minimizada, sem identificadores de clientes ou segredos.

## Riscos externos e limites

- [ ] As verificações são sequenciais e alimentadas por `TrustedRoutingPorts` de laboratório. Uma mudança entre o último snapshot e a futura gravação, ou uma sequência ABA entre duas leituras, exige **recheck transacional na S0**; digest SHA-256 de dados alegados não cria autenticidade da origem.
- [ ] M2M, chave pública Ed25519 sob custódia independente, source of truth S0 de App/grant/revisão, mapping `tenant` para `concessionaria_id` e projecção por finalidade não estão implementados na Meta. Dependência [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8) com S0 `EM_IMPLEMENTACAO` em laboratório, ainda sem aceite.
- [ ] Uma unidade física POST indivisível, transação SQL, readback/recuperação `COMMIT_UNKNOWN`, HA, idempotência real, HTTP GET/POST, ACK/retry e redelivery precisam de ratificação e testes reais da S0/Infra na [#2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2).
- [ ] PR real/merge, binário final, deploy e homologação externa não verificados. Nenhuma autorização de Graph, envio, alteração comercial ou ACK decorre deste trabalho.

**Estado:** avanço técnico offline aprovado; M12-D, M11-D, M10-D, M09-D, M08-D e M07-D continuam pendentes. Próxima evolução deve preservar a separação das frentes e não antecipar efeito externo.
