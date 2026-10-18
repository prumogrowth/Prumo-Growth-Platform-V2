# Prumo — mapa mental simples

```mermaid
flowchart TD
  P[Prumo] --> E[Entrada por concessionária]
  E --> IMP[Lotes por loja]
  E --> INB[Mensagens C02 por canal exclusivo]
  INB --> L
  INB --> PEND[Multiplos ciclos: revisao humana]
  IMP --> L[Cliente por loja → lead/ciclo: 8 estados]
  L --> EV[Eventos de status]
  L --> IA[IA Vendedora]
  IA --> H[Atendimento humano]
  H --> CAD[Cadastro versionado]
  CAD --> BAN[Remessa humana ao Banco]
  BAN --> RES[Resultado com prova]
  L --> REC[Recontatos]
  REC --> PLA[Planejadora: templates aprovados]
  REC --> ELIG[C04: elegibilidade e opt-out por loja/canal]
  ELIG --> CAN
  REC --> CAN[Resposta ou gestor: cancelar pendentes]
  INB --> CAN
  P --> C07[C07 simulado: callbacks tecnicos, sem reenvio]
  C07 --> RC[Sem correlacao: reconciliacao pendente]
  C07 --> RISK[Falha ou incerteza: sem retry automatico]
  RC --> GEST[Revisao do gestor: versao e justificativa]
  RISK --> GEST
  P --> AUTH[Backend S0: GoTrue verificado + sessao ativa]
  AUTH --> OP[Comandos sintéticos restritos: gestor/versao/loja]
  AUTH --> GWAY[Papel NOLOGIN, wrappers C07/C08]
  GWAY --> AUD[Auditoria de comandos aplicados sem dados sensiveis]
  GWAY --> ROT[Chaves HMAC: ativar, revogar e historico de versao]
  GWAY --> NONCE[Nonce unico, limpeza conservadora]
  AUTH --> NEG[Negativas sanitizadas sem token ou PII]
  OP --> GEST
  P --> ADM[Gestão e MCP com confirmação]
  P --> DB[Supabase: dados, RLS e auditoria]
  P --> INT[Integrações futuras]
  INT --> WA[Meta WhatsApp via Supabase direto]
  WA --> WABIND["App/WABA/número exclusivos por loja [D]"]
  WABIND --> WAHMAC["GET verify e POST HMAC por App [P offline]"]
  WAHMAC --> WAINBOX["Inbox durável antes do ACK [R S0]"]
  WABIND --> WATOKEN["Token: verificação por terceiro [R]"]
  WA --> WASEND["C03/C06/C12: outbox e envio Graph [P offline]"]
  INT --> OAI[OpenAI API]
  INT --> N[n8n opcional, fora do caminho critico Meta]
```

S0 fundação: telefone de cliente pode existir em A/B/C com históricos isolados; emissor Prumo exclusivo por loja; importação C01, ingresso C02, elegibilidade C04, planos C05 e cancelamento C08 simulados com eventos e idempotência; nenhuma transmissão externa. S0 testes sintéticos; S1 operação humana/banco simulados; S2 IA/Meta simulados; S3 MCP controlado; S4 ativação real somente por autorização específica. Não há IA Analista autônoma. Nenhum dado cruza lojas.

## Linha do tempo S0 auditada — 18/10/2026

```mermaid
flowchart TD
  ROOT["S0: fundação comercial, sem produção"] --> ID["028/031: identidade 8↔9 e C01 por loja"]
  ROOT --> Q["029/030/032: inbox, outbox e tarefas sintéticas"]
  Q --> C02["033/034: aplicação C02 atômica, pendências e integridade"]
  ROOT --> CB["034B: auditoria de contrato C07/WA-01C"]
  ROOT --> AUTH["035: GoTrue/PostgREST local"]
  AUTH --> GATE["036 + 036A: proprietário das entradas assinadas e ACL completa"]
  GATE --> A["037A: ALTER OWNER comercial isolado é NO-GO"]
  A --> B["037B: RLS e DML por loja somente em rollback"]
  B --> C["037C: cadeia assinada C08/C07 comprovada no PG17 — owners comerciais legados"]
  C --> AUD["Auditoria 037A–C: sessão/ator e replay divergente — PG17 PASS"]
  AUD --> FUT["Futuro: projetar owners comerciais sem postgres e revalidar no Supabase local"]
  CB --> WAIT["C07 Meta real bloqueado: ocorrência/dedupe e armazenamento protegido"]
```

### Decisões e fronteiras

