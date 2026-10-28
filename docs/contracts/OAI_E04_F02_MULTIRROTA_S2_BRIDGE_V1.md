# E04 — F01/F02/F03: execução dos validadores originais S2 em rotas múltiplas

**Data:** 28/10/2026. **Checkpoint anterior:** F02 `7a4473d`, CI #40616632413 SUCCESS (1.191/1.191). **Domínio:** OpenAI F01/F02/F03; S0 somente leitura. **Natureza:** laboratório, sem autenticação operacional.

## Incremento A32

O módulo `backend/f02_multiroute_s2_validation_candidate.py`, função `check_routed_proof_with_pinned_s2`, usa diretamente o resultado de `check_routed_posthuman_proof` (A31), que já reutiliza `classify_route_candidate`, `prepare_handoff` e `inspect_claimed_proof_binding`.

Somente quando a rota, último encerramento humano, pedido F02 e as quatro provas alegadas são estruturalmente coerentes, ele constrói a sequência completa de **visitas** `F01`, `F02`, `F03` a partir dos eventos. Exige exatamente um pacote de candidato por visita e sua ordem original. Antes de chamar S2, compara os identificadores de loja/caso da entrada ao escopo da rota, a correspondência de `closureId` da F03 ao evento, e a separação entre F02 pré-humano (`seller_ai`, `pre_human`) e pós-humano (`human`, `post_human`). A escolha de template/versão pós-humano precisa corresponder à proposta F02 de laboratório.

**Código S2 original utilizado, sem cópia de lógica:** `docs/integracoes/openai/e04_offline_lab/core.mjs`, do commit fixado `ebf6fe4e546f2fe990bdaefe2df25aa0cf18e74c`, já obtido no GitHub Actions da própria branch. O adaptador Node `backend/tests/s2_pinned_route_validator.mjs` importa **esse checkout**, executa para cada pacote `validateF01`, `validateF02`, `prepareF03History` e `validateF03Proposal`, e devolve apenas os rótulos de resultado. Nenhum retorno de `PROPOSED` significa atendimento executado, texto enviado, ficha aplicada, consentimento, reconciliação física ou ratificação S0.

Uma rota positiva só retorna `MULTIROUTE_AND_S2_SHAPE_RECHECK_ONLY` quando **todos** os validadores da S2 devolvem `PROPOSED` e os vínculos anteriores também estão corretos. `DENIED`, `STALE`, `SOURCE_INVALID`, `REVIEW_REQUIRED`, falha de processo Node, falta do checkout fixado, pacote inesperado, cross-tenant ou troca de encerramento **não** conseguem conceder capacidade.

## Fronteiras e riscos conhecidos

- A origem do login, o fechamento humano, o histórico, as versões e as autorizações de cada pacote são **fixtures sintéticas**, mesmo quando um campo se chama `authenticated`. A verificação local não autentica a fonte e não transforma booleanos em provas S0.
- Os testes invocam o **Node real** com o JS S2 original fixado, além do código Python F02. Não se trata de tradução Python da lógica S2. A importação estática depende do checkout `.s2-e04-source` já feito pela workflow `.github/workflows/s0-f03-pg17.yml` — execução fora desse ambiente **falha fechada** se o checkout estiver ausente.
- Uma recomendação F03 de desistência/perda (\`commercialAdvisory\`), mesmo que estruturalmente \`PROPOSED\` pelo validador isolado S2, **não dispara F02**: permanece em revisão humana, coerentemente com a guarda do \`journey.mjs\`.\n- O vínculo do template/versão é candidato, sem recibo assinado, política comercial oficial ou fonte autoritativa. Os IDs físicos de `personId` e `leadId` não são equiparados por inferência; somente um `synthetic_person_id` informado independentemente é confrontado com a F03. A S0 deve fornecer mapeamento canônico posteriormente.
- O escopo deste checkpoint é o **resultado F02 pós-humano** após uma ou mais visitas pré-humanas e F03. Não é motor universal de todas as rotas de produção; não liga o Node a serviços hospedados, Meta nem modelos OpenAI reais. Não há replay físico unificado nem decisão S0.
- G01–G07 permanecem não homologados; a arquitetura-alvo continua backend no Supabase + OpenAI API diretamente, n8n opcional. Nenhum merge, deploy, contratação ou migração.

## Testes

`backend/tests/test_f02_multiroute_s2_validation_candidate.py` adiciona 27 casos com rota simples e não linear positiva, S2 Python→Node, F01 stale/source inválida/retorno, F03 cutoff/closure/conflito, F02 pre/post humano e template, escopo cruzado, omissão/reordenação de etapas, falta da fonte fixada, prova F02 alterada, resposta após recontato e proibição de ação/autoridade. Os testes são incorporados ao runner `scripts/run-s0-f03-pg17-local.sh` e executam o código JS S2 pinado pelo mesmo workflow.

**Aceite A32:** `LAB_VERIFIED` somente depois de CI SUCCESS no commit definitivo. Limite de evidência: composição com **validações do laboratório S2**, não OpenAI SDK, Meta, aplicação de negócio, sessão real ou decisão humana.
