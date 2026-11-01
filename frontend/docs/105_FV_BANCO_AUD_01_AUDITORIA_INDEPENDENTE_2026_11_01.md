# FV-BANCO-AUD-01 — Auditoria independente da fila bancária e do protocolo entre frentes

**Data:** 01/11/2026. **Repositório:** `prumogrowth/Prumo-Growth-Platform-V2`. **Objeto auditado, imutável:** `feat/fv-banco-fila-aptos-20261101` @ `d50e259b9b96e6ca3094b3caefdaacd615e2f93c`. **Branch exclusiva do relatório:** `audit/fv-banco-01-20261101`. Nenhuma edição foi feita na fonte auditada.

## 1. Verificação e limitação do escopo

- [CI oficial 41296687168](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/actions/runs/41296687168): status `completed/success`, HEAD exato `d50e259b9b96e6ca3094b3caefdaacd615e2f93c`, gate `FULL LOCAL ACCEPTANCE: PASS`, **459/459 testes Node**, nenhuma falha Node, Chromium Playwright e pacote de prévia executados pelo workflow.
- O teste é **sintético** e a maioria das regressões históricas cobre a interface antiga; o novo `bank-ready-list.mjs` tem **quatro testes específicos de domínio**. A CI não é teste da lista de aptos renderizada: esse componente não é consumido por `frontend/visual/app.mjs`.
- `frontend/docs/104_FV_BANCO_01_LISTA_APTOS_TELAS_PROPRIAS_2026_11_01.md` reconhece explicitamente: Lote A = seletor candidato e testes; Lote B = navegação visual, ainda não entregue. Nenhuma operação bancária, autorização S0 real ou produção foi realizada.

## 2. Achados de coerência

### BAN-AUD-01 — ALTA — `unavailable` é aceito como “não enviado”

Em `frontend/visual/bank-ready-list.mjs`, `NOT_YET_SUBMITTED` inclui `'unavailable'`, aceitando registros com projeção bancária inexistente ou desconhecida. Mas `bankProjectionFor` (`frontend/visual/bank-view.mjs`) retorna justamente `phase:'unavailable'` **quando o estado do banco é ausente, inválido ou não comprovado**. **Ausência de evidência de remessa não prova ausência de remessa**.

Reprodutor por inspeção da própria fixture: `A-114` tem `bankReadinessProjection.confirmed=true` e versão coincidente, mas **não fornece `bankProjection`**; ainda assim `projectBankReadyList` espera/exibe `A-114` no teste positivo. O nome entraria na fila apesar de não existir confirmação explícita `not_submitted`.

**Aceite corretivo:** representação autoritativa/versionada S0 de aptidão **e de elegibilidade para nova remessa**, ou estado explícito `not_submitted` autenticado, antes de listar. Rejeitar fase desconhecida e estados de solicitação, incerteza ou prova em andamento. Ajustar a fixture para um exemplo realmente elegível, sem transformar “sem dado” em “não enviado”. Regredir perda de `bankProjection`, `unavailable`, `unverified` e remessa já confirmada. **Não modificar S0 ou implantar envio a partir do frontend.**

### BAN-AUD-02 — ALTA / BLOQUEIO DE ACEITE VISUAL — módulo não integrado à tela

`frontend/visual/app.mjs` continua com `openBank()` abrindo `bank-dialog`. `renderBank()` popula `bank-case-select` a partir de **todas as conversas `accessible()`**, e não de `projectBankReadyList()`; os nomes ainda são acompanhados de `id` e concessionária no seletor. `frontend/visual/index.html` define `bank-dialog` e `team-dialog` modais. Não há import do novo seletor no app. Logo a decisão do proprietário de **área própria Banco/Gestão e lista apenas de nomes aptos** **ainda não está aplicada visualmente**.

**Aceite corretivo:** Lote B separado, com áreas `Conversas | Banco | Gestão` sem diálogos grandes, Banco alimentado pelo seletor de aptos, lista somente nomes, ficha autorizada somente leitura, navegação desktop/móvel, retorno e preservação de rascunhos/áudios, sem marcar conversa como lida ao consultar Banco. Nova matriz DOM/Chromium e auditoria de interface; sem merge/deploy automático.

### BAN-AUD-03 — MÉDIA / CONTRATO S0 — aptidão do caso versus histórico do cliente

A fixture `A-114` é **novo ciclo humano após remessa bancária** do caso `A-105` (`postmarkProjection.originCaseRef='A-105'`; vínculo bancário histórico preservado). `A-114` tem `bankReadinessProjection` afirmativa. A fila não decide se há **nova operação bancária permitida**, simples atualização de ficha ou continuação humana de remessa anterior. Em múltiplos casos do mesmo cliente/loja, repetir nomes pode induzir remessa duplicada.

