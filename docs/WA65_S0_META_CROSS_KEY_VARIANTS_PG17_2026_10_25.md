# WA65 — Replays entre chaves, corpo com variantes e status independentes (PG17)

**25/10/2026 · Laboratório S0/Meta. Sem entrada pública, Graph API, S1 ou Supabase hospedado.**

## Identidade do evento e interpretação correta dos conflitos

O identificador de evento criado pela WA46 é SHA-256 do tuplo `[waba,phone,wamid,recipient,status,timestamp]`. Portanto:

- **Mesma identidade e mesmos bytes de corpo:** replay exato; resultado `LAB_EXACT_BODY_REPLAY`, nenhum novo registro original.
- **Mesma identidade, corpo bruto JSON semanticamente equivalente mas bytes reordenados:** `body_sha256` diferente com mesmo `event_ref`; o contrato de laboratório retorna `LAB_BODY_VARIANT_QUARANTINED` para a segunda observação. O registro original permanece imutável; futuras repetições de cada variante passam por replay exato.
- **Outro status ou timestamp:** outro `event_ref` por construção. Isso é um **novo evento**, não `LAB_KIND_CONFLICT_QUARANTINED` sob a rota raw WA46. Não se deve inventar conflito de `kind` entre identificadores diferentes. O contrato SQL possui tal rótulo para outros padrões de entrada, mas a rota WA46 estrita não fabrica evento com mesmo `event_ref` e status diferente.

## Provas efetivas

`supabase/tests/s0_wa_070_cross_key_variant_pg17.test.mjs` contém 24 verificações em dois vínculos S0 e outboxes sintéticas novas. O worker descartável WA60 passa a aceitar apenas dois perfis explícitos `wa65-a` e `wa65-b`.

**Intenção A:** criação de observação primária, segundo corpo sintético com ordem diferente de propriedades assinado por outra chave, replay dessa variante, novo status `read` como evento independente, negativa por HMAC incorreto, negativa por campo extra (contrato raw exato), cancelamento e observação tardia, replay sem duplicação após cancelamento, revogação individual de chave e negativa por segredo não correspondente ao identificador da chave.

**Intenção B:** cancelamento antes de dois envios com corpo idêntico em PIDs/chaves distintas. O lock do evento garante um `LAB_LATE_UNVERIFIED` e um `LAB_EXACT_BODY_REPLAY`, não dois registros. Outra variante de corpo recebe classificação própria; status `failed` e `read` são eventos diferentes. Revogar uma chave impede seus replays sem gastar nonce, preservando outra chave válida. Rotacionar permite observação tardia inédita e replay de corpo já registrado. Provas negativas não produzem recibos SQL.

**Auditoria final:** 9 observações sintéticas novas, originais e hashes preservados, 0 conflitos de tipo inventados, 0 registros shadow receipts, todos os indicadores comerciais falsos, caminho legado WA52 sem EXECUTE, contadores de nonce isolados por chave.

## Execução e certificação

Somente quatro arquivos de código de teste/CI e este documento são modificados, todos na branch S0. Sem migrações, alterações em S1/main, merge, envio WhatsApp ou direitos de acesso reais. A contagem confirmada pela WA64 é 727; a WA65 adiciona **24** provas candidatas, total **751/751** somente após CI **SUCCESS** no SHA final.

**Próxima candidata WA66:** variantes semânticas e canonização/normalização de payload sob concorrência em laboratório, incluindo limite de admissão e não reutilização de nonce.
