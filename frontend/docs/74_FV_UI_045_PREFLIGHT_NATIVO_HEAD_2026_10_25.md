# FV-UI-045 — Preflight nativo e proveniência do HEAD oficial

**Data:** 25/10/2026 · **Repositório autorizado:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch experimental:** `feat/frontend-plataforma-visual` · **Escopo de modificação:** apenas `frontend/`.

## Motivo do incremento

Os incrementos FV-UI-036 a FV-UI-044 tiveram conferência de hashes no GitHub, mas os ensaios Chromium/Node anteriores utilizaram uma cópia local derivada do FV-UI-036. Antes desta execução, foi comparada a cópia preservada `FV_UI_036_derived_snapshot.zip` com a árvore Git oficial do HEAD `95fde1631ab8269e10d2b0ed45e1862bed89a4a0`: **51 dos 59 arquivos eram exatamente iguais** por hash Git blob; **8 divergiam**. Divergentes: `README.md`, `app.mjs`, `styles.css`, `tests/app.dom.test.mjs`, `tests/browser.smoke.py`, `tests/dom-fixture.mjs`, `tests/source-contract.test.mjs` e `tests/verify_offline_export.py`. Um teste executado sem corrigir essas diferenças não pode ser tratado como validação do HEAD oficial.

O executor `tests/run_acceptance.py` já checava revisão e branch antes das suítes, mas os hashes de todos os blobs eram validados só mais tarde, na suíte Node. Isso permitia iniciar uma etapa de segurança e diagnósticos sobre dados potencialmente incompletos.

## Correção efetivamente aplicada

Novo `check_native_blob_manifest(expected_head, revision_ok)`, integrado a `run_acceptance.py` como **etapa bloqueante anterior à regressão Python, Node e Chromium**:

1. Só funciona se a verificação de revisão Git/branch do executor tiver passado.
2. Lê o `MANIFEST = json.loads(...)` de `verify_offline_export.py` usando `ast.parse`, sem executar o verificador nem tratar texto externo como código.
3. Exige `source_branch` correto, `source_head` válido e **ancestral** do `--expected-head`; o manifesto pode referenciar o commit de conteúdo anterior ao repin do próprio verificador.
4. Obtém `git ls-tree -r --long` do HEAD autorizado e confere os **mesmos caminhos, SHA Git e tamanhos** do manifesto, excluindo deste apenas o verificador autopinado.
5. Confere os bytes realmente presentes no diretório local, incluindo o próprio `verify_offline_export.py`, e rejeita arquivo ausente, symlink ou alterado. Arquivos adicionais no inventário Git também causam bloqueio.
6. Em falha, registra `passed=false` em `steps[]` e **não executa** regressões de ZIP, Node ou Chromium. Não declara `full_acceptance=true`.

A lista de testes Node, o roteiro Chromium, os contratos de apresentação e a regra de proibição de operação real não foram alterados.

## Evidências realmente executadas

A partir da cópia derivada do FV-UI-036, os dois arquivos Python alterados foram comparados por **hash Git blob exato** aos blobs publicados no novo repositório após o commit de código FV-UI-045. A regressão `python3 -B -m unittest discover -s tests -p test_offline_export.py` foi executada localmente com esses mesmos bytes: **24/24 PASS**.

Quatro testes novos usam um repositório Git sintético e temporário, com **zero acesso à rede**: aceitação de árvore íntegra, recusa de arquivo local adulterado, recusa de blob extra versionado não incluído no manifesto e recusa de checkout não verificado. Os 20 testes adversariais de ZIP já existentes permaneceram aprovados.

A execução do `run_acceptance.py` sobre a cópia antiga, fornecendo explicitamente o HEAD oficial e `--skip-browser`, foi corretamente recusada: ela não é checkout Git acessível e o preflight negou a execução. **Não há aprovação do gate nativo completo** sobre a branch oficial; nenhum teste de Node/Chromium integral foi atestado aqui.

## Limitações, continuidade e segurança

- A conferência remota de hashes confirma integridade documental, não substitui executar os testes sob o código oficial.
- Preflight usa Git local; exige um checkout limpo da branch e o SHA completo esperado. Não aceita só um ZIP, mesmo que íntegro, como checkout Git.
- A documentação deve identificar o HEAD certificado e o `source_head` efetivamente repinado após publicar este incremento.
- Para concluir validação integrada, executar o `run_acceptance.py --expected-head <SHA de 40 caracteres>` em checkout autenticado com Git, Node, Python e Chromium instalados, inspecionando `steps`, `browser_executed` e `full_acceptance`. A ausência dessas evidências implica pendência, não aprovação.
- Apenas dados de demonstração. Sem alterações de S0/S1, serviços externos, Meta/WhatsApp, OpenAI, Supabase, autenticação, pagamentos, regras comerciais, atribuições, permissões, merge na `main` ou deploy.

**Anterior:** [FV-UI-044](./73_FV_UI_044_FOCO_TECLADO_CONVERSA_2026_10_24.md).
