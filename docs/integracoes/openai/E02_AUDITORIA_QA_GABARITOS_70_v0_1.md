# E02-QA v0.1 — Auditoria de consistência dos 70 cenários documentais

**Data:** 22/10/2026. **Abrangência:** [E02-MT v0.3](./E02_MATRIZ_REGRESSAO_OPERACIONAL_v0_3.md), [70 oráculos v0.4](./E02_CADERNO_70_ORACULOS_E_OBSERVAVEIS_v0_4.md), [caderno de dez exemplos](./E02_CADERNO_FIXTURES_DOCUMENTAIS_v0_3.md), [contrato E01-INT v0.4](./E01_CONTRATO_TIPADO_ADAPTADOR_FALHAS_v0_4.md), AL-IA-01/02/03, CFI-01/CF-OP-02 e pacotes E02-REV. **Revisão editorial do corpus**, não inspeção de código executável, parecer jurídico, homologação interfrentes ou teste de modelo.

## 1. Resultado quantitativo verificável desta auditoria documental

| Família de teste | Casos SYN | P0 | P1 |
|---|---:|---:|---:|
| F03: extração, histórico, fila, estados e identidade | 31 | 31 | 0 |
| F01: handoff e informação comercial | 2 | 2 | 0 |
| F02/Meta: templates, cadeias e relógios | 12 | 11 | 1 |
| Voz auxiliar (STT/TTS) | 6 | 4 | 2 |
| Protocolo: injeção, schema, segredos, retries e privacidade | 6 | 5 | 1 |
| Conhecimento, bases e configuração global | 9 | 8 | 1 |
| MCP Diretor | 4 | 4 | 0 |
| **TOTAL** | **70** | **65** | **5** |

Contagem obtida dos 70 cabeçalhos SYN-01..SYN-70: sequenciais, sem duplicação. **70 EXPECTED documentais, 0 ACTUAL medidos, 0 PASS/FAIL executados.** NC, CF2, OAI8 e OAI-T históricos possuem interseções; não adicioná-los à contagem de casos únicos sem deduplicação.

## 2. Achados com correção aplicada aos oráculos v0.4

| ID de auditoria | Problema verificado | Correção textual feita | Situação |
|---|---|---|---|
| **QA-01** | SYN-02 anterior enfatizava ausência opcional, mas deixava sem teste explícito a proibição de inventar o campo e o retorno humano quando **essencial**. | Agora compara variantes ESSENCIAL/OPCIONAL com fonte e autorização de catálogo S0, sem inferência. | **CORRIGIDO NO GABARITO [P]** |
| **QA-02** | SYN-03 anterior permitia leitura ambígua de dois valores exclusivos sem distinguir conflito real de retificação. | Duas exclusividades não resolvidas ⇒ conflito com ambas as fontes; retificação explícita ⇒ candidato atual com trilha histórica; sem elevação silenciosa. | **CORRIGIDO NO GABARITO [P]** |
| **QA-03** | SYN-08 dizia, de modo absoluto, que somente mudança de versão justificava revalidação negativa; não separava perda de direito/concorrência. | Três variantes: inbound posterior sem perda presumida de aplicabilidade, mudança de versão e revogação. Cutoff E1 persiste; **negação de autorização não expõe STALE**. | **CORRIGIDO NO GABARITO [P]** |
| **QA-04** | SYN-09 preservava no GIVEN hipótese antiga de edição permitida pelo Consultor, embora o THEN a negasse. | Estímulos distintos: F03-B legitimamente aplicada pela S0 altera v4→v5; tentativa direta do Consultor é bloqueada. F03-A não substitui v5. | **CORRIGIDO NO GABARITO [P]** |
| **QA-05** | SYN-27 e SYN-28 foram indevidamente classificados apenas como F01 na primeira geração do caderno v0.4. | Família **PROTOCOLO**; injeção e schema/refusal devem cobrir mais de uma função, sem ampliar autoridade do modelo. | **CORRIGIDO NO GABARITO [P]** |
| **QA-06** | SYN-29..32 tinham WHEN genérico sobre carregar base/conhecimento mesmo quando objetivo era segredo/timeout/n8n/privacidade. | WHEN e GIVEN ajustados à borda de transporte, observabilidade, erro e minimização de cada cenário. | **CORRIGIDO NO GABARITO [P]** |
| **QA-07** | SYN-31 poderia parecer obrigação de adotar/testar n8n e obter latências mesmo que arquitetura descartasse essa rota. | Comparação **condicional** à escolha/autorizaçāo futura; do contrário, `NÃO_APLICÁVEL/JUSTIFICADO`, jamais `PASS`. | **CORRIGIDO NO GABARITO [P]** |

