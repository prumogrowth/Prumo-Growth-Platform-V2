# Prumo — Fronteira de identidade do backend S0 (17/10/2026)

**Status:** protótipo interno validável, sem servidor HTTP exposto, sem implantação Supabase remota e sem operação com dados reais. Não é a solução final de autenticação de produção.

## Motivação e fontes normativas

- Documento `26_Contratos_Conceituais_Eventos_APIs`, §1/2 e C08/C23: identidade individual autenticada e produtor real, autorização por loja/papel/estado/versão e deduplicação; **identidade declarada pelo modelo ou cliente não é credencial**.
- Documento `40_Contratos_Interfaces_Campos_Operacionais_Rastreabilidade`, INT01/02/09: identificação obtida do servidor, versões revalidadas, revogação prevalece sobre JWT antigo.
- Documento `41_Decisao_Aprovada_Matriz_Permissoes_Gestor_Operador_MCP`, D41-01–06: supervisor lê somente lojas concedidas; gestor só age onde tem alçada; atribuição/ações de operador são distintas. Escritas via MCP futuras exigem preparação e dupla confirmação — **este adaptador NÃO é o MCP**.
- Segurança Supabase: não usar `user_metadata` para autorização, não enviar `service_role`/credenciais privilegiadas ao navegador; RPC privilegiado exige isolamento forte e backend confiável.

## Implementação

Arquivos `backend/identity_boundary.py`, `backend/tests/test_identity_boundary.py` e `backend/requirements-s0-local.txt`.

**Fluxo em simulação:**
1. O cliente apresenta cabeçalho `Authorization: Bearer <token>` e uma operação permitida com `loja_id`, identificador de alvo e `expected_version`. O payload **não pode conter** `ator_id`, `user_id`, nome de tabela ou SQL; campos extras são recusados.
2. O adaptador consulta **GET /auth/v1/user** na origem GoTrue pré-configurada no servidor, sem seguir redirecionamentos, com timeout; não valida assinatura JWT por decodificação local. Apenas **depois de GoTrue autenticar** utiliza os claims `sub` e `session_id`, exigindo que `sub` coincida com o usuário informado por GoTrue.
3. Na **mesma transação PostgreSQL**, o adaptador verifica `auth.sessions(id,user_id)` sob lock `FOR KEY SHARE`. Sessão revogada ou não existente impede a operação, mesmo que o JWT ainda esteja no prazo de expiração.
4. O banco recebe `p_ator` exclusivamente a partir dessa identidade verificada, por SQL parametrizado fixo. As funções privadas já revalidam a vinculação ativa de gestor, escopo da loja, alvo e versão antes de alterar o domínio.
5. O retorno é o `jsonb` transacional da função, sem declarar envio real. Falha da verificação de identidade não executa SQL de mutação.

**Lista fechada de operações do protótipo:**
- `cancelar_plano` → `prumo_private.cancelar_plano_gestor_sintetico`, sem transporte WhatsApp.
- `conciliar_c07` → `prumo_private.conciliar_pendencia_c07_sintetica`, encerramento/vinculação **fictícia** com justificativa e versão. Não permite retry nem prova envio.

**Segurança deliberadamente conservadora:**
- `PsycopgTrustedDatabase` aceita somente DSN PostgreSQL `localhost`/loopback em banco descartável; **recusa host remoto**. Essa implementação só serve ao sandbox; nunca apontar para o projeto hospedado.
- A conexão privilegiada `postgres` é um detalhe do **S0 local** e deve ser substituída por serviço com identidade/credenciais dedicadas e alçada mínima, depois de auditoria de funções e RLS.
- Não há rota HTTP nem armazenamento/transmissão de segredos como serviço. Toda exposição pública requer threat model, TLS, rate limiting, isolamento dos segredos, mapeamento de erros, trilha de recusas e revisão humana.
- Não cria usuário administrador, não permite alterar permissões, DDL, D3/D4 ou parâmetros de IA; não executa MCP nem chama serviços externos Meta/Banco/OpenAI.
- O objeto de `session_id` é lido de um token autenticado pelo GoTrue; **nunca** de valor arbitrário fornecido no corpo da chamada.

## Verificações
- 12 testes unitários com identidades fictícias: rejeição de ator arbitrário, token divergente, sessão inválida, redirects/host inseguro, comandos desconhecidos, payload com versão inválida, SQL parametrizado, proibição de DSN remoto, falha de Auth e sessão revogada.
- Suíte PostgreSQL 17 completa da branch continua cobrindo autorização das funções privadas, idempotência e isolamento A/B. Execução e commit verificados no `tests/S0_ACEITE.md`.
- `AUTH-12` amplia o roteiro GoTrue/PostgREST local para validar cancelamento com gestor real do sandbox e negar operador, gestor de loja diferente, sessão revogada e `ator_id` inventado. Registrar resultado real da execução **separadamente**, sem inferir aprovação pelo fato de o teste estar escrito.

## Próximos portões
Implementar transporte de backend com autenticação/sessão realmente gerenciada, autorização de origem por aplicativo, atendimento humano, auditoria de recusas e erros, conta de banco menos privilegiada e mecanismos de controle de sessão em produção; submeter Auth/REST integrado e revisão de segurança antes de qualquer rede real.

**Decisão:** GO para testes e evolução S0 em branch DRAFT; NO-GO para merge, deploy de banco remoto, exposição de endpoint, Meta, produção, coleta D3/D4 ou cliente real.
