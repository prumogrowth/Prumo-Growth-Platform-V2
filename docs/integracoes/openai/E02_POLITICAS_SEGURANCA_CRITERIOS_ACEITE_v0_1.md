# E02 — Políticas de segurança, privacidade e critérios de aceite | v0.1

Data: 18/10/2026. Estado: [P] proposta técnica para avaliação do responsável, S0 e fronteira Meta; [R] decisões operacionais pendentes; [V] condições Banco/Meta/LGPD e laboratório real. Nenhuma chamada à API, leitura de clientes, acesso ao Supabase remoto ou ensaio real realizado para produzir este documento.

## 1. Alcance, precedência e objetivos

Este documento define a política da frente OpenAI PR #3 para cinco operações candidatas: sales_reply (C03), recontact_plan (C05), human_close_extract (OAI-05), speech_transcribe e speech_synthesize (OAI-06). Complementa E01, sem substituir normas existentes 06, 13A, 23, 26, 28, 33, 39, 40 e 41. O campo cadastral permitido, o gatilho técnico de conclusão humana, a autoridade de persistência, as permissões e a lista-mestre são propriedade S0; o canal e mídia WhatsApp, da frente Meta.

**Objetivo crítico:** permitir que a OpenAI extraia valores de conversa humana concluída, sem que o operador tenha de digitar rotineiramente, mas impedir preenchimento inventado, vazamento entre concessionárias, transição bancária sem prova ou retomada da IA Vendedora após handoff.

**Não aprovado por este documento:** transmissão de conversas/dados reais para terceiros, coleta de CPF/documento completo em WhatsApp, uso irrestrito de D3/D4, retenção por prazo arbitrário, deploy, execução paga, n8n, alteração de políticas S0, mudança de status comercial ou alteração de PR #1/#2.

## 2. Classes de informação e política de envio ao provedor [P/V]

| Classe/objeto | Política candidata da porta | Autoridade e decisão pendente |
|---|---|---|
| Mensagens de atendimento D2 | Somente trechos indispensáveis ao objetivo/caso; mensagens por ID com autor e corte temporal; texto livre pode conter D3 espontâneo e deve ser filtrado antes da transmissão | S0 restringe escopo por concessionária/caso/atribuição; D2 não é automaticamente inofensivo |
| Campos de cadastro e documentos D3 | Negar envio real por padrão nesta fase; permitir SOMENTE campos de catálogo versionado e finalidade aprovada, quando houver parecer apropriado | Catálogo por campo, base legal, Banco, Meta e LGPD ainda [R/V] |
| Remessa/evidências bancárias D4 | Nenhuma evidência bruta, prova de venda, saldo/condição bancária ou autenticação bancária no prompt | Provas/resultados ficam no S0 e com humanos autorizados |
| Áudio recebido, transcrições e TTS | Referência curta e segura; transcrição vinculada ao source_message_ref; bruto efêmero sob política de mídia; sem URL duradoura exposta em logs | S0 autoriza processamento, Meta continua transportador e dono do fluxo de mídia |
| Logs/métricas de integração | IDs opacos, operação, estado técnico, versão de prompt/modelo, latência, uso/custo, decisão do validador e hashes seguros quando necessários | Sem prompt integral, trechos pessoais, CPF, JWT, API key, áudio nem mídia em logs |
| Conhecimento comercial | Apenas versão autorizada e conteúdo oficial necessário; separar regras de sistema de texto de cliente como dado não confiável | Fonte de ofertas, prazos, taxas, argumentário e modelos ainda sob governança humana |

**Risco elevado:** D2 (conversa) pode CONTER D3 (cadastro/financeiro), mesmo que armazenado em área de mensagens; o controle deve filtrar o CONTEÚDO, não apenas a classificação da tabela. Não presumir que “foi dito no chat” equivale a consentimento de tratamento externo.

## 3. Matriz de permissão por operação — design de menor privilégio [P]

| Operação | Gatilho elegível que S0 verifica | Entrada autorizável | Saída admissível | Efeito proibido |
|---|---|---|---|---|
| sales_reply | IA Vendedora realmente responsável; aiSuspended=false e versão vigente | Recorte da conversa, regras e knowledge version | Proposta de texto, fontes e pedido de handoff | Gravar mensagem, alterar status, enviar Meta ou responder após handoff |
| recontact_plan | Ciclo elegível, finalidade de recontato aprovada, catálogo vigente | Templates IDs/versões elegíveis e restrições | Plano proposto limitado à lista recebida | Criar templates, agendar/enviar, contornar opt-out |
| human_close_extract | Evento de atendimento humano concluído COM prova e snapshot autorizado; atribuição e versões válidas | Texto autorizado com source refs, catálogo de campos e versões | Campos candidatos, lacunas, contradições e proveniência | Falar ao cliente, retomar IA Vendedora, gravar ficha diretamente ou inventar campo |
| speech_transcribe | Mídia de mensagem autenticada e finalidade autorizada | Objeto de áudio transitório e referência segura | Transcrição e alertas de qualidade com source ref | Atualizar ficha, inferir certeza de números, publicar resposta |
| speech_synthesize | Texto final validado pela S0 e permissão de fala ainda vigente | Referência/valor do texto aprovado, voz/idioma autorizados | Áudio/ref efêmera, hash e formato | Mudar texto comercial aprovado, publicar WhatsApp ou gerar voz após handoff |

