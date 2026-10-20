# FV-UI-015 — Indicador único de conversas e confirmação G2 (20/10/2026)

**Status:** incremento funcional **exclusivamente sintético**, ainda sem integração S0/S1. **Base de produto [D]:** indicador único com duas cores provisórias, números de mensagens não lidas e bolinha sem número quando o operador leu e não respondeu; nenhum SLA/cronômetro na fila operacional. Gestor não marca mensagens como lidas por mera supervisão. Pausa/retomada via botão + confirmação, sem motivo/data; nenhum acesso, distribuição ou carteira alterados no navegador.

## Implementado

1. **`app.mjs`** agora usa `conversation-attention.mjs` para desenhar exatamente um dos estados na lista: `attention-unread` numerado (limite de exibição 99) ou `attention-pending` sem número. O segundo depende de leitura sintética pelo titular **e** última interação humana relevante representada por mensagem recebida. Resposta humana fictícia remove o estado pendente. Não se infere entrega real do WhatsApp ou tempo de espera.
2. Ao abrir conversa, o navegador só zera o contador fictício quando o perfil atualmente selecionado é o **profissional designado**; um gestor que apenas supervisiona pode ler D2, mas não altera o estado de leitura do profissional. Gestor formalmente **autoatribuído** é tratado como titular no cenário sintético. A confirmação de leitura REAL continua pertencendo ao S0; `local-fixture-only` não é prova de autorização.
3. **`index.html` + `styles.css`** trazem um diálogo nativo de confirmação para solicitar pausa/retomada G2, com cores de badge provisórias. A solicitação local só aparece ao clicar **Confirmar**. Cancelar, trocar de perfil e resetar descartam a confirmação anterior.
4. **Nenhuma redistribuição é executada**, nenhum status comercial/conta/loja é mutado, não há armazenamento, remessa, Supabase, Meta, banco real, autorização na UI ou chamadas de rede.
5. `browser.smoke.py` concatena o módulo novo na ordem correta, sem colisão lexical com D3 (renomeação para `ATTENTION_EMPTY`). Todos os testes DOM existentes de G2 passaram a acionar a confirmação antes de afirmar pedido local.

## Evidências realmente executadas

- **Node v22.16.0, nativo**: `node --test --test-reporter=tap tests/*.test.mjs` → **221 PASS / 221, 0 FAIL**. Inclui os **sete cenários novos** `tests/attention-integration.test.mjs` (badge numérico, badge lido sem número, resposta, isolamento da supervisão, troca de perfil, cancelamento/confirmação e bloqueio a operador).
- **Chromium real, Playwright**: `CHROMIUM_EXECUTABLE=/usr/bin/chromium python tests/browser.smoke.py` → **PASS** nos quatro viewports 1440×900, 900×780, 390×844 e 320×640, mais G2/G3/G4, O3/O4/O5, templates e histórico.
- O ambiente nativo foi reconstruído a partir do ZIP fornecido pelo responsável e dos incrementos versionados, com hashes Git conferidos dos módulos alterados e roteiro Chromium; os artefatos documentam esta reconciliação. **Não há checkout Git autenticado**, portanto o runner formal permanece pendente.
- Também houve um ensaio de interação em V8 sobre fontes lidas diretamente da branch do GitHub, com **11 verificações afirmativas**. Isso não substitui os testes nativos.

## Limites funcionais e coordenação

- A regra de pendência derivada da **última mensagem da fixture** só é válida para a demonstração; dados reais precisarão de marcadores explícitos de leitura por profissional, prova da resposta humana e versão do caso em projeção autorizada do S0. Supervisor não escreve marcador em nome do operador.
- `requestMockIntake` continua retornando `requested_demo`, sem efeito no núcleo; a S1 deve separar conta de recebimento e implementar pausa seletiva/transfers sob sua responsabilidade, inclusive sem destinatário elegível. A orientação enviada pelo responsável (FV-UI-014) permanece governante.
- Os estados do indicador não são um novo status comercial: preservam-se os **oito estados canônicos**. Nenhum destaque de tempo aguardando, SLA ou ranking foi introduzido.
- A aparência permanece provisória conforme o responsável; foco exclusivamente funcional.

**Governança:** branch `feat/frontend-plataforma-visual`, arquivos alterados apenas em `frontend/`; nenhuma alteração feita na S1 ou S0 nesta rodada. FV-UI-013 segue NÃO HOMOLOGADA pelo checkout formal; 19F permanece 69/100.
