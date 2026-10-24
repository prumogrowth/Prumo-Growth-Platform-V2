# FV-UI-042 — Legibilidade do cabeçalho e das mensagens da conversa

**Data:** 24/10/2026 · **Repositório oficial:** `0marcos0paulo0-rgb/Plataforma-de-Vendas-por-IA` · **Branch:** `feat/frontend-plataforma-visual` · **Escopo:** somente `frontend/`.

## Objetivo

Dar continuidade à hierarquia visual estabelecida na fila (FV-UI-040) e nos Detalhes (FV-UI-041). A conversa ainda apresentava corpo das mensagens em 12px, horários internos em 9px, separador de dia em 10px e contexto de cabeçalho pouco contrastante. A nota que explica a simulação do compositor também era pequena no celular. A orientação é manter a linguagem neutra inspirada na organização de aplicativos de mensageria, sem reproduzir identidade de terceiro e sem ocultar avisos técnicos.

## Implementação

CSS escopado a `.thread-pane`:

- Cabeçalho: nome 15px (14px com largura até 400px); contexto 12px (11px até 400px).
- Balões: texto de 13px e entrelinha de 1,65; horários dos balões 11px.
- Mensagem de sistema: pelo menos 12px, mantendo o tom próprio de aviso técnico.
- Separador de dia e nota de simulação do compositor: 11px; destaque condicional no modo escuro para o separador.
- Ajuste de cores dos elementos secundários nos temas claro e escuro, mantendo cores de transporte/ACK, proibição de reenvio automático, status comercial e estado humano.
- O componente de mensagem, conteúdo, ordem, ações, botões, eventos e regras de permissão são inalterados.

## Evidências disponíveis

O ensaio **Chromium real direcionado FV-UI-042 passou em 8/8 cenários**: 320, 390, 900 e 1440 CSS px × temas claro/escuro. Verificou a visibilidade da conversa, seis alvos de tipografia, contraste calculado **≥4,5:1** para os alvos amostrados, inexistência de erros JS e ausência de overflow horizontal. Foi utilizado um **snapshot local derivado do FV-UI-036**, com a correção CSS aplicada, sem acesso de checkout Git ao repositório privado.

A regressão Node sobre o snapshot local, excluindo deliberadamente o teste de manifesto dessa versão anterior, resultou em **339/339 PASS**. Não deve ser confundida com execução dos contratos FV-UI-037 a 042 sobre um checkout autêntico.

A execução do roteiro completo `tests/browser.smoke.py` da base local ultrapassou o limite permitido no ambiente e foi interrompida. **Não existe PASS integral de browser para este incremento**; somente o smoke direcionado acima foi aprovado.

A auditoria da árvore do GitHub e o manifesto de 58 blobs serão conferidos após o registro do código. Integridade dos blobs não equivale ao gate nativo de execução do checkout oficial.

## Fronteiras preservadas

Demonstração sintética apenas. Nenhum S0/S1, API Meta/WhatsApp, OpenAI, Supabase, transação bancária, dado de cliente real, integração, autenticação, concessão, alteração de atribuição ou permissão. Não fazer merge na `main` nem deploy.

**Anterior:** [FV-UI-041](./70_FV_UI_041_LEGIBILIDADE_DETALHES_2026_10_24.md).

## Ajuste posterior de contraste em estados técnicos

Ao revisar a regra genérica que estiliza elementos `small` dos balões, foi identificado risco de confundir horários neutros com as etiquetas técnicas `message-send-state`, `message-transport-state` e `message-transport-hint`. O ajuste final atribui a cor neutra **somente aos horários sem classe**, mantém o tamanho mínimo de 11px em todas as etiquetas e define cores próprias e contrastantes para os estados técnicos nos dois temas. O aviso de transporte tinha contraste insuficiente na base local clara (**aprox. 2,26:1**); após a correção, o ensaio direcionado repetido passou em **8/8 cenários** com contraste calculado ≥4,5:1 também nesse aviso. Continua sendo evidência local derivada, não gate integral de checkout.


## Registro final na branch oficial

- Primeiro commit visual, testes e documentação: `1347de6359fe10a3767df10aa11da5e3dc40e563`.
- Primeiro repin de manifesto: `48f341ce83422aff244e31af49101b4dbd48621f` (substituído pelo repin definitivo).
- Correção de contraste e distinção dos estados técnicos: `f787b7138cdcaa7aeed27dc3d661744ccd47499f`.
- Manifesto definitivo: `0060ffbbeb288c17afea30722a3c59aad09ef69b`, com `source_head=f787b7138cdcaa7aeed27dc3d661744ccd47499f`.
- Conferência remota: **58/58 hashes Git blob SHA-1 e tamanhos conferidos**, zero divergências; blob SHA do próprio verificador: `737197f7be4230e18f3538f9982a3665e3db4742`.
- Comparação com FV-UI-041: **4 commits e 7 arquivos alterados**, todos sob `frontend/`.
- `main` preservada em `dace737ab7afb7ae3f5a3a6f5cb522e6def8b43a` — nenhum merge ou deploy.
- **Gates:** Chromium direcionado **8/8 PASS**, Node da base derivada **339/339 PASS** (excluindo manifesto antigo). A suíte Chromium completa excedeu o tempo e não deve ser registrada como PASS; checkout autenticado do HEAD oficial e aceite humano continuam pendentes.
