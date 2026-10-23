# FV-UI-036 — Gate nativo do snapshot visual com tema claro/escuro

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** exclusivamente `frontend/`. Validação demonstrativa, **não homologação**.

## Procedência e revisão

- Commit do código, testes e documentação: `2b86418c5674ed762cfe3058a0d0c770b73251ed`.
- Commit do repin de `verify_offline_export.py`: `e847f8bc81ee5186d55935b95fb3578c5d0104d2`.
- `source_head` do manifesto: `2b86418c5674ed762cfe3058a0d0c770b73251ed`, que representa a revisão dos **58 arquivos de conteúdo** anterior à atualização do próprio verificador.
- Foram conferidos por Git blob SHA-1 os **oito arquivos visuais alterados** em relação ao FV-UI-035. O verificador repinado possui blob Git `6e9483b4fd080c0c2676ed7f367f731e9093a2b1`, também comparado byte a byte com o snapshot.
- Amostra: `FV_UI_036_derived_snapshot.zip`, reconstruída localmente a partir de fontes previamente exportadas e do conteúdo FV-UI-036 conferido no GitHub. **Não** foi um checkout autenticado nem um download oficial do novo commit contendo o histórico Git.

## Gate sequencial executado

```bash
python -B tests/verify_offline_export.py \
  --archive FV_UI_036_derived_snapshot.zip \
  --run-native --json-report native_report.json
```

| Etapa | Resultado observado |
|---|---|
| Verificação integral do inventário | **58/58 hashes Git válidos**; verificador igual ao publicado |
| Testes adversariais Python do ZIP | **20/20 PASS**, exit code 0 |
| Node `--test` nativo | **343/343 PASS**, exit code 0 |
| Chromium/Playwright real | **PASS**, exit code 0 |
| `snapshot_verified` / `native_snapshot_pass` | **true / true** |
| `git_checkout_verified` / `full_acceptance` | **false / false** |

O Chromium exerceu as alternâncias Claro/Escuro em **1440×900, 900×780, 390×844 e 320×640**, conferindo `aria-pressed`, mudança efetiva da superfície e dos balões, preservação do caso e ausência de overflow. Foi executado também um contexto com `prefers-color-scheme: dark` e diálogo gerencial nativo aberto, confirmando que o `body` participa do tema.

Uma versão local preliminar apresentava `source_head` temporário e falha de manifesto na suíte completa; essa versão **não foi considerada válida**. Os 58 hashes foram reconstruídos somente após a última alteração visual, o SHA remoto do verificador foi conferido e **todos os gates sequenciais foram repetidos e aprovados**.

## Limites e próximos passos

- Tema selecionado apenas em memória da página; não há persistência em navegador/storage nem preferência de conta.
- Snapshot sintético não equivale a checkout Git autenticado e limpo, teste de tecnologia assistiva humana, auditoria de contraste WCAG exaustiva, aprovação de design, merge ou deploy.
- Nenhum sistema S0/S1, RLS, Supabase, API Meta/WhatsApp, OpenAI, remessa bancária ou efeito comercial foi acionado.
- Próxima prioridade: revisar a densidade de informação, escopo de estilos dos modais e contraste de componentes adicionais com regressões por camadas; continuar os ajustes incrementais sobre este design neutro.

**Implementação:** [FV-UI-036](./64_FV_UI_036_BASE_VISUAL_TEMA_CLARO_ESCURO_2026_10_23.md). **Etapa anterior:** [FV-UI-035](./63_FV_UI_035_GATE_NATIVO_SNAPSHOT_2026_10_23.md).
