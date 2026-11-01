# FV-BANCO-01 — decisão de produto: Banco como área própria, lista exclusiva de aptos

**Decisão expressa do responsável:** 01/11/2026. **Escopo:** UX e contrato candidato do Frontend sintético; não habilita execução bancária ou altera S0/S1/Meta.

## Decisão vinculante

1. Conversas, Banco e Gestão são **áreas/telas distintas** da **mesma** plataforma. Não devem abrir grandes janelas modais sobre Conversas para a navegação principal. Modais menores podem servir a confirmações pontuais.
2. **A lista principal do Banco contém exclusivamente cadastros realmente prontos e elegíveis para ir ao banco.** Pendências, cadastros incompletos, conflitos bloqueantes, processamento em curso, estados sem confirmação e clientes aguardando retorno de remessa **não aparecem**.
3. **Cada item da lista exibe apenas o nome do cliente**, sem selo, tag ou etiqueta “Cadastro pronto”, pois estar pronto é pré-requisito do universo da lista. A chave técnica do caso pode existir internamente e no contexto da ficha para desambiguação, sem virar etiqueta repetitiva da fila.
4. Selecionar o nome apresenta os **dados cadastrais confirmados e autorizados**, em modo somente leitura, com proveniência e versão em detalhes quando pertinente. A consulta no Banco não abre conversa nem marca leitura.
5. Um caso deixa a fila de prontos quando a S0 confirmar efetivamente a remessa. O registro bancário e os snapshots permanecem em um **histórico próprio**, não na fila de entrada.
6. O Consultor não edita manualmente campos da ficha. O eventual botão **“Registrar envio realizado ao banco”** é uma **capacidade futura** (C15–C18), só habilitável mediante contrato S0, autenticação, autoridade, versionamento, referência/prova da operação feita no canal bancário autorizado, recheck e confirmação persistida. O protótipo não deve simular uma remessa efetiva nem marcar enviado por clique local.
7. Gestor em supervisão não obtém automaticamente dados D3/D4; apenas acesso autorizado pela S0 pode expor ficha detalhada. Nunca ampliar concessões no frontend.
8. Banco e Gestão são áreas navegáveis, com retorno claro a Conversas, preservação de rascunhos por contexto e comportamento responsivo.

## Critério de elegibilidade da lista (projeção sintética)

Exigir cumulativamente: caso/loja/ator autorizados; caso ativo, ainda não enviado/não terminal; ficha persistida e visível ao titular; **aptidão bancária confirmada e versionada** correspondendo à versão atual da ficha; nenhuma remessa ou solicitação já em curso. Ficha persistida **não equivale** automaticamente a aptidão; ausência de status, campo de exemplo ou etiqueta “pronto” não é evidência.

O núcleo S0 é a autoridade definitiva. `frontend/visual/bank-ready-list.mjs` implementa apenas uma projeção conservadora para demonstração. A lista só retorna `id` (chave interna) e `name`. Esse recorte não deve se tornar autorização ou API de produção.

## Estrutura visual proposta

- Menu lateral: **Conversas | Banco | Gestão** (Gestão apenas para Gestor autorizado).
- **Banco:** lista pesquisável de nomes aptos à esquerda; ficha do nome selecionado à direita, em desktop. Em móvel, lista e ficha em telas sequenciais, com botão Voltar. Sem colunas obrigatórias de “estado” ou “cadastro pronto”.
- Na ficha: identificação contextual, dados disponíveis/proveniência, ação bancária futura claramente indisponível até integração, navegação ao histórico pertinente sem confundir com fila de entrada. Não mostrar dados pendentes na lista.
- **Gestão:** tela própria reaproveitando Consultores, Monitoramento, Lotes e Fila compartilhada; sem atribuir ao Gestor acesso cadastral indiscriminado.

## Aceite e escopo técnico

**Lote A (nesta branch):** registrar decisão; implementar e testar seletor conservador de nomes aptos. **Não afirmar que a migração de telas está concluída.**

**Lote B (em branch descendente):** substituir navegação modal principal por telas reais, adaptar testes DOM/Chromium, preservar conteúdo de Conversas/áudio/Notas, inclusive em trocas de tela, e manter permissões. Não fundir em main sem auditoria funcional e visual independente.

**Lote C (dependência externa):** só habilitar efetiva ação de registro C15–C18 após os contratos, evidências, permissões e autorização de produção.

**Não alterar** estados comerciais canônicos ou declarar integração bancária real.