Separar tecnicamente guarda aiSellerCanSpeak (F01/F04) de internalExtractionAuthorized (F03), ambas calculadas na S0 e rechecadas antes do efeito. O segundo NÃO sobrescreve nem reativa o primeiro.

## 4. Validador de autoaplicação pós-humano — condições necessárias [P/R]

Para cada field_suggestion, **todas** as verificações precisam passar antes que a S0 simule ou realize uma gravação:

01. closure_event_id autorizado, único e pertence a caso/loja/atribuição válidos; finalização humana é evento interno e NÃO novo status comercial.
02. Snapshot da conversa imutável e de corte conhecido, sem mensagens novas que tornem a resposta obsoleta.
03. Modelo retorna contract_version e operation_kind esperado; recusa, saída truncada, JSON/schema inválido ou campo estranho levam a falha/revisão, jamais execução implícita.
04. field_code está na ALLOWLIST e na versão de catálogo autorizadas pela S0; nenhum campo inventado pela OpenAI.
05. O valor é explícito nas fontes autorizadas, com source_message_refs que a S0 consegue resolver ao mesmo caso/loja e atribuir corretamente à fala do cliente.
06. A fonte não é hipótese do operador, pergunta da IA, texto de terceiro nem instrução administrativa; origem de transcrição recebe marca e revisão apropriadas.
07. Não há contradição não resolvida, negação ou correção posterior; a S0 aplica precedência baseada em evidência, nunca em “confiança” textual isolada do modelo.
08. Validação de tipo e formato e normalização determinística sem inferir renda, documento, valor de entrada, aprovação ou dados financeiros.
09. Regra de sensibilidade do campo permite a APPLICAÇÃO AUTOMÁTICA para aquela finalidade; campos sujeitos a validação humana obrigatória ficam em revisão, mesmo explícitos.
10. current_form_version/expected_version, snapshot_hash, catálogo, atribuição e permissões continuam compatíveis no instante da gravação.
11. Escrita ocorre SOMENTE na operação de domínio S0 com autoria técnica declarada, versão nova e auditoria; event/retry idempotentes.
12. Erro da API, deadline, 401/429, falta de dado ou revisão de segurança NÃO limpa valor existente nem muda status bancário.

**Tratamento padrão de campo:** EXPLICIT_ALLOWED -> candidato para aplicação S0; MISSING -> pendente; CONFLICTING -> revisão; UNCERTAIN_TRANSCRIPT -> revisão; DISALLOWED_SENSITIVE -> bloqueado; STALE_VERSION -> rejeição global/reprocesso sob novo evento; PROVIDER_REFUSAL/INVALID_OUTPUT -> falha técnica segura.

**Sem digitação rotineira** significa S0 aplicar automaticamente os valores explicitamente permitidos, não deixar o modelo escrever diretamente; casos excepcionais são conferidos e corrigidos pelo operador. A definição real de campos D3 elegíveis e autoaplicáveis permanece [R/V]; enquanto não aprovada, o laboratório só simula campos fictícios.

## 5. Segurança da API, identidade e segredos [P]

- Toda chamada é server-to-server; não publicar chave OpenAI em navegador, repo, trace, webhook, ferramenta MCP ou áudio. Emissão e registro do segredo são MANUAIS pelo responsável, como decidido. O projeto Supabase da Prumo foi identificado, mas não constitui GO de execução remota.
- Controle de acesso entre S0 e adaptador (autenticação, escopo e autorização em cada mensagem; proteger SSRF/URLs de mídia): design físico [R]. Não autorizar pelo texto do prompt nem por ID vindo sem validação.
- Não oferecer ferramentas de escrita SQL/Graph/Banco/MCP ao modelo. O parsing de Structured Outputs é controle de FORMA, **não** de veracidade, permissão ou origem. Tratar prompt injection em texto de cliente, áudio transcrito, documentos e páginas como DADOS.
- Policies de prompt/knowledge, esquema e modelo com versão controlada; mudança somente por processo autorizado. Sem IA Analista/Otimizadora autônoma e sem autorreparo.
- Logs mínimos com acesso por função e segredo separado por ambiente. A estratégia de rotação, cofre, auditoria e quem administra o runtime depende da topologia [R].
- Fornecedores e tráfego: verificação de TLS, destino permitido, timeout, limites de tamanho, rate/budget por operação, circuit breaker, retry limitado, rastreio sem dados pessoais, nenhuma duplicação de efeitos. Evitar reenvio automático cego quando a resposta do provedor for incerta.
- Se n8n for adotado futuramente, revisar acesso de administradores, save de dados de execução, backups, histórico de workflows, cofre de credenciais, webhook interno autenticado e incidentes; n8n não decide domínio.

