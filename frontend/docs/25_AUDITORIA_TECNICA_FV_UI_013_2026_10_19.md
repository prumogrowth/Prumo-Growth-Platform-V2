# FV-UI-013 — Auditoria técnica de validação nativa e integridade do aceite | 19/10/2026

**Escopo:** somente `frontend/` na branch `feat/frontend-plataforma-visual`. Nenhum merge, deploy, integração, banco, backend, API externa ou dado real. Progresso auditado 19F mantido em **69/100**.

## Revisão efetivamente examinada

- Base lida no GitHub privado: `ac575520be5b4e7d03c421aae49f0fa7fdf612c3` (commit de correção de seleção estável FV-02).
- Correção introduzida: `ffb47918bb3f6d425e4a5b31026ec958184aeb78`, exclusivamente em `frontend/visual/tests/run_acceptance.py`.
- Issue de divergência interfrentes G2: [#9](https://github.com/prumogrowth/Prumo-Growth---Platform/issues/9), permanece aberta. Não reinterpretar gestor por loja.
- Os contratos FV-01/FV-02/CF-OP-02, auditorias anteriores G2/G3/G4 e FV-GATE-01 foram tratados como limites: a UI simula projeções, enquanto S0 controla a autoridade real.

## Evidências executadas nesta etapa

| Verificação | Resultado | Natureza da evidência |
| --- | --- | --- |
| Consulta autenticada de branch, árvore, arquivos e commits | Confirmada; branch no commit acima antes da correção | GitHub remoto real |
| Inventário `frontend/visual/` | 11 módulos `.mjs` do bootstrap, `index.html`, `styles.css`, 14 testes `*.test.mjs`, `dom-fixture.mjs` e scripts Python presentes | Leitura remota de arquivos; **não é execução de teste** |
| Ordem das dependências locais e paridade com sequência de `browser.smoke.py` | Consistentes para os 11 módulos | Inspeção dos arquivos lidos |
| Sintaxe dos 11 módulos | Aceita pelo V8 após retirar declarações ESM de import/export no ensaio; **não** equivale a `node --test` ou importação ESM nativa | Ensaio estático/sintético |
| `index.html`: identificadores | 58 IDs, sem duplicação; um CSS e um script de entrada | Inspeção estática |
| Seletores `#id` do smoke Chromium | 84 referências identificadas; três IDs não literais no HTML (`note-text`, `internal-note-form`, `request-completion`) foram localizados como elementos **gerados dinamicamente** em `app.mjs`; não se constatou divergência por inexistência de ID | Inspeção estática, **sem navegador** |
| Quatro dimensões Chromium (1440×900, 900×780, 390×844, 320×640) | Declaradas no roteiro; comportamento em viewport **não verificado** | Inspeção do roteiro apenas |
| Python `py_compile` do runner **corrigido** | PASS; blob local reproduz o SHA GitHub `3ad511c7d70212bd50f24a6e01a1b078b35db0e2` | Python local, apenas runner |
| Ensaio negativo do runner com checkout vazio | Exit 1; 29 arquivos obrigatórios ausentes; Node/Chromium não executados; `full_acceptance=false` | **Execução real do runner**, checkout propositalmente incompleto |
| Ensaio negativo com apenas um teste Node artificial `fixtures.test.mjs` aprovado (1/1) | Node isolado PASS 1/1, mas runner exit 1, 28 arquivos ausentes, Node/Chromium integrados bloqueados, `full_acceptance=false` | Teste real do **bloqueio de suíte truncada**, não regressão da aplicação |

**Ambiente local observado:** Node.js v22.16.0, Python 3.13.5, Chromium em `/usr/bin/chromium` e pacote Python Playwright importável. O comando de acesso direto ao GitHub via `git ls-remote` falhou por resolução de host; a integração autenticada GitHub permitiu leitura e commits, mas **não disponibilizou um checkout integral executável ao processo Node/Chromium local**.

## Falha encontrada e correção aplicada

O runner original descobria `*.test.mjs` e considerava suficiente existir pelo menos um arquivo de teste. Um checkout truncado contendo somente um teste aprovado poderia seguir até `full_acceptance=true`, caso o smoke também executasse.

O runner agora exige **14 testes Node esperados**, **13 arquivos base** (HTML/CSS e 11 módulos), `browser.smoke.py` e `dom-fixture.mjs`. Registra no JSON a etapa `FV-UI-013 checkout inventory`, a lista de faltantes e a contagem esperada. Em checkout incompleto, **não executa** a suíte Node nem o Chromium e retorna resultado geral negativo. `--skip-browser` continua somente diagnóstico, sem aceite integral.

Esta correção é **implementada e versionada**; o comportamento negativo foi reproduzido com o runner local idêntico ao blob remoto. O caminho positivo de aceite completo **não foi exercitado**.

## Matriz de regressão O1–O5 e G1–G4

| Jornada | Evidência atual | Resultado da repetição nativa |
| --- | --- | --- |
| O1/O2 — central, conversa, histórico, notas e conclusão | Arquivos e seletores analisados; cenário presente em `browser.smoke.py` e testes `app*.test.mjs` | **Pendente** |
| O3 — cadastro/extração e D3 | Módulo, teste dedicado e verificações de seleção/visibilidade no roteiro | **Pendente** |
| O4 — remessa/retorno bancário D4 fictícios | `bank-view.mjs`, teste e verificações no roteiro | **Pendente** |
| O5 — novo ciclo após banco/venda | `postmark-view.mjs`, teste e seletores A-114/A-116 no roteiro | **Pendente** |
| G1 — escopo operador/gestor, filtros | Projeções e controles de perfil no roteiro | **Pendente** |
| G2 — equipe de operadores e pausa global apenas solicitada | `team-operations.mjs`, teste e roteiro; conflito #9 respeitado | **Pendente** |
| G3 — monitoramento próprio, sem D3/D4 | `team-monitor.mjs`, `team-monitoring.mjs` e testes respectivos | **Pendente** |
| G4 — lotes próprios e qualidade fictícia | `batch-monitor.mjs` e teste dedicado | **Pendente** |

Os **180/180** testes G2–G4 citados na auditoria FV-UI-012 constituem evidência **histórica e sintética**. Não foram repetidos nesta etapa como `node --test` nativo nem como browser real. Não atribuir PASS nativo às jornadas com base na presença do roteiro.

## Pendências / gate

1. Obter **checkout privado integral** e atualizado da branch em ambiente com Node/Chromium autorizado, mantendo a revisão identificada. A impossibilidade atual de resolver `github.com` por Git local é bloqueio de ambiente, não falha de produto.
2. Executar, a partir da raiz do repositório: `python3 frontend/visual/tests/run_acceptance.py --json-report frontend/visual/tests/fv-ui-013-local-report.json` (relatório local não versionar automaticamente), com `CHROMIUM_EXECUTABLE=/usr/bin/chromium` quando necessário.
3. Registrar número de testes executados, stdout/stderr, status de cada etapa, reprodução das jornadas em Chromium e falhas por viewport; corrigir eventuais erros verificáveis **apenas** em `frontend/` na branch autorizada, reexecutar e atualizar esta auditoria.
4. Complementar com navegação real por teclado, acessibilidade e performance em ambiente adequado. Ensaios locais não homologam autorização S0, tenant isolation real, dados D3/D4, Meta, OpenAI, banco, entrega SENT nem segurança de produção.
5. Só preparar avaliação visual do responsável após gates funcionais e técnicos documentados; **não** usar esta auditoria como liberação de UX final.

**Veredito da FV-UI-013 nesta data: PARCIAL / NÃO HOMOLOGADA.** Corrigida uma falha real do mecanismo de aceite e validado o comportamento de bloqueio; ausência de checkout completo impede comprovar a execução nativa da aplicação.
