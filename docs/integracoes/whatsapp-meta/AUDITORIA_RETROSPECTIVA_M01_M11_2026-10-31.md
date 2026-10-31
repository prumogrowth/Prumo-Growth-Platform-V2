# Auditoria retrospectiva da frente WhatsApp/Meta — M01 a M11

**Data:** 31/10/2026. **Solicitação:** vistoriar M11 e as etapas anteriores não formalmente auditadas antes de começar M12.

**Classificação após correções:** **CONFORME PARA PROSSEGUIR SOMENTE NO DESENVOLVIMENTO OFFLINE, COM RESSALVAS E DEPENDÊNCIAS BLOQUEANTES**. Os três defeitos concretos encontrados na frente Meta foram corrigidos e verificados em CI. **NÃO** significa integração real homologada, segurança formalmente comprovada, merge, endpoint, produção ou autorização de HTTP POST ACK/Graph.

**Fonte auditada:** branch `feat/meta-s0-physical-interop-ack-guard-20261031`; commit funcional pós-correção `60f789df841485e8cce41525f4517f00c6975e91`. CI [41222509935](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41222509935): **1.344/1.344** testes Meta offline, nenhum skip/falha; 36/36 Ed25519 e 369/369 regressões focadas são subconjuntos, **não somar**; scanner lexical ACK aprovou 311 arquivos rastreados; segundo job **18 verificações físicas PG17↔Meta**, ambos `success`. Fonte S0 congelada, read-only: `01ffdb093013664b73b18d23f92aac2202578210`.

## 1. Método e limite de alcance

