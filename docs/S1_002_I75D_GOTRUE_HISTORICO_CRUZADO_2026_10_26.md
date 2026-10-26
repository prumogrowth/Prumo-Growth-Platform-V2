# S1-002 — I75D — Histórico contextual por contato e loja com GoTrue real

**Data:** 26/10/2026. **Branch:** `feat/s1-002-equipe-prumo`. Integração test-only I63 com GoTrue/PostgREST descartáveis. **Sem alteração de S0, migrations hospedadas, `main` ou deploy.**

## Recuperação externa e contrato

Fonte: [PR Draft #12 — retorno à Issue #10](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/pull/12), commit `e3bf423a8fbf2064e536c416364c8cc318f1998a`, base S0 `060b472b03e9e7b89f5b3d7e19b72b98836f106d`. O relatório da auxiliar registra 11 snapshots, cinco catálogos de laboratório e negativos SQL sobre isolamento, escrita e revogação. **Não foi importado código do PR #12, seus workflows ou suas migrations**: a S1 consumiu o contrato e ampliou seus testes próprios com JWT GoTrue real.

Principais fatos mantidos: a chave histórica é **`(concessionaria_id, leads_loja.id)`**; telefone não une lojas; `mensagens` chega ao contato via `concessionaria_id + conversa_id`; acesso contextual a caso antigo **não** permite escrever nele; I63 é **candidata** (8 policies em `supabase/tests`), não RLS homologada. Helpers I63 de laboratório não são endpoint produtivo de mídia.

## Implementação I75D

- `scripts/test_s1_002_i75d_real_history_e2e.py` cria somente dados sintéticos e roda nas fases **antes e depois** da revogação I61 já executada no I63.
- `scripts/test_s1_002_i63_canonical_rls_e2e.py` ganhou as duas chamadas ao testador I75D. A operação de transferência/revogação assinada I62, as políticas SQL I63 e a lógica de autorização **não foram alteradas**.
- `.github/workflows/s1-002-i37-intake-signed-local.yml` recebeu somente o novo caminho no filtro de execução da **própria frente**. Nenhum novo workflow foi criado; nenhuma otimização da Issue #3 foi executada.

As provas executam após transferência I62 real e conservam a exceção de `op6` sem grant geral de loja. Comparam caso atual e caso de ciclo anterior do mesmo contato, pré-caso I63 já existente e novo contato de **outra loja usando exatamente o mesmo telefone**, mas lead_id distinto.

## Marcadores confirmados no log GoTrue real

| Prova | Resultado |
|---|---|
| **I75D-E2E-01** | Consultor com exceção ativa lê conversa e mensagem de caso/ciclo anterior do **mesmo** contato e loja |
| **I75D-E2E-02** | Caso, conversa e mensagem da **outra concessionária**, apesar de telefone idêntico, não aparecem |
| **I75D-E2E-03** | Gestor de outra equipe não herda leitura do histórico antigo por coincidir a loja |
| **I75D-E2E-04** | POST/INSERT sintético em conversa de caso antigo recusado; nenhuma mensagem indevida persistida |
| **I75D-E2E-05** | SELECT de `conteudo_sintetico` autorizado comprovado na candidata; **não** é catálogo D3/D4 nem aprovação de minimização |
| **I75D-E2E-06** | Revogação assinada I61/I62 corta leitura do ciclo anterior usando o **mesmo JWT GoTrue ainda válido** |
| **I75D-E2E-07** | Objetos sintéticos extras eliminados e exatamente **8 policies I63** preservadas no ensaio |

**Certificação final:** commit de código `d3e9f0a053e16d90190696dd59cec6d77b7f1e73`; [workflow oficial GoTrue #40403944872](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40403944872), jobs `121856741178` e `121856741743` **SUCCESS**. Logs explicitam `PASS I75D-E2E-01..07` **7/7**, preservam I63 6/6, I74 GoTrue 8/8 + PROV 4/4 + SEC 3/3, `S1INTAKE-147/148`, encerramento de 132 E2E históricos + 16 novos I37 e **179 unitários**.

**Intercorrência, não contabilizada como aprovação:** [run #40403455399](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40403455399) executou 6/7 I75D e falhou por falta do prefixo `f` em uma consulta SQL que verificava limpeza da loja B; a interpolação usou `'{foreignlead75}'` literal em vez de UUID. Corrigido no commit `d3e9f0a`. Não houve alteração de RLS, ACL ou regras de escrita. A segunda execução concluiu **todos** os testes e regressões.

## G3 continua PARCIAL: contratos e dependências reais

1. **Revogação de sessão para SELECT histórico não corrigida ou certificada.** O PR #12 demonstrou com `auth.uid()` sintético que remoção de linha em `auth.sessions` não interrompe o SELECT por si só. A I75D demonstrou revogação da **exceção I61**, evento diverso. A correção de sessão pertence à S0/Codex principal; **não transportar** a proteção CFI do PR #9 para a RLS de leitura por inferência. Exigir futuro GoTrue logout/teste de token ainda válido e reavaliação do contexto antes de homologar.
2. **Mídia, Storage, download e URLs assinadas não identificados** nos catálogos examinados pelo PR #12. Atestados/modalidades do F03 PR #1 são fixtures privadas de laboratório, não arquivo, URL ou banco operacional. Sem endpoint real não existe teste válido de download nem de revogação de URL.
3. **D3/D4 não ratificados** por campo, papel e finalidade; retenção, mascaramento e expurgo ainda precisam de decisão Produto/LGPD/S0. O texto sintético de mensagens é SELECT-able sob RLS da candidata; isso não legitima revelar dados bancários que venham no texto.
4. **Sem integração de produção** com frontend, Meta ou CFI/F03. O PR #12, o PR #9 e o PR #8 permanecem isolados; G1/G2/G4/G5/G6 e outros critérios G3 continuam sujeitos a homologação própria.

**Próxima execução sugerida:** reconciliar a futura entrega de sessão da S0 com a leitura G3, e manter evolução independente de G1/G2. A Issue #10 documenta as dependências; não duplicar a correção do núcleo. **Gate G3 parcial; nenhum merge/deploy autorizado.**
