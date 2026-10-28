# S0–Meta–Ingress–01 — matrizes de prova, limites e integração

28/10/2026, America/Sao_Paulo. Somente laboratório isolado. Contrato completo em `CONTRATO_CANDIDATO_V1.md`.

## Fontes externas consultadas somente para leitura

HEADs atuais foram consultados pelo conector GitHub antes da leitura e conferidos por refs Git. Nenhum merge/cherry-pick/importação integral de branch auxiliar. Os 27 blobs copiados são dependências transitivas das suítes selecionadas, sob a allowlist e com manifesto Git SHA-1 verificável.

| Fonte | HEAD observado | Uso e limite |
|---|---|---|
| PR7 | `450dcd645f35d4c8bf93e974e75d3b09467965a7` | Composição guardada, RLS de locks com USING true/WITH CHECK false e ordem real. Não executamos suas 823 WAs nem instalamos suas migrations. |
| PR14 | `31bb84fa524f4ecfdf02360988471d7f989506d7` | ACK-03, C1–C7, limites FileStore e regressões originais. Contratos auxiliares não ratificados operacionalmente. |
| PR16 | `b298252c26c69f668b3c3fdb86e9252faff9e44b` | Parecer Meta, barreira de sessão humana, recheck e limites de locks globais. Nenhuma adaptação do CFI. |
| PR18 | `88af4aea3aeb2c403bab4c078fdc04d560f2cba0` | Evidência PENDING_EVIDENCE não é aprovação; resultado incerto não prova rollback; nenhuma concessão humana ou comercial importada. |
| PR19 | `d453a22f7160c4e9ff146d21aebe0c2679c9840a` | Catálogo e autorização de envio pertencem a entrega separada. Não há catálogo implementado aqui. |
| I85 congelada | `3cab3d57619cc1157698a08ac26f34e0c363f6dd` | Checkpoint I85, contratos I79/S0/S1, segurança de chaves/nonce/logs. Código certificado e CI históricos permanecem históricos. |

O conteúdo vivo da conversa I86 não foi consultado. Não há dependência de arquivos, contratos, banco ou autoridade I86.

## Matriz de autorização técnica

| Prova ou recurso | Positivo | Negativa obrigatória e prova |
|---|---|---|
| App física | HMAC externo sintético com segredo escolhido por App confiada | Assinatura alterada/App sem segredo: T17/T20 |
| Principal M2M | Ed25519, issuer/key/revision/audience/scope, registro técnico | Tamper, domínio errado, JWT humano, bool declarativo, issuer/key/ACL: T18–T20 |
| Tempo/nonce | Clock DB após espera, TTL≤30s, nonce único por chave | Expirado, futuro, duplicado, expiração na fila: T02/T20/T39/T40 |
| Rota | App e revisão ativa do registro | Rota/App cruzadas/revisão obsoleta: T20/T23 |
| Binding | Cada WABA/phone/App/tenant/channel e revisão, fonte SQL confiada e canal explicitamente autorizado à chave | Outro tenant/App, desconhecido/desativado: T12–T14/T26/T49 |
| Multicanal | Dois canais da mesma App/concessionária | Sem transferência de direito entre canais: T09/T12–T14 |
| Revogação | Fence rota antes de principal/binding, CAS | Ambas as ordens e readback pós-revogação: T21–T26/T46 |
| Rotação M2M | Nova chave técnica explicitamente registrada, antiga revogada | Recuperação pela nova chave e negação pela revogada: T22/T43 |
| Recibo | Chave Ed25519 S0 separada e pública fixada pelo consumidor | Corpo, chave/contexto falsos, chave privada incompatível: T32/T33/T44 |
| Login runtime | NOSUPERUSER/NOBYPASSRLS, sem membership do owner/DDL | UPDATE efetivo/DELETE/DDL/SET ROLE recusados, locks ainda funcionam: T34 |
| Autoridade humana/comercial | Nenhuma operação disponível | Não há endpoint de Diretor/equipe/grant/envio/lead/template; flags sempre falsas e 364 arquivos herdados conferidos. |

## Matriz de resistência e regressão

Txx refere-se ao método numerado em `integration/s0_meta_ingress/test_ingress.py`; 49 testes de topo, com subcenários explícitos. Contagens não são somadas aos testes históricos como certificação de integração operacional.

