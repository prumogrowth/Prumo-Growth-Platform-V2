# Mapa de capacidades e pendências — Frente OpenAI | v0.1

> **AVISO DE PRECEDÊNCIA — AUDITORIA DA FRENTE OPENAI, 22/10/2026.** Este documento anterior permanece preservado como **contrato candidato/histórico**; trechos conflitantes **NÃO são a direção funcional vigente**. Ler primeiro [AL-IA-00 — índice e precedência](./ALINHAMENTO_2026_10_22_00_INDICE_E_PRECEDENCIA_v0_1.md), [AL-IA-01 — jornada](./ALINHAMENTO_2026_10_22_01_JORNADA_F01_F02_F03_v0_1.md), [AL-IA-04 — deltas](./ALINHAMENTO_2026_10_22_04_RASTREABILIDADE_DELTAS_PENDENCIAS_v0_1.md), [AL-IA-07 — dependências entre frentes](./ALINHAMENTO_2026_10_22_07_DEPENDENCIAS_RELEVANTES_OUTRAS_FRENTES_v0_1.md) e [AL-IA-08 — auditoria documental](./ALINHAMENTO_2026_10_22_08_AUDITORIA_FECHAMENTO_DOCUMENTAL_FRENTE_OPENAI_v0_1.md). O texto abaixo documenta o estado de sua data original, **sem emendar código, criar autorização S0, nem corrigir documentação de outras frentes**.
>
> **Atenção especial:** a matriz antiga menciona correção excepcional da ficha pelo Consultor; essa permissão foi retirada na diretriz mais recente. O mapa não contém integralmente as novas bases de conhecimento, pausa agendada, cache opcional, catálogo de habilidades e governança MCP, que constam dos arquivos AL-IA.


**Data:** 18/10/2026. Fonte: pacote auditado do projeto de 17/10 (principalmente docs 06, 08B, 11, 23, 24, 26, 40, 41) e decisão funcional nova do responsável nesta conversa. Classificação [D] normativo confirmado, [D-NEGÓCIO] manifestação funcional atual, [P] contrato proposto, [R] decisão interna pendente, [V] validação externa. Mapa não autoriza implementação, gasto, transferência de dados ou reatribuição de backlog.

## Inventário que deve sobreviver ao desenvolvimento

| Frente funcional relacionada à OpenAI | Fonte/situação | Nossa responsabilidade técnica OAI | Dependências/limites |
|---|---|---|---|
| Conversa da IA Vendedora (texto) | [D] doc06/08B | Modelo e porta `sales_reply` C03, prompt versionado, resposta curta verificável e fallback | S0 controla status/segurança/contexto, Meta envia |
| Planejamento de recontatos | [D] doc06/08B | `recontact_plan` C05; escolher somente versões de templates existentes/aprovadas, testar modelo | S0 decide agenda e cancelamentos, Meta executa |
| **Extração cadastral após encerramento humano** | **[D-NEGÓCIO] orientação atual; [P/R] OAI-05** | Extrair campos com referência de mensagens/transcrições e retornar proposta estruturada; operador sem preenchimento rotineiro | S0 valida/aplica automaticamente o permitido e versiona; operador corrige exceções |
| Transcrição de áudio recebido | Diretriz mídia [D/V] doc06/08B; modelo [P] | `speech_transcribe`, qualidade pt-BR e fontes | Meta mídia/canal; S0 LGPD, escopo e persistência |
| Áudio enviado pela IA Vendedora | **[D-NEGÓCIO] requisito atual**, [P/R] OAI-06 | `sales_reply` textual + `speech_synthesize` apenas após aprovação S0 | S0 outbox/guardas; Meta entrega, sem fala após handoff |
| Interpretação de imagem/foto e documento/PDF | Diretriz condicionada [D/V] doc06/08B Q67; **não entregue** | Futuro contrato de extração multimodal [R], comparar visão/PDF após avaliação de finalidade | Mídia não retida no núcleo por padrão, LGPD/Banco, Meta; NÃO supor coleta de foto documental necessária |
| Conhecimento oficial / guardrails comerciais | [D/P/R] docs 06/11 | Versionar prompt e consumir conhecimento autorizado do núcleo; testar alucinações | Dono do conteúdo/versões não é a OpenAI; fontes oficiais do banco pendentes |
| Modelo por tarefa, custos e failover | [P/R] OAI-06 | Matriz de escolha e benchmarks sem modelo prematuramente fixado | Autorização de orçamento/chave manual e testes específicos |
| Integração direta ou n8n | [R] OAI-04 | Provar rota direta e justificar ou testar n8n | Não alterar S0/Meta nem contratar n8n por presunção |
| ChatGPT/MCP de responsáveis | [D] docs 06/41, **outra linha funcional** | Apenas esclarecer possíveis dependências OpenAI quando solicitadas | Não absorver MCP ou eliminar dupla confirmação de escrita |
| IA Analista/Otimizadora autônoma da v0.2 histórica | **EXCLUÍDA [D] pelo doc06 posterior** | Não implementar como serviço, nem habilitar autoalteração de prompts/parâmetros | Revisões de desempenho sob iniciativa de humanos por MCP, sem novo agente independente |
| Rotinas de remessa/resultado bancário | [D] docs 21–23, 26, 41 | Nenhuma execução bancária; somente extrair fatos declarados quando legitimamente permitido | Remessa, venda e recusa definitiva continuam atos humanos comprovados na S0 |

