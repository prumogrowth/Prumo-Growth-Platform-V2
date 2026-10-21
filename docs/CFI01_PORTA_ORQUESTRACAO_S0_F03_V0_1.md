# CFI-01 — Porta mínima de orquestração S0 → F03, sem autorização fictícia | v0.1

**20/10/2026 | Escopo: [P/R] integração estrutural OFFLINE na branch OpenAI do PR #8 Draft.** Não existe implementação autenticada de `S0CompletionPort` nessa frente. O código **não** conclui atendimento, chama API da OpenAI, grava cadastro, agenda plano, envia mensagem, processa dados reais nem cria prova de remessa bancária.

## Objetivo e implementação

O arquivo `backend/s0_openai_bridge/s0_completion_port.py` cria somente a **sequência de confiança** que deverá ser usada quando a S0 ratificar a assinatura da operação. Uma solicitação de conclusão `CompletionRequest` só carrega:
- `case_ref` (opaco);
- `expected_case_version`;
- `idempotency_key`.

**Não** contém `actor_id`, `store_ref`, `session_authorized`, `grant`, `owner_route`, hash, watermark nem evento criados pelo cliente. Esses fatos pertencem ao S0/S1 autenticado.

A porta **a implementar pela S0** é propositalmente pequena:
1. `S0CompletionPort.begin(request) -> S0Answer`: S0 autentica sessão atual, resolve concessionária/caso/ciclo/atribuição, autorização e fechamento, registra ou retorna o evento técnico durável/idempotente, escolhe corte e catálogo, e entrega um `S0ClosedSnapshot` mínimo de referência quando autorizado.
2. `F03CandidatePort.propose(captured) -> object`: símbolo para futura extração pela OpenAI; atualmente somente um *fake* em testes. O código de orquestração **não interpreta essa resposta**, pois a assinatura OAI-05/07 física ainda não foi homologada.
3. `S0CompletionPort.recheck(captured) -> S0Answer`: depois da proposição, o S0 verifica novamente sessão, grant/atribuição, fechamento, hash, watermark e versões. Revogação `DENIED` prevalece sobre defasagem `STALE`; não se expõe resultado do modelo caso a autorização falhe.
4. Somente quando as duas verificações concordam, o **resultado é `S0_VALIDATION_REQUIRED`**, jamais `APPLIED`. A S0 ainda precisa validar catálogo, evidência, valor, classe sensível, conflito, autoria e fazer commit transacional idempotente com versão auditada. Esta etapa NÃO existe neste módulo.

`prepare_f03_completion_review()` sem **ambas** as portas retorna `BLOCKED_BY_S0_CONTRACT`. Sua execução positiva com `FakeS0` é uma prova de **ordem de chamadas**, NÃO de sessão verdadeira nem de autorização GoTrue/HMAC. Nenhuma porta tem conector web, token, método de mutação, SQL, rota Meta, prova do Banco ou comando da F02.

## Contrato concreto pendente do proprietário S0

A implementação de `S0CompletionPort` **não deve aceitar objetos `S0Answer` construídos no browser ou pela IA como prova**. É implementação exclusivamente server-side por S0 após assinatura de CFI-01, aproveitando o caminho de identidade GoTrue e sessão atual do backend do PR #1 onde for apropriado, mas **sem reutilizar `cancelar_plano`/`conciliar_c07` como se autorizassem a F03**.

A S0 deve definir evento técnico imutável de fechamento, versão do caso e ficha, atribuição vigente com regras S1, concessão de loja (incluindo exceção por caso ainda [R]), snapshot mínimo com hash e watermark, catálogo autorizado com regras LGPD, idempotência e política de atualização concorrente. S0 é única responsável por validar/persistir os dados elegíveis e por provar remessa/resultado bancário. Nenhum dos oito status comerciais é alterado pela resposta da F03.

