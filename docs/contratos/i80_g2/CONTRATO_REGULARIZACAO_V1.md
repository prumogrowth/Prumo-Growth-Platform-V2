# S0/S1 I80 — regularização administrativa explícita do legado, v1

27/10/2026 (America/Sao_Paulo). Candidato interno executável somente em PG17 /
GoTrue / PostgREST descartáveis, sobre a I79 do PR #26. Não é runtime hospedado,
endpoint público, importação de permissões ou ratificação de contrato comercial.

## Continuidade e arquitetura

I79 recuperada em `8068db1c42216fb1da6855401146eab257f3eff1`, código
`ab96b5d2`, CI `40484344324` SUCCESS. S1 original permanece no checkpoint I78
`8780b576`. Não houve avanço nesses dois HEADs antes da implementação.

São reutilizados equipe/cargo, chefia, constraints I79, ator GoTrue, competência
global de Diretoria, HMAC/chaves, nonce, RLS, DSN e transação S0. Os executáveis
certificados I54–I79 não são reescritos. I80 acrescenta porta e ledgers privados
de inventário/prévia/aplicação; não cria sistema alternativo de identidade/cargos.

A [ADR de arquitetura](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/blob/2171d9a17e6d3e345cc52b432294ad1a244f16e0/docs/decisoes/ADR_20261027_BACKEND_SUPABASE_OPENAI_DIRETO.md)
foi consultada: backend próprio no Supabase, inicialmente Edge Functions,
servidor → OpenAI via HTTPS. PostgreSQL não chamará OpenAI por trigger. Este
Python continua sendo adaptador de laboratório; o SQL persiste domínio/estado.
Não se iniciou migração de runtime, worker externo ou integração hospedada.

## Fluxo obrigatório: inventário → prévia → aplicação

O Diretor autenticado escolhe **explicitamente** cargo e, quando necessário,
Gestor. Concessões de lojas, subordinados, carteira e hashes não escolhem cargo.
Uma prévia READY não aplica nada. O cliente precisa enviar outro comando APPLY,
vinculado ao ID/hash da prévia persistida e à mesma sessão do Diretor.

Porta: `S1LegacyRegularizationLocal`, herdando a construção I79 sobre uma instância
real de `S0CFI01AtomicCommandsLocal`. Cada chamada verifica Bearer no GoTrue e
revalida sessão/competência em PostgreSQL. Ator/sessão não vêm do payload nem de
`user_metadata`, papel de loja ou alegação do cliente.

Nove campos exatos: `action`, `target_id`, `cargo`, `manager_id`,
`expected_sha256`, `preview_id`, `cursor`, `limit`, `idempotency_key`.

| Operação | Vinculação e resultado |
| --- | --- |
| INVENTORY | demais campos de proposta nulos; cursor UUID opcional; limit inteiro 1–50; retorna página minimizada de atores sem cargo ou com chefia incompatível |
| PREVIEW | alvo, cargo Gestor/Consultor explícito, Gestor proposto opcional e hash do item do inventário; limit 0, sem cursor/preview_id; persiste READY/BLOCKED e impacto |
| APPLY | mesmos alvo/cargo/Gestor, preview_id e hash do **contexto da prévia**; limit 0, sem cursor; compara prévia imutável e estado atual, aplica uma vez |

UUIDs canônicos não nulos, chaves ASCII 8–128 caracteres e hashes SHA-256 em
hexadecimal minúsculo. Não há cargo Diretor nesta porta, ativação implícita,
criação Auth, grant geral de loja, envio, venda ou mudança de estado comercial.

Inventário é paginado por UUID e cada página usa o estado observado naquela
chamada, não um snapshot global congelado de todo o cadastro. A lista só contém
UUID, cargo/estado, indicação de completude e digest. Não retorna nome, email,
telefone, mensagem, JWT, HMAC ou segredo. Uma nova concessão/versão não é
descartada porque a quantidade de registros permaneceu igual.

## O que a prévia vincula e mostra

