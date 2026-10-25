# Frente OpenAI — situação auditada e estratégia de integração geral (25/10/2026)

**Orientação do responsável (25/10):** concluir boa parte de cada frente separadamente, reconciliar as interfaces de todas, **somente depois montar/integrar os componentes no Supabase hospedado em uma fase concentrada**, previamente aos testes reais. Proibido tratar progresso da fixture PostgreSQL local como implantação. O GitHub Actions com PostgreSQL 17 descartável continua liberado para E04; não criar nem aplicar migrations no Supabase remoto, não trabalhar com cliente real, OpenAI/Meta/Banco real, não fazer merge/deploy automaticamente.

## Artefatos que de fato existem

1. **S0/F03 física E04 (branch `feat/oai-s0-f03-history-port-20261023`, PR #1 Draft):** manifesto do histórico multi-casos da mesma pessoa/loja; conteúdo textual sintético com HMAC S0 persistido; recibos e registros append-only; versões de ficha/catálogo/caso/atribuição/identidade; reserva F03 consultiva; contratos de campos e catálogo sintéticos; aplicação sintética via decisão explícita de gestor S0, CAS de valores anteriores, hash campo a campo, auditoria/rollback; revisão e HOLD triplo de identidade. O F03 **não** escolhe identidade, não aplica diretamente nem recebe direito de acesso por HOLD.
2. **S2/OpenAI lógica de F01, F02, F03 (branch separada `feat/s2-openai-adapter-sintetico`):** `docs/integracoes/openai/e04_offline_lab/core.mjs`, `plan-lifecycle.mjs`, `f03-commit-gate.mjs`, `journey.mjs`, `template-frequency.mjs`, `transport-evidence.mjs`. São funções puras/fixtures que simularam F01 → humano → F03 → eventual F02, planos, templates, transporte e erros Meta. Não possuem credenciais ou execução OpenAI real. Há registro histórico de **212/212** casos em V8 adaptado para cinco suítes, **não** execução integral com `npm test`/CI; o resultado não pode ser somado aos testes físicos S0/F03 como uma única suíte integrada.
3. **Testes físicos certificados na branch S0/F03 atual:** Actions [40181061329](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40181061329), código `04168101245a5717bf01ca5bedd8cd915ea0b89f`, `SUCCESS`, PostgreSQL 17.11: **84/84 S0 + 299/299 F03 = 383/383**, com **195/195** testes físicos F03. Oito novos cenários 188–195 verificaram a recusa de outros leads candidatos por telefone/variante/alias, a escrita bloqueada, o isolamento por concessionária e concorrência. Estes são testes E04 físicos **sobre dados fictícios**, não execução de IA real.
4. **Branches distintas:** F01/F02/F03 lógica da S2 ainda não foi integrada fisicamente com S0/F03, S1, Meta ou frontend. A documentação da S2 contém referências históricas ao repositório anterior e a PR #3; **não afirmar que o PR #3 existe no repositório oficial** sem evidência atual.

## Estado por entrega verificável

| Entrega | Estado hoje | Risco restante |
|---|---|---|
| Regras e propostas F01 | E04 implementado em JS puro, sem atendimento real | estados S0 reais, mensagens, conhecimento, prompt, canais |
| Planos e eventos F02 | E04 JS puro | autorização S0, categorias/templates reais, opt-out, clocks e recibos Meta |
| Histórico textual F03/S0 | E04 PG17 validado | áudio/mídia, retenção, completude sob todos os escritores, proveniência semântica |
| Contratos, versões e CAS campo a campo | E04 PG17 validado | ficha/catálogo reais, aprovação humana ratificada, acoplamento do adaptador de propostas |
| Identidade multitelefone e disputa | E04 com HOLD e proteções de candidatos | resolução final legítima, fluxos de revisão/recuperação com regras de negócio |
| Jornada funcional interfrentes | apenas simulada em JS puro | juntar front, S0/F01/F02/F03/S1/Meta sem conceder autoridade à IA |
| Suite original de aceite E02 — 70 SYN | oráculos documentais, sem homologação integral | execução e gabaritos oficiais, regressões e métricas de qualidade |
| APIs/modelos reais, credenciais e custo | não iniciados/fora de E04 | E05 e aprovação separada, parâmetros custos e segurança |
| Supabase hospedado e testes reais | **adiado por decisão atual** | integração geral somente depois dos gates E04 e aprovação do responsável |

## Como aferir a distância sem porcentagem fictícia

**Núcleo transacional S0/F03 em E04: avançado**; não é o mesmo que F03 ponta a ponta. **Frente OpenAI completa: ainda em desenvolvimento relevante, não em fase final**: lógica offline existe para F01/F02/F03, porém não existe validação física unificada, execução real de modelos, mídia, integração S0/S1/frontend/Meta ou aprovação E02 completa. **Plataforma pronta para piloto real: distante**, por definição condicionada às outras frentes e à instalação posteriormente planejada.

Evitar estimativa numérica de término sem contagem estável de entregáveis e sem evidência de integração. O número de testes mede regressão de funcionalidades presentes, **não porcentagem da frente**. Atualizar o mapa por gates tecnicamente verificáveis.

## Próximos gates estritamente offline (sem Supabase remoto)

**G1 — Validar contratos lado a lado:** conferir os envelopes JS E04 de proposta F03 contra recibos, versões, identidade e campos S0 físicos, sem tratar booleans de fixture como sessão real.

**G2 — Evidência/mídia e privacidade:** classificação de texto/áudio/anexos, disponibilidade de transcrição, cutoff, retenção e minimização LGPD; quando faltar prova, recusar.

**G3 — Regresso end-to-end offline:** executar `npm test` nativo (branch S2), física PG17 (branch S0/F03), criar ensaios integrados via adaptadores S0 simulados com provas autenticadas, executar os 70 oráculos E02 e matriz adversarial. Não somar suítes desconexas como teste único.

**G4 — Ratificar interfaces com S0/S1/Frontend/Meta:** tipos de retorno, elegibilidade de operador/gestor, consentimento, categorias/template, cadastro, catálogo e quem tem autoridade de escrever. Nenhuma F03 aplica unilateralmente.

**G5 — Preparar pacote de integração geral:** migrations **apenas versionadas e revisadas**, migração ordenada, segurança/RLS, idempotência, rollback, checklist GO/NO-GO, plano de compatibilidade de dados; aplicação ao Supabase hospedado **apenas após decisão posterior do responsável**.

**G6 — E05/produção:** credenciais, cobrança, APIs reais, automações, conformidade, canais e dados reais são fase futura condicionada a aprovações separadas; não estão autorizados pela decisão de manter o Supabase para depois.

## Ponto desta execução

Remediação de colisão de identidade para reserva F03, leitura de contrato e CAS humano em `backend/s0_f03_identity_uniqueness_local.py` e callers; serialização com escritores S0 do mesmo tenant; 8 cenários físicos novos aprovados. Commit certificado `04168101245a5717bf01ca5bedd8cd915ea0b89f`. Nenhum efeito externo.
