# FV-UI-030 — Camadas de testes para permitir redesign sem retrabalho desnecessário

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** apenas `frontend/`, fixtures e testes sintéticos. **Não homologado nem integrado**.

## Decisão de sequência

O Frontend ainda poderá mudar de identidade visual, cores, tipografia, componentes e disposição de painéis. Para isso, **não é necessário jogar fora todos os testes**: regras operacionais e transições de estado devem sobreviver a modificações puramente estéticas. Porém, **mudanças de estrutura do DOM, semântica, botões, tabs e modais podem exigir adaptar alguns testes de interação**; testes de layout, foco e reflow sempre exigem nova execução depois de um redesign significativo.

**Ordem recomendada:** (1) consolidar regras e comportamentos essenciais; (2) definir design e fluxos visuais; (3) implementar o redesign; (4) reexecutar todos os testes de interação, DOM, CSS, acessibilidade, viewport e Chromium; (5) somente depois considerar gate de checkout autenticado e integrações S0/S1 ratificadas.

## Implementação

- `frontend/visual/tests/validation-layers.json`: classifica **as 27 suítes Node** por objetivo principal, além do roteiro Chromium. A classificação é **operacional**, não uma afirmação de independência perfeita entre camadas.
- `frontend/visual/tests/run_validation_layers.mjs`: executor **diagnóstico** por camada; recusa nome desconhecido, suíte não classificada ou duplicada, evita shells e mantém mensagens claras de que execução isolada não equivale a homologação.
- `frontend/visual/tests/validation-layers.test.mjs`: verifica exaustividade do inventário, ausência de suítes duplicadas, que os testes principais de interação estejam na camada certa e que o executor recuse uma camada inválida.
- `frontend/visual/tests/run_acceptance.py`: registra a nova suíte e os dois artefatos do executor como parte obrigatória do inventário do checkout completo.
- `frontend/visual/tests/acceptance-matrix.json`: associa o teste de inventário à rastreabilidade **FV-22-16**, mantendo 16 critérios sem promoção automática de cobertura.

### Quais testes executar

| Camada | Suítes | Uso |
|---|---:|---|
| `domain` | 19 Node | Regras e projeções fictícias, estados operacionais, limites de autorização apresentados no protótipo |
| `interaction` | 3 Node | Botões, diálogos, contexto, foco, mudanças de perfil e fluxo de atendimento em DOM simulado |
| `source` | 5 Node | Contrato estrutural, CSS, módulos, matriz de aceitação, hashes e inventário |
| `browser` | 1 roteiro Playwright | Chromium real com interações, viewport, foco, estilo e reflow; repetir quando houver mudança visual significativa |

**Comandos no checkout ou snapshot com arquivos completos:**

```bash
node frontend/visual/tests/run_validation_layers.mjs domain
node frontend/visual/tests/run_validation_layers.mjs interaction
node frontend/visual/tests/run_validation_layers.mjs source
node frontend/visual/tests/run_validation_layers.mjs browser
```

O executor de camada não valida SHA, branch Git, árvore limpa, permissões externas, envio, persistência ou serviço. **Para aceite local completo**, segue obrigatório o runner anterior: `python3 frontend/visual/tests/run_acceptance.py --expected-head <SHA_DE_40_CARACTERES>` em checkout Git autenticado, além das avaliações manuais que permaneçam necessárias.

## Limites e evidência

- A conferência **estrutural** do inventário GitHub na elaboração deste incremento mostrou 27 suítes, cada uma classificada uma única vez (19 + 3 + 5).
- **Não declarar aprovação nativa de 27 suítes, Chromium ou CI nesta rodada** sem executar a revisão atual de ponta a ponta. Os resultados anteriores (FV-UI-029: 323 Node, 20 Python e Chromium em cópia local derivada) referem-se ao snapshot anterior.
- O protótipo continua com fixtures sintéticas, sem acesso novo a Meta, OpenAI, Supabase, RLS, S0/S1, remessas bancárias, integração, merge ou deploy. Reclassificação de 19F e homologação FV-22 permanecem pendentes.

**Próxima frente sugerida:** definição do design visual alvo da central de atendimento, com variantes desktop e mobile, hierarquia de ações e estados vazios, antes de investir em ajustes finos do layout provisório. Quando aprovado o novo visual, reexecutar as quatro camadas integralmente.
