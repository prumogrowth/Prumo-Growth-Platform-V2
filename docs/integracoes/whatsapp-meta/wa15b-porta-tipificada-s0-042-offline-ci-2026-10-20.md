# WA-15B — Porta TypeScript tipificada para S0-042, sem I/O

> **[LEITURA_ORIENTADA_2026_10_21] Registro histórico ou de engenharia, não substitui decisões recentes.** Consulte [LEIA PRIMEIRO](./README.md), [especificação funcional vigente](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md) e [mapa de conflitos](./02-mapa-fontes-conflitos-e-emendas-2026-10-21.md). Somente trechos expressamente substituídos perdem vigência; provas offline não significam serviços reais homologados.

**Data:** 20/10/2026 UTC. **PR #2:** Draft. Proibido usar para produção, Graph ou ACK.

## Mudança

`integrations/whatsapp-meta/s0-technical-binding-contract.ts` expõe a função pura `prepareWa15FixtureCommand(reference,graphEvidence,action)`.

A função prepara **somente argumentos ordenados**, sem interpolação SQL, para funções privadas de fixture S0-042:
- `REGISTER_FIXTURE` → `prumo_private.registrar_vinculo_meta_tecnico_fixture_s0` com **dez parâmetros** (IDs numéricos App/WABA/phone, UUID canal e intenção, IDs de tentativa/correlação, destinatário, wamid, HTTP 2xx);
- `RECOVER_FIXTURE` → `prumo_private.consultar_vinculo_meta_tecnico_fixture_s0` com **nove parâmetros** (sem HTTP status).

Valida tipos e formas locais (UUID, IDs numéricos Meta, destinatário, evidência `API_ACCEPTED`, `wamid`) e rejeita getters/objetos com campos extras. Empacota snapshots congelados e não aceita nomes de função arbitrários. **Não executa a consulta nem autentica os valores fornecidos**: App/WABA/emissor, canal e intenção precisam continuar sendo revalidados pelo banco S0 contra cadastro privado e outbox em transação. Loja declarada pelo input sequer é enviada como parâmetro de SQL; a S0 deriva a loja autorizada.

As decisões da porta sempre incluem `ack_allowed:false`, `retry_external:false`, `production_authorized:false`. Nenhuma chamada HTTP ou banco, nem disparo Graph, segredo ou estado comercial.

## Evidência

[GitHub Actions Meta run 39399340849](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39399340849), commit de introdução da suíte `f002c5a8146e567ecb50da8d13b3ffe76990643c`:

- `integrations/whatsapp-meta/s0-technical-binding-contract.test.ts` **WA15B-01..12: 12/12 PASS**, contidos na regressão Meta integral `--all`.
- Log TAP: **479 testes, 479 PASS, 0 FAIL, 0 skipped** (467 legados + 12 novos).
- No mesmo workflow, a suíte WA-06D PostgreSQL 17 de 20 marcadores continuou aprovada.
- [S0 PostgreSQL run 39398947528](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39398947528): **WA15A 16/16 PASS**, WA14 18/18 PASS no banco descartável.

## Limites da integração

Os dois contratos foram validados **separadamente**, ainda não houve uma chamada **real** do TypeScript à função SQL em um mesmo processo/fixture e a porta não obtém a identidade confiável do backend. Faltam adaptar o executor interno autenticado, testar a transação cruzada Meta→S0, concorrência/commit desconhecido, HMAC/verificação de origem, preservação de callback posicional e ACK durável. Nenhuma mudança nas integrações bancárias, nos oito estados comerciais ou nas credenciais reais.