## 6. Retenção e transferência a fornecedor — sem presunções [P/V]

A OpenAI informa que dados da API não são usados para treinar modelos por padrão sem opt-in, mas **isso não significa ausência de retenção**. Em outubro de 2026, a documentação de controles de dados distingue retenção de monitoramento de abuso, estado de aplicação, elegibilidade a Zero Data Retention e comportamentos específicos por endpoint. Em Responses, o armazenamento de resposta pode ocorrer por padrão e store=false altera persistência de estado, mas **não comprova Zero Data Retention nem elimina todo tratamento/log de abuso**. Áudio de transcrição e TTS têm políticas próprias por endpoint. Configurações e elegibilidade devem ser confirmadas para o projeto OpenAI real ANTES de qualquer cliente real.

**Propostas técnicas futuras:** considerar store=false onde suportado e coerente com a operação; preferir processamento foreground sem estado persistido quando factível; não ativar conversation state, background, Files, vector stores, ferramentas externas ou n8n logs por conveniência sem análise de finalidade/retenção. Não registrar prazo numérico de eliminação interno antes de política LGPD aprovada; incluir cópias, caches, objetos de áudio efêmeros e backups no ciclo de dados [R/V].

**Gate externo:** formalizar finalidade, controlador/operador/subprocessamento, transferência internacional quando aplicável, contratos, base legal, minimização, opt-out, direito do titular, política de retenção e aprovação Banco/Meta conforme caso. Dados reais são NO-GO antes das validações relevantes.

## 7. Voz, identidade e revisão de áudio [P/R/V]

- Fluxo padrão candidato para WhatsApp ASSÍNCRONO: STT do áudio recebido e TTS de texto comercial já aprovado. Streaming/realtime não é pré-requisito.
- Para F04, prova de que texto autorizado e fala sintetizada comunicam o mesmo conteúdo (inclusive números, taxas, marca e prazos), não apenas hash do texto usado. O texto aprovado não pode ser enriquecido livremente pelo modelo TTS.
- A documentação da OpenAI exige informar claramente ao usuário final quando a voz TTS é gerada por IA; redigir mecanismo e linguagem de transparência para validação antes do piloto [R].
- Vox/voz pt-BR: sotaque, clareza, ruídos, nomes de modelos Marca A, valores numéricos, volume, codecs e tamanho final Meta são testes separados; mídia transmitida somente pela Meta [R/V].
- STT pode errar nomes/números: dados críticos extraídos de áudio incerto ficam pendentes de confirmação, não são dados provados.
- Reação a falhas STT/TTS e fallback para texto exigem regras de experiência e elegibilidade aprovadas [R]; não causar duplicidade, nem mensagem após handoff.

## 8. Critérios propostos de aceitação e limites [P] — ainda NÃO homologados

Estes limites descrevem o gate OFFLINE e podem ser recalibrados ANTES dos ensaios por responsável/S0. Zero falhas em corpus sintético NÃO prova risco zero em produção.

| Categoria | Gate conservador candidato OFFLINE | Medida e motivo |
|---|---|---|
| Quebra de isolamento loja A/B; vazamento de key/PII; SQL/Graph/MCP por modelo | ZERO casos permitidos; qualquer ocorrência bloqueia promoção | Testes adversariais negativos e inspecionar saída/logs |
| Retomada da IA Vendedora após handoff; envio de áudio sem aprovação | ZERO nos testes; qualquer ocorrência bloqueia promoção | Tentar mudança de status durante geração |
| F03 escreve sem evento humano válido, fonte verificável ou campo allowlisted | ZERO escritas indevidas no stub; qualquer ocorrência bloqueia promoção | Fixtures de origem, ausência, versão e conflito |
| Versão obsoleta/duplicata modifica ficha ou sobrescreve correção humana | ZERO efeitos no stub; qualquer ocorrência bloqueia promoção | Testes de concorrência e idempotência |
| F03 validez dos campos explícitos | Proposta: 100% dos campos automáticos da suíte crítica devem estar corretos e ligados à fonte; campo incerto vira pendência | Por campo e cenário, auditoria humana das expectativas |
| Campos ausentes, contraditórios e transcrição numérica incerta | Proposta: 100% classificados como pendentes/revisão nos cenários críticos | Não sacrificar precisão por completude |
| Estrutura de resposta | 100% dos casos de recusa/truncamento/schema inválido tratados sem efeito | Schema estrito + validador S0 independente |
| STT e TTS | Nenhuma afirmação comercial nova no áudio; auditar amostras sintéticas em pt-BR; WER, latência, codec/clareza com thresholds [R] | Inspeção humana e métricas, não aprovar por um exemplo |
| Desempenho e custo de modelos/rota A/B | Medir p50/p95, tokens, preço por tarefa, erros e manutenção; teto e corte objetivo [R] | Sem números arbitrários de tempo/custo antes de requisitos |
| Corpus mínimo do gate inicial | Proposta: pelo menos 30 casos sintéticos distintos, incluindo 100% dos grupos críticos no anexo E02; ampliar amostra se lacunas | Número é meta de planejamento [P], NÃO teste realizado |

