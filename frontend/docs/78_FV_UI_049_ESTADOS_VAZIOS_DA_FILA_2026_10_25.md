# FV-UI-049 — Estados vazios da busca e filtros

**Data:** 25/10/2026 · **Repositório autorizado:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual`.

## Problema corrigido

Até FV-UI-048, `renderList()` apresentava um texto genérico "Nenhuma conversa neste filtro" para qualquer lista vazia, exceto perfil suspenso. Também exibia a contagem total de `projectInbox` em `#list-count`, mesmo que `filtered()` tivesse zero correspondências, tornando a quantidade visível ambígua.

## Ajuste estritamente local e visual

- Diferencia **busca textual vazia**, **filtros sem correspondências**, **lista ativa/histórica genuinamente vazia** e **perfil fictício suspenso**. Cada caso apresenta título e orientação sem expor dados além do contexto autorizado.
- Em refinamento, o contador passa a exibir `<visíveis> de <total da aba> atendimentos`. A base de cálculo para os indicadores sintéticos e a lógica de elegibilidade não mudaram.
- Somente com refinamento ativo e base de lista não vazia, o estado vazio oferece **Limpar busca e filtros**. A ação limpa `state.query`, `state.filter`, `state.statusFilter` e respectivos inputs, depois re-renderiza a lista e devolve foco à busca. **Não** altera `actorId`, `shopId`, `inboxView`, `selectedId`, permissões, casos ou estados comerciais.
- Perfil suspenso continua sem ação de limpeza ou de liberação. Lista realmente vazia orienta usar as abas existentes; não adiciona uma transição de dados.
- Estado vazio com `role=status`, área de 44px para ação, cores nos temas claro/escuro e apresentação compacta em 320px.

## Critério de regressão

Roteiro Chromium 320×640, 390×844, 900×780, 1440×900 × claro/escuro: busca impossível, indicador de zero resultados, limpeza com foco preservado, filtros restabelecidos, perfil/concessionária inalterados, retorno de casos e suspensão sem ação de limpeza. Contrato Node verifica distinções, CSS e roteiro. Aprovação **apenas quando GitHub Actions nativo sobre SHA integral, com manifesto repinado, confirmar sucesso no Chromium/Node/Python**.

## Fronteiras

Demonstração sem API. Nada altera Auth, gestão, S0/S1, concessões, Meta/WhatsApp, banco, transportes, pagamentos, deploy, ou `main`. Não modificar a projeção de visibilidade `projectQueue`/`projectInbox`, nem automatizar qualquer operação real.

**Etapa anterior:** [FV-UI-048](./77_FV_UI_048_ESPACO_LISTA_MOVEL_2026_10_25.md).
