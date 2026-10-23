# S0/S1-002 — I52 integração canônica de intake no registro de atribuições

**Data 23/10/2026. Decisão do usuário:** S0 e S1 são da mesma responsabilidade de implementação. Não manter dependência fictícia de "outra frente" para ajustes no próprio repositório. Continuam proibidos merge/deploy, ambiente hospedado e integrações reais Meta/Banco sem autorização.

## Mudança concreta além do mock

Nova migration incremental `supabase/migrations/202610190053_s0_s1_intake_atribuicao_guard.sql` introduz o estado versionado **prumo_private.s1_intake_estado** e eventos mínimos **s1_intake_eventos**, separadamente de `equipe_prumo_s1.estado` (status da conta). A operação `s1_definir_intake` exige executor interno confiável, Gestor da equipe, conta ativa, versão CAS e lock na linha `equipe_prumo_s1`. Não recebe autorização diretamente do navegador: a identidade do Gestor deverá ser derivada de sessão validada pelo backend assinado já explorado no I37.

O novo **trigger S0 canônico** `s0_s1_guard_intake_atribuicao` opera antes de INSERT ou alteração de destino/caso/loja em `public.atribuicoes_humanas`, tabela proprietária da S0. Ele compartilha o lock do estado da conta com a operação de pausa; após adquirir o lock, verifica que o destino está ativo e que intake está habilitado. Assim o bloqueio **não depende do mecanismo S1 de transferência**: gravações diretas da S0, distribuição automática, movimentos manuais e caminhos que convergem ao registro canônico precisam passar pelo mesmo gate. Fechar uma atribuição já existente não é bloqueado pela pausa.

Também desabilitamos as funções S1/048 legadas `s1_pausar_operador_da_equipe` e `s1_reativar_operador_da_equipe` depois do carregamento histórico dos testes: elas suspendiam toda a **conta** e redistribuíam casos indiscriminadamente, comportamento já incompatível com o contrato atual. O histórico dessas migrations foi preservado, não reescrito.

## Testes e limitações

`supabase/tests/s1_076_integracao_intake_canonico_aceite.sql` executa 6 cenários em transação com rollback, sobre o banco PG17 já com S0/001–037 e S1/038–053:

1. Atribuições existentes antes de pausar; 
2. Pausa CAS somente de intake, sem suspender conta ou remover antigo titular;
3. INSERT canônico S0 e transferência manual S1 ambos rejeitam destino pausado e preservam titular;
4. Replay/versionamento/ator sem chefia recusados e trilha enxuta auditável;
5. Consultor pausado mantém leitura/resposta em caso pré-existente;
6. Caminho de pausa global legado bloqueado, retomada habilita nova transferência e titular único.

**Status:** codificado como migration nova e testes integrados PostgreSQL locais; não implantado no ambiente hospedado nem comprovado no serviço S0 em execução real. É avanço real de integração S0/S1 do repositório, **não** apenas mock I49/I50. Ainda é necessário encadear o backend de autenticação GoTrue/assinatura ao executor interno e dar tratamento ao evento real de primeiro contato e fila; ambos já pertencem ao plano de trabalho da mesma equipe de implementação.

## Segurança / próximos testes

- A função administrativa exige `current_user='postgres'` e revoga EXECUTE para `anon`, `authenticated` e `service_role`; **não** constitui RPC autenticado nem serviço produtivo. O contrato de assinatura/identidade não foi liberado ao cliente.
- As fontes canônicas S0 e S1 agora se encontram no **trigger do registro de atribuição**, porém toda atribuição por rotinas privilegiadas ainda deve revalidar autorização externa e exigir idempotência.
- Pausa versus atribuição em sessões reais exige teste transacional complementar em fluxo integrado e retomada do estado após a verificação de histórico. A2 é regra [D] fechada, não mais pendência de produto. Demais critérios G1–G6 do I50 persistem.

## Evidências

Registrar separadamente o SHA do código e workflows efetivamente concluídos antes de declarar aprovado.
