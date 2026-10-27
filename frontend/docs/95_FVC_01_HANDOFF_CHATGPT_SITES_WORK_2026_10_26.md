# FVC-01 — Pacote candidato para ChatGPT Work → ChatGPT Sites

> **FV-UX-01 — DIRETRIZ VISUAL POSTERIOR (26/10/2026):** o responsável avaliou a prévia interativa e solicitou **menos poluição, hierarquia centrada nas conversas, paleta verdadeiramente neutra, áudio, emojis e visões distintas de Consultor/Gestor**. **Não utilizar este handoff antigo para publicar nova rodada do Sites sem antes executar a lapidação UX**, preservando a única base do frontend. Leia [96_FV_UX_01_COMUNICACAO_LIMPEZA_AUDIO_EMOJI_2026_10_26.md](./96_FV_UX_01_COMUNICACAO_LIMPEZA_AUDIO_EMOJI_2026_10_26.md). A atual prévia existente não deve ser apresentada como a versão refinada. O material deste FVC-01 permanece válido como inventário técnico, mas **a recomendação temporal de publicar agora foi superada**.


**26/10/2026 · Frente visual de Prumo · pronto para alinhamento de escopo com o responsável.**  
**Este documento NÃO autoriza publicação; é um roteiro para preparar prévia privada navegável.**

## 1. Objetivo de entrega

A partir do frontend real e existente, preparar **prévia interativa temporária** no **ChatGPT Sites** para avaliação conjunta por participantes autorizados no celular e computador. Não reconstruir por mockup ou gerar interface diferente. Manter a navegação funcional, os cenários locais e a responsividade da branch visual. A aparência e usabilidade **ainda dependem de revisão humana**; a prévia será o meio de coletá-la, não um lançamento comercial.

**Identidade:** Prumo é identificação técnica provisória da plataforma/equipe. **LiberaCred é o produto financeiro da instituição financeira**, não o nome confirmado da plataforma.

## 2. Fonte única de implementação, não usar `main`

- Repositório privado: `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`.
- Branch de trabalho autorizada: `feat/frontend-plataforma-visual`.
- Runtime: **`frontend/visual/`**, entrada `frontend/visual/index.html`, CSS `styles.css` e módulos ESM `*.mjs`.
- Projeto **sem compilador obrigatório** e sem dependências npm para o runtime visual. Os módulos usam imports relativos; servir via HTTPS/HTTP, não via `file://`. Se o ChatGPT Sites exigir adaptação da estrutura, produzir uma **cópia para prévia** rastreável, sem alterar a fonte autoral de maneira implícita.
- Apenas **dados sintéticos** em `fixtures.mjs`. Não adicionar clientes reais, credenciais, Supabase, Meta/WhatsApp, OpenAI operacional nem instituição financeira.
- O owner da S0 é o **Codex**. Não editar `frontend/s1/`, autenticação, APIs, migrações, políticas, grants produtivos, `main` ou branches de terceiros para publicar a prévia.

## 3. Evidências técnicas já aprovadas

| Gate/artefato | Origem verificável | Estado |
| --- | --- | --- |
| FVA-01 — isolamento entre perfis/lojas/casos | [run 40300012152](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40300012152) | PASS histórico |
| FVA-02 — erros, confirmação, solicitações locais | [run 40405009482](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40405009482) | **PASS**, 379 Node, 25 Python, Chromium |
| FVB-01 — matriz de 9 capturas | [run 40406051248](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40406051248) | **PASS**, artefato capturas [12691307610](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40406051248/artifacts/12691307610) |
| ZIP visual para navegador, sem S0 | [artefato 12691342751](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40406051248/artifacts/12691342751) | Gerado; **não publicado** |
| Exportação rápida com pin da última base visual certificada | [run 40406216028](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40406216028) | PASS |

O fato de existir uma base técnica testada **não comprova** autenticação real, acessibilidade assistiva plena, UX aprovada em celulares físicos, integração produtiva ou compatibilidade garantida com ChatGPT Sites.

## 4. Documentação a consumir primeiro

