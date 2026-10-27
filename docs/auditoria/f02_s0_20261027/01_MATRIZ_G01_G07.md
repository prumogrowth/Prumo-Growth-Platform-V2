# Matriz auditada F02/S0 — G01–G07

27/10/2026. Avaliação de implementação e integração; **nenhum gate operacional liberado**. `PARCIALMENTE ATENDIDO` reconhece trabalho aproveitável sem remover o bloqueio do manifest F02. Os G01–G07 desta matriz são diferentes dos G1–G6 da S1. Evidências E01–E12 em [02_EVIDENCIAS_E_LACUNAS.md](02_EVIDENCIAS_E_LACUNAS.md) e [EVIDENCIAS.json](EVIDENCIAS.json).

| Gate | Estado | Laboratório / integração física / operação |
|---|---|---|
| G01 — Contrato e versões S0/F02 | PARCIALMENTE ATENDIDO | PASS de compatibilidade; pin byte a byte confirmado; Registro interno do candidato comprovado; não transporte interfrentes; operação: PENDENTE |
| G02 — Transporte autenticado, binding CFI e recuperação | PARCIALMENTE ATENDIDO | Modelo F02 não autentica projection; GoTrue/PG reais para porta interna e recuperação COM binding preservado; operação: PENDENTE |
| G03 — Proveniência F03/C08/origem/intenção | PARCIALMENTE ATENDIDO | Produtores físicos PG17 com identidades/evidências sintéticas; Contexto CFI real sim; quatro testemunhas integradas ao registro S0 não; operação: PENDENTE |
| G04 — Ratificação humana gerencial S0/S1 | PARCIALMENTE ATENDIDO | Intenção F02 sintética não conta como aprovação; Administração I79 com GoTrue real comprovada; ato F02 ausente; operação: PENDENTE |
| G05 — Meta, consentimento, opt-out e disposição externa | PARCIALMENTE ATENDIDO | Modelos/fixtures e classificação offline comprovados; Composição forense anterior de laboratório; sem last mile F02 operacional; operação: PENDENTE |
| G06 — Política temporal, minimização e retenção | PARCIALMENTE ATENDIDO | Limites de fixture e testes UTC; Clock DB e terminais persistentes em PG descartável; operação: PENDENTE |
| G07 — Caminho físico integrado F01/F03/F02 | PENDENTE | Peças testadas separadamente; Jornada integrada ausente no recorte; operação: PENDENTE |

## G01 — Contrato e versões S0/F02

**Estado: PARCIALMENTE ATENDIDO. Responsável: Codex principal S0/S1, com revisão contratual F02.**

Código e contratos aproveitáveis:

- Schema result 0.1-candidate, 13 estados, revision decimal string e flags operacionais falsas.
- prepare_handoff e módulos lifecycle/recovery: blobs idênticos em F02, PR18 e I79; consumidores F02 mais recentes já existem.

Evidência verificável: E01, E02, E05, E11.

Lacunas concretas:

- Não há ratificação nem política de compatibilidade/migração/retirada de versão.
- Request é documento interno construído por dataclasses; não existe endpoint JSON aprovado.
- Proveniências 84d76c/dcac0d nos manifests F02 são baselines históricas, não o HEAD dc18e410.
- Schema result foi adicionado depois do executável S0 certificado; CI F02 testa o pin final, mas não é CI no HEAD S0.

**Próxima ação segura:** Revisar o candidato existente, registrar a versão aceita e a política de evolução em resposta separada ao handoff; manter as flags falsas. Não criar outro envelope.

Decisões/dependências:

- Codex principal: interface, comandos e compatibilidade.
- Produto: cardinalidade de pedidos por encerramento e substituição; loja+ator+chave não implica exclusividade comercial.

## G02 — Transporte autenticado, binding CFI e recuperação

**Estado: PARCIALMENTE ATENDIDO. Responsável: Codex principal S0/S1; Frontend apenas após decisão UI D1–D4; Segurança/Infra para fronteira e custódia.**

Código e contratos aproveitáveis:

- S0F02ReviewRegistryLocal.execute(record/read/withdraw), GoTrue, sessão viva, CFI, nonce/HMAC, CAS, ledger e auditoria existentes.
- Barreira de histórico PR16; comparação integral do recibo antes de COMMIT preservada.
- I79 reaproveita o gateway existente e trata cargo/chefia; não cria lookup F02.

