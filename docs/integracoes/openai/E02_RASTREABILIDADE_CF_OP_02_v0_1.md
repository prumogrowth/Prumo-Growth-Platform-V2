# E02 — Rastreabilidade de regressão CF-OP-02 e CFI-01 | v0.1

Data: 18/10/2026. **Estado [P/R]: projeto de testes e vínculos entre frentes, NÃO suíte executada.** Sem custo, API real, alteração S0/Meta, fixture física ou homologação. Referências: [CF-OP-02 issue #6](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6), [PR #7](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/7), [CFI-01 issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4), OAI-08, OAI-05, OAI-07, E01/E02.

## 1. Famílias candidatas e ausência de execução

- **SYN-01..32 (32 descrições)**: E02_MATRIZ_CASOS_SINTETICOS_E_METRICAS_v0_1.md, segurança e comportamento da porta.
- **NC-01..17 (17 descrições)**: OAI-07, desfecho, campos, handoff e modalidade de voz.
- **OAI8-01..10 (10 descrições)**: OAI-08, planejamento pós-humano.
- **OAI-T01..27 (27 descrições)**: matriz-dependencias-e-testes-v0_1.md, corrigidos IDs duplicados com mapa de migração.
- **CF2-01..34 (34 descrições da coordenação)**: PR #7; muitos casos pertencem a S0, Meta, Frontend ou S1 e NÃO devem ser executados pela OpenAI.

Total meramente aritmético **120 referências**, com sobreposição e responsabilidades distintas. **NÃO são 120 testes físicos, 120 cenários únicos, aprovações nem testes passados.** Contagem de testes executados desta frente permanece 0; aceites dependem de fixture com gabarito e resultado.

## 2. Matriz interfrentes por requisito (E02/E04 candidato)

| Requisito | Referências propostas | Prova em laboratório OpenAI / stub S0 | Dono da homologação |
|---|---|---|---|
| Encerramento humano real e snapshot com corte | E01-T02, SYN-08/10, OAI-T16/22, CF2-07 | Evento autorizado único; retorno antigo descartado se nova mensagem | S0/Frontend [R] |
| Todos os campos elegíveis, essenciais vs opcionais | SYN-01..05, NC-03/04, OAI-T17/23 | Stub só aplica valor com fonte e código allowlisted; falta opcional não bloqueia | S0; catálogo Banco [R/V] |
| Desfecho sem falsa venda/recusa | NC-09/10/15/16/17, OAI8-10, OAI-T03/11 | NEGOTIATION_READY para remessa não é vendido; provas bancárias fora da IA | S0/Banco [R/V] |
| Contexto inconclusivo → recomendação de nova cadeia | OAI8-01, CF2-14..17 | F03 devolve advisory fundamentado; nenhum plano persistido/feito pelo modelo | S0 + OpenAI [R] |
| Pedido de cadeia por operador humano válido | OAI8-02, CF2-14..17 | Stub S0 autoriza e F02 escolhe apenas catálogo permitido | S0/S1 + OpenAI [R] |
| Template único ≠ cadeia F02; concorrência | CF2-11..13, OAI8-06 | Chamada única fora de F02; teste de não duplicação se disputa com plano | S0/Meta/Frontend [R/V] |
| Plano novo após handoff, plano antigo cancelado | OAI8-02/03, OAI-T05, CF2-18..20 | IDs de plano separados, sem ressuscitar C08/C10, nenhum envio pelo adaptador | S0 [R] |
| Limite 2–5 e final separado | OAI8-02/06, SYN-19/20 | Catálogo/intervalo/final validado no stub; modelo não impõe C09 | S0 + Meta [R/V] |
| Data futura explícita vs ambígua | OAI8-05, CF2-14..17 | Detectar compromisso somente com fonte; não inventar data/hora/timezone | OpenAI + S0 [R] |
| Roteamento após resposta | OAI8-03/04, CF2-18..20, OAI-T02/25 | Se houve handoff, retorno ao humano atual; caso IA só se nunca houve handoff | S0/S1 [R] |
| Os TRÊS relógios independentes | CF2-07..17, OAI8-02, NC-12 | Provar em S0 stub que Meta 24h do inbound não é C09 24h após final `sent`, nem conclusão humana | S0/Meta/Frontend [R/V] |
| C09 pós-humano limitado a status elegível | CF2-11..20, OAI8-10, NC-12 | Nunca perdido pelo modelo; stub só permite perda por silêncio pós-final comprovado em pré-banco elegível; matriz real [R] | S0, norma 26/C09 e Banco [R/V] |
| Opt-out, desistência explícita, falta essencial | SYN-13, SYN-20, OAI8-07, NC-04 | Não converter qualquer um em silêncio automaticamente; revisar elegibilidade | S0/Meta/LGPD [R/V] |
| Separação de concessionárias e revogação | SYN-06/07, OAI8-09, OAI-T01, CF2-01..06 | Nenhum dado B em A, e atribuição atual fornecida pelo S0 | S0/S1-002 [R] |
| Fallback/erros/áudio/modelo e gastos | SYN-21..32, OAI-T08/10/19/20/21/26/27 | Sem envio/custo real; erro seguro, sem segredo, nenhuma retomada IA | OpenAI/S0/Meta [R/V] |

A referência aos intervalos CF2 é indicativa (cobre mais de uma disciplina), não atesta que um teste externo esteja dentro da propriedade OpenAI. **Não contar teste externo como resultado desta frente**.

## 2A. Retorno pós-venda e fila protegida — casos adicionais de REVISÃO, sem execução

**Fontes:** doc.22 [D], doc.26 C02/C14 [P], evolução S1-002/I6–I8 na issue #6, e [adendo OAI-08](OAI_08_CONTRATO_PLANEJADORA_POS_HUMANA_CF_OP_02_v0_1.md). Estes são **cenários candidatos**, não novas transições nem fixture física.

| Candidato | Oráculo OpenAI / responsabilidade S0 | Estado |
|---|---|---|
| **PV-01** — inbound espontâneo de caso histórico `vendido` | Novo caso exclusivamente humano da mesma loja; nenhuma fala IA Vendedora nem alteração do `vendido` anterior. F03 apenas com fechamento válido do NOVO caso. | [D/P/R], NÃO EXECUTADO |
| **PV-02** — F03 avalia reclamação/suporte depois de venda anterior | Pode indicar `NOT_APPLICABLE`/revisão de finalidade (enum só lógico [P]); não preencher campos de remessa por analogia nem concluir nova venda. | [P/R], NÃO EXECUTADO |
| **PV-03** — F02 recebe retorno pós-venda sem ciclo comercial novo e elegível | Nenhum recontato comercial executável. Novo ciclo e elegibilidade futura pertencem ao S0; ausência de autorização é bloqueio, não convite à IA. | [R/V], NÃO EXECUTADO |
| **PV-04** — caso humanizado sem operador elegível entra em fila protegida | Resultado F03/F02 não cria atribuição ou outbound. S0/S1 deixam pendente, revalidam após atribuição legítima; nenhum fallback para Vendedora. | [P/R], NÃO EXECUTADO |
| **PV-05** — novo operador atribuído, resposta chega junto com proposta obsoleta | S0 descarta proposta desatualizada/revalida versão e autorização; resposta permanece com humano atual. | [P/R], NÃO EXECUTADO |

**Atenção:** fontes S1 relatam testes em SUA branch, mas **nenhuma validação OpenAI**. Estes 5 nomes `PV` não integram automaticamente os 32 SYN, 16 EX ou 34 CF2 e não são quantidades de testes executados.

## 3. Critérios de qualidade antes de converter em testes físicos

1. Escolher uma assinatura **canônica homologada** F03 entre S0/OpenAI, a partir da **proposta** CFI_01_PROPOSTA_CONCILIACAO_ENVELOPE_F03_v0_1.md; somente após aceite gerar fixtures de contrato como se fossem schema executável.
2. S0 ratificar elegibilidade por fase/status do C09 pós-humano; em especial `cadastro enviado ao operador` ainda indecidido. **Sem regra ratificada, testar apenas casos sintéticos com expected DENY para situações bloqueadas, sem inventar ALLOW.**
3. E02 submeter rubrica de falso preenchimento, privacidade, orçamento, áudio, templates e custo ao responsável/partes pertinentes antes do gate de testes.
4. E04 só pode declarar PASS/FAIL com `fixture_id`, `expected`, `actual`, versão, commit e log sanitizado. Enquanto não houver suíte executada, estado de cada caso é **PLANEJADO, NÃO EXECUTADO**.
5. Dependências Meta e S1 permanecem nos contratos proprietários; esta matriz não autoriza mexer neles.

**Detalhamento de SYN [P/R]:** a entrada e os resultados esperados para os 32 casos-base estão no `E02_GABARITO_DOCUMENTAL_SYN_01_32_v0_1.md`. Os nomes/criticidades originais permanecem os da matriz E02; o texto não é prova de execução nem contrato físico homologado.

## 3A. Exemplos EX-01..EX-16 [P/R]

O pacote [E02_PACOTE_REVISAO_CASOS_FICTICIOS_CFI_CF02_v0_1.md](E02_PACOTE_REVISAO_CASOS_FICTICIOS_CFI_CF02_v0_1.md) apresenta 16 entradas/expectativas de revisão: extração de campos opcionais e essenciais, bloqueio por evidência, handoff, modelo silencioso, F02 nova cadeia, opt-out, finalidade bancária e os três relógios. **Não são fixtures executáveis nem 16 testes PASS.** O resultado EX-16 está explicitamente bloqueado até matriz C09 S0 ratificada. A contagem das famílias anteriores não ganha nova prova por ter exemplos adicionais.

## 3B. Rubrica de aceite pré-E04 [P/R]

Ver [E02_RUBRICA_DE_ACEITE_PRE_E04_CF_OP_02_v0_1.md](E02_RUBRICA_DE_ACEITE_PRE_E04_CF_OP_02_v0_1.md) para critérios de bloqueio P0, resultados não mensurados, métricas/denominadores, campos com fontes, planos pós-humanos e cautelas C09. Rubrica ainda não aprovada e não constitui prova de teste.

## 4. Nota de precedência obrigatória

**[D-direção CF-OP-02]** A IA Planejadora pode sugerir plano pós-humano **NOVO** e limitado a templates aprovados, com retorno sempre ao humano autorizado do caso humanizado. O plano pré-handoff incompatível permanece cancelado. **S0 é quem decide criação e C09**, nunca a IA.

**[R]** C09 original do doc.26 ainda foi formulado para casos “sob IA”; extensão a caso humano elegível precisa de emenda/matriz por status aprovada pelo S0, preservando proibição de perda automática por silêncio em `cadastro enviado ao banco`, `vendido` e `perdido` histórico. Recusa definitiva bancária e venda não são inferidas de conversa ou timer. Os três relógios não se substituem.

**Status:** todos os cenários candidatos, nenhuma execução nesta entrega; controle geral do projeto não é atualizado por esse documento.
