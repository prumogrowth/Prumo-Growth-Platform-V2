# S0 + S1-002 / I55 — API assinada de consulta e assunção da fila

**23/10/2026.** Continuidade do I54; S0 e S1 são implementadas pela mesma frente. Ambiente de teste **somente CI local descartável**, sem deploy, merge, WhatsApp, cliente real ou bancos externos.

## Integração

O I54 criou a fila na S0, mas ela ainda não dispunha de API autenticada. I55 acrescenta um gateway HTTP de loopback em `backend/s1_gateway_fila_canonical_local.py`, que valida Bearer de GoTrue e só aceita dois comandos, ambos POST:

- `/s1/fila`, corpo exatamente `{"loja_id":"<UUID>"}`: retorna no máximo 25 itens pendentes com **apenas** `concessionaria_id`, `lead_id`, `ciclo_id` e `versao`. Não retorna telefones, mensagens ou casos de outras equipes; Gestor deve estar ativo e possuir grant vigente para aquela concessionária.
- `/s1/assumir_fila`, corpo `{"loja_id":"<UUID>","ciclo_id":"<UUID>","versao_esperada":1}`: registra assunção **no comando S0 canônico**, com lock no lead, versão CAS, novo caso e atribuição em transação e trilha de auditoria. `CONFLICT` ou caso já criado respondem HTTP 409. Nunca delega um papel administrativo, destinatário ou ator a partir do corpo HTTP.

**Assinatura e autoridade:** domínios separados `FILA55L` e `FILA55C` com identidade ator/sessão verificada independentemente pelo assinador, loja/ciclo/versão assinados, HMAC conferido exclusivamente no custodiante I22 e nonce consumido pelo executor I21 (role NOLOGIN). A ponte PostgreSQL, owned por postgres, confere novamente `auth.sessions` viva, ator cadastrado, alçada de Gestor e delega a assunção ao `prumo_private.s0_fila_assumir` do I54. A sessão ou chave revogada impede nova operação; sem concessão da loja não há listagem nem assunção. Funções internas e tabela de fila permanecem fora de `authenticated` e do login SQL do gateway.

## Limites e validação

`supabase/tests/s1_079_fila_assinada_canonica_local_only.sql` instala o **protótipo de serviço assinado I55** dentro da stack Supabase CLI efêmera, após migrations S0/S1 053 e 054; não é migration pública em produção. A suíte `scripts/test_s1_002_i55_signed_queue_e2e.py` usa o gateway GoTrue/HMAC I37/I53 com oito cenários de aceitação: evento S0; projeção mínima; escopo multi-loja; schema HTTP estrito; claim/CAS e owner único; nonce; revogação de grant no mesmo JWT; impossibilidade de SELECT/RPC direto. `tests/test_s1_002_i55_queue_gateway.py` inspeciona assinaturas e entrada HTTP.

**Ainda não homologado:** implementação distribuída e HTTPS da borda, sessão persistente e KMS/isolamento de hosts, reconciliação de pendência quando outro produtor cria caso, comprovação de primeiro contato/delivery, UI, D2/D3/D4, F03, produção Meta/Banco e aprovação LGPD. Os resultados dos testes serão adicionados após validação no GitHub Actions. A2 segue fechada: Consultor pausado jamais recebe novo atendimento, inclusive manual.

## Evidências

**Código entregue e ainda NÃO homologado**, 23/10/2026:

- Commit de implementação `0560175332668d1c2c0cb6dfcc0388f7923b4dd5`, seguido de `4aa8cfa30e75b2f2ff04b854a1035a9c5bdab97c` (consulta da fila com `FOR SHARE` na equipe, concessão e loja, serializando revogação durante leitura; rejeição explícita de HMAC nula).
- [GoTrue/E2E #40039146985](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40039146985) e [PG17 #40039147068](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40039147068): **FAILURE sem qualquer etapa registrada nos jobs e logs do job indisponíveis (404 BlobNotFound)**. Reexecução via API solicitada, mas novamente não houve passos com evidência. Não se pode inferir falha ou êxito da implementação.
- Após correção pontual, [E2E #40039422379](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40039422379) e [PG17 #40039422319](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40039422319) também **FAILURE antes de qualquer etapa**. Isto caracteriza bloqueio de validação por infraestrutura/execução do Actions ou outra causa ainda não identificada, **não uma regressão de negócio comprovada**.
- Testes escritos e conectados ao workflow: `tests/test_s1_002_i55_queue_gateway.py` (8 unitários de esquema/assinatura) e `scripts/test_s1_002_i55_signed_queue_e2e.py` (8 cenários GoTrue reais locais). **Não declarar 8/8 aprovado** até obter saídas individuais e conclusão SUCCESS do CI.
- I54 permanece a última camada **de fila** com validação positiva (8+2 testes PG17, 16/16 workflows na evidência I54). I55 é uma implementação adicional sujeita à execução e auditoria de segurança. Não houve merge, deploy ou acesso a Meta/Banco.

**Próxima atividade do mesmo responsável S0/S1:** recuperar a execução dos runners GitHub Actions e confirmar a ponte assinada no GoTrue efêmero; depois finalizar reconciliação de filas obsoletas, hardening de sessão/revogação e UI.

## I55.1 — defesa adicional na borda (24/10/2026)

A resposta do executor assinado agora passa também por uma **allowlist de saída** do gateway: a listagem só permite 25 itens e exatamente quatro campos UUID/versão por item; a assunção só permite o resultado e IDs/versionamento esperados. Uma futura mudança não auditada do `SECURITY DEFINER` não pode encaminhar telefones, mensagens ou campos extras automaticamente. Qualquer resposta divergente falha fechada em HTTP 503. Erros transitórios do PostgreSQL como `40001`/`40P01` não são tratados como proibição HTTP 403: exigem recuperação ou retry seguro. Foram adicionados testes unitários de contrato para saída e mapeamento de erros. **Aprovação E2E permanece pendente até execução verificável.**

## Diagnóstico E2E no novo repositório (24/10/2026)

A primeira execução com Actions operante no espelho ([#40082201339](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40082201339)) aprovou os 11 testes unitários do I55 e chegou à S0 real (\`PASS S1QUEUE-157\`), mas a primeira consulta autenticada retornou HTTP 403. A causa identificada no fixture foi **a ausência de concessão de Gestor à loja**: o cenário histórico I37 vinculava o Gestor à equipe sem criar um \`vinculos_papel_escopo\` de papel \`gestor\` para a concessionária. A política I55 exige corretamente ambas as condições. O fixture E2E foi atualizado para conceder explicitamente esse escopo sintético ANTES da consulta, sem alterar a regra de segurança. A reexecução completa é necessária para confirmar o resultado.
