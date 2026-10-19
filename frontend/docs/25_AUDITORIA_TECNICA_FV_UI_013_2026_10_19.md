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


---

## Continuidade FV-UI-013 — nova execução e proteção por revisão Git (19/10/2026, segunda rodada)

**Contexto e limite:** o checkout privado integral continua inacessível por Git local. Confirmado novamente em container: `git ls-remote https://github.com/prumogrowth/Prumo-Growth---Platform.git HEAD` falhou por resolução DNS. A conexão GitHub autenticada continuou funcionando para leitura/escrita. Node v22.16.0, Python 3.13.5 e Chromium instalado foram observados, **mas nenhuma jornada da aplicação real foi executada nativamente**.

### Incrementos versionados na mesma branch

- [`2f893387`](https://github.com/prumogrowth/Prumo-Growth---Platform/commit/2f893387b3025d5996329302426a24e9f1421b71) e [`7e77608c`](https://github.com/prumogrowth/Prumo-Growth---Platform/commit/7e77608cb99041a5b25c62e46aebb506ad9264ca): acrescentada e corrigida verificação **Node nativa futura** em `source-module-graph.test.mjs`. O teste passa a montar a concatenação real do smoke, remover import/export pelo mesmo padrão Python e compilar o bundle inteiro com `node:vm.Script` para detectar declarações léxicas duplicadas e sintaxe que falharia apenas ao unir módulos. Em **ensaio V8 neste atendimento**, 11 módulos concatenados compilaram sem colisões (98.536 caracteres após transformação). **Isso não é `node --test` nativo.**
- [`132e56ca`](https://github.com/prumogrowth/Prumo-Growth---Platform/commit/132e56cad1e23ca9d79008173ca54adbb367b034) e [`4a05a039`](https://github.com/prumogrowth/Prumo-Growth---Platform/commit/4a05a0397fbf5c08f35749eaed112e26ae56f4a0): runner de aceite exige argumento `--expected-head` (40 caracteres hexadecimais), compara com `git rev-parse HEAD`, exige a branch `feat/frontend-plataforma-visual` e detecta alterações locais em `frontend/visual`. Se a revisão não bate, impede executar tanto Node quanto Chromium e sinaliza falta de prova no JSON. Blob remoto pós-correção: `7c7f21ceb05a7a71b771b6b45ed7673db5629a2d`.

### Ensaios realmente executados sobre o runner, sem aplicação real

Reproduzido localmente um **clone literal do arquivo de runner**, confirmado pelo mesmo SHA Git blob `7c7f21ceb05a7a71b771b6b45ed7673db5629a2d`. Para provar a lógica de orquestração, criou-se um **repositório Git local artificial**, na branch autorizada, com arquivos-sentinela que levam o inventário a passar, 14 testes Node deliberadamente triviais e um script Python que representa o passo do browser **sem abrir Chromium**. Seis cenários de controle foram executados:

| Cenário artificial | Resultado processual | Prova de controle |
| --- | --- | --- |
| SHA/branch corretos, árvore limpa, sentinelas Node/browser com saída zero | exit 0; `full_acceptance=true` | Somente a lógica de orquestração do executor |
| SHA antigo | exit 1; Node/browser não executados | Negação por revisão inválida |
| Arquivo não rastreado sob `frontend/visual` | exit 1; Node/browser não executados | Negação por árvore suja |
| Outra branch com mesmo commit | exit 1; Node/browser não executados | Negação por branch |
| Script Python-sentinela do browser falha | exit 1; Node aprovado no ensaio artificial, browser reprovado | Propagação de falha do passo browser |
| Teste Node-sentinela falha | exit 1; Node reprovado, passo Python-sentinela aprovado | Propagação de falha Node |

**Interpretação indispensável:** o resultado exit 0 do primeiro cenário **não significa Chromium PASS**, porque ele executa propositalmente apenas uma sentinela Python. Não significa O1–O5/G1–G4 PASS, nem comprova testes de acessibilidade, API, segurança ou produção. A matriz de jornadas nativas permanece **pendente**. O objetivo desses seis ensaios é comprovar que o **executor** aceita/rejeita condições de teste de forma coerente, não validar a aplicação.

### Procedimento reprodutível quando o checkout autorizado estiver disponível

1. Confirmar no GitHub o HEAD atual da branch; fornecer esse SHA **exato** ao runner por `--expected-head`.
2. Certificar-se de que `frontend/visual` não contém alterações locais/untracked antes da execução e que a branch está selecionada, sem checkout detached.
3. No checkout integral atualizado, executar `python3 frontend/visual/tests/run_acceptance.py --expected-head SHA_COMPLETO --json-report /tmp/fv-ui-013-evidencia.json`. Definir `CHROMIUM_EXECUTABLE` se necessário.
4. Registrar saídas `node --test` e Chromium verdadeiras, observações por viewport e revisões corretivas; **somente então** reconsiderar o gate FV-UI-013.

**Veredito após continuidade:** o mecanismo de aceite está mais rigoroso e seus cenários de controle foram executados; **o frontend completo ainda não tem aceite Node/Chromium nativo**. Não houve integração, deploy, merge ou alteração fora de `frontend/`. O índice formal **19F permanece em 69/100**.


## FV-UI-013 — Nova rodada de regressão sobre o HEAD `517fc1ab` (19/10/2026)

**Origem de prova:** fontes completas recuperadas via integração autenticada GitHub do commit `517fc1ab0f835ea07daa4fb7f6d2912681e90c5a`. Sem checkout Git integral local: `github.com` permanece indisponível por DNS no container de execução. Os testes a seguir foram **executados em V8 por adaptação dos módulos ESM e asserts Node**, e não em `node --test` ou Chromium.

| Grupo de verificações | Resultado V8 | Escopo |
| --- | ---: | --- |
| Regras/projeções: fixtures, view-model, CF-OP-02, registration, bank | 49/49 | Cinco suítes originais |
| Regras/projeções: postmark, team-operations, team-monitor, team-monitoring, batch-monitor | 61/61 | Cinco suítes originais |
| Interação: app.dom + app.mobile.dom com `dom-fixture.mjs` | 45/45 | DOM sintético, desktop/mobile |
| Contratos estáticos: `source-contract.test.mjs` | 25/25 | Arquivos reais e roteiro Playwright, leitura de texto |
| **Total desta execução** | **180/180 PASS em V8 adaptado** | **Não é aceite nativo** |

**Nota de método:** as importações ESM foram removidas mantendo as declarações de módulos em escopo lexical compartilhado; os métodos de asserção utilizados foram reimplementados no harness V8. Nos testes DOM, o mock original foi instalado antes do aplicativo, reproduzindo os cenários de `app.dom.test.mjs` e `app.mobile.dom.test.mjs`. Isso fornece evidência atual de regressão sintética, mas não garante paridade com `node:test`, navegador, CSS, acessibilidade ou isolamento do servidor. Nenhum envio Meta, remessa bancária, acesso real D3/D4 ou integração ocorreu.

**Roteiro Chromium examinado:** ordem de 11 módulos consistente; em larguras de até 1040 px o bootstrap oculta o painel de detalhes e o roteiro o abre com `#detail-toggle`; os elementos `#internal-note-form`, `#note-text` e `#request-completion` são criados dinamicamente pelo `app.mjs`. Esses pressupostos foram conferidos em fonte e simulação, **não em navegador real**.

**Veredito atualizado:** regressão sintética integral de **180/180 confirmada nesta rodada** para o HEAD declarado. FV-UI-013 **continua sem homologação nativa Node/Chromium da aplicação completa**. Próximo gate é a execução integral do runner em checkout privado autenticado, na branch e SHA conferidos. Manter 19F em **69/100**; sem merge/deploy/alteração externa ao frontend.
