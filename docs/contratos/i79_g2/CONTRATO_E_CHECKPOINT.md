# S0/S1 — I79/G2: profissionais, ativação e chefia principal

Data: 27/10/2026 (America/Sao_Paulo). Escopo: branch experimental
`exp/s0-s1-i79-profissionais-20261027`, sem merge/deploy/Supabase hospedado.

## Continuidade recuperada

S1 original: `8780b576aa18bd3983c063339e2e42d2452af22c`; nenhum HEAD posterior
identificado antes da implementação. I78 executável: `f8268bc35c4701a8b522a66504e080628673b11d`,
CI `40475205913` SUCCESS. I77 reproduziu o PR #20 e verificou 34 fontes S1 sem
drift. Os mesmos 34 hashes foram conferidos nesta execução antes de mudar o ref
do manifesto de integração para o HEAD I78. Não foi incorporado PR completo.

Base S0 desta branch: PR #20 `4775091`, preservando PR #18 `88af4ae`, PR #16
`b298252`, CFI-01 e suas correções precommit. Contrato funcional S1 vigente,
relatórios I77/I78, checkpoints e Issue #23 foram lidos. A autorização atual do
responsável transfere a implementação integrada S0/S1 ao Codex principal; as
restrições históricas de solicitar mudanças técnicas à antiga conversa S1 não
se aplicam à presente branch experimental.

## Fonte autoritativa de cargo e competência

Uma coluna `cargo` é acrescentada à **mesma** `public.equipe_prumo_s1`:
`diretor`, `gestor`, `consultor`; labels visíveis correspondem a Diretor, Gestor,
Consultor. Não é um segundo cadastro de identidade nem um sistema de permissões.
O UUID continua sendo o ator S0/usuário GoTrue existente.

Diretor precisa também do registro global canônico
`prumo_private.s1_responsaveis_plataforma`, equipe ativa e `ativo=true` naquela
competência. Cargo não substitui competência e revogação não depende de renovar
JWT. A instalação só classifica como Diretor quem **já estava explicitamente**
nesse registro; não deduz Diretoria de grant de loja. O novo comando não cria ou
promove Diretores. O bootstrap de Diretoria permanece responsabilidade de
provisionamento confiável, não self-service.

Gestor é identificado pelo cargo explícito, mesmo com zero subordinados e zero
concessões de loja. Consultor é identificado pelo cargo explícito; a relação de
chefia continua em `s1_gestor_operadores`, preservando índice único e IDs antigos.
Grant de loja não se torna cargo e cargo não se torna grant de loja.

Registros legados sem cargo ficam NULL: **não são classificados por inferência**.
A atribuição canônica S0 rejeita novos leads para esse grupo. Leitura/carteira
anterior não é apagada ou transferida pelo instalador. Regularização explícita
do legado precisa de incremento administrativo próprio; esta entrega não afirma
que todo o acervo histórico foi migrado ou que o gate G2 operacional terminou.

## Porta interna administrativa v1

`backend/s1_professionals_local.py`, classe `S1ProfessionalsLocal`, usa a instância
real de `S0CFI01AtomicCommandsLocal`: verificador GoTrue, validação de DSN loopback,
chave de serviço e tabelas de nonce já existentes. Não cria autenticação paralela,
endpoint público, convite de usuário, senha de profissional ou client service_role.

Entrada estrita: `action`, `target_id`, `cargo`, `manager_id`,
`expected_relationship_id`, `idempotency_key`. UUIDs canônicos, cargo restrito a
Gestor/Consultor, chave ASCII 8–128, ID esperado inteiro não booleano em bigint.
Ator e sessão nunca vêm do payload: derivam do Bearer verificado no GoTrue.

| Ação | Precondição/efeito |
| --- | --- |
| REGISTER | UUID GoTrue já existe; cria ator se necessário e equipe pendente com cargo explícito; sem chefia, loja ou caso |
| ACTIVATE Gestor | equipe pendente e cargo Gestor; ativa sem exigir subordinados |
| ACTIVATE Consultor | equipe pendente, cargo Consultor e Gestor explícito ativo; cria chefia e ativa na mesma transação |
| TRANSFER | Consultor ativo, relação atual igual ao ID esperado e novo Gestor explícito ativo; encerra relação anterior e insere sucessora |

