# FVA-02 — Fechamento de estados de erro, confirmações e ações pendentes

**26/10/2026 · Frente visual Prumo · branch `feat/frontend-plataforma-visual`**

## Achado e correção na demonstração

O código de `changeActor` já invalidava intenções de fila, equipe, resultados e diálogos ao mudar perfil, **mas não limpava `state.followupRequests`**: um pedido de template/cadeia *exclusivamente local* poderia continuar parecendo solicitado quando o avaliador voltava ao mesmo caso por outro perfil. A troca de concessionária também conservava essa intenção. Não é dado real, incidente de segurança nem envio Meta: é uma **inconsistência de UX da simulação**, relevante para avaliação coletiva.

**Correção FVA-02:** limpar `state.followupRequests` em troca de ator e de loja, sem alterar mensagens, status comerciais, provas ou registros de F03. Preservar a distinção entre **solicitação local não enviada** e evento efetivamente confirmado pela S0. Os controles já possuíam guards de confirmação obsoleta, cuja cobertura foi ampliada.

## Cenários encadeados novos

| Teste | FV-22 / proteção | Esperado |
| --- | --- | --- |
| Template pendente → troca de ator → callback antigo → solicitação local → troca e retorno | 08,09,10 | Sem efeito de callback antigo; solicitação local não atravessa identidade; nenhuma prova `SENT` criada |
| Fila de leads → assunção local Aurora → troca para Horizonte → volta a Aurora | 12,13 | Solicitação sintética da loja anterior não aparece como atribuída ou pendente na outra concessionária; ação permanece disponível |
| Concluir F03 → `stale`, `uncertain`, `denied`, `unavailable` → caso de banco | 04,05,06,10,15 | Nenhuma gravação, retry automático ou mudança comercial; ação antiga não altera caso bancário |
| G2 pausa modal → troca de Gestor → callback antigo → nova pausa fictícia | 11,12,13 | Nenhuma pausa ou redistribuição aplicada por confirmação velha; monitor apresenta pedido local separado de estado confirmado |

## Fronteira técnica, segurança e continuidade

- Modificações permitidas: `frontend/visual/app.mjs`, `frontend/visual/tests/app.dom.test.mjs`, repin do manifesto `frontend/visual/tests/verify_offline_export.py` e documentação presente.
- O manifesto manterá apenas a referência do commit de fontes e hashes reais; **a saída testada precisa de CI PASS** antes de declaração de homologação.
- A interface permanece sintética, sem autenticação, isolamento S0 real, API, WhatsApp, banco, Supabase ou F03 real. O **Codex é owner do S0**.
- A validação atual de frontend cobre Python, Node e Chromium; **testes manuais com leitor de tela e dispositivos reais ainda pendentes**.
- **Destino futuro:** ChatGPT Sites via Work, somente após encerramento e alinhamento do prompt com o responsável. Nenhuma publicação ou conversão automática nesta execução.

## Evidências de certificação

**Pendente** até verificar workflow GitHub Actions para o conteúdo técnico desta execução. Não confundir execução iniciada com `FULL LOCAL ACCEPTANCE: PASS`.

## Diagnóstico da execução 40355374324 (superada por correção de teste)

- Preflight 59 arquivos e Python 25/25 PASS; Node 377/379 PASS, Chromium não iniciado pelo gate fail-closed. Duas falhas **nos cenários de teste FVA-02**: comparação ampla de `ENVIADO` capturou o aviso explícito de **nunca enviado**; teste de Gestor tentou oferecer template em caso cujo titular era o Consultor. Não foi evidenciada regressão nos 375 testes anteriores.
- Correção: usar comparação de estado inequívoco (`Envio comprovado` ausente) e substituir o cenário inelegível por fila compartilhada entre duas lojas concedidas à Gestora. Os guards do produto foram preservados. **Nova execução de CI necessária.**
