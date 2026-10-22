# E01 v0.3 — Contrato funcional integrado OpenAI F01/F02/F03 e áudio (candidato)

> **Anexo técnico lógico v0.4 [P/R]:** [E01-INT — entradas/saídas tipadas e política de falha fechada](./E01_CONTRATO_TIPADO_ADAPTADOR_FALHAS_v0_4.md). Preserva os limites funcionais desta v0.3; não substitui contrato ratificado S0 nem autoriza chamada de modelo.

> **Complemento E01-KH v0.3:** [Conhecimento, bases, habilidades e MCP do Diretor](./E01_CONHECIMENTO_HABILIDADES_E_MCP_OPERACIONAL_v0_3.md). O conteúdo deste complemento é **candidato [P/R]**, não interface S0 ratificada. E02 operacional tem segurança, matriz de 70 cenários e fixtures narrativas com **zero execução**.

**Data:** 22/10/2026. **Status:** versão operacional de trabalho **[P/R]**, coerente com diretrizes [DN] AL-IA de 22/10, sem homologação bilateral, código, testes de modelo ou integração real. Este arquivo é sucessor para futuras implementações de `E01_CONTRATO_FUNCIONAL_MULTI_CAPACIDADE_v0_2.md`, mantido como histórico de 18/10.

## 1. Documentos e regra de precedência

**Para implementar no futuro, a referência coordenada é:** AL-IA-00/01/02/03/04/07/08 → OAI-01 v0.3 (fronteira) → OAI-05 v0.3 (F03) → OAI-07 v0.3 (desfecho/roteamento) → OAI-08 v0.3 (F02). OAI-06 continua proposta histórica válida para STT/TTS quando não conflitar; requisitos de conhecimento de AL-IA-02 deverão ganhar contrato físico próprio na E01/E02, não inferir sistema já escolhido. Dúvidas interfrentes permanecem [R], fora do poder de aprovação exclusivo da OpenAI.

## 2. Catálogo de funções e limites

| Capacidade | Entrada lógica fornecida pela S0 | Trabalho da IA/OpenAI | Retorno à S0 |
|---|---|---|---|
| F01 `sales_reply` | Caso sob IA, tenant e contexto autorizados; fatos institucionais e da loja elegíveis; configurações globais | Atendimento comercial natural, fatos sem promessas não comprovadas, coleta permitida | Texto/resposta sugeridos, referências e motivo de handoff; **não** envio Meta |
| F02 `recontact_plan` | Pedido específico, limites, público e templates versionados **pré-filtrados** por finalidade/loja | Selecionar horários/versões elegíveis, inclusive nova cadeia humana autorizada | Plano candidato e final separado; **não** agendamento/envio |
| F03 `human_close_extract` | Conclusão humana expressa, corte, acesso lógico ao histórico integral cliente/loja e catálogo de campos | Extrair todos campos permitidos com fonte, conflitos, desfecho e avisos | Propostas estruturadas; S0 decide aplicar/transicionar |
| `speech_transcribe` (apoio) | Mídia/áudio autorizado e origem | Transcrever mantendo incerteza e prova de autoria | Transcrição referenciada; sem mutar ficha por si |
| `speech_synthesize` (apoio) | Texto F01 previamente aprovado + política de mídia | Gerar áudio coerente com texto aprovado | Ativo para Meta, não envio |
| Avaliação de modelos | Corpus sintético e rubrica aprovada | Medir por tarefa | Relatório comparativo, sem seleção automática definitiva |

**F01, F02, F03 são as três capacidades funcionais de IA**, áudio é modalidade/serviço auxiliar, não duas novas IAs autônomas. IA Analista/Otimizadora autônoma histórica está **excluída**, e ChatGPT/MCP do Diretor não se confunde com F01/F02/F03.

## 3. Instruções, conhecimento e contexto

Exatamente **quatro campos globais separados e versionados**: (1) instruções F01; (2) comportamento F01; (3) instruções F02; (4) instruções F03. Nenhum campo de instrução/comportamento local por concessionária. A S0 fornece identidade do tenant e dados permitidos; a Prumo administra fatos institucionais e de cada loja, conhecimento com gatilho semântico/fato canônico/metadados, bases adicionais restritas a sua loja, pausa manual/automática opcional e vigência de campanhas, conforme AL-IA-02. Contexto de base pausada pode servir **à interpretação histórica**, não a ofertar condição vencida.

Recuperação de fatos e histórico não confere autorização, nem substitui validação S0 de permissão/versão/vigência. A F03 pode reexaminar **fontes históricas de diversos casos da mesma loja**, inclusive mídias legalmente disponíveis, **sem** expor dados a outra concessionária. Cache é opcional; internet aberta não é fonte padrão. Habilidades configuráveis requerem capacidade técnica existente, autorização e conhecimento associado; IAs não instalam nem criam ferramentas.

## 4. Papéis, jornada e segurança