REGISTER e ACTIVATE usam ID esperado 0 (sem relação ativa); TRANSFER usa ID
imutável positivo da relação anterior. O ID gerado da sucessora é o novo token
CAS. Não se atribui versão comercial de caso/ciclo a essa relação, e não se
ratificam os contratos UI/S0 D1–D4. IDs de relação na resposta são strings
decimais para não perder precisão de bigint em consumidores JavaScript.

O cadastro é **organizacional de uma identidade já existente**. Criação/convite
no provedor Auth não é fingida como concluída: requer fluxo administrativo de
identidade e custódia próprios antes de haver operação hospedada.

Resposta mínima: `outcome`, `request_id`, `action`, `target_id`, `cargo`,
`manager_id`, `previous_relationship_id`, `relationship_id`. `APPLIED` ou
`ALREADY_APPLIED` confirmam apenas a mutação administrativa. O adaptador confere
todos os vínculos retornados antes do COMMIT e fecha conexão inclusive se uma
constraint adiada falhar na saída da transação.

Recusas: `INPUT_REJECTED`, `DENIED`, `STALE`, `CONFLICT`, `UNAVAILABLE`. Não há
retry automático, envio, transferência de caso ou confirmação comercial. Em
falha de comunicação durante confirmação, `UNAVAILABLE` não prova rollback;
reconciliar com a mesma chave, nunca gerar outra silenciosamente.

## Transação, revogação e invariantes

HMAC SHA-256 com domínio `s0-s1-i79-admin-v1` vincula todos os campos, ator,
sessão, chave, emissão e nonce. Janela existente de 30 s e tolerância futura de
5 s, rechecagem depois das esperas, nonce no mesmo banco/transação. MACs G1/F02
não representam comando administrativo. Auditoria mínima não contém JWT/HMAC,
segredo, mensagem ou PII textual.

Ordem dos locks da porta: chave/sessão existentes; atores ordenados UUID
`NO KEY UPDATE`; equipe dos participantes ordenada UUID `UPDATE`; competência
global do Diretor `SHARE`; relação atual `UPDATE`. O Gestor anterior é obtido
pelo ID imutável esperado antes dos locks; a relação é relida depois deles.
Não há aquisição de lead/caso por transferência de chefia. Ativação classificada
não executa a recuperação histórica de casos I6, evitando promoção implícita de
um mecanismo anterior ao contrato de prova de contato humano.

O registro do Diretor é reavaliado **após** as esperas. Sua revogação confirma
antes e recusa o comando, ou espera o comando em andamento confirmar e corta o
próximo. O mesmo vale à barreira de sessão existente. Não se promete recolher
bytes já entregues ou cancelar transação que já linearizou antes da revogação.

Índice único existente continua garantindo no máximo uma relação. Novos triggers
de constraint **DEFERRABLE INITIALLY DEFERRED** garantem, no COMMIT, que Consultor
classificado ativo tenha exatamente um Gestor classificado ativo. Impedem também
inativar um Gestor deixando Consultores ativos dependentes. Linhas de relação e
conta são barreiras reais para escritas concorrentes, com rechecagens após locks.
Fechamento de relação é irreversível: não se reabre histórico para desfazer uma
transferência; retorno de chefia é outro comando CAS auditado.

A constraint privada executa como DEFINER de owner fixo: eventos adiados são
avaliados no COMMIT depois que a porta assinada retornou, sob o login SQL da
transação. Não se concede EXECUTE dos helpers nem SELECT de tabelas privadas ao
login para contornar essa diferença de contexto. A função só valida invariantes,
tem `search_path=''` e não recebe um ator escolhido pelo cliente.

