# S0-037A — Gate de privilégios comerciais legados, sem rebaixamento de proprietário

**Data:** 18/10/2026. **Escopo:** análise de dependências e ensaios negativos na branch `feat/s0-fundacao-prumo` do PR #1. Esta etapa **não introduz migração** nem faz transferência de proprietário. A migration numerada 037 que já existe é exclusivamente o reparo **S0-036A** de ACL. Não reutilizar esse número. Todos os ensaios SQL são `BEGIN; ... ROLLBACK;` no PostgreSQL 17 descartável.

## Baseline e hipótese examinada

No baseline auditado até S0-036A:
- `gateway_cancelar_plano_assinado_s0` e `gateway_conciliar_c07_assinado_s0` são `SECURITY DEFINER` com owner `prumo_s0_signed_executor`, sem login, BYPASSRLS ou DML comercial direto.
- Elas exigem validação HMAC de curta duração, nonce irrepetível por `prumo_s0_signer`, depois chamam apenas `gateway_cancelar_plano_s0` ou `gateway_conciliar_c07_s0`.
- **As duas wrappers comerciais legadas são `SECURITY DEFINER postgres`**, com `search_path` vazio, e validam uma `auth.sessions` ainda vigente, assinatura de operação pela camada externa, alvo, versão e a saída de domínio antes de gravar a auditoria de gateway.
- As rotinas subjacentes `cancelar_plano_gestor_sintetico` e `conciliar_pendencia_c07_sintetica` são `SECURITY INVOKER` e verificam logo no início `current_user<>'postgres'` → `INTERNAL_ONLY`. Isso é **dependência funcional explícita da identidade efetiva do owner**.

### Cadeia real de funções

| Caminho | Ponto privilegiado | Leitura/escrita de domínio e restrições |
| --- | --- | --- |
| Cancelamento C08 | `gateway_cancelar_plano_s0` (postgres) | `auth.sessions` em lock `FOR KEY SHARE`; checagem de gestor/loja; `leads_loja` e `planos_recontato_sinteticos` em `FOR UPDATE`; `envios_template_sinteticos` UPDATE; inserção em `eventos_envio_template_sinteticos`; escrita em `auditoria_gateway_s0` |
| Reconciliação C07 | `gateway_conciliar_c07_s0` (postgres) | `auth.sessions`; gestor/loja, pendência e versão; `pendencias_reconciliacao_c07_sinteticas` em lock; callback, envio, plano e lead; associação fictícia opcional; auditoria; bloqueio de retry automático |
| Prova de chamada | `gateway_validar_prova_s0` (prumo_s0_signer) | chave privada HMAC e nonce, papel restrito distinto; não muda estado comercial |
| Entrada assinada | `gateway_*_assinado_s0` (prumo_s0_signed_executor) | apenas `EXECUTE` no verificador e nas duas wrappers legadas; sem DML nem acesso direto a `auth.sessions` |

É insuficiente executar `ALTER FUNCTION ... OWNER` nas duas wrappers legadas. Sem alterações das rotinas de domínio, o novo `current_user` falha no guard `INTERNAL_ONLY`. Mesmo corrigindo esse guard, o novo proprietário **não tem** SELECT/locks em `auth.sessions`, SELECT nas entidades sob RLS, UPDATE nas transições comerciais, nem INSERT na trilha de auditoria. Conceder `BYPASSRLS`, `SUPERUSER` ou permissões irrestritas violaria o objetivo. Mover o acesso comercial para outro `SECURITY DEFINER postgres` escondido não elimina a dependência, apenas a desloca.

## Evidências implementadas

Arquivo `supabase/tests/s0_037a_gate_owner_comercial.sql` (executado pelo runner local seguro; nenhuma migration alterada):
- **OWNER37-01:** identifica owner `postgres`, `SECURITY DEFINER` e `search_path` vazio das duas wrappers legadas; identifica `SECURITY INVOKER`, proprietário e guards `INTERNAL_ONLY` nas duas rotinas de domínio;
- **OWNER37-02:** verifica que `prumo_s0_signed_executor` ainda pode delegar às wrappers, porém não pode consultar sessão/lead, escrever planos/reconciliação/auditoria nem chamar diretamente as rotinas comerciais;
- **OWNER37-03:** cria **somente dentro de transação revertida** um papel probe `NOLOGIN NOINHERIT NOBYPASSRLS`, concede temporariamente EXECUTE nas duas rotinas invoker e confirma rejeição exatamente `INTERNAL_ONLY`, antes de qualquer mutação;
- **OWNER37-04:** fornece no ensaio SELECT para o papel probe e um lead sintético preexistente na transação; comprova que, mesmo com grant SELECT, a política RLS para `authenticated` não abre registros ao papel técnico sem política própria. **É prova de RLS do lead, não teste de toda a cadeia transacional.**
- **OWNER37-05:** guardas negativos de ausência de login/BYPASSRLS e de filiação indevida do papel temporário.

O SQL é `BEGIN`/`ROLLBACK`; não deixa role, GRANT, lead, concessionária, sessão ou dado persistido no banco descartável. `scripts/run-s0-local.sh` inclui esse arquivo no fluxo PostgreSQL 17. As suítes GW, OWNER-01..06, AUD-036A, C01/C02/C07, Auth/REST anteriores não são alteradas.

## Parecer de viabilidade e exigências da migração real

**NO-GO para transferir owners neste incremento.** A mudança real exige, numa migration independente ainda não aprovada:
1. Matriz de privilégios **por tabela/coluna** e políticas RLS explicitamente escopadas por operação/loja/sessão, com testes de impersonação, conflito de versão e cancelamento simultâneo;
2. Evoluir o guard de domínio sem confiar apenas em `current_user`, preservando autorização forte, mas sem dar EXECUTE direto a operadores ou ao gateway sem HMAC;
3. Privilégios mínimos necessários para `auth.sessions` e locks, sem ampliar leitura de JWT/sessão nem eliminar revogação imediata; permissões para trigger/sequence e auditoria versionada;
4. Regressões negativas para `anon`, `authenticated`, `service_role`, `prumo_s0_gateway`, `prumo_s0_signer` e executor; verificações reais na stack GoTrue/PostgREST local gerenciada, além de PostgreSQL 17;
5. Desenho que não conceda `BYPASSRLS` nem operações irrestritas entre concessionárias; provar que `SECURITY DEFINER` residual `postgres` não reaparece disfarçado.

Não avançar para execução comercial, novos RPCs, contas SQL, credenciais reais, Meta/Graph/Banco, produção, merge de PRs ou banco hospedado. DEC-WA-01/02/03 e DEC-WA-05 permanecem aprovadas; DEC-WA-04/06 e a semântica de evento C07/WA-01C permanecem pendentes e não bloqueiam este estudo sintético.

**Aceite e evidências:** preencher com SHA/run real somente após finalizar o CI deste incremento. Até lá é documentação de engenharia, não homologação da transferência.