O hash do inventário identifica o estado do alvo. A prévia acrescenta o contexto
do Gestor escolhido e a versão da autoridade do Diretor. A fonte é PostgreSQL,
não um hash calculado pelo chamador. Snapshot interno ordenado inclui:

- cargo/estado e versões físicas das linhas;
- existência do UUID Auth e competência global conflitante;
- vínculos de chefia atuais/históricos e cargos/estados dos pares;
- concessões de lojas, validade e identidade de cada grant;
- intake e sua versão;
- atribuições, encerramentos e identificadores dos casos;
- exceções I61, escopo e revogação;
- cargo/competência do Gestor proposto e versões da competência do Diretor.

Os `xmin` registrados detectam mudanças de ida/volta (ABA) mesmo se os campos
visíveis voltarem aos mesmos valores. Canonicalização é JSONB do PG17 com timezone
UTC; validade temporal é avaliada no servidor. Conteúdo de mensagens não integra
esse digest de autorização: a regularização não lê nem altera o texto histórico.
Ela não deve invalidar uma conversa apenas por chegada de mensagem nova.

A prévia dura cinco minutos, tem ID próprio e é imutável. Vincula ator e sessão:
logout e nova sessão não reutilizam a mesma prévia. Revogar e conceder novamente
a competência do Diretor altera seu contexto e exige nova prévia. A renovação de
prazo não é feita por replay. Uma repetição de APPLY já confirmado pode recuperar
o recibo após o prazo, desde que mesma sessão/autoridade e estado final ainda
coincidam; isso não executa novamente a alteração.

Impacto contém estado preservado, relação anterior, necessidade de mudar relação,
IDs das exceções a revogar, contagens de grants/atribuições/casos e intake. Expõe
se a **barreira técnica de intake do Consultor** poderá ficar habilitada; exige
sempre rechecagem de alçada na atribuição real. Isso não é direito geral de loja
ou de envio. Pausa mantém essa barreira fechada sem suspender conta.

Perfis com mais de 2.000 registros ligados são marcados incompletos e BLOCKED,
sem contagens parciais apresentadas como completas. Exigem processamento/revisão
administrativa apropriados em incremento posterior, não promoção silenciosa.

## Regras de regularização e negativas conservadoras

| Situação | Comportamento |
| --- | --- |
| Cargo NULL e proposta explícita consistente | pode classificar; conserva estado, carteira, grants e intake |
| Consultor ativo órfão + Gestor explícito/classificado/ativo | cria chefia e cargo na mesma transação, sob constraints I79 |
| Vínculo atual já é o escolhido e válido | mantém o mesmo ID; não fecha/reabre nem replica a relação |
| Chefia precisa mudar | fecha relação anterior, cria sucessora, sem transferir casos |
| Gestor solicitado ainda é subordinado | BLOCKED; não encerra esse vínculo por inferência |
| Consultor solicitado ainda tem subordinados | BLOCKED; não remove/reparenta subordinados automaticamente |
| Consultor ativo sem escolha de Gestor | BLOCKED |
| Gestor proposto sem cargo explícito/ativo ou com competência Diretoria conflitante | BLOCKED |
| Cadastro pendente sem chefia | pode classificar, conserva pendente; ativação futura usa I79 |
| Cadastro pendente com proposta/vínculo de chefia antecipado | BLOCKED para revisão/ativação I79, sem contornar seu CAS |
| Cargo já conhecido e válido | usa operação I79 apropriada; I80 não vira troca arbitrária de cargo/chefia |
| Ausência de registro de equipe/Auth ou dados incompatíveis | inventário/negativa; sem cadastrar ou completar por suposição |
| Estado ou autoridade mudou desde a prévia | STALE/DENIED; exige leitura/prévia atualizadas |

O cargo do profissional não é promovido automaticamente por estar ativo. Cargo
e chefia são decisões do Diretor; a porta só aplica a proposta explícita e
consistente. Não solicita novamente decisões de produto D1/A2 já vigentes.

