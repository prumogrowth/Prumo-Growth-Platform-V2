# OAI-OFF-02 — mapa estrutural de E02, não homologação

**Fonte:** `E02_CADERNO_70_ORACULOS_E_OBSERVAVEIS_v0_4.md` e `E02_AUDITORIA_QA_GABARITOS_70_v0_1.md`. Existem 70 SYN (65 P0/5 P1); **nenhum cenário E02 integral foi executado nesta missão**. `COVERED_STRUCTURAL_ONLY` significa apenas uma regressão parcial em `typed-boundary.test.mjs`, nunca PASS E02.

| SYN | Asserção OFF-02 / referência | Alcance | Situação E02 |
|---|---|---|---|
| 08–10 | revogação antes de stale, versões por domínio | estrutura | COVERED_STRUCTURAL_ONLY |
| 27–28 | chaves injetadas, ferramentas e autorizações proibidas | estrutura | COVERED_STRUCTURAL_ONLY |
| 29–30 | canários de segredo e payload minimizado | estrutura | COVERED_STRUCTURAL_ONLY |
| 31–32 | timeouts, falhas sanitizadas e ausência de integração real | estrutura | COVERED_STRUCTURAL_ONLY |
| 33–34 | histórico multi-casos por loja, cutoff | estrutura | COVERED_STRUCTURAL_ONLY |
| 39, 43 | essenciais/optionais e proposta F03 sem aplicação | estrutura | COVERED_STRUCTURAL_ONLY |
| 47–49 | solicitação S0 e templates elegíveis | estrutura | COVERED_STRUCTURAL_ONLY |
| 50–55 | simulação de prova Meta, 131049, sequência e janela | parte da S2 guard | BLOCKED_S0_META; COVERED_STRUCTURAL_ONLY na simulação |
| 57–60 | isolamento/instruções e fontes atuais/históricas | estrutura | COVERED_STRUCTURAL_ONLY |
| 69–70 | privacidade/esquema e fontes | estrutura | COVERED_STRUCTURAL_ONLY |
| Outros SYN | oráculos documentais mantidos | não abordado integralmente | NOT_EXECUTED_E02 |
| A38 (fora do lote E02) | histórico pinado `ebf6fe4e...` | não recuperado | BLOCKED_A38 |

O corpus original exige outras evidências de S0/Meta, semântica de modelo, histórico multimodal e/ou execução ponta a ponta. Mocks, assertions unitárias e hashes não satisfazem esse protocolo.