| Requisito | Prova executável |
|---|---|
| Commit integral/readback e raw exato | T01, readback antes e depois de commit, digest e bytes com whitespace preservado |
| Replay com mesma prova / nova autenticação | T02/T03, T39 concorrente com mesmo nonce |
| Mesmo ID divergente / mesmo raw ID diferente | T04/T05; conflito persistido sem trocar original |
| Variante física com novo ID | T06, outro lote sem efeitos comerciais |
| Concorrências equivalentes/conflitantes | T07: 12 conexões; T08: oito conexões; um lote lógico |
| Ordem/proveniência/tipos/duplicatas | T09–T11; status não vira inbound; mensagens iguais mantêm posições/UUIDs distintos |
| Item inválido tardio/ocorrência desconhecida | T15/T16/T45, zero lote/itens/nonces de aceite parcial |
| Falhas entre cada escrita | T27: nonce, batch, item, precommit; todas as tabelas sem resíduos |
| Processo SIGKILL | T28: oito filhos reais em nonce/batch/item/precommit/postcommit/readback/pré-assinatura/pós-assinatura |
| Resposta perdida após commit | T29; erro sanitizado e readback com nova prova |
| Queda abrupta PostgreSQL/WAL/restart | T30: container SIGKILL, volume conservado, redo observado, recibo igual, transação não confirmada desfeita |
| Armazenamento parcial/tamper de recibo | T31/T32; incerteza ou verificação negativa, sem sucesso presumido |
| Indisponibilidade e recibo irrecuperável | T33/T36/T38/T44 |
| HTTP local real | T37, socket loopback e perda física de resposta, mesmo registro recuperado |
| WAL local obrigatório | T41 força sessão synchronous_commit=off e runtime restabelece on; runner registra fsync/full_page_writes/sync_commit |
| Revisão e locks | T42/T46/T47: bindings mudados, espera observada em pg_stat_activity, canais na ordem inversa sem inversão |
| Instalação guardada/atômica | T48: falta opt-in e reinstalação recusadas, catálogo herdado preservado |
| Modelo puro/FileStore anterior | 52 originais PR14, sem edição; explicitamente separados de SQL físico |
| Regressões Meta anteriores | 161 originais, oito suítes sem edição; parser, assinatura, routing, builders e gates |
| Escopo | 12 adversariais: I85 pendente, I86 nova, migration staged, exclusão/rename, workflow, base, manifesto, arquivo ignorado, symlink, positivo e edição própria versionada |
| Herança S0/I85 | 288 backend; 7 filesystem I85 + 9 boundary I84, normal e Python -O. Nenhum banco I85 ou fluxo humano executado. |

## Matriz de limitações e riscos residuais

| Limite | Garantia real / risco restante | Responsável futuro |
|---|---|---|
| PostgreSQL local | Commit/WAL e restart de processo/container em volume local testados. Sem falha física de host/disco, corrupção, réplica, quorum, backup ou failover. | S0/Infra |
| Fronteira do runtime | Runtime interno confiável verifica M2M; login SQL tem INSERT/SELECT nos ledgers privados do lab. Não é SQL RPC resistente a comprometimento desse runtime ou do instalador. Não distribuir DSN nem expor acesso SQL ao ingressor. | Segurança/S0 |
| Custódia | Chaves sintéticas em memória e senha de instalação em env-file privado temporário, removido no descarte. Sem KMS/HSM, memória protegida ou zeroização garantida pelo Python/host. | Segurança/Infra |
| Registro técnico | Fixtures explícitas; CAS/revogação via controle suportado. Superusuário pode alterar ou reativar diretamente, adulterar ledgers e logs. Fonte real de provisionamento ainda precisa contrato. | S0/Meta/Infra |
| Recibo após rotação | Corpo e chave pública duráveis; recuperação exige chave privada histórica/instância corretas. Um signer por instância no lab; não há keyring/KMS distribuído. | S0/Segurança |
| Transporte | Harness loopback sem TLS, sem Meta real, challenge público, quotas, proteção DoS/slowloris ou política de HTTP externa. | Meta/Infra |
| Canonicalização | Formato Python estreito e parser próprio para multicanal; suítes originais preservadas são regressão, não homologação de um ingressor em outra linguagem. | Meta/S0 |
| Capacidade | Limites baixos e advisory exclusivo por rota favorecem prova de atomicidade. Sem benchmark ou SLA; fila expira e falha fechada. | S0/Infra |
| Retenção/privacidade | Bytes/contatos originais ficam no banco fictício, nunca nos artifacts. Sem política de retenção/expurgo, acesso operacional/minimização ou LGPD homologada. | Privacidade/S0 |
| Negativas de perímetro | Rejeições antes de autenticação não geram auditoria SQL durável. Sink sanitizado, rate limit e alertas externos ainda pendentes. | Segurança/Infra |
| Locks compartilhados | Nenhum recurso canônico é usado. Provas locais não certificam ordem global S0/S1/Meta; integração exige inventário de mutadores/FKs/triggers. | Orquestração/S0/S1/Meta |
| Classificação comercial | Tudo fica ARCHIVED_UNRESOLVED. Wamid, delivered, durabilidade e ACK não criam consentimento, caso, lead, venda ou envio. | Contratos autoritativos independentes |
| Autoridade I86 | Nenhum gate dessa frente depende de autoridade humana. Política futura de quem administra registro técnico exige orquestração; nenhuma permissão concedida aqui. | Orquestração/I86, se deliberado |

