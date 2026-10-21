# S0/CFI-01 — verificação S1 na mesma transação e ordem dos bloqueios

**21/10/2026 · Escopo: PR #12 Draft, branch S0 aditiva.** A própria frente OpenAI está desenvolvendo os incrementos S0 necessários. Nada aqui autoriza merge, deploy, produção, Meta, Banco ou chamada OpenAI paga.

## O problema corrigido

A primeira versão de `s0_human_closure_event_local.py` travava `casos_humanos` / `atribuicoes_humanas` ANTES de consultar a S1. No contrato I13, a S1 trava equipe ANTES do caso. A ordem invertida abre risco de **deadlock** entre conclusão humana e redistribuição/alteração de titularidade da S1.

A nova sequência do protótipo **na mesma transação e mesmo cursor** é:

```text
GoTrue verify → auth.sessions FOR KEY SHARE
→ S1 equipe_prumo_s1 [ativo] FOR SHARE     (lock_team)
→ S0 casos_humanos/ciclo/loja/atribuicao FOR UPDATE
→ S0 vinculos_papel_escopo FOR SHARE
→ S1 verifica vinculo exato atribuicao+loja+caso+operador (check)
→ S0 conversas do caso FOR UPDATE
→ S0 mensagens do caso FOR SHARE
→ S0 fingerprint + chave idempotente → fixture local de evento técnico
```

**Objetos do código:**
- `backend/s0_s1_closure_authority_local.py`: `S0S1LocalTeamAuthority.lock_team` valida que o ator **já verificado pela S0** está em `public.equipe_prumo_s1` com `estado='ativo'`, e trava a linha via `FOR SHARE` antes do caso. `check` revalida escopo de atribuição em `public.atribuicoes_humanas` e concessão em `public.vinculos_papel_escopo` na mesma transação.
- `backend/s0_human_closure_event_local.py`: exige a chamada `lock_team` antes da consulta do caso. Sem implementação S1, o fluxo continua bloqueado. `_MESSAGES` agora usa `FOR SHARE OF m` para proteger as linhas de mensagem existentes contra atualização concorrente enquanto se calcula SHA-256.
- `backend/tests/test_s0_s1_closure_authority_local.py`: 20 testes novos que cobrem equipe ausente/inativa, atribuição/caso/loja diferentes, concessão revogada, tipos inválidos, ordem S1→S0 e a execução da porta real local por cursor simulado.

**Dependência obrigatória:** o branch-base `feat/s0-fundacao-prumo` não contém `public.equipe_prumo_s1`. Ela é criada na migração `supabase/migrations/202610180038_s1_equipe_prumo_gate.sql` do PR #5 da S1, que **não foi mesclado**. Em ambiente S0 sem essa tabela, a consulta falha, retorna `UNAVAILABLE` e não grava evento. **Não criar uma tabela alternativa com esse nome nem aprovar a aplicação de migrations S1 em produção sem revisão**.

**Limite de elegibilidade:** esta porta só considera **operador/gestor com concessão NORMAL de loja**. A exceção S1-002 `s1_excecoes_55` por caso/atribuição (fixture 055, não migration de produto) é conservadoramente recusada pelo gate normal `_GRANT`. É preciso desenhar e homologar uma checagem específica com prova estrita por caso antes de contemplar essa exceção. Pausa de intake não equivale a conta suspensa nem invalida casos sob titularidade preservada.

## Prova e estado

**93/93 PASS, Python local, na mesma execução**:
- 33 testes anteriores de pré-verificação S0;
- 40 testes de evento técnico de conclusão, incluindo 5 testes adicionais sobre ordem de locks e integridade do recorte;
- 20 testes de verificação S1 com curso de execução simulado.

`python -m compileall -q backend` PASS. Comparações Git blob dos artefatos publicados: código evento `37d92335074337408ecf34a5e35a97f45ca5bf6b`, teste evento `0f8b79d125ce5b8a72baf77e5f0d902f98ff435c`, novo S1 `93e759db498cabe7127d2b83f88168a6f7a60634`, novo teste S1 `6b8ab7fcf6f1b82d0f3def76310591c2c881e1c1`.

**Limitações:** esses são testes unitários com `Principal`, cursor e S1 simulados, não execuções PostgreSQL/GoTrue reais. Não existe `postgres`, `psql` ou Docker disponíveis na sessão de laboratório; não declarar que bloqueios SQL ou ausência de deadlock foram **comprovados fisicamente**. Regressão OpenAI anterior (220) e as sete suítes F03 históricas (210) **não** estão somadas nem executadas como parte desses 93.

## Próxima verificação física necessária

Em ambiente descartável e isolado com PostgreSQL 17 + GoTrue, aplicar o baseline S0, depois a migração S1 038/ordem de dependências S1 necessária, depois a fixture manual `supabase/tests/s0_cfi01_human_closure_table_local_only.sql`. Sem aplicar ao Supabase hospedado. Fazer dois clientes concorrentes para confirmar:
1. S1 desativa/transfere o operador versus pedido de conclusão sob locks compatíveis;
2. Novo inbound/atualização de mensagem versus leitura do snapshot e hash;
3. Dois pedidos de conclusão com a mesma chave e com chaves diferentes;
4. Concessão de loja, sessão ou titularidade revogada, acesso a outra concessionária;
5. Falha depois de inserir evento e antes de commit, rollback integral;
6. Sem schema S1 instalado, nenhuma captura e nenhum privilégio elevado.

Só após prova física avançar a `begin/recheck` S0/integração com F03 OAI-05/OAI-07 e aplicação de campos. Mesmo assim, seguirão pendentes a assinatura de contrato e autorização real de serviço com privilégio mínimo. **A pausa para dúvidas e auditoria documental geral deve ocorrer depois dos dois marcos combinados; não agora.**
