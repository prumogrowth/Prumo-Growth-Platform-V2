# FV-UI-023 — Preparação da validação nativa de ZIP offline

**Data:** 22/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Natureza:** qualidade do Frontend, sem execução de API de negócio e **sem homologação**.

**Referências:** [FV-DOC-03](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md), [FV-UI-021](./45_FV_UI_021_PREPARACAO_S0_S1_ACESSIBILIDADE_2026_10_22.md), [FV-UI-022](./46_FV_UI_022_ESCAPE_RASCUNHO_SMOKE_REGRESSAO_2026_10_22.md).

## Problema e solução

O ambiente desta conversa dispõe de Node e Chromium, mas não de um checkout autenticado do repositório privado. A versão anterior de `tests/verify_offline_export.py` estava pinada em fontes anteriores aos incrementos FV-UI-019..022; por isso não validava o Frontend vigente nem continha o teste de manifesto.

O incremento **FV-UI-023** atualiza a rota independente de `git clone` para um **ZIP exportado diretamente da branch no GitHub pelo usuário**. Não baixa arquivos via rede no script: recebe arquivo ZIP local e compara **cada Git blob SHA-1 + tamanho** com o inventário pinado, antes de abrir o snapshot para testes. Não aprova por nome, data, quantidade de commits ou simples afirmação de HEAD.

Controles introduzidos:
- `offline-export-manifest.test.mjs` prova em Node, quando executado, que todos os arquivos da pasta `frontend/visual` (excluído o próprio verificador para evitar circularidade) estão no manifesto, com conteúdo, hash Git e tamanho corretos.
- `verify_offline_export.py` rejeita arquivos inesperados dentro de `frontend/visual`, entradas ZIP duplicadas, caminhos inseguros, links simbólicos e arquivos excessivamente grandes; exige que a cópia do **próprio verificador Python** no ZIP seja idêntica à que está executando.
- O script só extrai arquivos explicitamente pinados, mais o próprio verificador previamente comparado; não extrai outras árvores do repositório.
- O inventário atualizado inclui **26 arquivos de testes `*.test.mjs`** e o roteiro `browser.smoke.py`, além de arquivos de dados, HTML, CSS e módulos. O runner `run_acceptance.py` continua restrito à branch autorizada para aceite completo de checkout.
- `acceptance-matrix.json` inclui o teste offline em **FV-22-16**; os 16 critérios são rastreabilidade, não porcentagens ou aprovação real.

## Roteiro manual de diagnóstico sem clone

1. No GitHub, abrir `prumogrowth/Prumo-Growth---Platform`, selecionar **`feat/frontend-plataforma-visual`** e escolher **Code → Download ZIP**. **Não** usar ZIP de documentação antiga ou de outra branch.
2. Extrair o ZIP num diretório local seguro para acessar a cópia `frontend/visual/tests/verify_offline_export.py` incluída nele.
3. Executar o Python a partir dessa cópia, passando o ZIP **original** por `--archive`:
   ```bash
   python3 /caminho/extraido/.../frontend/visual/tests/verify_offline_export.py \
     --archive /caminho/downloads/Prumo-Growth---Platform.zip \
     --run-native --json-report /caminho/relatorio_fv_023.json
   ```
4. O script deve emitir `Integrity PASS` e, quando Node/Chromium e Playwright Python estiverem instalados, testar ambos contra uma cópia temporária **verificada**. Um erro, ausência de binário ou divergência de bytes resulta em falha explícita.
5. **Diagnóstico de ZIP não é homologação FV-UI-013**: para essa etapa ainda é necessário um checkout Git autorizado, SHA HEAD exato, árvore limpa, Node/Chromium e validação de acessibilidade/integridade com os contratos S0/S1 quando ratificados.

## Evidências e limites

- Implementação de verificação local e teste de consistência de manifesto versionados na branch; inventário pinado a revisão concreta no próprio código.
- A comparação do manifesto com os metadados GitHub na conexão é **estrutural**. Não foi executado, nesta sessão, um ZIP privado completo em Node nem a bateria de navegador. Nenhum resultado de Chromium real deve ser inferido.
- Nenhuma alteração de S0/S1, autenticação, OpenAI F01/F03, Meta, MCP, banco, RLS, banco de dados, integração real, produção, merge ou deploy.

**Gate pendente:** obter o ZIP privado diretamente do GitHub e executar o comando anterior, ou executar o `run_acceptance.py --expected-head SHA_COMPLETO` sobre checkout autorizado. Corrigir quaisquer falhas reais antes de anunciar homologação.
