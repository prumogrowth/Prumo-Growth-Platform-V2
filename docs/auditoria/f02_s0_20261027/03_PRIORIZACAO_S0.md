# Próximas implementações S0 — proposta para o principal

Sequência condicionada à revisão do Codex principal. Esta auditoria implementa somente documentos e verificação; nenhuma proposta abaixo é ordem para alterar outra branch ou autorização para operação.

| Ordem | Trabalho | Aproveitar | Critério de aceite proposto |
|---|---|---|---|
| P0 — em andamento | Preservar I79/G2 como prioridade: regularização explícita do legado e continuidade administrativa já previstas | PR #26, mesma equipe/cargo/chefia, competência de Diretor, GoTrue/nonce/auditoria e I61 | Evolução versionada pelo principal; sem inferir cargo de grant/subordinados, sem reabrir D1/A2 funcionais |
| P1 — decisão de interface | Resolver G01 e recorte D3/D4 de G02 | Result 0.1-candidate, request interno, três módulos F02 preservados | Versão aprovada, compatibilidade e depreciação documentadas; distinguir captura, pedido e ato humano; flags de envio falsas |
| P2 — recuperação técnica | Lookup server-owned mínimo do binding/documento no caminho S0 existente | Recibo/auditoria CFI, `f02_review_requests_local`, `claimed_body`, janela e tombstones | Queda/restart sem binding em memória; mesma chave e prazo; principal vivo, negativa interloja/caso/sessão; nenhum segredo em UI/F02 |
| P3 — proveniência | Adaptar validação das quatro provas após mapa aprovado G03 | Produtores locais F03/C08/origem/intenção existentes | Rejeição de prova ausente, trocada ou obsoleta; identidade/cutoff/versões comprovadas por fonte; não promover digest |
| P4 — ato humano | Implementar somente após desenho aprovado G04 sobre I79 vigente | Cargo/chefia/competência, concessões e exceções existentes, sessão e auditoria | Gestor distinto com acesso legítimo; aprovar/negar/revogar expirável; CAS e corridas com troca de chefia/logout; sem reutilizar sessão do capturador |
| P5 — política e última milha | G05/G06: decisões de domínio em paralelo, implementação após contratos aprovados | C1–C7, T1–T6, classificadores Meta e relógio/tombstones S0 | Fontes autoritativas de consentimento/opt-out/template/disposição, política versionada e retenção; principal M2M separado; sem chamada comercial nesta etapa |
| P6 — composição | Jornada G07 descartável e homologação posterior separada | Suites existentes, mesmo runtime e ledgers; sem duplicar banco/identidade | Recibos por fronteira, negativos e concorrência comprovados; laboratório não vira liberação comercial |

P3 e decisões de P5 podem avançar documentalmente enquanto P0/P1 são resolvidos. P4 depende da identidade/chefia atual e de acesso legítimo ao pedido; não se deve contornar G02 para acelerá-lo. A18 e envio não são pré-requisitos para registrar um pedido técnico de revisão, mas permanecem bloqueios independentes para operação.

## Adaptações exatas a revisar, sem implementação nesta etapa

**Recuperação:** estender o caminho de `S0F02ReviewRegistryLocal.execute` e `S0CFI01F03ReceiptBridgeLocal` com resolução interna aprovada. Resolver o recibo integral e o documento original a partir dos ledgers atuais, incluindo a chave da captura, snapshot/watermark/contagem/atribuição/ciclo e a janela original. Não usar o hash F02, `review_ref` ou `revision` como credencial. O cliente não pode fornecer principal, cargo, sessão, HMAC ou reconstruir `S0F03BoundReceiptLocal`. O contrato atual impede novo login/Gestor: continuidade exige uma decisão explícita; não substituir a sessão antiga por outra no recibo. A resposta ao consumidor deve ter origem autenticada pelo transporte escolhido, sem ampliar o payload visual.

**Proveniência:** manter os quatro campos alegados compatíveis com o candidato; definir referências/versionamento numa evolução revisada, em vez de reinterpretar silenciosamente os hashes como provas. Selecionar o recibo final F03 correto e leitores mínimos dos produtores C08/origem/intenção. Esses leitores devem revalidar fontes/cutoff sob protocolo de concorrência aprovado, sem importar automaticamente os adaptadores inteiros da F02 nem abrir acesso privilegiado ao frontend.

**Ato gerencial:** usar as fontes I79 existentes de cargo/chefia/competência e os direitos sobre loja/caso/atribuição. `S1ProfessionalsLocal` é administração, não API de aprovação F02. Propor ato durável ligado a `review_ref`, revisão/documento/provas, principal verificado, decisão, finalidade, validade e versão de política, com auditoria e idempotência; negar caso sem fonte ou permissão. A regra de ratificador distinto e o efeito da troca de chefia ainda precisam aprovação. O novo ato não deve reutilizar os estados administrativos APPLIED como aprovação comercial nem alterar a semântica dos 13 estados review-only existentes sem versionamento.

**Concorrência:** inventariar namespaces, modos, FKs/triggers e revogadores dos objetos efetivos antes da nova transação. Preservar a comparação precommit do PR #13 e a ordem atual CFI→ledger F02; incluir as mudanças I79/I61. LOCK-04 modelado não prova ordem PG global. Não afrouxar guards/owners para fazer a composição passar.

## Lacuna independente e segura para revisão posterior

Adicionar, no laboratório integrado que o principal controla, cenários F02 **depois** de instalar I79: registro/leitura/retirada com cargo explícito, negativa para legado sem cargo quando aplicável ao direito aprovado, mudança de supervisão/chefia e revogação concorrente. Reutilizar `integration/f02/test_authoritative_review.py` e o workflow I79 atual, observando que os 56 cenários atuais rodam antes do delta. Primeiro definir os direitos esperados; não inventar a regra de acesso no teste. Sem novas portas ou mudança de núcleo para essa preparação.

## Cenário mínimo G07 proposto

1. Evento humano/handover do produtor F01/S0 existente, com IDs e ordenação aprovados; nenhuma flag criada pelo auditor.
2. Captura CFI autenticada e recheck no encerramento/cutoff físico; F03 usa conteúdo autorizado/minimizado e retorna o recibo selecionado no mapa.
3. C08, origem e intenção são resolvidos nas fontes correspondentes; tentativa já reservada continua externa incerta.
4. F02 prepara proposta/handoff; S0 registra somente revisão com prova de contexto e, após evolução aprovada, fontes verificadas.
5. Simular perda de resposta/processo e recuperar pela chave original após nova prova; testar retirada/expiração persistidas e janela imutável.
6. Quando houver ato G04 aprovado, executar Gestor distinto legítimo e negativas de autor, equipe/loja errada, chefia alterada e sessão revogada, com duas conexões nas duas ordens.
7. Falhar após nonce/auditoria e antes/no COMMIT; confirmar atomicidade, indisponibilidade sem falso rollback e limpeza da stack. Nenhum passo envia mensagem, chama Graph ou habilita agendador.
