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