- **Isolamento multi-concessionária em todas as operações e recuperação**; canais App/WABA/número da concessionária, fornecidos/configurados/operados pela Prumo com autorização, sem fusão de dados/credenciais.
- F01 não conhece equipe/escala; S0/S1 decide handoff/posse. Handoff silencia F01 no caso. Cliente que já foi vendido ou teve cadastro enviado ao banco **na mesma concessionária** retorna humano.
- F02 não edita templates/variáveis, não envia e não avalia erros ordinários de envio; somente templates elegíveis. Motivos `perdido` por falha Meta/ausência de resposta são determinísticos S0 sob guardas, não inferidos livremente por IA.
- F03 executa exclusivamente após botão do Consultor e lê histórico autorizado até **cada cutoff imutável**; resultados exigem revalidação da **autorização atual** antes de escrita. Ficha é única/evolutiva por cliente/loja. Consultor vê segundo UI permitida, mas **não edita**; incidentes F03 não geram esse atalho.
- F03 pode propor transição automática validada pela S0 (inclusive `perdido` por desistência inequívoca), mas **`vendido` só humano com prova bancária**; `cadastro enviado ao banco` só com remessa efetiva; negativa definitiva do Banco somente ato humano comprovado.
- Pendência de essencial/conflito após F03: retorno preferido ao Consultor original e, se realmente indisponível para esse caso, seu Gestor (S0/S1); `intake_paused` isolado não retira caso. Ausência só de opcional não bloqueia. F02 pós-humano não é disparada automaticamente por lacuna.
- Retorno após venda/remessa pode abrir novo caso humano, sem apagar evento histórico ou iniciar F01, e nova conclusão pode atualizar a ficha atual.
- Os **três relógios** são distintos: janela Meta desde último inbound, conclusão humana por clique e 24h desde `sent` comprovado de template final para C09 elegível; a matriz C09 humana ainda depende da S0.

## 5. Interfaces físicas ainda a pactuar com S0 [R]

| Questão | Prova existente | Por que não está concluída |
|---|---|---|
| Recibo F03 e autenticação | PR #12 S0 com `expected_cycle_version`, cutoff/hash/watermark, GoTrue/HMAC/PG17 locais | Recibo não contém payload cliente, `form_version`/catálogo nem autorização de integração com IA |
| Contrato de entrada F03 | CFI-01 v0.1 candidato | Histórico integral, múltiplos casos, mídia, identidade/versões e minimização pendentes |
| Contrato de saída F03 | OAI-05/OAI-07 v0.3 conceituais | Schema tipado, provas, erros e efeito comercial de S0 não ratificados |
| F02 pós-humano | CF-OP-02 / OAI-08 v0.3 | C05/C08/C09, templates, prova `sent` e estado/fase pendentes |
| Conhecimento/habilidades | AL-IA-02/03 [DN] | Catálogo, ACL, API de recuperação, vigência, prompts globais e MCP executável ainda a especificar |
| STT/TTS/modelos | OAI-06, plano de avaliação [P] | Avaliação, preços, cobertura e políticas reais não testados |
| Banco | Preferência de envio direto futuro [DN/V] | Investigação e integração expressamente adiadas |

Não derivar `expected_case_version`, `form_version` ou permissão a partir da versão de ciclo. Não inventar campos bancários, domínio do número Meta, requisitos de retenção nem métodos de verificação de identidade por múltiplos telefones. Transições comerciais S0 permanecem ao dono do domínio.

## 6. Conjunto mínimo de testes E02/E04 a preparar [P/R]

1. Isolamento A/B de prompts, fatos, contexto histórico, mídias e cache; mesma pessoa/número em lojas distintas.
2. F01 com handoff e restrição de equipe; resposta tardia negada; sem condição bancária inventada.
3. F02 com templates/versionamento/finalidades/slots; opt-out, duas falhas definitivas e relógio `sent` versus `API_ACCEPTED`; C09 somente elegível.
4. F03 com caso histórico antigo da mesma loja, cutoff por conclusão humana, nova mensagem e nova conclusão, mídia disponível/indisponível, ficha única com atualização após remessa, campo opcional, autoria/proveniência, versões concorrentes e desistência distinta de negativa bancária.
5. Exigir `vendido` apenas humano, negar remessa sem prova, devolver essencial ao Consultor/Gestor autorizado sem liberar edição e sem confundir pausa de intake com revogação.
6. Recuperação de conhecimento de base pausada sem oferta vencida, pausa agendada opcional e instruções globais exatamente quatro, sem prompt local.
7. Habilidade não instalada, prompt injection de dado externo, negação por consentimento, JSON inválido, 401/429, timeout, retry, áudio incerto, custo e ausência de cache.

**Não contar casos textuais SYN/EX/PV como PASS**, nem laboratório S0 como teste OpenAI. Nenhum E04/E05 foi iniciado na branch OpenAI.

## 7. Critério de aprovação e continuidade

Esta v0.3 é **implementável como intenção de contrato**, não como formato físico homologado. Para fechar E01, requer revisão de S0↔OpenAI de envelope/autorização/erro/proveniência, revisão de fronteiras Meta/S1/FV, e catálogo/versões sem contradizer as decisões AL-IA; E02 precisa rubrica e casos atualizados. **E04 offline somente sob gate de implementação expressamente liberado; E03 credenciais e E05 uso pago continuam adiados até autorizações específicas.** Nenhuma alteração nas outras frentes, sem deploy, merge, custo ou dados reais.