**Lacunas do protótipo intencionalmente abertas:** falta contrato canônico com `fields_proposed`/`conversational_assessment`/lacunas/conflitos, transferência do recorte autorizado de mensagens, fonte real do snapshot, mecanismo de prova de autoridade e transação de aplicação. O retorno tipado `S0ClosedSnapshot` é DTO provisório de teste, **não assinatura física aprovada**.

## Evidência local e gates

`backend/tests/test_s0_completion_port.py`: **20/20 testes sintéticos**, incluindo ausência da porta S0, requisição sem identidade controlada pelo browser, negação antes do modelo, rejeição de versões e caso divergentes, revogação após a proposição, mensagem nova, hash/fechamento alterados, indisponibilidade e saída do modelo contendo alegação fictícia de venda/autoridade sem efeito.

Uma única execução local sobre a versão dos módulos anteriores preservados do pacote do PR #8 executou **199/199 PASS**: **179 regressões anteriores de F02+F03/roteamento** e **20 testes desta porta**. `compileall` PASS. Arquivos publicados byte a byte: `s0_completion_port.py` blob Git `f9e401831123c81194992750f6e2ad57144ddec0`; testes blob `c0740b5be333e7068307caa5ec6e192f59fdf9e9`. **Não** inclui as sete suítes históricas de 210 testes F03 ainda pendentes, CI, chamadas de modelo real nem teste PostgreSQL.

**Para marcar etapa de conciliação encerrada:** aprovação expressa do contrato por S0/OpenAI/FV/S1, identificador de versão canônica e prova de implementação backend ratificada. **Para marcar substituição de fixtures por permissões reais:** porta S0 funcional em sandbox GoTrue/PostgreSQL local com verificações de sessão, grants, atribuição, versão, concorrência e aplicação atômica; testes de integração e de revogação. Enquanto isso, o estado da frente é `BLOCKED_BY_S0_CONTRACT`, não `GO`.

A pausa para dúvidas e auditoria geral solicitada pelo responsável só acontecerá **depois** da conclusão comprovada das duas etapas, não agora. Sem merge/deploy, Supabase hospedado, API OpenAI paga, dados reais, modificações ao S0 proprietário ou consumo de Meta/Banco.

## Incremento de segurança e atualização S1 — 20/10/2026 (posterior à primeira execução)

O contrato **candidato** `S0ClosedSnapshot` ganhou `completion_request_key`, `assignment_ref` e `assignment_version`. A comparação do identificador de solicitação impede aceitar snapshot relativo a outra `idempotency_key`; a comparação integral do snapshot no `recheck` invalida alterações de atribuição, sua versão, catálogo ou recorte durante a proposição. **Nenhum desses campos é prova criptográfica, concessão ou identidade autenticada:** a S0 real precisa emitir e verificar todos eles, e seus nomes e semântica exigem ratificação. O modelo não pode definir ou substituir esses campos.

O retorno do modelo agora recebe **apenas conferência mínima de tipo e `operation_kind='human_close_extract'`**. Payload vazio ou de outra operação resulta em `MODEL_RESPONSE_INVALID`, mas até um `dict` com esse identificador permanece **não validado** quanto a campos, fonte, desfecho ou alegação bancária. A rechecagem S0 ainda precede o retorno de erro de resposta do modelo: se a sessão caiu nesse intervalo, `DENIED` tem precedência sobre o estado do payload.

A frente **S1-002**, em sua issue #10 e PR #5, publicou testes PostgreSQL isolados de (a) prova transacional do contato humano com corridas de redistribuição, (b) autorização excepcional **estritamente por caso/atribuição/loja**, e (c) indicador de mensagens independente da leitura do gestor. **São fixtures S1, não migrations operacionais nem interface S0 GoTrue/HMAC**; a S0 continua precisando disponibilizar a fonte autenticada da atribuição/entitlement para a F03. A pausa no recebimento de novos leads não equivale à suspensão da conta nem extingue por si só a atribuição humana de um caso iniciado. Não importar a exceção de teste como grant da S0.

