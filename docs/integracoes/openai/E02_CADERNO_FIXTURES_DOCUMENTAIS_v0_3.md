# E02-FIX v0.3 — Caderno de fixtures documentais E02, sem execução

> **Ampliação documental:** [70 oráculos E02-FIX v0.4](./E02_CADERNO_70_ORACULOS_E_OBSERVAVEIS_v0_4.md), com entrada, EXPECTED, observável e negativos por cenário. Os dez casos aqui seguem como exemplos detalhados; nenhuma fixture executável ou teste foi criado.

**Data:** 22/10/2026. **Status:** [P/R] artefato de preparação E02-FIX. Dados **100% inventados**. As chaves abaixo são apenas **linguagem lógica de teste**, não JSON Schema da S0, payload OpenAI, estrutura persistida nem contrato físico. Não há código, testes executados, API, custo, credenciais ou aceite bilateral.

## Convenções dos exemplos

- `tenant` = concessionária fictícia A ou B; `person` é resolvido pela S0; `case` e `closure` são distintos; `mNN` são mensagens com autoria e ordem.
- `S0_DECIDES` = efeito sujeito a ACL, esquema, catálogo, versões, estado e idempotência; não é promessa de que F01/F02/F03 possam gravar.
- `NO_EFFECT` = nenhuma mutação de negócio, envio ou leitura fora de escopo. `ACTUAL=NÃO_EXECUTADO` para todos os casos.
- Todos os instantes usados são **ficcionais** e servem para testar comparação/ordenação; a regra precisa tratar UTC, fuso da concessionária e relógio Meta sem misturá-los.
- Cada caso mantém o ID da matriz v0.3; outros 60 cenários da matriz exigem posterior concretização da mesma maneira. Este documento não é autorização E04.

## SYN-33 — Histórico de dois casos da mesma loja (P0)

**GIVEN:** tenant A, pessoa PA1, caso K1: `m01(cliente, 01/10): "Minha renda é 3000"`; caso K2: `m09(cliente, 22/10): "Corrigindo, minha renda agora é 3500"`; `closure=E2` autenticado, cutoff `m09`; campo fictício `renda` autorizado no catálogo.

**WHEN:** S0 solicita F03 após E2 e disponibiliza histórico lógico autorizado de PA1/A até m09.

**EXPECTED:** propostas contêm `renda=3500` com fonte `m09` e referência histórica contextual `m01`; não consulta B; não cria ficha separada para K2; persistência somente via S0 e versões válidas.

**MUST NOT:** anexar mensagem posterior m10 ou esconder fonte anterior. **ACTUAL:** NÃO_EXECUTADO.

## SYN-34 — Cutoff preservado, aplicação revalidada (P0)

**GIVEN:** tenant A, m07 é última mensagem no evento E1 de fechamento autorizado às 11:00; m08 chega às 11:03; a IA conclui análise E1 às 11:05; S0 percebe que a versão da ficha mudou entre leitura e tentativa de gravação; mais tarde há conclusão E2 legítima.

**WHEN:** a proposta F03 referente a E1 chega para validação.

**EXPECTED:** (a) recibo/prova de E1 permanece corte histórico em m07, sem importar m08; (b) decisão de mutação analisa versão/atribuição atuais e bloqueia gravação obsoleta ou coloca em revisão [R]; (c) E2 tem cutoff próprio e pode incluir m08.

**MUST NOT:** tratar E1 como inválido retroativamente ou incluir m08 na extração E1. **ACTUAL:** NÃO_EXECUTADO.

## SYN-38 — Opcionais também devem ser extraídos (P0)

**GIVEN:** catálogo sintético A obrigatório, B/C opcionais; fontes cliente m01 `A=MODELO_X`, m02 `B=COR_X`, m03 `C=PRAZO_X`; conclusão E1 válida, sem conflito.

**WHEN:** F03 extrai todos os campos elegíveis.

**EXPECTED:** A, B e C propostos com respectivas fontes; outro opcional D não mencionado **não** exige retorno humano. Se A estivesse ausente, A geraria pendência; não permitir edição manual pelo Consultor.

**MUST NOT:** omitir B/C ou bloquear por D. **ACTUAL:** NÃO_EXECUTADO.

## SYN-40 — Pausa de captação ≠ perda do caso (P0)

**GIVEN:** C1 é Consultor atribuído ao caso K1, `intake_paused=true`, mas S0 confirma C1 disponível/autorizado para K1; F03 aponta campo essencial A ausente.

**WHEN:** S0 direciona pendência.

