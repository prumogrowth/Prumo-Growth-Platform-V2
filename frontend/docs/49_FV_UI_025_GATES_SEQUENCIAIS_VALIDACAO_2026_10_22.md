# FV-UI-025 — Gates sequenciais de validação nativa (fail-closed)

**Data:** 22/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** somente `frontend/`; sem deploy, merge ou integração externa.

## Descoberta na auditoria

O [FV-UI-024](./48_FV_UI_024_TESTES_ADVERSARIAIS_ZIP_E_GATE_NATIVO_2026_10_22.md) exigia a execução de testes adversariais Python, mas o verificador de ZIP ainda disparava Node e Chromium **mesmo quando o gate de segurança falhava**. O runner de checkout tinha comportamento equivalente: rejeitava o aceite final, porém continuava executando etapas posteriores. Isso desperdiçava execução e ampliava a superfície de processamento de código em ambiente com pré-requisitos comprometidos.

## Correção aplicada

| Arquivo | Correção de execução |
|---|---|
| `frontend/visual/tests/verify_offline_export.py` | Só executa **Node após Python adversarial aprovado**; só executa **Chromium após Node aprovado**. Falha/indisponibilidade de segurança ou Node deixa os passos seguintes com `executed:false`, `passed:false` e motivo explícito. `native_snapshot_pass` exige os três gates executados e aprovados. Teste Python utiliza `-B` para não escrever `__pycache__` no snapshot verificado. |
| `frontend/visual/tests/run_acceptance.py` | Aplica a mesma ordem em checkout Git autorizado: revisão/branch/inventário → testes Python → Node → Chromium. O resultado final `full_acceptance` continua falso diante de qualquer bloqueio ou `--skip-browser`. Invoca testes Python com `-B` para não sujar o checkout verificado. |
| `frontend/visual/tests/test_offline_export.py` | **20 testes Python** no total, incluindo cinco regressões de fluxo: falha no gate de segurança, impossibilidade de executá-lo, falha de Node, indisponibilidade de Node e percurso aprovado (com `execute()` simulado). Mantém os casos adversariais de ZIP anteriores. Nenhum teste dessa suíte conecta S0/S1 ou Meta. |
| `frontend/visual/tests/source-contract.test.mjs` | Acrescenta verificação de contrato estático: condicionais de bloqueio, uso de `-B`, presença dos testes de fluxo e impedimento de Chromium sem Node. |

## Evidências desta rodada

- **Verificação V8 de fonte**, executada sobre as versões recuperadas da branch GitHub: novo teste estático FV-UI-025 **1/1 aprovado**, e os **20 nomes dos cenários Python** identificados no arquivo. Isso **não é execução nativa do Python ou dos testes Node**.
- **Não executados nesta rodada:** os 20 testes Python, as 26 suítes Node, Playwright/Chromium, navegação com tecnologia assistiva, S0/S1, Supabase/GoTrue/RLS, Meta/WhatsApp, OpenAI/F03 ou banco. O ambiente não dispõe de checkout/ZIP do código privado, apenas acesso aos arquivos através do conector GitHub.
- Inventário do Frontend e hashes Git pinados no `verify_offline_export.py` **após as alterações** (verificação de consistência separada). `source_head` identifica a revisão de onde os blobs foram coletados, não substitui prova de checkout Git em `run_acceptance.py`.
- Os **16 critérios FV-22** continuam rastreados como `prototype_only`/`partial`/`external_blocked`. Sem alteração da pontuação histórica 19F ou homologação FV-UI-013.

## Regras de aceite inalteradas

1. Diagnóstico de ZIP da branch: validar hashes e verificador byte a byte; executar `test_offline_export.py`, `node --test` e smoke Chromium **nessa ordem**; qualquer falha bloqueia os passos seguintes.
2. Homologação local de checkout Git: confirmar branch, HEAD completo, árvore de trabalho limpa e inventário; executar os mesmos gates, além das verificações funcionais e visuais reais.
3. Qualquer resultado `passed` de mock ou verificador de fonte não comprova autorização S0/S1, eventos Meta, persistência, envio a banco ou conformidade de produção.

**Referência anterior:** [FV-UI-023](./47_FV_UI_023_MANIFESTO_ZIP_OFFLINE_NATIVO_2026_10_22.md). **Próxima necessidade:** obter ZIP privado legítimo ou checkout Git autorizado para finalmente executar a bateria nativa e registrar logs completos, sem alterar outras frentes.