- **[D] DEC-WA-01/02/03:** variantes telefônicas brasileiras com e sem nono dígito são aliases do mesmo contato **quando a associação é confiável e não ambígua na mesma loja**; o mesmo telefone pode existir em outras concessionárias com histórico independente. Reutilizar o domínio S0 e manter inbox/outbox transacionais. Nenhuma fusão automática de pessoas em conflito ou compartilhamento de histórico entre lojas.
- **[D] DEC-WA-05:** App/WABA/número emissor Meta pertencem à concessionária; a Prumo integra sob autorização. Um emissor é atribuído a apenas uma loja por vigência. Não modificar canais comerciais por inferência.
- **[P] WA-01C:** `statuses[].id` é ID da mensagem enviada, **não** ID único de ocorrência do callback; `status+timestamp` não prova deduplicação. C07 real permanece não integrado à inbox.
- **[R] DEC-WA-04/06:** ambiente definitivo, segredos, proteção/retensão de payload, recibo/ACK operacional e recuperação ainda exigem definição/autorização. A POC Meta não autoriza operação comercial.
- **[D] Meta → Supabase direto como direção de integração:** Edge Function autentica a origem, persistência durável antes de ACK, worker controlado, outbox e Graph; n8n opcional fora do caminho crítico, não um componente obrigatório.
- **[D] Oito estados comerciais somente:** `aguardando primeiro disparo`, `primeiro disparo enviado`, `em atendimento pela IA`, `em atendimento pelo operador`, `cadastro enviado ao operador`, `cadastro enviado ao banco`, `vendido`, `perdido`. `APPLIED`, `QUARANTINED`, estados Meta e leases são técnicos, não comerciais.
- **[R] Menor privilégio comercial integral:** gateway e assinador têm papéis NOLOGIN isolados; as **duas wrappers comerciais legadas ainda pertencem a `postgres`**. S0-037A/037B não autorizaram a transferência. S0-037C testa a cadeia existente, não instala papel operacional novo.
- **[Gate]** GitHub PR #1 e PR #2 permanecem Draft, sem merge; testes PostgreSQL descartável e Supabase Auth/REST local quando necessários; Supabase hospedado não recebeu as migrations comerciais, sem envio Meta/Banco real, nenhum plano pago ou deploy autorizado.

### Marcos e evidências