1. `frontend/docs/00_COMECE_POR_AQUI_DECISOES_VIGENTES_2026_10_21.md` — decisões vigentes da frente.
2. `frontend/docs/38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md` — papéis, 16 critérios FV-22 e limitações.
3. `frontend/docs/88_FV_UI_059_FECHAMENTO_CRITERIOS_FV22_E_PROXIMOS_MARCOS_2026_10_26.md` — marcos FVA/FVB/FVC.
4. `frontend/docs/89_FVA_01_REGRESSOES_CRUZADAS_JORNADAS_2026_10_26.md` — testes de isolamento.
5. `frontend/docs/92_FVA_02_ESTADOS_ERRO_E_ACOES_PENDENTES_2026_10_26.md` — correção e certificação FVA-02.
6. `frontend/docs/94_FVB_01_MATRIZ_CAPTURAS_PARA_REVISAO_2026_10_26.md` — matriz visual e arquivos.
7. `frontend/docs/91_FVB_SITES_02_CHATGPT_SITES_DESTINO_VIGENTE_2026_10_26.md` — destino de publicação escolhido; substitui fluxo antigo Google Sites/Cloudflare.

## 5. Critérios mínimos da primeira prévia privada do Sites

- Abrir no desktop e no celular com todos os assets locais carregados; nenhum 404 de JS/CSS nem erro de runtime.
- Manter layout e interações desktop/mobile (320px, 390px e ≥900px) e claro/escuro sem scroll horizontal indevido.
- Navegar em lista, conversa, detalhes, abas Resumo/Histórico/Notas/Extração/Banco/Novo contato quando elegíveis; equipe para Gestor; busca e filtros; modais; solicitação fictícia sem envio.
- Demonstrar troca de perfil `Consultor/Gestor`, loja e acesso excepcional por caso sem confundir seletor local com autenticação.
- Diferenciar solicitações `NÃO ENVIADAS`, `API_ACCEPTED`, `UNCERTAIN` e prova de envio; não prometer mensagem real, conclusão F03, venda ou operação bancária.
- Exibir aviso permanente de **demonstração com dados fictícios** e nome da plataforma provisório.
- Mostrar **prévia privada primeiro**, e relatar adaptações, limitações e custo/permissões do ChatGPT Sites antes de qualquer compartilhamento.
- Confirmar controles de visibilidade no Sites; não presumir que uma URL direta seja restrita por padrão. Compartilhar somente após aprovação do responsável e com dados sempre fictícios.

## 6. Pedido sugerido ao ChatGPT Work (a ajustar em conversa com responsável)

> Trabalhe com o projeto **existente**, repositório privado `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA`, branch `feat/frontend-plataforma-visual`, pasta `frontend/visual/`. Sua tarefa é preparar, no **ChatGPT Sites**, uma **prévia interativa privada** da interface sintética atual para revisão visual e de navegação por uma equipe. Antes de alterar código, leia os contratos e as evidências FVA/FVB indexados em `frontend/docs/95_FVC_01_HANDOFF_CHATGPT_SITES_WORK_2026_10_26.md`, verifique sua conectividade com o repositório e compatibilidade do Sites com HTML/CSS e módulos ESM. **Preserve a interface e o comportamento existente; não recrie do zero.** Se for preciso adaptar, faça em uma cópia/branch de preparação identificada, sem afetar `main`, S0/S1 ou o frontend de origem. Use **apenas fixtures sintéticas**; nenhum token, PII, WhatsApp, Meta, S0, OpenAI produtivo ou instituição financeira. Mostre uma **prévia privada navegável**, em desktop e celular, com notas sobre o que precisou ser ajustado. **Não publique, não libere link a terceiros nem altere controles de acesso sem minha aprovação explícita**. Após minha revisão, poderemos decidir quem terá acesso e coletar sugestões de UX.

## 7. Estado e responsabilidade

**FVA: concluída para validação sintética. FVB: evidências automáticas prontas; revisão visual humana pendente. FVC: handoff documental candidato pronto para alinhamento com o responsável; implantação no ChatGPT Sites ainda não iniciada.**

A entrega ao Work será uma **etapa assistida**, iniciada pelo responsável após acertarmos escopo e permissões. Não existe deploy automático por este commit. A frente S0 mantém autonomia e revisão final de integração futura.
