# S0 + S1-002 / I53 — intake canônico pelo gateway GoTrue assinado

**Corte:** 23/10/2026. **Responsabilidade:** a mesma implementação detém S0 e S1; não há handoff fictício. **Ambiente:** Supabase CLI/GoTrue/PostgREST e PostgreSQL em CI descartável, não hospedado. Sem merge/deploy nem operações Meta/Banco.

## Problema específico resolvido

I52 integrou o estado de pausa versionado à **tabela canônica S0** `public.atribuicoes_humanas` com trigger fail-closed. Porém a entrada HTTP autenticada I37 ainda encaminhava ao modelo antigo `s1_definir_disponibilidade_leads_10`, cujo estado não controlava o trigger canônico. A migration I52 também desabilita os comandos antigos de pausa **da conta**. Como o antigo teste de 132+16 casos I18–I37 ainda dependia de movimentos globais simulados, a importação antecipada da migration I52 fazia o teste legado falhar. Isso não significa reabilitar a suspensão indevida de contas.

I53 corrige o **alvo real** do comando assinado e a **sequência de migração testada**: roda os testes anteriores contra o contrato histórico, aplica `202610190053_s0_s1_intake_atribuicao_guard.sql` **depois dos testes históricos**, instala nova ponte assinada e então valida diretamente a integração canônica.

## Arquitetura e ameaças

- **HTTP**: allowlist de único comando `POST /s1/intake`, JSON exato `{operador_id, pausar, versao_esperada}`; sem parâmetro de gestor, motivo em texto livre ou escolha de papel SQL pelo cliente. HTTPS, limitação distribuída e deployment final não fazem parte do servidor de loopback.
- **Identidade**: GoTrue valida Bearer; assinador independente verifica identidade e o gateway produz prova HMAC com `actor_id` + `session_id` não fornecidos pelo JSON de solicitação. O PostgreSQL relê a sessão em `auth.sessions` na ponte com `FOR KEY SHARE`; G1 só pode pausar pessoal de sua equipe.
- **Domain separation I53**: a assinatura de operação **`INTAKE53`** não é igual à assinatura legada **`INTAKE`**, mesmo com os mesmos ator, sessão, versão, nonce e chave. Uma prova de I37 não pode autorizar a nova função I53. A função `invocar_intake_v53` do executor NOLOGIN verifica HMAC no custodiante I22, nonce único e expiração de cinco/trinta segundos, só então chama ponte postgres com sessão viva.
- **Destinatário real**: `prumo_private.s1_definir_intake` do **I52** opera CAS no estado canônico `prumo_private.s1_intake_estado` protegido por lock. O trigger S0 usa o mesmo lock em cada nova atribuição, sem derrubar acesso aos casos antigos.
- **Privilégios**: login SQL efêmero dispõe de EXECUTE exclusivamente na fachada assinada; segredo de chave, histórico de intake, função de negócio interna e nonce permanecem sem grant público/authenticated. Ambos modelos de servidor e credenciais são deliberadamente locais e sintéticos.

## Arquivos I53

- `supabase/tests/s1_077_intake_assinado_canonico_local_only.sql` — teste de arquitetura do comando firmado, derivado de I37 com novo nome e prova de domínio, owner NOLOGIN, ponte segregada, chamadas à migration canônica.
- `backend/s1_gateway_intake_canonical_local.py` — adaptador estrito I53, subclass do verificador HTTP/GoTrue I37, SQL fixo e assinatura de ação `INTAKE53`.
- `backend/s1_gateway_intake_signed_local.py` — única refatoração de compatibilidade: enunciado SQL privado `_statement` constante na classe, permitindo rota histórica I37 sem alteração e rota nova I53 por subclass.
- `tests/test_s1_002_i53_canonical_gateway.py` — testes unitários de formato e separação HMAC.
- `scripts/test_s1_002_i53_signed_canonical_e2e.py` — 8 cenários reais de autenticação e integração canônica; usa a mesma stack GoTrue/certificado da I37, em seguida ao teste 146, antes de desativar a chave de sessão que protege os testes 147–148.
- `scripts/test_s1_002_i37_intake_e2e_local.py` — adia carregamento da migration 053 até a transição I53, sem modificar o comportamento histórico para esconder falhas.
- `.github/workflows/s1-002-i37-intake-signed-local.yml` — novos gatilhos, compilação e testes unitários.

## Critérios de aceite E2E local

| Caso | Prova |
| --- | --- |
| I53-149 | S0/S1/053 real instalado depois de cenários legados; ponte privada HMAC de domínio distinto |
| I53-150 | Gestor real GoTrue pausa só intake, sem suspender conta nem retirar caso anterior |
| I53-151 | replay funcional idempotente e versão obsoleta responde HTTP 409 |
| I53-152 | Gestor de outra equipe / campo HTTP não autorizado recebem negação |
| I53-153 | INSERT canônico S0 e transferência manual S1 negam novo destinatário pausado |
| I53-154 | HMAC legada não serve na rota I53; nonce consumido não pode executar duas vezes |
| I53-155 | retomada assinada libera atribuição nova na S0, com histórico de versões |
| I53-156 | função interna e comandos de suspensão legados não são RPCs expostas |

## Pendências de produto posteriores

A execução ainda é deliberadamente **local**. S0/S1 são responsabilidade conjunta desta implementação e os próximos pontos exigem código próprio, não outra frente: adicionar esse gateway assinado a uma infraestrutura de implantação segura, ligar a fila real/primeiro contato ao novo intake, eliminar caminhos que ainda dependam da antiga operação de suspensão global, consolidar serviço e UI, e reexecutar integrações de ponta a ponta. A2 permanece [D] fechada. Não usar snapshots do sandbox como evidência de consentimento Meta.

## Evidências

**CI concluído e logs inspecionados — 23/10/2026:**

- **GoTrue/PostgREST/HMAC/custódia mTLS:** [GitHub Actions #40027119209](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40027119209), job `120665985957`, **SUCCESS** no commit de código `dc0a77dc7c0902767431ef0f950e27c1b4bb8737`. Logs verificados: `PASS S1CANON-149..156` (**8/8**) e `PASS S1INTAKE-147..148` na nova rota canônica (chave revogada = negação; assinador indisponível = HTTP 503). Os testes unitários do mesmo workflow passaram.
- **PG17 S0/S1 com cutover atômico:** [GitHub Actions #40026784395](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/40026784395), **SUCCESS** no commit `55375661a2bb652c56baa46721300f867ec0eebc`, incluindo os demais testes do comando S0 canônico.
- **Regressões históricas:** o runner de I12 deixou de incluir a migration 053 antes de tempo; agora `scripts/run-s1-002-i52-local.sh` a aplica após os testes legados. A verificação GitHub Actions dos gateways históricos I18–I31 terminou verde no commit `5537566`. Isso **não** reabilita suspensão global no contrato vigente.
- **Correções auditáveis:** E2E I53 anterior obteve 8/8, mas falhou ao invocar v37 depois da desativação intencional. O commit `dc0a77d` moveu as provas de revogação/offline para a rota canônica v53 e retirou a asserção obsoleta. Não houve flexibilização de ACL ou de validação HMAC.
- **Limites**: ambiente totalmente efêmero, sem merge, deploy, credenciais/usuários reais, Meta ou operações bancárias. O gateway é exercício integrado de implementação S0/S1, não homologação para exposição pública.

**Próximo trabalho de código:** ligar fila real e distribuição S0 ao estado canônico de intake e definir comando de assunção idempotente com mesma identidade verificada, CAS/locks e auditoria; preservar o escopo de equipe/loja e histórico de casos.
