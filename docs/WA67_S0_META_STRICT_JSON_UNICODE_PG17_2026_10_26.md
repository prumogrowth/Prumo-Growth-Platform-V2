# WA67 — Ambiguidade JSON / Unicode antes do arquivo forense

**26/10/2026 — candidato experimental S0/Meta, sujeito a aprovação de integração pela frente Codex/S0.**

## Questão identificada

Os adaptadores laboratoriais WA46/WA56 utilizavam `JSON.parse`, que aceita chaves repetidas no mesmo objeto e sobrescreve a primeira com a última, inclusive em colisões do tipo `"status"` versus `"st\\u0061tus"` depois da decodificação. Além disso, o parser JSON admite escapes de surrogate UTF-16 órfãos. Uma assinatura HMAC válida só prova integridade dos bytes recebidos; não elimina divergências de interpretação por parsers distintos.

## Proposta isolada (não incorporada ao núcleo oficial)

Novo módulo **`supabase/tests/s0_wa_072_strict_json_keys.mjs`**: após decodificação UTF-8 fatal e validação sintática por `JSON.parse`, percorre o JSON original, decodifica o valor de cada nome de propriedade (inclusive escapes Unicode), rejeita repetições **dentro do mesmo objeto**, rejeita surrogate órfão em nomes ou valores e BOM UTF-8 inicial. Cada objeto mantém `Set` local; nomes iguais em objetos diferentes são permitidos. Limites explícitos de 48 níveis, 2.048 nomes e 4.096 nós; resultado booleando, falha fechada. O módulo **não normaliza Unicode nem reserializa o payload** e não substitui `JSON.parse` como autoridade de sintaxe; não altera a definição WA46 de `event_ref` ou `body_sha256`.

Integração experimental restrita: `s0_wa_050_meta_raw_hmac_gate.mjs` chama a verificação na rotina interna `parseOneStatus` **após o HMAC** e antes da formação do ticket WA45; `s0_wa_060_meta_raw_to_pg17_bridge.mjs` revalida antes de interpretar `rawEvent`, para não depender apenas do guard anterior. Todas as alterações são laboratoriais na branch isolada e **não representam autorização para alterar a política canônica S0**.

## Testes e invariantes

A suíte `supabase/tests/s0_wa_073_json_ambiguity_pg17.test.mjs` implementa **24 provas**: aceitação de Unicode suplementar representado por par válido; rejeição de duplicate keys planas, aninhadas e com nomes escapados; rejeição de UTF-8 inválido, BOM e surrogate não pareado; dois tipos de chaves Unicode confundíveis; provas HTTP/PG17 de que entradas negadas não arquivam evidência nem consomem nonce; escape Unicode ASCII legítimo e reordenação de propriedades devem ser **aceitos** como variantes de corpo bruto sob a **mesma identidade de evento**; replay exato, cancelamento, revogação, rotação de chave e observação tardia preservam histórico e flags comerciais negativas.

## Contratos e dependências para Codex/S0

**Arquivos propostos:** `supabase/tests/s0_wa_072_strict_json_keys.mjs` (novo); `supabase/tests/s0_wa_050_meta_raw_hmac_gate.mjs`; `supabase/tests/s0_wa_060_meta_raw_to_pg17_bridge.mjs`; `supabase/tests/s0_wa_064_pg17_restart_worker.mjs` (perfil sintético `wa67-a`); `supabase/tests/s0_wa_073_json_ambiguity_pg17.test.mjs` (novo); `scripts/run-s0-local.sh`; `.github/workflows/wa39-s0-meta-offline.yml`; este documento.

**Dependências:** Node com `TextDecoder('utf-8',{fatal:true,ignoreBOM:true})`, assinaturas HMAC Meta laboratoriais, WA45 ticket, WA56 bridge e WA55 writer, 127.0.0.1 apenas, PostgreSQL 17 descartável, ACL/estado S0 preservados. A regressão histórica e CI no SHA exato são obrigatórios.

**Decisões de integração pendentes da frente Codex:** aprovar ou modificar (a) rejeição de nomes duplicados com escapes equivalentes; (b) rejeição de surrogate órfão e BOM; (c) limites de complexidade do scanner; (d) regras de equivalência/normalização Unicode; (e) posição e custo do parser em serviço autenticado real. Rejeição de assinaturas inválidas antes da verificação semântica continua. A integração deverá comparar política do parser com contratos e autenticação atuais do núcleo.

**Fronteira:** nenhum merge, cherry-pick, modificação de `main`, S0 oficial ou S1, Graph API, webhook público, entrega Meta, IAM real ou Supabase hospedado. PR #2 permanece **Draft**; apenas esta branch experimental pode receber a proposta. WA39–66 certificados: 775/775. **WA67 +24** poderá ser contabilizada como **799/799** somente após aprovação do workflow no SHA final.

**Próxima proposta possível:** WA68 — auditoria de custo/admissão de variantes JSON dentro do teto de bytes, rejeição por orçamento de CPU e comportamento sob concorrência, sujeita às decisões de contrato do Codex.
