# E04 — F01/F03 rota múltipla vinculada à revisão F02 (candidato)

**Data:** 27/10/2026. Referência: `a69f601` CI #40584729728 SUCCESS, 1.167 testes; matriz F02-A30. Este incremento **não** repete auditoria nem modifica S0.

O controlador `backend/f01_f02_f03_route_ledger_candidate.py` já aceita várias sequências, inclusive F01→F02→F01→F03→F02. Porém, uma rota internamente coerente não comprovava que seu **último encerramento humano** era o mesmo da prova F03 e do pedido F02.

Novo módulo `backend/f02_multiroute_proof_gate_candidate.py`: `check_routed_posthuman_proof(scope, events, evidence, proposal, window, packet)` **reutiliza os validadores existentes** `classify_route_candidate`, `prepare_handoff` e `inspect_claimed_proof_binding`. Exige etapa final F02 pós-humano, marcador F03 anterior e encerramento mais recente, IDs coerentes de concessão/lead/caso/encerramento, igualdade de instante UTC do fechamento alegado e cronologia de solicitação/janela, e compara as quatro provas alegadas ao pacote F02.

Recusa reuso de encerramento humano anterior, caso diferente, tempo divergente, alteração de hash, mudança da proposta ou da janela. Um `CUSTOMER_INBOUND` após o plano pós-humano muda a fase para revisão de retomada humana, não abertura automática de F01. Nenhum ator externo ganha permissão por isso.

**Resposta positiva `F02_ROUTE_AND_PROOF_SHAPE_RECHECK_ONLY` significa apenas compatibilidade entre três declarações não autenticadas.** Não é recibo real F03, HMAC S0, aprovação S1, opt-in, autorização Meta, envio ou confirmação de entrega. Todos os eventos e hashes podem ser falsificados. G01–G07 permanecem abertos; homologação física depende de S0/Meta e dos contratos específicos.

Testes: `backend/tests/test_f02_multiroute_proof_gate_candidate.py`, 24 casos novos incluindo múltiplas rotas válidas, resposta tardia, troca de closure/tenant/case, alterações de versão/janela, fonte falsa e cronologia. Nenhuma API, rede, banco, segredo ou cliente real.

**Continuidade:** adaptar a parte restante da jornada às funções JS F01/F02/F03 `validateF01`, `validateF02`, `prepareF03History`, `validateF03Proposal` da S2 fixada em `ebf6fe4`. Essas funções não foram chamadas por este módulo Python; ainda não há integração total de runtime entre Python/Node/S0 físico. O código atual cobre unicamente compatibilidade de rota com validação F02 das quatro provas. O PR permanece Draft sem merge/deploy.
