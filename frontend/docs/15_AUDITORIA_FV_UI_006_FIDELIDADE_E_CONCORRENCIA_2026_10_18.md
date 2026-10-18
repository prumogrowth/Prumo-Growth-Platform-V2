# FV-UI-006 — Fidelidade de estados e segurança de interações (18/10/2026)

**Escopo:** `frontend/visual/` na branch `feat/frontend-plataforma-visual`, exclusivamente dados artificiais e operações na memória da demonstração. Confronto com FV-01/FV-02/FV-03, CF-OP-02 e FV-GATE-01. Nenhuma API, banco, Meta ou OpenAI real.

## Achados e reparos

| ID | Divergência identificada | Correção realizada |
| --- | --- | --- |
| UI6-01 | Estado `humanCompletionProjection=unknown` podia ser apresentado como “etapa concluída”, embora não existisse confirmação | Tratamento explícito de `pending / completed / unknown` com mensagem “não confirmada” sem inferência; fixtures IA/banco agora mantêm estado desconhecido na ausência de dado |
| UI6-02 | Uma resposta `accepted` do botão podia ser interpretada como conclusão humana efetivada | Simulação passa a `requested_demo` e exibe **“Conclusão solicitada”**, sem alegar desfecho, extração concluída, ficha persistida, remessa ou venda |
| UI6-03 | Modal aberto em caso/perfil anterior podia receber confirmação obsoleta após troca de contexto | Contexto de caso+loja+ator capturado ao abrir e consumido uma única vez no fechamento; mudanças de ator, loja, conversa ou caixa ativa/histórico cancelam e invalidam os diálogos |
| UI6-04 | Callback de nota antiga podia agir sobre referência de caso anterior | Submissão revalida que o caso atual coincide com o formulário e continua atribuído/elegível; retornos sintéticos de extração e pedidos de cadeia também verificam o caso |
| UI6-05 | Mock DOM não expunha propriedade nativa `dialog.open` usada no fechamento | Mock corrigido; testes novos cobrem troca de perfil/caso enquanto há modal, ausência de falso sucesso e callback de formulário antigo |

## Evidência executada nesta revisão

Todos os arquivos de código e teste foram relidos da branch GitHub **após os reparos** e avaliados em harness JavaScript V8, adaptando `import/export` e as asserções estritamente para o avaliador:

- **25/25** testes de regras/projeções: passaram.
- **17/17** testes de interação DOM sintético (desktop/genérico e mobile): passaram.
- **6/6** inspeções estáticas de HTML/CSS/JS: passaram.
- **48/48 verificações sintéticas** no total, zero falhas observadas neste harness.

**Limitações importantes:** não se trata de execução literal de `node --test`, nem prova de Chromium, responsividade renderizada, leitores de tela, APIs, autenticação ou persistência. O script `tests/browser.smoke.py` está disponível, mas **não foi executado com a versão FV-UI-006**. Este documento não homologa a aplicação.

## Gating e continuidade

- **Frontend:** os pontos de inconsistência documental acima foram corrigidos; executar Node e Playwright real em ambiente com os arquivos da branch e registrar evidência, depois completar telas O3/O4/O5/G2–G4 conforme contratos revisados, sempre com dados fictícios.
- **S0/OpenAI/Meta/S1-002:** seguem responsáveis por contrato físico, autorização, concorrência real, conclusão humana e extração, status do banco, prova de envio de template, remanejamento e isolamento. A UI não pode assumir essas decisões.
- **Usuário:** avaliação de aparência/posicionamento reservada para a interface madura; nenhuma decisão do responsável exigida agora.
- **Operação:** sem merge, deploy, domínio, hospedagem, alteração de Supabase ou elevação automática da régua auditada do doc.19F (**69%**).
