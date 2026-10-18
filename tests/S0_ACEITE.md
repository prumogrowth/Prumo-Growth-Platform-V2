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
