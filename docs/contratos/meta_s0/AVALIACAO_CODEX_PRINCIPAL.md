# Avaliação pelo Codex principal

**Entrega auxiliar pronta para revisão, não para integração.** Versão 0.1-candidate, código 92703c34fd4a2b9bae0d00768969c7c53cc16da3. Branch aux/meta-s0-contracts-20261026, base Meta PR #8 cb7fc3e. A branch existe para comparar propostas; não substitui checkpoint de nenhuma frente.

## Ordem da avaliação

1. Ler CONTRATOS_CANDIDATOS_0_1.md, particularmente fronteiras de identidade, crash window e C1–C7.
2. Conferir EVIDENCIAS.md/JSON e o CI no SHA executável. Contagens 52 novas + 161 preservadas, sete blobs intactos. Não contar os testes históricos PG/GoTrue como execução desta tarefa.
3. Rever diff aditivo contra cb7fc3e: apenas integration/meta_s0_candidate/, docs/contratos/meta_s0/ e workflow auxiliar. Não cherry-pickar FileStore, fixtures de chave ou gates sintéticos para backend/migrations.
4. Avaliar cada contrato independentemente. Marcar aprovado, adaptar ou pendente, com responsável e fontes reais necessárias. Esta entrega deixa todos não ratificados.
5. Reproduzir o modelo sem rede/dependências; depois planejar laboratório físico separado, se autorizado e após ratificação. Não executar integração final a partir deste guia.

## Matriz para revisão

| Contrato | Arquivos executáveis | O que o CI prova | O que ainda bloqueia adoção |
|---|---|---|---|
| DISPATCH-01 | candidate.mjs: reserve/begin; protocol.mjs | Dedupe, ocupação, CAS, gates negativos, begin único e rollback no modelo | Fontes/bindings comerciais, constraints e locks PG reais, handle de transporte e custo de possível não envio |
| DISPATCH-02 | candidate.mjs: observe/read/review | Reuso classificador Meta, incerteza, sanitização, evidência tardia/quarentena, nenhuma liberação | Custódia do transporte, correlação externa confiável, autoridade e UX da conciliação, retenção |
| ACK-03 | protocol.mjs; candidate.mjs: append_batch; lab-store.mjs | HMAC M2M de laboratório distinto, HMAC Meta sintético, lote inteiro, sync antes de indicador laboratorial, duas quedas reais de processo | Principal M2M produtivo, KMS/rotação/TLS, banco/recibo, durabilidade/failover, HTTP ACK e política de rejeição |
| LOCK-04 | lock-plan.mjs; revokeFixture no modelo | Plano total proposto, recusa de inversão, ambas as ordens de corridas serializadas | Inventário de mutadores S1/S0/Meta, modos/locks implícitos, PG17 com dois clientes e direitos reais |

## Experimentos físicos a propor depois da ratificação

Aproveitar a composição temporária/guardada do PR #7 e os checkpoints atualizados do S0/S1; não transplantar SQL histórico nem reabrir as portas seladas. Exigir banco novo, local, PG17 e executor restrito, com teardown, sem credenciais/identidades produtivas.

| Cenário | Asserção necessária |
|---|---|
| Duas reservas mesma chave/slot, duas chaves mesmo intento | Uma ocupação/tentativa; fingerprint divergente conflita; nenhuma segunda execução |
| Dois begins, crash após commit, perda de resposta antes de saber se houve POST | Um vencedor; ocupação persistente; recuperação não faz POST |
| Erro após insert nonce/item/auditoria ou resultado SQL inválido | Rollback de toda unidade; nenhum recibo parcial nem nonce órfão |
| Timeout, 429/503, 2xx malformado e commit externo incerto | Estado incerto consultável; zero reenvio automático, sem falha comercial inferida |
| Transferência S1, retirada de concessão/equipe/atribuição versus reserva/begin, ambas as ordens | Locks efetivos e recheck; quem perdeu nega; sem permissão humana ou técnica substituta |
| Opt-out/cancelamento versus begin/observação tardia | Antes de begin impede; depois conserva incerteza/cancelamento e evidência permitida pela ACL técnica aprovada |
| Revogação/rotação de key/registry durante verificação e append | Mesmo namespace/ordem; resultado validado com revisão viva; principal revogado não escreve nem reconhece |
| Lote com vários itens, um inválido, repetição idêntica, variante física e fora de ordem | Unidade integral; conflito sem substituir original; eventos preservados; status não vira inbound/closure |
| Queda durante commit, ACK perdido, restart/readback | Somente recibo completo durável pode liberar política ACK; fresh proof não duplica itens |
| Locks implícitos, DML nos guards, entrypoints antigos, deadlock/serialization | Privilégios mínimos preservados; lock permitido/DML negado; nenhum retry de transação dispara I/O externo |

## Reprodução da entrega atual

~~~sh
git fetch origin aux/meta-s0-contracts-20261026
git switch --detach 92703c34fd4a2b9bae0d00768969c7c53cc16da3
python3 integration/meta_s0_candidate/verify_sources.py
node --experimental-strip-types --test --test-concurrency=1 integration/meta_s0_candidate/candidate.test.mjs integration/meta_s0_candidate/durable.test.mjs
~~~

O workflow lista o comando das 161 regressões Meta sem duplicar arquivos. Não são necessários npm install, Docker, CLI Supabase, JWT, token Graph ou DSN.

**Pendências para decisão:** C1–C7 no contrato. Nenhuma recomendação deste guia aprova automaticamente merge, deploy, acesso credencial, migration hospedada, transporte real, autorização comercial ou integração final.
