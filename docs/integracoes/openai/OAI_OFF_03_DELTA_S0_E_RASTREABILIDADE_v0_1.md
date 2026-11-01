# OAI-OFF-03 — Solicitação candidata de contratos à S0 e rastreabilidade E02

**Estado:** minuta técnica para a frente S0, **não enviada, não ratificada e sem autorização de alteração física**. A futura lista de comunicação entre frentes definirá o canal de conciliação. Não editar S0/S1/Meta/Frontend durante esta entrega.

## Contratos específicos que a S0 precisa emitir ou ratificar

| ID | Demanda delimitada | Consequência sem prova física |
|---|---|---|
| F03-S0-01 | Resolver pessoa por concessionária e números autorizados com prova anti-fusão; devolver `personId`/casos vinculados à mesma loja e revisão da identidade. | Bloquear associação histórica entre casos. |
| F03-S0-02 | Evento expresso de conclusão humana autenticada, `closureId`, cutoff imutável e sequência global por pessoa/loja **ou ordem equivalente explicitamente definida**; prova de cobertura de todos os casos elegíveis. | Bloquear alegação de histórico completo; não confundir watermark de caso único com multi-casos. |
| F03-S0-03 | Manifests de fontes versionados com vínculo `case,person,store`, direitos de leitura, descarte/indisponibilidade de mídia, auditoria, base legal/retenção e conteúdo minimizado autorizado a fornecedor. | Excluir fonte incerta e sinalizar lacuna, jamais inventar mídia. |
| F03-S0-04 | Catálogo tipado do formulário e identificação de campos essenciais/opcionais; versões de `case,cycle,form,catalog,assignment,identity,policy` sem equiparar uma à outra. | `STALE`/revisão; nenhuma atualização silenciosa. |
| F03-S0-05 | Correções explícitas verificáveis por S0, encadeamento de proveniência e resolução de conflitos **sem** adotar suposição de que “o mais recente vale”. | `REVIEW_REQUIRED` quando houver versões incompatíveis. |
| F03-S0-06 | Contrato de retorno: `requestId,closureId,cutoff,proposalRef`, revisão semântica dos valores e das fontes, revalidação de escopo/autoridade atual e aplicação atômica idempotente exclusivamente pela S0. | Nenhuma aplicação da ficha ou transição comercial. |
| F03-S0-07 | Falhas e concorrência: revogação antes de stale, E1/E2 independentes, mensagem após cutoff, repetição de solicitação e conflito entre execução e resposta tardia. | Bloquear efeito; retornar status sanitizado. |
| F03-S0-08 | Preservar os reparos de `expected_receipt`, cópia de payload e rechecagem pré-COMMIT dos módulos OPS-02; não importar cegamente ponte F03 anterior. | Proibir integração até conciliação com a S0 atual. |

**Referências fixadas:** S2 `1747cb0fee2a95322dc768044bafe9817d8cc540`; F03 `dc8554db2e625accbf95cf922fdff8446be56f00`; S0 OPS-02 `7d3232f59aab35265c3aa7fb5ab5ab2f06d5d047`; OFF-01 `394512327cd3756dfbe61ff970a6279c354b6565`. São referências documentais, não prova de homologação. Conferir versões mais recentes antes de qualquer integração.

## Matriz de testes adversariais offline (E02: somente correspondências parciais)

| Cobertura OFF-03 | Oráculos de referência | Evidência de laboratório |
|---|---|---|
| Identidade loja/pessoa, múltiplos casos, origem fora da cobertura | SYN-07, SYN-33, SYN-34, SYN-35, SYN-69 | Assertions sintéticas de scope, case-list e projeção. |
| Cutoff E1, evento tardio e retorno stale, sem contaminar história anterior | SYN-08, SYN-09, SYN-34, SYN-42 | Filtro por sequência e recheck de sete versões. |
| Essencial x opcional e fontes de campo explícitas | SYN-02, SYN-39, SYN-40 | Testes de missing, atribuição tipada e revisão. |
| Duas afirmações conflitantes e correção declarada | SYN-03, SYN-43, SYN-45 | Conflitos inferidos das claims sintéticas, não só da saída. |
| Desistência sugerida vs. ato comercial | SYN-46 e cenários correlatos | Advisory nunca gera `vendido`/remessa/mutação. |
| Recusa de schema, dados extraclasse, identidade, segredos, mídia ausente | SYN-27..30 e casos E02 correlatos | Inspeção da projeção e testes de propriedades extras. |

**Não marcar nenhum SYN como PASS por esta matriz.** Não foram executados os oráculos E02 originais com executor físico nem modelo. Revisar a numeração diante do caderno E02 v0.4 oficial na homologação. A38: fonte histórica exata `ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c` segue não recuperada e não é substituída.