## Relatório de interfaces futuras / pedidos de integração

Nenhuma mudança de componente compartilhado foi necessária para o laboratório. Os itens abaixo são pedidos de contrato, **sem autorização de edição** e sem ampliação da allowlist.

| Interface/arquivo futuro | Motivo/contrato afetado | Alternativa proposta no lab / gate restante |
|---|---|---|
| `integrations/whatsapp-meta/cloud-webhook-handoff.ts` (fonte PR14, somente leitura) | Seu escopo único não representa o multicanal ratificado para esta prova; META-S0-ACK-03/C4 | Normalizador novo exclusivo; preservar fonte e regressões. Meta/S0 devem homologar parser multicanal e proveniência física, sem substituir o módulo agora. |
| Host de ingresso Meta/Infra, caminho a ser definido pela orquestração | Converter recibo verificado em decisão HTTP externa; ACK-03/C3/C4 | API interna + harness loopback. Definir códigos, assinatura bytes, retry, limite, DLQ de inválidos permanentes, backpressure, timeout e segurança TLS. |
| Registro técnico autoritativo S0, caminho a definir | Fonte real App/WABA/número/canal/concessionária e mutadores/revisões; C1/C3/C5 | Fixtures SQL locais e controle CAS. Homologar administração, grants técnicos por canal, rotação/revogação, ownership imutável e fonte de App Secret sem usar identidade humana como principal M2M. |
| Adaptador/custódia S0, caminho a definir | Signer e trust anchors de recibo versionados, retenção de chaves, HA/readback; C3/C4/C6 | Signer Ed25519 sintético em memória; nenhuma chave ou serviço hospedado. |
| Mapeamento comercial posterior, sem arquivo solicitado | Ocorrências arquivadas não resolvem negócio; C1/C6 e catálogo PR19 | Conservar eventos não resolvidos; nenhuma relação automática por telefone ou política de envio. |

Procedimento de homologação Meta/Infra: conferir assinatura S0 com âncora confiável e contexto do webhook; exigir ACK_ELIGIBLE completo; em perda de resposta conservar mesmos bytes/identidade e obter nova prova/nonce; em conflito manter original e encaminhar; em inválido permanente aplicar política ratificada de quarentena, sem simular processamento integral; em indisponibilidade/incerteza seguir política de retry do provedor sem efeitos comerciais. A S0 desta entrega não decide o HTTP externo.

## Reprodução e descarte

Workflow exclusivo `exp-s0-meta-ingress-01.yml`, runner GitHub hospedado novo por job. PostgreSQL 17.6 por digest fixado; nome/container/volume/custódia UUID próprios e porta loopback reservada. Sem compartilhamento de worktree, credenciais, volume ou banco com I86. Cada execução controla seu descarte em finally; falha de cleanup reprova a prova física. Não armazenar logs Docker/env-file/DSNs/dumps em artifacts; somente TAP sintético e relatório de contagens/configuração/ausência.

Com Python3.12, Node22.23.3 e Docker local, em checkout próprio:

```sh
python3 integration/s0_meta_ingress/verify_scope.py
python3 -m integration.s0_meta_ingress.test_scope
python3 integration/s0_meta_ingress/verify_sources.py
python3 integration/s0_meta_ingress/run_models.py
python3 -m pip install -r integration/s0_meta_ingress/requirements.txt
PYTHONDONTWRITEBYTECODE=1 python3 -m integration.s0_meta_ingress.test_ingress
```

Definir `PYTHONDONTWRITEBYTECODE=1` também para as verificações de Python em checkout auditado, como faz a CI. Diretórios temporários ficam fora da árvore versionada e são removidos. O verificador compara histórico inteiro e estado final contra o SHA congelado, incluindo index, worktree e untracked inclusive ignorados; recusa alteração em qualquer um dos 364 arquivos herdados, exclusões, renames, merges, SHA de base substituído e arquivos fora do manifesto/allowlist. Edições próprias posteriores são permitidas sem ampliar escopo. Não certifica conteúdo semântico de um verificador maliciosamente reescrito; revisão da orquestração continua necessária.
