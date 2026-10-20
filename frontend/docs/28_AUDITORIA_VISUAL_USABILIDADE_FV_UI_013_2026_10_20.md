# FV-UI-013 — auditoria visual e usabilidade em quatro viewports (20/10/2026)

**Escopo autorizado:** apenas `frontend/` na branch `feat/frontend-plataforma-visual`. Artefato **demonstrativo com dados fictícios**; sem backend, Supabase, autenticação real, Meta, instituição financeira, remessa, deploy, merge ou mudança de progresso 19F.

## Método e fonte de evidência

Foi utilizado o ZIP integral do GitHub anexado pelo responsável, correspondente ao commit `50cc951e52c5ac5ca125e93416b2cad45f416ee9`, com **31 blobs** do frontend previamente conferidos por hash Git. O ambiente de testes contém Node.js v22.16.0, Playwright e Chromium real. Inspeção visual e medição por `getBoundingClientRect()` em **1440×900, 900×780, 390×844 e 320×640**, sobre o mesmo roteiro de módulos JS/CSS/HTML locais de `tests/browser.smoke.py`. Os arquivos alterados foram confrontados com os blobs publicados no GitHub. Não se tratou de inspeção em servidor S0.

## Achados demonstrados e correções

| Achado antes da correção | Evidência observada | Correção visual/UX |
|---|---|---|
| G3 ficava abaixo de um quadro inicial demasiado comprido | Primeira métrica G3 em Y=1066 (desktop), 1057 (tablet), 1419 (390px) e **1708px (320px)** | `app.mjs` prioriza indicadores, carteira e sinais; preserva por completo o quadro comercial canônico abaixo |
| Diálogo gerencial ocupa quase todo o espaço do celular com orientação longa | No celular 320×640: título + instruções consumiam 325px aproximadamente; botões quebravam em duas linhas | `index.html` usa título conciso, descrição essencial e `<details>` nativo para explicação integral; `styles.css` permite mais altura útil e mantém botões numa linha |
| Botões pequenos no diálogo móvel | Em 390/320px, botões de G2/G3/G4 mediam cerca de 32px de altura, fechar 38px | Botões e fechar passam a ter pelo menos 44px de altura no mobile |
| Contraste fraco em textos auxiliares | Ex.: rótulos `#69828c` sobre `#f3f8f7` tinham contraste calculado ≈**3,79:1** | Rótulos `#536d75` sobre o mesmo fundo: ≈**5,14:1**; cabeçalhos e textos gerenciais ajustados localmente |

### Comprovação pós-correção no Chromium real

| Viewport | Primeira métrica antes (Y) | Depois (Y) | Inteira na área visível do modal? |
|---|---:|---:|---|
| 1440×900 | 1066px | 372px | Sim |
| 900×780 | 1057px | 363px | Sim |
| 390×844 | 1419px | 335px | Sim |
| 320×640 | 1708px | 379px | Sim |

Em **320×640**, os botões G2/G3/G4 passaram de **72px de altura total, com quebra**, para **44px em uma linha**. A área vertical visível do modal passou de 538px para 616px. O resumo comercial, as etapas canônicas e os alertas S0 sintéticos continuam disponíveis com os mesmos dados; a explicação longa fica a um acionamento no controle nativo `<details>`.

## Testes realmente executados

- **Node nativo**: `node --test --test-reporter=tap tests/*.test.mjs` → **190/190 PASS, 0 FAIL, 0 SKIP**, após atualização do contrato estático G3 e adição de teste preventivo de UX.
- **Chromium real**: `python tests/browser.smoke.py` → **PASS** nos quatro tamanhos, mais histórico, O5, G2/G3/G4 e suspensão; asserções adicionadas conferem primeira métrica G3 dentro do modal, alvos de toque de 44px, disclosure aberto/fechado por clique e teclado **Enter**.
- Os hashes Git Blob dos cinco arquivos modificados correspondem exatamente aos usados nas execuções locais finais. Nenhum overflow horizontal foi sinalizado pelo roteiro nos tamanhos testados.

## Riscos remanescentes e veredito

**Não houve ensaio com leitor de tela, auditoria WCAG integral, contraste exaustivo de toda a aplicação, testes em dispositivos físicos ou autorização no backend.** A mudança de ordem do G3 refere-se apenas à apresentação; não valida autenticidade/segurança de informações reais. Continuam pendentes a aprovação visual pelo responsável e o requisito formal de checkout Git de `run_acceptance.py`, que não é suprido automaticamente por ZIP.

**Conclusão:** a barreira visual gerencial demonstrada foi corrigida e passou pelos testes Node/Chromium reais. **FV-UI-013: evidência positiva com auditoria visual parcial; NÃO HOMOLOGADA** até liberação formal. **19F: 69/100**, inalterado.