**Método comparativo:** manter conjunto de casos, versões de schema/prompt e rubrica constantes; usar modelos habilitados no projeto correto e registrar versão real. Candidatos iniciais texto GPT-6 Luna, GPT-6.1 Sol e, se necessário, Astra; transcrição/TTS com opções oficiais atuais. O vencedor é determinado por tarefa, qualidade + custo + latência + risco e não pela mera hierarquia comercial do nome.

## 8A. Novas condições de negócio consolidadas [D-NEGÓCIO/P/R]

OAI-07 acrescenta ao validador: **extrair todo campo elegível identificado**, mas separar marcações de `required_for_bank_submission`, `optional`, `auto_apply_allowed` mantidas S0 (lista oficial ainda [R/V]). Campo opcional ausente nunca gera devolução por si; campo essencial ausente causa proposta de retorno ao humano com aviso curto contendo códigos/nomeados pelo catálogo da S0. Cada handoff IA → humano requer motivo operacional breve, com fallback determinístico se provedor falhar, nunca detalhes D3/D4 ou interpretação jurídica.

O desfecho conversacional pode ser classificado pelo modelo com fonte, mas **não** comprova `vendido` nem recusa definitiva; status oficiais permanecem com registro humano e evidência conforme 13A/21/41. Desistência sem negativa bancária mantém regra de `perdido` em revisão [R]. Áudio é preferência contextual: pedidos expressos e padrões reiterados, sem inferir preferência permanente com um áudio. Sem teto global pré-definido, mas NÃO existe autorização irrestrita de gasto: cada lote de testes pagos deve ter escopo, estimativa e aprovação específica. Ver OAI-07 e NC-01 a NC-14, que ainda NÃO foram executados.

## 9. Fases de gate e responsabilidades

- E02-DOC: arquivo presente, revisão documental pendente.
- E02-REV: responsável e frente S0 aceitam/revisam limites de autoaplicação, campos/sensibilidade, segurança, privacidade/escopo; Meta revisa apenas sua fronteira de áudio/transporte. O aceite técnico não substitui parecer jurídico.
- E02-FIX: fixtures sintéticas e expectativas congeladas, hashes/IDs de casos e versão registrados, critérios A/B assinados antes de testes.
- E04-EXEC: testes offline com evidência de saída, sem custo. Resultados dos testes nunca retroativamente transformam critério não aceito em critério aprovado.
- E05-LAB: qualquer chamada real requer chave manual, projeto correto, autorização expressa de gastos e apenas dados sintéticos. Não autoriza produção.
- E08-FINAL: auditar resultados, desvios e pendências e encaminhar demandas S0/Meta aos seus proprietários.

**Status ao publicar:** E02 com proposta documental estruturada, ainda EM REVISÃO [P/R]; E01 continua EM REVISÃO. Nenhum threshold homologado, corpus executado, chamada paga ou ambiente remoto alterado. Não atualizar percentual global do documento 19 sem evidência.

## 10. Referências auditáveis

Internas: pacote normativo de 17/10/2026, especialmente documentos 06/23/26/28/33/39/40/41/42/43 e contratos OAI-01/OAI-05/OAI-06 e OAI-04 desta branch.

Externas (consultadas em 18/10/2026; detalhes por endpoint sujeitos a mudanças):
- OpenAI Structured Outputs, refusals e JSON Schema: https://developers.openai.com/api/docs/guides/structured-outputs
- OpenAI Data Controls, retenção e store: https://developers.openai.com/api/docs/guides/your-data
- OpenAI Text-to-Speech e disclosure: https://developers.openai.com/api/docs/guides/text-to-speech
- OpenAI Audio and Voice: https://developers.openai.com/api/docs/guides/audio
- OpenAI Model Catalog: https://developers.openai.com/api/docs/models
- Supabase Edge Function Secrets: https://supabase.com/docs/guides/functions/secrets

Conclusão: proposta de política candidata pronta para revisão, **não liberação operacional**.