Evidência verificável: E02, E03, E05, E06.

Lacunas concretas:

- Falta transporte de resposta S0 autenticada até F02 e lookup server-owned durável do binding após perda de processo.
- test_34 recria o broker conservando self.binding: não prova HA/failover nem perda completa de estado.
- CFI exige ator/sessão originais; novo login ou Gestor distinto não pode reutilizar automaticamente o recibo.
- UNAVAILABLE não prova rollback; read ainda exige documento, janela e binding originais.

**Próxima ação segura:** Concluir a consulta dos checkpoints I79 e decidir D3/D4; propor resolução pelo recibo/auditoria e ledger existentes com principal atual verificado e escopo aprovado, sem nova identidade nem sessão do cliente.

Decisões/dependências:

- Codex principal: continuidade entre sessões, lookup e autenticação da resposta.
- Segurança: vínculo ator/sessão/captura, expiração do handle, anti-CSRF conforme transporte escolhido.
- Produto/Privacidade: retenção e conteúdo mínimo do lookup.

## G03 — Proveniência F03/C08/origem/intenção

**Estado: PARCIALMENTE ATENDIDO. Responsável: Codex principal S0/S1 coordena; F01/F03 e F02 documentam seus produtores existentes.**

Código e contratos aproveitáveis:

- CFI real comprova loja/caso/ciclo/encerramento/hash/watermark/contagem/atribuição; PR18 compara lead/canal físicos.
- F02 tem produtores de laboratório de recibos F03, testemunha C08, ledger de origem e intenção sintética; preservar e mapear, sem portar a branch inteira.

Evidência verificável: E01, E02, E08.

Lacunas concretas:

- Os quatro *_sha256 de ClaimedS0Evidence são alegações; PR18 não lê nem autentica os quatro produtores.
- Faltam contratos de referência estável, canonicalização, verificador, chave/versão, cutoff e versão de fonte por testemunha.
- expected_case_version, form_version, assignment_version e catálogo/minimização F03 não são fornecidos por aliases de ciclo/UUID.
- Intenção EXPLICIT_REVIEW_SYNTHETIC_ONLY não é ratificação G04; C08 local não é cancelamento externo.

**Próxima ação segura:** Preencher mapa de cada prova para fonte/ID/versão/verificador/cutoff reais; demonstrar rejeição de prova ausente e escopo trocado antes de propor adapter S0.

Decisões/dependências:

- Codex principal e F03: contrato canônico de provas e versões independentes.
- Segurança: custódia e separação de domínios HMAC.
- Produto/Privacidade: mensagens autorizadas, finalidade e minimização.

## G04 — Ratificação humana gerencial S0/S1

**Estado: PARCIALMENTE ATENDIDO. Responsável: Codex principal conjunto S0/S1; Produto define limites do ato.**

Código e contratos aproveitáveis:

- I79: cargo explícito na equipe existente, Gestor sem subordinados, Diretor por competência canônica, ativação e transferência autenticadas, chefia obrigatória no COMMIT.
- I61/I62, concessões, RLS e barreira de sessão existentes; G1 prova encaminhamento da própria equipe, sem grant geral.

Evidência verificável: E02, E04, E06, E07.

Lacunas concretas:

- O result S0 mantém human_ratification=NOT_IMPLEMENTED_CONTRACT_PENDING.
- Não existe ato F02 APPROVE/DENY/REVOKE com ratificador distinto, escopo, validade, CAS e auditoria aprovados.
- O binding CFI do capturador não autoriza o Gestor a agir; cargo Gestor não concede acesso geral à loja/caso.
- A suíte F02 de 56 cenários da CI I79 roda antes da instalação I79; não comprova F02 sob cargo/chefia alterados.
- Legado sem cargo, desligamento, API/UI e owner hospedado permanecem abertos na própria I79.

**Próxima ação segura:** Preservar a prioridade I79/G2. Depois da fundação e regularização sob o principal, desenhar o ato de revisão usando as mesmas fontes de cargo/chefia/competência; não implementar um segundo sistema gerencial.

Decisões/dependências:

- Produto/Codex principal: quem pode ratificar, distinção do capturador, acesso e finalidade; competência de Diretor não equivale a aprovação F02.
- Produto: efeito de transferência/desligamento sobre ato já dado e sua validade.
- Segurança: prova do ato e auditoria/revogação.

## G05 — Meta, consentimento, opt-out e disposição externa