1. Consultadas todas as Issues abertas da fila compartilhada (protocolo [#4](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/4)), últimas respostas de [#2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2), [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8), [#9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9) e [#10](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/10). **Novo contrato candidato S0 M09-01** recebido durante a auditoria (ver seção 4).
2. Revisados módulos de roteamento/segredos, GET, POST HMAC, escopo de lote, auditoria HTTP/ACK, Ed25519 e as implementações M09/M10/M11 e respectivos testes. Conferidas evidências de M01–M06 no checklist, artefatos/código representativos e CI histórico por SHA; **não se reivindica uma nova auditoria linha a linha de todos os módulos M01–M06**.
3. Para M07/M08, reutilizada e validada a [auditoria específica anterior](AUDITORIA_M07_M08_2026-10-31.md) e o CI pós-correção; não reaberto ACK.
4. Adicionados **13 testes adversariais inéditos**, aplicadas 3 correções de segurança exclusivamente na árvore `integrations/whatsapp-meta/`. Comparação GitHub da base `4260b3accf4930026f7f74e902f5962472d89057` ao SHA testado `60f789df841485e8cce41525f4517f00c6975e91` revelou **7 commits**, somente **7 arquivos de código/teste Meta** alterados; nenhuma alteração S0/S1/Infra/Frontend.
5. Executada pelo GitHub Actions a suíte integral com testes de laboratório e consumidor S0 PG17 físico descartável. Não houve testes de rede de webhook real, autenticação M2M hospedada, deploy, smoke test de Graph, PR trigger efetivo ou teste do binário de produção.

## 2. Parecer por etapa

| Marco | Vistoria deste ciclo | Parecer e limite |
|---|---|---|
| **M01** | Revisão documental/evidências WDC e precedência vigentes | Conformidade documental de referência, não prova de implantação. Sem nova alteração. |
| **M02** | Regressões integrais de HMAC/GET/POST e leitura dos guards de entrada/roteamento | Conforme **offline** após correção de alias de segredo (AUD-01). Sem webhook externo. |
| **M03** | Suíte offline de saída da Meta e revisão do isolamento GET/POST/Graph | Conforme ao escopo anterior **offline**; Graph real permanece proibido. |
| **M04** | 36 provas de recibo Ed25519 sintético e revisão da fonte de trust pin | Conforme **laboratório**; nenhuma âncora/custódia de chave real. |
| **M05** | CI histórico [41187216781](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41187216781) verificado no SHA `a91b0dac2c332ef5ebbe07fb7884ed5137d60484`; suíte atual 1.344/1.344 | Rastreabilidade SHA/CI conforme. Ainda não houve prova efetiva de execução como PR. |
| **M06** | CI histórico [41188097646](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41188097646) verificado no SHA `b1828b1db7ad653608606916209a1f25ad57e7fe`, S0 PG17 fixada; 18 provas atuais | Interoperabilidade física **laboratorial**, sem durabilidade/serviço externo ratificados. |
| **M07/M08** | Auditoria específica [M07/M08](AUDITORIA_M07_M08_2026-10-31.md) e [CI histórico 41194019498](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41194019498), SHA `dd27a01d6a44bd8496d52d9cc2455c8b5752f886`, rechecados; scanner atual aprovado | M07-A/B/C e M08-A/B/C mantidos, **D e pais [ ]**. Nenhum POST ACK real. |
| **M09** | Revisão de inventário, `credential-routing.ts`, 5 novos testes específicos e teste de alias de segredo | **Dois defeitos corrigidos** (AUD-01/02), 43 testes próprios + guard de roteamento; M09-D segue **[ ]**. |
| **M10** | Revisão do pin Ed25519, contexto de serviço, 3 novos testes adversariais | **Um defeito corrigido** (AUD-03); 42 testes próprios, M10-D **[ ]**, principal não autenticado. |
| **M11** | Revisão do envelope GET/POST, roteamento e parser, 4 negativos adicionais de revogação em curso, getter e slot | **48 testes próprios**; nenhum defeito residual demonstrado pela matriz executada; M11-D **[ ]** (HTTP/ACK e endpoint reais bloqueados). |

As contagens por módulo são subconjuntos dos **1.344 testes totais**. A revisão retrospectiva M01–M06 verificou evidência e regressões, mas **não substitui auditoria completa de cada módulo, de deployment ou de superfície externa**.

## 3. Achados concretos e correções

| ID | Gravidade do risco em eventual reutilização | Falha identificada | Correção auditada |
|---|---|---|---|
| **AUD-01** | **Alta** em integração futura de secrets | A validação de slots em `credential-routing.ts` detectava repetição entre Apps mas não **entre os três propósitos da mesma App**: GET verify token, POST App Secret e token Graph poderiam referenciar o mesmo slot. Invariante de isolamento por finalidade não estava garantida pelo registry. | Exigir `new Set(names).size === names.length` antes de aceitar. [Regressão `AUD-CRED-01`](../../../integrations/whatsapp-meta/credential-routing.test.ts) valida todas as combinações e guardas cruzados M09/M11. |
| **AUD-02** | **Média** para robustez de entrada não confiável | `wa09-asset-onboarding-audit.ts` percorria arrays de manifestos sem verificar previamente que todos os elementos eram **dados próprios, densos, sem getters**. Um getter poderia executar e variar durante um snapshot apesar de o verificador afirmar recusar accessors. | Novo snapshot estrito `dense()` para apps, WABAs, números e bindings S0, recusando arrays esparsos e accessors **antes de leitura dos elementos**. Regressões `AUD-M09-01..05`, incluindo alias. |
| **AUD-03** | **Média** para robustez de trust fixture | `wa10-service-trust-pin-audit.ts` validava os registros por descritores, mas iterava arrays externos de pins/principais sem validar previamente seus elementos; getters/listas esparsas escapavam dessa exigência. | `dense()` para listas de pins e principais antes da seleção. Regressões `AUD-M10-01..03` validam recusa sem invocar getters e sparse. |
| **AUD-04** | **Risco de integração, não defeito corrigível neste branch** | Contrato S0 M09-01 candidato requer revisões independentes (rota/App/binding/grant/principal), `slot_ref` apenas por finalidade, mapeamento explícito `tenant ↔ concessionaria_id` e recheck autoritativo. `TrustedMetaRegistry` e `wa09` usam **uma revisão de App** e três nomes de slots juntos, próprios de fixture. | **Não criar adaptador falso nem marcar integração pronta**. Solicitar ratificação e mapeamento versionado em [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8). |
| **AUD-05** | **Risco operacional bloqueante** | M11 é apenas uma função pura; a aceitação de HMAC **não prova** persistência S0, M2M, resposta ACK, política de proxy ou entrega. GET challenge separado de POST ACK. | Adicionados `AUD-M11-01..04` (revogação entre leituras, getter e alias). M11-D permanece pendente na [#2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) e [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8). |

**Confiança do scanner:** o guard de HTTP 200 é **lexical** e heurístico; prova somente a ausência de padrões específicos nos fontes rastreados, não a ausência formal de caminhos de execução, aliases computados ou comportamento de código compilado.

## 4. Revisão do novo contrato candidato M09 S0/S1

**Fonte S0:** `coord/s0s1-m09-contract-20261031`, SHA **`af3c7a16f777eb0d9b37e96f5ac496f1afc03913`**, [M09 contrato 0.1](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/af3c7a16f777eb0d9b37e96f5ac496f1afc03913/docs/contratos/s0s1_meta_registry/M09_CONTRATO_CANDIDATO_0_1_E_MISSAO.md), recebido na [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8). Proposta documentada, **sem CI próprio novo, endpoint S0 ou aceite Meta**.

**Alinhamentos:** fonte S0 autoritativa por loja/canal; rota de entrada não derivada de payload; não expor segredos; separar finalidade GET/POST/Graph; revogação invalidando snapshot; PRE_DISPATCH separado de planejamento F02 e de ACK.

**Ajustes/requisitos antes de contrato ratificado:**
- Definir esquema de leitura/correspondência explícita `tenant` PG17 ↔ `concessionaria_id` S0 e proveniência/titularidade, sem confiar em comparação de fixtures.
- Preservar **revisões separadas** de rota, App, vínculo, grant e principal M2M no adaptador; não colapsar em `expected_revision` de `credential-routing.ts` como se fosse versão global confiável.
- Para cada finalidade GET/POST/Graph, um único `slot_ref` escopado; evitar fornecer a consumidores ordinários o catálogo conjunto das três slots, como faz a fixture Meta.
- Definir recheck sob fonte S0 no **instante de uso**, CAS/revogação/conflito e sem tratar snapshot como ticket de envio ou ACK; negar fonte indisponível, principal não autenticado, slot ausente e revisão stale.
- Escolher porta adaptadora após ratificação, sem reescrever S0/OPS03 nem construir uma nova S0 paralela. A Meta poderá então escrever **consumidor laboratorial isolado** com testes de compatibilidade.

**Resultado da revisão:** direção compatível **conceitualmente**; **esquema físico não consumível diretamente**. Aceite M09-D, M10-D e M11-D continua pendente.

## 5. Segurança, CI e governança — pendências que a auditoria NÃO apaga

- [ ] Autenticação **real** do serviço M2M, chaves Ed25519 independentes e custodiadas, HMAC/vault e rotação/revogação real (S0/Infra, [#2](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/2) e [#8](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/8)).
- [ ] Endpoint HTTP hospedado, cadeia proxy raw-body confiável, rate limits, política de status/redelivery/retry, HMAC Meta real, transação única + readback S0 e E2E autorizado. O envelope M11 pode recusar headers aceitos em ambientes distintos porque seu perfil é **restrito de laboratório**; não adaptá-lo silenciosamente sem validação S0/Infra.
- [ ] Validação do **gatilho PR real** e regras de branch/required checks, análise de artefato compilado e comportamento em implantação, conforme auditoria M07/M08.
- [ ] Revisão independente de segurança/políticas de permissões e LGPD com dados reais sob autorização, testes HA/failover/recuperação e homologação humana antes de merge/deploy/produção.
- [ ] [#9](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/9) WA-39 ainda requer schema consumível F02, revisão S0 e evidências reais; este ciclo não implementa outbound.
- [ ] Os marcos pais **M07, M08, M09, M10 e M11** permanecem `[ ]`. M01–M06 permanecem `[x]` **somente para os escopos históricos explicitamente provados**, sem elevá-los a marcos de integração externa.

## 6. Decisão e critério de próximo ciclo

**PASS para seguir apenas em M12 offline**, com os bloqueios acima preservados. Não migrar a registry antiga para nova estrutura S0 sem contrato ratificado; não alterar S0/S1/Infra por conta própria; não presumir autorização de POST ACK, Graph real, decisões comerciais, deploy ou merge.

As correções deste ciclo mudam somente sete arquivos de código/testes Meta. Toda evidência deve referenciar o SHA funcional testado e não converter um documento ou um comentário em aprovação produtiva.
