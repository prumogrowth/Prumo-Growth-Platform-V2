# FVA-CI-03 — Certificação estável do navegador obrigatório

**26/10/2026 · Branch `feat/frontend-plataforma-visual` · somente CI e documentação.**

## Diagnóstico baseado nos logs nativos

A execução [40357063810](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40357063810) foi **CANCELADA** pelo tempo máximo do job: `16:13:44–16:29:05 UTC` (~15m). A instalação de dependências do comando `python -m playwright install --with-deps chromium` foi de aproximadamente **16:13:57 a 16:27:13 UTC** (~13m), dominando a execução. Depois, o Node **379/379 PASS** foi finalizado, e o Chromium começou às 16:27:48, interrompido pelo teto externo. O cancelamento não prova uma falha visual nem permite declarar aceite integral.

Na execução anterior [40356069436](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40356069436), Python **25/25** e Node **379/379** passaram, mas o smoke ultrapassou o limite interno anterior de 180s. O script `run_acceptance.py` agora dispõe de 300s para Chromium. Dois problemas independentes de orçamento/instalação estavam impedindo a certificação nativa.

## Reparo fail-closed de pipeline

Alteração somente em `.github/workflows/frontend-visual-validation.yml`:

1. Aumentar o limite máximo do **job GitHub** de **15 para 25 minutos**, sem reduzir ou remover suítes.
2. Instalar o executável Chromium com `python -m playwright install chromium`, evitando a instalação de dependências pesadas em todo run quando já presentes no runner.
3. **Abrir o Chromium de verdade** e verificar que um documento HTML sintético carrega. Se falhar, instalar dependências com `python -m playwright install-deps chromium` e **exigir nova abertura real**. Uma falha em qualquer etapa interrompe o job.
4. Manter obrigatórios: checkout Git com hash, manifesto 59 arquivos, 25 testes Python adversariais, 379 testes Node, smoke Chromium completo, `FULL LOCAL ACCEPTANCE: PASS`, sem `--skip-browser`; artefatos disponibilizados somente após aprovação.

A correção não altera `frontend/visual/`, não exige repin de seus hashes, não altera regras S0, nem publica Site. O workflow só reage a paths autorizados da branch de visual.

## Estado de aceite

**PENDENTE** de um novo run `completed/success` com evidências explícitas de `FULL LOCAL ACCEPTANCE: PASS` e 379/379. Após o run, anexar evidência e link e avançar para **FVB — revisão visual consolidada**, sem solicitar ao usuário feedback parcelado. ChatGPT Sites / Work somente após fechamento visual e alinhamento com responsável.

## Validação do reparo — PASS

GitHub Actions [40405009482](https://github.com/0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA/actions/runs/40405009482) `completed/success` para `a14c46257c0d36a6a944af57e36635e1e75357f1`: navegador real abriu antes da suíte, inventário 59 arquivos PASS, 25 Python PASS, 379 Node PASS, Chromium smoke PASS, `FULL LOCAL ACCEPTANCE: PASS`. A captura de ZIP de demonstração também passou (artefato `12690672314`). O run foi concluído em menos de 4 minutos, sem instalação apt extra. Não é homologação S0/Meta/Banco.
