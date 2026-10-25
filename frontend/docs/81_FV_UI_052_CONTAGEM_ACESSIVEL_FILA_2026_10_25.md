# FV-UI-052 — Contagem de resultados acessível, sem anúncios duplicados

**Data:** 25/10/2026 · **Repositório:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch exclusiva:** `feat/frontend-plataforma-visual`.

## Estado anterior e motivação

FV-UI-049 tornou o contador visual da fila proporcional aos filtros; o estado vazio usa `role=status` e `aria-live=polite`. O contador `#list-count`, porém, era apenas texto visual: não anunciava mudanças em filtragem para tecnologias assistivas. Tornar tanto contador quanto estado vazio simultaneamente vivos criaria anúncios redundantes de zero resultados.

O FV-UI-051 foi certificado pelo [GitHub Actions 40196488010](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40196488010), SHA `86ca0c44e4d9b5b10884cadc5b481da5026e4234`, com **357/357 Node, 25/25 Python, Chromium PASS**. Um commit documental `92f3e63111e062d911fba2bb276dd46c88a51e84` preservou o código visual.

## Alteração limitada ao frontend

- O contador `#list-count` tem `role=status`, `aria-live=polite` e `aria-atomic=true`; o texto visível e os totais comerciais não mudam.
- Durante `renderList()`, `aria-live` passa a `off` se a seleção possui zero resultados; a região de estado vazio já usa `role=status` para anunciar o motivo. Com resultados, `aria-live` volta a `polite`.
- O comportamento da busca, filtros, abas ativa/histórico, perfil e concessionária é preservado; nenhuma intervenção nos dados ou autorização.
- O teste Node contrata os atributos e o controle por quantidade; o Chromium direcionado verifica **320×640, 390×844, 900×780, 1440×900 × claro/escuro** em busca com e sem resultados, não duplicação da região de anúncio, restauração de foco, perfil e concessionária, ausência de overflow e erros de execução.

## Estratégia e limites

O workflow atual da **própria frente visual** continuará validando Git, Python, Node e Chromium. Não é alterado. A [Issue #3](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/issues/3) trata de auditoria de otimização da frente S1; não autoriza alterações e **não é implementada** nesta etapa. A frente visual permanece independente, sem branch de integração, PR, merge na `main` ou deploy.

**Critério de aceite:** confirmar `FULL LOCAL ACCEPTANCE: PASS` nos logs do GitHub Actions no SHA repinado. Esta mudança não substitui testes humanos com leitor de tela, nem habilita integração real, WhatsApp, banco, S0/S1, Supabase, IA, pagamentos ou produção.

**Etapa anterior:** [FV-UI-051](./80_FV_UI_051_ORIENTACOES_TRES_PAINEIS_2026_10_25.md).


## Certificação e auditoria remota

- Commit de conteúdo (interface, contrato, roteiro, documentação): `9d85f939333cdc99ab9f61f147782148563637b9`.
- Manifesto repinado: `9027e8124c5084973125b571bdbce7f5c7cfdb3d`, com `source_head=9d85f939333cdc99ab9f61f147782148563637b9`.
- [GitHub Actions run 40198989629](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40198989629) executado no SHA do manifesto: **completed / success**.
- Log técnico: `Preflight nativo PASS: 59 arquivos`, Python **25/25 PASS**, Node **358/358 PASS** e **0 falhas**, `Chromium Playwright smoke` PASS, incluindo `FV-UI-052 contador de resultados e estado vazio acessiveis em 8 cenarios: PASS`. O executor registrou `FULL LOCAL ACCEPTANCE: PASS`.
- Arquivo de diagnóstico JSON disponível como artifact do run, com retenção de um dia. A validação representa o checkout oficial do protótipo com dados fictícios, não testes humanos assistivos, integrações externas ou produção.
- Auditoria de integridade pré-execução: **58/58 blobs Git pinados**, tamanho e SHA conferidos, zero divergências. Comparação com o FV-UI-051: dois commits de conteúdo/manifesto e **8 arquivos alterados**, todos em `frontend/`.
- O workflow da frente visual permaneceu inalterado; **nenhum workflow da frente S1 foi editado**, nenhuma otimização da Issue #3 foi aplicada, e não houve PR de integração, merge na `main` ou deploy.