Idempotência durável por `(diretor_id, idempotency_key)`, vinculando payload
exato. Repetição simultânea cria uma relação/pedido; adiciona auditoria/nonce
sem reaplicar a mutação. Payload divergente conflita. Uma relação já substituída
ou competência revogada não é reativada por replay.

## Privilégios e limite de provisionamento

Reutiliza o login SQL S0 restrito, o executor HMAC G1 NOLOGIN e os cofres/nonces
existentes. O login não recebe DML de profissionais, competência global, chefia
ou auditoria e não pode assumir o executor. `anon`, `authenticated` e
`service_role` não executam a porta administrativa privada.

A ponte administrativa estreita segue owned por `postgres`: o guard canônico
I46 de escrita de equipe/eventos exige esse `current_user`, assim como outros
guards S0/S1. Nenhum desses guards foi desabilitado para fazer o fluxo passar.
Isso **não certifica** a separação integral do owner de negócio para serviço
hospedado. Uma evolução de privilégios precisa revisar I46/I57/I61 conjuntamente,
com owner NOLOGIN e grants por coluna, não conceder postgres ao login. A fixture
e o instalador exigem opt-in, PG17 e ambiente loopback descartável.

## Integração com os consumidores existentes

- Nova barreira na `atribuicoes_humanas` canônica valida cargo/chefia, preservando
  fechamento de atribuições existentes e os guards I52/I57/I61.
- I54 recebe uma adaptação verificada por hash no seletor: somente Consultor
  classificado com Gestor classificado entra na seleção. Os demais algoritmos,
  CAS, locks e auditoria I54 são reutilizados. O patch e o delta inteiro são
  aplicados em uma só transação no instalador experimental.
- G1 conserva seu runtime e recebe guards nos ledgers de pedido/auditoria para
  exigir cargo Gestor do solicitante e Consultor do destino, inclusive replay.
  Um Gestor sem subordinados pode assumir pessoalmente pela I55 com grant da
  loja, mas não é reclassificado como Consultor para receber encaminhamento G1.
- Troca de chefia altera supervisão pela relação vigente. Não muda titularidade
  de casos, grants de loja, intake, indicadores ou estado comercial. RLS I63 e
  barreira de sessão do PR #16 são reutilizadas, não reconstruídas.
- Exceções I61 do vínculo encerrado são revogadas duravelmente e auditadas no
  mesmo COMMIT. Voltar ao Gestor original por nova relação não reativa a exceção.
  Não há reemissão automática; continuidade é outra operação autorizada.
  O revogador I61 existente bloqueia exceção antes de equipe; como a transferência
  já segura equipe, a aquisição das exceções usa NOWAIT em ordem de ID. Disputa
  aborta a transferência inteira para retentativa segura, sem nova aresta de
  espera invertida. A auditoria administrativa registra o Diretor verificado.

Pausa de intake continua sendo I52/I53, sem suspensão da conta. Consultor pausado
pode ter chefia transferida; conserva carteira/grants. A2 continua impedindo
qualquer nova atribuição, inclusive com exceção.

## Gates e sequência após esta fundação

G2 continua parcial até serviço/API/UI administrativa, provisionamento de
identidades, regularização de legado, gestão completa de desligamento e aceite
operacional. Não solicitar novamente decisões D1/A2 já expressamente aprovadas.

G1: composição técnica com cargo/chefia e regressões reais é parte desta entrega;
ficam porta pública/UI, ownership hospedado e prova real de primeiro contato.
G3: supervisão após transferência e sessão são exercitadas no catálogo existente;
serviços de mídia e D3/D4/retencão continuam dependências já registradas.
G4/G5: preservar distinções de contato confirmado, entrega, conclusão técnica e
venda; não fabricar eventos Meta/F03. G6: homologação conjunta e produção não são
autorizadas por este checkpoint.

Próximo incremento técnico recomendado: regularização explícita/versionada dos
profissionais legados com pré-visualização de impacto e tratamento das exceções
por caso na troca de chefia; depois compor API/DTO de administração com a frente
Frontend, sem transformar uma transferência de equipe em remanejamento de casos.
