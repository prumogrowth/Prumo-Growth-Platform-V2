# FV-UI-013 — Auditoria funcional: negar permissões malformadas (20/10/2026)

## Priorização

Por orientação do responsável, **priorizar funcionamento, autorização, transições e invariantes de domínio antes do acabamento estético**. O aspecto atual foi considerado excessivamente textual e visualmente provisório. Essa observação entra para a etapa de design, sem antecipar alterações cosméticas nesta rodada. Legibilidade mínima e acessibilidade são requisitos funcionais, mas **não constituem aprovação de identidade visual**.

## Falha reproduzida e escopo

Na projeção fictícia CF-OP-02, o browser usava `.includes()` diretamente em `allowedActionsProjection` e `eligibleTemplatesProjection`. Strings também possuem o método `.includes()`. Assim, uma projeção recebida em formato errado, como `allowedActionsProjection: "not_free_text"`, fazia `mayMockFreeText()` devolver **true**, apesar de não ser uma lista de autorizações; e uma string `"not_single_template,request_chain"` com catálogo textual permitia as duas ações de recontato. O ensaio foi executado com os arquivos reais do commit `27f53c61bfc9b86842f3a032a885a341082d394f` e o defeito reproduzido em V8.

É uma falha de **interpretação de dados do protótipo**, não uma falha comprovada de autenticação real, já que a UI não implementa autenticação/RLS e a autorização verdadeira deverá ocorrer em S0.

## Correção aplicada e testes

- `cf-op-02.mjs`: helpers `hasProjectedAction()` e `hasEligibleTemplateVersion()` só aceitam `Array.isArray(...)` e negam strings, objetos com `includes` forjado, `null`, booleanos e outros valores malformados.
- `app.mjs`: a conclusão humana e a seleção visual de templates usam os mesmos helpers tipados; nenhuma etapa comercial, regra bancária, concessão, status ou dado foi alterado.
- `tests/cf-op-02.test.mjs`: duas regressões novas com casos negativos e positivos, garantindo que ações válidas continuem operáveis e projeções inválidas sejam negadas.
- `tests/source-contract.test.mjs`: guarda estática adicional exige a utilização dos helpers tipados nos caminhos de conclusão e de escolha de template.

### Execução nativa sobre fontes comprovadas

O ZIP do commit `50cc951e52c5ac5ca125e93416b2cad45f416ee9` foi usado para recuperar a base. As sete fontes alteradas desde esse ZIP (`app.mjs`, `cf-op-02.mjs`, `index.html`, `styles.css`, `browser.smoke.py`, `cf-op-02.test.mjs` e `source-contract.test.mjs`) foram reconstruídas em cópia local e tiveram **cada Git blob SHA-1 confrontado com o correspondente publicado na branch**. Todos os **7/7 hashes coincidiram**. Os outros 24 arquivos da cópia de execução vieram diretamente do ZIP de origem, antes verificado por 31/31 hashes no commit de origem. O script posterior `tests/verify_offline_export.py` não compõe a cópia executada; não é dependência do app ou das suítes.

- **Node.js v22.16.0 nativo** — `node --test --test-reporter=tap tests/*.test.mjs`: **193/193 PASS, 0 FAIL, 0 SKIP**.
- **Chromium real + Playwright** — `python tests/browser.smoke.py` com `CHROMIUM_EXECUTABLE=/usr/bin/chromium`: **PASS** em 1440×900, 900×780, 390×844, 320×640 e nos cenários O5, templates, histórico, gestão e acesso suspenso.
- **Mutação negativa** — um desvio artificial que fazia `hasProjectedAction()` voltar a aceitar strings causou **1 falha esperada** especificamente na nova regressão de permissões (16/17 restantes da suíte CF-OP-02 passaram). A fonte foi restaurada e sua SHA conferida antes do teste integral final.

### Limitações e próximos gates

O snapshot é composto por bytes compatíveis com os blobs Git testados, **não um checkout Git autenticado**. O runner formal `run_acceptance.py` ainda exigirá HEAD, branch autorizada e árvore de trabalho íntegra. Esses testes **não** provam S0, autenticação, permissões RLS Supabase, Meta, integração bancária, persistência, remessa ou homologação de produção.

**Próxima prioridade funcional:** definir/validar contrato S0→frontend com projeções tipadas de identidade e escopo operador/equipe/loja, disponibilidade, janela Meta, ações autorizadas, status comerciais canônicos, eventos bancários e vínculos de recontato, com negação por padrão e sem execução real até autorização específica.

**Situação:** FV-UI-013 com evidência funcional nativa positiva, **NÃO HOMOLOGADA** formalmente; 19F preservado em **69/100**. Alterações restritas a `frontend/`; sem merge, deploy ou acesso a produção.