## Organização da frente OpenAI por entregável

**Contrato E01 obrigatório:** `sales_reply`, `recontact_plan`, `human_close_extract`, `speech_transcribe`, `speech_synthesize`; OAI-05/OAI-06 são propostas novas e ainda passam por revisão cruzada. Não abrir capacidades externas não autorizadas, como interpretação de documento sensível, só para completar o catálogo.
**Descoberta futura pós-E01:** `multimodal_analyze` para imagem/PDF se realmente permitido, e avaliação de Knowledge/FAQ. Não criar contrato de coleta real ou mídia retida prematuramente.
**Observabilidade transversal:** por operação, versionamento, origem, escolha de modelo, latência, custo e erros técnicos minimizados.

## Registro de lacunas [R/V]

1. [R] Catálogo final de campos e campos D3 permitidos para extração e aplicação automática.
2. [R] Semântica e autoridade de "operador concluiu atendimento"; fechamento técnico não altera estado de comercialização.
3. [R] Política de correção excepcional e representação de falha/revisão na ficha sem criar nono status comercial.
4. [R/V] Base legal, consentimento, retenção e subprocessamento de dados/conversas/áudios, alinhados com Banco/Meta/LGPD.
5. [R] Respostas de voz: quais situações, quem escolhe voz, informação sobre automação, limites de tamanho/tempo e fallback.
6. [R/V] Uso de imagens/fotos/documentos sensíveis: apenas quando pertinente e autorizado; armazenamento transitório.
7. [R] Métricas de "melhor modelo" por tarefa: qualidade/falso positivo/latência/custo; modelos e preços são temporais.
8. [R] Contrato com S0 para snapshot versionado e commits de `cadastro_versao` sem expansão de privilégios.
9. [R] Revisão conjunta com Meta somente para transcrição/mídia e publicação de áudio, sem tocar no PR #2.
10. [R] Política de n8n não presumida; decisão em OAI-04 posterior aos testes.

## Fontes OpenAI oficiais para viabilidade, NÃO teste do projeto

- Responses structured outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- Transcrição: https://developers.openai.com/api/docs/guides/speech-to-text
- Texto em fala: https://developers.openai.com/api/docs/guides/text-to-speech
- Imagens e visão: https://developers.openai.com/api/docs/guides/images-vision
- Arquivos/PDF: https://developers.openai.com/api/docs/guides/file-inputs
- Catálogo de modelos: https://developers.openai.com/api/docs/models

**Estado final da revisão:** inventário documentado; integrações não testadas; nenhum compromisso de desenvolver a interface dos operadores ou funções bancárias/Meta nesta branch.