**A correção documental não marca um cenário como aprovado/testado** e não altera o gabarito histórico v0.1 nem suas fontes. Para interpretar diferenças, usar os oráculos revisados desta branch; a política final permanece sujeita à ratificação S0/Meta/Prumo quando física.

## 3. Achados ainda abertos — bloqueiam promoção técnica

| ID | Tipo de lacuna | Necessário para fechar | Dono |
|---|---|---|---|
| **QA-08** | Gabaritos ainda não são fixtures serializadas no esquema físico: a redação de EXPECTED não é assertion programável. | Aprovar entrada/saída/evento/versões, construir massa fictícia com fontes/cutoff, assertion positiva+negativa, resultado ACTUAL e hash do lote. Somente quando E04 autorizado. | S0/OpenAI, donos por operação |
| **QA-09** | A maior parte dos cenários P0 da F03 requer manifesto multi-casos, identidade, catálogo e prova de mídia ainda não emitidos pelo recibo S0. | Ratificar [CFI-01 v0.3](./CFI_01_CONCILIACAO_PONTE_F03_INTERFRENTES_v0_3.md), [manifesto candidato](./CFI_01_MANIFESTO_HISTORICO_F03_CANDIDATO_v0_1.md) e campos distintos de `expected_cycle_version`. | S0/S1/FV/OpenAI/privacidade/Meta |
| **QA-10** | C09/post-humano carece de matriz de estado+fase e prova `sent` final e `definitive_failed` realmente ratificada. | Decisões F02C-R01..R07 e evidências [CF-OP-02 v0.3](./CF_OP_02_C09_CONCILIACAO_F02_INTERFRENTES_v0_3.md). | S0/Meta/S1 |
| **QA-11** | Bases/fatos, ferramentas MCP e controle de confirmação/auditoria precisam de ACL/catálogo físico e retenção. | Validar E01-KH v0.3 com S0/Prumo/privacidade; nenhuma alteração SQL/tool criada por texto. | S0/Prumo/MCP/segurança |
| **QA-12** | Falta autorização **expressa** para E04; E05 requer outra autorização de chave/billing/valor. | Cumprir G-FASE-DO-PROJETO após E02-REV; custo e acesso dependem de gate independente. | Responsável do projeto |

**Registro interfrentes:** questões encaminhadas à [issue #4](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/4#issuecomment-6352881916), [#6](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/6#issuecomment-6352882384) e [#15](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/15#issuecomment-6352882892). Até a leitura desta revisão, não havia nova ratificação. Os comentários são solicitações, **não** resposta dos owners.

## 4. Critérios para considerar a QA fechada

- **QA editorial desta revisão:** continuidade de SYN-01..70 conferida; negativas documentais e erros QA-01..07 corrigidos no caderno de oráculos. O status pode ser **REVISÃO EDITORIAL INTERNA CONCLUÍDA** apenas para esta rodada.
- **E02-REV:** **NÃO CONCLUÍDA**; QA-08..11 e decisões CFI/CF-OP continuam abertas. Não chamar isso de "contrato homologado".
- **E02-FIX:** **NÃO CONCLUÍDA**; nenhum dos 70 casos é fixture física executável/assinada, apesar do detalhamento narrativo.
- **E04:** **NÃO AUTORIZADA/INICIADA**; documentação não revoga gate.
- **E05 e fases seguintes:** **NÃO AUTORIZADAS/INICIADAS**; nenhuma credencial, consumo, mídia real ou deploy.

**Próxima ação que NÃO depende de inventar decisões:** obter respostas de S0/S1/FV/Meta/Prumo aos sete itens [E02-REV v0.4](./E02_RESUMO_DECISOES_PARA_RATIFICACAO_v0_4.md); somente então consolidar a assinatura física canônica e preparar a execução permitida. No intervalo, evitar criar versões paralelas especulativas do mesmo schema.
