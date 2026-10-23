# WA-38 — Pedido de revisão técnica interfrentes, com evidência e bloqueios de produção

**23/10/2026 · PR #2 WhatsApp/Meta (Draft) · pacote pronto para revisão, SEM aceite externo.**

## Objetivo

Consolidar um **pedido de decisão técnica concreto** ao núcleo S0, S1, responsável Meta e Infra/Segurança/LGPD a partir dos **12 itens WA36** e dos **24 cenários positivos/negativos propostos na WA37**, sem gerar novo privilégio, endpoint ou migração. Esta solicitação deve ser respondida pelos próprios donos e **não é, por si, ratificação ou liberação de produção**.

Fontes consultadas diretamente em 23/10/2026, com snapshots reproduzíveis:

| Frente / documento | Referência consultada | Natureza |
|---|---|---|
| Nossa frente PR #2 | `4f1edcb88d33c65157f8d6020c89c98e27727e85` | Draft; CI [#39936039966](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39936039966), 3/3, Node 732/732 |
| Fundação S0 PR #1 | `75095fe9b6050c704df37c663bb92595bc6513b6` | Draft; [incrementos 028/029 e adendo 030](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/75095fe9b6050c704df37c663bb92595bc6513b6/docs/DEC_WA_01_03_INCREMENTOS_S0_2026_10_17.md) |
| Equipe S1 PR #5 | `7867403fad752353af90d57feb1cf2594b476dd4` | Draft; três perfis humanos, sem serviço Meta |
| Conclusão humana S0 PR #12 | `948891714f632adb6179cf3a11f362a6eb914f91` | Draft; prova humana GoTrue não é ingresso M2M |
| [DEC-WA-05](./decisao-titularidade-meta-por-concessionaria-v1_0.md) | versão documental vigente na nossa branch | **Decisão de negócio APROVADA**: conta/App/WABA/número sob concessionária, com Prumo delegada; **prova dos vínculos reais e onboarding AINDA PENDENTES** |

**Precedência essencial:** a referência antiga do PR #1 que cita DEC-WA-05 como integralmente pendente foi corrigida em seu próprio adendo 030. Não pedir que a decisão de titularidade seja tomada de novo. Solicitar **somente a comprovação operacional**, sem acessar painel, alterar App/credencial ou números comerciais nesta rodada.

## Perguntas de revisão — respostas com autoria e escopo

### Núcleo S0 — proprietário das interfaces comerciais e persistência

**S0-Q01 (WA36-M2M-IDENTITY / MACHINE-ROLE / RLS).** Qual identidade de máquina, audiência, autorização exata e canal de chamadas **interno** poderá anexar `FORENSIC_APPEND_ONLY`? Qual principal autentica a assinatura no receptor? Qual a evidência de que anon, authenticated, service_role, papel humano, IA e cliente não podem escrever nem usar `SECURITY DEFINER` oportunista? Não reaproveitar login GoTrue de Consultor/Gestor/Diretor como webhook.

**S0-Q02 (WA36-SCOPE-BINDING / NONCE-ATOMICITY).** Qual vínculo persistente e revisional conecta **App/WABA/PhoneNumberID/wamid/destinatário** à **concessionaria_id/canal_id/caso/tentativa**? Em qual fronteira S0 se validam origem/tenant/revisão, assinatura interna, nonce exclusivo e evento de status **no mesmo COMMIT**, sob locks ratificados com S1? O runner WA35 usa SQL privilegiado e **não responde** a essa pergunta.

**S0-Q03 (WA36-CALLBACK-DEDUPE / ACK-RETRY).** O [incremento 029](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/75095fe9b6050c704df37c663bb92595bc6513b6/docs/DEC_WA_01_03_INCREMENTOS_S0_2026_10_17.md) tem inbox/evento/tarefa durável por lote sintético, com rollback integral; WA35 admite **exatamente um status por POST**. Devemos registrar um POST multi-evento como **lote atômico**, particionar por App/loja sob transações separadas ou recusar e sinalizar redelivery? Precisamos fixar: identidade por callback versus `statuses[].id` (normalmente `wamid` da mensagem, não chave única de callback), fingerprint, duplicata, conflito, atraso, erro parcial e o momento correto de HTTP ACK. **Nenhum exemplo de laboratório autoriza ACK ou reenvio Graph.**