**Evidência desta alteração:** `test_s0_completion_port.py` passou de **20 para 32 cenários** e a regressão combinada local passou de **199/199 para 211/211 PASS** (179 anteriores + 32 porta), em uma única execução `unittest discover`; `compileall` PASS. Blobs Git de código e testes coincidentes com o laboratório: `b350ac56fd03fb574705344796daa380a8d5d74b` e `edc1dcc316355d0c9f5f6de8bb3891fbb2263a44`. **211 não é a regressão histórica das sete suítes F03 (210 casos), que segue pendente**. Esta prova não substitui S0 real, nem ratifica o envelope OAI-05/07 ou executa aplicação.

**Permanecem obrigatórios [R/V]:** assinatura S0/FV/OAI de idempotência/fechamento/evento/caso/snapshot e recheck; implementação da S0 com sessão real, grants e prova de atribuição da S1 e transação de aplicação; escolha do JSON Schema canônico e tratamento LGPD/Banco/Meta; integração e testes cross-front com S0 real. Nenhum endpoint, chamada real, deploy, merge ou SQL foi criado nesta rodada.

## Incremento de minimização da porta — 20/10/2026, terceira rodada

**Correção de fronteira:** o protótipo anterior passava o objeto inteiro `S0ClosedSnapshot` ao método `F03CandidatePort.propose(...)`. Embora os testes fossem sintéticos, esse DTO contém **`completion_request_key`, `assignment_ref`, `assignment_version` e escopo interno da S0**, todos necessários à revalidação mas desnecessários à proposta do modelo. Esse acoplamento aumentava a superfície de vazamento caso alguém conectasse o adaptador a um serviço externo sem revisar a fronteira.

O novo DTO imutável `F03ModelView` contém SOMENTE `operation_kind='human_close_extract'`, `closure_event_ref`, `snapshot_hash`, `message_watermark` e `catalogue_version`. O fluxo mantém `S0ClosedSnapshot` integral apenas em `S0CompletionPort.recheck`; o objeto voltado ao modelo **não** carrega operador/atribuição, chave de idempotência, loja/caso, sessão, token, grant, provas do Banco, telefone nem conteúdo da conversa. Esse DTO **não é token de busca nem autorização** e não torna o provedor real seguro por si só.

**Limite decisivo:** as referências mínimas de teste não bastam para interpretar conversa; o formato de carga de mensagens minimizadas, o canal autorizado, o consentimento/base legal, a retenção e os dados permitidos D2/D3/D4 ainda precisam de contrato físico ratificado S0/OpenAI/LGPD. **Nenhum texto ou áudio real é enviado; o conector OpenAI real continua ausente**. A implementação futura deve obter a carga de mensagens da S0 sob escopo comprovado, e não dar ao modelo acesso a `S0ClosedSnapshot` ou ao banco.

**Evidência local nesta rodada:** **220/220 PASS** em `unittest discover` sobre os módulos F02/F03/roteamento e a porta; na porta isolada, **41/41 PASS**, com 9 novos cenários sobre minimização, isolamento de atributos, imutabilidade, preservação do snapshot completo apenas para rechecagem S0 e negação antes de propor. `compileall` PASS. Blobs Git publicados coincidem com os arquivos testados: código `b0c2edeffb06ef6c8ba5f333e8157a48ba59b332`; testes `f1999e157da67e658e33827cea1e774b7ab8a29c`. **São ensaios offline, não a regressão histórica de 210 F03, nem a substituição de permissões fictícias.**

**Status dos marcos solicitados:** conciliação técnica documentada, assinatura S0/OAI e emissão de autorização real **pendentes**; implementação do gateway/porta real, aplicação transacional, validação interfrentes e testes com sessão real **pendentes**. **Não iniciar pausa nem auditoria geral** até esses dois marcos terem evidência comprovada. Sem SQL, hospedagem, custo, merge ou deploy.
