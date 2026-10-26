# FV-UI-056 — Busca em português com acentos opcionais e espaços equivalentes

**Data:** 25/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`.

## Problema e decisão

A busca da fila convertia texto para minúsculas, mas exigia correspondência literal de acentos e espaços: digitar `cadástro enviado ao banco` não encontrava `cadastro enviado ao banco`, e `Cliente    Exemplo 02` não encontrava `Cliente Exemplo 02`. Não mudar papéis, estados, catálogo, autorizações ou conteúdo dos registros.

## Implementação

- Aplicar `normalize('NFD')` e retirar marcas combinantes U+0300–U+036F; converter para minúsculas em `pt-BR`; contrair sequências de espaços em um espaço e remover espaços nas pontas.
- Aplicar **a mesma normalização** à expressão procurada e somente aos campos já buscáveis de cada registro (`id`, `name`, `tag`, `status`). Conservar semântica de substring existente, sem indexar mensagens, notas, telefone, banco ou dados restritos.
- **Obrigatório:** executar `visibleConversations(records,actorId,shopId)` *antes* de qualquer busca. A normalização jamais deve ampliar o conjunto ou dar permissão real. O próprio frontend continua sendo demonstração sintética, não autenticação S0.
- Manter busca, atalhos, reset único, indicador de resultados, perfil/loja e telas existentes. Nenhuma chamada de API.

## Regressões propostas

- Node: variações maiúsculas/minúsculas, acentos nos termos e nos registros, normalização Unicode decomposta, espaços múltiplos, ID do atendimento, status e proteção entre lojas/perfis.
- Node DOM: atuação real da busca, estado e foco após limpar.
- Chromium: 320×640, 390×844, 900×780, 1440×900, dois temas, caso/estado, alternância de loja por gestor fictício e zero resultados no escopo não autorizado; não permitir overflow nem erros JS.
- **Certificação condicionada ao GitHub Actions:** preflight, Python, Node, Chromium, `FULL LOCAL ACCEPTANCE: PASS`. Não homologar S0/S1/WhatsApp, permissões produtivas ou leitor de tela humano. Não modificar `main`, nem PR, merge ou deploy.

**Anterior:** [FV-UI-055](./84_FV_UI_055_ACAO_UNICA_LIMPEZA_FILA_2026_10_25.md).

## Certificação nativa — GitHub Actions, 25/10/2026

- Commit de implementação: `edb85ab28f8f5201c2731649fd296d3ea278f352`.
- Manifesto repinado e **commit integralmente testado**: `5a109517288dcc5296d6932b6277cf1d70d13ad6`.
- [GitHub Actions 40253661175](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40253661175): **completed / success** exatamente no SHA de teste.
- Preflight de integridade: **59 arquivos PASS**; Python de segurança: **25/25 PASS**; Node ESM: **366/366 PASS**, **0 falhas**.
- Chromium/Playwright: **PASS**, inclusive `FV-UI-056 busca normalizada e isolamento de loja em 8 cenarios: PASS`.
- Evidência no log: `FULL LOCAL ACCEPTANCE: PASS`.
- Esta homologação atesta a consistência do **frontend demonstrativo sintético**, não conexão produtiva, autenticação real, autorização S0/S1, WhatsApp, IA, banco, leitor de tela humano ou implantação.
- O commit documental final não modifica nenhum arquivo visual testado. A branch `main` permanece intacta; sem merge ou deploy.
