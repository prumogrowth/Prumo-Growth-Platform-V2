# FV-UI-013 — evidência de execução nativa em ZIP verificado (19/10/2026)

**Origem:** ZIP do repositório enviado pelo usuário, exportado do commit `50cc951e52c5ac5ca125e93416b2cad45f416ee9`, SHA-256 do ZIP `6e3632eca47024137e4af7e063122486d4ef848d751d090b240563ab9a945c93`. Conteúdo `frontend/visual/` extraído em ambiente isolado, **31/31 arquivos** com comprimento e hash Git Blob SHA-1 idênticos ao inventário da árvore GitHub desse commit. Nenhum arquivo do backend ou documentação foi executado.

## Evidências observadas (execuções, não inferências de código)

1. **Node.js v22.16.0 real:** `node --test --test-reporter=tap tests/*.test.mjs` executado com os arquivos originais. **189 testes, 189 PASS, 0 FAIL, 0 SKIP**.
2. **Chromium/Playwright real, primeira execução:** o smoke original parou em uma asserção imediata de aba `Extração` depois de confirmar um diálogo nativo. Diagnóstico independente nas quatro larguras confirmou que a interface chegava ao estado correto após o evento `close`: tratava-se de sincronização do teste, sem evidência de falha de domínio.
3. **Correção de teste, não do aplicativo:** commit [`e873463e`](https://github.com/prumogrowth/Prumo-Growth---Platform/commit/e873463eaf36c6683477d30acb330bbe716e6660) ajusta `browser.smoke.py` para usar `expect(...).to_have_text('Extração')` e `expect(...).to_contain_text('Pedido simulado')` nos dois eventos de fechamento nativo. A versão local do teste corrigido tem hash Git Blob `b6aec358df62c98a08c0e4ef4eaa2bfb49e87f41`, **idêntico ao arquivo GitHub**.
4. **Node.js real após a correção:** novamente **189/189 PASS, 0 FAIL, 0 SKIP**.
5. **Chromium real com roteiro corrigido:** **três execuções integrais consecutivas PASS**, cobrindo 1440×900, 900×780, 390×844 e 320×640, fluxos O3/O4/O5, histórico, templates e isolamento de gestores em G2/G3/G4. Nenhum erro JavaScript ou overflow detectado pelas asserções do roteiro. Quatro capturas de tela ilustrativas também foram produzidas localmente, com dados inteiramente sintéticos.
6. **Verificador offline:** manifesto de 31 blobs atualizado no commit [`a2e4be53`](https://github.com/prumogrowth/Prumo-Growth---Platform/commit/a2e4be53cdb2c8413684ea440ac2ae0c59b4e667) para reconhecer a versão corrigida do smoke. O ZIP originalmente enviado continua identificado como revisão anterior; o teste corrigido foi aplicado e comparado por hash em ambiente isolado.

## Fronteiras e veredito

O conjunto de **código-fonte necessário aos testes nativos** está completo e tem integridade comprovada. O `run_acceptance.py --expected-head 50cc951e...` foi executado separadamente e identificou o inventário completo, mas **reprovou corretamente** seu gate de revisão por não haver diretório `.git` autenticado no ZIP: Node e Chromium foram bloqueados **apenas nesse runner formal**. As execuções nativas independentes registradas acima ocorreram, mas **não devem ser confundidas com `full_acceptance=true` do runner**, nem com homologação de produção.

Nada depende do Supabase nesta rodada: nenhuma autenticação, RLS, API Meta, banco real ou backend S0 foi acessado. Controle de permissões na UI sintética não comprova segurança de servidor. **FV-UI-013: evidência nativa positiva em snapshot ZIP, formalmente não homologada. 19F mantido em 69/100.** Sem alteração fora de `frontend/`, merge, deploy ou execução bancária.

Os registros TAP, logs Chromium, JSON de integridade/execução e capturas ficam como artefatos locais associados à conversa, não como dados reais versionados no repositório.