| Marco | Escopo | Evidência |
| --- | --- | --- |
| S0-033/034A | C02 ligado à inbox em uma transação; prova de conclusão, conflito de identidade durável e FKs por canal | PG17 aprovado, testes WA33/WA34 |
| S0-034B | C07 callbacks sintéticos, preservação de observações e dedupe **não operacional** | [CI #39119612194](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39119612194) |
| S0-035 | GoTrue/PostgREST local para 028–034 | [CI #39120161917](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39120161917) |
| S0-036/036A | Entradas assinadas com owner restrito, inventário completo de ACL | [CI #39122948236](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39122948236) |
| S0-037A | Guard `current_user=postgres` e RLS bloqueiam transferência isolada | [CI #39123912355](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39123912355) |
| S0-037B | Policies artificiais por loja e DML C07/C08 descartável | [CI #39126117200](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39126117200) |
| S0-037C | Regressão do caminho assinado com HMAC, sessão, nonce, C08 e duas decisões C07 | [CI #39127146330 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39127146330) |
| Auditoria S0-037A/B/C | Sessão e ator distintos, gestor interloja, replay C07 idêntico/divergente | [CI #39128133133 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39128133133) |
| S0-037D | Capacidade de laboratório por operação/loja/alvo/versão/txid; GUC falsificada não é autorização | [CI #39130042204 — SUCCESS](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39130042204) — **não é redução do owner comercial** |

**S0-037D testada no PostgreSQL 17:** capability de teste emitida pela fixture privilegiada, consumida em política RLS transacional sem confiar em GUC de sessão. Não há emissor autenticado e nem substituição das wrappers comerciais `postgres`. [CI PG17 #39130042204](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39130042204) aprovado; emissão real e auditoria integral continuam pendentes. Ver `docs/S0_037D_CAPACIDADE_TRANSACIONAL_2026_10_18.md`.

O `MAPA_MENTAL.md` é índice de navegação. As decisões normativas e os registros de aceite versionados têm precedência sobre os nós simplificados deste mapa. Atualizá-lo a cada incremento **depois de verificar** CI e escopo real, sem rotular proposta como entregue.


## Acompanhamento vivo — WhatsApp/Meta WA-01 a WA-04 (18/10/2026)

**Convenção:** este mapa é um **índice**, não um aceite técnico. A cada incremento relevante realizado nas frentes, atualizar também a linha do tempo, os bloqueios e a evidência observada; não mover automaticamente um item de [P] para [V], [D] ou **produção**. A atualização ocorrerá durante as próximas atividades de desenvolvimento, **não em segundo plano**. Os documentos e testes de cada PR prevalecem sobre este resumo.

```mermaid
flowchart TD
  WA0["WhatsApp Cloud API / Meta — sem ativação real"] --> I["WA-01A–D: HMAC, parser, recibo ACK candidato, IDs técnicos, GET"]
  I --> O["WA-02A–D: envio texto/template e conciliação — offline"]
  O --> AU["WA-03A/B: auditorias integradas, correções de isolamento e ocorrência"]
  AU --> CR["WA-04A: slots distintos GET / HMAC POST / Graph"]
  CR --> RT["WA-04B: rota confiável + assinatura por App + WABA/canal"]
  RT --> LC["WA-04C: propostas de revogação/rotação — somente laboratório"]
  LC --> GATE["Bloqueado: verificação externa do token e gates S0 / DEC-WA-04/06"]
  GATE --> LIVE["Testes reais e ativação: somente após liberação + autorização específica"]
  I --> C07["S0/C07: occurrence_ref interno + payload protegido + ACK durável pendentes"]
  RT --> OWN["DEC-WA-05: App/WABA/emissor por concessionária"]
```

| Etapa | Situação em 18/10/2026 | Evidência e limite |
| --- | --- | --- |
| WA-01A/B/C/D | **[P]** Código candidato versionado no PR #2 | Assinatura do corpo bruto, GET, pistas técnicas **não autoritativas** e estrutura de ACK; nenhum recibo real COMMITTED |
| WA-02A/B/C/D | **[P/V local]** Construtores, envio Graph fictício e callbacks técnicos | Testes unitários sintéticos; **nenhum** HTTP Graph, retorno comercial ou persistência durável |
| WA-03A/B | **[P/V local]** Auditorias e reparos publicados | 120 testes na suíte WA-03B; corrigidos isolamento, posições dos arrays, HMAC/buffer e correlações; não é CI de produção |
| WA-04A/B | **[P/V local]** Roteamento confiável e slots segregados por App/canal | 167/167 testes locais na WA-04B (inclui regressões anteriores selecionadas); sem token real ou conexão Supabase |
| WA-04C | **[P/V local]** Propostas puras de revogação de App/canal e rotação de slots | 13 testes próprios + 10 novos testes adversariais WA-04; 235 testes no conjunto completo das frentes Meta (incluídos WA-01 legados). Propostas **não aplicadas**, App inativo na cópia; sem ativação |
| Credenciais Meta definitivas | **[R]** Dependência de **verificação por terceira pessoa** para liberar o token | **Não disponíveis** para esta frente; testes reais WhatsApp adiados; não pedir valores em Git, issue, chat ou arquivo |
| S0 ↔ Meta real | **[R]** Gate operacional pendente | Ambiente DEC-WA-04, segredos/rotação/ACK/retensão DEC-WA-06, registro App→loja/canal autenticado, payload protegido, `occurrence_ref`, autorização C03/C06/C12 e C07 |

**Ressalva de auditoria entre frentes (18/10/2026):** após o registro WA-04C 13/13, o PR #2 acrescentou o commit `c98f3609b18c93dbd7c4cc8d4a75fd527c2a8be5`, alterando `integrations/whatsapp-meta/credential-lifecycle.ts` para negar registros inválidos/não clonáveis. A evidência 13/13 corresponde ao código **anterior** e **não certifica esse novo HEAD** sem nova rodada de testes da frente Meta. O PR #1 não incorporou nem executou esse código. **[R] Regressão WA-04C após a alteração**; continuar proibidas credenciais reais, Graph e deploy.

**Fonte de navegação:** [PR #2 — frente WhatsApp/Meta](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2) e seus documentos `docs/integracoes/whatsapp-meta/wa04a-...`, `wa04b-...`, `wa04c-ciclo-credenciais-sem-token-v0_1.md`. **Coordenação S0:** [PR #1](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/1), onde owners comerciais mínimos, RLS, Gateway e persistência/ocorrências C07 seguem seu próprio gate; não confundir CI PostgreSQL descartável ou Supabase **local** com implantação hospedada.

**Regra operacional preservada:** não usar a POC concessionária de demonstração como ambiente definitivo por inferência; nenhum merge, deploy, migração remota, webhook comercial ou número alterado. Mesmo depois da liberação do token, testes reais exigirão confirmação do projeto Supabase correto, das permissões/segurança e uma autorização específica.

**Auditoria complementar WA-01 a WA-04C (18/10/2026):** **235/235 testes sintéticos locais PASS** em **16 arquivos** (180 regressões anteriores + 10 novos adversariais WA-04 + **45 testes legados WA-01** reexecutados); TypeScript estrito **PASS** dos **11 módulos** e dos testes. O código WA-04C foi corrigido para recusar registros de App malformados/não clonáveis em vez de lançar exceção. Os hashes Git dos arquivos ensaiados foram conferidos. O diagrama **inicial** cresce apenas com cinco vínculos Meta relevantes para a arquitetura; detalhes técnicos permanecem nos documentos. **Nenhuma** aprovação de token, homologação Meta, commit durável S0 ou produção decorre desses testes.