**EXPECTED:** retorno a C1; não selecionar Gestor por causa exclusiva de `intake_paused`; F01 não recebe dados de roster. **ACTUAL:** NÃO_EXECUTADO.

## SYN-43 — Desistência explícita versus venda (P0)

**GIVEN:** cliente m04 diz `"Desisti da compra, não quero prosseguir"`; Consultor encerra E1, S0 confirma evento; estado corrente é elegível para revisão de transição (detalhe S0 ainda [R]).

**WHEN:** F03 avalia desfecho.

**EXPECTED:** proposta **separada** de mudança para `perdido` por desistência com fonte m04; execução somente quando S0 permitir e com motivo catalogado. **MUST NOT:** declarar negativa do Banco, remessa ou venda. **ACTUAL:** NÃO_EXECUTADO.

## SYN-50 — Relógio C09 não parte de aceite HTTP (P0)

**GIVEN:** template final `TPL_FINAL_V1` autorizado, retorno de API `API_ACCEPTED` às 12:00 e evento `queued` às 12:02; não existe recibo confiável `sent`. São 13:00 do dia seguinte; cliente silencioso.

**WHEN:** S0 avalia perda por silêncio pós-final.

**EXPECTED:** relógio de 24h **não** é iniciado sem `sent`; nenhuma perda C09 por silêncio; tentativa permanece estado técnico a resolver. **ACTUAL:** NÃO_EXECUTADO.

## SYN-59 — Base pausada interpretada, não ofertada (P0)

**GIVEN:** na loja A há base `CAMPANHA_JULHO`, com contexto semântico `"Campanha de julho com validade prevista até dia 20"`, estado pausado, fato aprovado de condição comercial histórica. Cliente: `"Aquela campanha de julho ainda existe?"`.

**WHEN:** F01 consulta conhecimento autorizado A no modo interpretar histórico.

**EXPECTED:** reconhecer que a campanha histórica existiu/foi mencionada, indicar que **não é oferta ativa**, sem prometer taxas/validade atuais; manter proveniência e não ler B. **MUST NOT:** ignorar contexto da base só por ela estar pausada, ou reofertar condição. **ACTUAL:** NÃO_EXECUTADO.

## SYN-62 — Pausa agendada prevalece sobre job atrasado (P0)

**GIVEN:** base A está rotulada ativa, `pausar_em=22/10/2026 12:00 America/Recife`; relógio simulado indica `12:01`; worker de atualização de rótulo está atrasado; fato contido de promoção só seria elegível com base ativa.

**WHEN:** S0 prepara contexto F01 de **oferta atual**.

**EXPECTED:** filtro de elegibilidade bloqueia uso do fato como vigente, apesar de rótulo antigo; auditoria pode registrar discrepância sem afirmar que houve pausa persistida. **ACTUAL:** NÃO_EXECUTADO.

## SYN-66 — Confirmações independentes por mutação MCP (P0)

**GIVEN:** Diretor Prumo autenticado solicita (1) criar base de conhecimento A; (2) excluir vinte registros operacionais de A. S0 prepara duas prévias separadas, incluindo escopo, consequência, versão e irreversibilidade. Diretor confirma autenticadamente **somente** a prévia 1.

**WHEN:** agente MCP tenta concluir ambas.

**EXPECTED:** (1) poderá ocorrer apenas se S0 aceitar todos os guards; (2) fica `NO_EFFECT` e deve solicitar confirmação própria. Não inferir confirmação de texto anterior para ação 2 nem devolver sucesso antes de resultado S0. **ACTUAL:** NÃO_EXECUTADO.

## SYN-67 — Registros MCP não editáveis pelo MCP (P0)

**GIVEN:** Diretor autentica, pede exclusão/alteração da auditoria protegida MCP e confirma explicitamente a mesma operação, inclusive em duas etapas.

**WHEN:** MCP chama operação administrativa, inclusive tentativa por importação em massa.

**EXPECTED:** S0 rejeita mutação com guarda fora do modelo; eventos prévios intactos e auditados; eventual leitura permitida com ACL. **ACTUAL:** NÃO_EXECUTADO.

## Pontos de aceite E02-FIX

Antes de virar código, cada exemplo deve obter revisão do **dono da operação real**, catálogo/esquema e versão formal, formato de autorização e prova, política de privacidade para mídia, expected em máquina verificável e commit. Os casos de `sent`/Meta, remessa bancária e MCP precisam de contratos físicos dos seus donos. Métrica de execução permanece **0**, e a completude documental parcial deste caderno não basta para declarar E02-FIX encerrada.