## Exceções I61 e preservação

Sem mudança de chefia, exceção válida no caso/atribuição atual pode ser preservada
sem criar grant. Exceções incompatíveis, fora da atribuição ativa ou de chefia
diferente são identificadas na prévia para revogação. Quando há criação/troca de
chefia, exceções anteriores do alvo são revogadas duravelmente, inclusive as que
poderiam ressuscitar ao criar novo vínculo com um concedente antigo.

APPLY revalida o plano depois dos locks e registra autoria do Diretor na trilha
I61. Reutiliza fechamento/constraints I79 e seus guards; não concede nova exceção
para "compensar" acesso perdido. Caso e titular continuam os mesmos. Continuidade
de caso que perdeu acesso requer operação gerencial separada e autorizada.

Não há UPDATE/DELETE de casos, atribuições, mensagens, histórico ou grants. A
única atualização de equipe é o cargo ainda NULL; `estado` e intake permanecem
iguais. Uma chefia incompatível não é apagada: quando o plano permite troca,
o registro antigo é fechado e preservado. Recusados/conflitantes ficam intactos.

## Concorrência, CAS e auditoria

Chave HMAC reutilizada de S0, com domínio distinto
`s0-s1-i80-regularization-v1`, todos os campos vinculados, janela de 30 s e tolerância
futura de 5 s, nonce no mesmo banco e rechecagem depois das esperas. A senha SQL
isolada não autoriza operação. Nenhum cofrezinho/role de autenticação paralelo.

Uma trava de idempotência por Diretor/operação/chave antecede os locks de domínio.
Mesma chave converge sem reaplicar. Chaves distintas não consomem duas vezes a
mesma prévia. Payload divergente conflita; replay não reativa estado revogado.

As linhas de atores são barreira forte contra novos FKs concorrentes; equipe,
relações, grants, intake, atribuições, casos e exceções são lidos/bloqueados em
ordem determinística, sem filtro antecipado de elegibilidade. Aquisições novas
de domínio usam NOWAIT, evitando esperar em sentido inverso dos escritores
I54/G1/I61 existentes. Contenção retorna CONCURRENT_CHANGE, sem retry cego.
Pares usados pela validação I79 são protegidos antes da alteração. Isso não
certifica uma ordem global para todo escritor futuro do projeto.

Contenção, stale CAS, falha parcial, auditoria rejeitada, constraint adiada ou
recibo inválido abortam a transação. A validação de resultado acontece antes do
COMMIT e a conexão é fechada inclusive em falha adiada. Falha de comunicação ao
confirmar retorna UNAVAILABLE, sem afirmar rollback de um resultado incerto:
reconciliar com a mesma chave.

Prévia, aplicação e auditoria são privadas, RLS habilitada, sem DML para o login,
`anon`, `authenticated` ou `service_role`; a aplicação só executa a porta assinada.
Não há membership permanente de owner para o login. Recibos e prévias são
imutáveis; inventariar/preparar somente acrescenta prova técnica e nonce, nunca
altera o cadastro. Recusas abortadas não são fingidas como auditoria durável.

## Limites e produção

A ponte de negócio continua com owner técnico `postgres`, exigido pelos guards
I46/I57/I61 já existentes. O executor HMAC é NOLOGIN restrito e é reutilizado.
Isso não resolve o provisionamento produtivo com owner de domínio mínimo.

Faltam borda/API/UI, operação em Edge Functions, custódia/observabilidade/retenção
dos novos registros e ensaios de escala. Não autoriza deploy, migration hospedada,
credencial produtiva ou chamada OpenAI/Meta.

F02: auditoria `7c282df` e H01 `559b583` foram consultados como referências, sem
reexecutar G01–G07 ou pedir novo levantamento. G01–G06 ficam parciais e G07
pendente. Cadastro/chefia I79/I80 não ratificam revisão comercial nem os quatro
hashes alegados pela F02. Nenhum módulo F02 foi incorporado ou implementado.
