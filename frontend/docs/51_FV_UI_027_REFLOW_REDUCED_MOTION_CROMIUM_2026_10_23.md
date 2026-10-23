# FV-UI-027 — Reflow em tela baixa, movimento reduzido e smoke nativo

**Data:** 23/10/2026 · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** exclusivamente `frontend/`.
**Base:** [FV-DOC-03](./38_FV_DOC_03_CONTRATO_FUNCIONAL_FRONTEND_2026_10_22.md), [FV-UI-025](./49_FV_UI_025_GATES_SEQUENCIAIS_VALIDACAO_2026_10_22.md) e [FV-UI-026](./50_FV_UI_026_EXECUCAO_NATIVA_DIAGNOSTICO_2026_10_22.md).

## Falha visual reproduzida antes da correção

No Chromium real, a janela de **360×500 CSS px** apresentava **16 px de altura útil da área de conversas**, dentro do painel com altura fixa de 500 px, enquanto o conteúdo calculado era maior que 500 px e o `body` impedia rolagem global. O rodapé e o restante da lista não eram alcançáveis de modo adequado. A largura da página não transbordava e não havia erro JavaScript, mas isso **não bastava** para garantir navegabilidade.

O problema foi encontrado numa **cópia local derivada do ZIP autorizado pelo usuário**; a investigação não envolveu dados reais nem serviços externos.

## Correções de código e teste

| Arquivo | Mudança | Limite |
|---|---|---|
| `frontend/visual/styles.css` | Regra específica `max-width:760px` e `max-height:700px`: habilita rolagem vertical do painel de lista, mantém cabeçalho/rodapé em fluxo e dá à lista uma altura mínima de 170px, permitindo percorrer todas as conversas. | A partir do breakpoint a lista inteira rola, inclusive o cabeçalho; não foi alterada a estrutura de permissões ou a lógica dos casos. |
| `frontend/visual/tests/browser.smoke.py` | Acrescenta cenários de viewport CSS `720×850`, `360×500`, `320×640`, `reduced_motion='reduce'`, ausência de overflow horizontal, última conversa/rodapé alcançáveis, retorno do foco em conversa/detalhe e ausência de erros JS. Também substitui duas verificações prematuras após o `close` assíncrono de diálogos por espera Playwright de estado real (fila e conclusão F03). | Esses viewports são **aproximação de reflow equivalente a 200%/400%**, não um teste de zoom de navegador/OS real. Não houve teste com leitor de tela humano. |
| `frontend/visual/tests/source-contract.test.mjs` | Registra teste estático FV-UI-027 para o breakpoint, rolagem, movimento reduzido e presença do novo roteiro Chromium. | Teste estático não equivale a teste visual. |

A regra `prefers-reduced-motion:reduce` já existia; este incremento acrescenta a **verificação nativa** da duração de transição (`0s`), não apresenta a preferência como uma capacidade inédita.

## Evidências executadas em ambiente local

Fonte: ZIP originalmente enviado do commit `83d5f4df`, com duas correções de FV-UI-026 e alterações de FV-UI-027 aplicadas numa **cópia derivada**, sem acesso a checkout privado. O manifesto local foi atualizado contra os bytes dessa cópia. Resultados:

- `python3 -B -m unittest discover`: **20/20 PASS**.
- `node --test`: **318/318 PASS** (inclui o novo teste estático FV-UI-027).
- Roteiro `browser.smoke.py` com Playwright/Chromium instalado: **PASS** nos fluxos existentes e nos três cenários adicionais de reflow, foco, rolagem e movimento reduzido. O roteiro completo foi repetido com êxito.
- `verify_offline_export.py --archive <ZIP_DERIVADO_LOCAL> --run-native`: **PASS** de integridade em **54/54 arquivos** e dos gates em sequência `zip_security_python` → `node` → `chromium`; `native_snapshot_pass=true`.
- **`git_checkout_verified=false` e `full_acceptance=false`**, como deve ser para um ZIP sem checkout autenticado, branch/HEAD verificadas pelo Git e árvore limpa.

Os resultados correspondem à **cópia local derivada testada**. As mesmas alterações foram aplicadas à branch GitHub, com manifesto de hashes pinado depois das mudanças. Isso não equivale a afirmar que uma nova exportação da branch foi executada depois do commit.

## Pendências

- Repetir o runner sobre exportação oficial do **novo HEAD** e, para homologação, sobre checkout Git autorizado limpo com `--expected-head` completo.
- Fazer avaliação manual de **zoom real 200%/400%**, navegação por teclado e leitores de tela, foco em modais, contraste e orientação mobile com dispositivo real.
- Não houve integração produtiva com S0/S1, Supabase/RLS, Meta/WhatsApp, IA F01/F03 ou banco; não há prova de envio/persistência, merge, deploy ou homologação FV-UI-013. Referência histórica `19F=69/100` inalterada.
