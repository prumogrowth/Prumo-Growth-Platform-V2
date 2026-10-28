> Continuidade manual: a política D01–D05 deste registro histórico foi atualizada pela instrução expressa do responsável. Consulte [contrato manual revisão 2](manual/CONTRATO_MANUAL_V2.md) e [checkpoint manual](manual/CHECKPOINT.md). Os resultados técnicos históricos abaixo permanecem limitados à sua revisão original.

# I86 — governança e observação de autoridade, candidato v1

28/10/2026, America/Sao_Paulo. Não ratificado pela orquestração.
Base imutável: 3cab3d57619cc1157698a08ac26f34e0c363f6dd.
Esta entrega não cria nomeação organizacional, endpoint ou autoridade produtiva.

## Fontes e regras já definidas

I79 define UUID canônico GoTrue/S0, cargo explícito na equipe e competência
global separada. Administração ordinária requer ator existente, equipe ativa,
cargo Diretor, competência ativa e sessão canônica viva. I80 mantém inventário,
prévia e APPLY separados. I81 preserva owners NOLOGIN, RLS, guards e constraints;
I82 define as seis ações HTTP, autenticação GoTrue e HMAC/nonce de servidor.
I83 dedica login/cofre à Edge; I84 confere engine, DB, rede, marcador e loopback;
I85 cria exclusivamente a primeira autoridade sintética por aprovação técnica.

Cargo, loja, subordinados, user_metadata, app_metadata ou JWT isolados não
constituem fonte de competência. A I86 não converte competência para administrar
profissionais em competência para nomear outro Diretor. Service_role e postgres
são capacidades técnicas do instalador, nunca autoridade humana.

A retirada I85 conserva cargo Diretor/estado ativo como classificação histórica,
mas torna a competência global inativa e retira as sessões observadas no corte.
Novo login Auth pode ser válido sem restaurar administração. Não se muda cargo,
estado, carteira, intake, concessões ou história por inferência.

## Capacidade implementada nesta proposta

AuthorityLab é uma ferramenta Python exclusiva do instalador de laboratório,
sem servidor HTTP, CLI pública ou credencial enviada à Edge. Reutiliza
SupabaseGoTrueVerifier, Bootstrap.owned e cfi01_session_valid_local, sem editar
nenhum deles. Não é o futuro runtime administrativo e não pode receber DSN remoto.

Entrada local estrita:

~~~json
{
  "version": "prumo.i86.observation.v1",
  "idempotency_key": "i86-observacao-sintetica-01",
  "expected_sha256": null
}
~~~

Identidade/sessão derivam exclusivamente do Bearer verificado em GoTrue; não são
campos de entrada. O verificador observa somente o próprio sujeito autenticado.
Um Gestor ou usuário Auth sem cadastro pode ter sua ausência de competência
diagnosticada pelo instalador, sem receber nova consulta pública ou poder.

A transação adquire chave técnica de idempotência, sessão, ator NO KEY UPDATE,
equipe UPDATE e competência SHARE, nessa direção. Revalida a sessão depois das
esperas. Captura classificação, competência, referências canônicas e versões
físicas xmin em um snapshot SQL, com hash SHA-256 e relógio do servidor.
Não obtém credenciais, email, mensagens, concessões comerciais ou dados Meta.

Somente duas tabelas novas do schema privado de ensaio prumo_i86_lab recebem
evidência/auditoria. Não há FK nova em tabelas herdadas: as referências históricas
são validadas na transação e precisam sobreviver à retirada da sessão. Essas
tabelas não são cadastro organizacional, mandatos ou um segundo Auth. São
postgres-owned, apenas para o instalador, com RLS/FORCE RLS, sem grants para
clientes/Edge e sem função SECURITY DEFINER. Nenhum SQL de nomeação existe.

Estados retornados:

| Estado | Significado |
| --- | --- |
| OBSERVED | Evidência técnica e auditoria confirmadas na transação |
| ALREADY_RECORDED | Mesma chave/payload/sessão e estado canônico ainda igual |
| INPUT_REJECTED | Forma, versão, chave ou CAS inválidos; nenhuma escrita |
| DENIED | Identidade/sessão inválida ou barreira canônica recusada |
| STALE | Snapshot/versão mudou; não devolve autoridade positiva antiga |
| CONFLICT | Chave reutilizada com comando divergente |
| CONCURRENT_CHANGE | Contenção sem aquisição segura; não repetir cegamente |
| UNAVAILABLE | Falha técnica/COMMIT incerto; não afirmar rollback |

