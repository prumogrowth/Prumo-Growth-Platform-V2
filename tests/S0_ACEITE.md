# Prumo — evidências de aceite PARCIAL S0 (17/10/2026)

Última suíte de regressão: [GitHub Actions #39062435159](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39062435159).
Banco: PostgreSQL 17 efêmero; identidade Supabase simulada exclusivamente para os testes. Nenhuma operação Meta, OpenAI, Banco ou MCP real. Não é aceite de produção.

## PASS apenas no escopo explicitamente testado

| Critério | Evidência |
|---|---|
| S0-A1 | FK cruzada A/B bloqueada; também FK lead-ciclo-caso na mesma loja |
| S0-A2 | Lote novo preserva novo item/reencontro e o histórico anterior, mesma chave não duplica (simulação SQL) |
| S0-A3 | Nono status comercial rejeitado |
| S0-A4 | Gestão e operações confinadas à loja/caso: SQL/RLS, gestores A/B e operadores |
| S0-A5 | Repetição de inbound com mesmo canal/ID não duplica; ID distinto preservado (simulação SQL) |
| D41 AP41-01/02/03 | Gestor A lê conversas D2 completas da sua loja, inclusive IA; B não |
| D41 AP41-05/06/09 | Autoatribuição, resposta simulada, remanejamento e revogação |
| Segurança da concessão | Usuário sem vínculo, anon, operador sem designação e vínculo expirar negam leitura/escrita indevida |
| Eventos | UNIQUE(ciclo,versão) para histórico impede duplicação, ainda sem serviço de transições completo |

**Logs e consultas realmente executados, não só expectativa do roteiro.** As migrations 001–005 estão apenas no GitHub e no PostgreSQL efêmero; projeto Supabase remoto continua SEM tabelas comerciais/migrations.

## Ainda NÃO VALIDADO

- Contrato real C01/C02 (API transacional e ingestão de provedores), concorrência multiworker, consulta ao id Meta real.
- Supabase Auth/Data API/Storage com identidades reais de teste, sem usar dados pessoais verdadeiros.
- Projeção D3/D4 e controles de acesso de cadastro/banco (sem tabela sensível implementada).
- AP41-07/08: correção versionada e remessa/resultado bancários simulados; AP41-10/11/12: MCP com confirmação e auditoria.
- Garantia atômica de mudança de estado + evento; contratação/uso dos provedores; painéis e fluxos reais.
- Retenção/LGPD, backup/restauração e estratégia operacional aprovada; não há testes RET/RES/REC integrais.
- Revisão humana final de migrações, configuração de grants/toggles API e procedimento de recuperação antes de deploy.

**Portão: PR continua DRAFT. Não fazer merge ou deploy remoto somente com os PASS desta página. A régua documental histórica 19F não é modificada automaticamente.**

## Incremento C01 e eventos atômicos — evidência em 17/10/2026

Evidência: [CI #39063441684](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39063441684), PostgreSQL 17 descartável.

| Teste da nova implementação | Resultado |
|---|---|
| TX-C01: função transacional de importação, linhas rejeitadas e reentrega com mesma chave | PASS (CI) |
| TX-AUTH: esquema interno não acessível a `anon` / `authenticated` | PASS (CI) |
| TX-STATUS: versão esperada, prova de inbound sintética, evento e idempotência | PASS (CI) |
| TX-HANDOFF: ciclo com caso humano não volta para atendimento pela IA | PASS (CI) |
| TX-CONC: duas conexões simultâneas, sem duplicar lote/lead/ciclo/item | PASS (CI) |

A função do lote **não é endpoint público**: exige execução interna com papel SQL `postgres` e verifica o ator gestor/loja. Ela ainda carece de um adaptador de identidade real, de política de retenção e de auditoria operacional. O controle de concorrência foi comprovado especificamente para duas chamadas concorrentes com a **mesma chave de lote**; lotes distintos, filas e concorrência de atribuições permanecem pendentes.

**S0 não homologado:** C02 real, Auth real, APIs Meta/Banco, acesso fino D3/D4, reações externas, backup/restauração e portões LGPD permanecem bloqueados. Nenhuma migração comercial foi aplicada ao Supabase remoto. Não alterar a porcentagem histórica de planejamento (19F) por esses testes.

## Auditoria corretiva — regra esclarecida de cliente x emissor (17/10/2026)

**Correção do registro anterior:** o requisito que impunha UNIQUE global no telefone de cliente foi **retratado**. O número do cliente pode existir em concessionárias diferentes; apenas o número de **atendimento emissor da Prumo** é exclusivo. A migração 007 foi excluída antes de implantar e a importação 006 voltou a deduplicar por `(concessionaria_id,telefone_cliente_normalizado)`. A migração 008 (leitura do lead por operador designado) permanece.

O link do CI antigo #39064447771 refere-se a implementação retirada e não serve como aceite vigente.

**Evidência corrigida e efetivamente executada:** [GitHub Actions #39065589861](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39065589861) — PostgreSQL 17 efêmero, resultado **PASS** com conferência dos logs. Critérios aprovados nesta simulação:
- Mesmo telefone em lojas A/B: 2 leads/ciclos independentes, RLS gestor A/B e nenhuma conversa cruzada.
- Mesmo telefone reimportado na MESMA loja: sem duplicação, com reencontro.
- Emissor Prumo repetido para duas lojas: rejeição por constraint única.
- Dois lotes concorrentes entre A/B para o mesmo cliente: dois leads/ciclos isolados, 0 itens rejeitados por compartilhamento.
- Operador não designado ou desatribuído não lê lead/conversa de outro caso.
- Demais testes C01, eventos, handoff e idempotência continuam obrigatórios.

**Portões permanecem:** Auth/REST em ambiente Supabase integrado, revisão de grants, backup/restauração, LGPD, aprovação humana, nenhuma migração no remoto.

**Evidência específica:** log `PASS TX-CROSS-SHOP: mesmo cliente em A e B sob concorrencia; historicos isolados`; `PASS TX-C01`, `PASS TX-STATUS`, `PASS TX-HANDOFF`, `PASS TX-CONC` e RLS A/B confirmados. Esses testes não substituem Supabase Auth real nem homologação operacional.

## Incremento C02 simulado — evidência de execução (17/10/2026)

CI [#39066422146](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39066422146) — `success`; conferidos os logs. PostgreSQL 17 descartável, sem canal Meta conectado.

| Caso | Evidência |
|---|---|
| C02-01 | mesmo telefone em A/B com canais diferentes, lead/ciclo independente; mesmo ID externo em A e B permitido |
| C02-02 | canal emissor exclusivo, canal desconhecido recusado, função interna sem acesso dos papéis API |
| C02-03 | segunda mensagem da mesma conversa não duplica status/evento |
| C02-04 | primeira resposta simulada depois de primeiro disparo enviado gera transição com evento |
| C02-05 | retorno após cadastro enviado ao banco cria caso humano; ciclo histórico intacto |
| C02-06 | retorno após vendido cria ocorrência humana distinta; sem retorno à IA |
| C02-07 | mais de um ciclo do mesmo lead não é associado arbitrariamente |
| C02-08 | gestores A/B só veem suas próprias mensagens mesmo com telefone de cliente igual |
| C02-CONC | webhook repetido concorrente cria uma só mensagem; dois eventos distintos em paralelo criam duas mensagens, apenas um lead/ciclo/conversa/evento |

**Limites:** este teste **não** autentica Meta, WhatsApp, IA, opt-in/out ou transporte HTTP; não cancela ENVIOS_TEMPLATE porque o planejador ainda não foi implementado; retorna `CANCELAMENTO_PENDENTE`. Roteamento `IA_PENDENTE`/`HUMANO_PENDENTE` não significa atendimento efetuado. Não libera S0/S2, merge nem implantação remota.

## Auditoria S0/C01/C02 — reparos executados e regressão

**CI validado:** [PostgreSQL 17 #39067051654](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39067051654) — `success`, logs C01/C02/concorrência/RLS conferidos. Dados e Auth exclusivamente sintéticos.

- PASS: C02-02 — rejeição de canal com identificador vazio ou espaços indevidos (migração 010).
- PASS: C02-07 — mensagem com vários ciclos possíveis é armazenada em `mensagens` e `pendencias_inbound_simulado`, sem atribuir ciclo/caso arbitrário, sem acionar IA, com reentrega idempotente (migração 011).
- PASS: C02-08 — gestor de A consegue consultar a pendência A; gestor de B não consegue consultar pendência A.
- PASS: demais C01/C02, mesmo cliente em A/B e emissores únicos, controle de status, handoff e múltiplas conexões concorrentes.

**Classificação: GO apenas para próxima engenharia sintética; NO-GO para uso real.** Documento completo: `docs/AUDITORIA_TECNICA_S0_C01_C02_2026_10_17.md`. Auth real, cancelamento de recontatos, prova bancária, integração Meta, tratamento humano de pendências, LGPD e backup/restauração continuam PENDENTES.

## Recontatos C05/C08 — entrega sintética, validação técnica 17/10/2026

[CI PostgreSQL 17 #39069478063 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39069478063), logs REC-01..06, C05-APPROVAL, C08-GESTOR, C08-PRIVATE e REC-RACE verificados.

| Teste | Resultado |
|---|---|
| REC-01/02 | PASS — plano idempotente e reserva sem transmissão externa |
| REC-03/04 | PASS — resposta C02 cancela programados/reservados da loja A sem afetar B; envio cancelado não volta à reserva |
| REC-05/06 | PASS — cancelamento não altera estado comercial; trilha de eventos e RLS A/B preservados |
| C05-APPROVAL | PASS — template sintético não aprovado recusado sem registro parcial |
| C08-GESTOR / C08-PRIVATE | PASS — gestor autorizado, expected_version, reexecução idempotente, sem execução da função via API |
| REC-RACE | PASS — duas conexões PostgreSQL; reserva→inbound e inbound→reserva não deixam envio obsoleto elegível |

Fonte de escopo: `docs/RECONTATOS_C05_C08_SIMULACAO_2026_10_17.md`.

O texto anterior que indicava **cancelamento de recontatos pendente** refere-se à versão anterior à migração 013; a pendência atual é **cancelamento operacional de envios reais e homologação Meta**, não a gravação sintética de cancelamento. Ainda não existe emissor real nem confirmação de entrega; não computar o aviso final como enviado nem 24 horas de silêncio.

## C04 — evidência fictícia de elegibilidade e opt-out (17/10/2026)

[GitHub Actions PostgreSQL 17 #39072889947 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39072889947): C04-01..06 aprovados, além das regressões C01/C02/C05/C08, REC-RACE, idempotência e RLS.

- C04-01: sem comprovação sequer sintética, C05 rejeita novo recontato; decisão indeterminada.
- C04-02: evidência fictícia da loja A não autoriza B; resultado positivo é SOMENTE para simulação.
- C04-03: opt-out grava supressão idempotente, cancela C08 pendentes e bloqueia reserva C06.
- C04-04: inbound espontâneo não é opt-in geral e não elimina supressão.
- C04-05: mesmo telefone de cliente em A/B sem compartilhar provas ou histórico.
- C04-06: RLS por concessionária e negação de escrita dos registros por usuário comum.
- [Supabase Auth/REST local #39072893018 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39072893018): AUTH-10 aprovado para as duas tabelas novas, acesso restrito por loja, operador/anon bloqueados e sem escrita via REST. AUTH-01..09 também aprovados.

**Escopo e pendências:** `docs/C04_ELEGIBILIDADE_OPTOUT_SIMULADO_2026_10_17.md`. Decisão sobre opt-out entre emissor/lojas [R/V]; sem comprovação Meta, LGPD, opt-in real, transporte de mensagens, recuperação ou produção. A evidência interna fictícia não é autorização comercial.

## Auditoria corretiva C04 antes de C07 — 17/10/2026

**[GitHub Actions PostgreSQL 17 #39073858011 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39073858011)**, logs inspecionados.

- `C04-RACE`: duas conexões PostgreSQL disputando opt-out e reserva em ambas as ordens; ambos os planos e tentativas resultaram cancelados, sem envio elegível.
- `C04-REPLAY`: a mesma chave de plano cancelado retorna `ALREADY_APPLIED`, mas sinaliza `estado_plano=cancelado` e `executavel_simulacao=false` (migração 017).
- `C04-04`: após opt-out, mensagem espontânea permanece inelegível para recontato, vai para revisão humana sintética, não reativa IA nem muda status comercial (migração 018).
- Restante da regressão de C01/C02/C04/C05/C08, oito estados e isolamento de concessionárias: PASS neste ambiente de teste.

Parecer: `docs/AUDITORIA_C04_PRE_C07_2026_10_17.md`. **GO somente simulação C07; NO-GO para operação real**. Auth/REST integrado da revisão atual requer evidência própria; teste baseline anterior [#39073125189](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39073125189) havia passado.

## C07 — callbacks técnicos sintéticos e controle de custos (17/10/2026)

[PostgreSQL 17 #39076677999 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39076677999). Evidências executadas: `PASS C07-01` a `PASS C07-05` (vínculo fictício, duplicidade e conflito, ordem tardia, incerteza/falha sem status comercial, pendência sem correlação, callback depois de opt-out, RLS A/B). As regressões anteriores também passaram no mesmo banco descartável.

**Auth/REST:** a suíte de integração de containers GoTrue/PostgREST ficou **intencionalmente SKIPPED** neste incremento para poupar minutos GitHub Actions; isso NÃO significa aprovação nova da tabela C07 pela API. Exige execução expressamente habilitada por etiqueta `run-auth-integration` ou via fluxo manual antes de qualquer gate de homologação. O teste anterior [#39074017823](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39074017823) comprovou C01–C04/C05–C08 pré-C07, não a migration 019.

**Economia:** workflow PG só com `push` seletivo por arquivos alterados (sem duplicação PR nem disparo por commits documentais), `cancel-in-progress` e timeout 5 min. Auth sob opt-in e timeout 12 min. Detalhes: `docs/CONTROLE_CUSTOS_GITHUB_ACTIONS_2026_10_17.md`.

**Gate:** GO apenas para engenharia C07 sintética; NO-GO para webhook Meta real, disparo, callbacks autenticados, relógio final + 24h ou alteração comercial por eventos simulados. Fontes: `docs/C07_CALLBACKS_SIMULADOS_2026_10_17.md`.

## C07 — reconciliação de incerteza e falhas (17/10/2026)

**[GitHub Actions PostgreSQL 17 #39078241536 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39078241536)**: `C07-REC-01..05` e regressões anteriores.

- REC-01: fila por loja para evento não correlacionado, resultado incerto, falha reportada e sinais contraditórios; reentrega não duplica.
- REC-02: duas notificações de falha no mesmo envio contam **uma tentativa distinta**; nova reserva bloqueada sem decisão de retry.
- REC-03: gestor A pode reconciliar só sua loja, `expected_version`, justificativa, vínculo fictício no mesmo canal e replay idempotente. Gestor B negado; histórico original permanece.
- REC-04: observação de falha impede **novo plano** mesmo depois de cancelamento do anterior e conclusão de revisão sem prova.
- REC-05: RLS por concessionária nas novas tabelas, sem UPDATE direto do gestor.
- **[GitHub Actions PostgreSQL 17 #39078390224 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39078390224)**: `C07-REC-RACE` com duas conexões resolvendo a mesma pendência; uma única auditoria, segunda execução `ALREADY_APPLIED`.

**Auth/REST:** foi acrescentado `AUTH-11` à suíte local para callbacks/pendências/associações/auditoria, mas essa suíte custosa **não foi acionada** nesta rodada. A migration 021 não está homologada por teste integrado PostgREST. Antes de qualquer gate externo, executar deliberadamente o teste integrado e revisar segurança.

**Norma:** `docs/C07_RECONCILIACAO_FALHAS_SIMULADAS_2026_10_17.md`. DEC-13/14/15 ainda pendentes; duas falhas técnicas NÃO equivalem a duas falhas qualificadas. Nenhum novo envio real, retry, 24h, prova Meta ou status `perdido` foi gerado. Somente engenharia sintética em ambiente isolado.

## Auditoria C07 após a reconciliação — 17/10/2026

- **[CI PostgreSQL 17 #39079075704 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39079075704)**: migrations 001–006, 008–022 e regressões de C01/C02/C04/C05/C07/C08 no PostgreSQL 17 descartável, incluindo os testes concorrentes.
- **C07-AUD-01 — PASS**: `agendar_recontatos_sinteticos` reconhece a mesma chave idempotente, mas responde `executavel_simulacao=false` quando um plano ainda `ativo` acumula sinal de falha/incerteza no ciclo. Não concede novo envio.
- **C07-REC-01..05, C07-REC-RACE — PASS**: filas de reconciliação, contagem de falhas por tentativa, vínculo versionado, restrição interlojas, nenhuma repetição de auditoria e nenhum retry cego.
- Migração **022** reforça os diagnósticos de associação manual, respeitando eventos históricos e sem alterar estados comerciais.
- **Auth/REST: PENDENTE, não falhou nem passou** para migrations 019–022. O teste `AUTH-11` existe no script mas não foi executado devido ao gate deliberado de minutos GitHub Actions. Fazer execução opt-in antes de homologar C07 por Data API.
- Ver parecer: `docs/AUDITORIA_C07_RECONCILIACAO_2026_10_17.md`. GO apenas para continuar engenharia sintética; NO-GO para produção/merge/deploy/Meta.

## Gate Auth/REST de C07 — execução deliberada (17/10/2026)

**[GitHub Actions #39079580129 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39079580129)**. Teste GoTrue/PostgREST rodado **uma única vez** em Supabase descartável com limite configurado de 12 minutos, no código vigente (migrations até 022). Logs conferidos: `AUTH-01` a `AUTH-11` PASS (sequência técnica dos rótulos varia).

- `AUTH-11` PASS: tabelas `eventos_callback_sinteticos`, `pendencias_reconciliacao_c07_sinteticas`, `associacoes_callback_c07_sinteticas` e `auditoria_reconciliacao_c07_sintetica`. Gestores A/B leem somente a própria concessionária; operador, sem vínculo e anônimo não leem; tentativas de INSERT via REST bloqueadas.
- A revogação do gestor bloqueia essas leituras mesmo com JWT previamente emitido. Revisões continuam operando somente via funções internas sob identidade privilegiada no sandbox.
- Após o job, a etiqueta `run-auth-integration` foi retirada do PR para não deixar novo disparo habilitado. **Não foi usado `db push` nem migração do projeto hospedado.**
- [Regressão PostgreSQL #39079075704 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39079075704), incluindo `C07-AUD-01` e concorrência. Ambos são testes **locais**, não homologação de origem Meta, LGPD ou operação real.

Esse gate resolve a pendência de **validação Auth/REST local de C07**; não resolve backend autenticado de produção, tráfego Meta real, recuperação, backup/restore, revisão DEC-13/14/15 ou autorização para merge/deploy.

## Backend autenticado S0 — gate de identidade (17/10/2026)

- [**PostgreSQL 17 #39080940371 — PASS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39080940371): doze testes unitários do pacote `backend` e regressões C01/C02/C04/C05/C07/C08 após endurecer DSN para `postgres` local exato ou `prumo_s0_test_*` local. Corridas anteriores continuam PASS.
- [**Supabase Auth/REST local #39080757870 — PASS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39080757870): `AUTH-01..12` com JWT e sessão reais do GoTrue temporário. `AUTH-12` comprova ator derivado do token, sessão `auth.sessions` ativa, gestor B autorizado, negativas de ator inventado/gestor revogado/operador/outro escopo e bloqueio após exclusão da sessão. Corresponde à versão funcional anterior ao reforço estrito do prefixo de DSN, sem alteração do caminho de sessão/SQL.
- Uma tentativa anterior (#39080593068) detectou falha de importação Python no runner e foi reparada antes do PASS integrado. Etiqueta `run-auth-integration` removida após execução.
- `backend/identity_boundary.py` é **biblioteca interna e somente para S0 local**, não um servidor ou API publicamente implantada. `PsycopgTrustedDatabase` usa postgres local privilegiado, não aceitável para produção.
- **NO-GO** para deploy remoto, cliente real, credenciais administrativas expostas, Meta ou operação comercial. Documento: `docs/BACKEND_IDENTIDADE_AUTENTICADA_S0_2026_10_17.md` e `docs/GATE_BACKEND_AUTH_S0_2026_10_17.md`.

## Papel de gateway restrito e auditoria — 17/10/2026

- **[PostgreSQL 17 #39082041958 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39082041958)**. Migração **023**, testes **GW-01..GW-05** e **15 testes unitários** do backend passaram, além das regressões comerciais anteriores e concorrência. O papel `prumo_s0_gateway` é NOLOGIN/NOINHERIT, sem SELECT nas tabelas comerciais ou nas sessões e sem EXECUTE nas funções antigas. As duas wrappers privadas exigem sessão ativa e chamam o domínio que revalida gestor, loja e versão. Auditoria transacional confirma APPLIED/ALREADY_APPLIED, sem gravar segredo.
- **[Supabase Auth/REST local #39082125663 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39082125663)**. Logs: AUTH-01..13 PASS e AUTH-13-REVOKE PASS. Um login sintético `prumo_gateway_ci` foi provisionado **apenas em Supabase descartável**, sem permissão de SELECT comercial, e executou a reconciliação permitida. Escopo cruzado, `ator_id` forjado e sessão revogada foram negados; auditoria de resultados aplicado/replay verificada. O job foi acionado uma vez por etiqueta opt-in, retirada depois.
- As primeiras rodadas de testes GW falharam por construção incorreta da assertion de acesso negado e ambiguidade de coluna em fixture; corrigidas antes do PASS. Nenhuma falha ou alteração chegou ao Supabase remoto.
- `docs/GATEWAY_PRIVILEGIOS_MINIMOS_AUDITORIA_S0_2026_10_17.md` contém modelo, limitações e bloqueios. **GO apenas para evolução sintética; NO-GO para login operacional, HTTP público, Meta, produção e deploy hospedado.**

## Auditoria corretiva do gateway — 17/10/2026

- **[PostgreSQL 17 #39082947695 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39082947695)**: migrações até **024**, `GW-01..07`, 16 testes unitários Python e regressões anteriores em banco descartável.
- **GW-06**: proprietário `postgres`, `SECURITY DEFINER`, EXECUTE negado a anon/auth/service_role e permitido somente ao papel `prumo_s0_gateway`, além de ausência de SELECT/INSERT/UPDATE/DELETE na auditoria.
- **GW-07**: o UUID de sessão foi removido da auditoria; fingerprint SHA-256 preserva correlação sem guardar o valor original. Sessão real continua necessária para executar, não é registrada em claro.
- **Unit test 03b**: JWT com Base64 malformado é negado, sem propagação de erro interno `binascii.Error`.
- **Auth/REST #39082125663 — PASS apenas baseline até 023**: ainda **não executado** depois da alteração 024. Nova validação integrada permanece opt-in para respeitar o orçamento Actions.
- **Gate de segurança:** SQL login comprometido que conheça `p_ator/p_sessao` válidos ainda pode chamar diretamente wrappers `SECURITY DEFINER`, sem token GoTrue. Bloqueio de produção e API pública; exige desenho de confiança e credenciais apropriado. Documentado em `docs/AUDITORIA_GATEWAY_S0_2026_10_17.md`.

## Gateway S0 — segunda prova HMAC e anti-replay (18/10/2026)

- [**PostgreSQL 17 #39083792469 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39083792469): migrations candidatas até **025**, `GW-01..07` e **18 testes unitários Python**, além das regressões anteriores. O login gateway não executa as wrappers legadas nem lê segredos; HMAC alterado/expirado e nonce reutilizado são negados. Prova nova permite `ALREADY_APPLIED` sem dupla mutação, e a revogação da sessão continua efetiva.
- [**Supabase local GoTrue/REST #39083914275 — SUCCESS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39083914275): logs `AUTH-01..14`, incluindo `AUTH-14` (login SQL sem HMAC não invoca wrappers antigas nem novas sem prova) e `AUTH-13` (gestor e sessão válidos, auditoria de operação e replay); restrições A/B/C e revogação intactas. Integração executada **uma vez** em Supabase efêmero, com limite de 12 minutos. Etiqueta `run-auth-integration` retirada.
- Migration `025_s0_prova_dupla_gateway.sql` cria **estruturas de chave vazias**; a chave HMAC fixa nos testes é **somente sintética** e não representa credencial operacional. Separação entre senha SQL e assinatura de curta duração com nonce transacional reduz risco de comprometimento apenas da senha SQL.
- **NO-GO para produção**: chave HMAC e senha SQL presentes no mesmo processo de teste; comprometimento combinado, funções `SECURITY DEFINER` de dono privilegiado, rotação de segredos, log de negativas, retenção/poda de nonces, TLS/rate limit, backup/restore, LGPD e autenticação real Meta/Banco exigem revisão independente. Sem migração comercial Supabase remoto.
- Guia: `docs/GATEWAY_PROVA_DUPLA_S0_2026_10_18.md`. A pendência da auditoria 024 quanto a Auth/REST foi superada nesta execução local 025, mas não houve homologação comercial nem deploy.

## Ciclo HMAC, nonce e registro sanitizado de negativas — gate S0 (17/10/2026)

- **[PostgreSQL 17 #39084739387 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39084739387)**: migrations candidatas até **026**, testes **KEY-01..05**, **24 testes unitários Python** e regressões comerciais/concor­rência anteriores. A migração 026 exige registro inativo e ativação versionada de chave, impede reativação após revogação, impede mudança de segredo com o mesmo ID, controla expiração e contabiliza manutenção de nonces com janela mínima de dez minutos.
- **[GoTrue/Auth/REST local #39084803545 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39084803545)**: logs **AUTH-01..14** e AUTH-13-REVOKE. As fixtures registram chave fictícia inicialmente inativa e a ativam via função administrativa da 026. Passaram negativas de login SQL sem HMAC, escopo A/B, autorização por gestor, revogação de sessão e auditoria do gateway.
- O módulo `backend/security_events.py` emite apenas categoria controlada de negativa + nome permitido da operação; testes provam que JWT, texto bruto, erros e IDs não saem pelo logger. **Não é ainda coleta central durável, com alertas e retenção.**
- O teste Auth foi executado uma vez mediante `run-auth-integration` e a etiqueta foi retirada após PASS; o runner mantém timeout máximo de 12 minutos.
- `docs/SEGURANCA_ROTACAO_CHAVES_LOGS_S0_2026_10_17.md` descreve contratos e riscos. Chaves do banco são `bytea` na tabela privada, **não cofre de segredos**; funções `SECURITY DEFINER` continuam com dono privilegiado. Nenhum dado operacional ou migração remota foi aplicado. **GO apenas S0; NO-GO produção/API/Meta/merge.**

## Privilégio mínimo do verificador HMAC — 17/10/2026

- **[PostgreSQL 17 #39085850000 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39085850000)**: migrations candidatas até **027**, `OWNER-01..03`, `GW-01..07`, `KEY-01..05`, **24 testes unitários** e regressões/comportamentos concorrentes anteriores. O verificador passa a executar como `prumo_s0_signer` NOLOGIN/NOINHERIT, sem privilégios comerciais, sem acesso às sessões e sem EXECUTE de wrappers comerciais.
- Alterações oficiais de chave e sua verificação adquirem o mesmo **advisory lock transacional**; isso evita conceder UPDATE no material de HMAC ao verificador. Operações SQL diretas do superusuário **não** são protegidas por esse protocolo de lock.
- A primeira regressão detectou que `SELECT FOR SHARE` exige UPDATE; o modelo foi ajustado para bloqueio cooperativo. A segunda detectou montagem incorreta do SQL; a terceira detectou fixture sem `auth.sessions` no PostgreSQL mínimo. Todos foram corrigidos antes do PASS final.
- **Limite:** a camada de domínio ainda usa `SECURITY DEFINER` de proprietário `postgres`. Chaves seguem no mesmo PostgreSQL, e segredo SQL + HMAC no mesmo protótipo; isto **não** é isolamento para produção. Documento: `docs/SEGURANCA_OWNER_HMAC_S0_2026_10_17.md`.

### Complemento de compatibilidade PostgreSQL/Supabase — migração 027 (17/10/2026)

- [**PostgreSQL 17 #39086358857 — PASS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39086358857): OWNER-01..03 e todas as regressões SQL/Python. A migração cria `prumo_s0_signer` sem login e sem privilégios comerciais e transfere somente o verificador HMAC para esse proprietário.
- No PostgreSQL 17, `SELECT FOR SHARE` exigiria um privilégio adicional de UPDATE. O fluxo oficial de verificação e ativação/revogação usa agora advisory lock transacional compartilhado, sem conceder UPDATE no segredo ao verificador.
- A execução local Supabase anterior #39085941430 detectou associação administrativa padrão de papel (SET FALSE); a #39086175162 detectou que a troca de proprietário exige SET TRUE. A política foi corrigida para permitir `SET ROLE` somente ao papel administrativo `postgres`, sem modificar o papel reservado `supabase_admin` e mantendo membros não administrativos proibidos. Essas tentativas **falharam antes de passar todos os testes Auth** e não podem ser citadas como aprovação.
- As funções comerciais `SECURITY DEFINER` continuam pertencendo a `postgres`. Esta entrega é apenas uma redução incremental de privilégios, não a conclusão do risco de produção.

- **[Regressão PostgreSQL final #39086930417 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39086930417)**: a migração ajustada concede ao `postgres` gerenciado apenas `SET TRUE, INHERIT FALSE` para a transferência de propriedade. Provas `OWNER-01..03`, `GW-01..07` e `KEY-01..05` mantidas. O teste integrado Auth/REST desta versão deve ser registrado separadamente.

### Fechamento do gate PostgreSQL 027 — 17/10/2026

- [**PostgreSQL 17 #39087193113 — PASS**](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39087193113). OWNER-01..03, GW-01..07, KEY-01..05, **24 testes unitários** e regressões anteriores aprovados na versão final de migração 027.
- Após detectar no Supabase a necessidade de `SET ROLE` para o papel `postgres` gerenciado e de `CREATE` no esquema para o novo proprietário, a migration passou a conceder `SET TRUE, INHERIT FALSE` **apenas** a `postgres`, sem alterar o reservado `supabase_admin`. A permissão `CREATE` é concedida e revogada **dentro de um único bloco transacional**; o teste OWNER-02 confirma que não fica permanente.
- **Auth/REST da versão final 027: PENDENTE, não aprovado.** A última tentativa [#39086997963](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39086997963) falhou na alteração de propriedade, antes dos testes Auth; o reparo de `CREATE` foi submetido e aprovado somente no PostgreSQL #39087193113. Não iniciar repetidas suítes Auth caras até uma revisão específica da compatibilidade.
- As migrações candidatas continuam apenas no GitHub; PR DRAFT, nenhum deploy remoto ou chave operacional. **GO somente engenharia sintética PG; NO-GO homologação Supabase/produção.**

## Fechamento da auditoria de compatibilidade Supabase 027 — 18/10/2026

- **[PostgreSQL 17 #39088775699 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39088775699)**: 24 testes unitários Python, OWNER-01..03, GW-01..07, KEY-01..05 e regressões S0. Migração 027 testada no commit de código `99504c968350267873d084c4f0391746beaa43ee`.
- **[Supabase Auth/REST local #39088838150 — PASS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39088838150)**: migration 027 aplicada com sucesso em Supabase EFÊMERO; logs de `AUTH-01` a `AUTH-14` e `AUTH-13-REVOKE` aprovados. O ambiente temporário foi encerrado após o teste.
- A tentativa anterior **[#39088483639 — FALHOU](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39088483639)** na migração 027, porque `REVOKE EXECUTE` foi executado **depois** de transferir o proprietário da função para `prumo_s0_signer`. No Supabase gerenciado, `postgres` não tinha autorização para revogar privilégios daquela função nesse ponto. **Correção:** revogação pública antes do `ALTER OWNER` e concessão explícita de `EXECUTE` ao administrador interno pelo novo proprietário. Nenhum EXECUTE foi concedido ao gateway, anon, authenticated ou service_role.
- **Custo:** execução integrada deliberada, com `timeout-minutes: 12`. Etiqueta `run-auth-integration` retirada; não foi executado deploy comercial remoto.
- **Inspeção do Supabase hospedado:** projeto ativo/saudável; zero tabelas `public` e zero migrações comerciais; Security Advisor sem alertas. `public.rls_auto_enable()` não executável por anon ou authenticated. O advisor remoto não verifica o SQL candidato não implantado.
- **Gate:** GO exclusivamente para continuar engenharia sintética local. Continuam pendentes desenho de cofre/isolamento de segredos, proprietário restrito das wrappers comerciais (ainda `postgres`), logs duráveis de negativas, retenção/backup/restore, LGPD e aceite para operação real. **NO-GO** para merge, SQL hospedado, cliente real, Meta/Banco e produção.

Esta atualização substitui a indicação anterior de que o teste Auth/REST da versão final 027 ainda estava pendente; mantém os erros antigos como histórico auditável.


## Incremento documental — dependências de privilégio comercial (17/10/2026)

Auditoria **estática**, sem modificação SQL ou novo teste: `docs/AUDITORIA_PRIVILEGIOS_COMERCIAIS_S0_2026_10_17.md`. Confirmadas no código as cadeias `gateway_assinado` → verificador HMAC / wrapper legada → `auth.sessions` / função de domínio / auditoria. Migração 023 declara explicitamente dependência de `current_user='postgres'` em código de domínio. **Nenhuma transferência de owner das funções comerciais aprovada ou executada.** Os CI #39088775699 (PG) e #39088838150 (Auth/REST) permanecem somente evidências da 027, não deste incremento documental. Próximo gate: inventário de grants e funções no PostgreSQL efêmero, implementação mínima e testes negativos antes de Auth/REST deliberado. Supabase hospedado: somente leitura, 0 tabelas `public`, 0 migrações, advisor de segurança sem alertas.


## DEC-WA-01/02/03 — incrementos sintéticos 028/029 (18/10/2026 UTC)

**Evidência executada:** [GitHub Actions PostgreSQL 17 #39092398299 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39092398299), commit `2697677e02178edc3a01f23c8377e36ac2e2c86e`. Logs conferidos: `WA-ID-01..05`, `WA-IN-01..03`, `WA-OUT-01`, `WA-SEC-01` **PASS**; as regressões S0 anteriores e 24 testes unitários Python também passaram. PostgreSQL 17 **descartável**, não Supabase hospedado.

- **028 — `202610180028_s0_identidade_aliases_sinteticos.sql`**: `prumo_private.aliases_identidade_s0`, histórico de identidade e pendências; resolvedor transacional de alias BR 8↔9 por concessionária **somente com evidência móvel de fixture**, conflito/necessidade de revisão sem fusão e ponte privada que reutiliza C02 sintético. Testado 9→8, 8→9, reentrega do mesmo ID, isolamento A/B, telefone fixo sem prova, colisão legada e ACL. **C01/C02 públicos internos legados não foram substituídos; não declarar dedupe geral de importação 8↔9 concluído.**
- **029 — `202610180029_s0_inbox_outbox_sinteticos.sql`**: lote técnico privado com persistência de evento + tarefa na mesma transação, fingerprint/ID de dedupe, rejeição de lote parcial, reserva/lease de worker por loja e outbox de intenção C03/C06/C12 **bloqueada para envio**. Testado lote de 2 inbound + 2 status, duplicata, conflito, rollback, isolamento de claims/ACL e idempotência de intenção. **Não há worker de aplicação C02/C07, função HTTP de ACK Meta, publicação Graph ou retry externo.**
- `scripts/run-s0-local.sh` inclui as duas migrations e os dois testes novos; não mudou o gatilho Auth/REST pesado. Documentação: `docs/DEC_WA_01_03_INCREMENTOS_S0_2026_10_17.md`.

**Limites:** a POC Meta hospedada permanece isolada; o banco Supabase hospedado não recebeu migrações, números comerciais ou novas tabelas. Sem prova Meta real da equivalência celular, sem segredo de lookup/rotatividade, sem integração de aliases no C01, sem autorização operacional dos trabalhadores/saídas, sem log externo ou retenção LGPD final. DEC-WA-04/05/06 continuam pendentes. PR #1 e PR #2 **Draft e sem merge**. **GO** somente para mais engenharia local sintética; **NO-GO** para implantação, Meta/Banco/IA real ou produção. Teste Auth/REST das migrações 028/029 permanece **NÃO EXECUTADO**.


## Marco corretivo S0/030 — DEC-WA-01/02/03 e precedência DEC-WA-05 (18/10/2026 UTC)

**Evidência verificada:** [GitHub Actions PostgreSQL 17 #39094224312 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39094224312), commit testado `096997891b376db5c069dc4e644a12af8123650e`. Logs do job `s0-db-isolation` conferidos, incluindo **24 testes Python — OK**, regressões S0 antigas, WA-ID-01..05, WA-IN-01..03, WA-OUT-01, WA-SEC-01 e os novos:

| Caso | Resultado confirmado em PG 17 descartável |
|---|---|
| WA30-ID-01 | PASS — pendência repetida idêntica; texto ou número divergente rejeitados (sem sobrescrever prova) |
| WA30-ID-02 | PASS — FK composta alias/lead/loja e evidência de variante |
| WA30-IN-01 | PASS — lote único com 2 lojas, 2 mensagens e 2 status; replay e conflito de payload |
| WA30-IN-02 | PASS — spoof de loja/app negado; nenhum commit parcial |
| WA30-SEC-01 | PASS — fixture privada não acessível a papéis de API/gateway |
| WA30-CONC-01 | PASS — **duas sessões concorrentes** de variantes 8↔9 → um lead/ciclo e duas mensagens |
| WA30-CONC-02/03 | PASS — disputa entre duas sessões de worker por uma tarefa; retomada após lease artificialmente expirada |

**Histórico CI:** [#39094102278 — FAILURE](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39094102278) ocorreu **após os testes SQL novos passarem**, porque um UUID de fixture no script de concorrência colidiu com fixture de outro teste existente; corrigido com IDs exclusivos no commit `0969978` antes do CI final aprovado. Não tratar a falha histórica como pendência ainda aberta. Execuções intermediárias foram canceladas automaticamente pelo `cancel-in-progress`.

**Implementação:** `supabase/migrations/202610180030_s0_replay_multicanal_fixture.sql`, `supabase/tests/s0_wa_030_auditoria.sql`, `scripts/test_s0_wa_030_concurrency.sh` integrados ao runner de banco descartável. Documentação detalhada: `docs/AUDITORIA_CORRECOES_WA_S0_030_2026_10_18.md`.

**Limitações do aceite:** é prova **exclusivamente de PostgreSQL sintético**, não GoTrue/PostgREST local gerenciado, Meta Graph, sandbox POC ou Supabase hospedado. A referência `payload_fixture_s0` é marcador sintético privado, **não** conteúdo pessoal criptografado, cofre ou recibo de entrega. A função retorna `FIXTURE_BATCH_STORED`, não `commit_state='COMMITTED'`, e **não justifica ACK HTTP**. C01 legado ainda não resolve aliases 8↔9, e operações C02/C07 reais, worker, retry, quarentena operacional e autorização de saída permanecem pendentes. As funções comerciais `SECURITY DEFINER postgres` ainda não passaram pela redução de ownership.

**Decisões:** DEC-WA-05 **aprovada apenas para titularidade dos Apps/WABAs/números por concessionária**; onboarding/mandato efetivo/permissões/produção dependem de validação. DEC-WA-04 e DEC-WA-06 **pendentes**. Nenhum merge, serviço externo, operação comercial, custo pago ou migration hospedada. **GO** somente para mais engenharia e integração sintética sob gates; **NO-GO** para API pública, webhook real, canal comercial ou produção.


## S0/031 — C01 opt-in com aliases 8↔9, integração sintética C02 (18/10/2026 UTC)

**CI PostgreSQL 17 descartável:** [GitHub Actions #39094706263 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39094706263), commit de código e runner testado `f8513baaae65802bd509b42af8313bd3bef80434`. Conferidos no log do job `s0-db-isolation`: `WA31-01` (lote com 8↔9, A/B, rejeições, replay e domínio de chave legado), `WA31-02` (C01→C02 mesma identidade sem novo ciclo), `WA31-03` (contato legado sem prova e duas identidades conflitantes), `WA31-04` (gestor fora de escopo, entrada não elegível e ACL privada), `WA31-CONC` (**duas sessões concorrentes** C01/C02 e C01/C01), **todos PASS**. Regressões antigas S0, WA28–WA30 e **24 testes Python — OK**, sem erros nos logs.

**Arquivos:** `supabase/migrations/202610180031_s0_c01_alias_importacao_sintetica.sql`; `supabase/tests/s0_wa_031_c01_identidade.sql`; `scripts/test_s0_wa_031_c01_concurrency.sh`; `scripts/run-s0-local.sh`; `docs/S0_031_C01_ALIAS_IMPORTACAO_2026_10_18.md`. Migrações 001–030 não foram alteradas.

**Aceite restrito:** novo C01 é opt-in, privado, `SECURITY INVOKER`, exige `current_user='postgres'`, vínculo gestor/loja, e declaração de prova móvel **exclusivamente fictícia**. Usa o resolvedor 028/030 sem duplicar tabelas comerciais. A importação C01 antiga continua por número textual. Não houve prova real de titularidade, ligação com arquivo externo de clientes, garantia de equivalência Meta, teste Auth/REST gerenciado das migrations 028–031, liberação de worker público ou persistência de mensagens Meta. A outbox continua bloqueada e o Supabase hospedado não recebeu migrations.

**Decisões:** DEC-WA-01/02/03 aprovadas como direção; DEC-WA-05 aprovada quanto à titularidade dos recursos Meta **por concessionária**, sem onboard/credenciais/canais comerciais; DEC-WA-04 e DEC-WA-06 pendentes. PR #1 e PR #2 permanecem Draft e sem merge. **GO** só para continuação de engenharia sintética; **NO-GO** para deploy, operação bancária, Meta real ou envio externo.


## S0/032 — ciclo de vida da inbox, fencing e reconciliação sintética (18/10/2026 UTC)

**CI confirmado:** [GitHub Actions PostgreSQL 17 #39095389775 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39095389775), commit de código `0c0f90a3d789f84437c7fe5fc9f7bbd5eefaa2ce`. Logs efetivamente conferidos, sem erros: **WA32-01..06 PASS**, **WA32-CONC-01 PASS**, **WA30-CONC-01 e WA30-CONC-02/03 ajustados PASS**, regressões S0 anteriores e **24 testes Python OK**.

| Evidência nova | O que comprova no PostgreSQL descartável |
|---|---|
| WA32-01 | Conclusão por versão/worker/lease, replay da mesma conclusão, auditoria protegida de mutação |
| WA32-02 | Retry seguro de fixture com agendamento, limite de três reservas e `DEAD_LETTER` |
| WA32-03 | Resultado incerto enviado para `QUARANTINED` sem auto-retry |
| WA32-04 | Lease vencido não pode ser reassumido automaticamente; conclusão tardia e revisão com versão errada negadas |
| WA32-05 | Apenas declaração sintética e explícita de `SEM_EFEITO_FIXTURE` permite reprogramar |
| WA32-06 | Loja/canal estritos, falha definitiva e ACL privada |
| WA32-CONC-01 | Duas conexões concorrentes disputando resultado de uma tarefa; só o titular confirma, sem reconciliação obsoleta |
| WA30-CONC-02/03 | Teste histórico atualizado para nova regra mais restritiva de recuperação com decisão explícita |

**Implementação:** migration `202610180032_s0_ciclo_tarefas_ingresso.sql`; testes `supabase/tests/s0_wa_032_lifecycle.sql` e `scripts/test_s0_wa_032_lifecycle_concurrency.sh`; alteração deliberada de `scripts/test_s0_wa_030_concurrency.sh`; runner `scripts/run-s0-local.sh`. Especificação `docs/S0_032_CICLO_TAREFAS_2026_10_18.md`.

**Limites:** nenhum worker real C02/C07, mensagem efetivamente aplicada, API HTTP, ACK Meta, autenticação de serviço, payload de PII, cofre, credencial operacional, envio de saída ou integração bancária foi testado ou habilitado. `APLICADO_SINTETICO` é apenas declaração fictícia de worker; não certifica efeito comercial exatamente uma vez. `QUARANTINED` e `DEAD_LETTER` são **estados técnicos**, não novos estados comerciais. Três tentativas e atrasos 15/60 segundos são parâmetros de laboratório, sujeitos a DEC-WA-06; transição operacional e privilégios de produção seguem NO-GO. Teste pesado GoTrue/PostgREST local gerenciado das migrations 028–032 **NÃO EXECUTADO**.

**Gates:** DEC-WA-01/02/03 direção aprovada; DEC-WA-05 titularidade Meta por concessionária aprovada, sem liberação de onboarding; DEC-WA-04/06 pendentes. PR #1 e #2 Draft, sem merge, sem migração no Supabase hospedado. **GO** só para engenharia/testes sintéticos; **NO-GO** para Meta real, Banco, OpenAI, API pública, canais comerciais e produção.


## S0/033 — aplicação C02 e conclusão da inbox no mesmo commit (18/10/2026 UTC)

**Evidência definitiva:** [GitHub Actions PostgreSQL 17 #39117446145 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39117446145), commit testado `ca706d3854ee4ef9f10884fdd765c8a85f13ba17` (primeiro CI do código `#39117349248` também SUCCESS; o segundo fortalece a asserção do teste de rollback). Logs verificados: `WA33-01..05 PASS`, `WA33-CONC-01 PASS`, `WA32-CONC-01 PASS`, regressões S0 anteriores e **24 testes Python — OK**; sem erros de execução.

**Arquivos implementados:** `supabase/migrations/202610180033_s0_inbox_aplicacao_c02_atomica.sql`, `supabase/tests/s0_wa_033_aplicacao_c02.sql`, `scripts/test_s0_wa_033_concurrency.sh` e runner `scripts/run-s0-local.sh`. Norma de escopo: `docs/S0_033_APLICACAO_INBOX_C02_2026_10_18.md`.

| Marcador | Resultado comprovado em PostgreSQL descartável |
|---|---|
| WA33-01 | Vínculo de fixture fictícia ao inbox, C02 e tarefa `APPLIED` em transação única; replay idêntico; equivalência 8↔9 e lojas distintas |
| WA33-02 | Falha *identificada exatamente* como `FIXTURE_ABORT_AFTER_C02` após o efeito C02 aborta também a mensagem, a tarefa e o histórico; reexecução válida aplica uma vez |
| WA33-03 | Lease vencido impossibilita aplicação e não cria mensagem |
| WA33-04 | Identidade ambígua não gera aplicação falsa, permite quarentena técnica explicitamente |
| WA33-05 | Checagens de loja/canal/provider message ID e revogação de EXECUTE/SELECT de papéis de API |
| WA33-CONC-01 | Duas sessões em paralelo competem por mesma tarefa; apenas uma mensagem, uma aplicação e um settlement persistidos |

**Limites:** somente `inbound_message` e prova **sintética** do C02; o conteúdo criado é fixture, não mensagem Meta durável/criptografada, o indicador móvel é de teste, e o vínculo App/WABA/loja deriva de registro fictício. `APPLIED_ATOMIC` comprova a transação PostgreSQL S0, não um ACK/commit do ingressor Meta real nem envio ou resultado bancário. C07 não foi conectado à fila; status callbacks não possuem identidade de evento única aprovada. Integração Auth/REST local gerenciado das migrations 028–033 **não executada**, assim como deploy Supabase hospedado, serviços externos e operações comerciais. Menor privilégio das wrappers `SECURITY DEFINER postgres` ainda pendente.

**Gates:** DEC-WA-01/02/03 aprovadas como diretriz; DEC-WA-05 titularidade Meta de cada concessionária aprovada, sem onboarding; DEC-WA-04/06 permanecem pendentes. PR #1 e PR #2 Draft e sem merge. **GO para engenharia sintética; NO-GO para API pública, Meta/Bank/Marca A/IA reais, canais comerciais, produção ou migração hospedada.**


## S0-034A — reparo dos achados A33-01/02/03 (18/10/2026 UTC)

**Evidência definitiva:** [GitHub Actions PostgreSQL 17 #39118986044 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39118986044), commit testado `cb167166574d353bb692c99acee471e0766ad8f6`. Logs do job `s0-db-isolation` verificados: `WA34-01..05 PASS`, `WA33-01..05 PASS` (com WA33-04 atualizado para preservar a pendência), `WA33-CONC-01 PASS`, demais testes/regressões S0 anteriores e **24 testes Python — OK**. Sem erros no CI final.

**Evidência inicial não aprovada:** [#39118911345 — FAILURE](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39118911345) teve `WA34-01 PASS`, porém no negativo WA34-02 o trigger de prova rejeitou associação cruzada **antes** da validação FK, e o teste esperava apenas `foreign_key_violation`. O teste foi corrigido para verificar separadamente a proteção do trigger e a FK composta, sem alterar a migração. **Falha histórica de teste resolvida** antes do CI definitivo; não a tratar como código ainda quebrado.

| Marcador | Resultado comprovado em PostgreSQL 17 descartável |
|---|---|
| WA34-01 | C02 vinculado não pode virar `APPLIED` sem prova via função genérica ou `UPDATE` direto; aplicação legítima preserva `APPLIED_ATOMIC` e replay |
| WA34-02 | Loja+canal+inbox/mensagem protegidos por FKs compostas; trigger adicional rejeita mensagem de mesmo canal com ID/texto incompatíveis |
| WA34-03 | `NEEDS_REVIEW` registra pendência, quarentena e motivo na mesma transação; sem mensagem ou prova `APPLIED`; reprocessamento cego recusado |
| WA34-04 | Colisão de duas identidades conserva o motivo `IDENTITY_CONFLICT`, distinto de resultado externo incerto |
| WA34-05 | Sem pendência com telefone/texto/escopo correspondentes não é possível forjar quarentena de identidade; permissões de API restritas |
| WA33-04 | Regressão adaptada ao resultado `QUARANTINED_IDENTITY` seguro em vez de rollback de pendência |

**Arquivos:** `supabase/migrations/202610180034_s0_integridade_c02_e_pendencias.sql`, `supabase/tests/s0_wa_034_integridade.sql`, regressão `supabase/tests/s0_wa_033_aplicacao_c02.sql`, `scripts/run-s0-local.sh`, `docs/S0_034A_REPAROS_INTEGRIDADE_2026_10_18.md`. As migrations históricas 001–033 foram preservadas.

**Limites:** `APPLIED_ATOMIC` é somente aplicação *fictícia* dentro da transação SQL C02, não equivale a `COMMITTED` de POST Meta real ou a confirmação bancária. A regra de prova cobre os eventos com `inbox_c02_fixture_s0`; rotinas sintéticas antigas que não têm essa fixture continuam independentes e não são prova de C02. `IDENTITY_CONFLICT` e `NEEDS_REVIEW` são causas técnicas de quarentena, não novos estados comerciais. Nenhuma credencial real, worker autêntico de menor privilégio, integração Meta/Graph/Banco, payload protegido real, ACK HTTP ou migração hospedada. Auth/REST integrado no Supabase local gerenciado para migrations 028–034 **NÃO EXECUTADO**. Os owners comerciais `SECURITY DEFINER postgres` continuam pendentes de redução de privilégio.

**Gates:** DEC-WA-01/02/03 diretrizes aprovadas; DEC-WA-05 titularidade por concessionária aprovada, sem liberação de implantação; DEC-WA-04/06 pendentes. PR #1 e PR #2 Draft sem merge. **GO** para engenharia sintética; **NO-GO** para webhook real, produção e Supabase hospedado.


## S0-034B — auditoria de contrato C07 / WA-01C (18/10/2026 UTC)

**Evidência PostgreSQL 17 descartável:** [GitHub Actions #39119612194 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39119612194), commit de implementação/teste `2ce6ccf0c47b0cb39c1c55165f35f1fe96712c6d`. Logs do job `s0-db-isolation` conferidos: `WA34B-CB-01..04 PASS`, regressões S0 já existentes, inclusive C07-01..05, C07-REC-01..05, WA33 e WA34, e **24 testes unitários Python — OK**. Nenhum erro nos logs do CI.

| Marcador | Evidência e limite |
|---|---|
| WA34B-CB-01 | Um ID de mensagem de saída contém vários status/ocorrências, incluindo duas com mesmo status e timestamp; preservadas **somente porque a fixture fornece IDs artificiais de evento distintos**; replay do mesmo ID local idempotente e evento atrasado identificado, sem alterar ciclo |
| WA34B-CB-02 | Prova negativa: `statuses[].id` **não** é ID exclusivo de ocorrência; se reutilizado em `evento_externo_ficticio`, status seguinte com conteúdo distinto gera `CONFLICT_IDEMPOTENCY_KEY` |
| WA34B-CB-03 | Status da loja A/canal A1 não é correlacionado por engano no canal A2 da mesma loja ou na loja B; vai a pendência técnica |
| WA34B-CB-04 | Prova negativa: `inbox` da migration 030 usa `status + timestamp + provider_message_id` como chave; mesmo conjunto com outra fixture causa conflito. **Não certifica dedupe Meta**, nem autorização para ACK, descarte ou conexão C07 |

**Artefatos:** `supabase/tests/s0_wa_034b_c07_contrato.sql`, `docs/S0_034B_AUDITORIA_CONTRATO_C07_WA01C_2026_10_18.md`; incluídos no runner `scripts/run-s0-local.sh`. **Nenhuma migration nova neste marco; funções C07 019–022, S0 028–034 e PR #2 preservados.**

**Contrato e gate:** WA-01C do PR #2 é apenas candidato `safe_to_auto_dedupe:false`. O C07 S0 exige `evento_externo_ficticio` único, enquanto a Meta não garante um ID por observação de status; `statuses[].id` é da mensagem enviada. Falta definição segura de ID interno de ocorrência, tratamento de reentrega, conservação do conteúdo protegido, HMAC por App e mapeamento com vigência App/WABA/emissor→canal antes de qualquer ligação C07. Status de Graph/Meta não altera estado comercial, reenvio automático em resultado incerto continua proibido, e `APPLIED` sintético da inbox não é `COMMITTED` do webhook.

DEC-WA-01/02/03 e titularidade DEC-WA-05 aprovadas como direção; DEC-WA-04/06 permanecem pendentes. **Auth/REST local gerenciado para migrations 028–034 ainda não executado**; Supabase hospedado não recebeu migrations comerciais. PR #1 e #2 Draft, sem merge. **GO** para engenharia de contrato com dados sintéticos; **NO-GO** para inbox→C07 real, Graph, canais comerciais e produção.


## S0-035 — Supabase GoTrue/PostgREST local gerenciado com migrations 028–034 (18/10/2026 UTC)

**Evidência real, CI independente do PG17:** [GitHub Actions Auth/REST local #39120161917 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39120161917). Commit de código/testes `fc1c7d2a7a76c9eb7c6dc35c38f4f19f07a3a655`; Supabase CLI 2.84.2 e psycopg 3.2.9 fixados, ambiente local gerenciado **sem link ao Supabase hospedado**, cleanup `supabase stop --no-backup` concluído. Nos logs foram conferidos `AUTH-01..14`, `AUTH-13-REVOKE`, `AUTH-15` e `AUTH-16` **PASS**, sem erro. Regrediu-se ainda no PostgreSQL 17 descartável em [#39120145381 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39120145381), para o mesmo commit.

**AUTH-15:** migrações S0 028–034 compatíveis com o inicializador Supabase local, tabelas privadas novas com RLS, SELECT/INSERT/UPDATE/DELETE e EXECUTE ausentes para `anon`, `authenticated`, `service_role`, `prumo_s0_gateway`, `prumo_s0_signer`; FKs loja+canal e triggers de prova C02 presentes e habilitados.

**AUTH-16:** tentativas via PostgREST público, anônimas e com JWT GoTrue válido de gestor, não expuseram `inbox_c02_fixture_s0`, `aplicacoes_c02_inbox_s0`, RPC `aplicar_inbox_c02_s0` ou `registrar_resultado_ingresso_s0`. Os testes 01–14 mantêm isolamento gestor/operador, revogação de vínculo/sessão, fronteira do backend e gateway de HMAC restrito.

**Execução consciente do workflow caro:** etiqueta `run-auth-integration` colocada deliberadamente no PR #1, removida após o sucesso; timeout de 12 minutos, cancelamento de execuções obsoletas e nenhum serviço pago. Registro detalhado em `docs/S0_035_COMPATIBILIDADE_AUTH_REST_2026_10_18.md`.

**Limites do aceite:** instalação/ACL/RLS/Data API **não** provam um futuro worker autenticado de menor privilégio que execute o processamento C02/C07 em Supabase; não há API pública privilegiada, serviço real, ACK Meta, segredo de produção, payload recuperável, HMAC Meta por App, teste Graph ou mensageria. Atribuições comerciais `SECURITY DEFINER postgres` seguem pendentes de redução de privilégios. O Supabase **hospedado** permanece intocado (zero tabelas comerciais `public`, zero migrations comerciais). DEC-WA-04/06 pendentes; DEC-WA-05 somente titularidade por concessionária. PR #1/#2 Draft e sem merge. **GO** para S0 sintético local; **NO-GO** para produção, contratação e implantação hospedada.


## S0-036 — proprietário restrito das entradas assinadas do gateway (18/10/2026 UTC)

**Código testado:** commit `77062a5047e57c212dff51bad844ae990b3cdcea`, migração `202610180036_s0_owner_gateway_assinado.sql`.

- **[PostgreSQL 17 #39120829358 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39120829358):** `OWNER-01..06`, `GW-01..07`, KEY, C01/C02/C07, inbox e demais regressões S0 PASS, 24 testes unitários Python OK. `OWNER-04` confere `prumo_s0_signed_executor` NOLOGIN/NOINHERIT e ownership das entradas assinadas; `OWNER-05` confere ausência de privilégios diretos sobre dados comerciais, `auth.sessions` e chaves HMAC, permitindo somente invocação delegada às funções exigidas; `OWNER-06` comprova que as wrappers comerciais legadas continuam com owner `postgres`, mas não podem ser invocadas pelo gateway sem a assinatura.
- **[Supabase GoTrue/PostgREST local gerenciado #39120910939 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39120910939):** `AUTH-01..17` PASS, incluindo `AUTH-13-REVOKE` e novo `AUTH-17` confirmando transferência de owner, ACL e RPC privadas; teardown do Supabase efêmero concluído, nenhum erro no log.

A label `run-auth-integration` foi aplicada deliberadamente uma vez e **removida após o sucesso** para reduzir custos. Documentação detalhada em `docs/S0_036_REDUCAO_OWNER_GATEWAY_2026_10_18.md`. Migrações históricas 001–034 foram mantidas sem reescrita; a ausência de migration S0/035 é intencional (S0-035 foi gate de teste, não alteração do banco).

**Aceite restrito:** a propriedade das duas entradas **assinadas** foi reduzida para `prumo_s0_signed_executor` NOLOGIN sem DML direto. Ainda há **privilégio efetivo `postgres SECURITY DEFINER` nas wrappers comerciais legadas** e verificação `current_user='postgres'` nas rotinas de domínio. Este marco **não** certifica privilégio mínimo ponta a ponta, não libera worker operacional, HTTP, Meta real, banco real, credenciais pagas, host remoto ou produção. Rotação/cofre de segredos, auditoria durável externa e DEC-WA-04/06 seguem pendentes; DEC-WA-05 define titularidade Meta por concessionária. PR #1 e #2 permanecem Draft, sem merge. **GO** para engenharia sintética, **NO-GO** para implantação comercial.


## S0-036A — auditoria corretiva de ACL após 035/036 (18/10/2026 UTC)

**Auditoria retroativa dos marcos 035 e 036:** as migrações 028–036 e a execução de OWNER/GW/AUTH mantêm as propriedades testadas no baseline, porém havia uma lacuna concreta na migration 026: `prumo_private.auditar_rotacao_gateway_s0()`, função auxiliar `RETURNS trigger`, não revogava `EXECUTE` padrão de `PUBLIC`. Embora esse tipo de função não seja executável diretamente como chamada comercial normal, o papel gateway possui `USAGE` no esquema e, antes do reparo, sua ACL excedia o contrato de apenas duas entradas assinadas. **Não houve evidência de abuso ou processamento comercial real.**

**Correção aditiva:** `202610180037_s0_036a_acl_audit_repair.sql` revoga `EXECUTE` do auxiliar para PUBLIC, anon, authenticated, service_role, gateway, signer e executor. A numeração de migration 037 é apenas ordem cronológica; o incremento é de auditoria **S0-036A**, sem iniciar a futura redução de privilégios comerciais. Sem mudança de dono, contrato, HMAC, nonce, canal ou dados comerciais.

**Evidência final do commit `af6a21926eb36dc33dc5150c4943f26f3a1e500d`:**
- [PostgreSQL 17 #39122872136 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122872136): **AUD-036A-01..04 PASS** (inventário de todas as funções privadas, gateway só duas entradas assinadas, signer/executor com dependências mínimas, todas SECURITY DEFINER com search_path vazio, trigger inacessível ao gateway), OWNER-01..06, GW-01..07, demais regressões S0 e 24 testes Python OK.
- [Supabase GoTrue/PostgREST local #39122948236 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122948236): **AUTH-01..18 PASS**, incluindo novo AUTH-18 de inventário de permissões e search_path no Supabase gerenciado. Ambiente efêmero sem vínculo com host remoto e teardown concluído. Etiqueta de gatilho cara removida.
- **Histórico transparente:** [#39122774143 — FAILURE](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122774143) por comparação incompleta do campo `search_path` no teste AUD-036A-03 (o catálogo serializa string vazia em formas equivalentes). Corrigimos **apenas o teste**; os demais AUD-036A-01/02 já passaram nessa rodada e a execução definitiva passou integralmente. CI intermediário #39122866007 cancelado por commit mais recente.

Artefatos: `docs/S0_036A_AUDITORIA_ACL_2026_10_18.md`, `supabase/tests/s0_036a_auditoria_acl_completa.sql`, `scripts/test_s0_auth_rest_local.py`, `scripts/run-s0-local.sh`. O reparo não torna as wrappers comerciais `SECURITY DEFINER postgres` privilégio mínimo ponta a ponta. Não certifica worker operacional, segredo real, Meta/Graph, instituição financeira, C07 real, retenção/restore, ACK HTTP ou produção. DEC-WA-04/06 e contrato WA-01C continuam pendentes; DEC-WA-05 mantém propriedade Meta por concessionária. PRs permanecem Draft sem merge; nenhuma migration no Supabase hospedado. **GO** para engenharia sintética posterior à auditoria; **NO-GO** para produção ou infraestrutura real.


## S0-037A — gate negativo de transferência do owner comercial (18/10/2026 UTC)

**Sem migration nova, sem mudança de owner, sem DML comercial persistente.** A migration `202610180037_s0_036a_acl_audit_repair.sql` segue exclusiva ao reparo anterior S0-036A; este marco S0-037A apenas amplia a validação executável de dependências das wrappers legadas `SECURITY DEFINER postgres` em `supabase/tests/s0_037a_gate_owner_comercial.sql`, incluído em `scripts/run-s0-local.sh`.

**Evidência de execução:** [GitHub Actions PG17 #39123912355 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39123912355), commit de código `5e99ba5761d54cfdf4d7ab77cabf2977e1d2724f`. Logs conferidos: **OWNER37-01..05 PASS**, AUD-036A-01..04 PASS, regressões anteriores S0 incluindo GW, OWNER, C01/C02/C07, concorrência e **24 testes Python OK**.
- OWNER37-01: proprietário `postgres` e `SECURITY DEFINER` nas duas wrappers legadas, e guard `current_user='postgres'` nas funções comerciais `SECURITY INVOKER`.
- OWNER37-02: executor assinado não recebe DML comercial nem acesso à sessão e mantém apenas delegação às wrappers legadas.
- OWNER37-03: papel temporário `NOLOGIN NOBYPASSRLS` com EXECUTE explicitamente concedido às funções invoker recebe **`INTERNAL_ONLY`**, logo ALTER OWNER isolado não é mudança segura.
- OWNER37-04: papel temporário com SELECT de `leads_loja` não enxerga linha fictícia existente sem uma política RLS apropriada; não é prova de autorização operacional completa.
- OWNER37-05: não há mudança no owner do domínio, contas ou associação de privilégios; objetos de teste são revertidos por ROLLBACK.

**Interpretação:** o requisito de reduzir privilégios efetivos das wrappers comerciais segue pendente; trocar diretamente o proprietário hoje quebraria a aplicação. Precisamos projetar a autorização, RLS específica e privilégios transacionais, mantendo HMAC, nonce, sessão GoTrue, gestor, loja, versão, auditoria, isolamento e sem novos meios de execução pública. **Não usar BYPASSRLS, privilégios amplos nem novos helpers `SECURITY DEFINER postgres` como atalho.**

**Supabase Auth/REST local gerenciado:** não repetido neste marco que não altera migrations/runtime; última evidência homologada para baseline S0-036A é [#39122948236 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122948236). Registros de análise em `docs/S0_037A_GATE_OWNER_COMERCIAL_2026_10_18.md`. DEC-WA-04/06, política de observações C07 e demais gates operacionais ainda pendentes. PRs Draft, sem merge, sem envio real, Supabase hospedado ou produção. **GO somente para projeto/testes sintéticos de privilégio mínimo; NO-GO para transferir as wrappers hoje.**


## S0-037B — matriz de privilégios mínimos C08/C07 em teste sintético (18/10/2026 UTC)

**Evidência:** [GitHub Actions PostgreSQL 17 #39126117200 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39126117200), commit testado `bd6772ce82a86ec8591cbb161d83e5f14f09bfdf`. Logs consultados: **OWNER37B-01..05 PASS**, regressões SQL anteriores, concorrência e **24 testes Python OK**, sem erro. O ensaio executa `supabase/tests/s0_037b_matriz_rls_escrita.sql` via `scripts/run-s0-local.sh`; registro em `docs/S0_037B_MATRIZ_PRIVILEGIOS_2026_10_18.md`.

- OWNER37B-01: duas concessionárias fictícias independentes, mesmo número cliente em leads separados; C07 com duas pendências isoladas; `auth.sessions` e a auditoria privada não são concedidos ao novo papel.
- OWNER37B-02: role efêmera `NOLOGIN/NOBYPASSRLS` recebe **só no ensaio** SELECT, UPDATE em colunas C08, INSERT de evento e RLS artificial atrelada ao UUID da loja A; atualizações com `versao=1`, evento fictício e negativas para B confirmados.
- OWNER37B-03: mesmo experimento com pendência C07 de A, decisão sintética `ENCERRAR_SEM_PROVA`, UPDATE versionado e inserção de auditoria; B não alterada. **`VINCULAR_SINTETICAMENTE` permanece sem ensaio nesse papel**.
- OWNER37B-04: bloqueio ao SQL de auditoria privada e às funções de domínio; tabela da loja B invisível.
- OWNER37B-05: roles reais `prumo_s0_gateway`, `prumo_s0_signed_executor` sem DML comercial direto adicional; toda política/grant/role/fixture experimentais removidos por `ROLLBACK`.

**Conclusão:** apenas a viabilidade de DML SQL escopado sob políticas literais de laboratório foi demonstrada. **Não** existe ainda credencial confiável de sessão/ator vinculado ao escopo do papel técnico; o SQL direto de teste **não verifica HMAC nem nonce**. Portanto **NÃO** promover grants/policies temporários à migration, usuário autenticado ou worker, nem transferir o owner das wrappers `SECURITY DEFINER postgres`. `auth.sessions` e `prumo_private.auditoria_gateway_s0` continuam bloqueios relevantes, assim como locks `FOR UPDATE`, concorrência, auditoria integrada e as duas decisões C07 completas. Sem deploy, merge ou escrita no Supabase hospedado. Auth/REST local não repetido porque o incremento só adicionou testes/documentação; última baseline [#39122948236 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122948236). **GO para design/ensaio sintético; NO-GO para redução comercial ou operação real.**


## S0-037C — regressão assinada C08 e C07 completo (18/10/2026 UTC)

**Evidência:** [GitHub Actions PostgreSQL 17 #39127146330 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39127146330), commit de código `219240503ea966e7a392aef6d2342872bb6929bb`; logs conferidos: **OWNER37C-01..05 PASS**, regressões SQL/concor­rência S0 e **24 testes Python OK**. Artefatos: `supabase/tests/s0_037c_execucao_assinada_c07_c08.sql`, runner `scripts/run-s0-local.sh`, `docs/S0_037C_EXECUCAO_ASSINADA_COMERCIAL_2026_10_18.md` e **`docs/MAPA_MENTAL.md` atualizado**.

- OWNER37C-01: gateway sem acesso SQL direto a sessão/dados/auditoria; HMAC falso recebe `PROVA_INVALIDA`.
- OWNER37C-02: cancelamento C08 assinado de plano/envio fictício com nonce irrepetível e replay de novo nonce `ALREADY_APPLIED`.
- OWNER37C-03: C07 `ENCERRAR_SEM_PROVA` e `VINCULAR_SINTETICAMENTE` assinados em A; tentativa de A sobre B negada por `FORBIDDEN_SCOPE`.
- OWNER37C-04: quatro provas consumidas e quatro registros de gateway consistentes com as transições; loja B intacta; oito estados comerciais preservados.
- OWNER37C-05: remoção da sessão de teste no banco bloqueia assinatura válida com `SESSAO_INATIVA`, sem persistir nonce/auditoria adicionais.

**Falhas intermediárias do teste resolvidas antes do aceite:** [#39126937486](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39126937486) (GUC malformada), [#39127006581](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39127006581) (JOIN com `id` ambíguo), [#39127073850](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39127073850) (checagem de `auth.sessions` sem acesso ao esquema). Somente fixture/teste corrigida; nenhuma migration, permissão permanente ou regra comercial alterada.

**Não é homologação de privilégio mínimo ponta a ponta.** As wrappers legadas seguem `SECURITY DEFINER postgres`, dependem de `current_user='postgres'`; a role temporária de RLS da S0-037B não foi promovida. Última compatibilidade Auth/REST local [#39122948236 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122948236). DEC-WA-04/06 e C07 Meta real pendentes; PRs Draft, sem merge, sem migração hospedada nem tráfego real.


## Auditoria S0-037A/B/C — regressões adversariais (18/10/2026)

**Evidência final:** [CI PostgreSQL 17 #39128133133 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39128133133), commit de código/teste `2c2d81311b1bd275fb4364cd4fa422d1efb9e659`. Logs: **AUD37-01..03 PASS**, OWNER37C-01..05 PASS, regressões anteriores e 24 testes Python OK.

**AUD37-01:** ator A com sessão B recebe `SESSAO_INATIVA`; gestor B atuando na loja A, mesmo com assinatura sintética válida, recebe `FORBIDDEN_SCOPE`.

**AUD37-02:** replay da mesma decisão C07 com ator, justificativa e envio iguais, novo nonce, resulta `ALREADY_APPLIED`; decisão C07 divergente na versão encerrada resulta `CONFLICT_VERSION`.

**AUD37-03:** a contabilidade inclui cinco nonces e cinco entradas de auditoria do gateway para operações aceitas, sem duplicar vínculo ou auditoria comercial C07; nenhuma tentativa negada consome nonce persistente no ensaio. O último teste OWNER37C-05 passou com os contadores esperados atualizados.

**Parecer:** duas lacunas de cobertura corrigidas **somente na fixture de teste**, sem alterar migrações, owners, roles reais, RLS permanente ou operações comerciais. `docs/S0_037ABC_AUDITORIA_RETROATIVA_2026_10_18.md` documenta a revisão; `docs/MAPA_MENTAL.md` atualizado. A S0-037B segue prova de DML fictício sob RLS transitória, e S0-037C prova a cadeia assinada **ainda com wrappers comerciais SECURITY DEFINER postgres**. Nenhum owner comercial de privilégio mínimo foi homologado. Último teste Auth/REST local da baseline: [#39122948236](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122948236), não repetido nesta alteração restrita a testes. PRs Draft, sem merge, sem migrations Supabase hospedadas, Meta real ou deploy. **GO para evolução sintética; NO-GO para produção.**


## S0-037D — capacidade transacional por ação/loja/alvo/versão/txid (18/10/2026)

**Evidência do commit executável `f785e4e51bbec419f7fad5997510695d802e460a`:** [GitHub Actions PostgreSQL 17 #39130042204 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39130042204). `OWNER37D-01..04 PASS`, regressões S0 e **24 testes Python OK**. Registros em `supabase/tests/s0_037d_capacidade_transacional.sql`, runner `scripts/run-s0-local.sh`, `docs/S0_037D_CAPACIDADE_TRANSACIONAL_2026_10_18.md` e **`docs/MAPA_MENTAL.md` atualizado**.

- OWNER37D-01: GUC falsificada `prumo.user_loja`/`prumo.user_acao` não concede acesso à loja B; role `NOLOGIN/NOBYPASSRLS` não pode inserir capacidade no ledger protegido da fixture.
- OWNER37D-02: autorização emitida **pelo postgres da fixture** para `C08_CANCELAR`, loja A, alvo e versão esperada, amarrada à transação, permite somente UPDATE sintético escopado; não abre loja B nem repete versão antiga.
- OWNER37D-03: pendências sintéticas C07 de A têm autorização distinta para `ENCERRAR_SEM_PROVA` e `VINCULAR_SINTETICAMENTE`; ação incorreta rejeitada pelo predicado RLS e B isolada. **Não** executa o algoritmo comercial nem grava associação/auditoria completa.
- OWNER37D-04: papel real `prumo_s0_gateway` e executor assinado mantêm os privilégios originais, sem DML direto. Role/grants/policies/capacidades e dados da prova são revertidos via `ROLLBACK`.

**Falha de teste resolvida:** [#39129933121 — FAILURE](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39129933121) mostrou falta do revisor obrigatório da pendência C07 na fixture; o teste foi corrigido sem modificar migration/função/comportamento comercial, e o CI final passou.

**Limite de segurança:** tabela TEMP emitida por `postgres` em laboratório **não é emissor seguro operacional** nem prova de HMAC/sessão GoTrue. O chamador com DML autorizado dentro da mesma transação ainda pode executar os comandos permitidos; a solução final necessita vincular emissão, verificação e consumo atômicos a HMAC, nonce, sessão, gestor, loja, versão, auditoria, locks e revogação. **Não transferir owners comerciais nem promover grants/policies descartáveis**. A S0-037C continua validando em paralelo a cadeia HMAC existente sob wrappers `SECURITY DEFINER postgres`. Auth/REST local não repetido pois não houve runtime/migration nova; última baseline [#39122948236 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122948236). PRs Draft, sem merge; sem hosted Supabase, operação Meta, token real ou produção.