**Aceite contratual:** S0 distinguir `customer/shop`, `case/cycle`, operação de remessa versionada e aptidão explícita para **a próxima remessa**, com idempotência e preservação de snapshot anterior; não deduzir novo envio de nova conversa ou nova versão de ficha. Não proibir por heurística todo recontato legítimo.

### BAN-AUD-04 — MÉDIA — cobertura negativa limitada

Os quatro testes BANCO-01 checam autorização básica, versões, algumas fases e terminalidade, mas **não exercitam estado `unavailable` como negação**, inconsistência entre registro pronto e ficha com `missing/conflicts`, nem múltiplos casos do mesmo cliente/loja e suas respectivas provas de remessa. O título “ficha parcial, incompleta” é mais abrangente que as mutações efetivamente verificadas. `registrationProjectionFor` aceita `partial` persistido; uma aptidão S0 verdadeira poderia torná-lo elegível, mas a taxonomia de lacunas essenciais/opcionais não está aqui ratificada.

**Aceite corretivo:** testes de negativas adicionais e contrato S0 sobre *lacuna bloqueante* versus opcional. A UI não deve criar regra própria a partir da contagem de campos ou assumir que qualquer `partial` sempre é inabilitado.

### BAN-AUD-05 — BAIXA / UX — nomes iguais

A projeção da lista retorna `{id,name}`, corretamente reservando `id` para seleção interna, mas não descreve como o usuário distinguirá **dois clientes homônimos** se a instrução for mostrar somente nomes. Evitar solução por exposição desnecessária de CPF/telefone; o desenho pode tratar casos homônimos sob regra de privacidade e desambiguação futura, se ocorrer.

## 3. Pontos preservados

- Ficha somente leitura; campos confirmados/proveniência; `bankReadinessFor` exige evidência de aptidão e **mesma versão de ficha**, com escopo de titular.
- Gestor supervisor não recebe automaticamente D3/D4; falta de permissão nega a entrada no seletor.
- Projeção de lista contém apenas `id` interno e `name` (sem etiquetas “Cadastro pronto”).
- Casos comerciais já marcados `cadastro enviado ao banco`, `vendido`, `perdido`, remessas solicitadas/em andamento/pendentes de retorno são excluídos do **modelo de lista**.
- Nenhum comando C15–C18 operacional, escrita, transferência bancária ou status comercial foi introduzido.

## 4. Protocolo entre frentes: adesão e demandas existentes

Lido e adotado o [protocolo #4](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/4): uma Issue por dependência, comentários `STATUS:`, revisão da frente consumidora, SHA e CI; `ENTREGUE` não significa `ACEITO`.

- [#15 Frontend→S0/S1](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/15): demanda canônica de Banco. Registrar **BAN-AUD-01/03/04**, solicitar contrato S0 de remessa elegível com negativa para desconhecido, sem duplicar Issue. Frontend mantém correção visual do Lote B isolada.
- [#14 Frontend→S0/S1](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/14): S0 respondeu `STATUS: EM_ANALISE`, assumindo contrato futuro de leitura ao abrir, operador titular, pendência e timestamps. Frontend deve revisar versão/prova quando **efetivamente publicada**, não tratar o comentário como API pronta.
- [#13 OpenAI→S0/S1](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/issues/13): sínteses **curtas** F01/F02/F03 na aba **Resumo** e Histórico técnico separado; **pedido explicitamente futuro, não implementar agora**.
- Demais #2/#5..#12: acompanhar interfaces relevantes, sem assumir ownership de Meta/OpenAI/S0. **Não há demanda nova explicitamente pronta para aceite pelo Frontend** no checkpoint consultado.

[Autorização de desenvolvimento isolado](https://github.com/prumogrowth/Prumo-Growth-Platform-V2/blob/95186006964f2e29b330164b5cda189fa65768aa/docs/contratos/s0s1_meta_registry/DECISAO_ESCOPO_INTEGRACAO_FRENTES_2026_11_01.md) permite adapters/testes candidatos, não concessão de poderes S0, produção ou dados reais.

## 5. Parecer

**RESULTADO: ACEITE FUNCIONAL/VISUAL BLOQUEADO**, apesar da CI integral `PASS` para o escopo sintético testado. O Lote A é um **componente de domínio entregue tecnicamente**, mas possui lacuna de segurança semântica `unavailable` vs `not_submitted` e **não está conectado à UI**. A correção requer coordenar S0 pela #15, ajustar o seletor e executar o Lote B com auditoria independente de navegação e escopo.

**Sem merge, deploy, alteração de dados hospedados ou aceite automático.**