**Estado: PARCIALMENTE ATENDIDO. Responsável: Codex principal S0/S1 para C1–C7 e T1–T6; Meta/Infra para fonte externa; Produto/Privacidade para política.**

Código e contratos aproveitáveis:

- Classificadores Cloud, webhook e observação de template existentes; contratos candidatos DISPATCH-01/02, ACK-03, LOCK-04 e TEMPLATE-CATALOG-05.
- F02 preserva RESERVED_PREVIOUSLY_EXTERNAL_UNKNOWN; PR18 não consulta Meta e não cria tentativa.

Evidência verificável: E08, E09, E10.

Lacunas concretas:

- Sem fonte autenticada e atual de consentimento/opt-out/disposição vinculada à tentativa e sem catálogo operacional aprovado.
- Contratos M2M/ACK/dispatch/locks continuam candidatos; FileStore e booleanos de fixture não são backend.
- PRs Meta #21/#22/#24/#25 posteriores continuam offline; observação não equivale a sync confiado/aprovação.
- Cancelamento local não restitui slot; API_ACCEPTED/2xx não prova entrega nem autorização.

**Próxima ação segura:** Consolidar dependências já abertas C1–C7/T1–T6 numa revisão única; aproveitar classificadores e determinar fontes/estados, mantendo incerto e bloqueado o que não tiver prova.

Decisões/dependências:

- Produto/Privacidade: base legal, opt-out por escopo, janela/template/finalidade, conciliação e novo intento.
- Segurança/Infra: principal M2M, custódia, audience, ACL, rotação e ACK após durabilidade.
- Codex principal: bindings/versões e corridas com I79/S1.

## G06 — Política temporal, minimização e retenção

**Estado: PARCIALMENTE ATENDIDO. Responsável: Produto e Privacidade decidem; Codex principal implementa; Segurança/Infra cuida de clock/acesso.**

Código e contratos aproveitáveis:

- PR18 usa clock_timestamp após locks, janela voluntária imutável, tombstones de expiração/retirada e CLOCK_RECHECK_REQUIRED.
- F02 normaliza UTC, detecta regressão/cronologia e mantém 48h de laboratório separado da janela voluntária S0.

Evidência verificável: E01, E02, E08.

Lacunas concretas:

- Faltam TTL máximo/default, validade do ato humano, janela de contato, versão e fonte de política aprovados.
- 48h e 24h–7d são fixtures; não adotar como regra de Produto.
- Sem política aprovada por classe para alegações/recibos/auditoria/mídia/handles, acesso, expurgo e retenção de tombstones.
- Ausência de JWT/texto de conversa no ledger não certifica minimização de todo o fluxo nem relógio/HA operacional.

**Próxima ação segura:** Produzir tabela normativa por classe de dado e por prazo, com fonte/versionamento, finalidade, retenção/expurgo e efeito na idempotência. Manter constantes de laboratório explícitas.

Decisões/dependências:

- Produto: prazos de negócio, atraso permitido e validade de revisão.
- Privacidade: minimização, retenção, base legal e apagamento versus auditoria.
- Infra/Segurança: relógio confiável e comportamento sob indisponibilidade/retrocesso.

## G07 — Caminho físico integrado F01/F03/F02

**Estado: PENDENTE. Responsável: Codex principal coordena S0/S1; F01/F03/F02 fornecem contratos/fixtures existentes.**

Código e contratos aproveitáveis:

- Suites F01/F02/F03 S2 no CI F02; CFI/registro físico PR18; I79 e G1 existentes.
- A16–A18 e manifest de sete gates já registram o que falta; não reconstruir suítes.

Evidência verificável: E01, E02, E06, E12.

Lacunas concretas:

- Sem jornada comprovada do handover humano real até pedido persistido S0 com quatro testemunhas autênticas.
- Sem teste conjunto de binding recuperado, Gestor distinto, revogação concorrente e versões/cutoff contra fontes atuais.
- Execuções de suites na mesma CI e testes PG com identidades SQL sintéticas não estabelecem essa integração.

**Próxima ação segura:** Após G01 e desenho G02/G03/G04, compor um cenário descartável mínimo reutilizando os testes existentes; registrar recibos e falhas por fronteira, sem Meta real.

Decisões/dependências:

- Codex principal: checkpoint integrado e ordem de composição.
- Produto e proprietários: critérios de homologação operacional posteriores; sandbox local não libera envio.