**S0-Q04 (identidade 8↔9).** O [incremento 028](https://github.com/prumogrowth/Prumo-Growth---Platform/blob/75095fe9b6050c704df37c663bb92595bc6513b6/docs/DEC_WA_01_03_INCREMENTOS_S0_2026_10_17.md) usa `p_mobile_confirmado` apenas como fixture e preserva ambiguidades. Qual fonte técnica realmente autorizará conversão de telefone BR 8↔9, distinguindo número do **cliente** (pode aparecer em várias lojas) do número **emissor** (exclusividade global)? **Não** transformar equivalência heurística em destinatário confirmado nem prova civil de titularidade.

### S1 — titular de concessão, pessoas e ordem de locks

**S1-Q01 (WA36-MACHINE-ROLE / LOCK-ORDER / REVOCATION).** Confirmar se o ingresso técnico deve depender de estado de atribuição/concessão da equipe antes de anexar um evento **estritamente forense**, e em quais estados uma revogação mantém somente trilha histórica sem reabrir fluxo. Indicar a ordem exata de locks compartilhados S1→S0. Os papéis oficiais **Diretor/Gestor/Consultor** são humanos e não devem emitir tokens de serviço Meta.

**S1-Q02 (WA36-SCOPE-BINDING).** Qual autoridade fornece revisão transacional de loja/canal/caso quando concessionária A e B compartilham um mesmo número de cliente? Quem pode rotacionar/cancelar binding e como impedir leitura obsoleta até COMMIT?

### Responsável WhatsApp/Meta (nossa frente) + núcleo S0

**META-Q01 (WA36-META-PROVENANCE / CALLBACK-DEDUPE).** Assinatura é HMAC dos **bytes brutos** sob segredo do App selecionado pela rota de servidor; só depois do MAC validar associar WABA/PhoneNumberID à loja. Ratificar a taxonomia de `sent/delivered/read/failed`, diferenças entre status de provedor e **estado comercial**, e dedupe apropriada sem presumir ID único para cada evento. A hash sintética WA35 de status+timestamp **não é ID certificado pela Meta**.

**META-Q02 (WA36-REVOCATION / ACK-RETRY).** Definir comportamento para callbacks assinados que cheguem após opt-out, troca de template, revogação de concessão ou pedido já encerrado: arquivo técnico mínimo permitido, sem autorização Graph, ACK somente se operação de ingresso durável for confirmada. Definir resposta segura para commit incerto e não recorrer a retry Graph por ausência de recibo local.

### Infra / Segurança / LGPD + concessionárias

**INFRA-Q01 (WA36-KEY-SEPARATION / M2M-IDENTITY).** Escolher e registrar mecanismo de identidade máquina, credenciais isoladas, rotação/revogação e auditoria, sem segredos em Git, sem login humano como serviço, sem permitir assinatura interna produzida por cliente ou IA.

**INFRA-Q02 (WA36-RETENTION-LGPD).** Aprovar finalidade, retenção, expurgo, visibilidade por loja, logs mínimos, trilha de acesso e segregação de evidência forense versus conteúdo da conversa. Nenhum `raw_body`, `wamid` ou destinatário deve ser divulgado por prompt/HTTP público.

**TENANT-Q01 (DEC-WA-05 — evidência operacional, NÃO nova decisão).** Concessionária comprova no contexto autorizado: titularidade de Business Manager, App, WABA, Phone Number ID, delegação revogável à Prumo, permissões e situação do número comercial. Não acessar nem inscrever número real antes de autorização de onboarding e plano de reversão.

## Pacote de aceite referenciado — critérios positivos E negativos

A [WA37](./wa37-contrato-aceite-interfrentes-m2m-2026-10-23.md) mapeia os seguintes pares, **ainda não executados em ambiente homologado**:

| Área | IDs WA36 | Provas mínimas externas |
|---|---|---|
| Identidade de máquina e ingressão confiável | `WA36-M2M-IDENTITY`, `WA36-META-PROVENANCE` | `WA37-P01 / WA37-N01`, `WA37-P02 / WA37-N02` |
| Gestão de credenciais e escopo por tenant | `WA36-KEY-SEPARATION`, `WA36-SCOPE-BINDING` | `WA37-P03 / WA37-N03`, `WA37-P04 / WA37-N04` |
| Permissão do serviço, atomicidade, locks e RLS | `WA36-MACHINE-ROLE`, `WA36-NONCE-ATOMICITY`, `WA36-LOCK-ORDER`, `WA36-RLS-MIN-PRIVILEGE` | `WA37-P05 / WA37-N05`, `WA37-P06 / WA37-N06`, `WA37-P07 / WA37-N07`, `WA37-P08 / WA37-N08` |
| Repetição/ACK/contabilização | `WA36-CALLBACK-DEDUPE`, `WA36-ACK-RETRY` | `WA37-P09 / WA37-N09`, `WA37-P10 / WA37-N10` |
| Dados mínimos e revogação | `WA36-RETENTION-LGPD`, `WA36-REVOCATION` | `WA37-P11 / WA37-N11`, `WA37-P12 / WA37-N12` |

## O que caracteriza uma resposta válida

Resposta deve indicar **(a)** quem está legitimamente decidindo e por qual frente; **(b)** quais perguntas/IDs cobriu; **(c)** contrato/commit/revisão efetivamente analisados; **(d)** decisão **aceita, aceita com restrição ou rejeitada**; **(e)** evidências ou testes positivos e negativos realizados **pelo proprietário**; **(f)** limitações e próximos bloqueios. Um comentário de bot, falha de teste, checklist preenchido por nós ou referência ao PR #12 **não** são aceite.

Registro deste pedido num comentário **do PR #2**, sem mencionar contas aleatórias, solicitar reviewers não identificados, marcar o PR como pronto ou alterar PRs S0/S1. A possibilidade de resposta existe; **nenhuma revisão externa é assumida até evidência expressa na thread ou documento aprovado**.

## Estado e limite operacional

**WA-38 = solicitação entregue para revisão, não revisão concluída.** Laboratório WA27–36 possui provas PG17 e Node, e WA37 validou estrutura do checklist com 732/732 Node na execução [#39936039966](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39936039966). Não há CFI-01 Meta, usuário de serviço autenticado, chave produtiva, Graph, HTTP ACK, migração, deploy, merge, mudança no Supabase hospedado ou número comercial. PR #2 permanece **Draft**; não alterar papéis humanos, S0/S1, IA/OpenAI, frontend ou POC concessionária de demonstração.