OBSERVED não significa Diretor autorizado para governança. A saída declara
authority_scope=ORDINARY_ADMIN_OBSERVED_ONLY, authorization_token=false e
governance_state=PENDING_DECISION. A observação é histórica e não pode ser
apresentada como autorização futura: cada comando I79/I80 continua autenticando
e revalidando o domínio por suas próprias portas assinadas.

## CAS, idempotência e recuperação

expected_sha256 é um token técnico de snapshot, não versão de mandato, caso,
ciclo ou regra comercial. O hash inclui contexto canônico e xmin; mudança
física com mesmos valores aparentes invalida replay. xmin não é versão
organizacional de longo prazo e exigirá outra decisão antes de uso produtivo.

Idempotência é local ao ator/sessão/chave, com payload exato e rechecagem do
estado atual antes de retornar. Replay não restaura competência revogada nem
confirma governança. Auditoria e observação confirmam juntas; falha diferida
impede retorno de COMMIT confirmado. Perda de resposta pode ser reconciliada
pela mesma chave, sempre sob sessão viva e estado ainda igual. Não há retry
automático, novo POST Auth ou novo grant de bootstrap.

Não se cria outro journal/cofre no filesystem. O journal I85 permanece intacto,
com sua recuperação e seus bloqueios. A observação SQL é evidência de laboratório.

## Decisões pendentes e transições bloqueadas

| ID | Decisão que falta | Responsável pelo encaminhamento | Efeito atual |
| --- | --- | --- | --- |
| D01 | Fonte organizacional competente para nomear/substituir Diretor | Orquestração com responsável organizacional a designar | APPOINT_DIRECTOR e REPLACE_DIRECTOR bloqueados |
| D02 | Quantidade/forma de aprovações, prova verificável, validade e revogação do ato | Mesma coordenação, com requisitos de segurança | Nenhuma alegação de aprovação aceita |
| D03 | Continuidade, sequência de retirada/entrada e eventual janela sem responsável | Orquestração/produto organizacional | Sem troca automática, sobreposição ou transferência comercial |
| D04 | Autoridade e evidência para recuperação na ausência/perda do último responsável | Orquestração e responsável organizacional | REACTIVATE_AUTHORITY bloqueada; instalador não vira substituto |
| D05 | Quem pode retirar competência ordinariamente e efeitos organizacionais adicionais | Orquestração/produto organizacional | Revogação humana operacional bloqueada; retirada sintética I85 preservada |

governance_gate apenas diagnostica PENDING_DECISION para essas quatro famílias.
Não aceita approved=true, escolha de aprovador, contagem de assinaturas, claim
de serviço ou cargo como ratificação. A simultaneidade de duas nomeações reais
continua PENDING_DECISION; concorrência de evidências técnicas não a certifica.

## Compatibilidade, isolamento e produção

Não há edição de I79–I85, local_admin, backend, SQL/migrations, Edge, Frontend,
contratos Meta ou workflows herdados. Nenhuma regra de lojas/equipes é ampliada.
As seis portas administrativas continuam as existentes, com HMAC/nonce,
idempotência, constraints diferidas e competência do Diretor.

Provas físicas usam runners GitHub-hosted separados, engine e stack próprios,
sem compartilhamento físico de portas, volumes, custódia ou credenciais com
outra conversa. Fontes são exportadas do commit exato para RUNNER_TEMP:
caches/estado do CLI não alteram o checkout revisado. Nome/portas fixos da
infraestrutura herdada são exclusivos dentro de cada VM, nunca compartilhados.

Não há dependência da branch Meta. Administração futura de canais é interface
a especificar depois, sem M2M, webhook, lote, ACK, recibo de ingestão ou F02.
Produção, usuário real, governança ratificada, owner mínimo do eventual serviço
de observação, custódia hospedada, TLS, Frontend, homologação e rollout não são
autorizados por esta proposta.
