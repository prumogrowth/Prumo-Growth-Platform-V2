# WA-26 — Ponte S0 ↔ catálogo de finalidades: três gates offline

**22/10/2026 · Frente WhatsApp/Meta · PR [#2 Draft](https://github.com/prumogrowth/Prumo-Growth---Platform/pull/2).** Continuação WA-25, execução exclusivamente em laboratório. **Não é endpoint, consulta S0 real nem autorização Graph.**

## 1. Regras e precedência

Fontes vigentes: [00 — WDC-10/11](./00-decisoes-vigentes-precedencia-documental-2026-10-21.md), [01 — §§5–6 e §11](./01-especificacao-funcional-vigente-whatsapp-meta-2026-10-21.md), [WA-22 — XWA-03, 10 e 12](./wa22-revisao-cruzada-outras-frentes-contratos-2026-10-22.md), [WA-25](./wa25-finalidades-grants-filtro-candidatos-offline-2026-10-22.md), S0-043/044/045 (branches da S0 em Draft). Regras humanas de concessão por caso não são inventadas pelo adaptador.

O **catálogo aprovado/ativo** permanece necessário, mas insuficiente. Planejamento F02 não implica consentimento, autorização comercial da campanha, posse do caso ou capacidade de enviar.

## 2. O que foi construído

- [`s0-template-purpose-bridge.ts`](../../../integrations/whatsapp-meta/s0-template-purpose-bridge.ts): portas FAKE de leitura S0, `prepareS0TemplateCandidatesFixture()` e `recheckS0TemplateCandidateFixture()`.
- [`s0-template-purpose-bridge.test.ts`](../../../integrations/whatsapp-meta/s0-template-purpose-bridge.test.ts): **26 cenários WA26-01..26** sobre escopo, política, etapa e revogação.
- **PLAN:** resolve escopo *simulado* de principal/caso/lead, verifica política e catálogo separados, e retorna apenas referências mínimas dos templates para a Planejadora F02. Os `internal_tickets` com IDs de caso/lead são **somente para armazenamento/proteção interna S0**, não para prompts, frontend ou cliente.
- **RESERVE:** reobtém o escopo, prova de política e catálogo e valida a versão do caso, revisão de autorização, revisão da política, status Meta, finalidade e grants exatos do candidato.
- **PRE_DISPATCH:** exige ticket interno originado de RESERVE e refaz as consultas e regras. Revisões/versões alteradas, revogação de consentimento, opt-out, público/campanha inelegível ou template pausado/remapeado bloqueiam a etapa. `RESERVE` não pode ser pulada.
- Em todos os retornos: `send_authorized:false`, `production_authorized:false`; não há Graph, variável de mensagem, telefone de destinatário, banco, conexão real ou callback ACK.

## 3. Contratos em aberto com os donos S0/S1/Meta

A porta `resolveSelection(selection_ref,phase)` é **sintética**. Futuramente, a S0 precisa autenticar serviço/ator, grants de concessionária e WABA, caso atribuído (inclusive exceção por caso), versão e revogação de permissão sob RLS real. Nomes de papéis usam **Diretor/Gestor/Consultor** (S0-045); não usar rótulos para inferir grant. `selection_ref` é identificador de lookup, jamais token de autorização.

A porta `readScopedPolicy(scope,phase)` simula dados de uma fonte confiável **independente do modelo/frontend**: consentimento válido **da mesma concessionária**, opt-out, permissão no caso, elegibilidade de público, campanha/oferta comprovada e revisões. Não representa consentimento real nem licença LGPD/Meta; política externa e comprovação permanecem **[R/V]**. Campanha não aplicável é diferente de campanha elegível.

A porta `readScopedCatalog(scope,phase)` simula leitura tenant-scoped de versões/status Meta, finalidades N:N e grants. **Não** cria tabela, não fixa entidade física de campanha e não altera a frente S0. Toda chamada positiva é uma **demonstração de algoritmo**, não prova de que as portas realmente estejam seguras.

A leitura sequencial desses três mocks **NÃO é transação única nem evita TOCTOU**. Integração operacional só após serviço S0 autenticado, RLS, snapshot consistente/lock e rechecagem atômica junto da reserva e do despacho, contratos de retorno/auditoria e status Meta fresco. A validação final real também depende dos demais gates de C06, janela, opt-in/opt-out, tentativas e autorização de envio que este contrato não substitui.

## 4. Prova técnica e limitações

- Commits iniciais de módulo e testes: `d4eef0b1158fbf9677c3bab24e4a53e3804b6bdf`, `598c1f078b2b9b3c33839bd037cfc7d0598e72a6`.
- [GitHub Actions #39819592116](https://github.com/prumogrowth/Prumo-Growth---Platform/actions/runs/39819592116), commit `598c1f0...`: **Node 22 567/567 testes de regressão PASS**, incluindo os novos WA26 (44/44 gate WA16/17). Jobs PG17 WA06D e WA15C são separados; registrar conclusão somente após status final dos jobs.
- Testes com estados de revisão e permissão alterados são **fixtures**, não prova em produção. Nenhuma alteração em outra frente, deploy, merge ou comunicação com Meta ocorreu.

**Próxima entrega sugerida:** ratificar com S0/S1 quais fontes autenticarão `resolveSelection`/política/catálogo e suas revisões; depois integrar controles transacionais com prova física em banco descartável e testes de concorrência, sem acionar Graph real.
