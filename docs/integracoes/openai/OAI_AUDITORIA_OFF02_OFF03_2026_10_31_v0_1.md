# Auditoria independente de qualidade — OFF-02 e OFF-03

**Data:** 31/10/2026. **Resultado:** REPAROS LOCAIS APLICADOS; PROMOÇÃO/ACEITE GERAL PENDENTES. **Escopo:** revisão de código, testes e documentos dos pacotes OFF-02/OFF-03; NÃO avaliação da integração física S0, nem E02 integral.

## Bases examinadas

- `OAI_OFF_02_codigo_e_documentacao.zip` (6 arquivos), `OAI_OFF_03_codigo_testes_documentacao.zip` (6 arquivos) e `OAI_OFF_02_03_pacote_cumulativo_sobre_OFF01.zip` (12 arquivos): arquivos correspondentes conferidos **byte a byte**, sem divergências entre os dois pacotes individuais e o cumulativo.
- OFF-01 repositório e S2 informados nos relatórios, **não presentes** no pacote. A reprodução direta de `node --test tests/*.test.mjs` no ZIP isolado resulta em `ERR_MODULE_NOT_FOUND` para `core.mjs`/`f03-commit-gate.mjs`. Isso é compatível com o caráter incremental do patch, mas não fornece prova de regressão integral.
- Código novo: `typed-boundary.mjs`, `s2-guard-links.mjs`, `f03-history-boundary.mjs`, suites correspondentes e contratos/documentos.

## Achados confirmados em execução adversarial ANTES dos reparos

| ID | Gravidade | Achado / prova | Remediação local |
|---|---|---|---|
| AUD-01 | Alta | OFF-03 aceitava um `sourceAliases` de campo contendo **uma fonte correta e outra sem suporte**; retornava `PROPOSED` e incluía o registro inválido como proveniência. | Agora **todas** as fontes citadas devem atestar o mesmo código/valor. Novo teste AUD-F03-01. |
| AUD-02 | Alta | OFF-03 emitia `commercialAdvisory:{kind:'perdido'}` mesmo quando a suposta desistência era de uma fala **da IA**, ou quando a manifestação `true` havia sido **corrigida explicitamente para false**. Era somente sugestão para revisão, sem mutação, mas contaminava a decisão humana. | Exige declaração terminal e explícita `customer_withdrawal:true` oriunda do **cliente**, não corrigida nem contraditória. Retorno negativo `SOURCE_INVALID` sem candidato. AUD-F03-02/03. |
| AUD-03 | Média | `validatePrivateEnvelope` OFF-02 consultava `envelope.scope` antes de verificar descriptors: getter não confiável foi executado **quatro vezes** em entrada rejeitada. | Inspeção de descriptors e autorização antes de leitura; `safeTree` precede estrutura da entrada. AUD-F02-01. |
| AUD-04 | Média | `safeAuditEvent({status:'APPLIED'},'F03')` incluía `APPLIED` em log sanitizado, embora OpenAI não possa atestar aplicação. | Allowlist de códigos conhecidos; status não reconhecido vira `MODEL_FAILURE`. AUD-F02-02. |
| AUD-05 | Média | OFF-03 não exigia **identificador de correlação no output do fornecedor**, tornando propostas com aliases semelhantes associáveis ao contexto errado. | Novo `providerTag` opaco exigido e comparado; presente na projeção e no output. Schema OFF-03 revisto para `0.2-candidate`. AUD-F03-04. |
| AUD-06 | Baixa | Relatório OFF-02 contém a frase contraditória "403 esperados" seguida de "399 é projeção"; relatório OFF-03 ainda diz 92 em um trecho, quando seu total efetivo anunciado é 95. | Esta auditoria prevalece como errata quantitativa; documentos anteriores são registros históricos e não foram reescritos. |

## Reparos, escopo e resultados verificáveis

Reparos somente nos **dois módulos próprios e duas suites de teste**: `e04_offline_lab/typed-boundary.mjs`, `e04_offline_lab/f03-history-boundary.mjs`, `tests/typed-boundary.test.mjs`, `tests/f03-history-boundary.test.mjs`; adicionado este relatório e adendo do contrato OFF-03 v0.2. Nenhum módulo S2/OFF-01 ou outra frente foi alterado.

- Reprodução pré-reparo: OFF-03 **95/95** em ambiente isolado usando uma cópia **idêntica do parser `parseStrictJSON`**, extraída de OFF-02; original OFF-03 inalterado exceto caminho local do import. Os 3 testes adversariais provaram aceitação indevida de proveniência e aconselhamentos. OFF-02 getters e log testados com `core.mjs` **stub de auditoria somente** para permitir o carregamento do módulo, sem reivindicar testes herdados.
- Reprodução após reparo: OFF-03 **99/99 PASS** com o mesmo parser isolado. Verificações adicionais OFF-02 focadas em getter/log/parser **3/3 PASS**, mas **NÃO** equivalem à suíte OFF-02 integral.
- `node --check`: sintaxe de todos os módulos e suites do patch corrigido, aprovada; inspeção estática dos novos módulos sem chamadas externas, SQL, Graph, cliente OpenAI, rede ou escrita.
- Contagens históricas fornecidas: OFF-02 **61** e OFF-03 **95**, reportadas nas execuções anteriores (não verificadas aqui em ambiente S2 completo). Após anexar 2 testes OFF-02 e 4 OFF-03, **63 + 99 = 162 testes novos esperados**, **NÃO integralmente executados em conjunto**. Se os **342** testes herdados continuarem, a expectativa matemática é **504**, não um resultado comprovado.

## Pendências internas ainda obrigatórias (NÃO são integração S0)

1. **P0 de aceitação:** executar o `npm test` completo no checkout base exato OFF-01 com os 342 casos herdados e os 162 casos dos novos módulos. Capturar saídas, versão de Node/npm, SHA/árvore e divergências; reparar regressões caso existam. Sem esta reprodução, não declarar OFF-02/03 aprovadas integralmente.
2. **P1 de distribuição:** criar branch própria na origem Git oficial, publicar os arquivos e auditar diff contra `394512327cd3756dfbe61ff970a6279c354b6565` sem merge/deploy. Verificar que não foram sobrescritos arquivos de outras frentes.
3. **P1 de contrato:** ratificar **dentro da frente OpenAI** a adoção do novo schema F03 v0.2 antes de usar consumidores OFF-03; `providerTag` é correlação sintética, **não** prova de autorização/antirreplay durável. Manter contratos v0.1 como históricos.
4. **P1 de validação:** executar testes de substituição de resultado entre duas requisições e teste de fontes corrigidas/advisory; registrar testes adversariais como cobertura estrutural, sem `PASS` E02.
5. **P2 documental:** ao publicar entrega oficial, emitir relatório novo com números reais em vez de replicar os dois erros aritméticos históricos.

## Fronteiras preservadas

A38 segue bloqueada; SYN-01..70 não foram homologados. Sem cliente OpenAI real, autorização de dados pessoais/financeiros, uso Meta, mutações S0, atendimento, atualização de ficha, deploy ou contas pagas. Necessidades de contrato físico da S0 não foram consideradas defeitos internos desta auditoria.

**Decisão:** suspender o aceite definitivo de OFF-02/OFF-03 e o início de OFF-04 **até executar regressão oficial completa**, embora as falhas de lógica descobertas tenham sido reparadas no pacote candidato local.
