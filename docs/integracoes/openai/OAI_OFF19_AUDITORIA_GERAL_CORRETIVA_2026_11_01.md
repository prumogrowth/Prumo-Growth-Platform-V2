# AUD-OAI-19 — Auditoria geral corretiva da frente OpenAI (OFF-01…OFF-18)

**Data:** 01/11/2026. **Origem:** pedido do proprietário de revisar não somente o que foi testado, mas o alinhamento da frente com a visão LiberaCred, falhas de segurança e pontos desenvolvidos sem auditoria posterior. **Classificação:** `AUDITORIA_CORRETIVA_OFFLINE_APROVADA_COM_RESTRICOES`, não laudo de produção, parecer jurídico, pentest completo ou aceite de S0/Meta.

## 1. Bases e métodos

- Conceito: `projeto_liberacred_consolidacao_ideias_v0_2_auditada.md` (10/10/2026), com diretrizes **IA Vendedora**, **IA Analista/Otimizadora**, **IA Gestora**, orquestrador determinístico, dados por concessionária, atendimento humano, aprendizado somente em **configurações externas autorizadas** e manifestação favorável **verbal**, NÃO autorização formal do Banco Yamaha.
- Código canônico examinado: [OpenAI OFF-18 `1dcf6ef26c808489b176c988a0222f2d4a66618f`](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/commit/1dcf6ef26c808489b176c988a0222f2d4a66618f). Árvore `docs/integracoes/openai/e04_offline_lab`: `core`, `typed-boundary`, F01 atendimento/posse/fontes, F02 planejamento/WA-39, F03 histórico/metadados/commit, lifecycle, journey, transport, frequency, Responses preflight, manifestações de fonte, testes e workflows.
- Evidências herdadas: [OFF-08 678/678](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41268436358), [OFF-14 864/864](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41296787271), [OFF-16 950/950](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41312239545), [OFF-18 950 Node + 24 Python AST](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41328844179).
- Contratos externos **candidatos**, não ratificados: S0 F01 [#11](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/11), fontes [#12](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/12), F02 [#7](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/7), F03 [#5](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/5)/[#6](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/6), Meta evidência [#9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9)/PRE_DISPATCH [#10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10). OFF-18 reconheceu **somente** o mapeamento independente de ciclo/atribuição.
- Método: inspeção manual dos módulos e contratos, confronto com o documento conceitual, revisão de superfícies de permissão/dado/versão, regressões adversariais novas em `off19-core-audit.test.mjs`, execução cumulativa Node e rechecagem Python pinada via GitHub CI. **Não executamos ataque de rede, fuzzing exaustivo, PostgreSQL hospedado, modelo real ou cliente.**

## 2. Achados corrigidos nesta branch (incidentes prevenidos)

| ID | Risco encontrado | Evidência da versão anterior | Correção de laboratório | Severidade para futura integração |
|---|---|---|---|---|
| AUD19-01 | **Leitura de versão herdada/mascarada** na implementação legada `core.mjs/versionGate` | A comparação usava `k in ctx.current` (também verdadeiro para propriedade herdada) e apenas conferia a contagem de chaves próprias. Um objeto `current` com `case` herdada e uma chave substituta podia ser interpretado como `READY`. Accessors de versão podiam executar código do chamador. | Agora requer **mesmo conjunto exato de chaves próprias**, descritores de dados, versões inteiras válidas e protótipo simples/nulo. Rejeita getters sem chamá-los; mantém distinção `STALE/INVALID_INPUT/DENIED`. | **Alta se futuramente usado em entrada externa**; alcance atual somente laboratório E04, não bypass de S0 real |
| AUD19-02 | **Relógio implícito na validade de oferta da F01 legada** | `validateF01` usava `req.nowMs ?? Date.now()` para expiração de fonte; a mesma fixture podia mudar de veredicto conforme relógio do runner. | Para fonte com validade, agora exige `req.nowMs` inteiro não negativo; expiração compara apenas o instante injetado pela S0/fixture. Sem relógio de processo. | **Média**, risco de falso positivo/negativo em planejamento de integração |

Os **18 testes OFF-19** validam chaves herdadas, acessores, falsas flags de autenticação, símbolos, distinção de revisões de ciclo/atribuição, propagação F01/F02/F03 e relógio explícito. O novo gate CI exige **968/968 testes Node** (950 herdados + 18 novos), fail=0, skipped=0, e **24/24 auditorias Python** da origem S0 pinada `31e88ec` (conjuntos separados). **Primeiro CI validado:** [GitHub Actions 41338979377](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41338979377): 968/968 Node PASS, 0 FAIL, 0 SKIP, e 24/24 verificações Python PASS, source-level e separadas. A CI é repetida após o commit de fechamento deste relatório e do roteiro.

## 3. Inspeção por entrega

| Faixa | Cobertura auditada e constatação | Situação |
|---|---|---|
| OFF-01, bases `core/journey` | Encontrados AUD19-01/02 corrigidos na branch de auditoria. Módulos legados ainda não são uma interface pública e precisam de revisão dedicada se forem expostos em runtime. | **CORRIGIDO_NA_BRANCH / REVISÃO_OPERACIONAL_PENDENTE** |
| OFF-02 a OFF-08 | Pacote com manifesto de integridade, auditorias anteriores e regressão de 678, módulos F01/F02/F03 com propostas S0-only e provas de escopo e falha fechada. Testes não autenticam a S0. | **PROVA_OFFLINE**, não serviço |
| OFF-09/10 | Publicação ZIP auditada e CI de pré/pós-commit; apenas branch candidata. | **RASTREÁVEL**, não merge |
| OFF-11 | WA-39 candidato interpreta `API_ACCEPTED` distinto de `SENT`, recusa conflito e não autoriza C09. | **PROVA_SINTÉTICA**, falta Meta real |
| OFF-12 | F03 não promove histórico `REVIEW_ONLY_NOT_FROZEN` ou aplicação `APPLIED_SYNTHETIC_ONLY` a histórico completo ou escrita. | **PROVA_SINTÉTICA**, falta S0 multicases real |
| OFF-13 | F01 mantém handoff humano/opt-out/isolamento em duas leituras não autenticadas. | **PROVA_SINTÉTICA**, falta owner transacional real |
| OFF-14 | F01 separa ofertas vigentes e contexto histórico, marca correção, vencimento e tenant. | **PROVA_SINTÉTICA**, falta fonte oficial/banco/comercial |
| OFF-15 | 44 testes de não conversão entre domínios. | **PROVA_SINTÉTICA**, não pentest |
| OFF-16 | Preflight do formato Responses e 42 testes: aceita só `UNTRUSTED_JSON_CANDIDATE`, que devolve texto bruto não validado semanticamente. Flags de autorização `false`. | **PROVA_SINTÉTICA**, alto risco se integrador futuro confundir "preflight passou" com autorização |
| OFF-17/18 | Mapeamento F02 `cycle`/ `assignment` corrigido no S0 laboratório e reavaliado pela OpenAI, com 24 testes AST em cursor falso. | **ACEITE TÉCNICO CANDIDATO APENAS DO MAPEAMENTO** |

## 4. Riscos e lacunas NÃO resolvidos — bloquear promoção para operação

| ID | Prioridade | Lacuna e consequência | Responsável / critério de encerramento |
|---|---|---|---|
| AUD19-P1 | **Bloqueante** | Os CIs de 950/968 **não são** prova de autenticação S0, autorização de uso do modelo, isolamento hospedado, política Meta, consentimento real, publicação, PG17 integrado ou qualidade de textos bancários. | S0/Meta/Infra + aceite independente dos contratos autenticados e testes físicos/end-to-end |
| AUD19-P2 | **Bloqueante** | `responses-shape-preflight-lab` expõe `candidateRaw` marcado **não confiável** após checar apenas schema/tag de topo. Se um novo integrador o enviar a cliente ou interpretar como proposta final, poderá propagar conteúdo incorreto ou instrução maliciosa. | Qualquer futura integração OpenAI DEVE acoplar verificador específico F01/F02/F03, recheck S0 e sink isolado; **nunca** publicar conteúdo `candidateRaw` diretamente |
| AUD19-P3 | **Alta** | Validadores legados `core.mjs` permanecem utilitários de fixture e não normalizam integralmente toda árvore recebida como os wrappers mais novos. A correção version/clock NÃO equivale a segurança de todos os demais campos do módulo. | Não exportar `core.mjs` diretamente a endpoints; revisar/retirar utilitários legados no desenho do runtime e repetir ataques de getter/prototype/cycle |
| AUD19-P4 | **Alta** | Fontes verdadeiras do Banco Yamaha, preços, condições, cadastro/fechamento e autorização regulatória ainda não entregues; manifestação do gerente foi **verbal**, não documento formal. | Banco / jurídico / responsável: autorização e catálogo oficial antes de atender/cadastrar/fechar em operação real |
| AUD19-P5 | **Alta** | As mudanças OFF-11…OFF-19 estão em **branches de laboratório**, não na `main`, sem release controlada, auditoria cruzada da árvore final integrando S0/Meta e deploy. | Responsável de integração: aprovação de escopo, CI conjunto, diff/manifesto final e autorização explícita de merge/deploy |
| AUD19-P6 | **Alta** | Origem autenticada e minimização de dados ao modelo, retenção de logs/prompts, classificação LGPD e controle de custos ainda não testados com serviço real. | S0/Infra/Privacidade + trabalho OpenAI de avaliação com dados **100% sintéticos** e orçamento aprovado |
| AUD19-P7 | **Escopo futuro explícito** | Visão completa distingue **IA Vendedora**, **IA Analista/Otimizadora** e **IA Gestora**. O roteiro OpenAI OFF01–OFF18 cobre sobretudo **funções F01/F02/F03** (atendimento, planejamento, histórico); **não implementa nem testa** pipeline de analista que modifica somente parâmetros externos autorizados, aprovação/rollback, nem IA Gestora com privilégios administrativos. | Product owner planejar trilhas separadas, permissões e critérios antes de declarar "IA plataforma completa". Não é falha da F01 isolada |
| AUD19-P8 | **Alta** | Status de entrega/sent/WA-39, pré-despacho transacional, cadência por consentimento e time-to-live do evento dependem de contratos Meta/S0 ainda não homologados. | #7/#9/#10 e S0: eventos assinados/correlacionados, idempotência, readback e gate de envio |
| AUD19-P9 | **Alta** | Histórico F03 congelado por pessoa e multicases, mídia/transcrição, proveniência/confiança e commit de ficha com catálogo de campos não são homologados em S0 hospedada. | #5/#6: completude/cutoff, conta/perfil/loja, versões de formulário, CAS S0 físico e consentimento |
| AUD19-P10 | **Gestão de evidências** | 950 testes Node são acumulados em uma única árvore; 24 Python AST e 143 PG17 S0 pertencem a suites distintas. Não reportar "1117 testes integrados" nem dizer que todos os arquivos passaram por auditoria profunda/fuzz. | Manter contagens, SHAs e escopos por execução; auditoria independente pré-produção |

## 5. Objetivo: aderência x escopo

**Aderente em arquitetura:** IA produz propostas, o software/S0 determina permissões, concessionárias têm escopo segregado, handoff humano é definitivo, não confundir `API_ACCEPTED` com `SENT`, nem extração F03 com autoridade para alterar ficha, nem sugestão de IA com decisão bancária. IA Analista futura muda apenas **configurações externas autorizadas**, nunca pesos ou grants por conta própria.

**Ainda não entregue pela frente OpenAI:** avaliação semântica com modelo verdadeiro, corpus autorizado do banco, agente Analista, IA Gestora, monitoramento de qualidade/custos, rollback de estratégias, testes de voz/STT, dados reais autorizados e via de cadastro/fechamento. Isso **não** justifica ligar API OpenAI/Meta antecipadamente.

## 6. Regras para sequência

1. Somente corrigir no módulo legado a validação de versão e relógio apontadas nesta auditoria; **não reescrever** a frente S0/Meta nem a integração funcional OFF-04/05/03.
2. Registrar auditoria e teste no GitHub; CI exige 968 Node + 24 Python e nenhum arquivo backend/Meta/Supabase/Frontend alterado.
3. Manter 08B/08C, integração 09–11, testes físicos 12B/C e implantação 13 pendentes. OFF-19 não é avanço de integração operacional.
4. Prioridade próxima após a auditoria: **revisar arquitetura de sink seguro entre Responses preflight e avaliadores F01/F02/F03**; seguir integração WA39 apenas com fontes autenticadas, sem tratar `candidateRaw` como proposta aprovada.
5. Não pedir chave, não fazer chamadas pagas e não dar status de produção. Antes da API real, submeter missão limitada a aprovação expressa, orçamento e segredo em serviço autorizado.

**Conclusão de auditoria (condicionada aos limites acima):** a frente é coerente com a estratégia de IA sob controle do orquestrador, **mas NÃO está pronta para produção**. Dois defeitos de hardening foram corrigidos no código de laboratório, e há lacunas materiais de integração, fonte oficial, segurança e roadmap que permanecem bloqueadas ou futuras. Não afirmar "sem falhas" só porque o CI está verde.
