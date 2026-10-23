# OAI-01 v0.3 — Porta operacional S0 ↔ OpenAI (candidata)

> **Governança atualizada em 23/10/2026:** [S0 é infraestrutura compartilhada, sem frente proprietária exclusiva ativa](./DECISAO_S0_COMPARTILHADA_EDICAO_POR_FRENTES_2026_10_23_v0_1.md). A frente OpenAI desenvolve F01/F02/F03 e implementa na própria S0 as interfaces de backend que precisar, por alterações isoladas e compatíveis. Ratificação física e testes continuam exigidos, mas a ausência de uma frente S0 não é condição de espera. Primeira adaptação direta: [PR #16](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/16), ainda Draft e offline.

**Data:** 22/10/2026. **Estado:** [DN/DA] funções aprovadas em alinhamento de produto; [P/R] interface física ainda candidata; [V] homologações externas. **NÃO É** endpoint implementado, aceite conjunto, permissão de execução, nem autorização de custo/deploy.

## 1. Precedência e relação com versões anteriores

Esta é a **versão operacional de referência para conciliação** da frente OpenAI. Substitui funcionalmente trechos incompatíveis do `contrato-s0-openai-v0_1.md` (OAI-01 histórico), sem apagá-lo, e deve ser lida com `ALINHAMENTO_2026_10_22_00_INDICE_E_PRECEDENCIA_v0_1.md`, AL-IA-01/02/03/04/07/08. Para F03 consultar OAI-05 v0.3; desfechos/roteamento OAI-07 v0.3; recontatos OAI-08 v0.3; integração E01 v0.3. **Versão 0.3 não significa ratificação S0.**

**Terminologia:** plataforma = solução Prumo sem nome comercial definido; LiberaCred = produto financeiro da instituição financeira. Papéis de produto: Diretor, Gestor e Consultor; identificadores técnicos anteriores podem permanecer enquanto não conciliados.

## 2. Limite de autoridade e isolamento

- S0 autentica, autoriza, prepara contexto, controla ficha, ciclo, fila, status, consentimentos, idempotência e persistência. A saída do modelo é **proposta**, sem acesso de escrita privilegiada, sem poder de provar venda, remessa, envio WhatsApp ou permissão.
- Meta/WhatsApp fornece canal, templates e evidências de transporte; S1/equipe controla atribuição e disponibilidade; OpenAI somente interpreta/propõe resultados tipados. O modelo não chama Graph, Banco, SQL nem MCP administrativo por conta própria.
- Em **cada entrada, recuperação, ferramenta e retorno**, preservar escopo explícito da concessionária. Mesmo CPF/telefone de A e B nunca fundamenta mistura de histórico, vetor, conhecimento privado, logs, mídia ou resposta. Nenhum prompt cria ou amplia concessão.
- A Prumo providencia/configura/opera canais autorizados dentro da **estrutura Meta segregada da própria concessionária** (App/WABA/número/credenciais), sem inferir titularidade jurídica do número; pertencimento e canal autorizado são validados externamente ao modelo.
- F01 não recebe nomes, escalas, quantidade ou disponibilidade de consultores; solicita handoff à S0. F02/F03 não conversam diretamente com clientes.
- **Quatro campos globais** configuráveis, versionados: instruções F01, comportamento F01, instruções F02, instruções F03. **Nenhum** campo de instrução/comportamento por loja. Conteúdo de cada concessionária é conhecimento factual isolado, não prompt de governo alternativo; guias do MCP Diretor são domínio independente.

## 3. Operações lógicas (nomes herdados, assinatura física [R])

| Operação candidata | Finalidade | Pré-condição/S0 | Saída OpenAI |
|---|---|---|---|
| `sales_reply` (F01/C03) | Resposta comercial proposta | Posse da IA e janela/canal elegíveis; sem handoff definitivo; conhecimento autorizado | Conteúdo proposto + fontes/alertas, jamais envio |
| `recontact_plan` (F02/C05) | Planejar nova cadeia com templates preexistentes | Solicitação específica S0; finalidade/loja, templates/versões, opt-out e limites aprovados | Sequência candidata, razões, alertas; nunca envio/gravação |
| `human_close_extract` (F03) | Extrair e analisar após encerramento humano expresso | Evento S0 autenticado, histórico lógico do cliente/loja até cutoff, catálogo autorizado | Campos, evidências, lacunas, conflitos e avaliação conversacional; nunca mutação direta |
| `speech_transcribe` | Entrada de áudio, fonte autorizada | Referência de mídia/acesso e política aprovados | Transcrição, proveniência e incerteza |
| `speech_synthesize` | Saída em áudio | Texto F01 aprovado pela S0 e canal/mídia elegíveis | Ativo de áudio proposto ao Meta; nunca disparo |

Nomes são referências de interoperabilidade histórica, não rotas HTTP, métodos, schema JSON ou ferramentas já existentes. Interpretação de imagens/vídeos/documentos para contexto F03 exige autorização e contrato multimodal [R/V].

## 4. Envelope conceitual obrigatório, mas físico pendente

Entrada lógica sob confiança **S0 → adaptador**: identidade da operação; `request_id` e versão de contrato; `concessionaria_ref` e contexto de caso/cliente no escopo; autoria/propósito; política e versão de instruções globais; referência a conteúdo autorizado e evidências; catálogo e versão aplicáveis; versões de estado relevantes; idempotência/corte/deadline quando pertinente. Nenhum ID declarado pelo cliente ou pelo modelo é autorização.

Retorno **adaptador → S0**: versão/`request_id` correlacionados; operação; resultado tipado válido **ou** erro/refusal explícito; referência às fontes efetivamente utilizadas; versão do contexto e limites; diagnóstico sem dados privados de cliente em logs; métricas de uso sem PII quando disponíveis. Saída desconhecida, malformada, incoerente, sem escopo ou com permissão presumida **falha em fechado**.

F03 tem **dois conceitos separados**: (a) corte imutável de evidências por conclusão humana — historicamente válido; (b) atualidade de versões/autorização/atribuição antes de aplicar resultados — revalidada pela S0. Nova mensagem não altera o cutoff anterior; tampouco dá licença para gravar resultado obsoleto. `expected_cycle_version` físico da S0 **não** equivale automaticamente a `expected_case_version`/`form_version`/catálogo.

## 5. Guardas e comportamentos preservados

- F01 após handoff não retoma fala naquele caso. Retorno de cliente já vendido ou com cadastro remetido ao Banco na **mesma loja** segue humano. Após `perdido` pode haver novo ciclo elegível sem recriar ficha nem recuperar histórico legitimamente eliminado.
- F03 somente após **clique expresso de Concluir/Encerrar do Consultor**, não por relógio Meta nem por handoff em si; cada conclusão válida admite nova F03 com próprio cutoff.
- F03 pode **propor** transições comerciais que a S0 eventualmente executa se permitidas (inclusive `perdido` por desistência explícita fundamentada). **`vendido` é exclusivamente humano com prova bancária**; negativa bancária definitiva exige prova/registro humano; `cadastro enviado ao banco` requer remessa efetiva comprovada.
- As oito classificações comerciais existentes não recebem novo estado. Eventos de extração/conclusão/pendência são técnicos.
- Conhecimentos e bases (incluindo contexto de base pausada, vigência de ofertas e pausa automática opcional) não ampliam permissões. Internet aberta não é fonte padrão; cache de prompt é **otimização opcional**, nunca memória/controle de escopo.
- Identidade por múltiplos números na mesma ficha e recuperação histórica multimodal são diretrizes de produto, com prova de identidade, retenção e interface física pendentes [R/V].

## 6. Condições de falha e gates

Timeout, 401/429, recusa, JSON inválido, versão desatualizada, mídia indisponível, instrução adversarial, opt-out, revogação/transferência e corrida temporal devem produzir negação/revisão segura sem duplicar envio ou escrita. Falha reiterada F03 é **incidente técnico crítico**, não autorização para o Consultor editar ficha.

**Para ratificação:** S0 e OpenAI pactuar esquema, autenticação, IDs/versões, catálogo, proveniência, histórico e cutoff; S0/S1 roteamento; Meta templates e mídia; privacidade/retenção; critérios de erro e testes sintéticos. PR #12 S0 provou metadados/recibo em laboratório, **não** o payload completo da F03. E04/E05 dependem de gates próprios do plano; nenhuma credencial, custo ou integração real autorizados por este texto.
