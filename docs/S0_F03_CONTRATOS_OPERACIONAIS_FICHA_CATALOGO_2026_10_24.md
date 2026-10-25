# E04/S0-F03 — contratos operacionais de ficha e catálogo (apenas simulação)

**Escopo:** branch `feat/oai-s0-f03-history-port-20261023`, PR #1 Draft, base S0. Sem E05, Meta/OpenAI real, produção, deploy ou escrita cadastral.

## Fontes consultadas

O laboratório já possui as fontes S0 `cfi01_f03_form_fields_local`, `cfi01_f03_catalog_entries_local` e os cinco vetores `VersionVector(form,catalog,case,assignment,identity)`. A reserva `cfi01_f03_reservations_local` é append-only e consultiva. **Ainda não existe integração homologada de ficha e catálogo operacionais reais.**

## Incremento

- Nova fixture S0 `s0_f03_operational_contracts_local_only.sql`: registro *metadados de campos sintéticos* por concessionária (chave, tipo `TEXT_ONLY` ou `CATALOG_CODE`, comprimento máximo, ativação). Definições não podem trocar silenciosamente a chave nem o tipo; cada mutação efetiva incrementa `versao_catalogo`, invalidando reservas antigas.
- `S0F03LocalOperationalContractsStore`: valida SOMENTE proposta sintética já reservada (digest SHA-256 canônico do conjunto de campos, idempotência, cinco versões, prova HMAC persistida, recibo de encerramento, atribuição ativa, pendência S0, catálogo por loja e status ativo). Recusa nome duplicado, campo não cadastrado, tipo divergente, catálogo inativo/ausente e estado desatualizado.
- `S0F03LocalOperationalContractsBridge`: exige verificação autorizada e viva do conteúdo S0 **antes e depois** da conferência. Estado positivo é unicamente `CONTRACT_REVIEW_ONLY` sem dados ou autorização para F03.
- Nenhuma ficha é editada; não inventa campos reais, números de telefone, operações comerciais, contratos bancários ou novo modelo de produto.

**Segurança e limite:** o digest não equivale a aprovação humana; verificações são transitórias e não blindam edições futuras. O próximo passo é modelar o compromisso transacional final campo a campo sob autoridade autenticada S0, com aprovação humana explícita e sem promover HOLD automaticamente.

**Validação:** os testes PG17 desta rodada serão contabilizados somente após verificar logs de um workflow do commit correspondente.

## Certificação física executada

**GitHub Actions SUCCESS:** https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40145676674

**HEAD de código testado:** `359a4a956fde57c475f86e0140987d304bcb4fe6`; banco PostgreSQL 17 em container descartável.

- 84/84 testes S0 CFI-01 aprovados;
- 267/267 testes F03 aprovados, incluindo 171 físicos PostgreSQL;
- **351/351 no total**, incremento de 20 testes em relação aos 331 certificados anteriormente;
- Cenários físicos 160–171 e 8 novos testes unitários do contrato de campos aprovados;
- Foram testados campo permitido, item ativo, campo desconhecido, tipo e comprimento divergentes, produto ausente/inativo, mudança de versão do catálogo e da ficha, pendência de identidade, reidentificação de contrato proibida, isolamento ACL, digest, autenticação dupla e revogação.

Este registro posterior é somente documental; não altera a execução certificada.
